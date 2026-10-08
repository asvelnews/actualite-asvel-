"""Original trailer score for the ASVEL - Roanne teaser (procedural synthesis, 120 BPM, C minor).
Writes music.wav (stereo 48 kHz, 53 s: 5-s countdown + teaser). This is the ONLY audio of the teaser (clip sound muted)."""
import numpy as np, wave, sys
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
DUR = 53.5
N = int(SR * DUR)
rng = np.random.default_rng(7)
dry = np.zeros((N, 2))
wet_send = np.zeros((N, 2))   # goes to reverb

def t_(d): return np.arange(int(d * SR)) / SR
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x, axis=0)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x, axis=0)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x, axis=0)

OFF = 0.0  # time offset applied to every event (the teaser body starts after the 5-s countdown)
def add(sig, at, gain=1.0, pan=0.0, send=0.0):
    i = int((at + OFF) * SR)
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

# ===== COUNTDOWN 0-5 s (absolute): the music rises digit by digit =====
cd = drone(5.0)
cd *= np.linspace(0.25, 1.0, len(cd)) ** 1.5
add(cd, 0.0, 0.45)
for d in range(5):                       # one pulse per digit (5, 4, 3, 2, 1), louder each time
    g = 0.30 + 0.12 * d
    add(kick(0.45), d, g)
    add(boom(0.9, 52, 34), d, 0.20 + 0.08 * d)
    add(tom(80 + 10 * d, 0.6), d, 0.18 + 0.06 * d, send=0.4)
tt = 1.0; k = 0
while tt < 5.35:                         # ticking, eighths then sixteenths
    add(tick(), tt, 0.08 + 0.18 * (tt - 1) / 3.85, pan=(-0.3 if k % 2 == 0 else 0.3), send=0.2)
    tt += 0.25 if tt < 3.0 else 0.125; k += 1
tt = 3.0
while tt < 5.36:                         # snare build into the score
    x = (tt - 3.0) / 1.86
    add(snare(0.22), tt, 0.06 + 0.26 * x ** 1.6, send=0.25)
    tt += 0.125 if tt < 4.0 else 0.0625
add(riser(3.3, 150, 5000), 2.1, 0.30, send=0.3)
add(reverse_swell(0.8), 4.7, 0.35)

# ----- opening SFX (only place with sound effects): timer beeps + glass break -----
def beep(f, d):
    t = t_(d)
    env = np.minimum(1, t / 0.004) * np.minimum(1, (d - t) / 0.02)
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)) * env * 0.6
def glass(d=1.4):
    t = t_(d)
    out = hp(rng.standard_normal(len(t)), 1800) * np.exp(-t * 26) * 0.9       # the crack
    out += bp(rng.standard_normal(len(t)), 300, 3000) * np.exp(-t * 40) * 0.6  # body of the impact
    for _ in range(90):                                                         # falling shards
        at = rng.exponential(0.18); f = rng.uniform(2500, 9500)
        i = int(at * SR)
        if i >= len(t): continue
        tt = t[: len(t) - i]
        out[i:] += np.sin(2 * np.pi * f * tt + rng.random() * 6) * np.exp(-tt * rng.uniform(25, 60)) * rng.uniform(0.05, 0.22) * np.exp(-at * 2)
    return out
for k in range(5):
    add(beep(1000, 0.11), float(k), 0.32)          # 00:05 .. 00:01
add(beep(1000, 0.45), 5.0, 0.38)                   # 00:00
add(glass(), 5.5, 1.8, send=0.25)                 # the glass breaks, on the score impact

OFF = 5.5  # ---- everything below is in teaser-body time (body 0.0 = absolute 5.0 s) ----
# 0.00 HOOK impact (score card appears)
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

# ===== 8.0 DROP on the Find-the-shooter swish (body time; absolute = body + 5) =====
add(boom(2.0), 8.0, 1.0)
add(braam(36, 1.8), 8.0, 0.5, send=0.3)
add(noise_hit(1.0, 80, 6000, 5), 8.0, 0.35, send=0.6)

# groove body 8 -> 38 (15 bars of 2 s), then a half-bar fill to the message at 39
prog = [([48, 51, 55, 60], 36), ([44, 48, 51, 56], 32), ([51, 55, 58, 63], 39), ([46, 50, 53, 58], 34)]
pat = [0, 0, 12, 0, 0, 0, 7, 0, 0, 0, 12, 0, 3, 0, 7, 0]
for bi in range(15):
    bs = 8.0 + 2.0 * bi
    ch, root = prog[bi % 4] if bi < 14 else ([43, 47, 50, 55], 31)
    add(pad(ch, 2.1, 950 + bi * 70), bs, 0.28 + bi * 0.006, send=0.35)
    for i in range(16):
        add(bass_note(root + pat[i], 0.14), bs + i * B / 4, 0.42 if i % 4 == 0 else 0.28)
