"""Original trailer score for the ASVEL - Roanne teaser (procedural synthesis, 120 BPM, C minor).
Writes music.wav (stereo 48 kHz, 28 s). This is the ONLY audio of the teaser (clip sound muted)."""
import numpy as np, wave, sys
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
DUR = 28.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
dry = np.zeros((N, 2))
wet_send = np.zeros((N, 2))   # goes to reverb

def t_(d): return np.arange(int(d * SR)) / SR
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x, axis=0)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x, axis=0)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x, axis=0)

def add(sig, at, gain=1.0, pan=0.0, send=0.0):
    i = int(at * SR)
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], 1)
    j = min(N, i + len(sig))
    if j <= i: return
    dry[i:j] += sig[:j - i] * gain
    wet_send[i:j] += sig[:j - i] * gain * send

def saw(f, t, detune=0.0):
    ph = (f * (1 + detune)) * t
    return 2 * (ph - np.floor(ph + 0.5))

# ---------------- instruments ----------------
def boom(d=3.0, f0=62, f1=27):
    t = t_(d)
    f = f1 + (f0 - f1) * np.exp(-t * 5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.exp(-t * 1.6) * (1 - np.exp(-t * 400))
    s = np.sin(ph) * env
    s += 0.5 * np.tanh(3 * np.sin(ph)) * env * np.exp(-t * 3)
    return s

def noise_hit(d=1.2, lo=80, hi=6000, dec=6):
    t = t_(d)
    n = rng.standard_normal(len(t))
    return bp(n, lo, hi) * np.exp(-t * dec) * (1 - np.exp(-t * 800))

def braam(root=36, d=2.6, bright=1.0):
    t = t_(d)
    notes = [root - 12, root, root + 7, root + 12, root + 15]
    s = np.zeros(len(t))
    for k, m in enumerate(notes):
        for dt in (-0.006, 0.0, 0.007):
            s += saw(hz(m), t, dt) * (0.9 if k < 2 else 0.5)
    s = np.tanh(s * 0.35)
    # filter sweep closing
    out = np.zeros(len(t)); seg = int(0.05 * SR)
    for a in range(0, len(t), seg):
        fc = 180 + 1400 * bright * np.exp(-a / SR * 2.2)
        out[a:a + seg] = lp(s[max(0, a - 2000):a + seg], fc, 2)[-len(s[a:a + seg]):]
    env = np.exp(-t * 1.1) * (1 - np.exp(-t * 60))
    return out * env

def kick(d=0.45):
    t = t_(d)
    f = 42 + 110 * np.exp(-t * 28)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    click = hp(rng.standard_normal(len(t)), 2000) * np.exp(-t * 300) * 0.25
    return np.tanh(1.6 * s) + click

def snare(d=0.5):
    t = t_(d)
    n = bp(rng.standard_normal(len(t)), 250, 7000) * np.exp(-t * 14)
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 25) * 0.6
    return n + tone

def tom(f0=120, d=0.6):
    t = t_(d)
    f = f0 * (0.75 + 0.25 * np.exp(-t * 10))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)
    s += 0.2 * bp(rng.standard_normal(len(t)), 100, 1500) * np.exp(-t * 30)
    return np.tanh(1.3 * s)

def tick(d=0.03):
    t = t_(d)
    return hp(rng.standard_normal(len(t)), 5000) * np.exp(-t * 220)

def hat(d=0.06, open_=False):
    t = t_(d if not open_ else 0.25)
    return hp(rng.standard_normal(len(t)), 8000) * np.exp(-t * (90 if not open_ else 18))

def riser(d, f0=200, f1=4000):
    t = t_(d)
    n = rng.standard_normal(len(t))
    out = np.zeros(len(t)); seg = int(0.02 * SR)
    for a in range(0, len(t), seg):
        x = a / len(t)
        fc = f0 * (f1 / f0) ** (x ** 1.5)
        chunk = n[max(0, a - 1500):a + seg]
        out[a:a + seg] = bp(chunk, fc * 0.7, min(fc * 1.4, SR / 2 - 100))[-len(n[a:a + seg]):]
    env = (t / d) ** 2.2
    tone_f = 110 * 2 ** (2.0 * (t / d) ** 1.4)
    tone = np.sin(2 * np.pi * np.cumsum(tone_f) / SR) * 0.35 + np.sin(2 * np.pi * np.cumsum(tone_f * 1.5) / SR) * 0.2
    return (out * 1.4 + tone) * env

