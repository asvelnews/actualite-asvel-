import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {ACCOUNT, PLACES, TEAM} from '../data/tour';
import {formatDuration, formatKm} from '../lib/geo';
import {FINAL, LEGS, TOTAL_WINS} from '../lib/timeline';
import {C, FONT_TEXT, FONT_TITLE} from '../theme';
import {Bus, Check, Flame, House, Plane, Stadium} from './Icons';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const WIN_LEGS = LEGS.filter((l) => l.winNumber !== null);

/** Nombre de victoires affichées à l'image `frame`. */
const winsAt = (frame: number) => WIN_LEGS.filter((l) => frame >= l.resultStart + 4).length;

// ── En-tête : titre + compteur ───────────────────────────────────────────────
export const Header: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const intro = spring({frame: frame - 4, fps, config: {damping: 16}});
	const wins = winsAt(frame);
	const lastWin = WIN_LEGS[wins - 1];
	const bump = lastWin ? spring({frame: frame - lastWin.resultStart - 4, fps, config: {damping: 9, stiffness: 180}}) : 1;
	const pop = lastWin ? 1 + 0.22 * Math.sin(Math.PI * Math.min(bump, 1)) * (1 - Math.min((frame - lastWin.resultStart - 4) / 20, 1)) : 1;
	return (
		<div
			style={{
				position: 'absolute',
				left: 48,
				right: 48,
				top: 120,
				height: 200,
				display: 'flex',
				justifyContent: 'space-between',
				alignItems: 'flex-start',
				opacity: intro,
				transform: `translateY(${(1 - intro) * -40}px)`,
			}}
		>
			<div style={{fontFamily: FONT_TITLE, color: C.white}}>
				<div style={{fontSize: 26, fontWeight: 700, letterSpacing: 6, color: C.win}}>{ACCOUNT}</div>
				<div style={{fontSize: 112, fontWeight: 800, lineHeight: 0.92, letterSpacing: 1}}>
					{TEAM} <span style={{color: C.win}}>TOUR</span>
				</div>
				<div style={{fontFamily: FONT_TEXT, fontSize: 22, fontWeight: 700, color: C.muted, letterSpacing: 3, marginTop: 8}}>LA SÉRIE EN CARTE</div>
			</div>
			<div style={{textAlign: 'right', fontFamily: FONT_TITLE, color: C.white}}>
				<div style={{fontSize: 24, fontWeight: 700, letterSpacing: 4, color: C.muted}}>VICTOIRES</div>
				<div style={{fontSize: 112, fontWeight: 800, lineHeight: 0.92, transform: `scale(${pop})`, transformOrigin: 'right center'}}>
					<span style={{color: wins > 0 ? C.win : C.white}}>{wins}</span>
					<span style={{color: C.dim}}>/{TOTAL_WINS}</span>
				</div>
				<div style={{display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 10}}>
					{WIN_LEGS.map((l, i) => (
						<div key={i} style={{width: 40, height: 9, borderRadius: 5, background: i < wins ? C.win : C.dim}} />
					))}
				</div>
			</div>
		</div>
	);
};

