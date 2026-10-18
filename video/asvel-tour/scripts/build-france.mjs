// Génère src/data/france.json :
// - départements de France métropolitaine : IGN ADMIN EXPRESS (Licence ouverte),
//   conversion GeoJSON gregoiredavid/france-geojson (simplification 25 %)
// - pays voisins : Natural Earth 1:50m (domaine public, paquet npm world-atlas)
import {writeFileSync} from 'node:fs';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {feature} from 'topojson-client';

const DEPARTEMENTS_URL = 'https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson';
const require = createRequire(import.meta.url);

const CONTEXT = {minLon: -12, maxLon: 16, minLat: 38, maxLat: 56};
const NEIGHBOURS = new Set(['724', '380', '756', '276', '056', '442', '826', '492', '020', '372', '528', '040', '438']);

const round = (ring, d) => ring.map(([x, y]) => [Math.round(x * 10 ** d) / 10 ** d, Math.round(y * 10 ** d) / 10 ** d]);
const bbox = (ring) => ring.reduce((b, [x, y]) => ({
  minLon: Math.min(b.minLon, x), maxLon: Math.max(b.maxLon, x),
  minLat: Math.min(b.minLat, y), maxLat: Math.max(b.maxLat, y),
}), {minLon: Infinity, maxLon: -Infinity, minLat: Infinity, maxLat: -Infinity});
const overlaps = (b, box) => b.maxLon >= box.minLon && b.minLon <= box.maxLon && b.maxLat >= box.minLat && b.minLat <= box.maxLat;
const polygons = (geom) => (geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates);

const deps = await (await fetch(DEPARTEMENTS_URL)).json();
const departements = deps.features.map((f) => ({
  type: 'Feature',
  properties: {code: f.properties.code, nom: f.properties.nom},
  geometry: {type: 'MultiPolygon', coordinates: polygons(f.geometry).map((p) => p.map((r) => round(r, 4)))},
}));

const lo = JSON.parse(readFileSync(require.resolve('world-atlas/countries-50m.json'), 'utf8'));
const neighbours = feature(lo, lo.objects.countries).features
  .filter((f) => NEIGHBOURS.has(f.id))
  .map((f) => ({
    type: 'Feature',
    properties: {name: f.properties.name},
    geometry: {
      type: 'MultiPolygon',
      coordinates: polygons(f.geometry).filter((p) => overlaps(bbox(p[0]), CONTEXT)).map((p) => p.map((r) => round(r, 3))),
    },
  }))
  .filter((f) => f.geometry.coordinates.length > 0);

writeFileSync(new URL('../src/data/france.json', import.meta.url), JSON.stringify({departements, neighbours}));
console.log(`Départements : ${departements.length}, voisins : ${neighbours.length}`);
