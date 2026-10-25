import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Walker} from '../components/Walker';

/** Planche de test du rig de marche (profil, 3/4 face, dos). */
export const WalkTest: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / 60;
  const kinds = ['myers', 'freddy', 'ghost', 'art'] as const;
  return (
    <AbsoluteFill style={{background: 'linear-gradient(#2a0608,#080608)'}}>
      {kinds.map((k, i) => (
        <React.Fragment key={k}>
          <Walker kind={k} t={t} x={150 + i * 260} y={560} scale={0.75} view={90} rimSide={-1} />
          <Walker kind={k} t={t} x={150 + i * 260} y={1160} scale={0.75} view={150} rimSide={1} />
          <Walker kind={k} t={t} x={150 + i * 260} y={1760} scale={0.75} view={0} rim="#ff8a3a" />
        </React.Fragment>
      ))}
    </AbsoluteFill>
  );
};
