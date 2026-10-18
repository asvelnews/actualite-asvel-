import React, {useEffect, useState} from 'react';
import {AbsoluteFill, continueRender, delayRender, interpolate, useCurrentFrame} from 'remotion';
import {MapLayer} from './components/MapLayer';
import {Markers} from './components/Markers';
import {Banner, BottomPanel, Disclaimer, Final, Header, Intro, Strip} from './components/Overlay';
import {DURATION} from './lib/timeline';
import {C} from './theme';

export const AsvelTour: React.FC = () => {
	const frame = useCurrentFrame();
	const [handle] = useState(() => delayRender('Chargement des polices'));
	useEffect(() => {
		document.fonts.ready.then(() => continueRender(handle));
	}, [handle]);
	const fadeOut = interpolate(frame, [DURATION - 20, DURATION - 1], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<AbsoluteFill style={{backgroundColor: C.bg, opacity: fadeOut}}>
			<MapLayer />
			<Markers />
			{/* Voiles de lisibilité derrière l'en-tête et le panneau inférieur */}
			<AbsoluteFill
				style={{
					background: `linear-gradient(180deg, ${C.bg} 0%, rgba(7,11,16,0.92) 14%, rgba(7,11,16,0) 19%, rgba(7,11,16,0) 64%, rgba(7,11,16,0.85) 70%, ${C.bg} 100%)`,
				}}
			/>
			<Header />
			<Strip />
			<Banner />
			<BottomPanel />
			<Final />
			<Disclaimer />
			<Intro />
		</AbsoluteFill>
	);
};
