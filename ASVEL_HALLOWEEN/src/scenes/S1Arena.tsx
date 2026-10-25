import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, Easing} from 'remotion';
import {ShaderCanvas} from '../effects/ShaderCanvas';
import {skyPx} from '../effects/cpuShaders';
import {Smoke} from '../effects/Smoke';
import {Particles} from '../effects/Particles';
import {Bats} from '../effects/Bats';
import {Lightning, Flash, flashLevel} from '../effects/Lightning';
import {Black, Cobweb} from '../effects/Overlays';
import {Moon} from '../effects/Moon';
import {noise1, sumShake} from '../effects/random';
import {HorrorText} from '../components/TextFX';
import {C, FONT} from '../components/Fonts';
import tl from '../timeline.json';

const cue = tl.cues;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Coordonnées monde : la photo (1720x1290 après upscale x2) posée sous un ciel procédural.
const IMG_X = -320, IMG_Y = 690, IMG_W = 1720, IMG_H = 1290;

/** Ombre humanoïde floue qui glisse sur la façade. */
const Shadow: React.FC<{x: number; y: number; s: number; o: number}> = ({x, y, s, o}) => (
  <svg width={260 * s} height={620 * s} viewBox="0 0 260 620" style={{position: 'absolute', left: x, top: y, opacity: o, filter: 'blur(14px)', mixBlendMode: 'multiply'}}>
    <ellipse cx="130" cy="70" rx="48" ry="60" fill="#000" />
    <path d="M60 140 Q130 110 200 140 L235 380 L205 390 L190 260 L185 610 L140 610 L130 400 L120 610 L75 610 L70 260 L55 390 L25 380 Z" fill="#000" />
  </svg>
);

