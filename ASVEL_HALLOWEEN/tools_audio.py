"""Design sonore 100 % synthétisé (aucun échantillon externe => aucun problème de droits).
Lit src/timeline.json pour caler chaque son sur l'image. Produit trois fichiers 48 kHz stéréo :
  public/audio/ASVEL_HALLOWEEN_MIX.wav       (musique + effets)
  public/audio/ASVEL_HALLOWEEN_SFX_ONLY.wav  (effets seuls : version sans musique)
  public/audio/ASVEL_HALLOWEEN_MUSIC.wav     (musique seule, stem)
"""
import json
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
TL = json.load(open('src/timeline.json'))
FPS = TL['fps']
DUR = TL['duration'] / FPS
N = int(DUR * SR) + SR * 2
rng = np.random.default_rng(31)
sec = lambda fr: fr / FPS

music = np.zeros((N, 2))
sfx = np.zeros((N, 2))

def add(buf, t, x, gain=1.0, pan=0.0):
    """Ajoute un son mono/stéréo à t secondes, panoramique à puissance constante."""
    i = int(t * SR)
    if x.ndim == 1:
        l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
        x = np.stack([x * l, x * r], 1) * np.sqrt(2)
    j = min(N, i + len(x))
    if j > i >= 0:
        buf[i:j] += x[: j - i] * gain

def adsr(n, a, r):
    e = np.ones(n); A = max(1, int(a * SR)); R = max(1, int(r * SR))
    e[:A] = np.linspace(0, 1, A); e[-R:] *= np.linspace(1, 0, R)
    return e

def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), 'low'); return signal.lfilter(b, a, x, axis=0)
def hp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), 'high'); return signal.lfilter(b, a, x, axis=0)
def bp(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), min(f2 / (SR / 2), 0.99)], 'band'); return signal.lfilter(b, a, x, axis=0)

def lp_sweep(x, cut, bs=1024):
    """Passe-bas dont la coupure varie dans le temps (traité par blocs, état du filtre conservé)."""
    y = np.zeros_like(x); zi = None
    for i in range(0, len(x), bs):
        b, a = signal.butter(2, min(cut[i] / (SR / 2), 0.99), 'low')
        if zi is None: zi = signal.lfilter_zi(b, a) * 0
        y[i:i + bs], zi = signal.lfilter(b, a, x[i:i + bs], zi=zi)
    return y

def noise(dur): return rng.standard_normal(int(dur * SR))
def brown(dur):
    x = np.cumsum(noise(dur)); x = hp(x, 15); return x / (np.abs(x).max() + 1e-9)
def t_(dur): return np.arange(int(dur * SR)) / SR

def reverb_ir(dur=3.0, damp=3000):
    n = int(dur * SR); t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t * 6.9 / dur)[:, None]
    ir = lp(ir, damp); ir[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))[:, None]
    return ir / np.sqrt((ir ** 2).sum(0))[None, :]

def reverb(x, wet, dur=3.0, damp=3000):
    ir = reverb_ir(dur, damp)
    if x.ndim == 1: x = np.stack([x, x], 1)
    y = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    return x * (1 - wet) + y * wet * 3

# ---------------------------------------------------------------- instruments / effets
def heartbeat(gain=1.0):
    def thump(f0, dur, g):
        t = t_(dur); ph = 2 * np.pi * np.cumsum(f0 * (1 - 0.35 * t / dur)) / SR
        return np.sin(ph) * np.exp(-t * 18) * g + lp(noise(dur), 120) * np.exp(-t * 40) * 0.3 * g
    x = np.zeros(int(0.7 * SR))
    a = thump(58, 0.35, 1.0); b = thump(50, 0.35, 0.7)
    x[: len(a)] += a; o = int(0.26 * SR); x[o: o + len(b)] += b
    return lp(x, 180) * gain

