import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, Easing} from 'remotion';
import {Smoke, Fire} from '../effects/Smoke';
import {Particles} from '../effects/Particles';
import {Lightning, Flash} from '../effects/Lightning';
import {Black} from '../effects/Overlays';
import {sumShake, noise1} from '../effects/random';
import {PlayerRig, PATTY} from '../components/PlayerRig';
import {FireBall} from '../components/FireBall';
import {HorrorText, MetalText} from '../components/TextFX';
import {C, FONT} from '../components/Fonts';
import tl from '../timeline.json';

const S0 = tl.scenes.patty[0];
const L = (g: number) => g - S0;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** SCÈNE 3 : Patty Mills, l'ombre de l'ASVEL. */
export const S3Patty: React.FC = () => {
  const f = useCurrentFrame();
  const nameAt = L(tl.cues.pattyName);
  const strikes = [L(1610), L(1700), L(1840)];
  // caméra 2.5D : poussée lente + dérive ; les couches bougent à des vitesses différentes
  const cam = interpolate(f, [0, 600], [0, 1], {...clamp, easing: Easing.inOut(Easing.sin)});
  const z = 1 + 0.16 * cam;
  const sh = sumShake(f, [nameAt, ...strikes.slice(0, 1)], 26, 20);
  const driftX = noise1(f / 90, 2) * 12;
  const reveal = interpolate(f, [40, 170], [0, 1], {...clamp, easing: Easing.in(Easing.quad)});
  const eyes = interpolate(f, [110, 170], [0, 1], clamp);
  const cracks = interpolate(f, [150, 240], [0, 0.85], clamp);
  const hole = interpolate(f, [30, 190], [0, 1.05], {...clamp, easing: Easing.out(Easing.cubic)});
  const ballIn = interpolate(f, [130, 200], [0, 1], {...clamp, easing: Easing.out(Easing.back(1.4))});
  const layer = (depth: number): React.CSSProperties => ({
    transform: `translate(${sh.x * depth + driftX * depth}px, ${sh.y * depth}px) scale(${1 + (z - 1) * depth}) rotate(${sh.r * depth}rad)`,
    transformOrigin: '50% 45%',
  });
  const nameT = f - nameAt;
  const slam = interpolate(nameT, [0, 10], [1.7, 1], {...clamp, easing: Easing.out(Easing.cubic)});

  return (
    <AbsoluteFill style={{background: C.black, overflow: 'hidden'}}>
      {/* arrière-plan lointain : fumée noire + rouge éclairée par les flammes */}
      <AbsoluteFill style={layer(0.35)}>
        <AbsoluteFill style={{background: 'radial-gradient(ellipse 70% 50% at 50% 45%, #3a0508 0%, #120204 55%, #080608 100%)'}} />
        <Smoke seed={51} color={[0.02, 0.008, 0.01]} light={[0.6, 0.06, 0.04]} lightDir={[0, -1]} density={1.05} scale={1.3} flow={[0.02, 0.09]} opacity={0.95} />
        <Smoke seed={53} color={[0.12, 0.01, 0.015]} light={[0.95, 0.2, 0.08]} lightDir={[0, -1]} density={0.9} scale={2} flow={[-0.04, 0.12]} band={[0.0, 0.55, 0.1, 1]} opacity={0.7} blend="screen" />
        <Lightning strikes={strikes} from={[0.5, -0.02]} to={[0.3, 0.32]} seed={12} />
        <Lightning strikes={strikes.map((s) => s + 3)} from={[0.55, -0.02]} to={[0.75, 0.3]} seed={14} width={4} />
      </AbsoluteFill>
      {/* flammes sur les côtés */}
      <AbsoluteFill style={layer(0.6)}>
        <Fire dir={[1, 0]} height={0.14} intensity={0.85} seed={3} scale={5} opacity={interpolate(f, [60, 140], [0, 0.85], clamp)} />
        <Fire dir={[-1, 0]} height={0.14} intensity={0.85} seed={7} scale={5} opacity={interpolate(f, [60, 140], [0, 0.85], clamp)} />
        <Fire dir={[0, 1]} height={0.12} intensity={0.8} seed={4} scale={6} opacity={interpolate(f, [80, 160], [0, 0.7], clamp)} />
      </AbsoluteFill>
      {/* joueur */}
      <AbsoluteFill style={layer(1)}>
        <PlayerRig def={PATTY} x={-95} y={140} scale={1.55} reveal={reveal} eyes={eyes} cracks={cracks} rim={reveal * 0.95} aura="rgba(215,25,32,.75)" shadow={0.55} seed={3} />
        <Particles kind="embers" count={90} seed={21} area={[0.1, 0.45, 0.8, 0.55]} speed={1.3} opacity={interpolate(f, [80, 160], [0, 1], clamp)} />
      </AbsoluteFill>
      {/* premier plan : brouillard devant les jambes, ballon, étincelles */}
      <AbsoluteFill style={layer(1.3)}>
        <Smoke seed={57} color={[0.05, 0.02, 0.025]} light={[0.75, 0.15, 0.1]} lightDir={[0, 1]} density={1.15} scale={1.8} flow={[0.22, 0.02]} band={[0.0, 0.3, 0.1, 1]} opacity={0.95} />
        {ballIn > 0 ? (
          <div style={{transform: `translateY(${(1 - ballIn) * 700}px)`, opacity: Math.min(1, ballIn * 1.5)}}>
            <FireBall cx={835} cy={1270 + Math.sin(f / 22) * 14} size={250} />
          </div>
        ) : null}
        <Particles kind="sparks" count={60} seed={22} area={[0.0, 0.9, 1, 0.1]} speed={0.7} opacity={0.8} />
        <Particles kind="sparks" count={140} seed={23} burstAt={nameAt} burstCenter={[0.5, 0.78]} />
      </AbsoluteFill>
      {/* fumée noire de révélation (s'ouvre au centre) */}
      <Smoke seed={59} color={[0.008, 0.004, 0.006]} light={[0.3, 0.03, 0.03]} density={1.5} scale={1.2} flow={[0.02, 0.2]} turb={1.3} hole={[0.5, 0.58, hole]} opacity={interpolate(f, [0, 10, 200, 260], [1, 1, 1, 0], clamp)} />
      {/* texte */}
      <AbsoluteFill style={{transform: `translate(${sh.x * 0.5}px, ${sh.y * 0.5}px)`}}>
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 620, background: 'linear-gradient(0deg, rgba(8,6,8,.92) 20%, rgba(8,6,8,.6) 60%, transparent)', opacity: interpolate(nameT, [-20, 10], [0, 1], clamp)}} />
        {nameT >= 0 ? (
          <div style={{position: 'absolute', left: 0, right: 0, top: 1415, display: 'flex', justifyContent: 'center', transform: `scale(${slam})`, opacity: interpolate(nameT, [0, 4], [0, 1], clamp)}}>
            <MetalText text="PATTY MILLS" size={150} depth={16} sweep={interpolate(nameT, [10, 70], [0, 1.3], clamp)} />
          </div>
        ) : null}
        {nameT > 22 ? (
          <div style={{position: 'absolute', left: 0, right: 0, top: 1600, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 22, opacity: interpolate(nameT, [22, 36], [0, 1], clamp), transform: `translateY(${interpolate(nameT, [22, 40], [30, 0], clamp)}px)`}}>
            <Img src={staticFile('logo_asvel.png')} style={{height: 92, filter: 'drop-shadow(0 0 12px rgba(215,25,32,.9))'}} />
          </div>
        ) : null}
        <HorrorText text="13,3 PIR" at={nameAt + 45} y={1715} size={96} color={C.gold} glow="#a8641e" stagger={2} />
        <HorrorText text="STATISTIQUE D'AVANT-MATCH" at={nameAt + 60} y={1818} size={30} font={FONT.body} color="#cfc6bd" glow="rgba(0,0,0,0)" stagger={1} tracking={6} />
      </AbsoluteFill>
      <Flash strikes={strikes} max={0.25} color="#ffd0d0" />
      <Flash strikes={[nameAt]} max={0.55} color="#ff3a20" />
      <Black v={interpolate(f, [0, 8], [1, 0], clamp)} />
    </AbsoluteFill>
  );
};
