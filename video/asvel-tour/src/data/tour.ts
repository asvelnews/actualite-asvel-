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
	LFOU_T: {name: 'Cholet-Le Pontreau – aérogare', short: 'AÉRODROME CHOLET-LE PONTREAU', city: 'Cholet', kind: 'terminal', coords: [-0.87994, 47.08061]}, // OSM way 70208481
	LFAC_T: {name: 'Calais-Dunkerque – aérogare Louis-Blériot', short: 'AÉROPORT CALAIS-DUNKERQUE', city: 'Marck', kind: 'terminal', coords: [1.95526, 50.9581]}, // OSM way 220978419
	LIG_T: {name: 'Limoges-Bellegarde – aérogare', short: 'AÉROPORT LIMOGES-BELLEGARDE', city: 'Limoges', kind: 'terminal', coords: [1.17661, 45.86197]},
} satisfies Record<string, Place>;

export type PlaceId = keyof typeof PLACES;

export type Runway = {
	/** Désignations des deux QFU, dans l'ordre des extrémités */
	ids: [string, string];
	ends: [LonLat, LonLat];
	lengthM: number;
	widthM: number;
	/** Seuils décalés éventuels (atterrissage), dans l'ordre des extrémités */
	landingThresholds?: [LonLat | null, LonLat | null];
};

export type Airport = {
	iata: string;
	icao: string;
	name: string;
	city: string;
	/** Point de référence d'aérodrome */
	arp: LonLat;
	terminal: PlaceId;
	/** Piste utilisée par l'ATR 42-600 dans la simulation */
	runway: Runway;
};

// Sources : OurAirports (airports.csv / runways.csv) et OpenStreetMap (aeroway=runway),
// seuils de piste WGS84. Longueurs converties depuis les pieds publiés (1 ft = 0,3048 m).
// Règle : aérodrome adapté le plus proche de la salle, compatible avec l'appareil retenu.
export const AIRPORTS = {
	LYS: {
		iata: 'LYS', icao: 'LFLL', name: 'Lyon-Saint-Exupéry', city: 'Lyon', arp: [5.090139, 45.725996], terminal: 'LYS_T',
		runway: {ids: ['17R', '35L'], ends: [[5.08594, 45.7466], [5.0903, 45.7107]], lengthM: 4000, widthM: 45},
	},
	// Piste 03/21 asphalte 1 380 m × 30 m, seuil 03 décalé de 180 m (OSM ways 70208530 + 1375614076).
	CET: {
		iata: 'CET', icao: 'LFOU', name: 'Cholet-Le Pontreau', city: 'Cholet', arp: [-0.877064, 47.0821], terminal: 'LFOU_T',
		runway: {ids: ['03', '21'], ends: [[-0.880886, 47.076532], [-0.873213, 47.087763]], lengthM: 1380, widthM: 30, landingThresholds: [[-0.87988, 47.078004], null]},
	},
	// Piste 06/24 asphalte 1 535 m × 45 m (OSM way 173021626).
	CQF: {
		iata: 'CQF', icao: 'LFAC', name: 'Calais-Dunkerque', city: 'Calais', arp: [1.95476, 50.962101], terminal: 'LFAC_T',
		runway: {ids: ['06', '24'], ends: [[1.945178, 50.958741], [1.96435, 50.965443]], lengthM: 1535, widthM: 45},
	},
	LIG: {
		iata: 'LIG', icao: 'LFBL', name: 'Limoges-Bellegarde', city: 'Limoges', arp: [1.17944, 45.862801], terminal: 'LIG_T',
		runway: {ids: ['03', '21'], ends: [[1.17254, 45.8525], [1.1902, 45.8713]], lengthM: 2500, widthM: 45},
	},
} satisfies Record<string, Airport>;

export type AirportId = keyof typeof AIRPORTS;

/** Côté de l'étiquette d'aéroport sur la carte : 1 = à droite, -1 = à gauche */
export const AIRPORT_LABEL_SIDE: Record<AirportId, 1 | -1> = {LYS: 1, CET: 1, CQF: -1, LIG: -1};

/**
 * Compatibilité des pistes avec l'appareil retenu (ATR 42-600, fiche ATR 2022) :
 * 1 107 m au décollage à la MTOW et 966 m à l'atterrissage à la MLW (ISA, niveau de la mer).
 * L'Embraer ERJ 145 (2 270 m au décollage à la MTOW) est écarté : incompatible avec Cholet.
 */
export const RUNWAY_CHECK = [
	{icao: 'LFLL', name: 'Lyon-Saint-Exupéry', runway: '17R/35L', toraM: 4000, ldaM: 4000, widthM: 45},
	{icao: 'LFOU', name: 'Cholet-Le Pontreau', runway: '03/21', toraM: 1380, ldaM: 1200, widthM: 30},
	{icao: 'LFAC', name: 'Calais-Dunkerque', runway: '06/24', toraM: 1535, ldaM: 1535, widthM: 45},
	{icao: 'LFBL', name: 'Limoges-Bellegarde', runway: '03/21', toraM: 2500, ldaM: 2500, widthM: 45},
];

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
	/** Nom de ville affiché en grand sur la carte (matchs extérieurs), position par rapport à la salle */
	cityLabel?: LabelOffset;
};

export const TEAM = 'ASVEL';
export const ACCOUNT = '@ASVEL_NEWS';
export const HOME_AIRPORT: AirportId = 'LYS';
export const DISCLAIMER = 'Simulation de déplacements – données estimatives – non officielle';

export const GAMES: Game[] = [
	{opponent: 'Cholet', club: 'Cholet Basket', arena: 'MEILLERAIE', airport: 'CET', home: false, score: {asvel: 97, opponent: 85}, label: {dx: -60, dy: -140}, cityLabel: {dx: -10, dy: 58}},
	{opponent: 'Gravelines', club: 'Gravelines-Dunkerque', arena: 'SPORTICA', airport: 'CQF', home: false, score: {asvel: 70, opponent: 65}, label: {dx: 150, dy: -10}, cityLabel: {dx: -160, dy: 92}},
	{opponent: 'Roanne', club: 'Chorale Roanne Basket', arena: 'ASTROBALLE', airport: null, home: true, score: {asvel: 96, opponent: 77}, label: {dx: 160, dy: -110}},
	{opponent: 'Limoges', club: 'Limoges CSP', arena: 'BEAUBLANC', airport: 'LIG', home: false, score: {asvel: 97, opponent: 94}, label: {dx: -170, dy: 140}, cityLabel: {dx: 115, dy: 75}},
	{opponent: 'Nancy', club: 'SLUC Nancy', arena: 'ASTROBALLE', airport: null, home: true, score: null, label: {dx: 200, dy: 150}},
];

/** Libellé de score, équipe recevante en premier : « CHOLET – ASVEL », « 85-97 ». */
export const scoreLine = (g: Game) => {
	const opp = g.opponent.toUpperCase();
	const teams = g.home ? `${TEAM} – ${opp}` : `${opp} – ${TEAM}`;
	if (!g.score) return {teams, score: ''};
	const score = g.home ? `${g.score.asvel}-${g.score.opponent}` : `${g.score.opponent}-${g.score.asvel}`;
	return {teams, score};
};

/**
 * Musique : la vidéo n'embarque aucune piste par défaut. Pour en ajouter une,
 * déposer un fichier libre de droits (ou sous licence) dans `public/` et
 * indiquer son nom ici, par exemple 'musique.mp3'. Fondu d'entrée et de sortie.
 */
export const MUSIC_FILE: string | null = null;
