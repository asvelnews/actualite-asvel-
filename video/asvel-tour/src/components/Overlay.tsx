import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {ACCOUNT, AIRPORTS, DISCLAIMER, GAMES, PLACES, scoreLine, TEAM, type Game} from '../data/tour';
import {AIRCRAFT, FUEL_PRICE, sumRanges, type Range} from '../lib/aviation';
import {fmt, formatClock, formatDuration, formatEur, formatKm} from '../lib/geo';
import {
	BUSES,
	FINAL_T,
	FLIGHTS,
	TOTAL_WINS,
	WINS,
	busProgress,
	planeAt,
	segAt,
	type BusSeg,
	type FlightSeg,
	type ResultSeg,
	type Seg,
	type StageSeg,
	type UpcomingSeg,
} from '../lib/timeline';
import {C, FONT_TEXT, FONT_TITLE} from '../theme';
import {Bus, Check, Flame, House, Plane, Stadium} from './Icons';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const SIDE = 48;
const INNER = 1080 - SIDE * 2;

const winsAt = (frame: number) => WINS.filter((w) => frame >= w.start + 6).length;

// Statistiques calculées à partir des résultats
const played = GAMES.filter((g) => g.score);
let streak = 0;
for (let i = played.length - 1; i >= 0 && played[i].score!.asvel > played[i].score!.opponent; i--) streak++;
const awayWins = WINS.filter((w) => !w.game.home).length;
const homeWins = WINS.filter((w) => w.game.home).length;
const plural = (n: number, s: string, p: string) => (n > 1 ? p : s);

// ── Introduction ────────────────────────────────────────────────────────────
export const Intro: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	if (frame > 190) return null;
	const a = spring({frame: frame - 6, fps, config: {damping: 14}});
	const b = spring({frame: frame - 24, fps, config: {damping: 14}});
	const c = spring({frame: frame - 40, fps, config: {damping: 14}});
	const out = interpolate(frame, [150, 185], [1, 0], clamp);
	return (
		<div style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', opacity: out, background: `rgba(7,11,16,${0.55 * out})`}}>
			<div style={{display: 'flex', alignItems: 'center', gap: 26, transform: `scale(${0.7 + 0.3 * a})`, opacity: a}}>
				<div style={{fontFamily: FONT_TITLE, fontSize: 150, fontWeight: 800, color: C.white, lineHeight: 0.9}}>
					{TEAM} <span style={{color: C.win}}>TOUR</span>
				</div>
				<Plane size={110} color={C.win} style={{transform: `translateX(${(1 - a) * -80}px) rotate(-8deg)`}} />
			</div>
			<div style={{fontFamily: FONT_TITLE, fontSize: 64, fontWeight: 800, color: C.win, letterSpacing: 3, marginTop: 20, opacity: b, transform: `translateY(${(1 - b) * 30}px)`, display: 'flex', alignItems: 'center', gap: 18}}>
				{streak} {plural(streak, 'VICTOIRE', 'VICTOIRES CONSÉCUTIVES')} <Flame size={60} />
			</div>
			<div style={{fontFamily: FONT_TITLE, fontSize: 40, fontWeight: 700, color: C.muted, letterSpacing: 10, marginTop: 18, opacity: c}}>{ACCOUNT}</div>
		</div>
	);
};

