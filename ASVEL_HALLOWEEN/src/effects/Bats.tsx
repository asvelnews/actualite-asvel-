import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {hash} from './random';

/** Chauve-souris vectorielle : battement d'ailes par déformation verticale des ailes. */
const Bat: React.FC<{flap: number; size: number; color: string}> = ({flap, size, color}) => {
  const k = Math.sin(flap);
  const wy = -18 * k; // pointe des ailes
  return (
    <svg width={size} height={size * 0.6} viewBox="-50 -30 100 60" style={{overflow: 'visible'}}>
      <path
        fill={color}
        d={`M0,-4 C4,-8 6,-6 8,-2 C18,${-6 + wy * 0.5} 30,${-10 + wy} 48,${-4 + wy} C40,${2 + wy * 0.6} 36,${6 + wy * 0.4} 34,${10 + wy * 0.3}
           C28,${6 + wy * 0.2} 22,8 18,12 C14,8 10,8 6,8 L0,12 L-6,8 C-10,8 -14,8 -18,12 C-22,8 -28,${6 + wy * 0.2} -34,${10 + wy * 0.3}
           C-36,${6 + wy * 0.4} -40,${2 + wy * 0.6} -48,${-4 + wy} C-30,${-10 + wy} -18,${-6 + wy * 0.5} -8,-2 C-6,-6 -4,-8 0,-4 Z
           M-3,-6 L-4,-11 L-1,-7 Z M3,-6 L4,-11 L1,-7 Z`}
      />
    </svg>
  );
};

export const Bats: React.FC<{count: number; seed?: number; start?: number; color?: string; band?: [number, number]; speed?: number}> = ({
  count,
  seed = 1,
  start = 0,
  color = '#0b0507',
  band = [0.05, 0.45],
  speed = 1,
}) => {
  const frame = useCurrentFrame();
  const {width: W, height: H, fps} = useVideoConfig();
  const t = (frame - start) / fps;
  if (t < 0) return null;
  return (
    <AbsoluteFill>
      {Array.from({length: count}).map((_, i) => {
        const h1 = hash(i + seed * 13), h2 = hash(i * 2.3 + seed), h3 = hash(i * 5.1 + seed * 7);
        const depth = 0.35 + 0.65 * h3;
        const dur = (3.5 + 3 * h2) / speed;
        const ph = (t / dur + h1) % 1;
        const dir = h2 > 0.5 ? 1 : -1;
        const x = dir > 0 ? -0.2 * W + ph * 1.4 * W : 1.2 * W - ph * 1.4 * W;
        const y = (band[0] + (band[1] - band[0]) * h1) * H + Math.sin(ph * 9 + i) * 60 * depth - ph * 120;
        const size = 40 + 110 * depth;
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, transform: `scaleX(${-dir}) rotate(${Math.sin(ph * 12 + i) * 10}deg)`, filter: `blur(${(1 - depth) * 2}px)`, opacity: 0.6 + 0.4 * depth}}>
            <Bat flap={t * (16 + 8 * h3) + i} size={size} color={color} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
