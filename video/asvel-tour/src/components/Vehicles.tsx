// Véhicules vectoriels dessinés à la main (aucune image, aucun emoji).
import React from 'react';
import {C, FONT_TITLE} from '../theme';

// ── Embraer ERJ 145, vue de dessus ──────────────────────────────────────────
// Unités : mètres, nez vers +x, origine au centre de l'appareil.
// Cotes de référence (Embraer) : longueur 29,87 m, envergure 20,04 m,
// moteurs AE3007 en nacelles arrière, empennage en T.
const FUSELAGE =
	'M15 0C15-.62 14.3-1.14 12.7-1.14L-8.6-1.14C-11.2-1-13.6-.5-15-.16L-15 .16C-13.6.5-11.2 1-8.6 1.14L12.7 1.14C14.3 1.14 15 .62 15 0Z';
const WINGS = 'M2.4 1.05L-1.4 9.85L-2.55 10.02L-2.45 1.05ZM2.4-1.05L-1.4-9.85L-2.55-10.02L-2.45-1.05Z';
const STAB = 'M-11.7 0L-13.85 3.72L-14.85 3.78L-14.5 0L-14.85-3.78L-13.85-3.72Z';
const FLAPS = 'M-2.45 1.6L-2.5 6.2M-2.45-1.6L-2.5-6.2';
const AILERONS = 'M-2.5 6.6L-2.55 9.6M-2.5-6.6L-2.55-9.6';

const Nacelle: React.FC<{side: 1 | -1}> = ({side}) => (
	<g>
		<rect x={-9.1} y={side > 0 ? 0.95 : -1.45} width={1.9} height={0.5} fill="#B9C3CC" />
		<rect x={-10.4} y={side * 2.05 - 0.74} width={4.4} height={1.48} rx={0.72} fill="#D5DCE3" stroke="#59646F" strokeWidth={0.08} />
		<ellipse cx={-6.05} cy={side * 2.05} rx={0.22} ry={0.6} fill="#20262D" />
		<rect x={-10.55} y={side * 2.05 - 0.45} width={0.35} height={0.9} rx={0.15} fill="#3B444E" />
	</g>
);

export const Erj145: React.FC<{lengthPx: number; gear: number; shadow?: boolean}> = ({lengthPx, gear, shadow}) => {
	const s = lengthPx / 30;
	if (shadow) {
		return (
			<g transform={`scale(${s})`} fill="#000">
				<path d={FUSELAGE} />
				<path d={WINGS} />
				<path d={STAB} />
				<rect x={-10.4} y={1.31} width={4.4} height={1.48} rx={0.72} />
				<rect x={-10.4} y={-2.79} width={4.4} height={1.48} rx={0.72} />
			</g>
		);
	}
	return (
		<g transform={`scale(${s})`}>
			{/* Train d'atterrissage (visible quand il est sorti) */}
			<g opacity={gear} fill="#151A20">
				<rect x={-3.55} y={2.1} width={1.2} height={0.75} rx={0.2} />
				<rect x={-3.55} y={-2.85} width={1.2} height={0.75} rx={0.2} />
				<rect x={10.9} y={-0.32} width={0.9} height={0.64} rx={0.2} />
			</g>
			<path d={WINGS} fill="#E3E8ED" stroke="#5E6973" strokeWidth={0.08} strokeLinejoin="round" />
			<path d={FLAPS} stroke="#9AA5AF" strokeWidth={0.07} />
			<path d={AILERONS} stroke="#9AA5AF" strokeWidth={0.07} />
			{/* Saumons d'aile aux couleurs du club */}
			<path d="M-1.4 9.85L-2.55 10.02L-2.53 9.3L-1.17 9.3Z" fill={C.win} />
			<path d="M-1.4-9.85L-2.55-10.02L-2.53-9.3L-1.17-9.3Z" fill={C.win} />
			<path d={FUSELAGE} fill="#F7F9FB" stroke="#5E6973" strokeWidth={0.09} />
			{/* Bande dorsale verte et noire */}
			<path d="M10.5-.32L-12.5-.22L-12.5.22L10.5.32Z" fill={C.win} />
			<path d="M10.5-.1L-12.5-.06L-12.5.06L10.5.1Z" fill="#0B0F14" />
			<Nacelle side={1} />
			<Nacelle side={-1} />
			<path d={STAB} fill="#E3E8ED" stroke="#5E6973" strokeWidth={0.08} strokeLinejoin="round" />
			{/* Dérive vue de dessus */}
			<path d="M-9.4 0L-14.75-.2L-14.95 0L-14.75.2Z" fill="#0B0F14" />
			<path d="M-11.2-.12L-14.6-.17L-14.6.17L-11.2.12Z" fill={C.win} />
			{/* Pare-brise */}
			<path d="M13.75-.78Q14.75 0 13.75.78L13.15.62Q13.85 0 13.15-.62Z" fill="#1A2633" />
			<text x={4.5} y={0.25} fontFamily={FONT_TITLE} fontWeight={800} fontSize={0.62} fill="#0B0F14" textAnchor="middle" letterSpacing={0.05}>
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
