"""Images d'illustration : 1600x900 (article / partage) et 1080x1920 (couverture TikTok, = affiche finale).
Usage : python3 illustration.py <dossier_sortie>"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
import render as R
from render import ANTON, B8, B6, RED, WHITE, text, fit

OUT = sys.argv[1]
W, H = 1600, 900

def glow(cx, cy, r, color, k):
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-((xs - cx) ** 2 + (ys - cy) ** 2) / (r * r) * 1.6) * k
    return g[..., None] * np.array(color, np.float32)

def cutout(path, scale, eye, ex, ey, fade):
    im = Image.open(path).convert('RGBA')
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    x, y = round(ex - eye[0] * scale), round(ey - eye[1] * scale)
    lay.alpha_composite(im, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))
    a = np.asarray(lay).copy()
    ys = np.arange(H, dtype=np.float32)
    a[..., 3] = (a[..., 3] * np.clip((fade[1] - ys) / (fade[1] - fade[0]), 0, 1)[:, None]).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')

def put(can, t, x, y, align='c'):
    img, cx, base, left, right = t
    ax = {'c': cx, 'l': left, 'r': right}[align]
    can.alpha_composite(img, (round(x - ax), round(y - base)))

# ---------------------------------------------------------------- 1600 x 900
acc = glow(330, 330, 520, (255, 255, 255), 0.16) + glow(1270, 330, 520, (255, 25, 30), 0.30)
can = Image.fromarray(acc.clip(0, 255).astype(np.uint8)).convert('RGBA')
ys, xs = np.mgrid[0:H, 0:W]
st = np.zeros((H, W, 4), np.uint8); st[..., :3] = 255; st[..., 3] = (((xs + ys) % 64) < 2) * 10
can.alpha_composite(Image.fromarray(st, 'RGBA'))
pl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(pl)
d.polygon([(150, 0), (520, 0), (380, H), (10, H)], fill=(255, 255, 255, 16))
d.polygon([(1080, 0), (1450, 0), (1590, H), (1220, H)], fill=(226, 28, 38, 40))
can.alpha_composite(pl)
can.alpha_composite(cutout(os.path.join(R.SRC, 'patty-mills-detoure.png'), 1.45, (162, 80), 330, 250, (650, 900)))
can.alpha_composite(cutout(os.path.join(R.SRC, 'chima-moneke-detoure.png'), 1.576, (170, 80), 1270, 250, (650, 900)))
# voile central pour la lisibilite du texte
v = np.zeros((H, W, 4), np.uint8)
v[..., 3] = (np.clip(1 - np.abs(xs - 800) / 330, 0, 1) ** 1.5 * 170).astype(np.uint8)
can.alpha_composite(Image.fromarray(v, 'RGBA'))
CX = 800
put(can, text('BANDE-ANNONCE', B8, 34, RED + (255,), track=10), CX, 150)
put(can, text('ASVEL', ANTON, 170, WHITE + (255,)), CX, 330)
put(can, text('VS', ANTON, 56, RED + (255,), track=6), CX, 400)
er = fit('ÉTOILE ROUGE', ANTON, 560, 104)
put(can, text('ÉTOILE ROUGE', ANTON, er, WHITE + (255,)), CX, 505)
put(can, text('DE BELGRADE', ANTON, er, WHITE + (255,)), CX, 600)
d = ImageDraw.Draw(can)
d.rectangle([CX - 170, 632, CX + 170, 636], fill=RED)
put(can, text('MARDI 13 OCTOBRE • 20H00', B8, 44, WHITE + (255,), track=2), CX, 700)
put(can, text('ASTROBALLE', B6, 38, (225, 225, 225, 255), track=6), CX, 750)
put(can, text('EUROLEAGUE', B8, 32, RED + (255,), track=10), CX, 795)
put(can, text('ASVEL_NEWS', B6, 24, (150, 150, 150, 255), track=4), CX, 860)
os.makedirs(OUT, exist_ok=True)
can.convert('RGB').save(os.path.join(OUT, 'illustration-asvel-etoile-rouge.jpg'), quality=92)

# ---------------------------------------------------------------- couverture 1080 x 1920 (affiche finale)
R.poster(R.T_END - 0.5, R.DATES['date']).save(os.path.join(OUT, 'couverture-asvel-etoile-rouge.jpg'), quality=92)
print('ok')