# phase 1 shots (body 8-24.5): kick/snare + 8th hats; phase 2 finishes (24.5-35.5): 16th hats + extra kicks;
# phase 3 final dunk (35.5-38): full kit
for b in np.arange(8.0, 38.0, B):
    beat = int(round((b - 8.0) / B)) % 4
    if beat in (0, 2): add(kick(), b, 0.75)
    if beat in (1, 3): add(snare(), b, 0.5 if b < 24.5 else 0.56, send=0.35)
    if b >= 10.0: add(hat(), b + B / 2, 0.11, pan=0.3)
    if b >= 24.5:
        add(hat(), b + B / 4, 0.07, pan=-0.3)
        if beat == 2: add(kick(), b + 0.25, 0.5)
    if b >= 35.5:
        add(hat(), b + 3 * B / 4, 0.07, pan=-0.2)
        if beat == 0: add(kick(), b + 0.25, 0.45)
# accents on every basket, light pulses on the cuts (all in body time)
for at in (10.75, 13.05, 16.3, 20.05, 23.7, 25.95, 29.5, 31.05, 34.0):
    add(boom(1.4, 60, 32), at, 0.5)
    add(noise_hit(0.7, 150, 7000, 7), at, 0.2, send=0.6)
for at in (8.5, 11.0, 13.5, 17.0, 20.5, 24.5, 27.0, 30.0, 31.5):
    add(boom(0.8, 55, 38), at, 0.26)
add(riser(2.0, 300, 6000), 34.8, 0.22, send=0.3)          # lift into the final dunk
add(boom(2.0, 64, 30), 36.8, 0.85)                         # the dunk (abs 41.8)
add(braam(36, 1.6, 0.9), 36.8, 0.35, send=0.5)
add(noise_hit(1.0, 80, 7000, 5), 36.8, 0.3, send=0.7)
for i, tt in enumerate(np.arange(38.0, 39.0, 0.125)):      # tom fill into the message
    add(tom(150 - i * 8, 0.45), tt, 0.35 + i * 0.03, pan=(-0.4 + 0.1 * i), send=0.3)

# ===== 39.0 MESSAGE: pull back =====
add(boom(2.6, 58, 28), 39.0, 0.9)
add(braam(36, 2.6, 0.5), 39.0, 0.35, send=0.5)
add(pad([48, 51, 55, 60, 63], 2.9, 700), 39.0, 0.34, send=0.5)
for b in np.arange(39.0, 41.6, 1.0):
    add(kick(0.4), b, 0.45)
    add(kick(0.35), b + 0.22, 0.28)
tt = 40.0; k = 0
while tt < 41.8:
    add(tick(), tt, 0.14 + 0.1 * (tt - 40) / 1.8, pan=(-0.3 if k % 2 == 0 else 0.3))
    tt += B / 2; k += 1
add(riser(1.8, 150, 5000), 40.05, 0.30, send=0.3)
add(reverse_swell(0.8), 41.15, 0.4)

# ===== 42.0 POSTER (abs 47-53) =====
add(boom(3.5, 64, 26), 42.0, 1.0)
add(braam(36, 3.4, 1.0), 42.0, 0.6, send=0.45)
add(noise_hit(1.6, 60, 6000, 3.5), 42.0, 0.35, send=0.7)
add(pad([36, 43, 48, 51, 55], 4.9, 600), 42.1, 0.30, send=0.4)
for b in np.arange(43.0, 46.9, 0.5):
    add(bass_note(24, 0.4), b, 0.30)
    add(tick(), b + 0.25, 0.08)
add(boom(1.6, 62, 30), 47.0, 1.0)
add(braam(36, 1.5, 0.9), 47.0, 0.5, send=0.6)
add(noise_hit(1.2, 80, 6000, 4), 47.0, 0.3, send=0.8)

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
duck(5.40, 5.5, 0.35)    # suck-out before the score impact
duck(13.36, 13.5, 0.25)
duck(47.38, 47.5, 0.25)
# end fade
f = int(0.35 * SR)
mix[-f:] *= np.linspace(1, 0, f)[:, None]
mix = np.tanh(mix * 0.9) / np.tanh(0.9)
mix *= 0.89 / np.abs(mix).max()
out = (mix * 32767).astype(np.int16)
w = wave.open(sys.argv[1] if len(sys.argv) > 1 else 'music.wav', 'wb')
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes()); w.close()
print('ok', mix.shape)
