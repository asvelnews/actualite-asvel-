import React from 'react';
import {AbsoluteFill, Img, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, Easing} from 'remotion';
import {ShaderCanvas} from '../effects/ShaderCanvas';
import {skyPx} from '../effects/cpuShaders';
import {Smoke} from '../effects/Smoke';
import {Particles} from '../effects/Particles';
import {Lightning, Flash, flashLevel} from '../effects/Lightning';
import {Claws} from '../effects/Claws';
import {Moon} from '../effects/Moon';
import {Black} from '../effects/Overlays';
import {noise1, sumShake} from '../effects/random';
import {HorrorText} from '../components/TextFX';
import {C, FONT} from '../components/Fonts';
import tl from '../timeline.json';

const I = tl.cues.intro;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/**
 * Plan généré par IA (Magic Hour, image-to-video) : vraie vidéo, agrandie de 480x854
 * vers 1080x1920 par FFmpeg (Lanczos), lue à sa cadence native (24 i/s) dans le 60 FPS.
 */
const Clip: React.FC<{src: string; rate?: number; push?: [number, number]; dur: number}> = ({src, rate = 1, push = [1, 1.06], dur}) => {
  const f = useCurrentFrame();
  const z = interpolate(f, [0, dur], push, clamp);
  return (
    <AbsoluteFill style={{transform: `scale(${z})`}}>
      <OffthreadVideo src={staticFile(src)} playbackRate={rate} muted style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'contrast(1.08) saturate(1.05)'}} />
    </AbsoluteFill>
  );
};

/** SCÈNE 4 de l'intro : l'arrivée devant la vraie LDLC Arena. */
const Arrival: React.FC = () => {
  const f = useCurrentFrame(); // local, 0 = arrivée
  const D = I.out - I.arrival + 24;
  const p = interpolate(f, [0, D], [0, 1], {...clamp, easing: Easing.inOut(Easing.sin)});
  // grue : la caméra part du parvis (ombres des personnages) et s'élève vers l'arène
  const z = 1.25 - 0.3 * p;
  const fx = 700 - 120 * p;
  const fy = 2060 - 880 * p;
  const big = I.bigLightning - I.arrival;
  const sh = sumShake(f, [big], 40, 26);
  const flash = flashLevel(f, [big, big + 40]);
  const world = `translate(${540 + sh.x}px, ${960 + sh.y}px) scale(${z}) translate(${-fx}px, ${-fy}px)`;
  const box: React.CSSProperties = {position: 'absolute', left: -320, top: 690, width: 1720, height: 1290};
  const blink = 0.6 + 0.4 * (noise1(f / 4, 3) > -0.3 ? 1 : 0.2);
  // ombres des 4 personnages arrêtés face au bâtiment (éclairés depuis la caméra)
  const shadows: [string, number, number][] = [['freddy', 420, 0.95], ['michael', 600, 1.05], ['ghostface', 800, 1.08], ['art', 990, 0.75]];
  return (
    <AbsoluteFill style={{background: C.black, overflow: 'hidden'}}>
      <ShaderCanvas scale={0.2} opaque make={(t) => skyPx({t: t + 10, red: 1, flash})} />
      <Moon x={760} y={500 - 260 * p} r={190} amt={1} />
      <Smoke seed={101} color={[0.015, 0.008, 0.01]} light={[0.4, 0.05, 0.03]} density={1} scale={1.3} flow={[0.06, 0.05]} band={[0.45, 0.85, 0.15, 0]} opacity={0.75} />
      <Lightning strikes={[big, big + 40]} from={[0.5, -0.02]} to={[0.42, 0.42]} seed={33} width={9} color="#ffe2e2" />
      <AbsoluteFill style={{transform: world, transformOrigin: '0 0'}}>
        <Img src={staticFile('arena_building.png')} style={{...box, filter: `brightness(${0.55 + flash * 1.1}) saturate(.7) contrast(1.25)`}} />
        <Img src={staticFile('arena_tint.png')} style={{...box, mixBlendMode: 'multiply'}} />
        <Img src={staticFile('arena_lights_red.png')} style={{...box, mixBlendMode: 'screen', opacity: blink}} />
        <Img src={staticFile('arena_lights_red.png')} style={{...box, mixBlendMode: 'screen', opacity: blink * 0.7, filter: 'blur(12px)'}} />
        <Img src={staticFile('arena_ground_red.png')} style={{...box, mixBlendMode: 'screen', opacity: 0.8}} />
        {/* prolongement du parvis sous la photo (asphalte mouillé) */}
        <div style={{position: 'absolute', left: -320, top: 1950, width: 1720, height: 1100, background: 'linear-gradient(180deg, rgba(92,34,28,1) 0%, #2a1010 25%, #0b0607 100%)'}} />
        <div style={{position: 'absolute', left: -320, top: 1840, width: 1720, height: 140, background: 'linear-gradient(180deg, transparent, rgba(92,34,28,1))'}} />
        <div style={{position: 'absolute', left: 200, top: 1960, width: 900, height: 500, background: 'radial-gradient(ellipse 50% 40% at 50% 10%, rgba(255,60,30,.35), transparent 70%)', mixBlendMode: 'screen'}} />
        {/* ombres couchées sur le parvis, projetées vers l'arène (lumière derrière la caméra) */}
        {shadows.map(([n, x, s]) => (
          <div key={n} style={{position: 'absolute', left: x - 70, top: 2300 - 620 * s, transform: `skewX(${(x - 700) * 0.08}deg) scaleY(0.55)`, transformOrigin: '50% 100%', opacity: 0.72, filter: 'blur(4px)'}}>
            <Img src={staticFile(`intro/shadow_${n}.png`)} style={{height: 620 * s}} />
          </div>
        ))}
      </AbsoluteFill>
      <Smoke seed={103} color={[0.3, 0.27, 0.28]} light={[0.75, 0.55, 0.5]} lightDir={[0, 1]} density={1} scale={1.5} flow={[0.18, 0.01]} band={[0.0, 0.3, 0.1, 1]} opacity={0.7} />
      <Particles kind="embers" count={70} seed={104} area={[0, 0.55, 1, 0.45]} />
      <Particles kind="leaves" count={26} seed={105} wind={0.6} speed={0.9} opacity={0.9} />
      <HorrorText text="LE CAUCHEMAR" at={I.title - I.arrival} y={300} size={150} stagger={3} />
      <HorrorText text="ARRIVE À L'ARENA" at={I.title - I.arrival + 26} y={470} size={118} stagger={2} color="#ff3b1f" glow="#ff641b" />
      <Flash strikes={[big, big + 40]} max={0.75} color="#fff2f2" />
      <Claws at={I.out - I.arrival} angle={-30} hold={6} scale={1.1} />
      <Smoke seed={107} color={[0.008, 0.004, 0.006]} light={[0.3, 0.03, 0.03]} density={1.5} scale={1.2} flow={[0.02, 0.25]} turb={1.3} opacity={interpolate(f, [I.out - I.arrival - 6, I.out - I.arrival + 20], [0, 1], clamp)} />
    </AbsoluteFill>
  );
};

