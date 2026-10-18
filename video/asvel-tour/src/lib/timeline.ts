import {Easing, interpolate} from 'remotion';
import routesData from '../data/routes.json';
import {AIRPORTS, GAMES, HOME_AIRPORT, PLACES, type AirportId, type Game, type LonLat, type PlaceId} from '../data/tour';
import {AIRCRAFT, makeProfile, planFlight, type FlightPlan} from './aviation';
import {
	MAP_CENTER,
	along,
	angleDiff,
	bearing,
	bbox,
	cubic,
	destination,
	lerpLonLat,
	makeLine,
	project,
	pxPerKm,
	type Line,
	type Pt,
} from './geo';

export const FPS = 60;
export const WIDTH = 1080;
export const HEIGHT = 1920;

// ── Durées (images à 60 i/s) ────────────────────────────────────────────────
const INTRO = 180;
const STAGE = 60;
const RESULT = 110;
const UPCOMING = 210;
const BASE_HOLD = 50;
const CAM = 24; // transition caméra au début de chaque segment
const FINAL = {zoom: 60, stats: 500};

const busFrames = (km: number) => Math.round(Math.min(Math.max(70 + km * 0.7, 80), 150));
const airFrames = (km: number) => Math.round(105 + km * 0.12);
const FLIGHT_PHASES = {align: 20, roll: 40, climb: 26, approach: 44, rollout: 36, hold: 6};

// ── Caméra ──────────────────────────────────────────────────────────────────
/** Vue : point (x, y) de la carte de base placé en (MAP_CENTER.x, sy), à l'échelle k. */
export type View = {x: number; y: number; k: number; sy: number};
const MAP_SY = 800;
export const FULL_VIEW: View = {x: MAP_CENTER.x, y: MAP_CENTER.y, k: 1, sy: MAP_SY};
export const COMPACT_VIEW: View = {x: MAP_CENTER.x, y: MAP_CENTER.y, k: 0.6, sy: 640};

const fit = (pts: Pt[], w: number, h: number, minK: number, maxK: number, sy = MAP_SY): View => {
	const b = bbox(pts);
	const k = Math.min(Math.max(Math.min(w / Math.max(b.x1 - b.x0, 1e-6), h / Math.max(b.y1 - b.y0, 1e-6)), minK), maxK);
	return {x: (b.x0 + b.x1) / 2, y: (b.y0 + b.y1) / 2, k, sy};
};

// ── Types de segments ───────────────────────────────────────────────────────
export type Tone = 'aller' | 'retour' | 'upcoming';

type Base = {start: number; end: number; stage: number; game: Game};

export type BusSeg = Base & {
	kind: 'bus';
	from: PlaceId;
	to: PlaceId;
	tone: Tone;
	line: Line;
	km: number;
	minutes: number;
	/** début / fin du déplacement (après la transition caméra) */
	moveStart: number;
	moveEnd: number;
	banner: 'depart' | 'retour-bus' | null;
	arrivesAtBase: boolean;
};

export type FlightSeg = Base & {
	kind: 'flight';
	tone: Tone;
	plan: FlightPlan;
	profile: ReturnType<typeof makeProfile>;
	depRunway: string;
	arrRunway: string;
	lines: {roll: Line; climb: Line; air: Line; approach: Line; rollout: Line; all: Line};
	/** longueurs (base) pour la fraction de distance en vol */
	airLen: {climb: number; air: number; approach: number};
	t: {rollStart: number; climbStart: number; airStart: number; approachStart: number; rolloutStart: number; stop: number};
	views: {dep: View; air: View; app: View; arr: View};
};

export type ResultSeg = Base & {kind: 'result'; winNumber: number | null};
export type UpcomingSeg = Base & {kind: 'upcoming'};
export type StageSeg = Base & {kind: 'stage'};
export type Seg = BusSeg | FlightSeg | ResultSeg | UpcomingSeg | StageSeg;

type RouteRec = {distanceM: number; durationS: number; coords: [number, number][]};
const ROUTES = routesData.routes as unknown as Record<string, RouteRec>;
/** OSRM fournit des durées pour une voiture ; un autocar roule ≈ 15 % moins vite. */
const COACH_FACTOR = 1.15;

