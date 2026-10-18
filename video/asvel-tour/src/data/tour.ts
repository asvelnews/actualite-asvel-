// ─────────────────────────────────────────────────────────────────────────────
// ASVEL TOUR – données de la série.
// Pour une prochaine vidéo : ajouter les lieux manquants dans PLACES, puis
// compléter GAMES (le résultat d'un match à venir vaut `null`).
// Tout le reste (trajets, distances, durées, compteur, statistiques finales)
// est recalculé automatiquement.
// ─────────────────────────────────────────────────────────────────────────────

export type LonLat = [number, number];

export type Place = {
	name: string;
	city: string;
	kind: 'airport' | 'arena';
	/** [longitude, latitude] en degrés décimaux WGS84 */
	coords: LonLat;
};

// Coordonnées WGS84. Aéroports : point de référence d'aérodrome publié dans
// l'AIP France (SIA). Salles : emprise du bâtiment relevée sur OpenStreetMap.
export const PLACES = {
	LYS: {name: 'Lyon-Saint-Exupéry', city: 'Lyon', kind: 'airport', coords: [5.0811, 45.7256]},
	LFOU: {name: 'Cholet-Le Pontreau', city: 'Cholet', kind: 'airport', coords: [-0.8772, 47.0819]},
	LFAC: {name: 'Calais-Dunkerque', city: 'Marck', kind: 'airport', coords: [1.9547, 50.9622]},
	LIG: {name: 'Limoges-Bellegarde', city: 'Limoges', kind: 'airport', coords: [1.1797, 45.8608]},
	ASTROBALLE: {name: 'Astroballe', city: 'Villeurbanne', kind: 'arena', coords: [4.8866, 45.7676]},
	MEILLERAIE: {name: 'La Meilleraie', city: 'Cholet', kind: 'arena', coords: [-0.8617, 47.051]},
	SPORTICA: {name: 'Sportica', city: 'Gravelines', kind: 'arena', coords: [2.1323, 50.9817]},
	BEAUBLANC: {name: 'Palais des sports de Beaublanc', city: 'Limoges', kind: 'arena', coords: [1.2733, 45.8447]},
} satisfies Record<string, Place>;

export type PlaceId = keyof typeof PLACES;

/** Position de l'étiquette par rapport au marqueur, en pixels écran (vue France entière). */
export type LabelOffset = {dx: number; dy: number};

export type Game = {
	opponent: string;
	arena: PlaceId;
	/** Aéroport d'arrivée de l'avion, puis bus jusqu'à la salle */
	airport: PlaceId;
	home: boolean;
	/** Score ASVEL en premier ; `null` = match à venir */
	score: {asvel: number; opponent: number} | null;
	label: LabelOffset;
};

export const TEAM = 'ASVEL';
export const ACCOUNT = '@ASVEL_NEWS';
/** Point de départ de la tournée */
export const START: PlaceId = 'LYS';

export const GAMES: Game[] = [
	{opponent: 'Cholet', arena: 'MEILLERAIE', airport: 'LFOU', home: false, score: {asvel: 97, opponent: 85}, label: {dx: -20, dy: -150}},
	{opponent: 'Gravelines', arena: 'SPORTICA', airport: 'LFAC', home: false, score: {asvel: 70, opponent: 65}, label: {dx: 140, dy: -40}},
	{opponent: 'Roanne', arena: 'ASTROBALLE', airport: 'LYS', home: true, score: {asvel: 96, opponent: 77}, label: {dx: 50, dy: -190}},
	{opponent: 'Limoges', arena: 'BEAUBLANC', airport: 'LIG', home: false, score: {asvel: 97, opponent: 94}, label: {dx: -110, dy: 150}},
	{opponent: 'Nancy', arena: 'ASTROBALLE', airport: 'LYS', home: true, score: null, label: {dx: 20, dy: 170}},
];
