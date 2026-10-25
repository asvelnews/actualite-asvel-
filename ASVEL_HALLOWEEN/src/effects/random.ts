// Générateurs déterministes : aucune dépendance à Math.random, chaque frame est rejouable.
export const hash = (n: number) => {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453123;
  return x - Math.floor(x);
};
export const rng = (seed: number) => {
  let s = Math.floor(seed * 9973) % 2147483647 || 1;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
};
/** Bruit 1D lisse pour secousses et vacillements. */
export const noise1 = (t: number, seed = 0) => {
  const i = Math.floor(t);
  const f = t - i;
  const u = f * f * (3 - 2 * f);
  return (hash(i + seed * 101) * (1 - u) + hash(i + 1 + seed * 101) * u) * 2 - 1;
};
/** Secousse de caméra amortie après un impact (px). */
export const shake = (frame: number, at: number, dur: number, amp: number, seed = 0) => {
  const t = frame - at;
  if (t < 0 || t > dur) return {x: 0, y: 0, r: 0};
  const k = Math.pow(1 - t / dur, 2) * amp;
  return {x: noise1(t * 0.9, seed) * k, y: noise1(t * 0.9, seed + 7) * k, r: noise1(t * 0.5, seed + 13) * k * 0.0012};
};
export const sumShake = (frame: number, hits: number[], dur: number, amp: number) =>
  hits.reduce(
    (acc, h, i) => {
      const s = shake(frame, h, dur, amp, i + 1);
      return {x: acc.x + s.x, y: acc.y + s.y, r: acc.r + s.r};
    },
    {x: 0, y: 0, r: 0},
  );