const projLine = (coords: LonLat[]) => makeLine(coords.map(project));

// ── Construction d'un vol ───────────────────────────────────────────────────
const runwayFor = (id: AirportId, headingWanted: number) => {
	const rw = AIRPORTS[id].runway;
	const e0 = rw.ends[0] as LonLat;
	const e1 = rw.ends[1] as LonLat;
	const h01 = bearing(e0, e1);
	const h10 = bearing(e1, e0);
	// Sens retenu : le plus proche de l'axe du vol (le vent réel déciderait du QFU)
	return angleDiff(h01, headingWanted) <= angleDiff(h10, headingWanted)
		? {threshold: e0, far: e1, heading: h01, id: rw.ids[0], lengthKm: rw.lengthM / 1000}
		: {threshold: e1, far: e0, heading: h10, id: rw.ids[1], lengthKm: rw.lengthM / 1000};
};

const dirPx = (c: LonLat, heading: number): Pt => {
	const a = project(c);
	const b = project(destination(c, heading, 10));
	const n = Math.hypot(b.x - a.x, b.y - a.y);
	return {x: (b.x - a.x) / n, y: (b.y - a.y) / n};
};

const buildFlight = (from: AirportId, to: AirportId, plan: FlightPlan) => {
	const gcHeading = bearing(AIRPORTS[from].arp as LonLat, AIRPORTS[to].arp as LonLat);
	const dep = runwayFor(from, gcHeading);
	const arr = runwayFor(to, gcHeading);

	const liftoff = destination(dep.threshold, dep.heading, 1.3); // roulage ≈ 1 300 m
	const climbOut = destination(dep.far, dep.heading, 5);
	const faf = destination(arr.threshold, (arr.heading + 180) % 360, 8); // approche finale 8 km
	const touchdown = destination(arr.threshold, arr.heading, 0.35);
	const stop = destination(arr.threshold, arr.heading, 1.5);

	const roll = projLine([dep.threshold, liftoff]);
	const climb = projLine([liftoff, lerpLonLat(liftoff, dep.far, 0.5), dep.far, climbOut]);

	const p0 = project(climbOut);
	const p3 = project(faf);
	const d = Math.hypot(p3.x - p0.x, p3.y - p0.y);
	const L = Math.min(d * 0.3, 70 * pxPerKm(climbOut));
	const u0 = dirPx(climbOut, dep.heading);
	const u3 = dirPx(faf, arr.heading);
	const raw = cubic(p0, {x: p0.x + u0.x * L, y: p0.y + u0.y * L}, {x: p3.x - u3.x * L, y: p3.y - u3.y * L}, p3, 140);
	// Séparation latérale des couloirs aller / retour (≈ 4 km à droite du sens de vol)
	const off = 4 * pxPerKm(climbOut);
	const air = makeLine(
		raw.map((p, i) => {
			const a = raw[Math.max(i - 1, 0)];
			const b = raw[Math.min(i + 1, raw.length - 1)];
			const n = Math.hypot(b.x - a.x, b.y - a.y) || 1;
			const s = Math.sin((Math.PI * i) / (raw.length - 1)) * off;
			return {x: p.x - ((b.y - a.y) / n) * s, y: p.y + ((b.x - a.x) / n) * s};
		}),
	);
	const approach = projLine([faf, arr.threshold, touchdown]);
	const rollout = projLine([touchdown, stop]);
	const all = makeLine([...roll.pts, ...climb.pts.slice(1), ...air.pts.slice(1), ...approach.pts.slice(1), ...rollout.pts.slice(1)]);

	const runwayView = (rw: typeof dep): View => {
		const a = project(rw.threshold);
		const b = project(rw.far);
		const len = Math.hypot(b.x - a.x, b.y - a.y);
		return {x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, k: 500 / len, sy: MAP_SY};
	};

	return {
		depRunway: dep.id,
		arrRunway: arr.id,
		lines: {roll, climb, air, approach, rollout, all},
		airLen: {climb: climb.total, air: air.total, approach: approach.total},
		views: {
			dep: runwayView(dep),
			arr: runwayView(arr),
			air: fit([...climb.pts, ...air.pts, ...approach.pts], 860, 740, 1, 4),
			// Approche : l'avion (au repère d'approche finale) et la piste dans le même cadre
			app: fit([project(faf), project(arr.threshold), project(arr.far)], 700, 600, 1, 400),
		},
	};
};

