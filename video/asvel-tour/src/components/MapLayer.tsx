import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {AIRPORTS, type LonLat} from '../data/tour';
import {departementPaths, neighbourPaths, partial, project, pxPerKm, smoothAngle, along, type Pt} from '../lib/geo';
import {BUSES, FLIGHTS, HEIGHT, WIDTH, busProgress, cameraAt, mapTransform, planeAt, toScreen, type Tone, type View} from '../lib/timeline';
import {C, FONT_TITLE} from '../theme';
import {Atr42, Coach} from './Vehicles';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const TONE: Record<Tone, string> = {aller: C.win, retour: C.white, upcoming: C.upcoming};

const polyline = (pts: Pt[]) => pts.map((p) => `${p.x.toFixed(3)},${p.y.toFixed(3)}`).join(' ');

/** Trajet : tracé vif pendant le déplacement, puis ligne discrète permanente. */
const RouteLine: React.FC<{pts: Pt[]; tone: Tone; live: number; dash?: string}> = ({pts, tone, live, dash}) => (
	<polyline
		points={polyline(pts)}
		fill="none"
		stroke={TONE[tone]}
		strokeOpacity={0.42 + 0.53 * live}
		strokeWidth={2 + 2 * live}
		strokeDasharray={dash}
		strokeLinecap="round"
		strokeLinejoin="round"
		vectorEffect="non-scaling-stroke"
	/>
);

const Routes: React.FC<{frame: number}> = ({frame}) => (
	<>
		{FLIGHTS.map((s, i) => {
			if (frame < s.t.rollStart) return null;
			const live = interpolate(frame, [s.end, s.end + 30], [1, 0], clamp);
			const st = planeAt(s, Math.min(frame, s.end));
			return <RouteLine key={`f${i}`} pts={partial(s.lines.all, st.travelled)} tone={s.tone} live={live} />;
		})}
		{BUSES.map((s, i) => {
			if (frame < s.moveStart) return null;
			const live = interpolate(frame, [s.end, s.end + 30], [1, 0], clamp);
			return <RouteLine key={`b${i}`} pts={partial(s.line, busProgress(s, frame))} tone={s.tone} live={live} dash="1 0" />;
		})}
	</>
);

/** Pistes réelles (seuils OurAirports), dessinées quand la caméra est assez proche. */
const Runways: React.FC<{view: View}> = ({view}) => (
	<>
		{Object.values(AIRPORTS).map((ap) => {
			const a = toScreen(project(ap.runway.ends[0] as LonLat), view);
			const b = toScreen(project(ap.runway.ends[1] as LonLat), view);
			const len = Math.hypot(b.x - a.x, b.y - a.y);
			const o = interpolate(len, [40, 140], [0, 1], clamp);
			if (o <= 0) return null;
			const ang = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
			// Largeur exagérée pour la lisibilité (45 m réels)
			const w = Math.min(Math.max(((ap.runway.widthM * pxPerKm(ap.arp as LonLat)) / 1000) * view.k * 3, 10), 30);
			const cx = (a.x + b.x) / 2;
			const cy = (a.y + b.y) / 2;
			const nBars = 6;
			return (
				<g key={ap.iata} opacity={o} transform={`translate(${cx} ${cy}) rotate(${ang})`}>
					<rect x={-len / 2 - 6} y={-w / 2 - 6} width={len + 12} height={w + 12} rx={4} fill="#0E141A" opacity={0.85} />
					<rect x={-len / 2} y={-w / 2} width={len} height={w} fill="#2B323A" stroke="#C9D2DB" strokeWidth={1} />
					<line x1={-len / 2 + w * 2.4} y1={0} x2={len / 2 - w * 2.4} y2={0} stroke="#F4F7FA" strokeWidth={Math.max(w * 0.08, 1.2)} strokeDasharray={`${w * 1.2} ${w * 0.9}`} />
					{[-1, 1].map((side) =>
						Array.from({length: nBars}, (_, i) => (
							<rect
								key={`${side}${i}`}
								x={side < 0 ? -len / 2 + w * 0.3 : len / 2 - w * 0.3 - w * 0.9}
								y={-w / 2 + (w / nBars) * (i + 0.2)}
								width={w * 0.9}
								height={(w / nBars) * 0.55}
								fill="#F4F7FA"
							/>
						)),
					)}
					{[0, 1].map((e) => (
						<text
							key={e}
							x={e === 0 ? -len / 2 + w * 1.7 : len / 2 - w * 1.7}
							y={0}
							transform={`rotate(${e === 0 ? 90 : -90} ${e === 0 ? -len / 2 + w * 1.7 : len / 2 - w * 1.7} 0)`}
							textAnchor="middle"
							dominantBaseline="central"
							fontFamily={FONT_TITLE}
							fontWeight={800}
							fontSize={Math.max(w * 0.55, 9)}
							fill="#F4F7FA"
						>
							{ap.runway.ids[e]}
						</text>
					))}
				</g>
			);
		})}
	</>
);

