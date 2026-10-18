// ─────────────────────────────────────────────────────────────────────────────
// Modèle de vol simplifié – ATR 42-600 (turbopropulseur régional, 48 sièges).
// Simulation illustrative : valeurs d'un vol COMPARABLE, pas des trajets
// réellement effectués ni des dépenses réelles de l'ASVEL.
// Choix de l'appareil : compatible avec les quatre pistes retenues
// (la plus courte : Cholet-Le Pontreau, 1 380 m × 30 m, LDA 03 ≈ 1 200 m).
// Fiche ATR 42-600 (2022) : décollage 1 107 m (MTOW), atterrissage 966 m (MLW),
// croisière maxi 535 km/h au FL240, consommation de croisière 620 kg/h.
// Hypothèses (voir README) :
// - Croisière retenue : 520 km/h vraie.
// - Distance parcourue = orthodromie × 1,05 (routes aériennes, procédures).
// - Pénalité montée / descente / approche : +12 min sur le temps en vol.
// - Vent moyen en altitude : 40 km/h d'ouest (270°), différencie aller et retour.
// - Roulage : 12 min au départ de LYS, 6 min à LIG, 4 min sur les petits
//   terrains ; 6 / 4 / 3 min à l'arrivée.
// - Consommation : 650 kg/h en vol (croisière ATR 620 kg/h + montée),
//   2 kg/min au roulage ; densité Jet A-1 0,80 kg/L.
// - Prix Jet A-1 : 1,20 à 1,80 €/L HT (tarifs publics Air BP 2026 relevés
//   entre 1,60 et 1,92 €/L HT ; les opérateurs sous contrat paient moins).
// - Affrètement (carburant INCLUS, jamais ajouté une seconde fois) :
//   4 800 à 7 000 € par heure bloc (coût d'exploitation calculé ≈ 4 400 –
//   5 200 €/h + marge opérateur), minimum 1 h facturée par vol,
//   + 0,75 h de repositionnement par vol, + 800 à 1 600 € de redevances et
//   d'assistance par vol, + 900 à 1 500 € d'immobilisation au retour.
// ─────────────────────────────────────────────────────────────────────────────
import {AIRPORTS, type AirportId, type LonLat} from '../data/tour';
import {bearing, haversineKm} from './geo';

export const AIRCRAFT = {
	model: 'ATR 42-600',
	seats: 48,
	cruiseKmh: 520,
	routeFactor: 1.05,
	climbDescentMin: 12,
	burnKgH: 650,
	taxiBurnKgMin: 2,
	densityKgL: 0.8,
	/** Vitesses au sol (km/h) : rotation ≈ 105 kt, toucher ≈ 100 kt */
	rotationKmh: 195,
	touchdownKmh: 185,
	/** Roulage au décollage et distance d'arrêt après le toucher (km) */
	takeoffRollKm: 0.9,
	landingRollKm: 0.7,
};

const WIND = {fromDeg: 270, kmh: 40};
const FUEL_EUR_L: [number, number] = [1.2, 1.8];
const RATE_EUR_H: [number, number] = [4800, 7000];
const MIN_BILLED_H = 1;
const REPOSITION_H = 0.75;
const FEES_EUR: [number, number] = [800, 1600];
const NIGHT_STOP_EUR: [number, number] = [900, 1500];

const taxiOut = (a: AirportId) => (a === 'LYS' ? 12 : a === 'LIG' ? 6 : 4);
const taxiIn = (a: AirportId) => (a === 'LYS' ? 6 : a === 'LIG' ? 4 : 3);

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
	/** Prix moyen estimé du trajet (milieu de la fourchette d'affrètement) */
	charterMean: number;
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
		charterMean: round100((charter[0] + charter[1]) / 2),
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
