"""Bande-son du teaser Real Madrid vs LDLC ASVEL (50 s).
Musique originale entièrement synthétisée (oscillateurs, enveloppes, filtres) :
aucun sample externe, aucun droit tiers, aucune IA générative.
Durée 60 s. Sortie : music_sfx.wav (mix complet) + sfx_only.wav (effets seuls).
Tempo 120 BPM : tous les repères de montage tombent sur la grille de 0,5 s."""
import sys, numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
DUR = 60.0
N = int(SR * DUR)
rng = np.random.default_rng(7)

def buf(): return np.zeros((N, 2), np.float32)
music, sfx = buf(), buf()

def t_(d): return np.arange(int(d * SR)) / SR
def midi(m): return 440.0 * 2 ** ((m - 69) / 12)

def add(bus, start, mono, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N: return
    x = mono[: N - i] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    bus[i:i + len(x), 0] += x * l * 1.414
    bus[i:i + len(x), 1] += x * r * 1.414

def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR / 2 - 100) / (SR / 2), 'low'); return signal.lfilter(b, a, x)
def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band'); return signal.lfilter(b, a, x)

def env_adsr(n, a, d, s, r, total):
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4), np.where(t < a + d, 1 - (1 - s) * (t - a) / max(d, 1e-4), s))
    rel = total - r
    e = np.where(t > rel, e * np.clip(1 - (t - rel) / max(r, 1e-4), 0, 1), e)
    return e

def saw(f, d, detune=0.0):
    t = t_(d); out = 0
    for k in (-detune, 0, detune):
        ph = rng.random()
        out = out + 2 * ((t * f * (1 + k) + ph) % 1) - 1
    return out / 3

# ---------- instruments ----------
def heartbeat(gain=1.0):
    def thump(d=0.22, f0=70):
        t = t_(d); f = f0 * np.exp(-t * 6)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22)
    x = np.zeros(int(0.5 * SR)); a = thump(); b = thump(f0=60) * 0.7
    x[:len(a)] += a; o = int(0.16 * SR); x[o:o + len(b)] += b
    return lp(x, 300) * gain

def beep(f=1046.5, d=0.16):
    t = t_(d); x = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * f * t) * 0.5
    return lp(x, 4000) * env_adsr(len(t), 0.003, 0.0, 1, 0.03, d)

def buzzer(d=0.95):
    t = t_(d); x = 0
    for f in (196, 233):
        x = x + 2 * ((t * f) % 1) - 1
    x = bp(x, 150, 3000) * env_adsr(len(t), 0.005, 0, 1, 0.08, d)
    return np.tanh(x * 1.8)

def impact(d=2.5, f0=90, f1=32, noise=0.5):
    t = t_(d); f = f1 + (f0 - f1) * np.exp(-t * 9)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    nz = lp(rng.standard_normal(len(t)), 1800) * np.exp(-t * 14) * noise
    body = lp(rng.standard_normal(len(t)), 220) * np.exp(-t * 4) * 0.8
    return np.tanh((sub + nz + body) * 1.3)

def tom(f0=110, d=0.6, gain=1.0):
    t = t_(d); f = f0 * (1 + 0.6 * np.exp(-t * 30))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    x += lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 40) * 0.5
    return np.tanh(x * 1.5) * gain

def whoosh(d=0.6, lo=300, hi=4000, gain=0.35):
    t = t_(d); nz = rng.standard_normal(len(t)); out = np.zeros(len(t))
    seg = 1024
    for i in range(0, len(t), seg):
        p = i / len(t); fc = lo + (hi - lo) * np.sin(np.pi * p)
        out[i:i + seg] = bp(nz[i:i + seg], fc * 0.6, min(fc * 1.4, 20000), 1)
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return out * e * gain

def riser(d, gain=0.4):
    t = t_(d); p = t / d
    nz = rng.standard_normal(len(t)); out = np.zeros(len(t)); seg = 2048
    for i in range(0, len(t), seg):
        fc = 200 + 7000 * (i / len(t)) ** 2
        out[i:i + seg] = bp(nz[i:i + seg], fc * 0.7, min(fc * 1.3, 20000), 1)
    tone = np.sin(2 * np.pi * np.cumsum(110 * 2 ** (p * 2)) / SR) * 0.25
    return (out + tone) * p ** 2 * gain

def piano(m, d=2.5, vel=1.0):
    t = t_(d); f = midi(m); x = 0
    for k, amp in enumerate((1, 0.45, 0.25, 0.12, 0.06), 1):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)
        x = x + amp * np.sin(2 * np.pi * fk * t) * np.exp(-t * (1.6 + k * 0.9))
    x *= (1 - np.exp(-t * 600))
    return x * vel * 0.35

