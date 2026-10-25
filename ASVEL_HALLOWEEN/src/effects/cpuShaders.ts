/**
 * Moteur de shaders CPU (portage des shaders GLSL d'origine) : bruit simplex 2D,
 * fbm, fumée à déformation de domaine, flammes, ciel, ballon 3D par lancer de rayons.
 * Rendu en basse résolution dans un ImageData, sans WebGL : fonctionne avec la
 * composition logicielle de Chromium (5 à 8x plus rapide que SwiftShader ici).
 */

// --- Bruit simplex 2D (Stefan Gustavson, domaine public), table de permutation fixe
const perm = new Uint8Array(512);
const grad = new Float32Array([1, 1, -1, 1, 1, -1, -1, -1, 1, 0, -1, 0, 0, 1, 0, -1]);
{
  const p = new Uint8Array(256);
  for (let i = 0; i < 256; i++) p[i] = i;
  let s = 1337;
  for (let i = 255; i > 0; i--) {
    s = (s * 16807) % 2147483647;
    const j = s % (i + 1);
    const t = p[i];
    p[i] = p[j];
    p[j] = t;
  }
  for (let i = 0; i < 512; i++) perm[i] = p[i & 255];
}
const F2 = 0.5 * (Math.sqrt(3) - 1);
const G2 = (3 - Math.sqrt(3)) / 6;

export const snoise = (xin: number, yin: number): number => {
  const s = (xin + yin) * F2;
  const i = Math.floor(xin + s);
  const j = Math.floor(yin + s);
  const t = (i + j) * G2;
  const x0 = xin - (i - t);
  const y0 = yin - (j - t);
  const i1 = x0 > y0 ? 1 : 0;
  const j1 = 1 - i1;
  const x1 = x0 - i1 + G2, y1 = y0 - j1 + G2;
  const x2 = x0 - 1 + 2 * G2, y2 = y0 - 1 + 2 * G2;
  const ii = i & 255, jj = j & 255;
  let n = 0;
  let t0 = 0.5 - x0 * x0 - y0 * y0;
  if (t0 > 0) {
    const g = (perm[ii + perm[jj]] & 7) * 2;
    t0 *= t0;
    n += t0 * t0 * (grad[g] * x0 + grad[g + 1] * y0);
  }
  let t1 = 0.5 - x1 * x1 - y1 * y1;
  if (t1 > 0) {
    const g = (perm[ii + i1 + perm[jj + j1]] & 7) * 2;
    t1 *= t1;
    n += t1 * t1 * (grad[g] * x1 + grad[g + 1] * y1);
  }
  let t2 = 0.5 - x2 * x2 - y2 * y2;
  if (t2 > 0) {
    const g = (perm[ii + 1 + perm[jj + 1]] & 7) * 2;
    t2 *= t2;
    n += t2 * t2 * (grad[g] * x2 + grad[g + 1] * y2);
  }
  return 70 * n;
};

// fbm avec rotation inter-octaves (identique au GLSL : mat2(1.6,1.2,-1.2,1.6))
export const fbmN = (x: number, y: number, oct: number): number => {
  let f = 0, a = 0.5;
  for (let i = 0; i < oct; i++) {
    f += a * snoise(x, y);
    const nx = 1.6 * x - 1.2 * y;
    y = 1.2 * x + 1.6 * y;
    x = nx;
    a *= 0.5;
  }
  return f;
};

const sstep = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
const clamp01 = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);

export type Px = (u: number, v: number, asp: number, out: Float32Array) => void; // out = r,g,b,a (prémultiplié, 0..1)

export type SmokeU = {
  t: number;
  color: number[];
  light: number[];
  lightDir: number[];
  density: number;
  scale: number;
  flow: number[];
  seed: number;
  turb: number;
  band: number[];
  hole: number[];
  opacity: number;
};

