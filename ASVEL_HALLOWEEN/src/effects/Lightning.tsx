import React, {useMemo} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {rng} from './random';

type Seg = {x1: number; y1: number; x2: number; y2: number; w: number};

const bolt = (seed: number, x0: number, y0: number, x1: number, y1: number, W: number): Seg[] => {
  const r = rng(seed);
  const segs: Seg[] = [];
  const grow = (ax: number, ay: number, bx: number, by: number, w: number, depth: number) => {
    // déplacement du point milieu récursif
    let pts = [[ax, ay], [bx, by]];
    let disp = Math.hypot(bx - ax, by - ay) * 0.22;
    for (let k = 0; k < 7; k++) {
      const np: number[][] = [pts[0]];
      for (let i = 0; i < pts.length - 1; i++) {
        const [px, py] = pts[i], [qx, qy] = pts[i + 1];
        np.push([(px + qx) / 2 + (r() - 0.5) * disp, (py + qy) / 2 + (r() - 0.5) * disp * 0.3], pts[i + 1]);
      }
      pts = np;
      disp *= 0.55;
    }
    for (let i = 0; i < pts.length - 1; i++) {
      segs.push({x1: pts[i][0], y1: pts[i][1], x2: pts[i + 1][0], y2: pts[i + 1][1], w: w * (1 - (i / pts.length) * 0.6)});
      if (depth < 2 && r() < 0.06) {
        const ang = Math.atan2(by - ay, bx - ax) + (r() - 0.5) * 1.6;
        const L = Math.hypot(bx - ax, by - ay) * (0.15 + r() * 0.3);
        grow(pts[i][0], pts[i][1], pts[i][0] + Math.cos(ang) * L, pts[i][1] + Math.sin(ang) * L, w * 0.45, depth + 1);
      }
    }
  };
  grow(x0, y0, x1, y1, W, 0);
  return segs;
};

/**
 * Éclair ramifié qui frappe à chaque frame de `strikes` : 2 flashs rapides puis
 * persistance rétinienne. Renvoie aussi l'illumination globale via `flashLevel`.
 */
export const flashLevel = (frame: number, strikes: number[]) => {
  let v = 0;
  for (const s of strikes) {
    const t = frame - s;
    if (t < 0 || t > 30) continue;
    const a = t < 3 ? 1 : t < 6 ? 0.25 : t < 9 ? 0.85 : Math.exp(-(t - 9) / 6) * 0.6;
    v = Math.max(v, a);
  }
  return v;
};

export const Lightning: React.FC<{
  strikes: number[];
  color?: string;
  from?: [number, number];
  to?: [number, number];
  width?: number;
  seed?: number;
}> = ({strikes, color = '#ffd9d9', from = [0.6, -0.02], to = [0.45, 0.5], width = 5, seed = 1}) => {
  const frame = useCurrentFrame();
  const {width: W, height: H} = useVideoConfig();
  const active = strikes.map((s, i) => ({s, i})).filter(({s}) => frame - s >= 0 && frame - s < 22);
  const bolts = useMemo(
    () => strikes.map((s, i) => bolt(seed * 31 + i * 7 + 1, (from[0] + (i % 3 - 1) * 0.12) * W, from[1] * H, (to[0] + ((i * 7) % 5 - 2) * 0.06) * W, to[1] * H, width)),
    [strikes, seed, W, H, from, to, width],
  );
  if (!active.length) return null;
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen'}}>
      <svg width={W} height={H}>
        <defs>
          <filter id={`glow${seed}`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="10" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {active.map(({s, i}) => {
          const t = frame - s;
          const op = t < 3 ? 1 : t < 6 ? 0.2 : t < 9 ? 0.9 : Math.max(0, 1 - (t - 9) / 12);
          return (
            <g key={i} filter={`url(#glow${seed})`} opacity={op}>
              {bolts[i].map((sg, k) => (
                <line key={k} x1={sg.x1} y1={sg.y1} x2={sg.x2} y2={sg.y2} stroke={color} strokeWidth={sg.w} strokeLinecap="round" />
              ))}
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

/** Flash plein écran (éclair, explosion). */
export const Flash: React.FC<{strikes: number[]; color?: string; max?: number}> = ({strikes, color = '#fff', max = 0.8}) => {
  const frame = useCurrentFrame();
  const v = flashLevel(frame, strikes) * max;
  if (v <= 0.001) return null;
  return <AbsoluteFill style={{background: color, opacity: v, mixBlendMode: 'screen'}} />;
};