def wind(dur, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for c in range(2):
        x = brown(dur) * 0.6 + noise(dur) * 0.05
        lfo = 0.55 + 0.45 * np.sin(2 * np.pi * (0.09 + 0.03 * c) * t + c) * np.sin(2 * np.pi * 0.23 * t + 2 * c)
        x = bp(x, 250, 1400) * lfo
        whistle = bp(noise(dur), 700 + 80 * c, 760 + 80 * c, 2) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t + c)) * 6
        out[:, c] = x + whistle * 0.25
    return out / np.abs(out).max() * g

def rumble(dur, g=1.0):
    t = t_(dur); x = lp(brown(dur), 70, 4) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t))
    return x / (np.abs(x).max() + 1e-9) * g

def thunder(g=1.0, dist=0.0):
    dur = 4.5; t = t_(dur)
    crack = hp(noise(0.12), 1500) * np.exp(-t_(0.12) * 35) * (1 - dist)
    roll = lp(brown(dur), 400 - 250 * dist, 2)
    am = lp(np.abs(noise(dur)), 6) * 6
    roll = roll * np.exp(-t * (0.9 + dist)) * (0.4 + am) * np.minimum(1, t / 0.08)
    x = roll / (np.abs(roll).max() + 1e-9)
    x[: len(crack)] += crack / (np.abs(crack).max() + 1e-9) * 0.8
    return reverb(x * g, 0.35, 3.5, 2500)

def impact(g=1.0, braam=True):
    dur = 4.0; t = t_(dur)
    sub = np.sin(2 * np.pi * np.cumsum(65 * np.exp(-t * 1.2) + 28) / SR) * np.exp(-t * 1.1)
    hit = lp(noise(0.4), 2500) * np.exp(-t_(0.4) * 14)
    x = sub * 0.9; x[: len(hit)] += hit * 0.7
    if braam:
        br = np.zeros_like(t)
        for k, f in enumerate([36.7, 36.95, 73.4, 55.0, 110.1]):   # ré grave + quinte
            br += signal.sawtooth(2 * np.pi * f * t + k)
        y = lp_sweep(br, 180 + 1400 * np.exp(-t * 2.5))
        x += y * 0.12 * np.exp(-t * 0.8) * np.minimum(1, t / 0.03)
    return reverb(x * g, 0.3, 3.0, 3000)

def whoosh(dur=1.2, f0=300, f1=3000, g=1.0, rev=False):
    n = int(dur * SR); x = noise(dur); y = np.zeros(n); bs = 1024
    fr = np.geomspace(f0, f1, n) if not rev else np.geomspace(f1, f0, n)
    for i in range(0, n, bs):
        c = fr[i]; y[i:i + bs] = bp(x[i:i + bs], c * 0.7, c * 1.3)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return reverb(y * e / (np.abs(y).max() + 1e-9) * g, 0.25, 1.5)

def slash(g=1.0):
    x = whoosh(0.28, 6000, 1500, 1.0, False)
    t = t_(0.28); ring = sum(np.sin(2 * np.pi * f * t) for f in [2350, 3410, 5120]) * np.exp(-t * 14) * 0.15
    x[: len(ring)] += np.stack([ring, ring], 1)
    return x * g

def metal_screech(dur=1.6, g=1.0):
    t = t_(dur); vib = 1 + 0.012 * np.sin(2 * np.pi * 6.5 * t) + 0.02 * t
    x = sum(np.sin(2 * np.pi * np.cumsum(f * vib) / SR) * a for f, a in [(1180, 1), (1712, 0.6), (2395, 0.5), (3311, 0.35), (4870, 0.2)])
    grit = bp(noise(dur), 1500, 6000) * 0.25 * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 23 * t)))
    e = adsr(len(t), 0.05, 0.6)
    return reverb((x * 0.25 + grit) * e * g, 0.45, 2.5, 6000)

def creak(dur=1.4, g=1.0):
    t = t_(dur); pulses = (np.sin(2 * np.pi * np.cumsum(28 + 12 * np.sin(2 * np.pi * 0.8 * t)) / SR) > 0.97).astype(float)
    x = bp(signal.lfilter([1], [1, -0.97], pulses), 300, 2500) * adsr(len(t), 0.1, 0.4)
    return reverb(x / (np.abs(x).max() + 1e-9) * g, 0.4, 2)