// ── En-tête : titre + compteur de victoires ─────────────────────────────────
export const Header: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const intro = spring({frame: frame - 150, fps, config: {damping: 16}});
	const wins = winsAt(frame);
	const last = WINS[wins - 1];
	const pop = last ? 1 + 0.25 * Math.max(0, 1 - (frame - last.start - 6) / 24) : 1;
	return (
		<div style={{position: 'absolute', left: SIDE, right: SIDE, top: 78, height: 130, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', opacity: intro, transform: `translateY(${(1 - intro) * -30}px)`}}>
			<div style={{fontFamily: FONT_TITLE, color: C.white}}>
				<div style={{fontSize: 24, fontWeight: 700, letterSpacing: 6, color: C.win}}>{ACCOUNT}</div>
				<div style={{fontSize: 92, fontWeight: 800, lineHeight: 0.9, display: 'flex', alignItems: 'center', gap: 14}}>
					{TEAM} <span style={{color: C.win}}>TOUR</span>
					<Plane size={58} color={C.win} />
				</div>
			</div>
			<div style={{display: 'flex', alignItems: 'flex-end', gap: 12, fontFamily: FONT_TITLE, color: C.white}}>
				<div style={{fontSize: 118, fontWeight: 800, lineHeight: 0.82, color: wins ? C.win : C.dim, transform: `scale(${pop})`, transformOrigin: 'right bottom', fontVariantNumeric: 'tabular-nums'}}>{wins}</div>
				<div style={{fontSize: 34, fontWeight: 800, lineHeight: 1, letterSpacing: 2, paddingBottom: 6}}>{plural(wins, 'VICTOIRE', 'VICTOIRES')}</div>
			</div>
		</div>
	);
};

// ── Bandeau permanent des victoires ─────────────────────────────────────────
export const Strip: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const intro = interpolate(frame, [160, 190], [0, 1], clamp);
	const slots = TOTAL_WINS;
	const gap = 12;
	const w = (INNER - gap * (slots - 1)) / slots;
	return (
		<div style={{position: 'absolute', left: SIDE, width: INNER, top: 222, height: 84, display: 'flex', gap, opacity: intro}}>
			{WINS.map((r, i) => {
				const on = frame >= r.start + 6;
				const p = on ? spring({frame: frame - r.start - 6, fps, config: {damping: 13}}) : 0;
				const {teams, score} = scoreLine(r.game);
				return (
					<div
						key={i}
						style={{
							width: w,
							height: 84,
							boxSizing: 'border-box',
							borderRadius: 14,
							border: `2px ${on ? 'solid' : 'dashed'} ${on ? C.win : C.dim}`,
							background: on ? 'rgba(18, 60, 36, 0.92)' : 'rgba(10,16,23,0.8)',
							padding: '8px 12px',
							fontFamily: FONT_TITLE,
							color: C.white,
							position: 'relative',
							overflow: 'hidden',
						}}
					>
						{on ? (
							<div style={{opacity: p, transform: `translateY(${(1 - p) * 14}px)`}}>
								<div style={{fontSize: 19, fontWeight: 800, letterSpacing: 0.3, whiteSpace: 'nowrap', color: '#BFF5D3'}}>
									V{i + 1} · {teams}
								</div>
								<div style={{fontSize: 40, fontWeight: 800, lineHeight: 1.05, fontVariantNumeric: 'tabular-nums'}}>{score}</div>
								<Check size={30} bg={C.win} color="#04140A" style={{position: 'absolute', right: 10, bottom: 10}} />
							</div>
						) : (
							<div style={{fontSize: 22, fontWeight: 700, letterSpacing: 2, color: C.dim, lineHeight: '64px'}}>VICTOIRE {i + 1}</div>
						)}
					</div>
				);
			})}
		</div>
	);
};

// ── Bannière d'état (départ, retour, arrivée à la base) ─────────────────────
const bannerFor = (s: Seg | undefined, frame: number): {text: string; icon: 'plane' | 'bus' | 'house'; color: string; since: number} | null => {
	if (!s || s.kind === 'stage' || s.kind === 'result' || s.kind === 'upcoming') return null;
	if (s.kind === 'bus' && s.arrivesAtBase && frame >= s.moveEnd) return {text: 'DE RETOUR À LA BASE', icon: 'house', color: C.win, since: s.moveEnd};
	if (s.tone === 'retour') {
		const first = [...BUSES, ...FLIGHTS].filter((x) => x.game === s.game && x.tone === 'retour').sort((a, b) => a.start - b.start)[0];
		return s.game.airport ? {text: 'RETOUR À LYON', icon: 'plane', color: C.white, since: first.start} : {text: 'RETOUR À LA BASE', icon: 'bus', color: C.white, since: first.start};
	}
	if (s.kind === 'bus' && s.banner === 'depart') return {text: `DÉPART DE LA BASE · CAP SUR ${PLACES[s.game.arena].city.toUpperCase()}`, icon: 'bus', color: C.win, since: s.start};
	return null;
};

export const Banner: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = segAt(frame);
	const b = bannerFor(s, frame);
	if (!b) return null;
	const p = spring({frame: frame - b.since, fps, config: {damping: 14}});
	const out = s ? interpolate(frame, [s.end - 8, s.end], [1, 0], clamp) : 1;
	const next = s ? bannerFor(segAt(s.end), s.end) : null;
	const o = next && next.text === b.text ? 1 : out;
	const Icon = b.icon === 'plane' ? Plane : b.icon === 'bus' ? Bus : House;
	return (
		<div style={{position: 'absolute', left: 0, right: 0, top: 322, display: 'flex', justifyContent: 'center', opacity: o * Math.min(p * 1.5, 1)}}>
			<div
				style={{
					display: 'flex',
					alignItems: 'center',
					gap: 16,
					padding: '10px 26px 10px 18px',
					borderRadius: 40,
					background: b.color === C.win ? C.win : C.white,
					color: '#04140A',
					fontFamily: FONT_TITLE,
					fontSize: 38,
					fontWeight: 800,
					letterSpacing: 2,
					transform: `scale(${0.8 + 0.2 * p})`,
					boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
				}}
			>
				<Icon size={42} color="#04140A" />
				{b.text}
			</div>
		</div>
	);
};

