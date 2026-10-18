import {geoConicConformal, geoInterpolate, geoPath} from 'd3-geo';
import type {Feature, MultiPolygon} from 'geojson';
import mapData from '../data/france.json';
import type {LonLat} from '../data/tour';

export const france = mapData.france as unknown as Feature<MultiPolygon>;
export const neighbours = mapData.neighbours as unknown as Feature<MultiPolygon>[];

// Emprise de la carte en vue « France entière » (pixels de la vidéo 1080×1920).
export const MAP_BOX = {x0: 80, y0: 430, x1: 1000, y1: 1350};
export const MAP_CENTER = {x: (MAP_BOX.x0 + MAP_BOX.x1) / 2, y: (MAP_BOX.y0 + MAP_BOX.y1) / 2};

// Projection conique conforme de Lambert, paramètres du Lambert-93 (RGF93),
// projection officielle de la France métropolitaine (IGN).
export const projection = geoConicConformal()
	.parallels([44, 49])
	.rotate([-3, 0])
	.center([0, 46.5])
	.fitExtent(
		[
			[MAP_BOX.x0, MAP_BOX.y0],
			[MAP_BOX.x1, MAP_BOX.y1],
		],
		france,
	);

const path = geoPath(projection);
export const francePath = path(france) ?? '';
export const neighbourPaths = neighbours.map((n) => path(n) ?? '');

export type Pt = {x: number; y: number};

export const project = (c: LonLat): Pt => {
	const [x, y] = projection(c) ?? [0, 0];
	return {x, y};
};

const EARTH_RADIUS_KM = 6371.0088; // rayon moyen IUGG

/** Distance orthodromique (formule de haversine), en km. */
export const haversineKm = ([lon1, lat1]: LonLat, [lon2, lat2]: LonLat): number => {
	const r = Math.PI / 180;
	const dLat = (lat2 - lat1) * r;
	const dLon = (lon2 - lon1) * r;
	const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * r) * Math.cos(lat2 * r) * Math.sin(dLon / 2) ** 2;
	return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(a));
};

/** Points (projetés) le long de l'orthodromie entre deux lieux. */
export const greatCircle = (a: LonLat, b: LonLat, n = 160): Pt[] => {
	const interp = geoInterpolate(a, b);
	return Array.from({length: n + 1}, (_, i) => project(interp(i / n) as LonLat));
};

/** Points (projetés) d'un trajet routier stylisé : légère courbe entre deux lieux. */
export const roadCurve = (a: LonLat, b: LonLat, n = 60): Pt[] => {
	const p0 = project(a);
	const p2 = project(b);
	const dx = p2.x - p0.x;
	const dy = p2.y - p0.y;
	const ctrl = {x: (p0.x + p2.x) / 2 - dy * 0.18, y: (p0.y + p2.y) / 2 + dx * 0.18};
	return Array.from({length: n + 1}, (_, i) => {
		const t = i / n;
		const u = 1 - t;
		return {
			x: u * u * p0.x + 2 * u * t * ctrl.x + t * t * p2.x,
			y: u * u * p0.y + 2 * u * t * ctrl.y + t * t * p2.y,
		};
	});
};

/** Position et cap le long d'une polyligne, pour t ∈ [0, 1] (abscisse curviligne). */
export const along = (pts: Pt[], t: number): Pt & {angle: number} => {
	const lens = [0];
	for (let i = 1; i < pts.length; i++) {
		lens.push(lens[i - 1] + Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y));
	}
	const total = lens[lens.length - 1];
	const target = Math.min(Math.max(t, 0), 1) * total;
	let i = 1;
	while (i < pts.length - 1 && lens[i] < target) i++;
	const seg = lens[i] - lens[i - 1] || 1;
	const k = (target - lens[i - 1]) / seg;
	const a = pts[i - 1];
	const b = pts[i];
	return {x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, angle: (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI};
};

/** Sous-polyligne de 0 à t, terminée par le point interpolé exact. */
export const partial = (pts: Pt[], t: number): Pt[] => {
	if (t <= 0) return [pts[0]];
	if (t >= 1) return pts;
	const end = along(pts, t);
	const lens = [0];
	for (let i = 1; i < pts.length; i++) {
		lens.push(lens[i - 1] + Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y));
	}
	const target = t * lens[lens.length - 1];
	return [...pts.filter((_, i) => lens[i] < target), end];
};

// ── Estimations de temps de trajet ───────────────────────────────────────────
// Vol : vitesse moyenne bloc d'un avion de ligne régional (≈ 750 km/h en
// croisière) + 20 min de roulage, montée et approche.
const FLIGHT_CRUISE_KMH = 750;
const FLIGHT_OVERHEAD_MIN = 20;
// Route : distance à vol d'oiseau × 1,3 (coefficient de détour routier moyen)
// et 45 km/h de moyenne en zone périurbaine.
const ROAD_DETOUR = 1.3;
const ROAD_KMH = 45;

const roundTo5 = (min: number) => Math.max(5, Math.round(min / 5) * 5);

export const flightEstimate = (a: LonLat, b: LonLat) => {
	const km = haversineKm(a, b);
	return {km, minutes: roundTo5(FLIGHT_OVERHEAD_MIN + (km / FLIGHT_CRUISE_KMH) * 60)};
};

export const roadEstimate = (a: LonLat, b: LonLat) => {
	const km = haversineKm(a, b) * ROAD_DETOUR;
	return {km, minutes: roundTo5((km / ROAD_KMH) * 60)};
};

export const formatDuration = (min: number) => {
	const h = Math.floor(min / 60);
	const m = min % 60;
	if (h === 0) return `${m} MIN`;
	return `${h} H ${String(m).padStart(2, '0')}`;
};

export const formatKm = (km: number) => `${Math.round(km).toLocaleString('fr-FR')} KM`;
