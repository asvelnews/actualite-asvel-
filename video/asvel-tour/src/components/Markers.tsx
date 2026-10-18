import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {PLACES, TEAM} from '../data/tour';
import {project} from '../lib/geo';
import {FINAL, HEIGHT, LEGS, WIDTH, cameraAt, toScreen, type Leg} from '../lib/timeline';
import {C, FONT_TEXT, FONT_TITLE} from '../theme';
import {Check} from './Icons';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const CARD_W = 268;
const CARD_H = 124;

/** Facteur de réduction des étiquettes pour la vue finale compacte. */
const compactAt = (frame: number) => interpolate(frame, [FINAL.list, FINAL.list + 30], [0, 1], clamp);

const useAppear = (leg: Leg) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	return spring({frame: frame - leg.resultStart, fps, config: {damping: 14, stiffness: 140, mass: 0.7}});
};

const cardGeometry = (leg: Leg, frame: number) => {
	const view = cameraAt(frame);
	const anchor = toScreen(project(leg.arena), view);
	const compact = compactAt(frame);
	const scale = 1 - 0.3 * compact;
	const off = 1 - 0.36 * compact;
	const cx = anchor.x + leg.game.label.dx * off;
	const cy = anchor.y + leg.game.label.dy * off;
	return {anchor, cx, cy, scale};
};

const Leader: React.FC<{leg: Leg}> = ({leg}) => {
	const frame = useCurrentFrame();
	const p = useAppear(leg);
	if (frame < leg.resultStart) return null;
	const {anchor, cx, cy} = cardGeometry(leg, frame);
	const color = leg.winNumber !== null ? C.win : leg.game.score ? C.loss : C.upcoming;
	const ex = anchor.x + (cx - anchor.x) * Math.min(p, 1);
	const ey = anchor.y + (cy - anchor.y) * Math.min(p, 1);
	return <line x1={anchor.x} y1={anchor.y} x2={ex} y2={ey} stroke={color} strokeWidth={2.5} strokeOpacity={0.85} />;
};

const Dot: React.FC<{leg: Leg}> = ({leg}) => {
	const frame = useCurrentFrame();
	const p = useAppear(leg);
	if (frame < leg.resultStart) return null;
	const {anchor} = cardGeometry(leg, frame);
	const pulse = (frame - leg.resultStart) / 45;
	if (leg.winNumber === null && !leg.game.score) {
		// Match à venir : anneau doré pointillé autour de la salle
		return (
			<g transform={`translate(${anchor.x} ${anchor.y}) scale(${p})`}>
				<circle r={30} fill="none" stroke={C.upcoming} strokeWidth={3} strokeDasharray="6 5" transform={`rotate(${frame * 2})`} />
			</g>
		);
	}
	const color = leg.winNumber !== null ? C.win : C.loss;
	return (
		<g transform={`translate(${anchor.x} ${anchor.y})`}>
			<circle r={18 + (pulse % 1) * 26} fill="none" stroke={color} strokeWidth={2} opacity={(1 - (pulse % 1)) * 0.6} />
			<g transform={`scale(${p})`}>
				<circle r={19} fill={color} stroke="#fff" strokeWidth={3} />
				<text y={8} textAnchor="middle" fontFamily={FONT_TITLE} fontWeight={800} fontSize={24} fill="#04140A">
					{leg.winNumber ?? '–'}
				</text>
			</g>
		</g>
	);
};

const Card: React.FC<{leg: Leg}> = ({leg}) => {
	const frame = useCurrentFrame();
	const p = useAppear(leg);
	if (frame < leg.resultStart) return null;
	const {cx, cy, scale} = cardGeometry(leg, frame);
	const arena = PLACES[leg.game.arena];
	const base: React.CSSProperties = {
		position: 'absolute',
		left: cx - CARD_W / 2,
		top: cy - CARD_H / 2,
		width: CARD_W,
		height: CARD_H,
		transform: `scale(${scale * (0.6 + 0.4 * p)})`,
		opacity: Math.min(p * 1.4, 1),
		borderRadius: 18,
		boxSizing: 'border-box',
		boxShadow: '0 14px 40px rgba(0,0,0,0.55)',
		fontFamily: FONT_TITLE,
		color: C.white,
		overflow: 'hidden',
	};

	if (!leg.game.score) {
		return (
			<div style={{...base, background: C.panel, border: `3px solid ${C.upcoming}`, padding: '12px 18px'}}>
				<div style={{fontSize: 22, fontWeight: 800, letterSpacing: 3, color: C.upcoming}}>À VENIR</div>
				<div style={{fontSize: 38, fontWeight: 800, lineHeight: 1.05, whiteSpace: 'nowrap'}}>
					{leg.game.home ? `${TEAM} vs ${leg.game.opponent.toUpperCase()}` : `${leg.game.opponent.toUpperCase()} vs ${TEAM}`}
				</div>
				<div style={{fontFamily: FONT_TEXT, fontSize: 17, fontWeight: 700, color: C.muted, letterSpacing: 1.5}}>{arena.name.toUpperCase()}</div>
			</div>
		);
	}

	const won = leg.winNumber !== null;
	const color = won ? C.win : C.loss;
	return (
		<div style={{...base, background: C.panel, border: `3px solid ${color}`, display: 'flex'}}>
			<div
				style={{
					width: 66,
					background: color,
					color: '#04140A',
					display: 'flex',
					flexDirection: 'column',
					alignItems: 'center',
					justifyContent: 'center',
					lineHeight: 1,
				}}
			>
				<div style={{fontSize: 14, fontWeight: 800, letterSpacing: 0.5}}>{won ? 'VICT.' : 'DÉF.'}</div>
				<div style={{fontSize: 46, fontWeight: 800}}>{leg.winNumber ?? '–'}</div>
			</div>
			<div style={{flex: 1, padding: '10px 14px 0 14px', position: 'relative'}}>
				<div style={{fontSize: 27, fontWeight: 800, letterSpacing: 1, lineHeight: 1}}>{leg.game.opponent.toUpperCase()}</div>
				<div style={{fontSize: 52, fontWeight: 800, lineHeight: 1, marginTop: 3, fontVariantNumeric: 'tabular-nums'}}>
					{leg.game.score.asvel}-{leg.game.score.opponent}
				</div>
				<div style={{fontFamily: FONT_TEXT, fontSize: 14, fontWeight: 700, color: C.muted, letterSpacing: 1, marginTop: 2, whiteSpace: 'nowrap'}}>
					{arena.name.toUpperCase().replace('PALAIS DES SPORTS DE ', '')} · {leg.game.home ? 'DOMICILE' : 'EXTÉRIEUR'}
				</div>
				{won ? <Check size={38} bg={C.win} color="#04140A" style={{position: 'absolute', right: 12, top: 12}} /> : null}
			</div>
		</div>
	);
};

export const Markers: React.FC = () => {
	return (
		<>
			<svg width={WIDTH} height={HEIGHT} style={{position: 'absolute', inset: 0}}>
				{LEGS.map((leg) => (
					<Leader key={leg.index} leg={leg} />
				))}
				{/* Les matchs à venir d'abord, pour que les pastilles de victoire restent au premier plan */}
				{[...LEGS].sort((a, b) => Number(!!a.game.score) - Number(!!b.game.score)).map((leg) => (
					<Dot key={leg.index} leg={leg} />
				))}
			</svg>
			{LEGS.map((leg) => (
				<Card key={leg.index} leg={leg} />
			))}
		</>
	);
};
