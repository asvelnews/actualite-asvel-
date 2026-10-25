import React from 'react';
import {noise1} from '../effects/random';

/**
 * Personnage articulé en 3D légère (squelette hanches/genoux/chevilles/épaules/coudes)
 * animé par un cycle de marche paramétrique, projeté selon l'angle de vue, rendu en
 * silhouette à contre-jour avec liseré lumineux. Ce n'est pas une photo déplacée :
 * chaque membre suit une vraie cinématique de marche.
 */
export type Kind = 'myers' | 'freddy' | 'ghost' | 'art';

type V3 = [number, number, number]; // x latéral, y haut, z avant

const STYLE: Record<Kind, {cycle: number; thigh: number; knee: number; arm: number; elbow: number; bob: number; lean: number; height: number; width: number; jitter: number}> = {
  myers: {cycle: 1.35, thigh: 19, knee: 48, arm: 7, elbow: 10, bob: 4, lean: 0, height: 1.06, width: 1.12, jitter: 0},
  freddy: {cycle: 1.15, thigh: 22, knee: 55, arm: 16, elbow: 25, bob: 6, lean: 9, height: 0.98, width: 1, jitter: 0.15},
  ghost: {cycle: 1.2, thigh: 21, knee: 52, arm: 12, elbow: 20, bob: 5, lean: 4, height: 1.0, width: 1.05, jitter: 0},
  art: {cycle: 0.92, thigh: 25, knee: 62, arm: 34, elbow: 45, bob: 13, lean: -3, height: 1.0, width: 0.95, jitter: 1},
};

const rad = (d: number) => (d * Math.PI) / 180;

/** Pose 3D d'un personnage à l'instant t (s). stop: 0 marche -> 1 arrêté (pieds joints). */
const pose = (kind: Kind, t: number, stop: number, look: number) => {
  const S = STYLE[kind];
  const ph = (t / S.cycle) * Math.PI * 2;
  const go = 1 - stop;
  // démarche saccadée d'Art : le temps "accroche" par moments
  const jit = S.jitter ? 0.35 * Math.sin(ph * 2) * S.jitter : 0;
  const L = 95 * S.height, Sh = 92 * S.height, UA = 70 * S.height, FA = 66 * S.height, TOR = 150 * S.height;
  const hipY = L + Sh + 8 + S.bob * Math.cos(2 * ph) * go - 4 * stop;
  const leg = (side: number) => {
    const p = ph + (side > 0 ? 0 : Math.PI) + jit;
    const th = rad(S.thigh * Math.sin(p)) * go;
    const kn = rad(6 + S.knee * Math.pow(Math.max(0, Math.cos(p)), 2)) * go + rad(4) * stop;
    const hip: V3 = [side * 17 * S.width, hipY, 0];
    const knee: V3 = [hip[0], hip[1] - L * Math.cos(th), hip[2] + L * Math.sin(th)];
    const a2 = th - kn;
    const ankle: V3 = [hip[0] * 1.05, knee[1] - Sh * Math.cos(a2), knee[2] + Sh * Math.sin(a2)];
    const toe: V3 = [ankle[0], ankle[1] - 6, ankle[2] + 30];
    return {hip, knee, ankle, toe};
  };
  const lean = rad(S.lean);
  const neck: V3 = [0, hipY + TOR * Math.cos(lean), TOR * Math.sin(lean)];
  const arm = (side: number) => {
    const p = ph + (side > 0 ? Math.PI : 0) + jit;
    const a = rad(S.arm * Math.sin(p)) * go;
    const e = rad(S.elbow * (0.6 + 0.4 * Math.max(0, Math.sin(p)))) * go + rad(8);
    const sh: V3 = [side * 30 * S.width, neck[1] - 12, neck[2]];
    const el: V3 = [sh[0] * 1.08, sh[1] - UA * Math.cos(a), sh[2] + UA * Math.sin(a)];
    const hd: V3 = [el[0] * 1.02, el[1] - FA * Math.cos(a + e), el[2] + FA * Math.sin(a + e)];
    return {sh, el, hd};
  };
  const head: V3 = [0, neck[1] + 30, neck[2] + 6 + 4 * look];
  return {l: leg(-1), r: leg(1), la: arm(-1), ra: arm(1), neck, head, hipY, ph};
};

