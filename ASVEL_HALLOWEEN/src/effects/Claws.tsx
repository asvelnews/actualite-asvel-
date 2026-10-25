import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {hash} from './random';

/** Contour d'une entaille effilée (fine aux extrémités, large au centre, bords irréguliers). */
const slashPath = (len: number, width: number, p: number, bow: number, seed: number) => {
  const n = 40;
  const top: string[] = [];
  const bot: string[] = [];
  const m = Math.max(2, Math.round(n * p));
  for (let i = 0; i <= m; i++) {
    const t = i / n;
    const x = -len / 2 + t * len;
    const y = Math.sin(t * Math.PI) * bow;
    const w = Math.pow(Math.sin(t * Math.PI), 0.8) * width * (0.85 + 0.3 * hash(i * 3.7 + seed));
    top.push(`${x},${y - w / 2}`);
    bot.unshift(`${x},${y + w / 2 * (0.6 + 0.4 * hash(i + seed * 9))}`);
  }
  return `M${top.join(' L')} L${bot.join(' L')} Z`;
};

/**
 * Trois griffures qui lacèrent l'écran : tracé rapide, cœur incandescent,
 * bords sanglants sombres, puis cicatrisation (fondu).
 */
export const Claws: React.FC<{at: number; angle?: number; hold?: number; scale?: number; y?: number; x?: number}> = ({
  at,
  angle = -28,
  hold = 30,
  scale = 1,
  x = 0.5,
  y = 0.5,
}) => {
  const frame = useCurrentFrame();
  const {width: W, height: H} = useVideoConfig();
  const t = frame - at;
  if (t < 0 || t > 14 + hold + 20) return null;
  const fade = interpolate(t, [14 + hold, 14 + hold + 20], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const L = 1700;
  return (
    <AbsoluteFill style={{opacity: fade}}>
      <svg width={W} height={H}>
        <defs>
          <filter id={`cg${at}`} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="7" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <g transform={`translate(${x * W},${y * H}) rotate(${angle}) scale(${scale})`}>
          {[-1, 0, 1].map((k, i) => {
            const p = interpolate(t - i * 2.5, [0, 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
            if (p <= 0) return null;
            const off = k * 120 + (i === 1 ? 10 : 0);
            return (
              <g key={k} transform={`translate(0,${off})`}>
                <path d={slashPath(L * (0.92 + 0.08 * i), 95, p, -60, i + 1)} fill="#1a0003" opacity={0.85} />
                <path d={slashPath(L * (0.92 + 0.08 * i), 58, p, -60, i + 1)} fill="#8f0610" />
                <g filter={`url(#cg${at})`}>
                  <path d={slashPath(L * (0.92 + 0.08 * i), 24, p, -60, i + 1)} fill="#D71920" />
                  <path d={slashPath(L * (0.92 + 0.08 * i), 5, p, -60, i + 1)} fill="#ffb08a" />
                </g>
              </g>
            );
          })}
        </g>
      </svg>
    </AbsoluteFill>
  );
};