// ── Panneau inférieur ───────────────────────────────────────────────────────
const PANEL_TOP = 1292;
const PANEL_H = 350;

const Panel: React.FC<{s: Seg; children: React.ReactNode; border?: string}> = ({s, children, border}) => {
	const frame = useCurrentFrame();
	const o = interpolate(frame, [s.start, s.start + 10, s.end - 8, s.end], [0, 1, 1, 0], clamp);
	const next = segAt(s.end);
	// Pas de fondu entre deux panneaux du même type (évite le clignotement)
	const keep = next && next.kind === s.kind && frame > s.end - 8 ? 1 : o;
	return (
		<div
			style={{
				position: 'absolute',
				left: SIDE,
				width: INNER,
				top: PANEL_TOP,
				height: PANEL_H,
				boxSizing: 'border-box',
				borderRadius: 24,
				background: C.panel,
				border: `2px solid ${border ?? C.panelEdge}`,
				padding: '18px 24px',
				opacity: Math.max(keep, s.start + 10 > frame ? o : keep),
				fontFamily: FONT_TITLE,
				color: C.white,
				boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
			}}
		>
			{children}
		</div>
	);
};

const Label: React.FC<{children: React.ReactNode; color?: string}> = ({children, color}) => (
	<div style={{fontFamily: FONT_TEXT, fontSize: 19, fontWeight: 700, letterSpacing: 0.8, color: color ?? C.muted, whiteSpace: 'nowrap'}}>{children}</div>
);

const Cell: React.FC<{label: React.ReactNode; value: React.ReactNode; sub?: React.ReactNode; flex?: number; color?: string; size?: number}> = ({label, value, sub, flex = 1, color, size = 34}) => (
	<div style={{flex, minWidth: 0, background: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: '8px 12px'}}>
		<Label>{label}</Label>
		<div style={{fontSize: size, fontWeight: 800, lineHeight: 1.1, whiteSpace: 'nowrap', fontVariantNumeric: 'tabular-nums', color: color ?? C.white}}>{value}</div>
		{sub ? <div style={{fontFamily: FONT_TEXT, fontSize: 16, fontWeight: 700, color: C.muted, whiteSpace: 'nowrap'}}>{sub}</div> : null}
	</div>
);

const DirPill: React.FC<{dir: 'ALLER' | 'RETOUR' | 'À VENIR'}> = ({dir}) => {
	const bg = dir === 'ALLER' ? C.win : dir === 'RETOUR' ? C.white : C.upcoming;
	return <div style={{background: bg, color: '#04140A', borderRadius: 8, padding: '3px 12px', fontSize: 24, fontWeight: 800, letterSpacing: 2}}>{dir}</div>;
};

const Progress: React.FC<{p: number; color: string; icon: React.ReactNode}> = ({p, color, icon}) => (
	<div style={{position: 'relative', height: 30, flex: 1}}>
		<div style={{position: 'absolute', left: 0, right: 0, top: 13, height: 4, borderRadius: 2, background: C.dim}} />
		<div style={{position: 'absolute', left: 0, width: `${p * 100}%`, top: 13, height: 4, borderRadius: 2, background: color}} />
		<div style={{position: 'absolute', left: `calc(${p * 100}% - 15px)`, top: 0}}>{icon}</div>
	</div>
);

const rangeAt = (r: Range, k: number): Range => [r[0] * k, r[1] * k];
const fmtRange = (r: Range) => formatEur([Math.round(r[0] / 10) * 10, Math.round(r[1] / 10) * 10]);
/** Fourchette en milliers d'euros : « 11,2 – 17,3 k€ » */
const fmtK = (r: Range) => `${(r[0] / 1000).toFixed(1).replace('.', ',')} – ${(r[1] / 1000).toFixed(1).replace('.', ',')} k€`;

