import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, Easing} from 'remotion';
import {Smoke, Fire} from '../effects/Smoke';
import {Particles} from '../effects/Particles';
import {Flash} from '../effects/Lightning';
import {Claws} from '../effects/Claws';
import {Bats} from '../effects/Bats';
import {Cobweb} from '../effects/Overlays';
import {sumShake, noise1} from '../effects/random';
import {MetalText} from '../components/TextFX';
import {C, FONT} from '../components/Fonts';
import tl from '../timeline.json';

const S0 = tl.scenes.gameday[0];
const L = (g: number) => g - S0;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Reveal: React.FC<{at: number; children: React.ReactNode; y: number; from?: number}> = ({at, children, y, from = 40}) => {
  const f = useCurrentFrame();
  const t = f - at;
  if (t < 0) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top: y,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        opacity: interpolate(t, [0, 14], [0, 1], clamp),
        transform: `translateY(${interpolate(t, [0, 18], [from, 0], {...clamp, easing: Easing.out(Easing.cubic)})}px)`,
        filter: `blur(${interpolate(t, [0, 12], [8, 0], clamp)}px)`,
      }}
    >
      {children}
    </div>
  );
};

const Sep: React.FC = () => <div style={{width: 2, height: 64, background: 'linear-gradient(180deg, transparent, #D6A85A, transparent)', margin: '0 30px'}} />;

