"""Mix original score + real arena sound (Touchdown clip only: the other clips carry a pop track or no audio)."""
import numpy as np, wave, subprocess, sys
from scipy.signal import butter, sosfilt

SR = 48000; N = 25 * SR
def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '2', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).reshape(-1, 2) / 32768.0
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x, axis=0)
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x, axis=0)

music = load('aud/music.wav')[:N]
td = load('src/touchdown.mp4')
amb = np.zeros((N, 2))

def place(src_a, src_b, at, gain, fin=0.04, fout=0.04, filt=None):
    seg = td[int(src_a * SR):int(src_b * SR)].copy()
    if filt: seg = filt(seg)
    n = len(seg); a = int(fin * SR); b = int(fout * SR)
    env = np.ones(n)
    if a: env[:a] = np.linspace(0, 1, a)
    if b: env[-b:] = np.linspace(1, 0, b)
    i = int(at * SR)
    amb[i:i + n] += seg * env[:, None] * gain

# 5.0-8.0 : arena murmur under the build-up (real crowd from the Touchdown clip, thinned)
place(0.40, 3.40, 5.0, 0.55, fin=0.8, fout=0.15, filt=lambda x: lp(hp(x, 220), 7000))
# 13.0-17.0 : picture-synced real sound of the Sestina action (catch, finish, whistle, crowd roar)
place(3.05, 4.05, 13.0, 1.0, fin=0.02, fout=0.02)
place(4.65, 6.15, 14.0, 1.0, fin=0.02, fout=0.0)
place(6.15, 7.65, 15.5, 1.0, fin=0.0, fout=0.0)
# 17.0-19.8 : the same roar continues under the message (continuous with previous segment)
place(7.65, 10.45, 17.0, 0.85, fin=0.0, fout=0.9)

# music ducking where real sound must read
g = np.ones(N)
def dk(a, b, depth, r=0.08):
    i, j = int(a * SR), int(b * SR); rr = int(r * SR)
    g[i:j] = np.minimum(g[i:j], depth)
    g[i - rr:i] = np.minimum(g[i - rr:i], np.linspace(1, depth, rr))
    g[j:j + rr] = np.minimum(g[j:j + rr], np.linspace(depth, 1, rr))
dk(14.95, 15.9, 0.62)   # the basket + crowd eruption
dk(17.35, 19.2, 0.85)
mix = music * g[:, None] * 0.82 + amb * 0.9
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix *= 0.89 / np.abs(mix).max()
w = wave.open(sys.argv[1], 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype(np.int16).tobytes()); w.close()
for a, b, name in ((0, 2.5, 'hook'), (2.5, 5, 'rappel'), (5, 8, 'attente'), (8, 17, 'montee'), (17, 20, 'message'), (20, 25, 'rdv')):
    s = mix[int(a * SR):int(b * SR)]
    print(f'{name:8s} rms {20*np.log10(np.sqrt((s**2).mean())):6.1f} dB')