// ── Bandeau de trajet (vol / bus) ────────────────────────────────────────────
export const TravelChip: React.FC = () => {
	const frame = useCurrentFrame();
	const leg = LEGS.find((l) => frame >= l.focusStart && frame < l.resultStart + 10);
	if (!leg) return null;
	const isBus = frame >= leg.zoomStart;
	const seg = isBus ? leg.bus : leg.flight;
	const segStart = isBus ? leg.zoomStart : leg.focusStart;
	const segEnd = isBus ? leg.resultStart + 10 : leg.zoomStart;
	const o = interpolate(frame, [segStart, segStart + 8, segEnd - 8, segEnd], [0, 1, 1, 0], clamp);
	const Icon = isBus ? Bus : Plane;
	const stage = `ÉTAPE ${leg.index + 1} · ${PLACES[leg.game.arena].city.toUpperCase()}`;
	return (
		<div
			style={{
				position: 'absolute',
				left: 48,
				right: 48,
				top: 352,
				height: 92,
				borderRadius: 20,
				background: C.panel,
				border: `2px solid ${C.panelEdge}`,
				display: 'flex',
				alignItems: 'center',
				gap: 20,
				padding: '0 24px',
				opacity: o,
				transform: `translateY(${(1 - o) * -16}px)`,
				boxSizing: 'border-box',
			}}
		>
			<div style={{width: 60, height: 60, borderRadius: 14, background: isBus ? C.win : C.white, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
				<Icon size={40} color={C.bg} />
			</div>
			<div style={{flex: 1, minWidth: 0}}>
				<div style={{fontFamily: FONT_TEXT, fontSize: 18, fontWeight: 700, letterSpacing: 2, color: C.win}}>
					{stage} · {isBus ? 'BUS' : 'VOL'}
				</div>
				<div style={{fontFamily: FONT_TITLE, fontSize: 32, fontWeight: 700, color: C.white, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>
					{seg.fromName.toUpperCase()} → {seg.toName.toUpperCase().replace('PALAIS DES SPORTS DE ', '')}
				</div>
			</div>
			<div style={{textAlign: 'right', fontFamily: FONT_TITLE, color: C.white, lineHeight: 1}}>
				<div style={{fontSize: 34, fontWeight: 800, fontVariantNumeric: 'tabular-nums'}}>{isBus ? '≈ ' : ''}{formatKm(seg.km)}</div>
				<div style={{fontSize: 22, fontWeight: 700, color: C.muted}}>≈ {formatDuration(seg.minutes)}</div>
			</div>
		</div>
	);
};

// ── Tableau des victoires (permanent), puis bilan final ─────────────────────
const SLOT_W = 480;
const SLOT_H = 78;
const GAP = 24;

export const Scoreboard: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const intro = interpolate(frame, [20, 45], [0, 1], clamp);
	const t = interpolate(frame, [FINAL.list, FINAL.list + 30], [0, 1], {...clamp, easing: (x) => x * x * (3 - 2 * x)});
	const top = 1440 + (1022 - 1440) * t;
	const titleO = interpolate(frame, [FINAL.list + 15, FINAL.list + 35], [0, 1], clamp);
	return (
		<div style={{position: 'absolute', left: 48, width: 984, top, opacity: intro}}>
			<div
				style={{
					position: 'absolute',
					top: -44,
					fontFamily: FONT_TITLE,
					fontSize: 30,
					fontWeight: 800,
					letterSpacing: 4,
					color: C.white,
					opacity: titleO,
				}}
			>
				LES {TOTAL_WINS} VICTOIRES
			</div>
			<div style={{display: 'flex', flexWrap: 'wrap', gap: GAP}}>
				{WIN_LEGS.map((leg, i) => {
					const on = frame >= leg.resultStart + 4;
					const p = on ? spring({frame: frame - leg.resultStart - 4, fps, config: {damping: 13}}) : 0;
					// Séquence finale : les 4 lignes s'illuminent ensemble
					const flash = interpolate(frame, [FINAL.list + 30 + i * 6, FINAL.list + 42 + i * 6, FINAL.list + 70 + i * 6], [0, 1, 0], clamp);
					return (
						<div
							key={i}
							style={{
								width: SLOT_W,
								height: SLOT_H,
								borderRadius: 16,
								boxSizing: 'border-box',
								border: `2px ${on ? 'solid' : 'dashed'} ${on ? C.win : C.dim}`,
								background: on ? `rgba(31, 209, 107, ${0.1 + flash * 0.25})` : 'rgba(10,16,23,0.7)',
								display: 'flex',
								alignItems: 'center',
								padding: '0 18px',
								gap: 14,
								fontFamily: FONT_TITLE,
								color: C.white,
							}}
						>
							<div
								style={{
									width: 42,
									height: 42,
									borderRadius: 21,
									background: on ? C.win : 'transparent',
									border: on ? 'none' : `2px solid ${C.dim}`,
									color: on ? '#04140A' : C.dim,
									fontSize: 26,
									fontWeight: 800,
									display: 'flex',
									alignItems: 'center',
									justifyContent: 'center',
									flexShrink: 0,
								}}
							>
								{i + 1}
							</div>
							{on ? (
								<div style={{display: 'flex', alignItems: 'center', flex: 1, gap: 12, opacity: p, transform: `translateX(${(1 - p) * 30}px)`}}>
									<div style={{fontSize: 34, fontWeight: 800, letterSpacing: 1, flex: 1}}>{leg.game.opponent.toUpperCase()} :</div>
									<div style={{fontSize: 40, fontWeight: 800, fontVariantNumeric: 'tabular-nums'}}>
										{leg.game.score!.asvel}-{leg.game.score!.opponent}
									</div>
									<Check size={34} bg={C.win} color="#04140A" />
								</div>
							) : (
								<div style={{fontSize: 26, fontWeight: 700, letterSpacing: 3, color: C.dim}}>VICTOIRE {i + 1}</div>
							)}
						</div>
					);
				})}
			</div>
		</div>
	);
};

// ── Statistiques calculées à partir des résultats ───────────────────────────
const played = LEGS.filter((l) => l.game.score);
let streak = 0;
for (let i = played.length - 1; i >= 0 && played[i].winNumber !== null; i--) streak++;
const awayWins = WIN_LEGS.filter((l) => !l.game.home).length;
const homeWins = WIN_LEGS.filter((l) => l.game.home).length;
const plural = (n: number, s: string, p: string) => (n > 1 ? p : s);

const STATS = [
	{value: streak, text: plural(streak, 'VICTOIRE CONSÉCUTIVE', 'VICTOIRES CONSÉCUTIVES'), Icon: Flame, color: '#FF6A2B'},
	{value: awayWins, text: `${plural(awayWins, 'VICTOIRE', 'VICTOIRES')} À L'EXTÉRIEUR`, Icon: Plane, color: C.white},
	{value: homeWins, text: `${plural(homeWins, 'VICTOIRE', 'VICTOIRES')} À DOMICILE`, Icon: House, color: C.white},
];

export const Stats: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	if (frame < FINAL.stats) return null;
	return (
		<div style={{position: 'absolute', left: 48, width: 984, top: 1236, display: 'flex', flexDirection: 'column', gap: 12}}>
			{STATS.map((s, i) => {
				const p = spring({frame: frame - FINAL.stats - i * 12, fps, config: {damping: 14}});
				return (
					<div
						key={i}
						style={{
							height: 58,
							display: 'flex',
							alignItems: 'center',
							gap: 18,
							opacity: p,
							transform: `translateX(${(1 - p) * -60}px)`,
							fontFamily: FONT_TITLE,
							color: C.white,
						}}
					>
						<div style={{fontSize: 60, fontWeight: 800, color: C.win, width: 60, textAlign: 'center', lineHeight: 1}}>{s.value}</div>
						<div style={{fontSize: 42, fontWeight: 800, letterSpacing: 1, flex: 1}}>{s.text}</div>
						<s.Icon size={46} color={s.color} />
					</div>
				);
			})}
		</div>
	);
};

const NEXT = LEGS.find((l) => !l.game.score);

export const NextMatch: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	if (!NEXT || frame < FINAL.next) return null;
	const p = spring({frame: frame - FINAL.next, fps, config: {damping: 15}});
	const glow = 0.5 + 0.5 * Math.sin((frame - FINAL.next) / 8);
	const g = NEXT.game;
	return (
		<div
			style={{
				position: 'absolute',
				left: 48,
				width: 984,
				top: 1450,
				height: 200,
				borderRadius: 24,
				border: `3px solid ${C.upcoming}`,
				boxShadow: `0 0 ${30 + glow * 30}px rgba(255, 184, 0, ${0.25 + glow * 0.2})`,
				background: C.panel,
				boxSizing: 'border-box',
				padding: '20px 30px',
				opacity: p,
				transform: `translateY(${(1 - p) * 60}px)`,
				fontFamily: FONT_TITLE,
				color: C.white,
				display: 'flex',
				alignItems: 'center',
			}}
		>
			<div style={{flex: 1}}>
				<div style={{fontSize: 30, fontWeight: 800, letterSpacing: 5, color: C.upcoming}}>PROCHAIN MATCH :</div>
				<div style={{fontSize: 80, fontWeight: 800, lineHeight: 1}}>
					{g.home ? `${TEAM} vs ${g.opponent.toUpperCase()}` : `${g.opponent.toUpperCase()} vs ${TEAM}`}
				</div>
				<div style={{fontSize: 34, fontWeight: 700, letterSpacing: 3, color: C.muted}}>{PLACES[g.arena].name.toUpperCase()}</div>
			</div>
			<Stadium size={110} color={C.upcoming} />
		</div>
	);
};