/** Fumée : double déformation de domaine, bouffées, éclairage directionnel, zones, trou. */
export const smokePx = (U: SmokeU): Px => {
  const t = U.t;
  const gust = t + 0.45 * Math.sin(t * 0.6 + U.seed) + 0.25 * Math.sin(t * 1.7 + U.seed * 3);
  const dx = U.flow[0] * gust, dy = U.flow[1] * gust;
  const sd = U.seed * 17.3;
  const [cr, cg, cb] = U.color;
  const [lr, lg, lb] = U.light;
  const ldx = U.lightDir[0] * 0.45, ldy = U.lightDir[1] * 0.45;
  const [b0, b1, bs, bm] = U.band;
  const [hx, hy, hr] = U.hole;
  return (u, v, asp, out) => {
    let band = 1;
    if (bm < 0.5) band = sstep(b0 - bs, b0, v) * (1 - sstep(b1, b1 + bs, v));
    else if (bm < 1.5) band = 1 - sstep(b0, b1, v);
    else if (bm < 2.5) band = sstep(b0, b1, v);
    if (band <= 0.001) {
      out[0] = out[1] = out[2] = out[3] = 0;
      return;
    }
    const px = u * asp * U.scale + sd, py = v * U.scale + sd;
    const qx = fbmN(px * 0.7 + dx * 0.5, py * 0.7 + dy * 0.5 + t * 0.04, 3);
    const qy = fbmN(px * 0.7 + dx * 0.5 + 5.2 - t * 0.03, py * 0.7 + dy * 0.5 + 1.3 - t * 0.03, 3);
    const wx = px + U.turb * qx + dx, wy = py + U.turb * qy + dy;
    const big = fbmN(wx, wy, 4);
    const fine = fbmN(wx * 2.6 + t * 0.15, wy * 2.6 - t * 0.1, 2);
    const f = big * 0.78 + fine * 0.22;
    const f2 = fbmN(wx + ldx, wy + ldy, 2);
    let d = sstep(-0.45, 0.75, f);
    d = d * d * (0.55 + 0.45 * sstep(-0.6, 0.6, qx)) * U.density * band;
    if (hr > 0) {
      const ex = (u - hx) * asp, ey = v - hy;
      const r = Math.sqrt(ex * ex + ey * ey) + 0.12 * fbmN(ex * 3 + t * 0.3, ey * 3 + t * 0.3, 2);
      d *= sstep(hr * 0.55, hr, r);
    }
    d = clamp01(d);
    const lit = sstep(-0.25, 0.45, (f - f2) * 1.4 + 0.15) * 0.85;
    const glow = 0.18 * (1 - d) * (1 - d) * lit;
    const a = d * U.opacity;
    out[0] = (cr + (lr - cr) * lit + lr * glow) * a;
    out[1] = (cg + (lg - cg) * lit + lg * glow) * a;
    out[2] = (cb + (lb - cb) * lit + lb * glow) * a;
    out[3] = a;
  };
};

export type FireU = {t: number; height: number; intensity: number; seed: number; scale: number; dir: number[]; opacity: number; soft?: boolean};

/** Flammes : fbm étiré qui défile, hauteur modulée, rampe corps noir rouge->orange->jaune. */
export const firePx = (U: FireU): Px => {
  const {t} = U;
  const [ddx, ddy] = U.dir;
  return (u, v, asp, out) => {
    const cu = u - 0.5, cv = v - 0.5;
    const y = cu * ddx + cv * ddy + 0.5;
    if (y > U.height * 1.6 + 0.05) {
      out[0] = out[1] = out[2] = out[3] = 0;
      return;
    }
    const x = (cu * ddy - cv * ddx) * asp;
    const px = x * U.scale + U.seed * 11, py = y * U.scale * 0.55 - t * 1.6 + U.seed * 11;
    const n = fbmN(px + fbmN(px * 1.3 + t * 0.4, py * 1.3 + t * 0.4, 2) * 0.6, py, 4);
    const n2 = fbmN(x * U.scale * 2.3 + U.seed, t * 0.9, 2);
    const h = U.height * (0.65 + 0.45 * n2);
    let fl = clamp01((h - y) / Math.max(h, 0.001) + n * 0.55);
    fl = Math.pow(fl, 2.2) * U.intensity;
    const c = clamp01(fl);
    // rampe : noir -> #D71920 -> #FF641B -> jaune pâle
    let r = 0.84 * sstep(0, 0.35, c), g = 0.1 * sstep(0, 0.35, c), b = 0.12 * sstep(0, 0.35, c);
    const k1 = sstep(0.3, 0.7, c);
    r += (1 - r) * k1; g += (0.39 - g) * k1; b += (0.1 - b) * k1;
    const k2 = sstep(0.75, 1, c);
    r += (1 - r) * k2; g += (0.85 - g) * k2; b += (0.55 - b) * k2;
    let a = clamp01(fl * 1.4) * U.opacity;
    // flammes contenues dans un cadre (ballon) : bords adoucis, pas de base rectangulaire
    if (U.soft) a *= sstep(0, 0.2, u) * sstep(0, 0.2, 1 - u) * sstep(0, 0.12, v);
    out[0] = r * a; out[1] = g * a; out[2] = b * a; out[3] = a;
  };
};

export type SkyU = {t: number; red: number; flash: number};

