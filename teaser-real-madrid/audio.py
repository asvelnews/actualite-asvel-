"""Bande-son du teaser Real Madrid vs LDLC ASVEL (60 s) — version 2.
Musique originale entièrement synthétisée (oscillateurs, enveloppes, filtres, réverbération) :
aucun sample externe, aucun ayant droit tiers, aucune IA générative.
Tempo 120 BPM (temps = 0,5 s) : les coupes image tombent sur la grille.
Sortie : music_sfx.wav (mix complet) + sfx_only.wav (bruitages seuls)."""
import sys, numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
DUR = 60.0
N = int(SR * DUR)
rng = np.random.default_rng(11)

def buf(): return np.zeros((N, 2), np.float32)
music, sfx, amb = buf(), buf(), buf()

def t_(d): return np.arange(int(d * SR)) / SR
def midi(m): return 440.0 * 2 ** ((m - 69) / 12)

def add(bus, start, x, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N: return
    if x.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414
        x = np.stack([x * l, x * r], 1)
    x = x[: N - i] * gain
    bus[i:i + len(x)] += x

def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR / 2 - 100) / (SR / 2), 'low'); return signal.lfilter(b, a, x, axis=0)
def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'high'); return signal.lfilter(b, a, x, axis=0)
def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band'); return signal.lfilter(b, a, x, axis=0)

def env(n, a, r, total, hold=1.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * hold
    return e * np.clip((total - t) / max(r, 1e-4), 0, 1)

def saw(f, d, ph=None):
    t = t_(d); ph = rng.random() if ph is None else ph
    return 2 * ((t * f + ph) % 1) - 1

def smooth_noise(n, rate):
    k = max(2, int(n / SR * rate)); pts = rng.standard_normal(k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)

# ---------------------------------------------------------------- instruments
def strings(notes, d, fc=1800, gain=0.1, attack=0.8, release=1.0):
    """Ensemble de cordes : 5 scies désaccordées par note, vibrato lent, stéréo large."""
    n = int(d * SR); L = np.zeros(n); R = np.zeros(n); t = t_(d)
    for m in notes:
        for k in range(5):
            det = (k - 2) * 0.0035; vib = 1 + 0.0025 * np.sin(2 * np.pi * (4.8 + k * 0.3) * t + rng.random() * 6)
            x = 2 * ((np.cumsum(midi(m) * (1 + det) * vib) / SR + rng.random()) % 1) - 1
            p = (k - 2) / 2.5
            L += x * (1 - p) * 0.5; R += x * (1 + p) * 0.5
    y = np.stack([L, R], 1) / (len(notes) * 5) ** 0.5
    y = lp(y, fc, 2) * env(n, attack, release, d)[:, None]
    return y * gain

def braam(root, d=3.0, gain=0.35):
    """Cuivres graves de bande-annonce : filtre qui s'ouvre puis se referme, saturation."""
    n = int(d * SR); t = t_(d); y = np.zeros(n)
    for m, a in [(root - 12, 1.0), (root, 0.8), (root + 7, 0.5), (root + 12, 0.35)]:
        for k in (-1, 1):
            y += a * (2 * ((t * midi(m) * (1 + k * 0.004) + rng.random()) % 1) - 1)
    fcs = 200 + 1600 * np.exp(-t * 2.2) * (1 - np.exp(-t * 30))
    out = np.zeros(n); seg = 512; zi = None
    for i in range(0, n, seg):
        b, a = signal.butter(2, fcs[i] / (SR / 2), 'low')
        if zi is None: zi = signal.lfilter_zi(b, a) * 0
        out[i:i + seg], zi = signal.lfilter(b, a, y[i:i + seg], zi=zi)
    out = np.tanh(out * 0.9) * env(n, 0.02, 1.2, d)
    return np.stack([out, out * 0.96], 1) * gain

def taiko(f0=60, d=1.2, gain=1.0):
    t = t_(d); f = f0 * (1 + 0.9 * np.exp(-t * 28))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    skin = lp(rng.standard_normal(len(t)), 1400) * np.exp(-t * 35) * 0.6
    return np.tanh((body + skin) * 1.6) * gain

def snare_hit(d=0.5, gain=0.4):
    t = t_(d); x = bp(rng.standard_normal(len(t)), 900, 6000) * np.exp(-t * 14)
    x += np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.6
    return x * gain

def impact(d=3.0, f0=90, f1=28, noise=0.5, gain=1.0):
    t = t_(d); f = f1 + (f0 - f1) * np.exp(-t * 8)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.3)
    nz = lp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 12) * noise
    body = lp(rng.standard_normal(len(t)), 250) * np.exp(-t * 3.5) * 0.8
    return np.tanh((sub + nz + body) * 1.3) * gain

