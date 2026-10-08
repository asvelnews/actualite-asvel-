import sys, os
sys.argv = ['x']
from render import *
img = Image.open(os.path.join(HERE, 'cover_base.png')).convert('RGBA')
# bottom gradient
g = np.zeros((H, W), np.uint8); h = 1050
ramp = (np.clip(np.arange(h) / h, 0, 1) ** 1.2 * 255 * 0.93).astype(np.uint8); g[H - h:] = ramp[:, None]
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(Image.fromarray(g)); img.alpha_composite(sh)
f1 = fit(ANTON, 'L’HEURE DE LA', 880, 200); f2 = fit(ANTON, 'REVANCHE', 880, 300)
draw_text(img, (X0, 1090), 'L’HEURE DE LA', f1, WHITE)
draw_text(img, (X0 - 4, 1262), 'REVANCHE', f2, WHITE)
draw_text(img, (X0 + 2, 1600), 'ASVEL – ROANNE  ·  DIM. 11 OCT.  ·  19H', F(BARLOW_B, 52), LGREY, track=2)
img.convert('RGB').save(os.path.join(HERE, 'cover.jpg'), quality=94)
print(f1.size, f2.size)
