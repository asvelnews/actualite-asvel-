"""Audio for the ASVEL - Etoile Rouge trailer, in two separate stems so the PROVISIONAL music can be swapped
for the user's track without touching the effects:
  aud/sfx.wav   : hum, beeps, buzzer, glass, sub impacts (kept in the final)
  aud/music.wav : provisional procedural score (to be replaced by the supplied music)
  aud/mix.wav   : music (ducked where needed) + sfx
No original clip audio is used anywhere."""
import os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ['TRAILER_DUR'] = '53.64'
import synth_lib as L
from synth_lib import *                       # SR, N, add, boom, braam, kick, snare, tom, tick, hat, riser, pad, ...
from scipy.signal import fftconvolve

def render_bus():
    ir_len = int(2.2 * SR); ti = np.arange(ir_len) / SR
    ir = np.stack([L.rng.standard_normal(ir_len), L.rng.standard_normal(ir_len)], 1) * np.exp(-ti * 3.0)[:, None]
    ir = lp(ir, 6000); ir /= np.sqrt((ir ** 2).sum(0))
    wet = np.stack([fftconvolve(L.wet_send[:, c], ir[:, c])[:N] for c in range(2)], 1)
    out = hp(L.dry + 0.5 * wet, 25)
    L.dry[:] = 0; L.wet_send[:] = 0
    return out

B = 0.5
# =============================== SFX STEM ===============================
t = t_(5.0)                                                     # faint electric hum under the countdown
hum = (np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 100 * t))
hum = lp(hum, 600) * np.minimum(1, t / 0.6) * (0.6 + 0.4 * t / 5)
add(hum, 0.0, 0.10)
for k in range(5):                                              # one beep per digit, the first one isolated
    add(beep(880 if k < 4 else 1000, 0.09), float(k), 0.22 + 0.04 * k)
bt = t_(0.5)                                                    # 5.0 short buzzer
buzz = np.sign(np.sin(2 * np.pi * 330 * bt)) * 0.5 + np.sign(np.sin(2 * np.pi * 495 * bt)) * 0.3
buzz = lp(buzz, 3500) * np.minimum(1, bt / 0.01) * np.minimum(1, (0.5 - bt) / 0.06)
add(buzz, 5.0, 0.26)
add(boom(3.0, 60, 26), 5.0, 1.0)                                # grave impact
ct = t_(0.45); crack = hp(L.rng.standard_normal(len(ct)), 2500) * np.exp(-ct * 18)
add(crack, 5.0, 0.45)                                           # glass cracking
add(lp(glass(), 11000, 4), 5.43, 1.0, send=0.25)               # glass gives way with the light impact
for at, g in ((5.95, 0.7), (6.5, 0.8)):                         # history: "5", then "9"
    add(boom(1.6, 58, 30), at, g)
add(boom(1.4, 56, 32), 8.65, 0.6)                               # UNE NOUVELLE BATAILLE
add(boom(3.0, 64, 26), 44.58, 1.0)                              # last basket
add(boom(3.5, 62, 26), 46.63, 0.8)                              # poster
add(boom(2.0, 60, 28), 52.5, 0.9)                               # last impact
sfx = render_bus()

# =========================== PROVISIONAL MUSIC ===========================
# (replace with Justice - Genesis via mix_genesis.py once the file is supplied)
dr = drone(10.0); dr *= np.linspace(0.0, 1.0, len(dr))[:, None].squeeze() ** 1.5
add(dr, 0.5, 0.28)                                              # bass appears progressively
for b in np.arange(3.0, 5.0, 0.5): add(kick(0.4), b, 0.18 + 0.08 * (b - 3))
add(braam(36, 2.6, 0.7), 5.0, 0.45, send=0.4)                   # music enters on the zero
for b in np.arange(5.6, 10.0, 1.0):                             # history: contained pulse
    add(kick(0.4), b, 0.30); add(kick(0.35), b + 0.22, 0.18)
