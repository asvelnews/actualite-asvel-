"""Images de départ des plans générés : les vrais personnages (détourés de tes photos)
intégrés dans les décors (cimetière, route + LDLC Arena), étalonnés pour la nuit."""
from PIL import Image, ImageFilter, ImageEnhance, ImageChops
import numpy as np

C = 'assets/intro/cutouts/'
chars = {
    'freddy': Image.open(C + 'freddy_krueger.png').convert('RGBA'),
    'myers': Image.open(C + 'michael_myers.png').convert('RGBA'),
    'ghost': Image.open(C + 'ghostface.png').convert('RGBA'),
    'art': Image.open(C + 'art_birefnet-portrait.png').convert('RGBA'),
}
chars['art'] = chars['art'].crop(chars['art'].getbbox())

def grade(im, bright, rim_rgb, rim_side, tint=(1, 1, 1)):
    rgb = im.convert('RGB'); a = im.getchannel('A')
    rgb = ImageEnhance.Color(rgb).enhance(0.75)
    rgb = ImageEnhance.Brightness(rgb).enhance(bright)
    arr = np.asarray(rgb).astype(float)
    al = np.asarray(a).astype(float) / 255
    # liseré de contre-jour : bord de la silhouette côté lumière
    er = np.asarray(a.filter(ImageFilter.MinFilter(5))).astype(float) / 255
    edge = np.clip(al - er, 0, 1)
    gx = np.gradient(np.asarray(a.filter(ImageFilter.GaussianBlur(6))).astype(float), axis=1)
    side = np.clip(-gx * rim_side / 6, 0, 1) if rim_side else 1
    rim = edge * (0.4 + 0.6 * side)
    arr = arr * np.array(tint)[None, None]
    arr = arr * (1 - rim[..., None] * 0.35) + np.array(rim_rgb)[None, None] * rim[..., None] * 0.4
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA'); out.putalpha(a.filter(ImageFilter.GaussianBlur(0.8)))
    return out

def place(bg, im, cx, feet, h, bright=0.6, rim=(255, 120, 50), rim_side=1, shadow=0.55, tint=(1, 1, 1)):
    s = h / im.height
    im = im.resize((max(1, int(im.width * s)), int(h)), Image.LANCZOS)
    im = grade(im, bright, rim, rim_side, tint)
    x, y = int(cx - im.width / 2), int(feet - im.height)
    # ombre de contact
    sh = Image.new('L', bg.size, 0)
    from PIL import ImageDraw
    ImageDraw.Draw(sh).ellipse([cx - im.width * 0.38, feet - 10, cx + im.width * 0.38, feet + 14], fill=int(255 * shadow))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    bg.paste(Image.new('RGBA', bg.size, (0, 0, 0, 255)), (0, 0), sh)
    bg.alpha_composite(im, (x, y))

def fog(bg, y0, y1, strength):
    w, h = bg.size
    rng = np.random.default_rng(3)
    n = rng.random((h // 8, w // 8)); n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30))).astype(float) / 255
    yy = np.linspace(0, 1, h)[:, None] * h
    band = np.clip((yy - y0) / (y1 - y0), 0, 1) * np.clip((h - yy) / 40, 0, 1)
    a = np.clip(band * (0.5 + n) * strength, 0, 1)
    layer = np.zeros((h, w, 4)); layer[..., :3] = (150, 140, 145); layer[..., 3] = a * 255
    bg.alpha_composite(Image.fromarray(layer.astype(np.uint8)))

# --- Plan B : sortie du cimetière
bg = Image.open('assets/intro/frames/shotA_start.jpg').convert('RGBA')
place(bg, chars['art'], 455, 905, 255, 0.55, (255, 140, 60), -1, tint=(0.85, 0.88, 1.0))
place(bg, chars['freddy'], 165, 990, 380, 0.62, (255, 140, 60), -1, tint=(0.85, 0.88, 1.0))
place(bg, chars['myers'], 300, 1000, 395, 0.6, (255, 140, 60), -1, tint=(0.85, 0.88, 1.0))
place(bg, chars['ghost'], 545, 1010, 420, 0.75, (255, 140, 60), -1, tint=(0.85, 0.88, 1.0))
fog(bg, 920, 1080, 0.5)
bg.convert('RGB').save('assets/intro_frames/shotB_start.jpg', quality=95)

# --- Plan C : la route vers la LDLC Arena (ils avancent vers la caméra, l'arène derrière eux)
bg = Image.open('assets/intro/frames/road_plate.png').convert('RGBA').resize((720, 1280), Image.LANCZOS)
place(bg, chars['art'], 420, 1020, 230, 0.45, (255, 90, 40), 0, tint=(1.05, 0.72, 0.68))
place(bg, chars['freddy'], 175, 1110, 350, 0.5, (255, 90, 40), 0, tint=(1.05, 0.72, 0.68))
place(bg, chars['myers'], 315, 1125, 370, 0.5, (255, 90, 40), 0, tint=(1.05, 0.72, 0.68))
place(bg, chars['ghost'], 520, 1135, 390, 0.62, (255, 90, 40), 0, tint=(1.05, 0.72, 0.68))
fog(bg, 1080, 1200, 0.45)
bg.convert('RGB').save('assets/intro_frames/shotC_start.jpg', quality=95)
print('ok')
