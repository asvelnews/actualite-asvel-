# -*- coding: utf-8 -*-
"""Prépare les segments de voix (48 kHz mono, silences de bord retirés).

Priorité : enregistrement réel « voix/<id>.wav », sinon voix de synthèse
provisoire (Kokoro, voix française ff_siwis), mise en cache dans build/.
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

from narration import segments

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
REC_DIR = os.path.join(HERE, "voix")
OUT_DIR = os.path.join(HERE, "build", "voix")
KOKORO_DIR = os.environ.get("KOKORO_DIR", os.path.join(HERE, "build", "kokoro"))


def resample(x, sr_in, sr_out=SR):
    if sr_in == sr_out:
        return x
    n = int(round(len(x) * sr_out / sr_in))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def trim(x, thr_db=-42, margin=0.04):
    env = np.abs(x)
    thr = 10 ** (thr_db / 20) * max(env.max(), 1e-9)
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return x
    m = int(margin * SR)
    return x[max(0, idx[0] - m): idx[-1] + m]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    kokoro = None
    info = {}
    for sid, text, pause, tts in segments():
        out = os.path.join(OUT_DIR, sid + ".wav")
        rec = os.path.join(REC_DIR, sid + ".wav")
        src = "enregistrement" if os.path.exists(rec) else "synthese"
        stamp = os.path.join(OUT_DIR, sid + ".src")
        key = f"{src}|{os.path.getmtime(rec) if src == 'enregistrement' else tts}"
        if not (os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == key):
            if src == "enregistrement":
                x, sr = sf.read(rec, always_2d=True)
                x = resample(x.mean(axis=1), sr)
            else:
                if kokoro is None:
                    from kokoro_onnx import Kokoro
                    kokoro = Kokoro(os.path.join(KOKORO_DIR, "kokoro-v1.0.onnx"),
                                    os.path.join(KOKORO_DIR, "voices-v1.0.bin"))
                x, sr = kokoro.create(tts, voice="ff_siwis", speed=0.92, lang="fr-fr")
                x = resample(np.asarray(x, dtype=np.float64), sr)
            x = trim(x)
            sf.write(out, x.astype(np.float32), SR)
            open(stamp, "w").write(key)
            print(f"{sid}: {src}", file=sys.stderr)
        info[sid] = {"duree": sf.info(out).duration, "pause": pause, "source": src}
    json.dump(info, open(os.path.join(HERE, "build", "voix.json"), "w"), indent=1)
    print(f"{len(info)} segments, {sum(v['duree'] + v['pause'] for v in info.values()):.1f} s")


if __name__ == "__main__":
    main()