def riser(d, gain=0.4, f0=110, oct_=2):
    t = t_(d); p = t / d; nz = rng.standard_normal(len(t)); out = np.zeros(len(t)); seg = 2048
    for i in range(0, len(t), seg):
        fc = 250 + 7000 * (i / len(t)) ** 2
        out[i:i + seg] = bp(nz[i:i + seg], fc * 0.7, min(fc * 1.3, 20000), 1)
    tone = np.sin(2 * np.pi * np.cumsum(f0 * 2 ** (p * oct_)) / SR) * 0.25
    return (out + tone) * p ** 2.2 * gain

def whoosh(d=0.5, lo=300, hi=5000, gain=0.25):
    t = t_(d); nz = rng.standard_normal(len(t)); out = np.zeros(len(t)); seg = 1024
    for i in range(0, len(t), seg):
        fc = lo + (hi - lo) * np.sin(np.pi * i / len(t))
        out[i:i + seg] = bp(nz[i:i + seg], fc * 0.6, min(fc * 1.4, 20000), 1)
    return out * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * gain

def piano(m, d=4.0, vel=1.0, pan=0.0):
    """Piano additif : partiels légèrement inharmoniques, attaque de marteau, deux cordes désaccordées."""
    t = t_(d); f = midi(m); x = 0
    for k, a in enumerate((1, 0.5, 0.28, 0.15, 0.08, 0.04), 1):
        fk = f * k * np.sqrt(1 + 0.00035 * k * k)
        dec = 0.9 + k * 0.7 + (m - 60) * 0.02
        x = x + a * (np.sin(2 * np.pi * fk * t) + 0.6 * np.sin(2 * np.pi * fk * 1.0012 * t)) * np.exp(-t * dec)
    x += lp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 200) * 0.25
    x *= (1 - np.exp(-t * 900)) * vel * 0.22
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([x * l, x * r], 1) * 1.414

def heartbeat(gain=1.0):
    def thump(f0):
        t = t_(0.24); return np.sin(2 * np.pi * np.cumsum(f0 * np.exp(-t * 6)) / SR) * np.exp(-t * 20)
    x = np.zeros(int(0.5 * SR)); a = thump(68); b = thump(56) * 0.7
    x[:len(a)] += a; o = int(0.17 * SR); x[o:o + len(b)] += b
    return lp(x, 280) * gain

def beep(f=1046.5, d=0.15):
    t = t_(d); x = np.sign(np.sin(2 * np.pi * f * t)) * 0.4 + np.sin(2 * np.pi * f * t) * 0.6
    return lp(x, 5000) * env(len(t), 0.003, 0.03, d)

def buzzer(d=0.9):
    t = t_(d); x = sum(2 * ((t * f) % 1) - 1 for f in (196, 247, 294))
    return np.tanh(bp(x, 150, 3500) * 1.6) * env(len(t), 0.005, 0.08, d)

