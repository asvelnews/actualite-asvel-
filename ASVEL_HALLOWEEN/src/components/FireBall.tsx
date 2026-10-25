import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {ShaderCanvas} from '../effects/ShaderCanvas';
import {ballPx} from '../effects/cpuShaders';
import {Fire} from '../effects/Smoke';

/** Ballon 3D (lancer de rayons CPU) en rotation, enveloppé de flammes procédurales. */
export const FireBall: React.FC<{cx: number; cy: number; size: number; spinSpeed?: number; lava?: number; flames?: number; tilt?: number}> = ({
  cx,
  cy,
  size,
  spinSpeed = 2.4,
  lava = 0.4,
  flames = 1,
  tilt = 0.35,
}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const fw = size * 1.9, fh = size * 2.3;
  return (
    <div style={{position: 'absolute', left: cx - fw / 2, top: cy - fh + size * 0.75, width: fw, height: fh, WebkitMaskImage: 'radial-gradient(ellipse 50% 55% at 50% 60%, #000 65%, transparent 100%)'}}>
      {/* flammes derrière le ballon */}
      <Fire width={fw} heightPx={fh} height={0.75} intensity={1.35 * flames} scale={4.5} seed={5} res={0.3} opacity={flames} soft />
      <div style={{position: 'absolute', left: fw / 2 - size / 2, top: fh - size * 1.25, width: size, height: size, filter: `drop-shadow(0 0 ${size * 0.12}px rgba(255,100,27,.9))`}}>
        <ShaderCanvas width={size} height={size} scale={0.7} make={() => ballPx({t, spin: t * spinSpeed, tilt, lava, radius: 0.47})} />
      </div>
      {/* langues de feu devant le ballon */}
      <Fire width={fw} heightPx={fh} height={0.5} intensity={1.0 * flames} scale={7} seed={9} res={0.3} opacity={0.7 * flames} soft />
    </div>
  );
};
