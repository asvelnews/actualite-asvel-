import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {AIRPORTS, PLACES, scoreLine, TEAM, type Game, type LonLat} from '../data/tour';
import {project} from '../lib/geo';
import {FINAL_T, HEIGHT, RESULTS, UPCOMINGS, WIDTH, cameraAt, toScreen, type ResultSeg, type UpcomingSeg, type View} from '../lib/timeline';
import {C, FONT_TEXT, FONT_TITLE} from '../theme';
import {Check, House, Plane} from './Icons';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const CARD_W = 292;
const CARD_H = 122;

/** Réduction des étiquettes dans la vue finale compacte. */
const compactAt = (frame: number) => interpolate(frame, [FINAL_T.stats + 70, FINAL_T.stats + 110], [0, 1], clamp);

type CardSeg = ResultSeg | UpcomingSeg;
const CARDS: CardSeg[] = [...RESULTS, ...UPCOMINGS];

const geometry = (s: CardSeg, frame: number) => {
	const view = cameraAt(frame);
	const anchor = toScreen(project(PLACES[s.game.arena].coords as LonLat), view);
	const c = compactAt(frame);
	const off = 1 - 0.4 * c;
	let cx = anchor.x + s.game.label.dx * off;
	let cy = anchor.y + s.game.label.dy * off;
	// Quand le repère est à l'écran, l'encart reste dans la zone carte
	// (jamais sous l'en-tête ni sous le panneau inférieur).
	const onScreen = anchor.x > -40 && anchor.x < 1120 && anchor.y > 300 && anchor.y < 1300;
	if (onScreen) {
		const w = widthOf(s) / 2 + 16;
		cx = Math.min(Math.max(cx, w), 1080 - w);
		cy = Math.min(Math.max(cy, 330 + CARD_H / 2), 1270 - CARD_H / 2);
	}
	return {anchor, cx, cy, scale: 1 - 0.3 * c};
};

const widthOf = (s: CardSeg) => (s.kind === 'upcoming' ? 340 : CARD_W);

const toneOf = (s: CardSeg) => (s.kind === 'upcoming' ? C.upcoming : s.winNumber !== null ? C.win : C.loss);

const useAppear = (s: CardSeg) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	return spring({frame: frame - s.start, fps, config: {damping: 15, stiffness: 120, mass: 0.8}});
};

const Leader: React.FC<{s: CardSeg}> = ({s}) => {
	const frame = useCurrentFrame();
	const p = useAppear(s);
	if (frame < s.start) return null;
	const {anchor, cx, cy} = geometry(s, frame);
	const k = Math.min(p, 1);
	return <line x1={anchor.x} y1={anchor.y} x2={anchor.x + (cx - anchor.x) * k} y2={anchor.y + (cy - anchor.y) * k} stroke={toneOf(s)} strokeWidth={2.5} strokeOpacity={0.9} />;
};

const Dot: React.FC<{s: CardSeg}> = ({s}) => {
	const frame = useCurrentFrame();
	const p = useAppear(s);
	if (frame < s.start) return null;
	const {anchor} = geometry(s, frame);
	if (s.kind === 'upcoming') {
		return (
			<g transform={`translate(${anchor.x} ${anchor.y}) scale(${p})`}>
				<circle r={31} fill="none" stroke={C.upcoming} strokeWidth={3.5} strokeDasharray="7 6" transform={`rotate(${frame})`} />
			</g>
		);
	}
	const pulse = ((frame - s.start) / 80) % 1;
	const color = toneOf(s);
	return (
		<g transform={`translate(${anchor.x} ${anchor.y})`}>
			<circle r={19 + pulse * 26} fill="none" stroke={color} strokeWidth={2} opacity={(1 - pulse) * 0.6} />
			<g transform={`scale(${p})`}>
				<circle r={19} fill={color} stroke="#fff" strokeWidth={3} />
				<text y={8} textAnchor="middle" fontFamily={FONT_TITLE} fontWeight={800} fontSize={24} fill="#04140A">
					{s.winNumber ?? '–'}
				</text>
			</g>
		</g>
	);
};

const venueTag = (g: Game) => `${PLACES[g.arena].short} · ${g.home ? 'DOMICILE' : 'EXTÉRIEUR'}`;