def step(near):
    t = t_(0.25)
    thud = np.sin(2 * np.pi * np.cumsum(95 * (1 + 0.5 * np.exp(-t * 60))) / SR) * np.exp(-t * 28)
    click = hp(rng.standard_normal(len(t)), 1500) * np.exp(-t * 90) * 0.35 * (0.5 + near)
    return thud + click

def squeak(g):
    d = rng.uniform(0.05, 0.09); t = t_(d); f = rng.uniform(1800, 2600) * (1 + 0.25 * t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) * g

def crowd(d):
    """Rumeur de salle : bruit large bande modulé + applaudissements (stéréo décorrélée)."""
    n = int(d * SR); out = np.zeros((n, 2))
    for ch in range(2):
        for fc in (280, 480, 800, 1250, 1900, 2900):
            layer = bp(rng.standard_normal(n), fc * 0.7, fc * 1.4, 2)
            out[:, ch] += layer * (0.6 + 0.4 * np.tanh(smooth_noise(n, 1.6))) / np.sqrt(fc / 280)
        claps = np.zeros(n)
        for c in rng.uniform(0, d, int(d * 90)):
            i = int(c * SR); L = int(0.012 * SR)
            if i + L < n: claps[i:i + L] += rng.standard_normal(L) * np.exp(-np.arange(L) / (0.003 * SR)) * rng.uniform(0.2, 1)
        out[:, ch] += hp(claps, 1200) * 0.5
    return out / (np.abs(out).max() + 1e-9)

def reverb(x, secs=2.6, mix=0.25, bright=6000):
    t = t_(secs); ir = rng.standard_normal((len(t), 2)) * np.exp(-t * 6.9 / secs)[:, None]
    ir = lp(ir, bright)
    wet = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    wet *= (np.sqrt((x ** 2).mean()) + 1e-9) / (np.sqrt((wet ** 2).mean()) + 1e-9)
    return x * (1 - mix) + wet * mix

def automate(bus, pts):
    tl = np.arange(N) / SR; g = np.interp(tl, [p[0] for p in pts], [p[1] for p in pts]); bus *= g[:, None]

Dm, Bb, F, C, Gm, A = [50, 53, 57], [46, 50, 53], [45, 48, 53], [43, 48, 52], [43, 46, 50], [45, 49, 52]

# =============================================================== 0–6.5 : INTRO, chrono
CR = crowd(DUR)
crowd_env = [(0, 0), (1.2, 0.05), (6.0, 0.10), (6.5, 0.22), (10, 0.18), (16.8, 0.22), (17.0, 0.0), (40.0, 0.0),
             (42.5, 0.08), (44.0, 0.20), (45.0, 0.42), (48.8, 0.45), (49.0, 0.10), (53.2, 0.10), (53.35, 0.38), (59, 0.25), (60, 0)]
amb_far = lp(CR, 700)      # foule lointaine (derrière les murs) au début et dans le tunnel
amb_near = CR
tl = np.arange(N) / SR
far_mix = np.interp(tl, [0, 6.3, 6.6, 40, 44.0, 45.0, 60], [1, 1, 0, 0, 1, 0, 0])[:, None]
amb += (amb_far * far_mix + amb_near * (1 - far_mix)) * 0.9
automate(amb, crowd_env)

for i, ht in enumerate([1.0, 1.8, 2.6, 3.4, 4.2, 5.0]):
    add(sfx, ht - 0.25, heartbeat(0.45 + 0.07 * i))
for i, bt in enumerate([2.0, 2.8, 3.6, 4.4, 5.2]):
    add(sfx, bt, beep(), 0.10 + 0.05 * i)
add(music, 1.5, riser(5.0, 0.12, 55, 2))
add(music, 2.0, strings([38], 4.5, 300, 0.10, 2.0, 0.3))
add(sfx, 6.0, buzzer(), 0.30)

