// Régénère src/data/routes.json : itinéraires routiers réels (OSRM, données
// OpenStreetMap) pour chaque transfert en autocar de la tournée.
// Nécessite un accès réseau à router.project-osrm.org (ou OSRM_URL).
import {writeFileSync} from 'node:fs';
import {build} from 'esbuild';

const OSRM = process.env.OSRM_URL ?? 'https://router.project-osrm.org';

// Charge les données TypeScript de la tournée
const out = await build({entryPoints: [new URL('../src/data/tour.ts', import.meta.url).pathname], bundle: true, write: false, format: 'esm', platform: 'node'});
const {PLACES, AIRPORTS, GAMES, HOME_AIRPORT} = await import(`data:text/javascript;base64,${Buffer.from(out.outputFiles[0].text).toString('base64')}`);

// Liste des transferts, dans l'ordre de la vidéo (identique à src/lib/timeline.ts)
const legs = [];
const home = AIRPORTS[HOME_AIRPORT].terminal;
for (const g of GAMES) {
  if (g.airport) {
    const t = AIRPORTS[g.airport].terminal;
    legs.push(['BASE', home], [t, g.arena]);
    if (g.score) legs.push([g.arena, t], [home, 'BASE']);
  } else {
    legs.push(['BASE', g.arena]);
    if (g.score) legs.push([g.arena, 'BASE']);
  }
}

// Douglas-Peucker (tolérance ≈ 15 m)
const simplify = (pts, eps = 0.00014) => {
  if (pts.length < 3) return pts;
  const keep = new Set([0, pts.length - 1]);
  const stack = [[0, pts.length - 1]];
  const dist = ([px, py], [ax, ay], [bx, by]) => {
    const dx = bx - ax, dy = by - ay;
    const t = dx || dy ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy))) : 0;
    return Math.hypot(px - ax - t * dx, py - ay - t * dy);
  };
  while (stack.length) {
    const [i, j] = stack.pop();
    let m = -1, dm = 0;
    for (let k = i + 1; k < j; k++) {
      const d = dist(pts[k], pts[i], pts[j]);
      if (d > dm) [m, dm] = [k, d];
    }
    if (dm > eps) { keep.add(m); stack.push([i, m], [m, j]); }
  }
  return pts.filter((_, i) => keep.has(i));
};

const routes = {};
for (const [a, b] of legs) {
  const key = `${a}>${b}`;
  if (routes[key]) continue;
  const [A, B] = [PLACES[a].coords, PLACES[b].coords];
  const res = await fetch(`${OSRM}/route/v1/driving/${A[0]},${A[1]};${B[0]},${B[1]}?overview=full&geometries=geojson`);
  const json = await res.json();
  if (json.code !== 'Ok') throw new Error(`${key} : ${json.code}`);
  const r = json.routes[0];
  routes[key] = {
    distanceM: Math.round(r.distance),
    durationS: Math.round(r.duration),
    coords: simplify(r.geometry.coordinates).map(([x, y]) => [Math.round(x * 1e5) / 1e5, Math.round(y * 1e5) / 1e5]),
  };
  console.log(key, (r.distance / 1000).toFixed(1), 'km', Math.round(r.duration / 60), 'min');
}

writeFileSync(
  new URL('../src/data/routes.json', import.meta.url),
  JSON.stringify({source: 'OSRM (router.project-osrm.org, profil car), données © contributeurs OpenStreetMap (ODbL)', fetchedAt: new Date().toISOString().slice(0, 10), simplification: 'Douglas-Peucker ~15 m', routes}),
);