const Card: React.FC<{s: CardSeg}> = ({s}) => {
	const frame = useCurrentFrame();
	const p = useAppear(s);
	if (frame < s.start) return null;
	const {cx, cy, scale} = geometry(s, frame);
	const base: React.CSSProperties = {
		position: 'absolute',
		left: cx - widthOf(s) / 2,
		top: cy - CARD_H / 2,
		width: widthOf(s),
		height: CARD_H,
		transform: `scale(${scale * (0.6 + 0.4 * p)})`,
		opacity: Math.min(p * 1.4, 1),
		borderRadius: 18,
		boxSizing: 'border-box',
		boxShadow: '0 14px 40px rgba(0,0,0,0.6)',
		fontFamily: FONT_TITLE,
		color: C.white,
		overflow: 'hidden',
		background: C.panel,
		border: `3px solid ${toneOf(s)}`,
	};
	const {teams, score} = scoreLine(s.game);
	if (s.kind === 'upcoming') {
		return (
			<div style={{...base, padding: '10px 16px'}}>
				<div style={{fontSize: 20, fontWeight: 800, letterSpacing: 1.5, color: C.upcoming, whiteSpace: 'nowrap'}}>PROCHAIN MATCH · À VENIR</div>
				<div style={{fontSize: 40, fontWeight: 800, lineHeight: 1.05, whiteSpace: 'nowrap'}}>
					{TEAM} vs {s.game.opponent.toUpperCase()}
				</div>
				<div style={{fontFamily: FONT_TEXT, fontSize: 17, fontWeight: 700, color: C.muted, letterSpacing: 0.8, whiteSpace: 'nowrap'}}>{PLACES[s.game.arena].short} · OBJECTIF 5/5</div>
			</div>
		);
	}
	const won = s.winNumber !== null;
	return (
		<div style={{...base, display: 'flex'}}>
			<div style={{width: 64, background: toneOf(s), color: '#04140A', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', lineHeight: 1}}>
				<div style={{fontSize: 14, fontWeight: 800, letterSpacing: 0.5}}>{won ? 'VICT.' : 'DÉF.'}</div>
				<div style={{fontSize: 48, fontWeight: 800}}>{s.winNumber ?? '–'}</div>
			</div>
			<div style={{flex: 1, padding: '10px 14px 0 14px', position: 'relative'}}>
				<div style={{fontSize: 24, fontWeight: 800, letterSpacing: 0.8, lineHeight: 1, whiteSpace: 'nowrap'}}>{teams}</div>
				<div style={{fontSize: 54, fontWeight: 800, lineHeight: 1, marginTop: 3, fontVariantNumeric: 'tabular-nums'}}>{score}</div>
				<div style={{fontFamily: FONT_TEXT, fontSize: 14, fontWeight: 700, color: C.muted, letterSpacing: 0.8, marginTop: 3, whiteSpace: 'nowrap'}}>{venueTag(s.game)}</div>
				{won ? <Check size={38} bg={C.win} color="#04140A" style={{position: 'absolute', right: 12, bottom: 26}} /> : null}
			</div>
		</div>
	);
};

/** Repères fixes : Lyon, base lyonnaise, aéroports, salles. */
const Places: React.FC<{view: View; frame: number}> = ({view, frame}) => {
	// Repères atténués dans la vue finale compacte pour laisser la place aux résultats
	const reveal = interpolate(frame, [60, 110], [0, 1], clamp) * (1 - 0.75 * compactAt(frame));
	const near = interpolate(view.k, [1.6, 3.2], [0, 1], clamp);
	const lyon = toScreen(project([4.8357, 45.764]), view);
	const base = toScreen(project(PLACES.BASE.coords as LonLat), view);
	const pill = (x: number, y: number, text: string, color: string, o: number, key: string) => (
		<g key={key} opacity={o} transform={`translate(${x} ${y})`}>
			<rect x={14} y={-15} width={text.length * 11.5 + 18} height={30} rx={8} fill="rgba(7,11,16,0.85)" stroke={color} strokeWidth={1.5} />
			<text x={23} y={6.5} fontFamily={FONT_TITLE} fontWeight={800} fontSize={20} letterSpacing={1} fill={color}>
				{text}
			</text>
		</g>
	);
	return (
		<g opacity={reveal}>
			{pill(lyon.x - 120, lyon.y - 4, 'LYON', C.white, 1 - near, 'lyon')}
			{Object.values(AIRPORTS).map((ap) => {
				const p = toScreen(project(ap.arp as LonLat), view);
				// LYS se confond avec Lyon en vue France entière : affiché dès le zoom régional
				const o = ap.iata === 'LYS' ? near : 1;
				return (
					<g key={ap.iata} opacity={o}>
						<circle cx={p.x} cy={p.y} r={11} fill="#0B1118" stroke={C.white} strokeWidth={2} />
						<g transform={`translate(${p.x - 8} ${p.y - 8})`}>
							<Plane size={16} color={C.white} />
						</g>
						{pill(p.x, p.y, ap.iata, C.white, 1, `l${ap.iata}`)}
					</g>
				);
			})}
			<g opacity={near}>
				<circle cx={base.x} cy={base.y} r={14} fill={C.win} stroke="#fff" strokeWidth={2.5} />
				<g transform={`translate(${base.x - 9} ${base.y - 10})`}>
					<House size={18} color="#04140A" />
				</g>
				{pill(base.x, base.y + 2, 'BASE ASVEL', C.win, 1, 'base')}
			</g>
			{(['MEILLERAIE', 'SPORTICA', 'ASTROBALLE', 'BEAUBLANC'] as const).map((id) => {
				const p = toScreen(project(PLACES[id].coords as LonLat), view);
				return <rect key={id} x={p.x - 7} y={p.y - 7} width={14} height={14} transform={`rotate(45 ${p.x} ${p.y})`} fill={C.bg} stroke={C.white} strokeWidth={2} />;
			})}
		</g>
	);
};

export const Markers: React.FC = () => {
	const frame = useCurrentFrame();
	const view = cameraAt(frame);
	return (
		<>
			<svg width={WIDTH} height={HEIGHT} style={{position: 'absolute', inset: 0}}>
				<Places view={view} frame={frame} />
				{CARDS.map((s, i) => (
					<Leader key={i} s={s} />
				))}
				{/* Annonce à venir sous les pastilles de victoire */}
				{[...UPCOMINGS, ...RESULTS].map((s, i) => (
					<Dot key={i} s={s} />
				))}
			</svg>
			{CARDS.map((s, i) => (
				<Card key={i} s={s} />
			))}
		</>
	);
};
