import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, Easing} from 'remotion';
import {Smoke} from '../effects/Smoke';
import {Particles} from '../effects/Particles';
import {Lightning, Flash} from '../effects/Lightning';
import {Claws} from '../effects/Claws';
import {Black} from '../effects/Overlays';
import {hash, noise1, sumShake} from '../effects/random';
import {C} from '../components/Fonts';
import tl from '../timeline.json';

const H0 = tl.scenes.horror[0];
const cue = tl.cues.horror;
const L = (f: number) => f - H0; // cue absolue -> frame locale de la scène
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/**
 * Apparition d'un personnage issu de l'affiche : fenêtre à bords fondus (les extraits de
 * l'affiche ne sont pas détourés, on les fait naître des ténèbres), poussée de caméra
 * lente, lueur rouge intermittente, aberration chromatique sur les glitchs, ombre géante.
 */
const Apparition: React.FC<{
  src: string;
  start: number;
  end: number;
  w: number;
  h: number;
  light: number; // 0..1 éclairage courant (piloté par la scène)
  glitch?: number;
  y?: number;
  drift?: number;
}> = ({src, start, end, w, h, light, glitch = 0, y = 960, drift = 1}) => {
  const f = useCurrentFrame();
  if (f < start - 2 || f > end + 2) return null;
  const p = (f - start) / (end - start);
  const z = 1 + 0.12 * p;
  const dx = noise1(f / 40, start) * 14 * drift + (glitch > 0 ? (hash(f) - 0.5) * 40 * glitch : 0);
  const mask = 'radial-gradient(ellipse 50% 50% at 50% 46%, #000 52%, rgba(0,0,0,.55) 68%, transparent 82%)';
  const base: React.CSSProperties = {position: 'absolute', left: 540 - w / 2, top: y - h / 2, width: w, height: h, WebkitMaskImage: mask, maskImage: mask};
  return (
    <AbsoluteFill style={{transform: `translateX(${dx}px) scale(${z})`, transformOrigin: `50% ${(y / 1920) * 100}%`}}>
      {/* ombre géante projetée sur le "mur" de fumée */}
      <Img src={staticFile(src)} style={{...base, transform: 'scale(1.9) translate(4%, -6%)', filter: 'brightness(0) blur(22px)', opacity: 0.55 * light}} />
      <Img src={staticFile(src)} style={{...base, filter: `brightness(${0.15 + 1.05 * light}) contrast(1.15) saturate(1.1)`}} />
      {glitch > 0 ? (
        <>
          <Img src={staticFile(src)} style={{...base, left: base.left as number + 14 * glitch, mixBlendMode: 'screen', opacity: 0.5 * glitch, filter: 'sepia(1) hue-rotate(-50deg) saturate(6) brightness(.7)'}} />
          <Img src={staticFile(src)} style={{...base, left: base.left as number - 14 * glitch, mixBlendMode: 'screen', opacity: 0.35 * glitch, filter: 'sepia(1) hue-rotate(140deg) saturate(4) brightness(.5)'}} />
        </>
      ) : null}
      {/* lueur rouge qui lèche les bords */}
      <AbsoluteFill style={{background: `radial-gradient(ellipse 45% 30% at 50% ${(y / 1920) * 100}%, rgba(215,25,32,${0.25 * light}), transparent 70%)`, mixBlendMode: 'screen'}} />
    </AbsoluteFill>
  );
};