def pad(notes, d, fc=900, gain=0.12):
    x = sum(saw(midi(m), d, 0.004) for m in notes)
    x = lp(x, fc, 2) * env_adsr(int(d * SR), 0.6, 0, 1, 0.8, d)
    return x * gain

def strings_ostinato(m, start, end, step=0.25, gain=0.12, fc0=500, fc1=2500):
    t = start
    while t < end - 1e-6:
        p = (t - start) / max(end - start, 1e-6)
        x = saw(midi(m), step * 0.95, 0.003) + saw(midi(m + 12), step * 0.95, 0.003) * 0.4
        x = lp(x, fc0 + (fc1 - fc0) * p) * env_adsr(int(step * 0.95 * SR), 0.01, 0.05, 0.6, 0.05, step * 0.95)
        add(music, t, x, gain * (0.5 + 0.5 * p))
        t += step

def brass_stab(notes, d=0.9, gain=0.22):
    x = sum(saw(midi(m), d, 0.006) for m in notes)
    e = env_adsr(int(d * SR), 0.02, 0.2, 0.5, 0.3, d)
    return np.tanh(lp(x, 2200) * e * 1.4) * gain

def reverb(x, secs=2.6, mix=0.25):
    t = t_(secs); ir = rng.standard_normal((len(t), 2)) * np.exp(-t * 3.2)[:, None]
    ir = lp(ir.T, 6000).T
    wet = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    wet /= (np.abs(wet).max() + 1e-9) / (np.abs(x).max() + 1e-9)
    return x * (1 - mix) + wet * mix

Dm, Bb, F, C, A = [38, 50, 53, 57], [34, 50, 53, 58], [41, 48, 53, 57], [36, 48, 52, 55], [33, 49, 52, 57]

# ================= SCÈNE 1 : 0–7 =================
hb_times = [0.25, 1.0, 1.75, 2.45, 3.1, 3.7, 4.25, 4.75]
for i, ht in enumerate(hb_times):
    add(sfx, ht, heartbeat(0.55 + 0.06 * i))
for i, bt in enumerate([1.0, 1.8, 2.6, 3.4, 4.2]):
    add(sfx, bt, beep(), 0.10 + 0.05 * i)
add(music, 1.0, riser(4.0, 0.18))
add(sfx, 5.0, buzzer(), 0.32)
add(sfx, 5.55, whoosh(0.45, 400, 6000, 0.3))
add(sfx, 6.0, impact(2.8), 0.75)

# ================= SCÈNE 2–3 : 7–20 montée =================
add(music, 6.0, pad(Dm, 8.0, 500, 0.10))
for k, ch in enumerate([Bb, F, C]):
    add(music, 14.0 + 2 * k, pad(ch, 2.2, 700 + 200 * k, 0.11))
add(music, 6.0, lp(saw(midi(26), 13.5, 0.002), 160) * env_adsr(int(13.5 * SR), 1.5, 0, 1, 1.0, 13.5), 0.22)
strings_ostinato(50, 7.0, 14.0, 0.25, 0.07, 400, 1400)
strings_ostinato(50, 14.0, 18.5, 0.25, 0.10, 1400, 2600)
for bt in np.arange(10.0, 18.5, 1.0):
    add(music, bt, tom(70, 0.8, 0.35 + 0.03 * (bt - 10)))
for bt in [12.0, 13.0, 13.5]:
    add(music, bt, tom(95, 0.5, 0.25))
add(sfx, 7.0, whoosh(0.5, 300, 3000, 0.15))
add(sfx, 10.0, whoosh(0.5, 300, 3000, 0.15))
add(sfx, 12.0, whoosh(0.5, 300, 3000, 0.15))
add(music, 12.0, riser(2.0, 0.15))
add(sfx, 14.0, impact(1.8, 80, 35, 0.3), 0.45)
add(sfx, 15.5, impact(1.0, 120, 50, 0.4), 0.30)
add(sfx, 16.5, impact(1.0, 120, 50, 0.4), 0.30)
add(sfx, 18.5, whoosh(0.5, 2000, 300, 0.15))

# ================= SCÈNE 4–5 : 20–34 émotion (piano) =================
prog = [(Dm, [62, 65, 69, 65]), (Bb, [62, 65, 70, 65]), (F, [60, 65, 69, 65]), (C, [60, 64, 67, 64])]
t0 = 20.0
for bar in range(7):          # 7 mesures de 2 s = 20 → 34
    ch, arp = prog[bar % 4]
    add(music, t0 + 2 * bar, pad(ch, 2.3, 650, 0.07 if bar < 5 else 0.10))
    add(music, t0 + 2 * bar, piano(ch[0] + 12, 3.0, 0.9))
    for k, m in enumerate(arp):
        add(music, t0 + 2 * bar + 0.5 * k, piano(m, 2.2, 0.55 + (0.15 if k == 0 else 0)), pan=(-0.3 + 0.2 * k))