/** SCÈNE 6 : GAME DAY final (composition inspirée de l'affiche Halloween). */
export const S6GameDay: React.FC = () => {
  const f = useCurrentFrame();
  const info = L(tl.cues.infoReveal);
  const brand = L(tl.cues.brand);
  const fade = L(tl.cues.fadeOut);
  const slam = interpolate(f, [0, 9], [2.4, 1], {...clamp, easing: Easing.out(Easing.exp)});
  const slam2 = interpolate(f, [8, 17], [2.4, 1], {...clamp, easing: Easing.out(Easing.exp)});
  const sh = sumShake(f, [0, 8, L(tl.cues.bigImpact[5])], 34, 30);
  const sweep = interpolate(f, [20, 110], [-0.2, 1.3], clamp);
  const z = interpolate(f, [0, 480], [1.06, 1], {...clamp, easing: Easing.out(Easing.quad)});
  const flick = 0.85 + 0.15 * noise1(f / 3, 5);
  // disparition finale dans la fumée noire
  const endSmoke = interpolate(f, [fade, fade + 90], [0, 1], {...clamp, easing: Easing.in(Easing.quad)});
  const fadeBlack = interpolate(f, [fade + 70, 478], [0, 1], clamp);
  const corner = (side: 'left' | 'right'): React.CSSProperties => ({
    position: 'absolute',
    [side]: -30,
    bottom: 120,
    width: 520,
    height: 333,
    filter: `brightness(${flick})`,
    WebkitMaskImage: `radial-gradient(ellipse 60% 60% at ${side === 'left' ? '40%' : '60%'} 60%, #000 40%, transparent 75%)`,
  });

  return (
    <AbsoluteFill style={{background: C.black, overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `translate(${sh.x}px, ${sh.y}px) rotate(${sh.r}rad) scale(${z})`}}>
        <AbsoluteFill style={{background: 'radial-gradient(ellipse 80% 45% at 50% 35%, #5a0a0c 0%, #1d0304 50%, #080608 100%)'}} />
        <Smoke seed={81} color={[0.02, 0.008, 0.01]} light={[0.8, 0.12, 0.06]} density={1} scale={1.4} flow={[0.02, 0.12]} opacity={0.9} />
        <Bats count={7} seed={9} band={[0.02, 0.14]} speed={1.2} />
        {/* LDLC Arena réelle en bas, comme sur l'affiche */}
        <div style={{position: 'absolute', left: 540 - 430, top: 1080, width: 860, height: 645, opacity: 0.9}}>
          <Img src={staticFile('arena_building.png')} style={{width: 860, height: 645, filter: 'brightness(.45) contrast(1.2) saturate(.6)'}} />
          <Img src={staticFile('arena_tint.png')} style={{position: 'absolute', inset: 0, width: 860, height: 645, mixBlendMode: 'multiply'}} />
          <Img src={staticFile('arena_lights_red.png')} style={{position: 'absolute', inset: 0, width: 860, height: 645, mixBlendMode: 'screen', opacity: flick}} />
        </div>
        <Fire dir={[0, 1]} height={0.2} intensity={0.95} seed={22} scale={6} opacity={interpolate(f, [info - 10, info + 30], [0.9, 0.45], clamp)} />
        <Smoke seed={83} color={[0.25, 0.08, 0.06]} light={[1, 0.4, 0.15]} lightDir={[0, 1]} density={1.1} scale={1.8} flow={[0.2, 0.02]} band={[0, 0.3, 0.1, 1]} opacity={0.75} />
        <Img src={staticFile('pumpkins_left.jpg')} style={corner('left')} />
        <Img src={staticFile('pumpkins_right.jpg')} style={corner('right')} />
        {/* titre GAME DAY */}
        <div style={{position: 'absolute', left: 0, right: 0, top: 250, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <div style={{transform: `scale(${slam}) rotate(-4deg)`, opacity: interpolate(f, [0, 3], [0, 1], clamp)}}>
            <MetalText text="GAME" size={330} depth={26} sweep={sweep} />
          </div>
          <div style={{transform: `scale(${slam2}) rotate(-4deg)`, marginTop: -40, opacity: interpolate(f, [8, 11], [0, 1], clamp)}}>
            <MetalText
              text="DAY"
              size={360}
              depth={26}
              sweep={sweep - 0.15}
              glow="#ff641b"
              face="linear-gradient(170deg, #ffd27a 0%, #ff8a2a 30%, #ff641b 50%, #d71920 80%, #6a0608 100%)"
            />
          </div>
        </div>
        {/* fumée qui traverse les titres */}
        <Smoke seed={85} color={[0.05, 0.02, 0.02]} light={[0.7, 0.2, 0.1]} density={0.9} scale={1.1} flow={[0.3, 0.02]} band={[0.55, 0.85, 0.08, 0]} opacity={0.5} />
        <Particles kind="embers" count={120} seed={52} area={[0, 0.5, 1, 0.5]} speed={1.3} />
        <Particles kind="sparks" count={200} seed={53} burstAt={0} burstCenter={[0.5, 0.3]} />
        <Particles kind="sparks" count={140} seed={54} burstAt={8} burstCenter={[0.5, 0.42]} />
        <Cobweb corner="tl" size={380} opacity={0.3} seed={2} />
        <Cobweb corner="tr" size={330} opacity={0.25} seed={5} />
      </AbsoluteFill>
      <Claws at={14} angle={-20} hold={24} scale={0.9} y={0.32} />
      {/* informations du match */}
      <AbsoluteFill>
        <div style={{position: 'absolute', left: 0, right: 0, top: 1110, height: 810, background: 'linear-gradient(180deg, transparent, rgba(8,6,8,.75) 16%, rgba(8,6,8,.9) 100%)', opacity: interpolate(f, [info - 10, info + 10], [0, 1], clamp)}} />
        <Reveal at={info - 20} y={110}>
          <div style={{fontFamily: FONT.body, fontWeight: 700, fontSize: 36, color: C.gold, letterSpacing: 10}}>TURKISH AIRLINES EUROLEAGUE</div>
        </Reveal>
        <Reveal at={info} y={1160}>
          <Img src={staticFile('logo_asvel.png')} style={{height: 130, filter: 'drop-shadow(0 0 14px rgba(215,25,32,.9))'}} />
          <div style={{fontFamily: FONT.horror, fontSize: 110, color: C.ember, margin: '0 34px', textShadow: '0 0 24px #d71920'}}>VS</div>
          <Img src={staticFile('logo_baskonia.png')} style={{height: 150}} />
        </Reveal>
        <Reveal at={info + 14} y={1330}>
          <div style={{fontFamily: FONT.title, fontSize: 64, color: C.white, letterSpacing: 4}}>LDLC ASVEL</div>
          <div style={{fontFamily: FONT.title, fontSize: 44, color: C.blood, margin: '0 22px'}}>VS</div>
          <div style={{fontFamily: FONT.title, fontSize: 64, color: C.white, letterSpacing: 4}}>BASKONIA</div>
        </Reveal>
        <Reveal at={info + 30} y={1440}>
          <div style={{textAlign: 'center'}}>
            <div style={{fontFamily: FONT.title, fontSize: 58, color: C.white, letterSpacing: 6}}>LDLC ARENA</div>
            <div style={{fontFamily: FONT.body, fontSize: 32, color: '#cfc6bd', letterSpacing: 8}}>DÉCINES-CHARPIEU</div>
          </div>
          <Sep />
          <div style={{fontFamily: FONT.title, fontSize: 92, color: C.gold, letterSpacing: 2, textShadow: '0 0 20px rgba(214,168,90,.5)'}}>20H00</div>
        </Reveal>
        <Reveal at={info + 46} y={1600}>
          <div style={{textAlign: 'center'}}>
            <div style={{fontFamily: FONT.body, fontSize: 26, color: '#a89f97', letterSpacing: 10}}>DIFFUSION</div>
            <div style={{fontFamily: FONT.title, fontSize: 50, color: C.white, letterSpacing: 3}}>EUROLEAGUE TV / beIN SPORTS</div>
          </div>
        </Reveal>
        {/* signature ASVEL_NEWS */}
        <Reveal at={brand} y={1700} from={20}>
          <div
            style={{
              fontFamily: FONT.horror,
              fontSize: 136,
              color: C.blood,
              letterSpacing: 4,
              textShadow: `0 0 ${20 * flick}px #ff1a1a, 0 0 ${50 * flick}px #d71920, 0 4px 0 #2a0003`,
              transform: `rotate(-3deg) scale(${interpolate(f, [brand, brand + 14], [1.25, 1], {...clamp, easing: Easing.out(Easing.back(2))})})`,
            }}
          >
            ASVEL_NEWS
          </div>
        </Reveal>
      </AbsoluteFill>
      <Smoke seed={87} color={[0.006, 0.003, 0.004]} light={[0.2, 0.02, 0.02]} density={1.6} scale={1.2} flow={[0.05, 0.25]} turb={1.4} opacity={endSmoke} />
      <Flash strikes={[0, 8]} max={0.8} color="#ffb070" />
      <AbsoluteFill style={{background: '#000', opacity: fadeBlack}} />
    </AbsoluteFill>
  );
};
