import React from 'react';
import {Img, staticFile, useCurrentFrame} from 'remotion';
import {noise1} from '../effects/random';

export type PlayerDef = {
  id: 'patty' | 'tadas';
  w: number; // taille de l'image préparée (public/<id>.png)
  h: number;
  eyes: [number, number][]; // positions des yeux en px image
  eyeR: number;
  rimColor: string;
};

export const PATTY: PlayerDef = {id: 'patty', w: 819, h: 1024, eyes: [[396, 122], [426, 121]], eyeR: 9, rimColor: '#ff2a1e'};
// Tadas : image source 352x469 agrandie x2 (Lanczos) -> 704x938
export const TADAS: PlayerDef = {id: 'tadas', w: 704, h: 938, eyes: [[318, 146], [376, 144]], eyeR: 13, rimColor: '#ff6a28'};

/**
 * Joueur réel + calques VFX superposés, tous dans le repère de la photo :
 * ombre géante, aura, photo intacte, liseré de lumière, fissures, yeux rouges.
 * La photo elle-même n'est jamais déformée ni repeinte (seulement éclairée).
 */
export const PlayerRig: React.FC<{
  def: PlayerDef;
  x: number; // position écran du coin haut-gauche
  y: number;
  scale: number;
  reveal: number; // 0 silhouette noire -> 1 pleinement éclairé
  eyes: number;
  cracks: number;
  rim: number;
  aura: string;
  shadow?: number;
  seed?: number;
}> = ({def, x, y, scale, reveal, eyes, cracks, rim, aura, shadow = 0.6, seed = 1}) => {
  const f = useCurrentFrame();
  const flick = 0.82 + 0.18 * noise1(f / 3, seed); // lumière de feu vacillante
  const box: React.CSSProperties = {position: 'absolute', left: 0, top: 0, width: def.w, height: def.h};
  const auraPx = 10 / scale;
  const crackPulse = cracks * (0.7 + 0.3 * Math.sin(f / 9 + seed));
  return (
    <div style={{position: 'absolute', left: x, top: y, width: def.w, height: def.h, transform: `scale(${scale})`, transformOrigin: '0 0'}}>
      {/* ombre géante projetée dans la fumée, derrière le joueur */}
      <Img
        src={staticFile(`${def.id}_silhouette.png`)}
        style={{...box, transform: `translate(${def.w * 0.08}px, ${-def.h * 0.06}px) scale(1.32)`, transformOrigin: '50% 100%', filter: 'blur(16px)', opacity: shadow * reveal}}
      />
      <Img
        src={staticFile(`${def.id}.png`)}
        style={{
          ...box,
          filter: `brightness(${0.04 + 0.96 * reveal}) contrast(${1 + 0.12 * reveal}) drop-shadow(0 0 ${auraPx * 1.6}px ${aura}) drop-shadow(0 0 ${auraPx * 4}px ${aura})`,
        }}
      />
      {/* ombrage cinéma : bas du corps plus sombre */}
      <Img src={staticFile(`${def.id}_rim.png`)} style={{...box, opacity: rim * flick, mixBlendMode: 'screen'}} />
      <Img src={staticFile(`${def.id}_rim.png`)} style={{...box, opacity: rim * flick * 0.8, mixBlendMode: 'screen', filter: `blur(${6 / scale}px)`}} />
      {cracks > 0.01 ? (
        <>
          <Img src={staticFile(`${def.id}_cracks.png`)} style={{...box, opacity: crackPulse, mixBlendMode: 'screen'}} />
          <Img src={staticFile(`${def.id}_cracks.png`)} style={{...box, opacity: crackPulse * 0.7, mixBlendMode: 'screen', filter: `blur(${4 / scale}px)`}} />
        </>
      ) : null}
      {eyes > 0.01
        ? def.eyes.map(([ex, ey], i) => {
            const r = def.eyeR;
            const e = eyes * (0.85 + 0.15 * noise1(f / 4, seed + i));
            return (
              <React.Fragment key={i}>
                <div style={{position: 'absolute', left: ex - r * 6, top: ey - r * 6, width: r * 12, height: r * 12, borderRadius: '50%', background: `radial-gradient(circle, rgba(255,40,30,${0.55 * e}) 0%, rgba(215,25,32,${0.25 * e}) 30%, transparent 70%)`, mixBlendMode: 'screen'}} />
                <div style={{position: 'absolute', left: ex - r, top: ey - r * 0.6, width: r * 2, height: r * 1.2, borderRadius: '50%', background: `radial-gradient(ellipse, rgba(255,150,120,${e}) 0%, rgba(240,20,20,${e}) 40%, rgba(180,0,10,${0.6 * e}) 70%, transparent 100%)`, mixBlendMode: 'screen'}} />
                <div style={{position: 'absolute', left: ex - r * 9, top: ey - 1.2, width: r * 18, height: 2.4, background: `linear-gradient(90deg, transparent, rgba(255,80,60,${0.7 * e}), transparent)`, mixBlendMode: 'screen'}} />
              </React.Fragment>
            );
          })
        : null}
    </div>
  );
};
