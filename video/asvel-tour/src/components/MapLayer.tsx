import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {C} from '../theme';
import {francePath, neighbourPaths, along, partial, project, type Pt} from '../lib/geo';
import {FINAL, HEIGHT, LEGS, WIDTH, cameraAt, mapTransform, toScreen, type Leg} from '../lib/timeline';
import {BusTop, PlaneTop} from './Icons';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const polyline = (pts: Pt[]) => pts.map((p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(' ');

/** Trajet d'une étape : tracé progressif, puis ligne discrète permanente. */
const Route: React.FC<{leg: Leg; frame: number}> = ({leg, frame}) => {
	if (frame < leg.flightStart) return null;
	const flightT = interpolate(frame, [leg.flightStart, leg.zoomStart], [0, 1], clamp);
	const busT = interpolate(frame, [leg.busStart, leg.resultStart], [0, 1], clamp);
	// L'étape en cours est vive ; elle devient discrète une fois le résultat affiché.
	const live = interpolate(frame, [leg.resultStart + 20, leg.end], [1, 0], clamp);
	const opacity = 0.32 + 0.68 * live;
	const width = 1.6 + 2.4 * live;
	return (
		<g>
			<polyline
				points={polyline(partial(leg.flight.pts, flightT))}
				fill="none"
				stroke={C.route}
				strokeOpacity={opacity}
				strokeWidth={width}
				strokeDasharray={live > 0.05 ? undefined : '6 7'}
				strokeLinecap="round"
				vectorEffect="non-scaling-stroke"
			/>
			{busT > 0 ? (
				<polyline
					points={polyline(partial(leg.bus.pts, busT))}
					fill="none"
					stroke={C.win}
					strokeOpacity={opacity}
					strokeWidth={width + 1}
					strokeDasharray="2 9"
					strokeLinecap="round"
					vectorEffect="non-scaling-stroke"
				/>
			) : null}
		</g>
	);
};

const Vehicles: React.FC<{frame: number}> = ({frame}) => {
	const view = cameraAt(frame);
	return (
		<>
			{LEGS.map((leg) => {
				const out: React.ReactNode[] = [];
				if (frame >= leg.flightStart - 8 && frame <= leg.zoomStart + 8) {
					const t = interpolate(frame, [leg.flightStart, leg.zoomStart], [0, 1], clamp);
					const pos = along(leg.flight.pts, t);
					const s = toScreen(pos, view);
					const alt = Math.sin(Math.PI * t); // altitude stylisée : l'avion grossit en croisière
					const fade = interpolate(frame, [leg.flightStart - 8, leg.flightStart, leg.zoomStart, leg.zoomStart + 8], [0, 1, 1, 0], clamp);
					out.push(
						<g key={`p${leg.index}`} opacity={fade}>
							<g transform={`translate(${s.x + 10 + alt * 16} ${s.y + 14 + alt * 22}) rotate(${pos.angle})`} opacity={0.35}>
								<PlaneTop size={46 + alt * 10} color="#000" />
							</g>
							<g transform={`translate(${s.x} ${s.y}) rotate(${pos.angle})`}>
								<PlaneTop size={50 + alt * 18} color={C.white} />
							</g>
						</g>,
					);
				}
				if (frame >= leg.busStart - 10 && frame <= leg.resultStart + 18) {
					const t = interpolate(frame, [leg.busStart, leg.resultStart], [0, 1], {...clamp, easing: (x) => x * x * (3 - 2 * x)});
					const pos = along(leg.bus.pts, t);
					const s = toScreen(pos, view);
					const fade = interpolate(frame, [leg.busStart - 10, leg.busStart, leg.resultStart + 4, leg.resultStart + 18], [0, 1, 1, 0], clamp);
					out.push(
						<g key={`b${leg.index}`} opacity={fade} transform={`translate(${s.x} ${s.y}) rotate(${pos.angle})`}>
							<BusTop size={58} color={C.white} accent={C.win} />
						</g>,
					);
				}
				return out;
			})}
		</>
	);
};

/** Anneaux « radar » autour de la salle pendant l'arrivée du bus. */
const ArrivalRings: React.FC<{frame: number}> = ({frame}) => {
	const view = cameraAt(frame);
	return (
		<>
			{LEGS.map((leg) => {
				if (frame < leg.zoomStart || frame > leg.resultStart + 30) return null;
				const s = toScreen(project(leg.arena), view);
				const fade = interpolate(frame, [leg.zoomStart, leg.busStart, leg.resultStart, leg.resultStart + 30], [0, 1, 1, 0], clamp);
				const color = leg.game.score ? C.win : C.upcoming;
				return (
					<g key={leg.index} opacity={fade}>
						{[0, 1, 2].map((i) => {
							const phase = ((frame - leg.zoomStart) / 36 + i / 3) % 1;
							return <circle key={i} cx={s.x} cy={s.y} r={30 + phase * 190} fill="none" stroke={color} strokeWidth={2} opacity={(1 - phase) * 0.5} />;
						})}
					</g>
				);
			})}
		</>
	);
};

export const MapLayer: React.FC = () => {
	const frame = useCurrentFrame();
	const view = cameraAt(frame);
	const reveal = interpolate(frame, [0, 45], [0, 1], clamp);
	const fill = interpolate(frame, [15, 50], [0, 1], clamp);
	return (
		<svg width={WIDTH} height={HEIGHT} style={{position: 'absolute', inset: 0}}>
			<defs>
				<radialGradient id="bgGrad" cx="50%" cy="46%" r="70%">
					<stop offset="0%" stopColor={C.bg2} />
					<stop offset="100%" stopColor={C.bg} />
				</radialGradient>
				<linearGradient id="landGrad" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stopColor="#1C2A38" />
					<stop offset="100%" stopColor="#152029" />
				</linearGradient>
			</defs>
			<rect width={WIDTH} height={HEIGHT} fill="url(#bgGrad)" />
			<g transform={mapTransform(view)}>
				{neighbourPaths.map((d, i) => (
					<path key={i} d={d} fill={C.neighbour} stroke={C.neighbourEdge} strokeWidth={1} vectorEffect="non-scaling-stroke" opacity={fill} />
				))}
				<path d={francePath} fill="url(#landGrad)" fillOpacity={fill} stroke="none" />
				<path
					d={francePath}
					fill="none"
					stroke={C.landEdge}
					strokeWidth={2}
					vectorEffect="non-scaling-stroke"
					pathLength={1}
					strokeDasharray={`${reveal} 1`}
					strokeLinejoin="round"
				/>
				{LEGS.map((leg) => (
					<Route key={leg.index} leg={leg} frame={frame} />
				))}
			</g>
			<ArrivalRings frame={frame} />
			{frame < FINAL.zoom ? <Vehicles frame={frame} /> : null}
		</svg>
	);
};