add(pad([48, 51, 55], 4.4, 650), 5.6, 0.20, send=0.4)
add(riser(1.4, 150, 4000), 8.6, 0.2, send=0.3)
prog = [([48, 51, 55, 60], 36), ([44, 48, 51, 56], 32), ([51, 55, 58, 63], 39), ([46, 50, 53, 58], 34)]
pat = [0, 0, 12, 0, 0, 0, 7, 0, 0, 0, 12, 0, 3, 0, 7, 0]
for bi, bs in enumerate(np.arange(10.0, 42.9, 2.0)):           # actions: progressive build 10 -> 42.9
    ch, root = prog[bi % 4]
    add(pad(ch, 2.05, 900 + bi * 60), bs, 0.22 + 0.004 * bi, send=0.35)
    for i in range(16):
        tt = bs + i * B / 4
        if tt < 42.93 and (bs >= 18.0 or i % 2 == 0):
            add(bass_note(root + pat[i], 0.14), tt, 0.40 if i % 4 == 0 else 0.26)
for b in np.arange(10.0, 42.9, B):
    beat = int(round((b - 10.0) / B)) % 4
    if beat in (0, 2): add(kick(), b, 0.6 if b < 18 else 0.75)
    if beat in (1, 3) and b >= 13.9: add(snare(), b, 0.45 if b < 26.8 else 0.55, send=0.35)
    if b >= 18.0: add(hat(), b + B / 2, 0.10, pan=0.3)
    if b >= 26.8: add(hat(), b + B / 4, 0.07, pan=-0.3)
    if b >= 35.7 and beat == 2: add(kick(), b + 0.25, 0.5)
for at in (13.5, 17.6, 21.1, 24.2, 26.2, 30.0, 31.13, 35.4, 38.8, 40.9):   # baskets / block get an accent
    add(braam(36, 1.0, 0.7), at, 0.20, send=0.4)
add(riser(1.4, 300, 6000), 41.5, 0.2, send=0.3)
add(riser(1.25, 100, 2500), 43.33, 0.22, send=0.2)            # tension after the cut, ball in the air
for k, tt in enumerate(np.arange(43.4, 44.55, 0.125)): add(tick(), tt, 0.10 + 0.012 * k)
add(braam(36, 3.0, 1.0), 44.58, 0.6, send=0.45)                 # back hard on the last basket
for b in np.arange(44.58, 46.2, B):
    add(kick(), b, 0.8); add(snare(), b + 0.25, 0.4, send=0.3)
add(braam(36, 3.4, 0.9), 46.63, 0.45, send=0.5)                 # poster
add(pad([36, 43, 48, 51, 55], 6.0, 600), 46.65, 0.30, send=0.45)
for b in np.arange(47.0, 52.4, 0.5): add(bass_note(24, 0.4), b, 0.24)
add(braam(36, 1.0, 0.9), 52.5, 0.45, send=0.6)
music = render_bus()
i, j = int(42.93 * SR), int(43.33 * SR)
music[i:j] *= np.linspace(0.05, 0.0, j - i)[:, None]             # 0.4-s music cut before the last action
music[j:j + int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))[:, None]

# ================================ MIX ================================
def fade_end(x, d=0.5):
    n = int(d * SR); x[-n:] *= np.linspace(1, 0, n)[:, None]; return x
def save(path, x, peak=0.89):
    x = np.tanh(x * 0.9) / np.tanh(0.9); x = x * peak / max(np.abs(x).max(), 1e-9)
    w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype(np.int16).tobytes()); w.close()
os.makedirs(os.path.join(HERE, 'aud'), exist_ok=True)
save(os.path.join(HERE, 'aud', 'sfx.wav'), fade_end(sfx.copy()))
save(os.path.join(HERE, 'aud', 'music.wav'), fade_end(music.copy()))
save(os.path.join(HERE, 'aud', 'mix.wav'), fade_end(music * 0.85 + sfx * 0.9))
print('ok', N / SR)