export const S2Horror: React.FC = () => {
  const f = useCurrentFrame();
  const g = f + H0; // frame globale (pour comparer aux cues)
  // --- MICHAEL MYERS : sort de la fumée noire
  const myersLight = interpolate(g, [cue.myers + 30, cue.myers + 90, cue.freddy - 25, cue.freddy], [0, 0.85, 0.85, 0.2], clamp);
  const myersHole = interpolate(g, [cue.myers + 20, cue.myers + 120], [0, 0.75], {...clamp, easing: Easing.out(Easing.cubic)});
  // --- FREDDY : stroboscope rouge
  const strobe = noise1(g / 2.2, 4) > -0.1 ? 1 : 0.15;
  const freddyLight = g >= cue.freddy && g < cue.ghost ? interpolate(g, [cue.freddy, cue.freddy + 20], [0, 1], clamp) * (0.45 + 0.55 * strobe) : 0;
  // --- GHOSTFACE : n'existe que dans les éclairs
  const ghostStrikes = [cue.ghost + 20, cue.ghost + 60, cue.ghost + 66, cue.ghost + 120];
  const strikeLight = ghostStrikes.reduce((m, s) => {
    const t = g - s;
    return t < 0 || t > 26 ? m : Math.max(m, t < 3 ? 1 : t < 6 ? 0.3 : t < 9 ? 0.9 : Math.exp(-(t - 9) / 7) * 0.7);
  }, 0);
  const ghostLight = g >= cue.ghost && g < cue.art ? Math.max(0.08, strikeLight) : 0;
  // --- ART : naît du brouillard
  const artLight = interpolate(g, [cue.art, cue.art + 90, cue.black - 30, cue.black], [0, 0.9, 0.9, 0], clamp);
  const artFog = interpolate(g, [cue.art, cue.art + 110, cue.black - 40, cue.black], [1, 0.35, 0.35, 1], clamp);
  const glitch = (a: number) => (g >= a && g < a + 8 ? 1 : 0);
  const sh = sumShake(g, [cue.freddy, cue.ghost + 20, cue.art + 60, tl.cues.bigImpact[1] - 50], 24, 18);
  const blackEnd = interpolate(g, [cue.black - 10, cue.black + 10], [0, 1], clamp);

  return (
    <AbsoluteFill style={{background: C.black, overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `translate(${sh.x}px,${sh.y}px) rotate(${sh.r}rad)`}}>
        {/* fond : murs de fumée sombre éclairés de rouge */}
        <Smoke seed={31} color={[0.02, 0.01, 0.012]} light={[0.35, 0.03, 0.03]} density={1} scale={1.2} flow={[0.03, 0.08]} opacity={0.9} />
        <Apparition src="horror_myers.jpg" start={cue.myers - H0} end={cue.freddy - H0} w={1180} h={1094} light={myersLight} y={900} glitch={glitch(cue.freddy - 8)} />
        <Apparition src="horror_freddy.jpg" start={cue.freddy - H0} end={cue.ghost - H0} w={1160} h={1200} light={freddyLight} y={940} glitch={glitch(cue.freddy) + glitch(cue.ghost - 8)} />
        <Apparition src="horror_ghostface.jpg" start={cue.ghost - H0} end={cue.art - H0} w={1080} h={1222} light={ghostLight} y={930} glitch={glitch(cue.ghost + 60)} />
        <Apparition src="horror_art.jpg" start={cue.art - H0} end={cue.black - H0} w={1180} h={1131} light={artLight} y={930} glitch={glitch(cue.art + 60)} drift={1.6} />
        {/* fumée noire de Myers qui s'ouvre */}
        <Smoke seed={37} color={[0.01, 0.006, 0.008]} light={[0.25, 0.03, 0.03]} density={1.35} scale={1.5} flow={[0.02, 0.14]} turb={1.2} hole={[0.5, 0.53, myersHole]} opacity={interpolate(g, [cue.myers - 10, cue.myers + 5, cue.freddy - 30, cue.freddy], [0, 1, 1, 0], clamp)} />
        {/* brouillard d'Art */}
        <Smoke seed={41} color={[0.3, 0.27, 0.28]} light={[0.7, 0.5, 0.48]} lightDir={[0, 1]} density={1.2} scale={1.7} flow={[0.12, 0.03]} opacity={g >= cue.art ? artFog : 0} />
        <Smoke seed={43} color={[0.03, 0.01, 0.01]} light={[0.5, 0.06, 0.04]} density={1} scale={2.2} flow={[-0.1, 0.05]} band={[0, 0.3, 0.1, 1]} opacity={0.7} />
        <Particles kind="ash" count={60} seed={8} speed={0.8} wind={0.2} opacity={0.9} />
        <Particles kind="embers" count={35} seed={9} area={[0, 0.7, 1, 0.3]} opacity={0.8} />
        <Lightning strikes={ghostStrikes.map(L)} from={[0.3, -0.02]} to={[0.75, 0.6]} seed={6} color="#f0e6ff" />
      </AbsoluteFill>
      {/* transitions : griffures de Freddy, éclair, flash d'impact */}
      <Claws at={L(cue.freddy + 30)} angle={-32} hold={20} />
      <Claws at={L(cue.ghost - 10)} angle={24} hold={8} scale={1.2} />
      <Flash strikes={ghostStrikes.map(L)} max={0.3} color="#e8e0ff" />
      <Flash strikes={[L(cue.myers + 2), L(cue.art - 2)]} max={0.6} />
      <Black v={interpolate(f, [0, 12], [1, 0], clamp) + blackEnd} />
    </AbsoluteFill>
  );
};
