// Véhicules vectoriels dessinés à la main (aucune image, aucun emoji).
import React from 'react';
import {C, FONT_TITLE} from '../theme';

// ── ATR 42-600, vue de dessus ───────────────────────────────────────────────
// Unités : mètres, nez vers +x, origine au centre de l'appareil.
// Cotes de référence (ATR) : longueur 22,67 m, envergure 24,57 m, aile haute,
// deux turbopropulseurs PW127 à hélices six pales (Ø 3,93 m), empennage en T,
// train principal logé dans des carénages latéraux.
const ATR_FUSELAGE =
	'M11.35 0C11.35-.75 10.6-1.29 9.2-1.29L-4.8-1.29C-7.6-1.15-10-.62-11.3-.24L-11.3.24C-10 .62-7.6 1.15-4.8 1.29L9.2 1.29C10.6 1.29 11.35.75 11.35 0Z';
const ATR_WINGS = 'M1.45 1.2L.95 12.2L-.45 12.28L-1.15 1.2ZM1.45-1.2L.95-12.2L-.45-12.28L-1.15-1.2Z';
const ATR_STAB = 'M-9.5 0L-10.45 3.6L-11.15 3.65L-11.05 0L-11.15-3.65L-10.45-3.6Z';
const ATR_FLAPS = 'M-1.12 1.6L-.7 8.4M-1.12-1.6L-.7-8.4';
const ATR_AILERONS = 'M-.66 8.9L-.47 11.9M-.66-8.9L-.47-11.9';
const PROP_R = 1.965;

const AtrEngine: React.FC<{side: 1 | -1; propPhase: number}> = ({side, propPhase}) => {
	const y = side * 4.1;
	return (
		<g>
			{/* Nacelle */}
			<path d={`M4.2 ${y - 0.42}Q4.55 ${y} 4.2 ${y + 0.42}L3.2 ${y + 0.62}L-2.7 ${y + 0.5}Q-3.3 ${y} -2.7 ${y - 0.5}L3.2 ${y - 0.62}Z`} fill="#E7ECF1" stroke="#5E6973" strokeWidth={0.07} />
			<rect x={-1.4} y={y - 0.08} width={2.6} height={0.16} fill="#AEB8C2" />
			{/* Disque d'hélice vu de dessus (flou de rotation) */}
			<rect x={4.45} y={y - PROP_R} width={0.22} height={PROP_R * 2} rx={0.11} fill="#C9D2DB" opacity={0.35} />
			{/* Six pales : projection animée sur le plan de vue */}
			{Array.from({length: 6}, (_, i) => {
				const l = PROP_R * Math.cos(propPhase + (i * Math.PI) / 3);
				return <rect key={i} x={4.47} y={y + Math.min(0, l)} width={0.18} height={Math.abs(l)} fill="#1A2129" opacity={0.75} />;
			})}
			<ellipse cx={4.62} cy={y} rx={0.32} ry={0.3} fill={C.win} stroke="#0B0F14" strokeWidth={0.05} />
		</g>
	);
};

export const Atr42: React.FC<{lengthPx: number; gear: number; propPhase?: number; shadow?: boolean}> = ({lengthPx, gear, propPhase = 0, shadow}) => {
	const s = lengthPx / 22.67;
	if (shadow) {
		return (
			<g transform={`scale(${s})`} fill="#000">
				<path d={ATR_FUSELAGE} />
				<path d={ATR_WINGS} />
				<path d={ATR_STAB} />
				<rect x={-2.7} y={3.5} width={7.2} height={1.2} rx={0.5} />
				<rect x={-2.7} y={-4.7} width={7.2} height={1.2} rx={0.5} />
			</g>
		);
	}
	return (
		<g transform={`scale(${s})`}>
			{/* Train d'atterrissage (visible quand il est sorti) */}
			<g opacity={gear} fill="#151A20">
				<rect x={-0.9} y={1.5} width={1.1} height={0.55} rx={0.2} />
				<rect x={-0.9} y={-2.05} width={1.1} height={0.55} rx={0.2} />
				<rect x={8.6} y={-0.28} width={0.8} height={0.56} rx={0.2} />
			</g>
			<path d={ATR_FUSELAGE} fill="#F7F9FB" stroke="#5E6973" strokeWidth={0.08} />
			{/* Carénages du train principal */}
			<path d="M2.2 1.25Q.2 1.62-2.6 1.55L-2.6 1.25Z" fill="#DDE3E9" stroke="#5E6973" strokeWidth={0.06} />
			<path d="M2.2-1.25Q.2-1.62-2.6-1.55L-2.6-1.25Z" fill="#DDE3E9" stroke="#5E6973" strokeWidth={0.06} />
			{/* Bande dorsale verte et noire */}
			<path d="M8.6-.3L-9.6-.2L-9.6.2L8.6.3Z" fill={C.win} />
			<path d="M8.6-.09L-9.6-.05L-9.6.05L8.6.09Z" fill="#0B0F14" />
			{/* Aile haute (au-dessus du fuselage) */}
			<path d={ATR_WINGS} fill="#E3E8ED" stroke="#5E6973" strokeWidth={0.07} strokeLinejoin="round" />
			<rect x={-1.15} y={-1.2} width={2.6} height={2.4} fill="#E3E8ED" />
			<path d={ATR_FLAPS} stroke="#9AA5AF" strokeWidth={0.06} />
			<path d={ATR_AILERONS} stroke="#9AA5AF" strokeWidth={0.06} />
			<path d="M.95 12.2L-.45 12.28L-.4 11.5L.98 11.5Z" fill={C.win} />
			<path d="M.95-12.2L-.45-12.28L-.4-11.5L.98-11.5Z" fill={C.win} />
			<AtrEngine side={1} propPhase={propPhase} />
			<AtrEngine side={-1} propPhase={propPhase + 0.4} />
			{/* Empennage en T */}
			<path d="M-6.6 0L-11.15-.18L-11.3 0L-11.15.18Z" fill="#0B0F14" />
			<path d={ATR_STAB} fill="#E3E8ED" stroke="#5E6973" strokeWidth={0.07} strokeLinejoin="round" />
			<path d="M-9.6-.12L-11.05-.14L-11.05.14L-9.6.12Z" fill={C.win} />
			{/* Pare-brise */}
			<path d="M10.05-.92Q11.05 0 10.05.92L9.45.74Q10.15 0 9.45-.74Z" fill="#1A2633" />
			<text x={5.6} y={0.24} fontFamily={FONT_TITLE} fontWeight={800} fontSize={0.6} fill="#0B0F14" textAnchor="middle" letterSpacing={0.04}>
				ASVEL
			</text>
		</g>
	);
};