def step(g=1.0):
    t = t_(0.25); x = np.sin(2 * np.pi * 80 * t) * np.exp(-t * 30) + lp(noise(0.25), 900) * np.exp(-t * 45) * 0.6
    return reverb(x * g, 0.5, 2.2, 1800)

def breath(dur=2.2, g=1.0):
    t = t_(dur); n = len(t)
    e = np.concatenate([np.sin(np.linspace(0, np.pi, n // 2)) ** 1.5, 0.7 * np.sin(np.linspace(0, np.pi, n - n // 2)) ** 1.2])
    x = bp(noise(dur), 350, 1600) * e + bp(noise(dur), 2500, 4500) * e * 0.2
    return reverb(x / (np.abs(x).max() + 1e-9) * g, 0.3, 1.8)

def fire_crackle(dur, g=1.0, density=40):
    n = int(dur * SR); x = lp(brown(dur), 500) * 0.5
    for _ in range(int(dur * density)):
        i = rng.integers(0, n - 2000); L = rng.integers(80, 900)
        x[i:i + L] += hp(rng.standard_normal(L), 1500) * np.exp(-np.linspace(0, 8, L)) * rng.uniform(0.3, 1.2)
    return np.stack([x, np.roll(x, 300)], 1) / (np.abs(x).max() + 1e-9) * g

def distant_cry(g=1.0, f0=520):
    dur = 2.4; t = t_(dur)
    pitch = f0 * (1 + 0.25 * np.sin(np.pi * t / dur)) * (1 + 0.01 * np.sin(2 * np.pi * 5 * t))
    src = signal.sawtooth(2 * np.pi * np.cumsum(pitch) / SR)
    x = bp(src, 600, 1100) + bp(src, 2200, 2800) * 0.4   # voyelle "a" floue
    x = lp(x * adsr(len(t), 0.4, 1.2), 2000)
    return reverb(x / (np.abs(x).max() + 1e-9) * g, 0.85, 4.0, 2000)

# ---------------------------------------------------------------- musique
def note(f, dur, kind='str', g=1.0):
    t = t_(dur); n = len(t)
    if kind == 'str':     # cordes : scies désaccordées + vibrato + filtre
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t)
        x = sum(signal.sawtooth(2 * np.pi * np.cumsum(f * d * vib) / SR + k) for k, d in enumerate([0.996, 1.0, 1.004]))
        x = lp(x, min(3500, f * 6)) * adsr(n, min(0.6, dur / 3), min(0.8, dur / 3))
    elif kind == 'trem':  # cordes en trémolo
        x = sum(signal.sawtooth(2 * np.pi * f * d * t + k) for k, d in enumerate([0.997, 1.003]))
        x = lp(x, min(3000, f * 5)) * (0.6 + 0.4 * np.sin(2 * np.pi * 12 * t) ** 2) * adsr(n, 0.2, 0.3)
    elif kind == 'box':   # boîte à musique désaccordée
        x = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) + 0.2 * np.sin(2 * np.pi * f * 5.4 * t)) * np.exp(-t * 4)
    elif kind == 'brass':
        x = sum(signal.sawtooth(2 * np.pi * f * d * t) for d in [0.995, 1.0, 1.005])
        x = lp_sweep(x, 250 + 1500 * np.minimum(1, t / 0.4)) * adsr(n, 0.08, 0.5)
    elif kind == 'choir':
        x = sum(np.sin(2 * np.pi * f * h * t * (1 + 0.003 * np.sin(2 * np.pi * 4.8 * t + h))) / h for h in [1, 2, 3, 4, 5])
        x = bp(x, 300, 1800) * adsr(n, dur / 3, dur / 3)
    return x * g

def taiko(g=1.0, f0=70):
    t = t_(1.2); x = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.5 * np.exp(-t * 30))) / SR) * np.exp(-t * 6)
    x += lp(noise(1.2), 1200) * np.exp(-t * 25) * 0.5
    return x * g