/** Ciel : nuit bleue -> rouge sang, deux couches de nuages en parallaxe, éclairs. */
export const skyPx = (U: SkyU): Px => {
  const {t, red, flash} = U;
  return (u, v, asp, out) => {
    const g = v;
    const gp = Math.pow(g, 0.7);
    // nuit (photo) et rouge sang
    const nr = 0.04 + (0.01 - 0.04) * g, ng = 0.12 + (0.02 - 0.12) * g, nb = 0.35 + (0.08 - 0.35) * g;
    const rr = 0.32 + (0.02 - 0.32) * gp, rg = 0.015 + (0 - 0.015) * gp, rb = 0.02 + (0.005 - 0.02) * gp;
    let r = nr + (rr - nr) * red, gg = ng + (rg - ng) * red, b = nb + (rb - nb) * red;
    const px = u * asp, py = v;
    const c1 = fbmN(px * 1.6 + t * 0.035 + fbmN(px * 2 + t * 0.05, py * 2 + t * 0.05, 2) * 0.6, py * 3, 4);
    const c2 = fbmN(px * 3 + t * 0.07 + 5, py * 5 + 8, 3);
    let cl = sstep(-0.1, 0.6, c1) * 0.85 + sstep(0, 0.7, c2) * 0.4;
    cl *= sstep(0.15, 0.55, v) * 0.9 + 0.1;
    cl = clamp01(cl);
    const k = 0.15 * sstep(0, 0.6, c2);
    const cdr = 0.02 + 0.05 * red, cdg = 0.03 - 0.03 * red, cdb = 0.07 - 0.06 * red;
    const clr = 0.15 + 0.35 * red, clg = 0.2 - 0.13 * red, clb = 0.35 - 0.32 * red;
    const ccr = cdr + (clr - cdr) * k, ccg = cdg + (clg - cdg) * k, ccb = cdb + (clb - cdb) * k;
    r += (ccr - r) * cl * 0.9; gg += (ccg - gg) * cl * 0.9; b += (ccb - b) * cl * 0.9;
    const fl = flash * (0.25 + 0.75 * cl) * 0.8;
    out[0] = r + 0.9 * fl; out[1] = gg + 0.85 * fl; out[2] = b + fl; out[3] = 1;
  };
};

export type BallU = {t: number; spin: number; tilt: number; lava: number; radius: number};

/** Ballon de basket 3D : intersection rayon/sphère, rotation, coutures, grain, veines de lave. */
export const ballPx = (U: BallU): Px => {
  const cs = Math.cos(U.spin), ss = Math.sin(U.spin), ct = Math.cos(U.tilt), st = Math.sin(U.tilt);
  const R = U.radius;
  const Lx = -0.5, Ly = 0.6, Lz = 0.65, Ln = Math.hypot(Lx, Ly, Lz);
  return (u, v, asp, out) => {
    const x = (u - 0.5) * asp, y = v - 0.5;
    const d2 = x * x + y * y;
    const rr = Math.sqrt(d2);
    const inside = 1 - sstep(R - 0.004, R + 0.004, rr);
    if (inside <= 0) {
      out[0] = out[1] = out[2] = out[3] = 0;
      return;
    }
    const nz = Math.sqrt(Math.max(R * R - d2, 0));
    const nx = x / R, ny = y / R, nzz = nz / R;
    // rotation Y puis X (repère local du ballon)
    let px = cs * nx + ss * nzz, pz = -ss * nx + cs * nzz;
    let py = ct * ny - st * pz;
    pz = st * ny + ct * pz;
    const curve = Math.abs(Math.abs(pz) - 0.62 * Math.sqrt(Math.max(1 - py * py, 0)));
    const s = Math.min(Math.abs(py), Math.abs(px), curve);
    const seam = 1 - sstep(0.011, 0.022, s);
    const peb = snoise(px * 160 + pz * 90, py * 160) * 0.5 + snoise(py * 160, pz * 160) * 0.5;
    const tex = 0.88 + 0.12 * peb;
    let r = 0.78 * tex, g = 0.28 * tex, b = 0.07 * tex;
    r += (0.04 - r) * seam; g += (0.02 - g) * seam; b += (0.02 - b) * seam;
    const diff = Math.max((nx * Lx + ny * Ly + nzz * Lz) / Ln, 0);
    // reflet spéculaire (vue de face)
    const dotNL = (nx * Lx + ny * Ly + nzz * Lz) / Ln;
    const rz = 2 * dotNL * nzz - Lz / Ln;
    const spec = Math.pow(Math.max(rz, 0), 24) * 0.25;
    const rim = Math.pow(1 - nzz, 2.5);
    const lv = fbmN(px * 3 + U.t * 0.3 + pz * 2, py * 3 + pz * 2, 3);
    const vein = (1 - sstep(0, 0.06, Math.abs(lv))) * U.lava;
    r = r * (0.18 + 0.9 * diff) + spec + rim * 0.9 + vein * 1.4 + vein * vein;
    g = g * (0.18 + 0.9 * diff) + spec + rim * 0.135 + vein * 0.63 + vein * vein * 0.8;
    b = b * (0.18 + 0.9 * diff) + spec + rim * 0.045 + vein * 0.14 + vein * vein * 0.4;
    out[0] = r * inside; out[1] = g * inside; out[2] = b * inside; out[3] = inside;
  };
};