// ── Autocar de tourisme, vue de profil ──────────────────────────────────────
// Unités : pixels pour une longueur de 160, avant vers +x, origine au centre.
const Wheel: React.FC<{cx: number; rot: number}> = ({cx, rot}) => (
	<g transform={`translate(${cx} 43)`}>
		<circle r={9.5} fill="#0A0D11" />
		<circle r={8.4} fill="#1C2228" />
		<circle r={5.2} fill="#AEB8C2" />
		<g transform={`rotate(${rot})`} stroke="#5A646E" strokeWidth={1.3}>
			<line x1={-4.6} y1={0} x2={4.6} y2={0} />
			<line x1={0} y1={-4.6} x2={0} y2={4.6} />
			<line x1={-3.3} y1={-3.3} x2={3.3} y2={3.3} />
			<line x1={-3.3} y1={3.3} x2={3.3} y2={-3.3} />
		</g>
		<circle r={1.6} fill="#2A3138" />
	</g>
);

export const Coach: React.FC<{wheelRot: number; braking: boolean}> = ({wheelRot, braking}) => (
	<g transform="translate(-80 -27)">
		{/* Ombre portée au sol */}
		<ellipse cx={82} cy={52.5} rx={80} ry={3.5} fill="#000" opacity={0.45} />
		{/* Passages de roues */}
		<path d="M15 43A24 13 0 0 1 62 43Z" fill="#05070A" />
		<path d="M116 43A12 12 0 0 1 140 43Z" fill="#05070A" />
		{/* Carrosserie */}
		<path
			d="M3 40V9Q3 3 9 3H143Q151 3 154 9L158.5 21Q160 25 160 30V40Q160 43 157 43H140A12 12 0 0 0 116 43H62A24 13 0 0 0 15 43H6Q3 43 3 40Z"
			fill="#F4F7FA"
			stroke="#1B232C"
			strokeWidth={1.2}
			strokeLinejoin="round"
		/>
		{/* Bandeau vitré */}
		<path d="M8 8H140V25H8Z" fill="#16222E" />
		{[22, 36, 50, 64, 78, 92, 106, 120].map((x) => (
			<rect key={x} x={x} y={8} width={1.8} height={17} fill="#F4F7FA" />
		))}
		<path d="M10 10H40" stroke="#5B7389" strokeWidth={1.2} opacity={0.7} />
		{/* Pare-brise */}
		<path d="M143 6Q150 6 152.5 11L157.5 24H144Z" fill="#1E2E3D" />
		<path d="M147 8L153 22" stroke="#6E8AA3" strokeWidth={1} opacity={0.6} />
		{/* Porte avant */}
		<rect x={128} y={9} width={12} height={33} rx={1.5} fill="none" stroke="#1B232C" strokeWidth={0.9} />
		{/* Livrée ASVEL : bande verte et soubassement noir */}
		<path d="M3 28H160V34H3Z" fill={C.win} />
		<path d="M3 34H160V40Q160 43 157 43H140A12 12 0 0 0 116 43H62A24 13 0 0 0 15 43H6Q3 43 3 40Z" fill="#0B0F14" />
		<text x={86} y={33.4} fontFamily={FONT_TITLE} fontWeight={800} fontSize={6.2} fill="#04140A" textAnchor="middle" letterSpacing={0.6}>
			ASVEL · LYON-VILLEURBANNE
		</text>
		{/* Phares et feux */}
		<rect x={155.5} y={35} width={4} height={3.2} rx={1} fill="#FFF6C8" />
		<path d="M159.5 35.5L176 32.5V41L159.5 38Z" fill="#FFF6C8" opacity={0.18} />
		<rect x={3} y={30} width={2.6} height={7} rx={0.8} fill={braking ? '#FF3B4A' : '#9E1C27'} />
		{braking ? <circle cx={2} cy={33.5} r={5} fill="#FF3B4A" opacity={0.25} /> : null}
		{/* Rétroviseur */}
		<path d="M156 10Q163 8 163 13V20" fill="none" stroke="#1B232C" strokeWidth={1.4} />
		<rect x={161.2} y={18} width={3} height={6} rx={1} fill="#1B232C" />
		{/* Climatisation de toit */}
		<rect x={52} y={0.6} width={40} height={3} rx={1.5} fill="#C9D2DB" stroke="#1B232C" strokeWidth={0.6} />
		<Wheel cx={28} rot={wheelRot} />
		<Wheel cx={49} rot={wheelRot + 20} />
		<Wheel cx={128} rot={wheelRot + 40} />
	</g>
);