# =============================================================== 6.5–17 : MADRID / LE DÉFI (montée)
add(sfx, 6.45, whoosh(0.3, 600, 8000, 0.3))
add(sfx, 6.5, impact(3.5, 95, 26, 0.6), 0.85)
add(music, 6.5, braam(38, 3.5, 0.30))
add(music, 6.5, strings(Dm, 4.0, 1200, 0.10, 0.4, 0.8))
add(music, 10.0, strings(Bb, 2.2, 1500, 0.11, 0.3, 0.5)); add(music, 12.0, strings(F, 2.2, 1700, 0.12, 0.3, 0.5))
add(music, 14.0, strings(C, 2.2, 1900, 0.13, 0.3, 0.5)); add(music, 16.0, strings(A, 1.0, 2200, 0.14, 0.3, 0.1))
def ostinato(m, a, b, step_=0.25, g0=0.05, g1=0.1, fc0=600, fc1=2600):
    tt = a
    while tt < b - 1e-6:
        p = (tt - a) / max(b - a, 1e-6); d = step_ * 0.92
        x = (saw(midi(m), d) + saw(midi(m + 12), d) * 0.4) * env(int(d * SR), 0.008, 0.05, d)
        add(music, tt, lp(x, fc0 + (fc1 - fc0) * p), g0 + (g1 - g0) * p, pan=0.15 if int(tt * 4) % 2 else -0.15)
        tt += step_
ostinato(50, 8.0, 17.0, 0.25, 0.07, 0.11)
for i, bt in enumerate(np.arange(10.0, 17.0, 0.5)):
    add(music, bt, taiko(58 if i % 2 == 0 else 80, 1.0, 0.30 + 0.025 * i))
for bt in [12.0, 12.5, 13.0]:
    add(sfx, bt, impact(1.2, 120, 45, 0.3), 0.28)
add(sfx, 10.0, whoosh(0.35, 500, 7000, 0.28))
for i, bt in enumerate(np.arange(16.0, 17.0, 0.125)):
    add(music, bt, snare_hit(0.3, 0.06 + 0.03 * i))
add(music, 14.5, riser(2.5, 0.28))

# =============================================================== 17–31 : ÉMOTION (piano)
# 17.0 : tout s'arrête. 17.8 : premières notes.
pn = [  # (temps, notes, vélocité) — ré mineur, lent et mélancolique
    (17.8, [62], 0.8), (18.0, [38, 50, 57], 0.55), (18.6, [65], 0.6), (19.4, [69], 0.55), (20.2, [67], 0.5), (20.6, [65], 0.45),
    (22.0, [34, 46, 53], 0.55), (22.0, [62], 0.75), (22.8, [65], 0.55), (23.6, [70], 0.55), (24.2, [41, 48, 53], 0.55),
    (24.2, [69], 0.7), (25.0, [65], 0.5), (25.6, [64], 0.45),
    (26.0, [36, 48, 55], 0.6), (26.0, [67], 0.8), (26.6, [64], 0.5), (27.0, [60], 0.45),
    (27.8, [45, 52, 57], 0.6), (27.8, [73], 0.7), (28.4, [69], 0.55), (29.2, [38, 50, 57], 0.6), (29.2, [74], 0.75),
    (29.8, [69], 0.5), (30.2, [34, 46, 53], 0.6), (30.2, [70], 0.7), (30.6, [69], 0.55),
]
for tt, notes, v in pn:
    for k, m in enumerate(notes):
        add(music, tt + 0.012 * k, piano(m, 5.0, v * (0.8 if len(notes) > 1 else 1.0), pan=(-0.25 + 0.25 * k) if len(notes) > 1 else 0.15))
add(music, 18.0, strings([50, 57], 4.4, 900, 0.035, 2.0, 1.2))
add(music, 22.0, strings([50, 57], 5.2, 1100, 0.05, 2.0, 1.5))
add(music, 27.8, strings([52, 57, 61], 1.6, 1300, 0.06, 0.8, 0.6))
add(music, 29.2, strings([50, 57, 62, 65], 2.0, 1800, 0.08, 0.6, 0.5))
add(sfx, 17.8, whoosh(1.2, 150, 1200, 0.06))