strings_ostinato(57, 30.0, 34.0, 0.25, 0.06, 600, 1800)
add(sfx, 20.0, whoosh(0.7, 200, 1500, 0.12))
add(sfx, 27.0, whoosh(0.7, 200, 1500, 0.12))
add(sfx, 32.0, whoosh(0.4, 500, 5000, 0.18))

# ================= SCÈNE 6 : 34–43 suspense =================
add(sfx, 34.25, impact(2.2, 85, 30, 0.5), 0.6)
for ht in [35.1, 35.85, 36.6]:
    add(sfx, ht, heartbeat(0.75))
add(sfx, 37.0, impact(1.5, 110, 40, 0.3), 0.35)
add(music, 37.0, lp(saw(midi(26), 4.8, 0.003), 200) * np.linspace(0.2, 1, int(4.8 * SR)), 0.25)
add(music, 37.0, riser(4.8, 0.32))
strings_ostinato(50, 39.0, 41.75, 0.125, 0.08, 800, 3500)
for i, bt in enumerate(np.arange(40.0, 41.75, 0.125)):
    add(music, bt, tom(90 + 2 * i, 0.3, 0.12 + 0.02 * i))
for bt in [39.25, 39.75, 40.25]:
    add(sfx, bt, impact(0.8, 100, 45, 0.2), 0.18)

# ================= 42–43 : impact VICTOIRE, la musique explose puis s'éteint =================
add(sfx, 42.0, impact(3.5, 110, 28, 0.7), 1.0)
add(music, 42.0, brass_stab(Dm + [62], 1.4, 0.30))
add(music, 42.0, tom(65, 0.9, 0.6)); add(music, 42.5, tom(90, 0.6, 0.4))

# ---------- bruitages du final : pas, foule ----------
def step(gain=1.0, bright=1.0):
    t = t_(0.25)
    thud = np.sin(2 * np.pi * np.cumsum(95 * (1 + 0.5 * np.exp(-t * 60))) / SR) * np.exp(-t * 28)
    click = hp(rng.standard_normal(len(t)), 1500) * np.exp(-t * 90) * 0.35 * bright
    return (thud + click) * gain

def squeak(gain=0.08):
    d = rng.uniform(0.05, 0.09); t = t_(d); f = rng.uniform(1800, 2600) * (1 + 0.25 * t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) * gain

def smooth_noise(n, rate):
    k = max(2, int(n / SR * rate)); pts = rng.standard_normal(k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)

def crowd(d):
    """Ambiance de salle : rumeur large bande modulée + applaudissements (bruit filtré)."""
    n = int(d * SR); out = np.zeros(n)
    for fc in (300, 520, 850, 1300, 2000, 3000):
        layer = bp(rng.standard_normal(n), fc * 0.7, fc * 1.4, 2)
        out += layer * (0.6 + 0.4 * np.tanh(smooth_noise(n, 2.0))) / np.sqrt(fc / 300)
    claps = np.zeros(n)
    for c in rng.uniform(0, d, int(d * 120)):
        i = int(c * SR); L = int(0.012 * SR)
        if i + L < n: claps[i:i + L] += rng.standard_normal(L) * np.exp(-np.arange(L) / (0.003 * SR)) * rng.uniform(0.2, 1)
    out += hp(claps, 1200) * 0.6
    return out / (np.abs(out).max() + 1e-9)

corridor = buf()
# 43–50.5 : pas de cinq joueurs dans le couloir, de plus en plus proches
for p in range(5):
    tt = 43.15 + rng.uniform(0, 0.5); per = rng.uniform(0.52, 0.6)
    while tt < 50.6:
        near = min(1.0, max(0.0, (tt - 43.0) / 7.0))
        add(corridor, tt, step(0.18 + 0.32 * near, 0.6 + 0.6 * near), pan=(-0.6 + 0.3 * p))
        if rng.random() < 0.12: add(corridor, tt + 0.05, squeak(0.05 + 0.05 * near), pan=(-0.6 + 0.3 * p))
        tt += per + rng.uniform(-0.03, 0.03)
corridor = reverb(corridor, 1.9, 0.45)          # résonance du tunnel
sfx += corridor