const Plane: React.FC<{frame: number; view: View}> = ({frame, view}) => {
	const s = FLIGHTS.find((f) => frame >= f.start && frame < f.end);
	if (!s) return null;
	const st = planeAt(s, frame);
	const p = toScreen(st.pos, view);
	const fade = interpolate(frame, [s.start, s.start + 8, s.end - 6, s.end], [0, 1, 1, 0], clamp);
	const len = 140 + st.alt * 40;
	return (
		<g opacity={fade}>
			<g transform={`translate(${p.x + 3 + st.alt * 30} ${p.y + 4 + st.alt * 40}) rotate(${st.angle})`} opacity={0.38 - st.alt * 0.14}>
				<Atr42 lengthPx={len * (1 - st.alt * 0.12)} gear={0} shadow />
			</g>
			<g transform={`translate(${p.x} ${p.y}) rotate(${st.angle})`}>
				<Atr42 lengthPx={len} gear={st.gear} propPhase={frame * 0.9} />
			</g>
		</g>
	);
};

const Bus: React.FC<{frame: number; view: View}> = ({frame, view}) => {
	const s = BUSES.find((b) => frame >= b.start && frame < b.end);
	if (!s) return null;
	const u = busProgress(s, frame);
	const pos = along(s.line, u);
	const p = toScreen(pos, view);
	const ang = smoothAngle(s.line, u, 0.015);
	const left = Math.abs(ang) > 90;
	const raw = left ? (ang > 0 ? ang - 180 : ang + 180) : ang;
	const tilt = Math.max(-24, Math.min(24, raw));
	const fade = interpolate(frame, [s.start, s.start + 14, s.end - 8, s.end], [0, 1, 1, 0], clamp);
	const wheelRot = (u * s.km * 1000) / 3.2 * 57.3 * 0.02;
	const braking = frame >= s.moveStart && (frame - s.moveStart) / (s.moveEnd - s.moveStart) > 0.72 && u < 1;
	return (
		<g opacity={fade} transform={`translate(${p.x} ${p.y - 17}) rotate(${tilt}) scale(${left ? -1 : 1} 1)`}>
			<Coach wheelRot={wheelRot} braking={braking} />
		</g>
	);
};

export const MapLayer: React.FC = () => {
	const frame = useCurrentFrame();
	const view = cameraAt(frame);
	const reveal = interpolate(frame, [0, 70], [0, 1], clamp);
	return (
		<svg width={WIDTH} height={HEIGHT} style={{position: 'absolute', inset: 0}}>
			<defs>
				<radialGradient id="bgGrad" cx="50%" cy="42%" r="75%">
					<stop offset="0%" stopColor={C.bg2} />
					<stop offset="100%" stopColor={C.bg} />
				</radialGradient>
			</defs>
			<rect width={WIDTH} height={HEIGHT} fill="url(#bgGrad)" />
			<g transform={mapTransform(view)}>
				{neighbourPaths.map((d, i) => (
					<path key={i} d={d} fill={C.neighbour} stroke={C.neighbourEdge} strokeWidth={1} vectorEffect="non-scaling-stroke" opacity={reveal} />
				))}
				<g opacity={reveal}>
					{departementPaths.map((d, i) => (
						<path key={i} d={d} fill={C.land} stroke={C.landEdge} strokeWidth={0.8} strokeOpacity={0.55} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
					))}
				</g>
				<Routes frame={frame} />
			</g>
			<Runways view={view} />
			<Bus frame={frame} view={view} />
			<Plane frame={frame} view={view} />
		</svg>
	);
};
