import React from 'react';
import {Composition} from 'remotion';
import {AsvelTour} from './AsvelTour';
import {DURATION, FPS, HEIGHT, WIDTH} from './lib/timeline';

export const RemotionRoot: React.FC = () => (
	<Composition id="AsvelTour" component={AsvelTour} durationInFrames={DURATION} fps={FPS} width={WIDTH} height={HEIGHT} />
);
