"""Mixage : musique fournie (automation de volume + filtre passe-bas) et effets ponctuels synthetises.
Aucune voix off, aucun son de match. Usage : python3 audio.py <musique.wav 48 kHz> <sortie.wav>"""
import sys
import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt, sosfilt, fftconvolve

SR, DUR = 48000, 35.0
N = int(SR * DUR)
OFFSET = 3.10            # t (bande-annonce) = t (musique) - 3,10 s : l'entree de basse (29,60 s) tombe a 26,50 s
T = np.arange(N) / SR
rng = np.random.default_rng(5)

def db(x): return 10 ** (x / 20)

# ------------------------------------------------------------------ musique
sr, m = wav.read(sys.argv[1])
assert sr == SR
m = m.astype(np.float32) / 32768
m = m[int(OFFSET * SR):int(OFFSET * SR) + N]
CUTS = [200, 400, 700, 1200, 2500, 5000]
vers = [sosfiltfilt(butter(4, c, 'low', fs=SR, output='sos'), m, axis=0) for c in CUTS] + [m]
LOGC = np.log([*CUTS, 20000])

# (temps, gain dB, frequence de coupure)
AUTO = [(0.0, -80, 200), (0.8, -60, 200), (5.0, -24, 220), (5.05, -34, 220), (5.9, -30, 400),
        (6.0, -18, 700), (9.9, -14, 2500),
        (10.0, -8, 20000), (14.0, -6, 20000), (18.0, -4, 20000), (23.9, -0.5, 20000),
        (24.0, -1, 20000), (25.4, -21, 700), (25.85, -62, 400), (26.49, -80, 400),
        (26.505, 0, 20000), (34.3, 0, 20000), (34.98, -80, 20000), (35.0, -80, 20000)]
at = np.array([a[0] for a in AUTO]); ag = np.array([a[1] for a in AUTO]); ac = np.log([a[2] for a in AUTO])
gain = db(np.interp(T, at, ag))
lc = np.interp(T, at, ac)
music = np.zeros_like(m)
pos = np.interp(lc, LOGC, np.arange(len(LOGC)))
for i, v in enumerate(vers):
    w = np.clip(1 - np.abs(pos - i), 0, 1)
    music += v * w[:, None]
music *= gain[:, None]

# ------------------------------------------------------------------ effets
sfx = np.zeros((N, 2), np.float32)
def add(t0, sig, amp=1.0, pan=0.0):
    i0 = int(t0 * SR); sig = np.asarray(sig, np.float32) * amp
    n = min(len(sig), N - i0)
    if sig.ndim == 1: sig = np.c_[sig * (1 - max(pan, 0)), sig * (1 + min(pan, 0))]
    sfx[i0:i0 + n] += sig[:n]

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1) * np.exp(-t / d)

def beep(f=1000, dur=0.12):
    n = int(dur * SR); t = np.arange(n) / SR
    e = np.minimum(t / 0.003, 1) * np.clip((dur - t) / 0.02, 0, 1)
    return np.sin(2 * np.pi * f * t) * e

def boom(f0=80, f1=36, dur=1.4, decay=0.45):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.12)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * env(n, 0.002, decay)
    click = rng.standard_normal(n) * env(n, 0.0005, 0.012)
    click = sosfilt(butter(2, 2500, 'low', fs=SR, output='sos'), click)
    return np.tanh(1.6 * (s + 0.5 * click)) / np.tanh(1.6)

def noise_burst(dur, lo, hi, a, d):
    n = int(dur * SR)
    x = sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), rng.standard_normal(n))
    return x * env(n, a, d) / 3

# bourdonnement discret 0 - 5 s
n = int(5.0 * SR); t = np.arange(n) / SR
hum = (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 110 * t) + 0.2 * np.sin(2 * np.pi * 165 * t))
hum += 0.6 * sosfilt(butter(2, [90, 300], 'band', fs=SR, output='sos'), rng.standard_normal(n))
hum *= np.clip(t / 0.8, 0, 1) * np.clip((5.0 - t) / 0.03, 0, 1) * (0.6 + 0.4 * t / 5)
add(0, hum, db(-36))
# basse progressive : pulsation grave a chaque seconde, de plus en plus presente
for k in range(5):
    add(k + 0.0, boom(60, 42, 0.8, 0.22), db(-30 + 3.2 * k))