// ── Séquence complète ───────────────────────────────────────────────────────
const build = () => {
	const segs: Seg[] = [];
	let frame = INTRO;
	let wins = 0;
	let flightNo = 101;

	const bus = (game: Game, stage: number, from: PlaceId, to: PlaceId, tone: Tone, banner: BusSeg['banner']) => {
		const rec = ROUTES[`${from}>${to}`];
		if (!rec) throw new Error(`Itinéraire routier manquant : ${from}>${to} (npm run fetch:routes)`);
		const km = rec.distanceM / 1000;
		const arrivesAtBase = to === 'BASE';
		const moveStart = frame + CAM;
		const moveEnd = moveStart + busFrames(km);
		const end = moveEnd + (arrivesAtBase ? BASE_HOLD : 12);
		segs.push({
			kind: 'bus', start: frame, end, stage, game, from, to, tone, banner, arrivesAtBase,
			line: projLine(rec.coords as LonLat[]),
			km,
			minutes: (rec.durationS / 60) * COACH_FACTOR,
			moveStart,
			moveEnd,
		});
		frame = end;
	};

	const flight = (game: Game, stage: number, from: AirportId, to: AirportId, direction: FlightPlan['direction']) => {
		const plan = planFlight(from, to, direction, `ASVEL ${flightNo++}`);
		const geo = buildFlight(from, to, plan);
		const P = FLIGHT_PHASES;
		const rollStart = frame + P.align;
		const climbStart = rollStart + P.roll;
		const airStart = climbStart + P.climb;
		const approachStart = airStart + airFrames(plan.gcKm);
		const rolloutStart = approachStart + P.approach;
		const stop = rolloutStart + P.rollout;
		const end = stop + P.hold;
		segs.push({
			kind: 'flight', start: frame, end, stage, game, plan, profile: makeProfile(plan),
			tone: direction === 'ALLER' ? 'aller' : 'retour',
			...geo,
			t: {rollStart, climbStart, airStart, approachStart, rolloutStart, stop},
		});
		frame = end;
	};

	GAMES.forEach((game, i) => {
		const stage = i + 1;
		segs.push({kind: 'stage', start: frame, end: frame + STAGE, stage, game});
		frame += STAGE;
		const upcoming = game.score === null;
		if (game.airport) {
			bus(game, stage, 'BASE', AIRPORTS[HOME_AIRPORT].terminal, 'aller', 'depart');
			flight(game, stage, HOME_AIRPORT, game.airport, 'ALLER');
			bus(game, stage, AIRPORTS[game.airport].terminal, game.arena, upcoming ? 'upcoming' : 'aller', null);
		} else {
			bus(game, stage, 'BASE', game.arena, upcoming ? 'upcoming' : 'aller', 'depart');
		}
		if (upcoming) {
			segs.push({kind: 'upcoming', start: frame, end: frame + UPCOMING, stage, game});
			frame += UPCOMING;
			return;
		}
		const won = game.score!.asvel > game.score!.opponent;
		if (won) wins++;
		segs.push({kind: 'result', start: frame, end: frame + RESULT, stage, game, winNumber: won ? wins : null});
		frame += RESULT;
		if (game.airport) {
			bus(game, stage, game.arena, AIRPORTS[game.airport].terminal, 'retour', 'retour-bus');
			flight(game, stage, game.airport, HOME_AIRPORT, 'RETOUR');
			bus(game, stage, AIRPORTS[HOME_AIRPORT].terminal, 'BASE', 'retour', null);
		} else {
			bus(game, stage, game.arena, 'BASE', 'retour', 'retour-bus');
		}
	});
	return {segs, tourEnd: frame};
};

const built = build();
export const SEGS = built.segs;
export const BUSES = SEGS.filter((s): s is BusSeg => s.kind === 'bus');
export const FLIGHTS = SEGS.filter((s): s is FlightSeg => s.kind === 'flight');
export const RESULTS = SEGS.filter((s): s is ResultSeg => s.kind === 'result');
export const WINS = RESULTS.filter((r) => r.winNumber !== null);
export const UPCOMINGS = SEGS.filter((s): s is UpcomingSeg => s.kind === 'upcoming');
export const TOTAL_WINS = WINS.length;