def riser(dur, g=1.0):
    t = t_(dur); n = len(t)
    f = np.geomspace(60, 900, n)
    x = sum(signal.sawtooth(2 * np.pi * np.cumsum(f * m) / SR) for m in [1, 1.5, 2.003])
    x = lp(x, 3000) * (t / dur) ** 2
    nz = hp(noise(dur), 2000) * (t / dur) ** 3 * 0.6
    return (x * 0.3 + nz) * g

D = {'D1': 36.71, 'A1': 55.0, 'D2': 73.42, 'F2': 87.31, 'A2': 110.0, 'Bb2': 116.54, 'C3': 130.81, 'D3': 146.83, 'Eb3': 155.56, 'E3': 164.81,
     'F3': 174.61, 'G3': 196.0, 'A3': 220.0, 'Bb3': 233.08, 'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'A4': 440.0, 'D5': 587.33}

def stereo(x, w=0.003):
    d = int(w * SR); return np.stack([x, np.concatenate([np.zeros(d), x[:-d]])], 1)

# ================================================================= PLACEMENT
cue = TL['cues']; S = TL['scenes']

# --- S1 (0-10 s) : battements, vent, grondements, pas, tonnerre
hb_times = [0.5, 1.7, 2.85, 3.95, 5.0, 5.95, 6.85, 7.7, 8.5, 9.2]
for t in hb_times: add(sfx, t, heartbeat(), 0.95)
add(sfx, 0.0, wind(10.5), 0.22)
add(sfx, 0.0, rumble(10.0), 0.35)
for i, t in enumerate(np.arange(4.2, 9.3, 0.62)): add(sfx, t, step(), 0.22, pan=-0.4 + 0.08 * i)
add(sfx, 3.0, creak(1.6), 0.18, pan=0.5)
for fr in cue['lightning'][:4]: add(sfx, sec(fr) - 0.02, thunder(dist=0.2 if fr < 590 else 0.0), 0.55)
add(sfx, sec(cue['arenaText1']) - 0.3, whoosh(0.9, 200, 2500), 0.35)
add(sfx, sec(cue['arenaText2']) - 0.2, whoosh(0.8, 300, 3000), 0.35)
add(sfx, sec(cue['arenaText2']), impact(braam=False), 0.35)
# musique S1 : drone de ré grave + cluster de cordes qui grossit
add(music, 0.0, stereo(note(D['D2'], 10.2, 'str') * 0.5 + note(D['A1'], 10.2, 'str') * 0.4), 0.16)
add(music, 3.0, stereo(note(D['D3'], 7.2, 'trem') + note(D['Eb3'], 7.2, 'trem') * 0.7), 0.07)
add(music, 6.0, riser(4.0), 0.10)

# --- S2 (10-22 s) : apparitions
H = cue['horror']
add(sfx, sec(cue['bigImpact'][0]), impact(), 0.8)
add(sfx, sec(H['myers']) + 0.3, breath(2.4), 0.35)
add(sfx, sec(H['myers']) + 0.2, whoosh(1.6, 150, 900), 0.3)
add(sfx, sec(H['myers']) + 2.1, breath(2.2), 0.3)
add(sfx, sec(H['freddy']), metal_screech(1.8), 0.32, pan=-0.3)
add(sfx, sec(H['freddy']) + 0.5, slash(), 0.5)
add(sfx, sec(H['freddy']) + 0.55, impact(braam=False), 0.4)
for k, fr in enumerate([H['ghost'] + 20, H['ghost'] + 60, H['ghost'] + 120]): add(sfx, sec(fr), thunder(dist=0.1 * k), 0.5)
add(sfx, sec(H['ghost'] - 10), slash(), 0.45)
add(sfx, sec(H['art']) - 0.1, impact(braam=False), 0.45)
add(sfx, sec(H['art']) + 0.6, distant_cry(f0=480), 0.12, pan=0.6)
add(sfx, sec(H['ghost']) + 0.8, distant_cry(f0=610), 0.08, pan=-0.7)
add(sfx, 10.0, wind(12), 0.12)
for t in [sec(H['black']) + 0.15, sec(H['black']) + 0.6]: add(sfx, t, heartbeat(), 0.9)
# musique S2 : boîte à musique désaccordée (motif original) + cordes graves
box_mel = ['D5', 'A4', 'F4', 'E4', 'F4', 'D4', 'C#4', 'D4']
for i, n_ in enumerate(box_mel * 2):
    add(music, sec(H['art']) - 1.2 + i * 0.32, stereo(note(D[n_] * (1 + 0.006 * rng.standard_normal()), 1.2, 'box')), 0.09)
for k, (n_, t) in enumerate([('D2', 10.0), ('Bb2', 13.0), ('A1', 16.0), ('D2', 18.6)]):
    add(music, t, stereo(note(D[n_], 3.4, 'str') + note(D[n_] * 2, 3.4, 'trem') * 0.5), 0.13)
for fr in [H['freddy'], H['ghost'], H['art']]: add(music, sec(fr), stereo(note(D['D1'], 2.5, 'brass')), 0.18)

# --- S3 (22-32 s) : montée orchestrale sombre pour Patty Mills
p0 = sec(S['patty'][0])
add(sfx, p0, whoosh(1.8, 120, 1200), 0.5)          # nuage de fumée noire
add(sfx, p0 + 1.0, fire_crackle(9.0), 0.16)
add(sfx, sec(cue['pattyName']), impact(), 0.85)
add(sfx, sec(cue['pattyName']) + 0.75, whoosh(0.5, 400, 4000), 0.2)
for fr in [1610, 1700, 1840]: add(sfx, sec(fr), thunder(dist=0.3), 0.35)
for t in [p0 + 0.2, p0 + 1.1]: add(sfx, t, heartbeat(), 0.7)
chords = [(['D2', 'A2', 'D3', 'F3'], 0), (['Bb2', 'F3', 'Bb3', 'D4'], 2.5), (['C3', 'G3', 'C4', 'E4'], 5.0), (['A2', 'E3', 'A3', 'C#4'], 7.5)]
for ch, o in chords:
    for i, n_ in enumerate(ch): add(music, p0 + o, stereo(note(D[n_], 2.8, 'str'), 0.002 * (i + 1)), 0.075 + 0.02 * (o / 7.5))
    add(music, p0 + o, stereo(note(D[ch[0]] / 2, 2.8, 'brass')), 0.12)
add(music, p0 + 2.5, stereo(note(D['D4'], 7.5, 'choir')), 0.05)
add(music, p0 + 6.0, riser(4.0), 0.12)

# --- S4 (32-42 s) : percussions et basses pour Tadas
q0 = sec(S['tadas'][0])
for i, fr in enumerate([cue['tadasClaws'] - 10, cue['tadasClaws'] - 7, cue['tadasClaws'] - 4]): add(sfx, sec(fr), slash(), 0.55, pan=-0.3 + 0.3 * i)
add(sfx, sec(cue['tadasRedBlast']), impact(), 0.8)
add(sfx, sec(cue['tadasRedBlast']), whoosh(1.4, 3000, 200), 0.4)
add(sfx, sec(cue['tadasName']), impact(), 0.85)
for fr in [2050, 2260, 2400]: add(sfx, sec(fr), thunder(dist=0.25), 0.33)
add(sfx, q0 + 0.5, fire_crackle(9.5, density=60), 0.18)
bpm = 100; beat = 60 / bpm
pat = [1, 0, 0.6, 0, 1, 0.5, 0.6, 0]
for i in range(int(9.5 / (beat / 2))):
    v = pat[i % 8]
    if v: add(music, q0 + 0.5 + i * beat / 2, taiko(v, 62 if i % 4 == 0 else 85), 0.32, pan=(-0.3 if i % 2 else 0.3))
for k, n_ in enumerate(['D2', 'D2', 'F2', 'A1', 'D2', 'D2', 'Bb2', 'A1']):
    add(music, q0 + 0.5 + k * beat * 2.5, stereo(note(D[n_], beat * 2.4, 'brass')), 0.14)
add(music, q0, stereo(note(D['D3'], 10, 'trem') + note(D['A3'], 10, 'trem') * 0.6), 0.06)

# --- S5 (42-52 s) : montée épique du face-à-face
r0 = sec(S['faceoff'][0])
add(sfx, sec(cue['fireSweep']), whoosh(1.4, 100, 2500), 0.6)
add(sfx, sec(cue['fireSweep']), fire_crackle(1.6, density=200), 0.45)
for fr in [2700, 2930]: add(sfx, sec(fr), thunder(dist=0.0), 0.45)
for fr in [cue['faceoffText1'], cue['faceoffText2']]: add(sfx, sec(fr), impact(braam=False), 0.55)
add(sfx, r0, fire_crackle(10, density=70), 0.18)
for i in range(int(10 / 0.15)):
    t = r0 + i * 0.15 * (1 - 0.35 * i / 66)          # accélération
    if t > sec(cue['explosion']): break
    v = 1 if i % 4 == 0 else 0.45
    add(music, t, taiko(v, 70 if i % 4 == 0 else 95), 0.22 + 0.15 * i / 66, pan=(-0.25 if i % 2 else 0.25))
prog = [('D2', 'A3', 'D4', 'F4'), ('Bb2', 'F3', 'D4', 'F4'), ('C3', 'G3', 'E4', 'G3'), ('A2', 'E3', 'C#4', 'E4')]
for k, ch in enumerate(prog):
    for i, n_ in enumerate(ch): add(music, r0 + k * 2.5, stereo(note(D[n_], 2.7, 'str' if i else 'brass'), 0.002 * (i + 1)), 0.09 + 0.03 * k)
add(music, r0, stereo(note(D['D4'], 10, 'choir') + note(D['A4'], 10, 'choir') * 0.7), 0.06)
add(music, sec(cue['explosion']) - 6.0, riser(6.0), 0.24)
add(sfx, sec(cue['explosion']) - 1.2, whoosh(1.3, 200, 6000), 0.4)

# --- S6 (52-60 s) : impact final, réverbération et silence
g0 = sec(cue['gameDay'])
add(sfx, g0, impact(), 1.0)
add(sfx, g0, thunder(), 0.6)
add(sfx, g0 + sec(8), impact(), 0.75)
add(sfx, g0 + 0.25, slash(), 0.5)
add(sfx, sec(cue['bigImpact'][5]), impact(braam=False), 0.5)
for k in range(5): add(sfx, sec(cue['infoReveal']) - 0.35 + k * 0.27, whoosh(0.35, 800, 5000), 0.12)
add(sfx, sec(cue['brand']), impact(braam=False), 0.55)
add(sfx, sec(cue['brand']) + 0.1, metal_screech(1.0), 0.12)
add(music, g0, stereo(note(D['D1'], 6.0, 'brass') + note(D['D2'], 6.0, 'brass')), 0.3)
add(music, g0, stereo(note(D['D3'], 6.5, 'str') + note(D['A3'], 6.5, 'str') + note(D['F3'], 6.5, 'str')), 0.12)
add(music, g0 + 0.2, stereo(note(D['D4'], 5.5, 'choir')), 0.08)
add(sfx, g0 + 1.0, wind(7.0), 0.1)
for fr in cue['heartbeats'][-2:]: add(sfx, sec(fr), heartbeat(), 1.0)

# ---------------------------------------------------------------- mixage
def master(x, ceiling_db=-1.0):
    x = hp(x, 25, 2)
    # compression douce (RMS glissant) puis limiteur à saturation douce
    rms = np.sqrt(np.maximum(lp(x.mean(1) ** 2, 8), 0) + 1e-9)
    gr = np.minimum(1, (0.25 / rms) ** 0.18)
    x = x * gr[:, None]
    peak = np.abs(x).max()
    x = x / peak * 1.15
    x = np.tanh(x * 1.1) / np.tanh(1.1)
    return x / np.abs(x).max() * 10 ** (ceiling_db / 20)

L_ = int(DUR * SR)
music_r = reverb(music, 0.25, 2.8, 4000)
# automation : montée en tension acte par acte (dB), appliquée avant le master
pts_t = [0, 9.9, 10.0, 21.9, 22.0, 31.9, 32.0, 41.9, 42.0, 51.7, 52.0, 60.0, 62.0]
pts_db = [-7, -6, -6, -5, -4.5, -3, -2.5, -1.5, -2, 0, 0, 0, 0]
auto = 10 ** (np.interp(np.arange(N) / SR, pts_t, pts_db) / 20)[:, None]
music_r = music_r * auto; sfx = sfx * auto
mix = master(music_r * 0.95 + sfx)[:L_]
fade = np.ones(L_); fl = int(0.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
mix *= fade[:, None]
sfx_only = master(sfx)[:L_] * fade[:, None]
music_only = master(music_r)[:L_] * fade[:, None]
for name, x in [('ASVEL_HALLOWEEN_MIX', mix), ('ASVEL_HALLOWEEN_SFX_ONLY', sfx_only), ('ASVEL_HALLOWEEN_MUSIC', music_only)]:
    wavfile.write(f'public/audio/{name}.wav', SR, (x * 32767).astype(np.int16))
    print(name, 'peak dBFS %.2f' % (20 * np.log10(np.abs(x).max())), 'durée %.2f s' % (len(x) / SR))

# ---------------------------------------------------------------- version avec le thème fourni
# Si assets/audio/halloween_theme_user.mp3 existe (fourni par l'utilisateur, NON libre de droits),
# on produit un mix où il remplace la musique synthétisée. Les effets sonores restent identiques.
import os
THEME = 'assets/audio/halloween_theme_user.mp3'
if os.path.exists(THEME):
    import subprocess
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', THEME, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    th = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)
    OFFSET = 4.7          # t_trailer = t_theme + OFFSET : l'entrée complète (17,3 s) tombe à 22,0 s (Patty Mills)
    bed = np.zeros((N, 2)); i0 = int(OFFSET * SR)
    n = min(N - i0, len(th)); bed[i0:i0 + n] = th[:n]
    tt = np.arange(N) / SR
    # automation : piano discret sous le vent, plein à partir de Patty, coupure sèche au GAME DAY, fondu final
    g0 = sec(cue['gameDay'])
    pts_t = [0, 9.8, 10.0, 21.8, 22.0, 51.85, g0 - 0.02, g0 + 0.35, g0 + 0.9, 57.3, 59.3, 62]
    pts_db = [-5, -5, -3, -3, 0, 0, -60, -60, -1, -1, -60, -60]
    bed *= 10 ** (np.interp(tt, pts_t, pts_db) / 20)[:, None]
    # ducking sous les impacts (-6 dB, retour en 0,6 s)
    duck = np.zeros(N)
    for fr in cue['bigImpact'] + [cue['tadasRedBlast'], cue['faceoffText1'], cue['faceoffText2'], cue['brand']]:
        j = int(sec(fr) * SR); L = int(0.8 * SR)
        duck[j:j + L] = np.maximum(duck[j:j + L], np.linspace(1, 0, L)[: max(0, min(L, N - j))])
    bed *= (10 ** (-6 * duck / 20))[:, None]
    bed *= 10 ** (11 / 20)  # le thème (-21,6 LUFS) remonté pour porter le trailer
    theme_mix = master(bed + sfx)[:L_] * fade[:, None]
    wavfile.write('public/audio/ASVEL_HALLOWEEN_MIX_THEME.wav', SR, (theme_mix * 32767).astype(np.int16))
    print('ASVEL_HALLOWEEN_MIX_THEME peak dBFS %.2f' % (20 * np.log10(np.abs(theme_mix).max())))