def reverse_swell(d=0.9):
    t = t_(d)
    s = hp(rng.standard_normal(len(t)), 400) * np.exp(-t * 5)
    s = lp(s, 5000)
    return s[::-1] * 0.8

def pad(chord, d, cutoff=900):
    t = t_(d)
    s = np.zeros(len(t))
    for m in chord:
        for dt in (-0.004, 0.0, 0.005):
            s += saw(hz(m), t + rng.random(), dt)
    s = lp(s / (3 * len(chord)), cutoff, 2)
    env = np.minimum(1, t / 0.25) * np.minimum(1, (d - t) / 0.15)
    return s * env

def bass_note(m, d):
    t = t_(d)
    s = saw(hz(m), t) * 0.7 + np.sin(2 * np.pi * hz(m) * t) * 0.6
    fenv = 250 + 900 * np.exp(-t * 30)
    s = lp(s, 700) * np.exp(-t * 6) * (1 - np.exp(-t * 600))
    return np.tanh(1.5 * s)

def drone(d):
    t = t_(d)
    s = (saw(hz(24), t) + saw(hz(24), t, 0.004) + 0.6 * saw(hz(31), t, -0.003)) / 2.6
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.35 * t)
    out = lp(s, 160, 2) * (0.6 + 0.4 * lfo)
    out += 0.5 * np.sin(2 * np.pi * hz(36) * t)
    env = np.minimum(1, t / 1.5)
    return out * env

# ---------------- arrangement ----------------
B = 0.5  # beat (120 BPM)

# 0.00 HOOK impact
add(boom(3.2), 0.0, 1.0)
add(braam(36, 2.6), 0.0, 0.55, send=0.35)
add(noise_hit(1.5, 60, 4000, 4), 0.0, 0.35, send=0.5)

# drone 0.4 -> 8.0 (tension bed), swelling
dr = drone(7.4)
dr *= np.linspace(0.5, 1.0, len(dr))[:, None].squeeze()
dr[-int(0.12 * SR):] *= np.linspace(1, 0, int(0.12 * SR))
add(dr, 0.4, 0.30)

# card hits
for at, g in ((2.5, 0.7), (3.25, 0.8)):
    add(tom(70, 0.9), at, g * 0.75, send=0.4)
    add(boom(1.4, 55, 32), at, 0.38)
add(boom(2.6, 60, 28), 4.0, 0.7)
add(braam(36, 2.2, 0.6), 4.0, 0.35, send=0.4)
add(noise_hit(0.9, 100, 3000, 6), 4.0, 0.2, send=0.6)

# ticking clock 2.5 -> 7.8 (eighths), rising
k = 0
tt = 2.5
while tt < 7.75:
    g = 0.10 + 0.22 * (tt - 2.5) / 5.25
    add(tick(), tt, g * (1.0 if k % 2 == 0 else 0.6), pan=(-0.35 if k % 2 == 0 else 0.35), send=0.2)
    tt += B / 2; k += 1

# heartbeat 5.0 -> 7.5
for b in np.arange(5.0, 7.6, 1.0):
    add(kick(0.4), b, 0.45)
    add(kick(0.35), b + 0.22, 0.28)

# snare build 6.0 -> 7.8
tt = 6.0
while tt < 7.78:
    x = (tt - 6.0) / 1.78
    add(snare(0.25), tt, 0.08 + 0.3 * x ** 1.5, send=0.25)
    tt += 0.125 if tt < 7.0 else 0.0625
add(riser(2.6), 5.2, 0.32, send=0.3)
add(reverse_swell(0.9), 7.1, 0.35)

# ===== 8.0 DROP on the Mills swish =====
add(boom(2.0), 8.0, 1.0)
add(braam(36, 1.8), 8.0, 0.5, send=0.3)
add(noise_hit(1.0, 80, 6000, 5), 8.0, 0.35, send=0.6)

# groove 8 -> 20 (6 bars of 2 s)
chords = [([48, 51, 55, 60], 36), ([44, 48, 51, 56], 32), ([51, 55, 58, 63], 39),
          ([46, 50, 53, 58], 34), ([48, 51, 55, 60], 36), ([43, 47, 50, 55], 31)]
pat = [0, 0, 12, 0, 0, 0, 7, 0, 0, 0, 12, 0, 3, 0, 7, 0]
for bi, (ch, root) in enumerate(chords):
    bs = 8.0 + 2.0 * bi
    add(pad(ch, 2.1, 1000 + bi * 160), bs, 0.30 + bi * 0.012, send=0.35)
    for i in range(16):
        add(bass_note(root + pat[i], 0.14), bs + i * B / 4, 0.42 if i % 4 == 0 else 0.28)