# bips du compteur
for k in range(5):
    add(k + 0.02, beep(1000 + 40 * k), db(-24 + 1.2 * k))
# 0 : buzzer + impact + fissure
n = int(0.95 * SR); t = np.arange(n) / SR
bz = sum(np.sign(np.sin(2 * np.pi * f * t)) * w for f, w in ((233, 1.0), (349, 0.7), (466, 0.35)))
bz = sosfilt(butter(4, 2800, 'low', fs=SR, output='sos'), bz) * np.minimum(t / 0.01, 1) * np.clip((0.95 - t) / 0.12, 0, 1)
add(5.0, bz, db(-21))
add(5.0, boom(95, 34, 1.6, 0.5), db(-5))
for k in range(9):                                   # craquements de la vitre
    add(5.0 + k * 0.014 + rng.uniform(0, 0.01), noise_burst(0.05, 2500, 9000, 0.0005, 0.008), db(-16), rng.uniform(-0.4, 0.4))
# verre brise
add(5.55, noise_burst(0.7, 1800, 12000, 0.001, 0.12), db(-13))
for k in range(46):
    f = rng.uniform(2600, 7500); d = rng.uniform(0.02, 0.10); tt = 5.56 + rng.exponential(0.12)
    nn = int(0.3 * SR); x = np.arange(nn) / SR
    add(tt, np.sin(2 * np.pi * f * x) * env(nn, 0.0005, d), db(rng.uniform(-30, -22)), rng.uniform(-0.7, 0.7))
# historique : un impact grave par chiffre
add(6.6, boom(72, 38, 1.3, 0.42), db(-6))
add(7.6, boom(66, 34, 1.4, 0.48), db(-5))
# transitions discretes vers les portraits
for t0 in (9.72, 13.72, 17.72):
    n = int(0.38 * SR); x = np.arange(n) / SR
    w = sosfilt(butter(2, [400, 3500], 'band', fs=SR, output='sos'), rng.standard_normal(n))
    add(t0, w * (x / 0.38) ** 2 * np.clip((0.38 - x) / 0.03, 0, 1) / 3, db(-24))
# silence presque total avant la revelation : un souffle grave a peine audible
n = int(0.75 * SR); x = np.arange(n) / SR
air = np.sin(2 * np.pi * 55 * x) + 0.5 * sosfilt(butter(2, [60, 240], 'band', fs=SR, output='sos'), rng.standard_normal(n))
add(25.75, air * np.clip(x / 0.2, 0, 1) * np.clip((0.75 - x) / 0.02, 0, 1), db(-46))
# ARE / YOU / READY? : un coup sourd par mot, tres court, avant le quasi-silence
for t0, g in ((25.05, -17), (25.36, -15), (25.67, -13)):
    add(t0, boom(70, 45, 0.35, 0.09), db(g))
# revelation : le plus gros impact
add(26.5, boom(85, 30, 2.4, 0.75), db(-3))
add(26.5, noise_burst(1.6, 200, 5000, 0.001, 0.35), db(-12))
# dernier impact sur l'affiche, puis extinction
add(34.16, boom(78, 34, 0.84, 0.4), db(-6))

# reverberation legere sur les effets
ir_n = int(1.3 * SR)
ir = rng.standard_normal((ir_n, 2)) * np.exp(-np.arange(ir_n) / SR / 0.32)[:, None]
ir = np.stack([sosfilt(butter(2, 3500, 'low', fs=SR, output='sos'), ir[:, c]) for c in range(2)], 1)
ir /= np.abs(ir).sum(0) ** 0.5 * 4
wet = np.stack([fftconvolve(sfx[:, c], ir[:, c])[:N] for c in range(2)], 1)
sfx = sfx + 0.22 * wet

mix = music + sfx
mix *= np.clip((DUR - T) / 0.04, 0, 1)[:, None]      # pas de clic final
mix /= max(1e-6, np.abs(mix).max()) / 0.89
wav.write(sys.argv[2], SR, (mix * 32767).astype(np.int16))
print('ok peak', np.abs(mix).max())