# =============================================================== 30–40 : RETOUR DE LA HYPE
bass = np.zeros(int(10 * SR))
for i in range(20):  # basse en croches pointées sur ré
    d = 0.42; x = (saw(midi(26), d) + np.sin(2 * np.pi * midi(26) * t_(d)) * 1.2) * env(int(d * SR), 0.01, 0.1, d)
    s = int(i * 0.5 * SR); bass[s:s + len(x)] += lp(x, 260)
bass *= np.interp(np.arange(len(bass)) / SR, [0, 1.0, 10], [0, 1, 1])
add(music, 30.0, bass, 0.30)
add(music, 30.4, riser(0.6, 0.25))
cuts = [31.0, 32.5, 34.0, 35.5, 37.0]
for i, ct in enumerate(cuts):
    add(sfx, ct - 0.08, whoosh(0.2, 1500, 9000, 0.22))
    add(sfx, ct, impact(1.4, 110, 38, 0.4), 0.45)
    add(music, ct, braam(38 + [0, 3, 5, 0, 7][i], 1.4, 0.18))
for bt in np.arange(31.0, 38.5, 0.5):
    k = int(round((bt - 31.0) * 2))
    add(music, bt, taiko(55 if k % 4 in (0, 3) else 85, 0.9, 0.5 if k % 4 == 0 else 0.32))
    if k % 2 == 1: add(music, bt, snare_hit(0.4, 0.14))
for bt in np.arange(38.5, 40.0, 0.25):
    add(music, bt, taiko(80, 0.4, 0.35)); add(music, bt, snare_hit(0.25, 0.12))
    add(sfx, bt, whoosh(0.12, 2000, 9000, 0.10))
ostinato(50, 31.0, 40.0, 0.125, 0.06, 0.10, 1500, 3500)
add(music, 31.0, strings(Dm + [62], 4.0, 2400, 0.10, 0.2, 0.5)); add(music, 35.0, strings(Bb + [58], 2.0, 2400, 0.10, 0.2, 0.3))
add(music, 37.0, strings(Gm + [55], 1.5, 2600, 0.11, 0.2, 0.3)); add(music, 38.5, strings(A + [57], 1.5, 3000, 0.12, 0.2, 0.2))
add(music, 38.0, riser(2.0, 0.3))
add(sfx, 40.0, impact(3.0, 80, 26, 0.5), 0.75)

# =============================================================== 40–49 : L'ASVEL ENTRE DANS L'ARÈNE
corridor = buf()
for p in range(5):
    tt = 40.25 + rng.uniform(0, 0.5); per = rng.uniform(0.52, 0.6)
    while tt < 46.5:
        near = min(1.0, max(0.0, (tt - 40.0) / 6.0))
        add(corridor, tt, step(near), 0.20 + 0.30 * near, pan=(-0.6 + 0.3 * p))
        if rng.random() < 0.12: add(corridor, tt + 0.05, squeak(0.05 + 0.05 * near), pan=(-0.6 + 0.3 * p))
        tt += per + rng.uniform(-0.03, 0.03)
sfx += reverb(corridor, 1.9, 0.45, 4000)
add(music, 40.0, strings([38], 4.0, 220, 0.12, 1.0, 0.5))
add(music, 40.5, strings([62, 69], 3.5, 900, 0.025, 1.5, 0.5))
for tt in [40.3, 41.0, 41.7, 42.4, 43.1]:
    add(sfx, tt, impact(1.0, 70, 40, 0.15), 0.25)
