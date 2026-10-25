import React, {useLayoutEffect, useRef} from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import type {Px} from './cpuShaders';

const buf = new Float32Array(4);

/**
 * Couche "shader" calculée sur CPU en basse résolution puis agrandie par le navigateur
 * (lissage bilinéaire = parfait pour la fumée). `make(t)` reçoit le temps en secondes
 * dérivé de la frame : chaque frame est déterministe.
 */
export const ShaderCanvas: React.FC<{
  make: (t: number) => Px;
  scale?: number;
  timeOffset?: number;
  style?: React.CSSProperties;
  blend?: React.CSSProperties['mixBlendMode'];
  width?: number;
  height?: number;
  opaque?: boolean;
}> = ({make, scale = 0.25, timeOffset = 0, style, blend, width, height, opaque}) => {
  const frame = useCurrentFrame();
  const {fps, width: W, height: H} = useVideoConfig();
  const w = width ?? W;
  const h = height ?? H;
  const cw = Math.max(2, Math.round(w * scale));
  const ch = Math.max(2, Math.round(h * scale));
  const ref = useRef<HTMLCanvasElement>(null);

  useLayoutEffect(() => {
    const ctx = ref.current!.getContext('2d')!;
    const img = ctx.createImageData(cw, ch);
    const d = img.data;
    const px = make(frame / fps + timeOffset);
    const asp = cw / ch;
    for (let y = 0; y < ch; y++) {
      const v = 1 - (y + 0.5) / ch; // y vers le haut comme en GLSL
      for (let x = 0; x < cw; x++) {
        px((x + 0.5) / cw, v, asp, buf);
        const i = (y * cw + x) * 4;
        const a = buf[3];
        if (a <= 0.002) {
          d[i + 3] = 0;
          continue;
        }
        // ImageData attend des couleurs non prémultipliées
        const inv = opaque ? 1 : 1 / a;
        d[i] = Math.min(255, buf[0] * inv * 255);
        d[i + 1] = Math.min(255, buf[1] * inv * 255);
        d[i + 2] = Math.min(255, buf[2] * inv * 255);
        d[i + 3] = Math.min(255, a * 255);
      }
    }
    ctx.putImageData(img, 0, 0);
  });

  return (
    <canvas
      ref={ref}
      width={cw}
      height={ch}
      style={{position: 'absolute', left: 0, top: 0, width: w, height: h, mixBlendMode: blend, ...style}}
    />
  );
};
