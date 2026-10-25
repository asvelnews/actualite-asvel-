import React from 'react';
import {AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame, Easing} from 'remotion';
import {S1Arena} from '../scenes/S1Arena';
import {S2Horror} from '../scenes/S2Horror';
import {S3Patty} from '../scenes/S3Patty';
import {S4Tadas} from '../scenes/S4Tadas';
import {S5FaceOff} from '../scenes/S5FaceOff';
import {S6GameDay} from '../scenes/S6GameDay';
import {Claws} from '../effects/Claws';
import {Fire} from '../effects/Smoke';
import {Particles} from '../effects/Particles';
import {Grain, Vignette} from '../effects/Overlays';
import tl from '../timeline.json';

const sc = tl.scenes;
const cue = tl.cues;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const seq = (k: keyof typeof sc) => ({from: sc[k][0], durationInFrames: sc[k][1] - sc[k][0]});

/** Transitions qui chevauchent les coupes (frames globales). */
const Transitions: React.FC = () => {
  const f = useCurrentFrame();
  // mur de flammes qui passe devant la caméra (S4 -> S5)
  const fs = cue.fireSweep;
  const fireH = interpolate(f, [fs, fs + 24, fs + 36, fs + 62], [0, 1.25, 1.25, 0], {...clamp, easing: Easing.inOut(Easing.quad)});
  // explosion lumineuse (S5 -> S6)
  const ex = cue.explosion;
  const exp = interpolate(f, [ex, ex + 14, ex + 16, ex + 40], [0, 1, 1, 0], clamp);
  return (
    <AbsoluteFill>
      <Claws at={cue.tadasClaws - 10} angle={-35} hold={10} scale={1.15} />
      {fireH > 0.01 ? (
        <>
          <Fire dir={[0, 1]} height={fireH} intensity={1.25} seed={31} scale={4} res={0.25} />
          <AbsoluteFill style={{background: '#ff3a10', opacity: Math.max(0, fireH - 0.75) * 1.6, mixBlendMode: 'screen'}} />
        </>
      ) : null}
      {exp > 0 ? (
        <AbsoluteFill style={{background: `radial-gradient(circle at 50% 60%, rgba(255,250,235,${exp}) 0%, rgba(255,140,40,${exp}) ${30 + 40 * exp}%, rgba(215,25,32,${exp * 0.8}) 100%)`}} />
      ) : null}
      <Particles kind="sparks" count={220} seed={91} burstAt={ex + 10} burstCenter={[0.5, 0.6]} />
    </AbsoluteFill>
  );
};

export const Trailer: React.FC<{music?: boolean}> = ({music = true}) => (
  <AbsoluteFill style={{background: '#080608'}}>
    <Sequence {...seq('arena')}>
      <S1Arena />
    </Sequence>
    <Sequence {...seq('horror')}>
      <S2Horror />
    </Sequence>
    <Sequence {...seq('patty')}>
      <S3Patty />
    </Sequence>
    <Sequence {...seq('tadas')}>
      <S4Tadas />
    </Sequence>
    <Sequence {...seq('faceoff')}>
      <S5FaceOff />
    </Sequence>
    <Sequence {...seq('gameday')}>
      <S6GameDay />
    </Sequence>
    <Transitions />
    <Vignette strength={0.7} />
    <Grain opacity={0.09} />
    {music ? <Audio src={staticFile('audio/ASVEL_HALLOWEEN_MIX.wav')} /> : <Audio src={staticFile('audio/ASVEL_HALLOWEEN_SFX_ONLY.wav')} />}
  </AbsoluteFill>
);