export const FINAL_T = {
	zoom: built.tourEnd,
	stats: built.tourEnd + FINAL.zoom,
	end: built.tourEnd + FINAL.zoom + FINAL.stats,
};
export const DURATION = FINAL_T.end;

export const segAt = (frame: number) => SEGS.find((s) => frame >= s.start && frame < s.end);

// ── Images-clés de caméra ───────────────────────────────────────────────────
type Key = {frame: number; view: View};

const KEYS: Key[] = (() => {
	const keys: Key[] = [
		{frame: 0, view: {...FULL_VIEW, k: 0.9}},
		{frame: INTRO - 20, view: FULL_VIEW},
	];
	const last = () => keys[keys.length - 1].view;
	for (const s of SEGS) {
		keys.push({frame: s.start, view: last()});
		if (s.kind === 'stage') {
			keys.push({frame: s.start + 36, view: FULL_VIEW});
		} else if (s.kind === 'bus') {
			keys.push({frame: s.moveStart, view: fit(s.line.pts, 860, 720, 2, 400)});
		} else if (s.kind === 'flight') {
			keys.push({frame: s.t.rollStart + 10, view: s.views.dep});
			keys.push({frame: s.t.climbStart + 6, view: s.views.dep});
			keys.push({frame: s.t.airStart + 60, view: s.views.air});
			keys.push({frame: s.t.approachStart - 46, view: s.views.air});
			keys.push({frame: s.t.approachStart, view: s.views.app});
			keys.push({frame: s.t.rolloutStart + 6, view: s.views.arr});
		} else {
			const p = project(PLACES[s.game.arena].coords as LonLat);
			keys.push({frame: s.start + 50, view: {x: p.x, y: p.y, k: 2.4, sy: MAP_SY}});
		}
		keys.push({frame: s.end, view: last()});
	}
	keys.push({frame: FINAL_T.zoom + FINAL.zoom, view: FULL_VIEW});
	keys.push({frame: FINAL_T.stats + 70, view: FULL_VIEW});
	keys.push({frame: FINAL_T.stats + 110, view: COMPACT_VIEW});
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
			// Échelle interpolée en logarithme ; centre pondéré pour garder un
			// mouvement apparent régulier pendant les grands zooms.
			const k = Math.exp(Math.log(a.view.k) + (Math.log(b.view.k) - Math.log(a.view.k)) * t);
			const w = Math.abs(a.view.k - b.view.k) < 1e-6 ? t : (1 / a.view.k - 1 / k) / (1 / a.view.k - 1 / b.view.k);
			return {k, x: a.view.x + (b.view.x - a.view.x) * w, y: a.view.y + (b.view.y - a.view.y) * w, sy: a.view.sy + (b.view.sy - a.view.sy) * t};
		}
	}
	return KEYS[KEYS.length - 1].view;
};

export const toScreen = (p: Pt, v: View): Pt => ({x: (p.x - v.x) * v.k + MAP_CENTER.x, y: (p.y - v.y) * v.k + v.sy});
export const mapTransform = (v: View) => `translate(${MAP_CENTER.x} ${v.sy}) scale(${v.k}) translate(${-v.x} ${-v.y})`;

// ── État de l'avion ─────────────────────────────────────────────────────────
const clamp01 = (x: number) => Math.min(Math.max(x, 0), 1);
const smooth = (x: number) => x * x * (3 - 2 * x);

export type PlaneState = {
	pos: Pt;
	angle: number;
	/** 0 au sol, 1 en croisière */
	alt: number;
	/** 1 = train sorti */
	gear: number;
	speedKmh: number;
	/** fraction de la distance en vol (décollage → toucher) */
	f: number;
	elapsedMin: number;
	fuelL: number;
	phase: 'ALIGNEMENT' | 'DÉCOLLAGE' | 'MONTÉE' | 'CROISIÈRE' | 'DESCENTE' | 'APPROCHE' | 'ATTERRISSAGE' | 'ROULAGE';
	/** fraction de la trajectoire complète déjà parcourue (pour le tracé) */
	travelled: number;
};

