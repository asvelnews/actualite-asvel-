import {geoConicConformal, geoInterpolate, geoPath} from 'd3-geo';
import type {Feature, FeatureCollection, MultiPolygon} from 'geojson';
import mapData from '../data/france.json';
import type {LonLat} from '../data/tour';

type Dep = Feature<MultiPolygon, {code: string; nom: string}>;
export const departements = mapData.departements as unknown as Dep[];
export const neighbours = mapData.neighbours as unknown as Feature<MultiPolygon>[];
const franceFc: FeatureCollection = {type: 'FeatureCollection', features: departements};

// Emprise de la carte en vue « France entière » (pixels de la vidéo 1080×1920).
export const MAP_BOX = {x0: 90, y0: 360, x1: 990, y1: 1260};
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
		franceFc,
	);

const path = geoPath(projection);
export const departementPaths = departements.map((d) => path(d) ?? '');
export const neighbourPaths = neighbours.map((n) => path(n) ?? '');

export type Pt = {x: number; y: number};

export const project = (c: LonLat): Pt => {
	const [x, y] = projection(c) ?? [0, 0];
	return {x, y};
};

const EARTH_RADIUS_KM = 6371.0088; // rayon moyen IUGG
const RAD = Math.PI / 180;

/** Distance orthodromique (formule de haversine), en km. */
export const haversineKm = ([lon1, lat1]: LonLat, [lon2, lat2]: LonLat): number => {
	const dLat = (lat2 - lat1) * RAD;
	const dLon = (lon2 - lon1) * RAD;
	const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * RAD) * Math.cos(lat2 * RAD) * Math.sin(dLon / 2) ** 2;
	return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(a));
};

/** Cap vrai initial de a vers b, en degrés [0, 360[. */
export const bearing = ([lon1, lat1]: LonLat, [lon2, lat2]: LonLat): number => {
	const y = Math.sin((lon2 - lon1) * RAD) * Math.cos(lat2 * RAD);
	const x = Math.cos(lat1 * RAD) * Math.sin(lat2 * RAD) - Math.sin(lat1 * RAD) * Math.cos(lat2 * RAD) * Math.cos((lon2 - lon1) * RAD);
	return ((Math.atan2(y, x) / RAD) + 360) % 360;
};

/** Point atteint depuis `a` en suivant le cap `deg` sur `km` kilomètres. */
export const destination = ([lon, lat]: LonLat, deg: number, km: number): LonLat => {
	const d = km / EARTH_RADIUS_KM;
	const t = deg * RAD;
	const lat2 = Math.asin(Math.sin(lat * RAD) * Math.cos(d) + Math.cos(lat * RAD) * Math.sin(d) * Math.cos(t));
	const lon2 = lon * RAD + Math.atan2(Math.sin(t) * Math.sin(d) * Math.cos(lat * RAD), Math.cos(d) - Math.sin(lat * RAD) * Math.sin(lat2));
	return [lon2 / RAD, lat2 / RAD];
};

export const lerpLonLat = (a: LonLat, b: LonLat, t: number): LonLat => geoInterpolate(a, b)(t) as LonLat;

export const angleDiff = (a: number, b: number) => Math.abs(((a - b + 540) % 360) - 180);

/** Polyligne avec abscisses curvilignes pré-calculées. */
export type Line = {pts: Pt[]; lens: number[]; total: number};

export const makeLine = (pts: Pt[]): Line => {
	const lens = [0];
	for (let i = 1; i < pts.length; i++) lens.push(lens[i - 1] + Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y));
	return {pts, lens, total: lens[lens.length - 1]};
};

const indexAt = (line: Line, target: number) => {
	let lo = 1;
	let hi = line.pts.length - 1;
	while (lo < hi) {
		const mid = (lo + hi) >> 1;
		if (line.lens[mid] < target) lo = mid + 1;
		else hi = mid;
	}
	return lo;
};

/** Position et orientation (degrés écran) pour t ∈ [0, 1]. */
export const along = (line: Line, t: number): Pt & {angle: number} => {
	const target = Math.min(Math.max(t, 0), 1) * line.total;
	const i = Math.max(indexAt(line, target), 1);
	const a = line.pts[i - 1];
	const b = line.pts[i] ?? a;
	const seg = line.lens[i] - line.lens[i - 1] || 1;
	const k = (target - line.lens[i - 1]) / seg;
	return {x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, angle: (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI};
};

/** Orientation lissée : direction entre deux points encadrant t (fenêtre `w`). */
export const smoothAngle = (line: Line, t: number, w: number) => {
	const a = along(line, Math.max(t - w, 0));
	const b = along(line, Math.min(t + w, 1));
	if (Math.hypot(b.x - a.x, b.y - a.y) < 1e-9) return along(line, t).angle;
	return (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
};

/** Sous-polyligne de 0 à t. */
export const partial = (line: Line, t: number): Pt[] => {
	if (t <= 0) return [line.pts[0]];
	if (t >= 1) return line.pts;
	const target = t * line.total;
	const i = indexAt(line, target);
	return [...line.pts.slice(0, i), along(line, t)];
};

export const cubic = (p0: Pt, p1: Pt, p2: Pt, p3: Pt, n: number): Pt[] =>
	Array.from({length: n + 1}, (_, i) => {
		const t = i / n;
		const u = 1 - t;
		return {
			x: u * u * u * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t * t * t * p3.x,
			y: u * u * u * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t * t * t * p3.y,
		};
	});

export const bbox = (pts: Pt[]) => {
	const xs = pts.map((p) => p.x);
	const ys = pts.map((p) => p.y);
	return {x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys)};
};

/** Pixels de la carte de base par kilomètre, autour d'un point. */
export const pxPerKm = (c: LonLat) => {
	const a = project(c);
	const b = project(destination(c, 90, 10));
	return Math.hypot(b.x - a.x, b.y - a.y) / 10;
};

export const formatDuration = (min: number) => {
	const m = Math.round(min);
	const h = Math.floor(m / 60);
	const r = m % 60;
	if (h === 0) return `${r} MIN`;
	return `${h} H ${String(r).padStart(2, '0')}`;
};

export const formatClock = (min: number) => {
	const s = Math.max(0, Math.round(min * 60));
	return `${String(Math.floor(s / 3600)).padStart(1, '0')}:${String(Math.floor((s % 3600) / 60)).padStart(2, '0')}`;
};

export const fmt = (n: number) => Math.round(n).toLocaleString('fr-FR').replace(/ | /g, ' ');
export const formatKm = (km: number, digits = 0) =>
	`${digits ? km.toLocaleString('fr-FR', {minimumFractionDigits: digits, maximumFractionDigits: digits}).replace(/ | /g, ' ') : fmt(km)} KM`;

/** Cap vrai (degrés) d'un mobile situé en `p` (carte de base) et orienté selon `angleDeg` à l'écran. */
export const trueHeading = (p: Pt, angleDeg: number): number => {
	const a = projection.invert?.([p.x, p.y]);
	const r = (angleDeg * Math.PI) / 180;
	const b = projection.invert?.([p.x + Math.cos(r) * 0.5, p.y + Math.sin(r) * 0.5]);
	if (!a || !b) return 0;
	return bearing(a as LonLat, b as LonLat);
};
