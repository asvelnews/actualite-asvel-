// ─────────────────────────────────────────────────────────────────────────────
// ASVEL TOUR – données de la série.
// Pour une prochaine vidéo : compléter PLACES / AIRPORTS si besoin, ajouter le
// match dans GAMES, puis régénérer les itinéraires routiers
// (`npm run fetch:routes`). Le reste est recalculé automatiquement.
// ─────────────────────────────────────────────────────────────────────────────

export type LonLat = [number, number];

export type Place = {
	name: string;
	short: string;
	city: string;
	kind: 'base' | 'arena' | 'terminal';
	/** [longitude, latitude] WGS84 */
	coords: LonLat;
};

// Coordonnées vérifiées sur OpenStreetMap (Nominatim / Overpass, octobre 2026).
export const PLACES = {
	// Base lyonnaise : Tony Parker Adéquat Academy, Gerland (OSM way 527494526),
	// pôle d'entraînement et de formation du club. Modifiable ici.
	BASE: {name: 'Base ASVEL – Gerland', short: 'BASE ASVEL', city: 'Lyon', kind: 'base', coords: [4.82712, 45.72529]},
	ASTROBALLE: {name: 'Astroballe', short: 'ASTROBALLE', city: 'Villeurbanne', kind: 'arena', coords: [4.90736, 45.76642]}, // OSM way 85200814
	MEILLERAIE: {name: 'La Meilleraie', short: 'LA MEILLERAIE', city: 'Cholet', kind: 'arena', coords: [-0.8962, 47.0577]}, // OSM way 69972018
	SPORTICA: {name: 'Sportica', short: 'SPORTICA', city: 'Gravelines', kind: 'arena', coords: [2.12286, 50.99852]}, // OSM relation 16890974
	BEAUBLANC: {name: 'Palais des sports de Beaublanc', short: 'BEAUBLANC', city: 'Limoges', kind: 'arena', coords: [1.24339, 45.84752]}, // OSM way 70372530
	// Aérogares (point de départ / d'arrivée des autocars), OSM aeroway=terminal
	LYS_T: {name: 'Lyon-Saint-Exupéry – Terminal 1', short: 'AÉROPORT LYON-SAINT-EXUPÉRY', city: 'Colombier-Saugnieu', kind: 'terminal', coords: [5.07944, 45.71892]},
	NTE_T: {name: 'Nantes-Atlantique – aérogare', short: 'AÉROPORT NANTES-ATLANTIQUE', city: 'Bouguenais', kind: 'terminal', coords: [-1.60184, 47.15793]},
	LIL_T: {name: 'Lille-Lesquin – aérogare', short: 'AÉROPORT LILLE-LESQUIN', city: 'Lesquin', kind: 'terminal', coords: [3.0971, 50.56913]},
	LIG_T: {name: 'Limoges-Bellegarde – aérogare', short: 'AÉROPORT LIMOGES-BELLEGARDE', city: 'Limoges', kind: 'terminal', coords: [1.17661, 45.86197]},
} satisfies Record<string, Place>;

export type PlaceId = keyof typeof PLACES;

export type Runway = {
	/** Désignations des deux QFU, dans l'ordre des extrémités */
	ids: [string, string];
	ends: [LonLat, LonLat];
	lengthM: number;
	widthM: number;
};

export type Airport = {
	iata: string;
	icao: string;
	name: string;
	city: string;
	/** Point de référence d'aérodrome */
	arp: LonLat;
	terminal: PlaceId;
	/** Piste utilisée par l'ERJ 145 dans la simulation */
	runway: Runway;
};

