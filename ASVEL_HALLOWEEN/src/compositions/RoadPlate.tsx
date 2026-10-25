import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {ShaderCanvas} from '../effects/ShaderCanvas';
import {skyPx} from '../effects/cpuShaders';
import {Smoke} from '../effects/Smoke';
import {Moon} from '../effects/Moon';

/** Arbres morts procéduraux de part et d'autre de la route. */
const DeadTrees: React.FC<{hz: number}> = ({hz}) => {
  const branch = (x: number, y: number, len: number, ang: number, w: number, depth: number, seed: number): string[] => {
    if (depth > 6 || len < 8) return [];
    const x2 = x + Math.cos(ang) * len, y2 = y - Math.sin(ang) * len;
    const out = [`<line x1="${x}" y1="${y}" x2="${x2}" y2="${y2}" stroke="#050304" stroke-width="${w}" stroke-linecap="round"/>`];
    const r = (k: number) => {
      const v = Math.sin(seed * 91.3 + depth * 13.7 + k * 7.1) * 43758.5;
      return v - Math.floor(v);
    };
    out.push(...branch(x2, y2, len * (0.62 + 0.15 * r(1)), ang + 0.35 + 0.3 * r(2), w * 0.62, depth + 1, seed * 1.7 + 1));
    out.push(...branch(x2, y2, len * (0.6 + 0.15 * r(3)), ang - 0.4 - 0.3 * r(4), w * 0.6, depth + 1, seed * 2.3 + 2));
    return out;
  };
  const trees = [
    [-30, hz + 520, 330, 1.45, 34, 1],
    [140, hz + 120, 150, 1.6, 14, 2],
    [1110, hz + 600, 360, 1.7, 38, 3],
    [930, hz + 140, 170, 1.5, 15, 4],
  ];
  const svg = trees.map(([x, y, l, a, w, s]) => branch(x, y, l, a, w, 0, s).join('')).join('');
  return <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}} dangerouslySetInnerHTML={{__html: svg}} />;
};

/** Décor de départ du plan "la marche" : route sombre mouillée, vraie LDLC Arena au loin. */
export const RoadPlate: React.FC = () => {
  const W = 1080, H = 1920, hz = 1010;
  const aw = 760, ah = aw * 1290 / 1720;
  return (
    <AbsoluteFill style={{background: '#080608'}}>
      <ShaderCanvas scale={0.25} opaque make={(t) => skyPx({t: t + 3, red: 1, flash: 0})} />
      <Moon x={790} y={560} r={150} amt={1} />
      <div style={{position: 'absolute', left: W / 2 - aw / 2, top: hz - ah * 0.86, width: aw, height: ah}}>
        <Img src={staticFile('arena_building.png')} style={{width: aw, height: ah, filter: 'brightness(.55) contrast(1.2) saturate(.7)'}} />
        <Img src={staticFile('arena_tint.png')} style={{position: 'absolute', inset: 0, width: aw, height: ah, mixBlendMode: 'multiply'}} />
        <Img src={staticFile('arena_lights_red.png')} style={{position: 'absolute', inset: 0, width: aw, height: ah, mixBlendMode: 'screen'}} />
        <Img src={staticFile('arena_lights_red.png')} style={{position: 'absolute', inset: 0, width: aw, height: ah, mixBlendMode: 'screen', filter: 'blur(14px)'}} />
      </div>
      {/* route en perspective */}
      <svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id="road" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#1a0d0e" />
            <stop offset="1" stopColor="#0b0708" />
          </linearGradient>
          <linearGradient id="refl" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="rgba(255,70,30,.55)" />
            <stop offset="1" stopColor="rgba(255,70,30,0)" />
          </linearGradient>
        </defs>
        <rect x={0} y={hz} width={W} height={H - hz} fill="#0d0a0a" />
        <path d={`M${W / 2 - 70},${hz} L${W / 2 + 70},${hz} L${W + 260},${H} L${-260},${H} Z`} fill="url(#road)" />
        {Array.from({length: 9}).map((_, i) => {
          const a = Math.pow(i / 9, 2), b = Math.pow((i + 0.45) / 9, 2);
          const y1 = hz + (H - hz) * a, y2 = hz + (H - hz) * b;
          return <path key={i} d={`M${W / 2 - 2 - 9 * a},${y1} L${W / 2 + 2 + 9 * a},${y1} L${W / 2 + 2 + 9 * b},${y2} L${W / 2 - 2 - 9 * b},${y2} Z`} fill="rgba(220,200,180,.35)" />;
        })}
      </svg>
      <div style={{position: 'absolute', left: W / 2 - aw / 2, top: hz, width: aw, height: ah * 1.5, filter: 'blur(9px)', opacity: 0.6, mixBlendMode: 'screen', WebkitMaskImage: 'linear-gradient(180deg, #000, transparent 85%)'}}>
        <Img src={staticFile('arena_lights_red.png')} style={{width: aw, height: ah * 1.5, transform: 'scaleY(-1)'}} />
      </div>
      <DeadTrees hz={hz} />
      <Smoke seed={91} color={[0.25, 0.2, 0.21]} light={[0.7, 0.4, 0.35]} lightDir={[0, 1]} density={1} scale={1.6} flow={[0.1, 0.02]} band={[0.38, 0.5, 0.06, 0]} opacity={0.75} />
      <Smoke seed={93} color={[0.12, 0.08, 0.08]} light={[0.5, 0.2, 0.15]} lightDir={[0, 1]} density={1} scale={2} flow={[0.1, 0.02]} band={[0, 0.14, 0.06, 1]} opacity={0.6} />
    </AbsoluteFill>
  );
};