const FlightPanel: React.FC<{s: FlightSeg}> = ({s}) => {
	const frame = useCurrentFrame();
	const st = planeAt(s, frame);
	const p = s.plan;
	const from = AIRPORTS[p.from];
	const to = AIRPORTS[p.to];
	const dir = p.direction;
	const color = dir === 'ALLER' ? C.win : C.white;
	const count = interpolate(frame, [s.start + 4, s.start + 50], [0, 1], clamp);
	const fuelNow = rangeAt(FUEL_PRICE, st.fuelL);
	const pair = FLIGHTS.filter((f) => f.game === s.game);
	const aller = pair.find((f) => f.plan.direction === 'ALLER')!.plan;
	const retour = pair.find((f) => f.plan.direction === 'RETOUR')?.plan;
	return (
		<Panel s={s} border={color}>
			<div style={{display: 'flex', alignItems: 'center', gap: 14}}>
				<DirPill dir={dir} />
				<div style={{fontSize: 28, fontWeight: 800, letterSpacing: 1}}>VOL SIMULÉ {p.number}</div>
				<div style={{flex: 1}} />
				<div style={{textAlign: 'right'}}>
					<div style={{fontSize: 24, fontWeight: 800, letterSpacing: 1}}>{AIRCRAFT.model}</div>
					<Label color={color}>{st.phase}</Label>
				</div>
			</div>
			<div style={{display: 'flex', alignItems: 'center', gap: 18, marginTop: 6}}>
				<div>
					<div style={{fontSize: 50, fontWeight: 800, lineHeight: 1}}>{from.iata}</div>
					<Label>{from.name.toUpperCase()} · PISTE {s.depRunway}</Label>
				</div>
				<div style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
					<div style={{fontSize: 26, fontWeight: 800, color, fontVariantNumeric: 'tabular-nums'}}>{Math.round(st.f * 100)} %</div>
					<div style={{display: 'flex', width: '100%'}}>
						<Progress p={st.f} color={color} icon={<Plane size={30} color={color} />} />
					</div>
				</div>
				<div style={{textAlign: 'right'}}>
					<div style={{fontSize: 50, fontWeight: 800, lineHeight: 1}}>{to.iata}</div>
					<Label>{to.name.toUpperCase()} · PISTE {s.arrRunway}</Label>
				</div>
			</div>
			<div style={{display: 'flex', gap: 10, marginTop: 10}}>
				<Cell label="DISTANCE AÉRIENNE" value={`${fmt(st.f * p.gcKm)} / ${formatKm(p.gcKm)}`} flex={1.35} />
				<Cell label="TEMPS DE VOL" value={`${formatClock(st.elapsedMin)} / ${formatClock(p.airborneMin)}`} flex={1.1} />
				<Cell label="VITESSE" value={`${fmt(st.speedKmh)} KM/H`} />
				<Cell label="KÉROSÈNE" value={`${fmt(st.fuelL)} L`} />
			</div>
			<div style={{display: 'flex', gap: 10, marginTop: 10}}>
				<Cell label="CARBURANT (INCLUS)" value={fmtRange(fuelNow)} size={30} sub={`Jet A-1 ${FUEL_PRICE[0].toFixed(2).replace('.', ',')}–${FUEL_PRICE[1].toFixed(2).replace('.', ',')} €/L`} flex={1.25} />
				{dir === 'ALLER' ? (
					<>
						<Cell label="AFFRÈTEMENT VOL ALLER" value={fmtK(rangeAt(p.charter, count))} size={30} sub="carburant inclus" color={C.win} flex={1.25} />
						<Cell label="PRIX MOYEN ESTIMÉ" value={`≈ ${fmt(p.charterMean * count)} €`} size={30} sub="vol comparable" color={C.win} flex={0.95} />
					</>
				) : (
					<>
						<Cell label="VOL ALLER" value={fmtK(aller.charter)} size={27} sub={`moyenne ≈ ${fmt(aller.charterMean)} €`} flex={1} />
						<Cell label="VOL RETOUR" value={fmtK(rangeAt(p.charter, count))} size={27} sub={`moyenne ≈ ${fmt(p.charterMean)} €`} flex={1} />
						<Cell label="TOTAL A/R" value={fmtK(rangeAt(sumRanges([aller.charter, retour!.charter]), count))} size={27} sub={`moyenne ≈ ${fmt(aller.charterMean + retour!.charterMean)} €`} color={C.win} flex={1.05} />
					</>
				)}
			</div>
		</Panel>
	);
};

const placeLabel = (id: BusSeg['from']) => {
	const pl = PLACES[id];
	return pl.kind === 'arena' ? `${pl.short} – ${pl.city.toUpperCase()}` : pl.short;
};

