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
os.environ['TRAILER_DUR'] = '59.87'
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
t = t_(5.0)                                                     # electric hum under the countdown
hum = (np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 100 * t) + 0.25 * np.sign(np.sin(2 * np.pi * 150 * t)) * 0.3)
hum = lp(hum, 600) * np.minimum(1, t / 0.6) * (0.6 + 0.4 * t / 5)
add(hum, 0.0, 0.10)
for k in range(5):                                              # one beep per digit, the first one isolated
    add(beep(880 if k < 4 else 1000, 0.09), float(k), 0.22 + 0.04 * k)
bt = t_(0.7)                                                    # 5.0 buzzer
buzz = np.sign(np.sin(2 * np.pi * 330 * bt)) * 0.5 + np.sign(np.sin(2 * np.pi * 495 * bt)) * 0.3
buzz = lp(buzz, 3500) * np.minimum(1, bt / 0.01) * np.minimum(1, (0.7 - bt) / 0.08)
add(buzz, 5.0, 0.28)
add(boom(3.0, 60, 26), 5.0, 1.0)                                # grave impact
ct = t_(0.4); crack = hp(L.rng.standard_normal(len(ct)), 2500) * np.exp(-ct * 30)
add(crack, 5.0, 0.5)                                            # crack
add(lp(glass(), 11000, 4), 5.4, 1.2, send=0.25)                 # glass bursts
for at, g in ((8.1, 0.8), (10.3, 0.9), (14.7, 0.7)):            # history: "5", "9", "UNE NOUVELLE BATAILLE"
    add(boom(1.8, 58, 30), at, g)
add(boom(3.0, 64, 26), 49.88, 1.0)                              # final basket
add(boom(3.5, 62, 26), 52.37, 0.8)                              # poster
add(boom(2.0, 60, 28), 58.6, 0.9)                               # last impact
sfx = render_bus()

# =========================== PROVISIONAL MUSIC ===========================
dr = drone(16.0); dr *= np.linspace(0.0, 1.0, len(dr))[:, None].squeeze() ** 1.5
add(dr, 1.0, 0.30)                                              # bass appears gradually under the countdown
add(riser(3.0, 120, 3000), 2.0, 0.18, send=0.3)
for b in np.arange(3.0, 5.0, 0.5): add(kick(0.4), b, 0.2 + 0.08 * (b - 3))
add(braam(36, 2.6, 0.6), 5.0, 0.35, send=0.4)
# history 6-17: contained
for b in np.arange(6.0, 17.0, 1.0):                             # heartbeat
    add(kick(0.4), b, 0.30); add(kick(0.35), b + 0.22, 0.18)
add(pad([48, 51, 55], 11.0, 650), 6.0, 0.20, send=0.4)
add(riser(2.0, 150, 4000), 15.0, 0.2, send=0.3)
# heads 17-27.5: the music starts to grow
add(pad([44, 48, 51, 56], 5.5, 900), 17.0, 0.24, send=0.35)
add(pad([46, 50, 53, 58], 5.0, 1000), 22.5, 0.26, send=0.35)
pat = [0, 0, 12, 0, 0, 0, 7, 0, 0, 0, 12, 0, 3, 0, 7, 0]
for i, tt in enumerate(np.arange(17.0, 27.5, B / 2)):
    add(bass_note(36 + pat[i % 16] * (tt >= 21), 0.2), tt, 0.25 if i % 2 == 0 else 0.15)
for b in np.arange(19.0, 27.5, B):
    if int(round((b - 19) / B)) % 2 == 0: add(kick(), b, 0.55)
    else: add(snare(0.3), b, 0.30, send=0.3)
for at in (21.8, 27.2): add(braam(36, 1.2, 0.8), at, 0.25, send=0.4)
# 27.5-48.23: full groove, accelerating
prog = [([48, 51, 55, 60], 36), ([44, 48, 51, 56], 32), ([51, 55, 58, 63], 39), ([46, 50, 53, 58], 34)]
for bi, bs in enumerate(np.arange(27.5, 48.2, 2.0)):
    ch, root = prog[bi % 4]
    add(pad(ch, 2.05, 1000 + bi * 60), bs, 0.27, send=0.35)
    for i in range(16):
        if bs + i * B / 4 < 48.2: add(bass_note(root + pat[i], 0.14), bs + i * B / 4, 0.40 if i % 4 == 0 else 0.26)
for b in np.arange(27.5, 48.2, B):
    beat = int(round((b - 27.5) / B)) % 4
    if beat in (0, 2): add(kick(), b, 0.75)
    if beat in (1, 3): add(snare(), b, 0.5, send=0.35)
    add(hat(), b + B / 2, 0.11, pan=0.3)
    if b >= 37.0: add(hat(), b + B / 4, 0.07, pan=-0.3)
    if b >= 41.0 and beat == 2: add(kick(), b + 0.25, 0.5)
for at in (30.9, 34.47, 36.67, 40.62, 44.03, 46.78):            # baskets get an accent
    add(braam(36, 1.0, 0.7), at, 0.22, send=0.4)
add(riser(1.6, 300, 6000), 45.2, 0.2, send=0.3)
# 48.23-48.63: music cut (silence) ; 48.63-49.88: tension while the ball flies
add(riser(1.25, 100, 2500), 48.63, 0.22, send=0.2)
for k, tt in enumerate(np.arange(48.7, 49.85, 0.125)): add(tick(), tt, 0.10 + 0.012 * k)
# 49.88: the music comes back hard on the basket
add(braam(36, 3.0, 1.0), 49.88, 0.6, send=0.45)
for b in np.arange(49.88, 51.6, B):
    add(kick(), b, 0.8); add(snare(), b + 0.25, 0.4, send=0.3)
add(pad([36, 43, 48, 51, 55], 2.6, 900), 49.9, 0.3, send=0.4)
# poster 52.37-59.87
add(braam(36, 3.4, 0.9), 52.37, 0.45, send=0.5)
add(pad([36, 43, 48, 51, 55], 6.4, 600), 52.4, 0.30, send=0.45)
for b in np.arange(53.0, 58.4, 0.5): add(bass_note(24, 0.4), b, 0.24)
add(braam(36, 1.4, 0.9), 58.6, 0.45, send=0.6)
music = render_bus()
i, j = int(48.23 * SR), int(48.63 * SR)
music[i:j] *= np.linspace(0.05, 0.0, j - i)[:, None]             # the 0.4-s cut
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
