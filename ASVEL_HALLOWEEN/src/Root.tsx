import React from 'react';
import {Composition} from 'remotion';
import './components/Fonts';
import {Trailer} from './compositions/Trailer';
import {VfxTest} from './compositions/VfxTest';
import {S1Arena} from './scenes/S1Arena';
import {S2Horror} from './scenes/S2Horror';
import {S3Patty} from './scenes/S3Patty';
import {S4Tadas} from './scenes/S4Tadas';
import {S5FaceOff} from './scenes/S5FaceOff';
import {S6GameDay} from './scenes/S6GameDay';
import tl from './timeline.json';

const V = {fps: tl.fps, width: 1080, height: 1920};
const len = (k: keyof typeof tl.scenes) => tl.scenes[k][1] - tl.scenes[k][0];

export const Root: React.FC = () => (
  <>
    {/* Trailer complet : 60 s, 1080x1920, 60 FPS natifs */}
    <Composition id="Trailer" component={Trailer} durationInFrames={tl.duration} {...V} defaultProps={{music: true}} />
    {/* Scènes isolées pour le travail et les vérifications */}
    <Composition id="S1Arena" component={S1Arena} durationInFrames={len('arena')} {...V} />
    <Composition id="S2Horror" component={S2Horror} durationInFrames={len('horror')} {...V} />
    <Composition id="S3Patty" component={S3Patty} durationInFrames={len('patty')} {...V} />
    <Composition id="S4Tadas" component={S4Tadas} durationInFrames={len('tadas')} {...V} />
    <Composition id="S5FaceOff" component={S5FaceOff} durationInFrames={len('faceoff')} {...V} />
    <Composition id="S6GameDay" component={S6GameDay} durationInFrames={len('gameday')} {...V} />
    <Composition id="VfxTest" component={VfxTest} durationInFrames={300} {...V} />
  </>
);
