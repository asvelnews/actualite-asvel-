import React, {useLayoutEffect, useRef} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {hash, noise1} from './random';

/** Grain film animé (régénéré à chaque frame, basse résolution puis agrandi). */
export const Grain: React.FC<{opacity?: number}> = ({opacity = 0.12}) => {
  const frame = useCurrentFrame();
  const ref = useRef<HTMLCanvasElement>(null);
  const w = 270, h = 480;
  useLayoutEffect(() => {
    const ctx = ref.current!.getContext('2d')!;
    const img = ctx.createImageData(w, h);
    let s = (frame * 2654435761) >>> 0;
    for (let i = 0; i < w * h; i++) {
      s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0;
      const v = s & 255;
      img.data[i * 4] = v; img.data[i * 4 + 1] = v; img.data[i * 4 + 2] = v; img.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
  });
  return <canvas ref={ref} width={w} height={h} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', opacity, mixBlendMode: 'overlay', imageRendering: 'auto'}} />;
};

/** Vignette + légère respiration de l'exposition (vacillement de projecteur). */
export const Vignette: React.FC<{strength?: number}> = ({strength = 0.85}) => {
  const frame = useCurrentFrame();
  const flicker = 0.04 * noise1(frame / 4, 3);
  return (
    <AbsoluteFill
      style={{background: `radial-gradient(ellipse 75% 60% at 50% 48%, rgba(0,0,0,0) 40%, rgba(8,6,8,${strength + flicker}) 100%)`, pointerEvents: 'none'}}
    />
  );
};

/** Bandes letterbox cinéma (s'ouvrent/ferment). */
export const Letterbox: React.FC<{size?: number}> = ({size = 90}) => (
  <>
    <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: size, background: '#000'}} />
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: size, background: '#000'}} />
  </>
);

/** Fondu noir piloté (0..1). */
export const Black: React.FC<{v: number}> = ({v}) => (v > 0.001 ? <AbsoluteFill style={{background: '#000', opacity: Math.min(1, v)}} /> : null);

/** Toile d'araignée procédurale dans un coin, balancée par le vent. */
export const Cobweb: React.FC<{corner: 'tl' | 'tr' | 'bl' | 'br'; size?: number; opacity?: number; seed?: number}> = ({corner, size = 420, opacity = 0.35, seed = 1}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sway = Math.sin(frame / fps * 1.3 + seed) * 2 + noise1(frame / 40, seed) * 1.5;
  const spokes = 9;
  const rings = 8;
  const lines: string[] = [];
  const pt = (a: number, r: number) => [Math.cos(a) * r, Math.sin(a) * r];
  for (let i = 0; i < spokes; i++) {
    const a = (i / (spokes - 1)) * (Math.PI / 2);
    const [x, y] = pt(a, size * (0.9 + 0.15 * hash(i + seed)));
    lines.push(`M0,0 L${x},${y}`);
  }
  for (let k = 1; k <= rings; k++) {
    const r0 = (k / rings) * size * 0.9;
    let d = '';
    for (let i = 0; i < spokes; i++) {
      const a = (i / (spokes - 1)) * (Math.PI / 2);
      const r = r0 * (0.92 + 0.12 * hash(i * 3 + k + seed));
      const [x, y] = pt(a, r);
      if (i === 0) d += `M${x},${y}`;
      else {
        const am = ((i - 0.5) / (spokes - 1)) * (Math.PI / 2);
        const [cx, cy] = pt(am, r * 0.86); // fils qui pendent
        d += ` Q${cx},${cy} ${x},${y}`;
      }
    }
    lines.push(d);
  }
  const tf = {tl: 'scale(1,1)', tr: 'scale(-1,1)', bl: 'scale(1,-1)', br: 'scale(-1,-1)'}[corner];
  const pos: React.CSSProperties = {position: 'absolute', [corner[0] === 't' ? 'top' : 'bottom']: -6, [corner[1] === 'l' ? 'left' : 'right']: -6};
  return (
    <div style={{...pos, width: size, height: size, transform: tf, opacity}}>
      <svg width={size} height={size} style={{overflow: 'visible', transform: `rotate(${sway}deg)`, transformOrigin: '0 0'}}>
        <path d={lines.join(' ')} stroke="#e8dcd6" strokeWidth={1.4} fill="none" />
      </svg>
    </div>
  );
};
