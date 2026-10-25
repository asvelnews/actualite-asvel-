"""Rendu parallèle : N processus Remotion indépendants sur N tranches de la timeline.
Chaque processus a son propre Chromium (le processus GPU/compositeur de Chromium est
mono-thread : un seul rendu ne peut pas saturer plusieurs cœurs). Les tranches sont
ensuite concaténées sans réencodage (même codec, même débit, chaque tranche commence
sur une image clé).

Usage : python tools_render_parallel.py <sortie.mp4> [nb_tranches] [options remotion...]
"""
import json
import subprocess
import sys
import time
from pathlib import Path

out = Path(sys.argv[1])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
extra = sys.argv[3:]
total = json.load(open('src/timeline.json'))['duration']
tmp = out.parent / f'_chunks_{out.stem}'
tmp.mkdir(parents=True, exist_ok=True)
npx = 'npx.cmd' if sys.platform == 'win32' else 'npx'
bounds = [round(total * i / n) for i in range(n + 1)]
procs = []
t0 = time.time()
for i in range(n):
    a, b = bounds[i], bounds[i + 1] - 1
    part = tmp / f'part_{i:02d}.mp4'
    log = open(tmp / f'part_{i:02d}.log', 'w')
    cmd = [npx, 'remotion', 'render', 'src/index.ts', 'Trailer', str(part), f'--frames={a}-{b}', '--codec=h264',
           '--video-bitrate=20M', '--muted', '--concurrency=1', *extra]
    procs.append((subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT), part, log))
    time.sleep(3)  # décale les démarrages (bundling)
fail = False
for p, part, log in procs:
    p.wait()
    log.close()
    if p.returncode != 0:
        fail = True
        print('ÉCHEC', part)
if fail:
    sys.exit(1)
lst = tmp / 'list.txt'
lst.write_text(''.join(f"file '{p.resolve().as_posix()}'\n" for _, p, _ in procs))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', '-movflags', '+faststart', str(out)], check=True)
print(f'OK {out} en {time.time() - t0:.0f} s')
