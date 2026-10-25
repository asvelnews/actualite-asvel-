import React from 'react';
import {interpolate, useCurrentFrame, Easing} from 'remotion';
import {hash, noise1} from '../effects/random';
import {C, FONT} from './Fonts';

/**
 * Texte d'horreur : chaque lettre s'allume en vacillant (néon défaillant), passe du flou
 * au net, lueur rouge pulsée, puis se dissout dans la fumée à `out`.
 */
export const HorrorText: React.FC<{
  text: string;
  at: number;
  out?: number;
  size?: number;
  font?: string;
  color?: string;
  glow?: string;
  y: number;
  stagger?: number;
  tracking?: number;
  scratches?: boolean;
}> = ({text, at, out, size = 110, font = FONT.title, color = C.white, glow = C.blood, y, stagger = 3, tracking = 4, scratches = false}) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  if (t < 0) return null;
  const outP = out === undefined ? 0 : interpolate(frame, [out, out + 24], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (outP >= 1) return null;
  const pulse = 0.75 + 0.25 * Math.sin(frame / 7);
  const push = interpolate(t, [0, 160], [1.06, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.quad)});
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top: y,
        textAlign: 'center',
        fontFamily: font,
        fontSize: size,
        letterSpacing: tracking,
        lineHeight: 1,
        color,
        transform: `scale(${push + outP * 0.15})`,
        filter: `blur(${outP * 14}px)`,
        opacity: 1 - outP,
        whiteSpace: 'pre',
      }}
    >
      {text.split('').map((ch, i) => {
        const lt = t - i * stagger;
        const on = lt < 0 ? 0 : lt < 14 ? (hash(i * 13 + Math.floor(lt / 2)) > 0.45 ? 1 : 0.15) : 1;
        const blur = interpolate(lt, [0, 18], [10, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        const dy = interpolate(lt, [0, 18], [18, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
        const fl = 0.92 + 0.08 * noise1(frame / 3 + i, i);
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              opacity: on * fl,
              filter: `blur(${blur}px)`,
              transform: `translateY(${dy}px)`,
              textShadow: `0 0 ${18 * pulse}px ${glow}, 0 0 ${48 * pulse}px ${glow}, 0 4px 0 rgba(0,0,0,.6)`,
            }}
          >
            {ch === ' ' ? ' ' : ch}
          </span>
        );
      })}
      {scratches && t > 10 ? <Scratches w={size * text.length * 0.55} h={size} t={t - 10} /> : null}
    </div>
  );
};

/** Lacérations diagonales (3 griffes) qui entaillent un titre. */
const Scratches: React.FC<{w: number; h: number; t: number}> = ({w, h, t}) => {
  const p = Math.min(1, t / 7);
  return (
    <svg width={w} height={h * 1.4} style={{position: 'absolute', left: '50%', top: -h * 0.2, transform: 'translateX(-50%)', overflow: 'visible'}}>
      {[0, 1, 2].map((k) => {
        const x0 = w * (0.74 + k * 0.05), y0 = 0;
        const x1 = x0 + w * 0.12, y1 = h * 1.4;
        return (
          <g key={k}>
            <line x1={x0} y1={y0} x2={x0 + (x1 - x0) * p} y2={y0 + (y1 - y0) * p} stroke="#140002" strokeWidth={7} opacity={0.8} strokeLinecap="round" />
            <line x1={x0} y1={y0} x2={x0 + (x1 - x0) * p} y2={y0 + (y1 - y0) * p} stroke="#D71920" strokeWidth={3} strokeLinecap="round" />
          </g>
        );
      })}
    </svg>
  );
};

/** Titre métallique extrudé (empilement d'ombres = profondeur 3D), biseau doré, reflets. */
export const MetalText: React.FC<{
  text: string;
  size: number;
  depth?: number;
  sweep?: number; // 0..1 position du reflet
  face?: string;
  side?: string;
  glow?: string;
  font?: string;
  style?: React.CSSProperties;
}> = ({text, size, depth = 22, sweep = 0.5, face, side = '#3a0a0c', glow = C.blood, font = FONT.title, style}) => {
  const layers: string[] = [];
  for (let i = 1; i <= depth; i++) {
    const k = i / depth;
    const c = `rgb(${Math.round(70 - 50 * k)},${Math.round(14 - 10 * k)},${Math.round(16 - 12 * k)})`;
    layers.push(`${i * 0.6}px ${i}px 0 ${i === depth ? '#050203' : c}`);
  }
  layers.push(`0 ${depth + 10}px 40px rgba(0,0,0,.9)`, `0 0 60px ${glow}`, `0 0 120px ${glow}`);
  const s = Math.round(sweep * 300 - 100);
  const grad =
    face ??
    `linear-gradient(170deg, #fff8ee 0%, #e9e2da 22%, #8d8580 45%, #f4f1ec 52%, #6c625c 70%, #d6a85a 100%)`;
  return (
    <div style={{position: 'relative', fontFamily: font, fontSize: size, lineHeight: 0.95, letterSpacing: 2, ...style}}>
      <div style={{color: side, textShadow: layers.join(','), position: 'absolute', inset: 0}}>{text}</div>
      <div
        style={{
          position: 'relative',
          backgroundImage: `linear-gradient(105deg, transparent ${s - 12}%, rgba(255,255,255,.95) ${s}%, transparent ${s + 12}%), ${grad}`,
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          color: 'transparent',
          WebkitTextStroke: '2px rgba(60,10,10,.6)',
        }}
      >
        {text}
      </div>
    </div>
  );
};
