import {Easing, interpolate} from 'remotion';
import {GAMES, PLACES, START, type Game, type LonLat} from '../data/tour';
import {MAP_BOX, MAP_CENTER, flightEstimate, greatCircle, project, roadCurve, roadEstimate, type Pt} from './geo';

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

// Durées fixes (images)
const INTRO = 60;
const FOCUS = 30;
const ZOOM_IN = 24;
const RESULT = 66;
const FINAL_ZOOM = 40;
const FINAL_HOLD = 80;
const FINAL_LIST = 100;
const FINAL_STATS = 100;
const FINAL_NEXT = 150;

// La durée d'animation du vol est proportionnelle à la distance réelle.
const flightFrames = (km: number) => Math.round(interpolate(km, [0, 800], [40, 105], {extrapolateRight: 'clamp'}));
const busFrames = (km: number) => Math.round(interpolate(km, [0, 30], [34, 52], {extrapolateRight: 'clamp'}));

/** Vue caméra : point (x, y) de la carte de base placé en (MAP_CENTER.x, sy) à l'échelle k. */
export type View = {x: number; y: number; k: number; sy: number};

export const FULL_VIEW: View = {x: MAP_CENTER.x, y: MAP_CENTER.y, k: 1, sy: MAP_CENTER.y};
// Vue finale réduite : la France dans la partie haute, le bilan en dessous.
export const COMPACT_VIEW: View = {x: MAP_CENTER.x, y: MAP_CENTER.y, k: 0.64, sy: 690};

const fit = (pts: Pt[], w: number, h: number, sy: number, minK: number, maxK: number): View => {
	const xs = pts.map((p) => p.x);
	const ys = pts.map((p) => p.y);
	const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
	const k = Math.min(Math.max(Math.min(w / Math.max(x1 - x0, 1e-6), h / Math.max(y1 - y0, 1e-6)), minK), maxK);
	return {x: (x0 + x1) / 2, y: (y0 + y1) / 2, k, sy};
};

export type Leg = {
	index: number;
	game: Game;
	/** Numéro de victoire dans la série (null si match à venir / défaite) */
	winNumber: number | null;
	from: LonLat;
	airport: LonLat;
	arena: LonLat;
	flight: {km: number; minutes: number; pts: Pt[]; fromName: string; toName: string};
	bus: {km: number; minutes: number; pts: Pt[]; fromName: string; toName: string};
	focusStart: number;
	flightStart: number;
	zoomStart: number;
	busStart: number;
	resultStart: number;
	end: number;
	views: {flight: View; bus: View; result: View};
};

const buildLegs = () => {
	let frame = INTRO;
	let fromId = START;
	let wins = 0;
	return GAMES.map((game, index): Leg => {
		const from = PLACES[fromId].coords as LonLat;
		const airport = PLACES[game.airport].coords as LonLat;
		const arena = PLACES[game.arena].coords as LonLat;
		const flight = {...flightEstimate(from, airport), pts: greatCircle(from, airport), fromName: PLACES[fromId].name, toName: PLACES[game.airport].name};
		const bus = {...roadEstimate(airport, arena), pts: roadCurve(airport, arena), fromName: PLACES[game.airport].name, toName: PLACES[game.arena].name};
		const isWin = game.score !== null && game.score.asvel > game.score.opponent;
		if (isWin) wins++;

		const focusStart = frame;
		const flightStart = focusStart + FOCUS;
		const zoomStart = flightStart + flightFrames(flight.km);
		const busStart = zoomStart + ZOOM_IN;
		const resultStart = busStart + busFrames(bus.km);
		const end = resultStart + RESULT;
		frame = end;
		fromId = game.airport;

		const arenaPt = project(arena);
		return {
			index,
			game,
			winNumber: isWin ? wins : null,
			from,
			airport,
			arena,
			flight,
			bus,
			focusStart,
			flightStart,
			zoomStart,
			busStart,
			resultStart,
			end,
			views: {
				// Cadrage décalé vers le bas pour laisser le bandeau de trajet libre au-dessus.
				flight: fit(flight.pts, 700, 660, MAP_CENTER.y + 50, 1, 2.4),
				bus: fit(bus.pts, 560, 560, MAP_CENTER.y, 20, 260),
				result: {x: arenaPt.x, y: arenaPt.y, k: 2.6, sy: MAP_CENTER.y},
			},
		};
	});
};

export const LEGS = buildLegs();
export const TOTAL_WINS = LEGS.filter((l) => l.winNumber !== null).length;

const tourEnd = LEGS[LEGS.length - 1].end;
export const FINAL = {
	zoom: tourEnd,
	hold: tourEnd + FINAL_ZOOM,
	list: tourEnd + FINAL_ZOOM + FINAL_HOLD,
	stats: tourEnd + FINAL_ZOOM + FINAL_HOLD + FINAL_LIST,
	next: tourEnd + FINAL_ZOOM + FINAL_HOLD + FINAL_LIST + FINAL_STATS,
};
export const DURATION = FINAL.next + FINAL_NEXT;

// ── Caméra ───────────────────────────────────────────────────────────────────
type Key = {frame: number; view: View};

const KEYS: Key[] = (() => {
	const keys: Key[] = [
		{frame: 0, view: {...FULL_VIEW, k: 0.92}},
		{frame: INTRO, view: FULL_VIEW},
	];
	for (const leg of LEGS) {
		keys.push({frame: leg.flightStart, view: leg.views.flight});
		keys.push({frame: leg.zoomStart, view: leg.views.flight});
		keys.push({frame: leg.busStart, view: leg.views.bus});
		keys.push({frame: leg.resultStart, view: leg.views.bus});
		keys.push({frame: leg.resultStart + 40, view: leg.views.result});
		keys.push({frame: leg.end, view: leg.views.result});
	}
	keys.push({frame: FINAL.hold, view: FULL_VIEW});
	keys.push({frame: FINAL.list, view: FULL_VIEW});
	keys.push({frame: FINAL.list + 30, view: COMPACT_VIEW});
	return keys;
})();

const ease = Easing.inOut(Easing.cubic);

export const cameraAt = (frame: number): View => {
	if (frame <= KEYS[0].frame) return KEYS[0].view;
	for (let i = 1; i < KEYS.length; i++) {
		const a = KEYS[i - 1];
		const b = KEYS[i];
		if (frame <= b.frame) {
			const t = ease((frame - a.frame) / Math.max(b.frame - a.frame, 1));
			// Interpolation logarithmique de l'échelle, et du centre en coordonnées
			// écran pour éviter les embardées pendant les grands zooms.
			const k = Math.exp(Math.log(a.view.k) + (Math.log(b.view.k) - Math.log(a.view.k)) * t);
			const w = a.view.k === b.view.k ? t : (1 / a.view.k - 1 / k) / (1 / a.view.k - 1 / b.view.k);
			return {
				k,
				x: a.view.x + (b.view.x - a.view.x) * w,
				y: a.view.y + (b.view.y - a.view.y) * w,
				sy: a.view.sy + (b.view.sy - a.view.sy) * t,
			};
		}
	}
	return KEYS[KEYS.length - 1].view;
};

export const toScreen = (p: Pt, v: View): Pt => ({x: (p.x - v.x) * v.k + MAP_CENTER.x, y: (p.y - v.y) * v.k + v.sy});

export const mapTransform = (v: View) => `translate(${MAP_CENTER.x} ${v.sy}) scale(${v.k}) translate(${-v.x} ${-v.y})`;

export {MAP_BOX};