export const S1Arena: React.FC = () => {
  const f = useCurrentFrame();
  // Caméra virtuelle : poussée lente vers l'entrée principale
  const p = interpolate(f, [0, 600], [0, 1], {...clamp, easing: Easing.inOut(Easing.sin)});
  const z = 0.92 + 0.46 * p;
  const fx = 540 + (780 - 540) * p;
  const fy = Math.min(1980 - 960 / z, 780 + (1350 - 780) * p);
  const sh = sumShake(f, [cue.lightning[1], cue.lightning[3]], 30, 16);
  const flash = flashLevel(f, cue.lightning.slice(0, 4));
  const red = interpolate(f, [60, 330], [0, 1], {...clamp, easing: Easing.inOut(Easing.quad)});
  const moonAmt = interpolate(f, [150, 330], [0, 1], clamp);
  const fadeIn = interpolate(f, [0, 70], [1, 0], clamp);
  // lumières de l'arène qui clignotent (néon défaillant)
  const blink = f < 200 ? 0.2 : 0.55 + 0.45 * Math.sign(noise1(f / 5, 2) + 0.35) * (noise1(f / 2, 9) > -0.6 ? 1 : 0.1);
  const world = `translate(${540 + sh.x}px, ${960 + sh.y}px) rotate(${sh.r}rad) scale(${z}) translate(${-fx}px, ${-fy}px)`;
  const box: React.CSSProperties = {position: 'absolute', left: IMG_X, top: IMG_Y, width: IMG_W, height: IMG_H};

  return (
    <AbsoluteFill style={{background: C.black, overflow: 'hidden'}}>
      <ShaderCanvas scale={0.2} opaque make={(t) => skyPx({t, red, flash})} />
      <Moon x={(0.7 - 0.06 * p) * 1080} y={(1 - (0.45 + 0.04 * p)) * 1920} r={0.115 * 1920} amt={moonAmt} />
      <Bats count={9} seed={3} start={200} band={[0.06, 0.4]} />
      {/* fumée noire au-dessus du toit, loin */}
      <Smoke seed={11} color={[0.015, 0.008, 0.01]} light={[0.35, 0.05, 0.03]} lightDir={[0.5, 0.5]} density={1.0} scale={1.3} flow={[0.06, 0.05]} band={[0.35, 0.7, 0.15, 0]} opacity={interpolate(f, [90, 300], [0, 0.85], clamp)} />
      <AbsoluteFill style={{transform: world, transformOrigin: '0 0'}}>
        <Img src={staticFile('arena_building.png')} style={{...box, filter: `brightness(${0.6 + flash * 0.9 - red * 0.08}) saturate(${0.85 - red * 0.25}) contrast(${1.1 + red * 0.2})`}} />
        {/* teinte rouge sang appliquée uniquement au bâtiment (calque alpha précalculé) */}
        <Img src={staticFile('arena_tint.png')} style={{...box, mixBlendMode: 'multiply', opacity: red}} />
        {/* fenêtres / verrière / enseigne : lueur rouge qui clignote */}
        <Img src={staticFile('arena_lights_red.png')} style={{...box, mixBlendMode: 'screen', opacity: red * blink}} />
        <Img src={staticFile('arena_lights_red.png')} style={{...box, mixBlendMode: 'screen', opacity: red * blink * 0.7, filter: 'blur(12px)'}} />
        {/* reflets rouges sur le parvis */}
        <Img src={staticFile('arena_ground_red.png')} style={{...box, mixBlendMode: 'screen', opacity: red * (0.6 + 0.4 * blink)}} />
        <Shadow x={IMG_X + 300 + f * 1.1} y={IMG_Y + 520} s={1.1} o={interpolate(f, [240, 300, 520, 580], [0, 0.4, 0.4, 0], clamp)} />
        <Shadow x={IMG_X + 1500 - (f - 300) * 1.6} y={IMG_Y + 600} s={0.9} o={interpolate(f, [330, 380, 560, 600], [0, 0.35, 0.35, 0], clamp)} />
      </AbsoluteFill>
      {/* nuages de fumée orange autour de l'arène */}
      <Smoke seed={4} color={[0.08, 0.02, 0.01]} light={[0.9, 0.32, 0.08]} lightDir={[0, -1]} density={0.8} scale={1.9} flow={[-0.05, 0.03]} band={[0.25, 0.48, 0.12, 0]} opacity={interpolate(f, [120, 300], [0, 0.55], clamp)} blend="screen" />
      {/* brouillard rampant sur le parvis (2 couches de profondeur) */}
      <Smoke seed={7} color={[0.32, 0.3, 0.31]} light={[0.75, 0.55, 0.5]} lightDir={[0, 1]} density={1.0} scale={1.4} flow={[0.18, 0.01]} band={[0.04, 0.32, 0.1, 1]} opacity={interpolate(f, [20, 200], [0.3, 0.75], clamp)} />
      <Smoke seed={17} color={[0.2, 0.12, 0.13]} light={[0.8, 0.25, 0.18]} lightDir={[0, 1]} density={1.1} scale={2.6} flow={[0.32, 0.02]} turb={1.2} band={[0, 0.2, 0.08, 1]} opacity={interpolate(f, [100, 300], [0.2, 0.8], clamp)} />
      <Particles kind="embers" count={70} seed={2} area={[0, 0.55, 1, 0.45]} opacity={interpolate(f, [150, 300], [0, 1], clamp)} />
      <Particles kind="rain" count={160} seed={5} opacity={interpolate(f, [350, 450], [0, 0.8], clamp)} speed={1.3} />
      <Lightning strikes={cue.lightning.slice(0, 4)} from={[0.55, -0.02]} to={[0.4, 0.38]} seed={2} />
      {/* volutes qui passent devant la caméra */}
      <Smoke seed={23} color={[0.01, 0.005, 0.008]} light={[0.3, 0.04, 0.03]} density={1.15} scale={0.9} flow={[0.35, 0.05]} turb={1.1} band={[0, 1, 0.1, 3]} opacity={interpolate(f, [0, 40, 110, 160, 450, 520, 560, 600], [1, 0.9, 0.35, 0, 0, 0.45, 0.3, 0.6], clamp)} style={{filter: 'blur(6px)'}} />
      <Cobweb corner="tl" size={360} opacity={0.25 * red} seed={1} />
      <HorrorText text="CETTE NUIT..." at={cue.arenaText1} out={cue.arenaText2 - 30} y={360} size={120} font={FONT.horror} stagger={4} tracking={6} />
      <HorrorText text="L'ARÈNE" at={cue.arenaText2} out={585} y={260} size={170} stagger={3} />
      <HorrorText text="VA TREMBLER" at={cue.arenaText2 + 24} out={585} y={450} size={150} stagger={3} scratches />
      <Flash strikes={cue.lightning.slice(0, 4)} max={0.55} />
      <Flash strikes={[cue.bigImpact[0]]} max={1} />
      <Black v={fadeIn} />
    </AbsoluteFill>
  );
};
