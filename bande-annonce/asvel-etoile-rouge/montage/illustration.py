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
put(can, text('LE DUEL', B8, 40, RED + (255,), track=14), CX, 140)
ns = min(fit('PATTY MILLS', ANTON, 580, 130), fit('CHIMA MONEKE', ANTON, 580, 130))
put(can, text('PATTY MILLS', ANTON, ns, WHITE + (255,)), CX, 290)
put(can, text('VS', ANTON, 60, RED + (255,), track=6), CX, 370)
put(can, text('CHIMA MONEKE', ANTON, ns, RED + (255,)), CX, 500)
d = ImageDraw.Draw(can)
d.rectangle([CX - 170, 540, CX + 170, 544], fill=RED)
ms = fit('ASVEL – ÉTOILE ROUGE DE BELGRADE', B8, 560, 40, track=2)
put(can, text('ASVEL – ÉTOILE ROUGE DE BELGRADE', B8, ms, WHITE + (255,), track=2), CX, 610)
put(can, text('MARDI 13 OCTOBRE • 20H00', B8, 40, (235, 235, 235, 255), track=2), CX, 675)
put(can, text('ASTROBALLE', B6, 36, (215, 215, 215, 255), track=6), CX, 728)
put(can, text('EUROLEAGUE', B8, 32, RED + (255,), track=10), CX, 775)
put(can, text('ASVEL_NEWS', B6, 24, (150, 150, 150, 255), track=4), CX, 860)
os.makedirs(OUT, exist_ok=True)
can.convert('RGB').save(os.path.join(OUT, 'illustration-asvel-etoile-rouge.jpg'), quality=92)

# ---------------------------------------------------------------- couverture 1080 x 1920 (TikTok)
c = R.bg(R.glow(285, 420, 520, (255, 255, 255), 0.15), R.glow(800, 420, 520, (255, 25, 30), 0.26))
R.stripes(c, 0, 0, 9)
R.shape(c, R.para(250, 470, 300, 760, 0.3), (255, 255, 255, 20))
R.shape(c, R.para(830, 470, 300, 760, 0.3), (226, 28, 38, 45))
c.alpha_composite(R.MILLS.layer(2.53, 285, 335, fade_bottom=(600, 790)))
c.alpha_composite(R.MONEKE.layer(2.75, 805, 335, fade_bottom=(600, 790)))
X = R.CX
R.put(c, text('LE DUEL', B8, 56, RED + (255,), track=16), X, 905)
ns = min(fit('PATTY MILLS', ANTON, 880, 190), fit('CHIMA MONEKE', ANTON, 880, 190))
R.put(c, text('PATTY MILLS', ANTON, ns, WHITE + (255,)), X, 1065)
R.put(c, text('VS', ANTON, 72, RED + (255,), track=6), X, 1150)
R.put(c, text('CHIMA MONEKE', ANTON, ns, RED + (255,)), X, 1300)
R.shape(c, [(X - 210, 1338), (X + 210, 1338), (X + 210, 1342), (X - 210, 1342)], RED + (255,))
ms = fit('ASVEL – ÉTOILE ROUGE DE BELGRADE', B8, 860, 48, track=2)
R.put(c, text('ASVEL – ÉTOILE ROUGE DE BELGRADE', B8, ms, WHITE + (255,), track=2), X, 1410)
R.put(c, text('MARDI 13 OCTOBRE • 20H00', B8, 50, (235, 235, 235, 255), track=2), X, 1475)
R.put(c, text('ASTROBALLE · EUROLEAGUE', B6, 40, (215, 215, 215, 255), track=6), X, 1530)
R.put(c, text('ASVEL_NEWS', B6, 30, (150, 150, 150, 255), track=4), X, 1585)
c.convert('RGB').save(os.path.join(OUT, 'couverture-asvel-etoile-rouge.jpg'), quality=92)
print('ok')
