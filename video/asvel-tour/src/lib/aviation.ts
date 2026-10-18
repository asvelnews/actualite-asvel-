// ─────────────────────────────────────────────────────────────────────────────
// Modèle de vol simplifié – Embraer ERJ 145 (version LR).
// Toutes les valeurs produites sont des ESTIMATIONS, affichées comme telles.
// Hypothèses (voir README) :
// - Croisière : 780 km/h vraie (≈ Mach 0,72 au FL310 ; Mach 0,78 maxi constructeur).
// - Distance parcourue = orthodromie × 1,05 (routes aériennes, procédures).
// - Pénalité montée / descente / approche : +14 min sur le temps en vol.
// - Vent moyen en altitude : 50 km/h d'ouest (270°), différencie aller et retour.
// - Roulage : 12 min au départ de LYS, 8 min ailleurs ; 6 min / 5 min à l'arrivée.
// - Consommation : 1 090 kg/h en vol (≈ 359 gal US/h, donnée courtier),
//   6 kg/min au roulage ; densité Jet A-1 0,803 kg/L (référence Embraer).
// - Prix Jet A-1 : 1,20 à 1,80 €/L HT (tarifs publics Air BP 2026 relevés
//   entre 1,60 et 1,92 €/L HT ; les opérateurs sous contrat paient moins).
// - Affrètement (carburant INCLUS) : 5 000 à 7 500 € par heure bloc,
//   minimum 1 h facturée par vol, + 0,75 h de repositionnement par vol,
//   + 1 000 à 2 000 € de redevances aéroportuaires et d'assistance par vol,
//   + 1 000 à 1 800 € d'immobilisation (attente du match, équipage) au retour.
// ─────────────────────────────────────────────────────────────────────────────
import {AIRPORTS, type AirportId, type LonLat} from '../data/tour';
import {bearing, haversineKm} from './geo';

export const AIRCRAFT = {
	model: 'EMBRAER ERJ 145',
	cruiseKmh: 780,
	routeFactor: 1.05,
	climbDescentMin: 14,
	burnKgH: 1090,
	taxiBurnKgMin: 6,
	densityKgL: 0.803,
	rotationKmh: 250,
	touchdownKmh: 240,
};

const WIND = {fromDeg: 270, kmh: 50};
const FUEL_EUR_L: [number, number] = [1.2, 1.8];
const RATE_EUR_H: [number, number] = [5000, 7500];
const MIN_BILLED_H = 1;
const REPOSITION_H = 0.75;
const FEES_EUR: [number, number] = [1000, 2000];
const NIGHT_STOP_EUR: [number, number] = [1000, 1800];

const taxiOut = (a: AirportId) => (a === 'LYS' ? 12 : 8);
const taxiIn = (a: AirportId) => (a === 'LYS' ? 6 : 5);

export type Range = [number, number];
const round100 = (x: number) => Math.round(x / 100) * 100;
const mul = (r: Range, k: number): Range => [r[0] * k, r[1] * k];
const add = (...rs: Range[]): Range => rs.reduce<Range>((s, r) => [s[0] + r[0], s[1] + r[1]], [0, 0]);
const r100 = (r: Range): Range => [round100(r[0]), round100(r[1])];

export type FlightPlan = {
	number: string;
	direction: 'ALLER' | 'RETOUR';
	from: AirportId;
	to: AirportId;
	/** Distance orthodromique entre points de référence (km) */
	gcKm: number;
	trackDeg: number;
	/** Composante de vent (positive = arrière) */
	windKmh: number;
	groundSpeedKmh: number;
	airborneMin: number;
	blockMin: number;
	fuelKg: number;
	fuelL: number;
	taxiOutFuelL: number;
	taxiInFuelL: number;
	fuelCost: Range;
	charter: Range;
};

export const planFlight = (from: AirportId, to: AirportId, direction: FlightPlan['direction'], number: string): FlightPlan => {
	const a = AIRPORTS[from].arp as LonLat;
	const b = AIRPORTS[to].arp as LonLat;
	const gcKm = haversineKm(a, b);
	const trackDeg = bearing(a, b);
	const windTo = (WIND.fromDeg + 180) % 360;
	const windKmh = WIND.kmh * Math.cos(((trackDeg - windTo) * Math.PI) / 180);
	const groundSpeedKmh = AIRCRAFT.cruiseKmh + windKmh;
	const airborneMin = ((gcKm * AIRCRAFT.routeFactor) / groundSpeedKmh) * 60 + AIRCRAFT.climbDescentMin;
	const tOut = taxiOut(from);
	const tIn = taxiIn(to);
	const blockMin = airborneMin + tOut + tIn;
	const fuelKg = (airborneMin / 60) * AIRCRAFT.burnKgH + (tOut + tIn) * AIRCRAFT.taxiBurnKgMin;
	const fuelL = fuelKg / AIRCRAFT.densityKgL;
	const billedH = Math.max(MIN_BILLED_H, blockMin / 60) + REPOSITION_H;
	const charter = r100(add(mul(RATE_EUR_H, billedH), FEES_EUR, direction === 'RETOUR' ? NIGHT_STOP_EUR : [0, 0]));
	return {
		number,
		direction,
		from,
		to,
		gcKm,
		trackDeg,
		windKmh,
		groundSpeedKmh,
		airborneMin,
		blockMin,
		fuelKg,
		fuelL,
		taxiOutFuelL: (tOut * AIRCRAFT.taxiBurnKgMin) / AIRCRAFT.densityKgL,
		taxiInFuelL: (tIn * AIRCRAFT.taxiBurnKgMin) / AIRCRAFT.densityKgL,
		fuelCost: r100(mul(FUEL_EUR_L, fuelL)),
		charter,
	};
};

export const FUEL_PRICE = FUEL_EUR_L;
export const sumRanges = (rs: Range[]) => add(...rs);

/**
 * Profil de vitesse en vol en fonction de la fraction de distance f ∈ [0, 1] :
 * accélération après décollage, croisière, décélération en approche.
 * La vitesse de croisière du profil est ajustée pour que la durée totale
 * corresponde exactement au temps en vol estimé.
 */
export const makeProfile = (plan: FlightPlan) => {
	const N = 400;
	const vLow = 260;
	const shape = (f: number) => {
		const s = (x: number) => {
			const c = Math.min(Math.max(x, 0), 1);
			return c * c * (3 - 2 * c);
		};
		return s(f / 0.2) * s((1 - f) / 0.24);
	};
	const distKm = plan.gcKm * AIRCRAFT.routeFactor;
	const timeFor = (vc: number) => {
		let t = 0;
		for (let i = 0; i < N; i++) t += distKm / N / (vLow + (vc - vLow) * shape((i + 0.5) / N));
		return t * 60;
	};
	let lo = vLow + 1;
	let hi = 3000;
	for (let k = 0; k < 60; k++) {
		const mid = (lo + hi) / 2;
		if (timeFor(mid) > plan.airborneMin) lo = mid;
		else hi = mid;
	}
	const vc = (lo + hi) / 2;
	const elapsed: number[] = [0];
	for (let i = 0; i < N; i++) elapsed.push(elapsed[i] + (distKm / N / (vLow + (vc - vLow) * shape((i + 0.5) / N))) * 60);
	return {
		speedAt: (f: number) => vLow + (vc - vLow) * shape(f),
		elapsedAt: (f: number) => {
			const x = Math.min(Math.max(f, 0), 1) * N;
			const i = Math.min(Math.floor(x), N - 1);
			return elapsed[i] + (elapsed[i + 1] - elapsed[i]) * (x - i);
		},
	};
};