// Source : OurAirports (airports.csv / runways.csv), seuils de piste WGS84.
// Longueurs converties depuis les pieds publiés (1 ft = 0,3048 m).
export const AIRPORTS = {
	LYS: {
		iata: 'LYS', icao: 'LFLL', name: 'Lyon-Saint-Exupéry', city: 'Lyon', arp: [5.090139, 45.725996], terminal: 'LYS_T',
		runway: {ids: ['17R', '35L'], ends: [[5.08594, 45.7466], [5.0903, 45.7107]], lengthM: 4000, widthM: 45},
	},
	NTE: {
		iata: 'NTE', icao: 'LFRS', name: 'Nantes-Atlantique', city: 'Nantes', arp: [-1.61073, 47.153198], terminal: 'NTE_T',
		runway: {ids: ['03', '21'], ends: [[-1.61954, 47.1416], [-1.6019, 47.1648]], lengthM: 2900, widthM: 45},
	},
	LIL: {
		iata: 'LIL', icao: 'LFQQ', name: 'Lille-Lesquin', city: 'Lille', arp: [3.102429, 50.566564], terminal: 'LIL_T',
		runway: {ids: ['08', '26'], ends: [[3.08301, 50.5629], [3.12223, 50.5685]], lengthM: 2825, widthM: 45},
	},
	LIG: {
		iata: 'LIG', icao: 'LFBL', name: 'Limoges-Bellegarde', city: 'Limoges', arp: [1.17944, 45.862801], terminal: 'LIG_T',
		runway: {ids: ['03', '21'], ends: [[1.17254, 45.8525], [1.1902, 45.8713]], lengthM: 2500, widthM: 45},
	},
} satisfies Record<string, Airport>;

export type AirportId = keyof typeof AIRPORTS;

/**
 * Aérodrome écarté : Cholet-Le Pontreau (LFOU), piste 02/20 de 1 380 m × 30 m.
 * L'ERJ 145 LR demande 2 270 m au décollage et 1 400 m à l'atterrissage aux
 * masses maximales (fiche constructeur Embraer) : compatibilité non confirmée,
 * d'où le choix de Nantes-Atlantique (piste 03/21 de 2 900 m).
 */
export const REJECTED_AIRFIELDS = [{icao: 'LFOU', name: 'Cholet-Le Pontreau', runwayM: 1380, reason: 'Piste trop courte pour un ERJ 145 (2 270 m requis au décollage à la MTOW)'}];

/** Position de l'encart par rapport au marqueur (pixels écran, vue France entière). */
export type LabelOffset = {dx: number; dy: number};

export type Game = {
	/** Nom affiché dans les scores (équipe adverse) */
	opponent: string;
	/** Nom complet du club adverse */
	club: string;
	arena: PlaceId;
	/** Aéroport de destination pour un match à l'extérieur, `null` à domicile (autocar uniquement) */
	airport: AirportId | null;
	home: boolean;
	/** Score ASVEL / adversaire ; `null` = match à venir */
	score: {asvel: number; opponent: number} | null;
	label: LabelOffset;
};

export const TEAM = 'ASVEL';
export const ACCOUNT = '@ASVEL_NEWS';
export const HOME_AIRPORT: AirportId = 'LYS';
export const DISCLAIMER = 'Simulation de déplacements – données estimatives – non officielle';

export const GAMES: Game[] = [
	{opponent: 'Cholet', club: 'Cholet Basket', arena: 'MEILLERAIE', airport: 'NTE', home: false, score: {asvel: 97, opponent: 85}, label: {dx: -60, dy: -140}},
	{opponent: 'Gravelines', club: 'Gravelines-Dunkerque', arena: 'SPORTICA', airport: 'LIL', home: false, score: {asvel: 70, opponent: 65}, label: {dx: 150, dy: -10}},
	{opponent: 'Roanne', club: 'Chorale Roanne Basket', arena: 'ASTROBALLE', airport: null, home: true, score: {asvel: 96, opponent: 77}, label: {dx: 160, dy: -110}},
	{opponent: 'Limoges', club: 'Limoges CSP', arena: 'BEAUBLANC', airport: 'LIG', home: false, score: {asvel: 97, opponent: 94}, label: {dx: -150, dy: 130}},
	{opponent: 'Nancy', club: 'SLUC Nancy', arena: 'ASTROBALLE', airport: null, home: true, score: null, label: {dx: 160, dy: 120}},
];

/** Libellé de score, équipe recevante en premier : « CHOLET – ASVEL », « 85-97 ». */
export const scoreLine = (g: Game) => {
	const opp = g.opponent.toUpperCase();
	const teams = g.home ? `${TEAM} – ${opp}` : `${opp} – ${TEAM}`;
	if (!g.score) return {teams, score: ''};
	const score = g.home ? `${g.score.asvel}-${g.score.opponent}` : `${g.score.opponent}-${g.score.asvel}`;
	return {teams, score};
};
