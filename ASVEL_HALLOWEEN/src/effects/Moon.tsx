import React from 'react';
import {useCurrentFrame} from 'remotion';

/**
 * Lune orange : disque net avec texture de cratères (SVG feTurbulence, déterministe),
 * assombrissement du limbe, halo à deux niveaux. Placée derrière le bâtiment.
 */
export const Moon: React.FC<{x: number; y: number; r: number; amt: number}> = ({x, y, r, amt}) => {
  const frame = useCurrentFrame();
  if (amt <= 0.001) return null;
  const pulse = 1 + 0.03 * Math.sin(frame / 25);
  return (
    <div style={{position: 'absolute', left: x - r * 4, top: y - r * 4, width: r * 8, height: r * 8, opacity: amt, pointerEvents: 'none'}}>
      <div style={{position: 'absolute', inset: 0, borderRadius: '50%', background: `radial-gradient(circle, rgba(255,110,30,${0.5 * pulse}) 12%, rgba(215,40,20,.22) 22%, rgba(120,10,8,.08) 38%, transparent 55%)`, mixBlendMode: 'screen'}} />
      <svg width={r * 2} height={r * 2} style={{position: 'absolute', left: r * 3, top: r * 3}}>
        <defs>
          <filter id="crat" x="0" y="0" width="100%" height="100%">
            <feTurbulence type="fractalNoise" baseFrequency="0.028" numOctaves="4" seed="7" result="n" />
            <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 .62  0 0 0 0 .3  2.6 0 0 0 -1.0" result="c" />
            <feComposite in="c" in2="SourceGraphic" operator="in" />
          </filter>
          <radialGradient id="limb" cx="42%" cy="40%" r="62%">
            <stop offset="0%" stopColor="#ffc06a" />
            <stop offset="60%" stopColor="#ff8a2a" />
            <stop offset="100%" stopColor="#b8320e" />
          </radialGradient>
        </defs>
        <circle cx={r} cy={r} r={r} fill="url(#limb)" />
        <circle cx={r} cy={r} r={r} fill="#7a2408" filter="url(#crat)" opacity={0.7} style={{mixBlendMode: 'multiply'}} />
      </svg>
    </div>
  );
};