const planeRaw = (s: FlightSeg, frame: number): Omit<PlaneState, 'travelled'> & {seg: number; u: number} => {
	const {t, lines, airLen, plan, profile} = s;
	const total = airLen.climb + airLen.air + airLen.approach;
	const airborneFuel = plan.fuelL - plan.taxiOutFuelL - plan.taxiInFuelL;
	const fuelAt = (f: number) => plan.taxiOutFuelL + airborneFuel * (profile.elapsedAt(f) / plan.airborneMin);
	const altOf = (f: number) => smooth(clamp01(Math.min(f / 0.16, (1 - f) / 0.2)));
	const base = (pos: Pt & {angle: number}, f: number, phase: PlaneState['phase'], speed: number, gear: number): Omit<PlaneState, 'travelled'> => ({
		pos,
		angle: pos.angle,
		alt: altOf(f),
		gear,
		speedKmh: speed,
		f,
		elapsedMin: profile.elapsedAt(f),
		fuelL: fuelAt(f),
		phase,
	});

	if (frame < t.rollStart) {
		const p = along(lines.roll, 0);
		const a = along(lines.roll, 0.02);
		return {...base({...p, angle: a.angle}, 0, 'ALIGNEMENT', 0, 1), fuelL: plan.taxiOutFuelL, seg: 0, u: 0};
	}
	if (frame < t.climbStart) {
		const u = (frame - t.rollStart) / (t.climbStart - t.rollStart);
		const p = along(lines.roll, u * u);
		return {...base(p, 0, 'DÉCOLLAGE', AIRCRAFT.rotationKmh * u, 1), alt: 0, seg: 0, u: u * u};
	}
	if (frame < t.airStart) {
		const u = (frame - t.climbStart) / (t.airStart - t.climbStart);
		const f = (u * airLen.climb) / total;
		return {...base(along(lines.climb, u), f, 'MONTÉE', profile.speedAt(f), 1 - clamp01(u * 2.2)), seg: 1, u};
	}
	if (frame < t.approachStart) {
		const u = Easing.inOut(Easing.sin)((frame - t.airStart) / (t.approachStart - t.airStart));
		const f = (airLen.climb + u * airLen.air) / total;
		const phase = f < 0.2 ? 'MONTÉE' : f > 0.78 ? 'DESCENTE' : 'CROISIÈRE';
		return {...base(along(lines.air, u), f, phase, profile.speedAt(f), 0), seg: 2, u};
	}
	if (frame < t.rolloutStart) {
		const u = (frame - t.approachStart) / (t.rolloutStart - t.approachStart);
		const f = (airLen.climb + airLen.air + u * airLen.approach) / total;
		return {...base(along(lines.approach, u), f, 'APPROCHE', profile.speedAt(f), clamp01((u - 0.05) * 3)), seg: 3, u};
	}
	const u = clamp01((frame - t.rolloutStart) / (t.stop - t.rolloutStart));
	const e = 1 - (1 - u) * (1 - u);
	const p = along(lines.rollout, e);
	return {
		pos: p,
		angle: p.angle,
		alt: 0,
		gear: 1,
		speedKmh: interpolate(u, [0, 1], [AIRCRAFT.touchdownKmh, 25]),
		f: 1,
		elapsedMin: plan.airborneMin,
		fuelL: plan.fuelL - plan.taxiInFuelL + plan.taxiInFuelL * u,
		phase: u < 1 ? 'ATTERRISSAGE' : 'ROULAGE',
		seg: 4,
		u: e,
	};
};

export const planeAt = (s: FlightSeg, frame: number): PlaneState => {
	const {seg, u, ...st} = planeRaw(s, frame);
	const L = s.lines;
	const parts = [L.roll.total, L.climb.total, L.air.total, L.approach.total, L.rollout.total];
	const done = parts.slice(0, seg).reduce((a, b) => a + b, 0) + parts[seg] * u;
	return {...st, travelled: done / L.all.total};
};

// ── État de l'autocar ───────────────────────────────────────────────────────
/** Progression du car : accélération douce, arrêt progressif. */
export const busProgress = (s: BusSeg, frame: number) => {
	const u = clamp01((frame - s.moveStart) / (s.moveEnd - s.moveStart));
	return Easing.bezier(0.42, 0, 0.22, 1)(u);
};