/** NOUVELLE INTRO : cimetière -> sortie -> marche vers l'arène -> arrivée (0-22 s). */
export const S0Intro: React.FC = () => {
  const f = useCurrentFrame();
  const [a0, a1] = I.clipA, [b0, b1] = I.clipB, [c0, c1] = I.clipC;
  const redL = I.redLightning;
  return (
    <AbsoluteFill style={{background: C.black}}>
      <Sequence from={a0} durationInFrames={a1 - a0 + 6}>
        <Clip src="intro/clipA.mp4" dur={a1 - a0} push={[1.0, 1.1]} />
        <Smoke seed={111} color={[0.3, 0.29, 0.31]} light={[0.8, 0.6, 0.5]} lightDir={[0, 1]} density={1} scale={1.5} flow={[0.15, 0.01]} band={[0, 0.25, 0.1, 1]} opacity={0.6} />
      </Sequence>
      <Sequence from={b0} durationInFrames={b1 - b0 + 30}>
        <Clip src="intro/clipB.mp4" dur={b1 - b0} push={[1.04, 1.0]} />
        <Smoke seed={113} color={[0.28, 0.27, 0.29]} light={[0.8, 0.55, 0.45]} lightDir={[0, 1]} density={1} scale={1.6} flow={[0.2, 0.02]} band={[0, 0.2, 0.08, 1]} opacity={0.55} />
        <Particles kind="leaves" count={14} seed={114} wind={0.4} speed={0.8} opacity={0.8} />
      </Sequence>
      <Sequence from={c0} durationInFrames={c1 - c0}>
        <Clip src="intro/clipC.mp4" rate={I.clipCRate} dur={c1 - c0} push={[1.0, 1.07]} />
        <Smoke seed={115} color={[0.12, 0.05, 0.05]} light={[0.7, 0.2, 0.12]} lightDir={[0, 1]} density={1} scale={1.7} flow={[0.25, 0.02]} band={[0, 0.22, 0.08, 1]} opacity={0.6} />
        <Particles kind="leaves" count={24} seed={116} wind={0.7} speed={1} opacity={0.9} />
        <Lightning strikes={redL.map((s) => s - c0)} from={[0.35, -0.02]} to={[0.6, 0.3]} seed={44} color="#ff3a2a" />
        <Flash strikes={redL.map((s) => s - c0)} max={0.3} color="#ff2a1a" />
      </Sequence>
      <Sequence from={I.arrival} durationInFrames={1320 - I.arrival}>
        <Arrival />
      </Sequence>
      {/* transitions : éclair blanc (A->B), nuage de fumée (B->C), passage dans le noir (C->D) */}
      <Flash strikes={[b0 - 2]} max={0.9} />
      <Smoke seed={117} color={[0.01, 0.006, 0.008]} light={[0.3, 0.05, 0.04]} density={1.5} scale={1.1} flow={[0.3, 0.06]} turb={1.3} opacity={interpolate(f, [b1 - 24, b1, b1 + 6, b1 + 30], [0, 1, 1, 0], clamp)} />
      <Black v={interpolate(f, [0, 40], [1, 0], clamp) + interpolate(f, [c1 - 18, c1, c1 + 2, c1 + 26], [0, 1, 1, 0], clamp)} />
      <div style={{position: 'absolute', right: 40, top: 60, fontFamily: FONT.horror, fontSize: 44, color: C.blood, opacity: interpolate(f, [60, 90, 560, 600], [0, 0.85, 0.85, 0], clamp), textShadow: '0 0 12px #d71920'}}>ASVEL_NEWS</div>
    </AbsoluteFill>
  );
};
