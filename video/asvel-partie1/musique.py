# -*- coding: utf-8 -*-
"""Musique instrumentale discrète, générée (libre de droits) :
nappe de cordes douce + piano feutré, progression ré mineur, ~64 bpm."""
import numpy as np

SR = 48000
BPM = 64
BEAT = 60 / BPM

# accords (notes MIDI) : Dm - Bb - F - C / Dm - Gm - Bb - A
PROG = [
    [50, 57, 62, 65, 69], [46, 53, 58, 62, 65], [41, 53, 57, 60, 65], [48, 55, 60, 64, 67],
    [50, 57, 62, 65, 69], [43, 55, 58, 62, 67], [46, 53, 58, 62, 65], [45, 52, 57, 61, 64],
]
ARP = [0, 2, 3, 4, 3, 2, 1, 2]   # ordre des notes du piano dans l'accord


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pad_note(f, n, rng):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for det in (-0.12, 0.0, 0.11):          # léger désaccord = chorus
        ff = f * 2 ** (det / 12)
        for k, a in ((1, 1.0), (2, 0.35), (3, 0.16), (4, 0.07)):
            s += a * np.sin(2 * np.pi * ff * k * t + rng.uniform(0, 6.28))
    att, rel = min(1.6, n / SR / 2), min(1.8, n / SR / 2)
    env = np.minimum(1, t / att) * np.minimum(1, (n / SR - t) / rel)
    return s * env * (1 + 0.08 * np.sin(2 * np.pi * 0.21 * t))


def piano_note(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (1.6 + 1.3 * k))
            for k, a in ((1, 1.0), (2, 0.42), (3, 0.18), (4, 0.08)))
    return s * np.minimum(1, t / 0.006)


def reverb(x, rng, seconds=2.6, wet=0.35):
    n = int(seconds * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 6.9 / seconds)
    ir /= np.sqrt((ir ** 2).sum())
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:len(x)]
    return (1 - wet) * x + wet * y * 3


def generer(duree, seed=7):
    rng = np.random.default_rng(seed)
    n = int((duree + 4) * SR)
    pad = np.zeros(n)
    pno = np.zeros(n)
    chord_len = 4 * BEAT
    i = 0
    t0 = 0.0
    while t0 < duree + 4:
        ch = PROG[i % len(PROG)]
        a, b = int(t0 * SR), min(n, int((t0 + chord_len + 1.4) * SR))
        for m in ch:
            pad[a:b] += pad_note(hz(m), b - a, rng) * (1.0 if m > 48 else 0.7)
        # piano : arpège en croches, plus clairsemé une mesure sur deux
        for j, k in enumerate(ARP):
            if i % 2 and j % 2:
                continue
            ts = t0 + j * BEAT / 2
            s = int(ts * SR)
            note = piano_note(hz(ch[k] + 12), 3.0)
            e = min(n, s + len(note))
            if s < n:
                pno[s:e] += note[:e - s] * (0.55 + 0.15 * rng.random()) * (0.9 if j else 1.1)
        t0 += chord_len
        i += 1
    # adoucit la nappe (passe-bas simple)
    spec = np.fft.rfft(pad)
    f = np.fft.rfftfreq(n, 1 / SR)
    lp = np.fft.irfft(spec / (1 + (f / 1800) ** 2), n)
    mix = 0.55 * lp / np.abs(lp).max() + 0.35 * pno / np.abs(pno).max()
    mix = reverb(mix, rng)
    mix /= np.abs(mix).max()
    return mix[:int(duree * SR)]