export const Walker: React.FC<{
  kind: Kind;
  t: number; // temps en secondes (avance du cycle)
  x: number; // position écran des pieds
  y: number;
  scale: number;
  view: number; // angle de vue (deg) : 0 = vu de dos, 90 = profil vers la droite, 180 = de face
  stop?: number;
  look?: number; // la tête se lève (regarder le bâtiment)
  rim?: string; // couleur du liseré (contre-jour)
  rimSide?: number; // -1 gauche, 1 droite, 0 = au-dessus (contre-jour arrière)
  light?: number; // éclairage frontal 0..1 (éclair)
  shadow?: number; // ombre portée au sol
  shadowDir?: number; // sens de l'ombre (1 vers le bas de l'écran)
}> = ({kind, t, x, y, scale, view, stop = 0, look = 0, rim = '#ff3a1f', rimSide = 0, light = 0, shadow = 0.5, shadowDir = 1}) => {
  const P = pose(kind, t, stop, look);
  const a = rad(view);
  const ca = Math.cos(a), sa = Math.sin(a);
  const front = ca < -0.2; // on voit le visage
  const proj = (p: V3): [number, number, number] => {
    const sx = p[0] * ca + p[2] * sa;
    const d = -p[0] * sa + p[2] * ca;
    const k = 1400 / (1400 + d);
    return [sx * k, -p[1] * k, d];
  };
  const dk = '#070506';
  const limbs: {a: V3; b: V3; w: number; c?: string}[] = [];
  const thick = kind === 'myers' ? 1.25 : kind === 'ghost' ? 1.3 : 1;
  for (const s of [P.l, P.r]) {
    limbs.push({a: s.hip, b: s.knee, w: 40 * thick}, {a: s.knee, b: s.ankle, w: 30 * thick}, {a: s.ankle, b: s.toe, w: 20});
  }
  for (const s of [P.la, P.ra]) {
    const sl = kind === 'ghost' ? 1.6 : kind === 'art' ? 1.35 : 1;
    limbs.push({a: s.sh, b: s.el, w: 30 * thick * sl}, {a: s.el, b: s.hd, w: 25 * thick * sl});
  }
  // ordre de dessin : du plus loin au plus proche
  const segs = limbs
    .map((L) => {
      const A = proj(L.a), B = proj(L.b);
      return {A, B, w: L.w, d: (A[2] + B[2]) / 2};
    })
    .sort((p, q) => q.d - p.d);
  const lh = proj(P.l.hip), rh = proj(P.r.hip), ls = proj(P.la.sh), rs = proj(P.ra.sh), nk = proj(P.neck), hd = proj(P.head);
  const torso = `M${ls[0]},${ls[1]} L${rs[0]},${rs[1]} L${rh[0] + (rh[0] - lh[0]) * 0.15},${rh[1]} L${lh[0] - (rh[0] - lh[0]) * 0.15},${lh[1]} Z`;
  const torsoW = Math.max(30, Math.abs(rs[0] - ls[0]));
  // robe de Ghostface : l'ourlet suit les chevilles, avec un flottement
  let robe = '';
  if (kind === 'ghost') {
    const la = proj(P.l.ankle), ra = proj(P.r.ankle);
    const fl = noise1(t * 3, 4) * 10;
    const hemL = Math.min(la[0], ra[0]) - 34 - Math.abs(fl), hemR = Math.max(la[0], ra[0]) + 34 + fl;
    const hy = Math.max(la[1], ra[1]) - 30;
    robe = `M${ls[0] - 8},${ls[1]} L${rs[0] + 8},${rs[1]} Q${rh[0] + 30},${(rh[1] + hy) / 2} ${hemR},${hy + fl * 0.3} Q${(hemL + hemR) / 2},${hy + 18 + fl} ${hemL},${hy - fl * 0.3} Q${lh[0] - 30},${(lh[1] + hy) / 2} ${ls[0] - 8},${ls[1]} Z`;
  }
  const headR = 27;
  const rimDx = rimSide * 3, rimDy = rimSide === 0 ? -3 : -1;
  const body = (fill: string, stroke: string) => (
    <>
      {segs.map((s, i) => (
        <line key={i} x1={s.A[0]} y1={s.A[1]} x2={s.B[0]} y2={s.B[1]} stroke={stroke} strokeWidth={s.w} strokeLinecap="round" />
      ))}
      <path d={torso} fill={fill} stroke={stroke} strokeWidth={torsoW * 0.35} strokeLinejoin="round" />
      <line x1={(lh[0] + rh[0]) / 2} y1={(lh[1] + rh[1]) / 2 - 10} x2={nk[0]} y2={nk[1] + 28} stroke={stroke} strokeWidth={62 * thick} strokeLinecap="round" />
      {robe ? <path d={robe} fill={fill} stroke={stroke} strokeWidth={6} /> : null}
      <line x1={nk[0]} y1={nk[1]} x2={hd[0]} y2={hd[1]} stroke={stroke} strokeWidth={22} strokeLinecap="round" />
      <circle cx={hd[0]} cy={hd[1]} r={headR} fill={fill} />
      {kind === 'ghost' ? <path d={`M${hd[0] - 40},${hd[1] + 30} Q${hd[0] - 44},${hd[1] - 46} ${hd[0]},${hd[1] - 50} Q${hd[0] + 44},${hd[1] - 46} ${hd[0] + 40},${hd[1] + 30} Z`} fill={fill} /> : null}
      {kind === 'freddy' ? (
        <>
          <ellipse cx={hd[0]} cy={hd[1] - 20} rx={46} ry={9} fill={fill} />
          <path d={`M${hd[0] - 25},${hd[1] - 22} L${hd[0] - 21},${hd[1] - 52} Q${hd[0]},${hd[1] - 60} ${hd[0] + 21},${hd[1] - 52} L${hd[0] + 25},${hd[1] - 22} Z`} fill={fill} />
        </>
      ) : null}
      {kind === 'art' ? (
        <>
          <rect x={hd[0] - 10} y={hd[1] - 46} width={20} height={18} rx={3} fill={fill} />
          <ellipse cx={hd[0]} cy={hd[1] - 28} rx={17} ry={4} fill={fill} />
          {Array.from({length: 9}).map((_, i) => {
            const an = (i / 9) * Math.PI * 2;
            return <circle key={i} cx={nk[0] + Math.cos(an) * 30} cy={nk[1] + 8 + Math.sin(an) * 10} r={11} fill={fill} />;
          })}
        </>
      ) : null}
    </>
  );
  // armes / détails clairs
  const rhd = proj(P.ra.hd), rel = proj(P.ra.el);
  const dirx = rhd[0] - rel[0], diry = rhd[1] - rel[1];
  const dn = Math.hypot(dirx, diry) || 1;
  const ux = dirx / dn, uy = diry / dn;
  const metal = `rgba(220,215,210,${0.55 + 0.45 * light})`;
  const faceVis = front ? 1 : 0;
  // ombre portée au sol
  const shadowG = shadow > 0 ? (
    <g transform={`scale(1, ${-0.22 * shadowDir}) skewX(${-25 * shadowDir})`} opacity={shadow} style={{filter: 'blur(6px)'}}>
      {body('#000', '#000')}
    </g>
  ) : null;
  return (
    <svg
      style={{position: 'absolute', left: x - 200 * scale, top: y - 520 * scale, overflow: 'visible'}}
      width={400 * scale}
      height={560 * scale}
      viewBox="-200 -520 400 560"
    >
      {shadowG}
      <g transform={`translate(${rimDx},${rimDy})`} style={{filter: 'blur(1.2px)'}}>
        {body(rim, rim)}
      </g>
      {body(dk, dk)}
      {/* éclairage frontal (éclair) : la silhouette se dévoile légèrement */}
      {light > 0.02 ? <g opacity={light * 0.35}>{body('#3a3236', '#3a3236')}</g> : null}
      {kind === 'freddy'
        ? [0, 1, 2, 3].map((k) => (
            <line key={k} x1={rhd[0] + k * 3 - 4} y1={rhd[1]} x2={rhd[0] + ux * 52 + (k - 1.5) * 9} y2={rhd[1] + uy * 52 + (k - 1.5) * 2} stroke={metal} strokeWidth={2.4} strokeLinecap="round" />
          ))
        : null}
      {kind === 'myers' || kind === 'ghost' ? (
        <line x1={rhd[0]} y1={rhd[1]} x2={rhd[0] + ux * 46} y2={rhd[1] + uy * 46} stroke={metal} strokeWidth={5} strokeLinecap="round" />
      ) : null}
      {faceVis ? (
        <g>
          {kind === 'myers' ? <ellipse cx={hd[0]} cy={hd[1] + 2} rx={18} ry={24} fill={`rgba(216,208,192,${0.55 + 0.4 * light})`} /> : null}
          {kind === 'ghost' ? (
            <g>
              <ellipse cx={hd[0]} cy={hd[1] + 2} rx={17} ry={26} fill={`rgba(236,232,224,${0.75 + 0.25 * light})`} />
              <ellipse cx={hd[0] - 7} cy={hd[1] - 6} rx={4} ry={8} fill="#000" transform={`rotate(20 ${hd[0] - 7} ${hd[1] - 6})`} />
              <ellipse cx={hd[0] + 7} cy={hd[1] - 6} rx={4} ry={8} fill="#000" transform={`rotate(-20 ${hd[0] + 7} ${hd[1] - 6})`} />
              <ellipse cx={hd[0]} cy={hd[1] + 14} rx={4} ry={9} fill="#000" />
            </g>
          ) : null}
          {kind === 'art' ? (
            <g>
              <ellipse cx={hd[0]} cy={hd[1] + 2} rx={19} ry={24} fill={`rgba(240,238,234,${0.7 + 0.3 * light})`} />
              <circle cx={hd[0] - 7} cy={hd[1] - 4} r={4} fill="#000" />
              <circle cx={hd[0] + 7} cy={hd[1] - 4} r={4} fill="#000" />
              <path d={`M${hd[0] - 9},${hd[1] + 12} Q${hd[0]},${hd[1] + 20} ${hd[0] + 9},${hd[1] + 12}`} stroke="#000" strokeWidth={3} fill="none" />
            </g>
          ) : null}
          {kind === 'freddy' ? <ellipse cx={hd[0]} cy={hd[1] + 6} rx={15} ry={18} fill={`rgba(120,40,30,${0.35 + 0.5 * light})`} /> : null}
        </g>
      ) : null}
    </svg>
  );
};

/** Instant (s) où un pied touche le sol, pour caler les bruits de pas. */
export const stepTimes = (kind: Kind, t0: number, t1: number) => {
  const c = STYLE[kind].cycle;
  const out: number[] = [];
  for (let k = Math.ceil(t0 / (c / 2)); k * (c / 2) < t1; k++) out.push(k * (c / 2) + c * 0.25);
  return out;
};
export const CYCLE = Object.fromEntries(Object.entries(STYLE).map(([k, v]) => [k, v.cycle])) as Record<Kind, number>;
