"""Exports finaux à partir du rendu vidéo Remotion (muet) + des pistes audio synthétisées.

Usage : python tools_export.py [video_1080x1920.mp4] [video_4k.mp4 (optionnel)]
Produit dans renders/ :
  ASVEL_HALLOWEEN_60FPS.mp4             vertical 1080x1920, H.264 ~20 Mb/s, AAC 48 kHz stéréo (thème fourni si présent)
  ASVEL_HALLOWEEN_60FPS_MUSIQUE_LIBRE.mp4 même vidéo, musique synthétisée libre de droits
  ASVEL_HALLOWEEN_60FPS_SANS_MUSIQUE.mp4 effets sonores seuls
  ASVEL_HALLOWEEN_CARRE_1080.mp4         1080x1080 (vertical centré sur fond flouté)
  ASVEL_HALLOWEEN_4K_60FPS.mp4           2160x3840 si le rendu 4K est fourni
et écrit renders/verification.json (ffprobe + loudness).
"""
import json
import subprocess
import sys
from pathlib import Path

R = Path('renders')
A = Path('public/audio')
src = Path(sys.argv[1] if len(sys.argv) > 1 else 'renders/_video.mp4')
src4k = Path(sys.argv[2]) if len(sys.argv) > 2 else None
AUD = ['-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-ac', '2']

def run(cmd):
    print('>', ' '.join(map(str, cmd)))
    subprocess.run(cmd, check=True)

def mux(video, audio, out):
    run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', *AUD,
         '-shortest', '-movflags', '+faststart', out])

def probe(path):
    p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                        'format=duration,bit_rate,size:stream=codec_name,profile,width,height,r_frame_rate,avg_frame_rate,nb_frames,pix_fmt,sample_rate,channels,bit_rate',
                        '-of', 'json', path], capture_output=True, text=True, check=True)
    return json.loads(p.stdout)

def loudness(path):
    p = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True)
    out = p.stderr[p.stderr.rfind('Summary'):]
    get = lambda key: next((l.split(':')[1].strip() for l in out.splitlines() if l.strip().startswith(key)), None)
    return {'integrated': get('I:'), 'range': get('LRA:'), 'true_peak': get('Peak:')}

outs = {}
final = R / 'ASVEL_HALLOWEEN_60FPS.mp4'
theme = A / 'ASVEL_HALLOWEEN_MIX_THEME.wav'   # thème fourni par l'utilisateur (droits non libres)
mux(src, theme if theme.exists() else A / 'ASVEL_HALLOWEEN_MIX.wav', final); outs['final'] = final
if theme.exists():
    libre = R / 'ASVEL_HALLOWEEN_60FPS_MUSIQUE_LIBRE.mp4'
    mux(src, A / 'ASVEL_HALLOWEEN_MIX.wav', libre); outs['musique_libre'] = libre
nomus = R / 'ASVEL_HALLOWEEN_60FPS_SANS_MUSIQUE.mp4'
mux(src, A / 'ASVEL_HALLOWEEN_SFX_ONLY.wav', nomus); outs['sans_musique'] = nomus
# Carré : la vidéo verticale entière (aucun texte coupé) sur un fond flouté de la même image
sq = R / 'ASVEL_HALLOWEEN_CARRE_1080.mp4'
run(['ffmpeg', '-v', 'error', '-y', '-i', final, '-filter_complex',
     '[0:v]scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,boxblur=40:2,eq=brightness=-0.18[bg];'
     '[0:v]scale=-2:1080:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:0,format=yuv420p[v]',
     '-map', '[v]', '-map', '0:a', '-c:v', 'libx264', '-preset', 'slow', '-b:v', '16M', '-maxrate', '20M', '-bufsize', '40M',
     '-r', '60', '-c:a', 'copy', '-movflags', '+faststart', sq])
outs['carre'] = sq
if src4k and src4k.exists():
    k4 = R / 'ASVEL_HALLOWEEN_4K_60FPS.mp4'
    mux(src4k, theme if theme.exists() else A / 'ASVEL_HALLOWEEN_MIX.wav', k4); outs['4k'] = k4

report = {k: {'fichier': str(v), 'ffprobe': probe(v)} for k, v in outs.items()}
report['final']['loudness'] = loudness(final)
(R / 'verification.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
for k, v in report.items():
    vs = next(s for s in v['ffprobe']['streams'] if s['codec_name'] == 'h264')
    print(f"{k:13s} {vs['width']}x{vs['height']} {vs['avg_frame_rate']} fps  {int(v['ffprobe']['format']['bit_rate']) / 1e6:.1f} Mb/s  {float(v['ffprobe']['format']['duration']):.2f} s")
