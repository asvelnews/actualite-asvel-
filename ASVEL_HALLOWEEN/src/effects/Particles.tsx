import React, {useLayoutEffect, useRef} from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {hash} from './random';

type Kind = 'embers' | 'ash' | 'sparks' | 'rain' | 'dust';

/**
 * Particules sans état : la position de chaque particule est une fonction pure du temps,
 * avec un cycle de vie qui boucle. Profondeur simulée (taille, vitesse, flou) par particule.
 */
export const Particles: React.FC<{
  kind: Kind;
  count: number;
  seed?: number;
  opacity?: number;
  area?: [number, number, number, number]; // x,y,w,h d'émission (relatif 0..1)
  speed?: number;
  wind?: number;
  burstAt?: number; // frame d'une explosion radiale (étincelles)
  burstCenter?: [number, number];
}> = ({kind, count, seed = 1, opacity = 1, area = [0, 0, 1, 1], speed = 1, wind = 0, burstAt, burstCenter = [0.5, 0.5]}) => {
  const frame = useCurrentFrame();
  const {width: W, height: H, fps} = useVideoConfig();
  const ref = useRef<HTMLCanvasElement>(null);
  useLayoutEffect(() => {
    const ctx = ref.current!.getContext('2d')!;
    ctx.clearRect(0, 0, W, H);
    const t = frame / fps;
    ctx.globalCompositeOperation = kind === 'ash' || kind === 'rain' ? 'source-over' : 'lighter';
    for (let i = 0; i < count; i++) {
      const h1 = hash(i * 3.1 + seed), h2 = hash(i * 7.7 + seed * 2), h3 = hash(i * 1.3 + seed * 5), h4 = hash(i * 9.9 + seed * 3);
      const depth = 0.3 + 0.7 * h3; // 1 = proche
      if (kind === 'embers' || kind === 'dust') {
        const life = 3 + 4 * h2;
        const ph = ((t * speed * (0.6 + depth * 0.6)) / life + h1) % 1;
        const x0 = (area[0] + area[2] * h4) * W;
        const y0 = (area[1] + area[3]) * H;
        const rise = ph * H * (kind === 'dust' ? 0.25 : 0.75) * depth;
        const x = x0 + Math.sin(t * (0.8 + h2) + i) * 40 * depth + wind * ph * 300;
        const y = y0 - rise;
        const flick = 0.55 + 0.45 * Math.sin(t * (8 + 10 * h1) + i * 3);
        const fade = Math.sin(Math.PI * ph);
        const r = (kind === 'dust' ? 1.5 : 1.2 + 3.2 * depth) * (0.7 + 0.3 * flick);
        const a = fade * flick * opacity * (0.35 + 0.65 * depth);
        const g = ctx.createRadialGradient(x, y, 0, x, y, r * 4);
        const col = kind === 'dust' ? '255,210,170' : h2 > 0.6 ? '255,200,90' : '255,100,27';
        g.addColorStop(0, `rgba(255,245,210,${a})`);
        g.addColorStop(0.25, `rgba(${col},${a * 0.8})`);
        g.addColorStop(1, `rgba(${col},0)`);
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(x, y, r * 4, 0, Math.PI * 2);
        ctx.fill();
      } else if (kind === 'ash') {
        const life = 6 + 6 * h2;
        const ph = ((t * speed) / life + h1) % 1;
        const x = (area[0] + area[2] * h4) * W + Math.sin(t * 0.7 + i) * 60 + wind * ph * 400;
        const y = (area[1] + area[3] * ph) * H;
        const s = 1 + 3 * depth;
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(t * (1 + h2 * 2) + i);
        ctx.fillStyle = `rgba(190,180,175,${opacity * 0.5 * Math.sin(Math.PI * ph) * depth})`;
        ctx.fillRect(-s, -s * 0.4, s * 2, s * 0.8);
        ctx.restore();
      } else if (kind === 'rain') {
        const ph = ((t * speed * (1.4 + depth)) + h1) % 1;
        const x = h4 * W * 1.2 - 0.1 * W + ph * 120 * (1 + wind);
        const y = ph * (H + 200) - 100;
        const len = 18 + 40 * depth;
        ctx.strokeStyle = `rgba(220,200,210,${opacity * 0.22 * depth})`;
        ctx.lineWidth = 0.6 + depth;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x - len * 0.18, y - len);
        ctx.stroke();
      } else if (kind === 'sparks') {
        let x: number, y: number, vx: number, vy: number, a: number;
        if (burstAt !== undefined) {
          const tt = (frame - burstAt) / fps;
          if (tt < 0 || tt > 2.2) continue;
          const ang = h1 * Math.PI * 2;
          const v = (500 + 1400 * h2) * depth;
          vx = Math.cos(ang) * v;
          vy = Math.sin(ang) * v - 200;
          const drag = (1 - Math.exp(-2.2 * tt)) / 2.2;
          x = burstCenter[0] * W + vx * drag;
          y = burstCenter[1] * H + vy * drag + 260 * tt * tt;
          a = Math.max(0, 1 - tt / (0.8 + 1.4 * h3)) * opacity;
          vy = vy * Math.exp(-2.2 * tt) + 520 * tt;
          vx = vx * Math.exp(-2.2 * tt);
        } else {
          const life = 0.8 + 1.2 * h2;
          const ph = ((t * speed) / life + h1) % 1;
          const ang = -Math.PI / 2 + (h4 - 0.5) * 1.4;
          const v = (300 + 700 * h3);
          vx = Math.cos(ang) * v + wind * 200;
          vy = Math.sin(ang) * v;
          const tt = ph * life;
          x = (area[0] + area[2] * hash(i * 4.4 + seed)) * W + vx * tt;
          y = (area[1] + area[3]) * H + vy * tt + 400 * tt * tt;
          vy += 800 * tt;
          a = (1 - ph) * opacity;
        }
        const sp = Math.hypot(vx, vy) || 1;
        const len = Math.min(40, sp * 0.03) * depth + 2;
        ctx.strokeStyle = `rgba(255,${170 + 80 * h2},${80 + 100 * h3},${a})`;
        ctx.lineWidth = 1 + 1.6 * depth;
        ctx.shadowColor = 'rgba(255,100,27,0.9)';
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x - (vx / sp) * len, y - (vy / sp) * len);
        ctx.stroke();
        ctx.shadowBlur = 0;
      }
    }
  });
  return <canvas ref={ref} width={W} height={H} style={{position: 'absolute', inset: 0}} />;
};
