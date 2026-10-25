import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, Easing} from 'remotion';
import {Smoke, Fire} from '../effects/Smoke';
import {Particles} from '../effects/Particles';
import {Lightning, Flash} from '../effects/Lightning';
import {sumShake, noise1} from '../effects/random';
import {PlayerRig, PATTY, TADAS} from '../components/PlayerRig';
import {FireBall} from '../components/FireBall';
import {HorrorText} from '../components/TextFX';
import {C, FONT} from '../components/Fonts';
import tl from '../timeline.json';

const S0 = tl.scenes.faceoff[0];
const L = (g: number) => g - S0;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
// séparation diagonale déchiquetée entre les deux camps
const SPLIT_L = 'polygon(0 0, 575px 0, 548px 420px, 562px 760px, 520px 1180px, 545px 1520px, 505px 1920px, 0 1920px)';
const SPLIT_R = 'polygon(575px 0, 1080px 0, 1080px 1920px, 505px 1920px, 545px 1520px, 520px 1180px, 562px 760px, 548px 420px)';

/** SCÈNE 5 : le face-à-face. */
export const S5FaceOff: React.FC = () => {
  const f = useCurrentFrame();
  const strikes = [L(2700), L(2930)];
  const t1 = L(tl.cues.faceoffText1);
  const t2 = L(tl.cues.faceoffText2);
  // tension croissante : poussée de caméra + secousses de plus en plus fortes
  const cam = interpolate(f, [0, 600], [0, 1], {...clamp, easing: Easing.in(Easing.quad)});
  const z = 1 + 0.1 * cam;
  const rumble = cam * cam * 6;
  const sh = sumShake(f, [t1, t2, ...strikes], 26, 18);
  const sx = sh.x + noise1(f / 2.5, 1) * rumble;
  const sy = sh.y + noise1(f / 2.5, 2) * rumble;
  const inL = interpolate(f, [0, 50], [-260, 0], {...clamp, easing: Easing.out(Easing.cubic)});
  const inR = interpolate(f, [0, 50], [260, 0], {...clamp, easing: Easing.out(Easing.cubic)});
  const ball = interpolate(f, [70, 130], [0, 1], {...clamp, easing: Easing.out(Easing.back(1.6))});
  const layer = (d: number): React.CSSProperties => ({transform: `translate(${sx * d}px, ${sy * d}px) scale(${1 + (z - 1) * d})`, transformOrigin: '50% 50%'});
  const colMask = 'linear-gradient(90deg, transparent 28%, #000 44%, #000 56%, transparent 72%)';

  return (
    <AbsoluteFill style={{background: C.black, overflow: 'hidden'}}>
      <AbsoluteFill style={layer(0.4)}>
        {/* camp ASVEL : noir et rouge */}
        <AbsoluteFill style={{clipPath: SPLIT_L, background: 'radial-gradient(ellipse 60% 50% at 30% 45%, #4a0608 0%, #160204 55%, #050304 100%)'}}>
          <Smoke seed={71} color={[0.01, 0.005, 0.007]} light={[0.7, 0.05, 0.05]} density={1.05} scale={1.4} flow={[0.03, 0.1]} opacity={0.9} />
        </AbsoluteFill>
        {/* camp Baskonia : rouge et orange */}
        <AbsoluteFill style={{clipPath: SPLIT_R, background: 'radial-gradient(ellipse 60% 50% at 70% 45%, #8a2a06 0%, #3a0a04 55%, #0a0404 100%)'}}>
          <Smoke seed={73} color={[0.08, 0.02, 0.005]} light={[1, 0.42, 0.1]} density={1} scale={1.4} flow={[-0.03, 0.1]} opacity={0.85} />
        </AbsoluteFill>
        <Lightning strikes={strikes} from={[0.5, -0.02]} to={[0.52, 0.55]} seed={41} color="#ffd6c0" width={6} />
      </AbsoluteFill>
      <AbsoluteFill style={layer(0.8)}>
        <Fire dir={[0, 1]} height={0.14} intensity={0.9} seed={18} scale={6} opacity={0.85} />
      </AbsoluteFill>
      <AbsoluteFill style={layer(1)}>
        <div style={{position: 'absolute', inset: 0, transform: `translateX(${inL}px)`}}>
          <PlayerRig def={PATTY} x={-262} y={420} scale={1.25} reveal={1} eyes={1} cracks={0.7} rim={0.9} aura="rgba(215,25,32,.8)" shadow={0.5} seed={3} />
        </div>
        <div style={{position: 'absolute', inset: 0, transform: `translateX(${inR}px)`, WebkitMaskImage: 'linear-gradient(180deg, #000 72%, transparent 80.5%)'}}>
          <PlayerRig def={TADAS} x={478} y={640} scale={0.98} reveal={1} eyes={1} cracks={0.6} rim={0.9} aura="rgba(255,100,27,.75)" shadow={0.5} seed={7} />
        </div>
      </AbsoluteFill>
      {/* colonne de fumée qui monte entre les deux joueurs */}
      <AbsoluteFill style={{...layer(1.15), WebkitMaskImage: colMask}}>
        <Smoke seed={75} color={[0.05, 0.015, 0.012]} light={[1, 0.3, 0.08]} lightDir={[0, -1]} density={1.25} scale={2.2} flow={[0, 0.32]} turb={1.3} opacity={0.95} />
      </AbsoluteFill>
      <AbsoluteFill style={layer(1.25)}>
        <Smoke seed={77} color={[0.02, 0.008, 0.008]} light={[0.6, 0.12, 0.05]} lightDir={[0, 1]} density={1.2} scale={1.7} flow={[0.15, 0.03]} band={[0, 0.22, 0.08, 1]} opacity={0.95} />
        {ball > 0 ? (
          <div style={{transform: `scale(${ball})`, transformOrigin: '540px 1150px'}}>
            <FireBall cx={540} cy={1150 + Math.sin(f / 20) * 10} size={230} spinSpeed={3.4} lava={0.55} />
          </div>
        ) : null}
        <Particles kind="embers" count={110} seed={44} area={[0, 0.4, 1, 0.6]} speed={1.4} opacity={1} />
        <Particles kind="ash" count={40} seed={45} opacity={0.7} wind={0.3} />
      </AbsoluteFill>
      {/* textes */}
      <AbsoluteFill style={{transform: `translate(${sx * 0.5}px, ${sy * 0.5}px)`}}>
        <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: 480, background: 'linear-gradient(180deg, rgba(8,6,8,.9) 30%, transparent)'}} />
        <HorrorText text="DEUX ÉQUIPES" at={t1} out={t2 - 40} y={170} size={130} stagger={3} />
        <HorrorText text="UN SEUL" at={t2} y={110} size={120} stagger={3} />
        <HorrorText text="VAINQUEUR" at={t2 + 16} y={240} size={170} stagger={3} color="#ff3b1f" glow="#ff641b" scratches />
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 300, background: 'linear-gradient(0deg, rgba(8,6,8,.95) 30%, transparent)'}} />
        <div style={{position: 'absolute', left: 60, bottom: 90, opacity: interpolate(f, [40, 70], [0, 1], clamp)}}>
          <Img src={staticFile('logo_asvel.png')} style={{height: 96, filter: 'drop-shadow(0 0 12px rgba(215,25,32,.9))'}} />
        </div>
        <div style={{position: 'absolute', right: 60, bottom: 70, display: 'flex', alignItems: 'center', gap: 14, opacity: interpolate(f, [40, 70], [0, 1], clamp)}}>
          <div style={{fontFamily: FONT.title, fontSize: 54, color: C.white, letterSpacing: 2, textShadow: '0 0 18px #ff641b'}}>BASKONIA</div>
          <Img src={staticFile('logo_baskonia.png')} style={{height: 120}} />
        </div>
      </AbsoluteFill>
      <Flash strikes={strikes} max={0.3} color="#ffd6c0" />
      <Flash strikes={[t1, t2]} max={0.35} color="#ff3a20" />
    </AbsoluteFill>
  );
};