add(music, 42.0, riser(2.0, 0.22))
add(sfx, 44.0, impact(3.5, 100, 26, 0.6), 0.85)
add(music, 44.0, braam(38, 3.0, 0.30)); add(music, 44.0, strings(Dm + [62], 2.0, 2200, 0.12, 0.1, 0.5))
add(music, 46.0, strings(Bb + [62], 2.0, 2500, 0.13, 0.2, 0.5)); add(music, 48.0, strings(A + [61], 1.0, 2800, 0.14, 0.2, 0.2))
pattern = [0, 0.75, 1.0, 1.5, 1.75]
for bs in [44.0, 46.0, 48.0]:
    for p in pattern:
        if bs + p < 49.0: add(music, bs + p, taiko(55 if p in (0, 1.0) else 85, 0.9, 0.48))
ostinato(50, 44.0, 49.0, 0.125, 0.07, 0.11, 2000, 3500)
add(music, 47.5, riser(1.5, 0.28))

# =============================================================== 49–54 : FACE-À-FACE
for ht in [49.25, 50.0, 50.75, 51.5, 52.2, 52.85]:
    add(sfx, ht, heartbeat(0.8))
add(sfx, 49.3, impact(1.8, 95, 32, 0.4), 0.5)
add(sfx, 50.6, impact(1.8, 105, 34, 0.4), 0.55)
add(sfx, 51.9, impact(1.2, 120, 45, 0.25), 0.4)
add(music, 51.9, strings([38, 50], 1.1, 400, 0.14, 0.6, 0.05))
add(music, 52.1, riser(0.9, 0.22))
add(sfx, 53.25, whoosh(0.1, 2000, 9000, 0.25))
add(sfx, 53.3, impact(4.0, 120, 24, 0.9), 1.25)
add(music, 53.3, braam(38, 3.5, 0.40))

# =============================================================== 53.3–60 : RÉVÉLATION
add(music, 53.3, strings(Dm + [62, 69], 3.0, 3000, 0.14, 0.05, 1.0))
for bs in [53.3, 55.3, 57.3]:
    for p in pattern:
        if bs + p < 59.2: add(music, bs + p, taiko(55 if p in (0, 1.0) else 85, 0.9, 0.5))
ostinato(50, 53.3, 58.8, 0.125, 0.08, 0.09, 3000, 3500)
add(music, 56.3, strings(Bb + [62], 2.0, 3000, 0.13, 0.1, 0.6))
add(music, 58.0, braam(33, 2.0, 0.32)); add(music, 58.0, strings(A + [61, 64], 2.0, 2800, 0.13, 0.05, 1.8))
add(sfx, 54.0, impact(2.5, 100, 30, 0.5), 0.6)
add(sfx, 58.0, impact(2.0, 90, 28, 0.5), 0.7)

# =============================================================== MIX
music = reverb(music, 2.4, 0.26)
def silence(bus, a, b): bus[int(a * SR):int(b * SR)] = 0
silence(music, 17.0, 17.8)                 # coupure brutale de la musique épique
music[int(27.35 * SR):int(27.8 * SR)] *= np.linspace(1, 0.15, int(27.8 * SR) - int(27.35 * SR))[:, None]
silence(music, 49.0, 49.25)                # la musique se coupe
music[int(49.25 * SR):int(53.3 * SR)] *= 0.55
silence(music, 53.0, 53.3)                 # silence très court avant « AVEC LA VICTOIRE »
silence(sfx, 53.0, 53.25)
sfx = reverb(sfx, 1.3, 0.12)
fade = np.ones(N); fs = int(59.0 * SR); fade[fs:] = np.linspace(1, 0, N - fs) ** 1.5
mix = (music * 0.9 + sfx + amb * 0.55) * fade[:, None]
def master(x):
    x = np.tanh(x * 1.15) / np.tanh(1.15)
    return (x / (np.abs(x).max() + 1e-9) * 0.89).astype(np.float32)
wavfile.write(sys.argv[1] if len(sys.argv) > 1 else 'music_sfx.wav', SR, master(mix))
wavfile.write(sys.argv[2] if len(sys.argv) > 2 else 'sfx_only.wav', SR, master((sfx + amb * 0.55) * fade[:, None]))
print('ok')