const BusPanel: React.FC<{s: BusSeg}> = ({s}) => {
	const frame = useCurrentFrame();
	const u = busProgress(s, frame);
	const dir = s.tone === 'aller' ? 'ALLER' : s.tone === 'retour' ? 'RETOUR' : 'À VENIR';
	const color = s.tone === 'aller' ? C.win : s.tone === 'retour' ? C.white : C.upcoming;
	return (
		<Panel s={s} border={color}>
			<div style={{display: 'flex', alignItems: 'center', gap: 14}}>
				<DirPill dir={dir} />
				<div style={{fontSize: 30, fontWeight: 800, letterSpacing: 1.5}}>TRANSFERT EN AUTOCAR</div>
				<Bus size={36} color={color} />
				<div style={{flex: 1}} />
				<Label>ITINÉRAIRE OSRM · OPENSTREETMAP</Label>
			</div>
			<div style={{display: 'flex', alignItems: 'center', gap: 16, marginTop: 12}}>
				<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', width: 26}}>
					<div style={{width: 14, height: 14, borderRadius: 7, border: `3px solid ${color}`}} />
					<div style={{width: 3, height: 34, background: C.dim}} />
					<div style={{width: 16, height: 16, borderRadius: 3, background: color}} />
				</div>
				<div style={{flex: 1}}>
					<div style={{fontSize: 32, fontWeight: 700, lineHeight: 1.15, color: C.muted, whiteSpace: 'nowrap'}}>{placeLabel(s.from)}</div>
					<div style={{fontSize: 38, fontWeight: 800, lineHeight: 1.15, whiteSpace: 'nowrap'}}>{placeLabel(s.to)}</div>
				</div>
			</div>
			<div style={{display: 'flex', gap: 10, marginTop: 12}}>
				<Cell label="DISTANCE ROUTIÈRE" value={formatKm(s.km, 1)} />
				<Cell label="DURÉE ESTIMÉE" value={`≈ ${formatDuration(Math.round(s.minutes / 5) * 5)}`} />
				<Cell label="KM PARCOURUS" value={formatKm(u * s.km, 1)} color={color} />
				<Cell label="PROGRESSION" value={`${Math.round(u * 100)} %`} />
			</div>
			<div style={{display: 'flex', marginTop: 12}}>
				<Progress p={u} color={color} icon={<Bus size={30} color={color} />} />
			</div>
		</Panel>
	);
};

const StagePanel: React.FC<{s: StageSeg}> = ({s}) => {
	const g = s.game;
	const steps = g.airport
		? `BASE → ${AIRPORTS.LYS.iata} ✈ ${AIRPORTS[g.airport].iata} → ${PLACES[g.arena].short} → RETOUR À LYON`
		: g.score
			? `BASE → ${PLACES[g.arena].short} EN AUTOCAR → RETOUR À LA BASE`
			: `BASE → ${PLACES[g.arena].short} EN AUTOCAR`;
	return (
		<Panel s={s}>
			<div style={{display: 'flex', alignItems: 'baseline', gap: 16}}>
				<div style={{fontSize: 30, fontWeight: 800, letterSpacing: 4, color: C.win}}>ÉTAPE {s.stage} / {GAMES.length}</div>
				<Label>{g.home ? 'MATCH À DOMICILE · SANS AVION' : 'MATCH À L’EXTÉRIEUR · AVION + AUTOCAR'}</Label>
			</div>
			<div style={{fontSize: 96, fontWeight: 800, lineHeight: 1, marginTop: 6}}>{g.opponent.toUpperCase()}</div>
			<div style={{fontSize: 30, fontWeight: 700, color: C.muted, marginTop: 4}}>
				{g.club.toUpperCase()} · {PLACES[g.arena].name.toUpperCase()}, {PLACES[g.arena].city.toUpperCase()}
			</div>
			<div style={{fontSize: 26, fontWeight: 700, color: C.white, marginTop: 14, letterSpacing: 1}}>{steps}</div>
		</Panel>
	);
};

const ResultPanel: React.FC<{s: ResultSeg}> = ({s}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const p = spring({frame: frame - s.start, fps, config: {damping: 12}});
	const {teams, score} = scoreLine(s.game);
	return (
		<Panel s={s} border={C.win}>
			<div style={{display: 'flex', alignItems: 'center', gap: 16}}>
				<div style={{fontSize: 34, fontWeight: 800, letterSpacing: 4, color: C.win}}>VICTOIRE {s.winNumber}</div>
				<Label>{s.game.home ? 'À DOMICILE' : 'À L’EXTÉRIEUR'} · {PLACES[s.game.arena].name.toUpperCase()}</Label>
			</div>
			<div style={{display: 'flex', alignItems: 'center', marginTop: 10}}>
				<div style={{flex: 1}}>
					<div style={{fontSize: 48, fontWeight: 800, letterSpacing: 1}}>{teams}</div>
					<div style={{fontSize: 150, fontWeight: 800, lineHeight: 0.9, transform: `scale(${0.7 + 0.3 * p})`, transformOrigin: 'left center', fontVariantNumeric: 'tabular-nums'}}>{score}</div>
				</div>
				<Check size={150} bg={C.win} color="#04140A" style={{transform: `scale(${p})`}} />
			</div>
		</Panel>
	);
};

