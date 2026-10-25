import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, Easing} from 'remotion';
import {Smoke, Fire} from '../effects/Smoke';
import {Particles} from '../effects/Particles';
import {Lightning, Flash} from '../effects/Lightning';
import {sumShake, noise1} from '../effects/random';
import {PlayerRig, TADAS} from '../components/PlayerRig';
import {HorrorText, MetalText} from '../components/TextFX';
import {C, FONT} from '../components/Fonts';
import tl from '../timeline.json';

const S0 = tl.scenes.tadas[0];
const L = (g: number) => g - S0;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** SCÈNE 4 : Tadas Sedekerskis, le cauchemar de Baskonia. */
export const S4Tadas: React.FC = () => {
  const f = useCurrentFrame();
  const blast = L(tl.cues.tadasRedBlast);
  const nameAt = L(tl.cues.tadasName);
  const strikes = [L(2050), L(2260), L(2400)];
  // travelling virtuel latéral + poussée ; profondeur de champ simulée par couches floutées
  const cam = interpolate(f, [0, 600], [0, 1], {...clamp, easing: Easing.inOut(Easing.sin)});
  const tx = -50 + 100 * cam;
  const z = 1.02 + 0.14 * cam;
  const sh = sumShake(f, [blast, nameAt, strikes[1]], 28, 22);
  const reveal = interpolate(f, [blast, blast + 50], [0, 1], {...clamp, easing: Easing.out(Easing.quad)});
  const eyes = interpolate(f, [blast + 50, blast + 110], [0, 1], clamp);
  const cracks = interpolate(f, [blast + 80, blast + 170], [0, 0.75], clamp);
  const blastHole = interpolate(f, [blast, blast + 70], [0, 1.3], {...clamp, easing: Easing.out(Easing.exp)});
  const layer = (depth: number): React.CSSProperties => ({
    transform: `translate(${tx * depth + sh.x * depth}px, ${sh.y * depth}px) scale(${1 + (z - 1) * depth}) rotate(${sh.r * depth}rad)`,
    transformOrigin: '50% 40%',
  });
  const nameT = f - nameAt;
  const slam = interpolate(nameT, [0, 10], [1.6, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const sweep = interpolate(nameT, [10, 70], [0, 1.3], clamp);

  return (
    <AbsoluteFill style={{background: C.black, overflow: 'hidden'}}>
      <AbsoluteFill style={{...layer(0.3), filter: 'blur(3px)'}}>
        <AbsoluteFill style={{background: 'radial-gradient(ellipse 70% 55% at 50% 50%, #5a1404 0%, #2a0604 45%, #080608 100%)'}} />
        <Smoke seed={61} color={[0.03, 0.008, 0.005]} light={[0.95, 0.3, 0.06]} lightDir={[0.3, -1]} density={1} scale={1.4} flow={[-0.03, 0.1]} opacity={0.9} />
        <Lightning strikes={strikes} from={[0.4, -0.02]} to={[0.62, 0.34]} seed={21} color="#ffb070" />
        <Lightning strikes={strikes.map((s) => s + 4)} from={[0.7, -0.02]} to={[0.25, 0.3]} seed={23} color="#ff9050" width={4} />
      </AbsoluteFill>
      <AbsoluteFill style={layer(0.55)}>
        <Smoke seed={63} color={[0.18, 0.02, 0.02]} light={[1, 0.35, 0.1]} lightDir={[0, -1]} density={0.85} scale={2.1} flow={[0.05, 0.08]} band={[0.25, 0.75, 0.15, 0]} opacity={0.6} blend="screen" />
        <Fire dir={[0, 1]} height={0.13} intensity={0.85} seed={14} scale={5.5} opacity={interpolate(f, [blast, blast + 60], [0, 0.85], clamp)} />
      </AbsoluteFill>
      <AbsoluteFill style={layer(1)}>
        <PlayerRig def={TADAS} x={-23} y={430} scale={1.6} reveal={reveal} eyes={eyes} cracks={cracks} rim={reveal * 0.9} aura="rgba(255,100,27,.7)" shadow={0.6} seed={7} />
        {/* étincelles sur les contours du maillot (épaules) */}
        <Particles kind="sparks" count={26} seed={31} area={[0.18, 0.47, 0.07, 0.02]} speed={0.9} opacity={reveal} />
        <Particles kind="sparks" count={26} seed={32} area={[0.77, 0.47, 0.07, 0.02]} speed={0.9} opacity={reveal} />
        <Particles kind="embers" count={70} seed={33} area={[0, 0.5, 1, 0.5]} speed={1.2} opacity={reveal} />
      </AbsoluteFill>
      {/* premier plan flou : brouillard noir autour des jambes, volutes */}
      <AbsoluteFill style={layer(1.35)}>
        <Smoke seed={65} color={[0.01, 0.005, 0.006]} light={[0.5, 0.12, 0.04]} lightDir={[0, 1]} density={1.3} scale={1.6} flow={[-0.2, 0.03]} band={[0.0, 0.26, 0.1, 1]} opacity={0.95} />
        <Smoke seed={67} color={[0.02, 0.01, 0.01]} light={[0.4, 0.08, 0.03]} density={1.1} scale={0.9} flow={[0.3, 0.05]} band={[0.0, 1, 0.1, 3]} opacity={interpolate(f, [300, 380, 480, 560], [0, 0.35, 0.35, 0], clamp)} style={{filter: 'blur(8px)'}} />
        <Particles kind="sparks" count={160} seed={34} burstAt={blast} burstCenter={[0.5, 0.5]} />
        <Particles kind="sparks" count={120} seed={35} burstAt={nameAt} burstCenter={[0.5, 0.12]} />
      </AbsoluteFill>
      {/* explosion de fumée rouge */}
      <Smoke seed={69} color={[0.35, 0.02, 0.03]} light={[1, 0.3, 0.1]} lightDir={[0, -1]} density={1.6} scale={1.3} flow={[0.0, 0.35]} turb={1.6} hole={[0.5, 0.5, blastHole]} opacity={interpolate(f, [0, blast - 4, blast + 60, blast + 110], [1, 1, 0.9, 0], clamp)} />
      {/* texte en haut (le visage reste dégagé) */}
      <AbsoluteFill style={{transform: `translate(${sh.x * 0.5}px, ${sh.y * 0.5}px)`}}>
        <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: 560, background: 'linear-gradient(180deg, rgba(8,6,8,.92) 35%, rgba(8,6,8,.5) 70%, transparent)', opacity: interpolate(nameT, [-20, 10], [0, 1], clamp)}} />
        {nameT >= 0 ? (
          <div style={{position: 'absolute', left: 0, right: 0, top: 60, display: 'flex', flexDirection: 'column', alignItems: 'center', transform: `scale(${slam})`, opacity: interpolate(nameT, [0, 4], [0, 1], clamp)}}>
            <MetalText text="TADAS" size={112} depth={12} sweep={sweep} glow="#ff641b" />
            <MetalText text="SEDEKERSKIS" size={140} depth={16} sweep={sweep - 0.1} glow="#ff641b" />
          </div>
        ) : null}
        {nameT > 22 ? (
          <div style={{position: 'absolute', left: 0, right: 0, top: 345, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 26, opacity: interpolate(nameT, [22, 36], [0, 1], clamp)}}>
            <Img src={staticFile('logo_baskonia.png')} style={{height: 104, filter: 'drop-shadow(0 0 10px rgba(255,100,27,.8))'}} />
            <div style={{fontFamily: FONT.title, fontSize: 64, color: C.white, letterSpacing: 3, textShadow: '0 0 20px #ff641b'}}>BASKONIA</div>
          </div>
        ) : null}
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 380, background: 'linear-gradient(0deg, rgba(8,6,8,.95) 35%, transparent)', opacity: interpolate(nameT, [30, 50], [0, 1], clamp)}} />
        <HorrorText text="13,0 PIR" at={nameAt + 45} y={1690} size={96} color={C.gold} glow="#a8641e" stagger={2} />
        <HorrorText text="STATISTIQUE D'AVANT-MATCH" at={nameAt + 60} y={1795} size={30} font={FONT.body} color="#cfc6bd" glow="rgba(0,0,0,0)" stagger={1} tracking={6} />
      </AbsoluteFill>
      <Flash strikes={strikes} max={0.22} color="#ffc090" />
      <Flash strikes={[blast, nameAt]} max={0.5} color="#ff4a1a" />
    </AbsoluteFill>
  );
};