# foule : monte de 47 à 53, se tait presque sur le silence de 53 s, revient à 55
cr = crowd(13.0); env = np.zeros(len(cr)); tl = np.arange(len(cr)) / SR + 47.0
env = np.interp(tl, [47, 48, 52.9, 53.0, 54.9, 55.15, 56.0, 59.0, 60], [0, 0.10, 0.42, 0.10, 0.12, 0.35, 0.45, 0.30, 0])
add(sfx, 47.0, cr * env)

# 43–47 : musique presque silencieuse (bourdon grave + nappe lointaine)
add(music, 43.0, lp(saw(midi(26), 4.6, 0.002), 140) * env_adsr(int(4.6 * SR), 1.0, 0, 1, 0.6, 4.6), 0.10)
add(music, 43.5, pad([62, 65, 69], 4.0, 600, 0.03))
# 47–53 : l'entrée — montée collective
add(sfx, 47.0, whoosh(1.0, 200, 2500, 0.18))
add(music, 47.0, pad(Dm, 2.0, 700, 0.08)); add(music, 49.0, pad(Bb, 2.0, 900, 0.09)); add(music, 51.0, pad(C, 2.0, 1200, 0.10))
add(music, 47.0, lp(saw(midi(26), 6.0, 0.003), 220) * np.linspace(0.3, 1, int(6.0 * SR)), 0.22)
strings_ostinato(50, 47.0, 53.0, 0.25, 0.10, 600, 3000)
for i, bt in enumerate(np.arange(48.0, 53.0, 0.5)):
    add(music, bt, tom(70 if i % 2 == 0 else 95, 0.7, 0.25 + 0.03 * i))
for i, bt in enumerate(np.arange(52.0, 53.0, 0.125)):
    add(music, bt, tom(100, 0.25, 0.15 + 0.03 * i))
add(music, 50.0, riser(3.0, 0.30))
# 53–56 : face-à-face (coupure, puis impacts sur chaque phrase)
add(sfx, 53.25, impact(1.8, 95, 32, 0.4), 0.55)
add(sfx, 54.2, impact(1.6, 110, 40, 0.35), 0.5)
add(music, 54.2, lp(saw(midi(26), 1.0, 0.003), 220) * np.linspace(0.3, 1, int(1.0 * SR)), 0.2)
add(music, 54.6, riser(0.6, 0.25))
add(sfx, 55.15, impact(2.0, 120, 34, 0.6), 0.8)
add(music, 55.15, brass_stab(Bb + [62], 0.8, 0.26)); add(music, 55.15, tom(65, 0.8, 0.55))
add(music, 55.5, tom(90, 0.5, 0.45)); add(music, 55.75, tom(90, 0.5, 0.5))
# 56–60 : révélation
add(sfx, 55.92, whoosh(0.25, 800, 8000, 0.25))
add(sfx, 56.0, impact(3.5, 110, 26, 0.8), 1.0)
add(music, 56.0, brass_stab(Dm + [62, 69], 1.8, 0.30))
add(music, 56.0, pad(Dm, 4.0, 1300, 0.10))
pattern = [0, 0.75, 1.0, 1.5, 1.75]
for bar_start in [56.0, 58.0]:
    for p in pattern:
        add(music, bar_start + p, tom(65 if p in (0, 1.0) else 90, 0.7, 0.5))
strings_ostinato(50, 56.0, 59.0, 0.125, 0.08, 2500, 3500)
add(music, 58.0, brass_stab(A + [61, 64], 1.6, 0.26))
add(sfx, 58.0, impact(2.0, 90, 30, 0.5), 0.6)

# ---------- mix ----------
cut = int(34.0 * SR)
music = reverb(music, 2.6, 0.28)
music[cut:int(34.25 * SR)] = 0                       # arrêt brutal à 34 s
music[cut:int(37 * SR)] *= 0                         # silence dramatique (la reverb ne déborde pas)
music[int(53.0 * SR):int(53.25 * SR)] = 0            # la musique s'arrête une fraction de seconde
music[int(53.25 * SR):int(54.2 * SR)] *= 0.25
sfx = reverb(sfx, 1.4, 0.12)
fade = np.ones(N); fs = int(59.0 * SR); fade[fs:] = np.linspace(1, 0, N - fs) ** 1.5
mix = (music * 0.9 + sfx) * fade[:, None]
sfx_out = sfx * fade[:, None]
def master(x):
    x = np.tanh(x * 1.2) / np.tanh(1.2)
    return (x / (np.abs(x).max() + 1e-9) * 0.89).astype(np.float32)
wavfile.write(sys.argv[1] if len(sys.argv) > 1 else 'music_sfx.wav', SR, master(mix))
wavfile.write(sys.argv[2] if len(sys.argv) > 2 else 'sfx_only.wav', SR, master(sfx_out))
print('ok')