const UpcomingPanel: React.FC<{s: UpcomingSeg}> = ({s}) => {
	const frame = useCurrentFrame();
	const glow = 0.5 + 0.5 * Math.sin((frame - s.start) / 10);
	return (
		<Panel s={s} border={C.upcoming}>
			<div style={{display: 'flex', alignItems: 'center', boxShadow: `0 0 ${20 + glow * 20}px rgba(255,184,0,0)`}}>
				<div style={{flex: 1}}>
					<div style={{fontSize: 34, fontWeight: 800, letterSpacing: 5, color: C.upcoming}}>PROCHAIN MATCH</div>
					<div style={{fontSize: 92, fontWeight: 800, lineHeight: 1}}>
						{TEAM} vs {s.game.opponent.toUpperCase()}
					</div>
					<div style={{fontSize: 36, fontWeight: 700, letterSpacing: 3, color: C.muted}}>{PLACES[s.game.arena].name.toUpperCase()} · {PLACES[s.game.arena].city.toUpperCase()}</div>
					<div style={{display: 'flex', gap: 14, marginTop: 14, alignItems: 'center'}}>
						<div style={{background: C.upcoming, color: '#04140A', borderRadius: 10, padding: '4px 16px', fontSize: 40, fontWeight: 800, letterSpacing: 2}}>OBJECTIF 5/5</div>
						<Label>RÉSULTAT À VENIR</Label>
					</div>
				</div>
				<Stadium size={130} color={C.upcoming} style={{opacity: 0.7 + 0.3 * glow}} />
			</div>
		</Panel>
	);
};

export const BottomPanel: React.FC = () => {
	const frame = useCurrentFrame();
	const s = segAt(frame);
	if (!s) return null;
	switch (s.kind) {
		case 'flight':
			return <FlightPanel s={s} />;
		case 'bus':
			return <BusPanel s={s} />;
		case 'stage':
			return <StagePanel s={s} />;
		case 'result':
			return <ResultPanel s={s} />;
		case 'upcoming':
			return <UpcomingPanel s={s} />;
	}
};

// ── Bilan final ─────────────────────────────────────────────────────────────
const totals = (() => {
	const plans = FLIGHTS.map((f) => f.plan);
	return {
		flights: plans.length,
		allers: plans.filter((p) => p.direction === 'ALLER').length,
		retours: plans.filter((p) => p.direction === 'RETOUR').length,
		km: plans.reduce((a, p) => a + p.gcKm, 0),
		minutes: plans.reduce((a, p) => a + p.airborneMin, 0),
		fuelL: plans.reduce((a, p) => a + p.fuelL, 0),
		charter: sumRanges(plans.map((p) => p.charter)),
		busKm: BUSES.reduce((a, b) => a + b.km, 0),
	};
})();
export const TOTALS = totals;

const NEXT: Game | undefined = GAMES.find((g) => !g.score);