for b in np.arange(8.0, 20.0, B):
    beat_in_bar = int(round((b - 8.0) / B)) % 4
    if b >= 19.0: break                      # tom fill takes the last bar half
    if beat_in_bar in (0, 2): add(kick(), b, 0.75)
    if beat_in_bar in (1, 3): add(snare(), b, 0.5, send=0.35)
    if b >= 11.0:
        add(hat(), b + B / 2, 0.12, pan=0.3)
    if b >= 14.5:
        add(hat(), b + B / 4, 0.07, pan=-0.3)
        if beat_in_bar == 2: add(kick(), b + 0.25, 0.5)
# musical accents follow the edit: baskets get a hit, cuts a light pulse
for at in (10.55, 14.08, 15.55, 18.6):
    add(boom(1.4, 60, 32), at, 0.55)
    add(noise_hit(0.7, 150, 7000, 7), at, 0.22, send=0.6)
for at in (11.1, 13.5, 14.5, 16.1, 17.1):
    add(boom(0.8, 55, 38), at, 0.28)
# tom fill + riser into the message
for i, tt in enumerate(np.arange(19.0, 20.0, 0.125)):
    add(tom(150 - i * 8, 0.45), tt, 0.35 + i * 0.03, pan=(-0.4 + 0.1 * i), send=0.3)
add(riser(1.4, 400, 6000), 18.6, 0.22, send=0.3)

# ===== 20.0 MESSAGE: pull back =====
add(boom(2.6, 58, 28), 20.0, 0.9)
add(braam(36, 2.6, 0.5), 20.0, 0.35, send=0.5)
add(pad([48, 51, 55, 60, 63], 2.9, 700), 20.0, 0.34, send=0.5)
for b in np.arange(20.0, 22.6, 1.0):
    add(kick(0.4), b, 0.45)
    add(kick(0.35), b + 0.22, 0.28)
tt = 21.0; k = 0
while tt < 22.8:
    add(tick(), tt, 0.14 + 0.1 * (tt - 21) / 1.8, pan=(-0.3 if k % 2 == 0 else 0.3))
    tt += B / 2; k += 1
add(riser(1.8, 150, 5000), 21.05, 0.30, send=0.3)
add(reverse_swell(0.8), 22.15, 0.4)

# ===== 23.0 RENDEZ-VOUS =====
add(boom(3.5, 64, 26), 23.0, 1.0)
add(braam(36, 3.4, 1.0), 23.0, 0.6, send=0.45)
add(noise_hit(1.6, 60, 6000, 3.5), 23.0, 0.35, send=0.7)
add(pad([36, 43, 48, 51, 55], 3.6, 600), 23.1, 0.30, send=0.4)
for b in np.arange(24.0, 26.4, 0.5):
    add(bass_note(24, 0.4), b, 0.30)
    add(tick(), b + 0.25, 0.08)
# final button + short resonance
add(boom(1.6, 62, 30), 26.5, 1.0)
add(braam(36, 1.5, 0.9), 26.5, 0.5, send=0.6)
add(noise_hit(1.2, 80, 6000, 4), 26.5, 0.3, send=0.8)

# ---------------- reverb + master ----------------
ir_len = int(2.2 * SR)
ti = np.arange(ir_len) / SR
ir = np.stack([rng.standard_normal(ir_len), rng.standard_normal(ir_len)], 1) * np.exp(-ti * 3.0)[:, None]
ir = lp(ir, 6000)
ir /= np.sqrt((ir ** 2).sum(0))
wet = np.stack([fftconvolve(wet_send[:, c], ir[:, c])[:N] for c in range(2)], 1)
mix = dry + 0.55 * wet
mix = hp(mix, 25)
# silence gaps before drops (dramatic suck-out), keep reverse swells
def duck(a, b, depth):
    i, j = int(a * SR), int(b * SR)
    ramp = np.ones(j - i) * depth
    mix[i:j] *= ramp[:, None]
duck(7.86, 8.0, 0.25)
duck(22.88, 23.0, 0.25)
# end fade
f = int(0.35 * SR)
mix[-f:] *= np.linspace(1, 0, f)[:, None]
mix = np.tanh(mix * 0.9) / np.tanh(0.9)
mix *= 0.89 / np.abs(mix).max()
out = (mix * 32767).astype(np.int16)
w = wave.open(sys.argv[1] if len(sys.argv) > 1 else 'music.wav', 'wb')
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes()); w.close()
print('ok', mix.shape)
