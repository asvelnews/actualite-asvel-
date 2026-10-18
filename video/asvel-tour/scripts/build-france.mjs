// Génère src/data/france.json à partir de Natural Earth (paquet npm world-atlas).
// - France métropolitaine + Corse en résolution 1:10m (données Natural Earth, domaine public)
// - Pays voisins en 1:50m, uniquement pour le contexte visuel
import {readFileSync, writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {feature} from 'topojson-client';

const require = createRequire(import.meta.url);
const load = (f) => JSON.parse(readFileSync(require.resolve(`world-atlas/${f}`), 'utf8'));

// Emprise métropolitaine : exclut la Guyane et les autres territoires ultramarins
const METRO = {minLon: -5.5, maxLon: 10, minLat: 41, maxLat: 51.5};
const CONTEXT = {minLon: -12, maxLon: 16, minLat: 38, maxLat: 56};
const NEIGHBOURS = new Set(['724', '380', '756', '276', '056', '442', '826', '492', '020', '372', '528', '040', '438']);

const round = (ring) => ring.map(([x, y]) => [Math.round(x * 1e4) / 1e4, Math.round(y * 1e4) / 1e4]);
const bbox = (ring) => ring.reduce((b, [x, y]) => ({
  minLon: Math.min(b.minLon, x), maxLon: Math.max(b.maxLon, x),
  minLat: Math.min(b.minLat, y), maxLat: Math.max(b.maxLat, y),
}), {minLon: Infinity, maxLon: -Infinity, minLat: Infinity, maxLat: -Infinity});
const inside = (b, box) => b.minLon >= box.minLon && b.maxLon <= box.maxLon && b.minLat >= box.minLat && b.maxLat <= box.maxLat;
const overlaps = (b, box) => b.maxLon >= box.minLon && b.minLon <= box.maxLon && b.maxLat >= box.minLat && b.minLat <= box.maxLat;

const polygons = (geom) => (geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates);

const hi = load('countries-10m.json');
const fr = feature(hi, hi.objects.countries).features.find((f) => f.id === '250');
const france = {
  type: 'Feature',
  properties: {name: 'France métropolitaine', source: 'Natural Earth 1:10m (world-atlas 2.0.2)'},
  geometry: {
    type: 'MultiPolygon',
    coordinates: polygons(fr.geometry).filter((p) => inside(bbox(p[0]), METRO)).map((p) => p.map(round)),
  },
};

const lo = load('countries-50m.json');
const neighbours = feature(lo, lo.objects.countries).features
  .filter((f) => NEIGHBOURS.has(f.id))
  .map((f) => ({
    type: 'Feature',
    properties: {name: f.properties.name},
    geometry: {
      type: 'MultiPolygon',
      coordinates: polygons(f.geometry).filter((p) => overlaps(bbox(p[0]), CONTEXT)).map((p) => p.map(round)),
    },
  }))
  .filter((f) => f.geometry.coordinates.length > 0);

writeFileSync(new URL('../src/data/france.json', import.meta.url), JSON.stringify({france, neighbours}));
console.log(`France : ${france.geometry.coordinates.length} polygones, voisins : ${neighbours.length}`);