export const Final: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	if (frame < FINAL_T.zoom) return null;
	const t0 = FINAL_T.stats + 80;
	const ap = (i: number) => spring({frame: frame - t0 - i * 14, fps, config: {damping: 15}});
	const cnt = (i: number) => interpolate(frame, [t0 + i * 14, t0 + i * 14 + 45], [0, 1], {...clamp, easing: (x) => 1 - (1 - x) ** 3});
	const titleO = interpolate(frame, [FINAL_T.zoom, FINAL_T.zoom + 20], [0, 1], clamp);
	const titleOut = interpolate(frame, [t0 - 20, t0], [1, 0], clamp);
	const statsOut = interpolate(frame, [FINAL_T.table - 20, FINAL_T.table], [1, 0], clamp);
	if (frame >= FINAL_T.table) return <FlightsTable />;
	const tile = (i: number, children: React.ReactNode, style: React.CSSProperties = {}) => (
		<div style={{opacity: ap(i), transform: `translateY(${(1 - ap(i)) * 40}px)`, background: C.panel, border: `2px solid ${C.panelEdge}`, borderRadius: 16, padding: '10px 16px', boxSizing: 'border-box', ...style}}>{children}</div>
	);
	const big = (v: React.ReactNode, color = C.white) => <div style={{fontSize: 46, fontWeight: 800, lineHeight: 1.05, color, fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap'}}>{v}</div>;
	return (
		<>
			{frame < t0 ? (
				<div style={{position: 'absolute', left: SIDE, width: INNER, top: PANEL_TOP, opacity: titleO * titleOut, fontFamily: FONT_TITLE, color: C.white, background: C.panel, borderRadius: 24, padding: '22px 26px', boxSizing: 'border-box', border: `2px solid ${C.panelEdge}`}}>
					<div style={{fontSize: 34, fontWeight: 800, letterSpacing: 5, color: C.win}}>BILAN DES DÉPLACEMENTS</div>
					<div style={{fontSize: 80, fontWeight: 800, lineHeight: 1}}>TOUTE LA TOURNÉE</div>
					<div style={{display: 'flex', gap: 26, marginTop: 14, fontSize: 26, fontWeight: 700}}>
						{[
							[C.win, 'TRAJETS ALLER'],
							[C.white, 'TRAJETS RETOUR'],
							[C.upcoming, 'PROCHAIN MATCH'],
						].map(([c, l]) => (
							<div key={l} style={{display: 'flex', alignItems: 'center', gap: 10}}>
								<div style={{width: 34, height: 6, borderRadius: 3, background: c}} />
								{l}
							</div>
						))}
					</div>
				</div>
			) : null}
			<div style={{position: 'absolute', left: SIDE, width: INNER, top: 960, display: 'flex', flexDirection: 'column', gap: 12, fontFamily: FONT_TITLE, color: C.white, opacity: statsOut}}>
				<div style={{display: 'flex', gap: 12}}>
					{[
						{v: streak, t: plural(streak, 'VICTOIRE CONSÉCUTIVE', 'VICTOIRES CONSÉCUTIVES'), I: <Flame size={40} />},
						{v: awayWins, t: `${plural(awayWins, 'VICTOIRE', 'VICTOIRES')} À L'EXTÉRIEUR`, I: <Plane size={40} color={C.white} />},
						{v: homeWins, t: `${plural(homeWins, 'VICTOIRE', 'VICTOIRES')} À DOMICILE`, I: <House size={40} color={C.white} />},
					].map((x, i) => (
						<React.Fragment key={i}>
							{tile(
								i,
								<>
									<div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
										<div style={{fontSize: 70, fontWeight: 800, color: C.win, lineHeight: 1}}>{x.v}</div>
										{x.I}
									</div>
									<div style={{fontSize: 24, fontWeight: 800, lineHeight: 1.05, letterSpacing: 0.5}}>{x.t}</div>
								</>,
								{flex: 1, height: 128},
							)}
						</React.Fragment>
					))}
				</div>
				{tile(
					3,
					<div style={{display: 'flex', alignItems: 'center', gap: 16}}>
						<Plane size={40} color={C.win} />
						<div style={{fontSize: 40, fontWeight: 800}}>{totals.flights} VOLS SIMULÉS</div>
						<div style={{fontSize: 30, fontWeight: 700, color: C.muted}}>
							{totals.allers} ALLERS + {totals.retours} RETOURS · {AIRCRAFT.model}
						</div>
					</div>,
				)}
				<div style={{display: 'flex', flexWrap: 'wrap', gap: 12}}>
					{tile(4, <><Label>DISTANCE AÉRIENNE TOTALE</Label>{big(formatKm(totals.km * cnt(4)))}</>, {width: (INNER - 12) / 2})}
					{tile(5, <><Label>DURÉE TOTALE DES VOLS</Label>{big(formatDuration(totals.minutes * cnt(5)))}</>, {width: (INNER - 12) / 2})}
					{tile(6, <><Label>KÉROSÈNE TOTAL ESTIMÉ</Label>{big(`${fmt(totals.fuelL * cnt(6))} L`)}</>, {width: (INNER - 12) / 2})}
					{tile(7, <><Label>COÛT TOTAL ESTIMÉ DES AFFRÈTEMENTS</Label>{big(formatEur([Math.round((totals.charter[0] * cnt(7)) / 100) * 100, Math.round((totals.charter[1] * cnt(7)) / 100) * 100]), C.win)}</>, {width: (INNER - 12) / 2})}
				</div>
				{tile(
					8,
					<div style={{display: 'flex', alignItems: 'center', gap: 16}}>
						<Bus size={40} color={C.white} />
						<Label>DISTANCE TOTALE EN AUTOCAR</Label>
						<div style={{flex: 1}} />
						{big(formatKm(totals.busKm * cnt(8), 1))}
					</div>,
				)}
				{NEXT
					? tile(
							9,
							<div style={{display: 'flex', alignItems: 'center', gap: 16}}>
								<div style={{flex: 1}}>
									<div style={{fontSize: 24, fontWeight: 800, letterSpacing: 4, color: C.upcoming}}>PROCHAIN MATCH</div>
									<div style={{fontSize: 52, fontWeight: 800, lineHeight: 1}}>
										{TEAM} vs {NEXT.opponent.toUpperCase()} · {PLACES[NEXT.arena].short}
									</div>
								</div>
								<div style={{background: C.upcoming, color: '#04140A', borderRadius: 10, padding: '4px 14px', fontSize: 34, fontWeight: 800}}>OBJECTIF 5/5</div>
							</div>,
							{border: `2px solid ${C.upcoming}`},
						)
					: null}
			</div>
		</>
	);
};

/** Tableau des 6 vols : distance, durée, kérosène, prix moyen estimé. */
const FlightsTable: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = FINAL_T.table;
	const head = spring({frame: frame - t, fps, config: {damping: 15}});
	const cols = '1.5fr 1fr 0.9fr 1fr 1.1fr';
	const cell: React.CSSProperties = {fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap'};
	return (
		<div style={{position: 'absolute', left: SIDE, width: INNER, top: 960, fontFamily: FONT_TITLE, color: C.white}}>
			<div style={{opacity: head, transform: `translateY(${(1 - head) * 30}px)`}}>
				<div style={{display: 'flex', alignItems: 'baseline', gap: 14}}>
					<div style={{fontSize: 44, fontWeight: 800, letterSpacing: 1}}>LES {FLIGHTS.length} VOLS SIMULÉS</div>
					<div style={{fontSize: 28, fontWeight: 700, color: C.muted}}>{AIRCRAFT.model}</div>
				</div>
				<Label color={C.upcoming}>VALEURS D'UN VOL COMPARABLE · ESTIMATIONS, PAS LES DÉPENSES RÉELLES DE L'ASVEL</Label>
				<div style={{display: 'grid', gridTemplateColumns: cols, marginTop: 12, padding: '0 16px'}}>
					{['TRAJET', 'DISTANCE', 'DURÉE', 'KÉROSÈNE', 'PRIX MOYEN'].map((h) => (
						<Label key={h}>{h}</Label>
					))}
				</div>
			</div>
			<div style={{display: 'flex', flexDirection: 'column', gap: 8, marginTop: 6}}>
				{FLIGHTS.map((f, i) => {
					const p = spring({frame: frame - t - 14 - i * 9, fps, config: {damping: 15}});
					const color = f.plan.direction === 'ALLER' ? C.win : C.white;
					return (
						<div
							key={i}
							style={{
								display: 'grid',
								gridTemplateColumns: cols,
								alignItems: 'center',
								height: 62,
								padding: '0 16px',
								borderRadius: 12,
								background: C.panel,
								borderLeft: `6px solid ${color}`,
								opacity: p,
								transform: `translateX(${(1 - p) * -50}px)`,
								fontSize: 34,
								fontWeight: 800,
							}}
						>
							<div style={{...cell, display: 'flex', alignItems: 'center', gap: 10}}>
								<span style={{color, fontSize: 20, letterSpacing: 1}}>{f.plan.direction}</span>
								{AIRPORTS[f.plan.from].iata} → {AIRPORTS[f.plan.to].iata}
							</div>
							<div style={cell}>{formatKm(f.plan.gcKm)}</div>
							<div style={cell}>{formatDuration(f.plan.airborneMin)}</div>
							<div style={cell}>{fmt(f.plan.fuelL)} L</div>
							<div style={{...cell, color: C.win}}>≈ {fmt(f.plan.charterMean)} €</div>
						</div>
					);
				})}
			</div>
			<div style={{marginTop: 10, opacity: spring({frame: frame - t - 80, fps, config: {damping: 15}})}}>
				<Label>
					CET = CHOLET-LE PONTREAU · CQF = CALAIS-DUNKERQUE · LIG = LIMOGES-BELLEGARDE · LYS = LYON-SAINT-EXUPÉRY
				</Label>
			</div>
		</div>
	);
};

export const Disclaimer: React.FC = () => {
	const frame = useCurrentFrame();
	const o = interpolate(frame, [20, 50], [0, 1], clamp);
	const inFlight = segAt(frame)?.kind === 'flight';
	return (
		<div style={{position: 'absolute', left: 0, right: 0, top: 1656, textAlign: 'center', fontFamily: FONT_TEXT, fontSize: 18, fontWeight: 500, color: C.muted, opacity: 0.85 * o, letterSpacing: 0.5}}>
			{inFlight ? 'Vol simulé à titre illustratif – valeurs d\'un vol comparable, pas les dépenses réelles de l\'ASVEL' : `${DISCLAIMER} · ${ACCOUNT}`}
		</div>
	);
};
