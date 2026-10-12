"""Teaser Instagram Reels / TikTok — REAL MADRID vs LDLC ASVEL (EuroLeague, jeudi 15/10/2026, 21h00).
Version 2 : refonte complète. Toute l'histoire se déroule au Movistar Arena.

Techniques de montage classiques uniquement :
- plusieurs cadrages d'une seule vraie photo de la salle (recadrage, mouvements de caméra virtuelle,
  profondeur de champ par flou), sans rien inventer de la salle ;
- joueurs détourés intégrés à la salle par compositing (ombre portée douce, habillage lumineux des bords,
  étalonnage et grain communs à toute l'image) ;
- typographie, fondus, coupes sur le temps, flous de mouvement sur les coupes rapides.
Aucune image générée, aucun visage, maillot, numéro ou posture modifié, aucun mouvement de corps.

Usage : python3 render.py OUT.mp4 AUDIO.wav           (rendu complet)
        python3 render.py --stills DOSSIER t1 t2 ...  (images de contrôle)"""
import os, sys, subprocess, math, functools
from multiprocessing import Pool
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, DUR = 1080, 1920, 30, 60.0
WHITE, GREY, GOLD, BLACK = (246, 244, 240), (160, 158, 152), (206, 166, 82), (0, 0, 0)
AMBER = (255, 172, 20)
def P(*p): return os.path.join(HERE, *p)

# ================================================================ outils
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_io5(x): x = clamp(x); return x ** 3 * (x * (6 * x - 15) + 10)
def lerp(a, b, k): return a + (b - a) * k
def win(t, a, b, fin=0.3, fout=0.25):
    if t < a or t > b: return 0.0
    return min(1.0, (t - a) / fin if fin else 1.0, (b - t) / fout if fout else 1.0)
def keys(t, ks, ease=ease_io):
    """Interpolation de images-clés (t, v1, v2, ...) avec lissage."""
    if t <= ks[0][0]: return ks[0][1:]
    for (t0, *a), (t1, *b) in zip(ks, ks[1:]):
        if t <= t1:
            k = ease((t - t0) / (t1 - t0)); return tuple(lerp(x, y, k) for x, y in zip(a, b))
    return ks[-1][1:]

FONT = {'anton': P('fonts', 'anton.woff'), 'osw': P('fonts', 'oswald400.woff'), 'oswb': P('fonts', 'oswald700.woff')}
@functools.lru_cache(None)
def font(name, size): return ImageFont.truetype(FONT[name], size)

@functools.lru_cache(1024)
def text_img(text, fname, size, color, tracking=0.0, shadow=0.55, line_gap=0.10):
    """Texte (multi-lignes, centré) avec ombre douce pour la lisibilité sur la photo."""
    f = font(fname, size); lines = text.split('\n')
    lh = int(size * (1.10 + line_gap)) if fname == 'anton' else int(sum(f.getmetrics()) * (1 + line_gap))
    def lw(s): return sum(f.getlength(c) for c in s) + tracking * size * max(len(s) - 1, 0)
    ws = [lw(l) for l in lines]; pad = int(size * 0.35)
    w = int(max(ws)) + 2 * pad; h = lh * len(lines) + int(size * 0.3) + 2 * pad
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = pad + (max(ws) - ws[i]) / 2; y = pad + i * lh
        for c in l:
            d.text((x, y), c, font=f, fill=color + (255,)); x += f.getlength(c) + tracking * size
    if shadow:
        a = im.getchannel('A').filter(ImageFilter.GaussianBlur(max(2, size * 0.09)))
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * shadow)))
        sh.alpha_composite(im); im = sh
    bb = im.getbbox(); return im.crop(bb) if bb else im

def fit(text, fname, size, color, maxw=960, **kw):
    im = text_img(text, fname, size, color, **kw)
    while im.width > maxw and size > 16:
        size = int(size * 0.95); im = text_img(text, fname, size, color, **kw)
    return im

def fade_img(im, o):
    if o >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * o))); return im

def wipe_img(im, k, soft=0.18):
    """Révélation de gauche à droite (bord adouci)."""
    if k >= 1: return im
    a = np.asarray(im.getchannel('A')).astype(np.float32)
    x = np.linspace(0, 1, im.width)[None, :]
    ramp = np.clip((k * (1 + soft) - x) / soft, 0, 1)
    im = im.copy(); im.putalpha(Image.fromarray((a * ramp).astype(np.uint8))); return im

def put(c, im, cx, cy, o=1.0, s=1.0, wipe=1.0, align='center'):
    if o <= 0.004 or wipe <= 0: return
    if abs(s - 1) > 1e-3: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    im = fade_img(wipe_img(im, wipe), o)
    x = int(cx - im.width / 2) if align == 'center' else int(cx)
    y = int(cy - im.height / 2)
    layer = Image.new('RGBA', c.size, (0, 0, 0, 0)); layer.paste(im, (x, y), im); c.alpha_composite(layer)

def line_text(c, t, text, a, b, cy, size=120, color=WHITE, fname='anton', tracking=0.02, fin=0.45, fout=0.3, rise=18, maxw=960):
    """Titre : révélation par balayage + légère montée, sortie en fondu."""
    o = win(t, a, b, 0.05, fout)
    if o <= 0: return
    k = ease_out((t - a) / fin)
    put(c, fit(text, fname, size, color, maxw=maxw, tracking=tracking), W / 2, cy + rise * (1 - k), o, wipe=k)

def gold_rule(c, t, a, b, cy, width=220, th=3):
    k = ease_out((t - a) / 0.5) * win(t, a, b, 0.01, 0.25)
    if k <= 0: return
    w = max(2, int(width * k)); r = Image.new('RGBA', (w, th), GOLD + (255,)); put(c, r, W / 2, cy, k)

# ================================================================ la salle : une seule vraie photo
@functools.lru_cache(None)
def arena_src(blur):
    src = Image.open(P('assets', 'movistar_arena.webp')).convert('RGB')
    up = src.resize((1600, 1200), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2.0, 55, 2))
    a = np.asarray(up).astype(np.float32) / 255
    if blur: a = cv2.GaussianBlur(a, (0, 0), blur)
    return a

def arena(cx, cy, h, blur=0, dark=0.0):
    """Cadrage 9:16 dans la photo (coordonnées de la photo 800×600). h = hauteur cadrée."""
    h = min(h, 600.0); w = h * W / H
    cx = clamp(cx, w / 2, 800 - w / 2); cy = clamp(cy, h / 2, 600 - h / 2)
    src = arena_src(blur)
    M = np.float32([[W / (w * 2), 0, -(cx - w / 2) * 2 * W / (w * 2)], [0, H / (h * 2), -(cy - h / 2) * 2 * H / (h * 2)]])
    out = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return out * (1 - dark) if dark else out

# ================================================================ joueurs
# yeux (x, y) et distance yeux–menton mesurés sur chaque photo source
EYES = {'maledon_cut.png': (338, 107, 98), 'tlc_cut.png': (336, 95, 92),
        'mills_cut.png': (412, 120, 54), 'crowder_cut.png': (421, 120, 56),
        'joueur1_cut.png': (576, 208, 170), 'waters_cut.png': (621, 237, 235), 'besson_cut.png': (643, 256, 235)}
CHEST_CROP = {'waters_cut.png', 'besson_cut.png', 'joueur1_cut.png', 'maledon_cut.png', 'tlc_cut.png'}
TOP_CROPPED = {'besson_cut.png', 'waters_cut.png'}

@functools.lru_cache(None)
def cut(name):
    im = Image.open(P('assets', name)).convert('RGBA')
    a = np.asarray(im.getchannel('A')).astype(np.float32).copy()
    if name in TOP_CROPPED: k = 18; a[:k] *= np.linspace(0, 1, k)[:, None]
    if name in CHEST_CROP:   # photos coupées à la poitrine/taille : fondu doux du bas plutôt qu'un bord net
        k = int(im.height * 0.16); a[-k:] *= np.linspace(1, 0, k)[:, None] ** 1.3
    im.putalpha(Image.fromarray(a.astype(np.uint8))); return im

@functools.lru_cache(64)
def player_layer(name, target, ex_out, ey_out, bright=1.0):
    """Joueur placé sur un calque plein cadre, l'échelle réglée par la taille du visage (yeux–menton)."""
    ex, ey, ec = EYES[name]; s = target / ec
    im = cut(name); im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if s > 1.15:
        rgb = im.convert('RGB').filter(ImageFilter.UnsharpMask(1.3, 35, 2)); rgb.putalpha(im.getchannel('A')); im = rgb
    if bright != 1.0:
        a = np.asarray(im).astype(np.float32); a[..., :3] *= bright; im = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    layer.paste(im, (int(ex_out - ex * s), int(ey_out - ey * s)), im)
    return layer

def cam(layer, s, ax, ay, dx=0, dy=0):
    """Caméra virtuelle sur un calque : zoom autour d'un point + déplacement."""
    if abs(s - 1) < 1e-4 and not dx and not dy: return layer
    M = np.float32([[s, 0, ax - s * ax + dx], [0, s, ay - s * ay + dy]])
    a = np.asarray(layer)
    out = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    return Image.fromarray(out, 'RGBA')

def composite(bg, layer, bg_soft=None, shadow=0.45, wrap=0.35, light=1.0, opacity=1.0):
    """Intègre un calque joueur dans la photo de la salle : ombre douce + habillage lumineux des bords."""
    a = np.asarray(layer).astype(np.float32) / 255
    A = a[..., 3:4] * opacity; rgb = a[..., :3] * light
    if A.max() <= 0.002: return bg
    if shadow:
        sh = cv2.GaussianBlur(np.roll(A[..., 0], 26, axis=0), (0, 0), 22)[..., None]
        bg = bg * (1 - shadow * sh)
    out = bg * (1 - A) + rgb * A
    if wrap:
        soft = bg_soft if bg_soft is not None else cv2.GaussianBlur(bg, (0, 0), 14)
        edge = A * cv2.GaussianBlur(1 - A[..., 0], (0, 0), 7)[..., None]
        out = out * (1 - wrap * edge) + soft * (wrap * edge)
    return out

# ================================================================ logos
LOGO_FILES = {'rm': P('logos', 'real-madrid.png'), 'asvel': P('logos', 'ldlc-asvel.png')}
LOGO_OPTICAL = {'asvel': 1.12}
@functools.lru_cache(None)
def logo(key, size):
    im = Image.open(LOGO_FILES[key]).convert('RGBA'); bb = im.getbbox(); im = im.crop(bb)
    size = int(size * LOGO_OPTICAL.get(key, 1.0)); s = size / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    sh = Image.new('RGBA', (im.width + 80, im.height + 80), (0, 0, 0, 0))
    a = Image.new('L', sh.size, 0); a.paste(im.getchannel('A'), (40, 40))
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.6)))
    sh.alpha_composite(im, (40, 40)); return sh

# ================================================================ chronomètre (afficheur 7 segments)
SEG = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg'}
def seg_polys(x, y, w, h, th):
    s = th / 2; g = th * 0.18
    hz = lambda x0, y0, l: [(x0 + g, y0), (x0 + s + g, y0 - s), (x0 + l - s - g, y0 - s), (x0 + l - g, y0), (x0 + l - s - g, y0 + s), (x0 + s + g, y0 + s)]
    vt = lambda x0, y0, l: [(x0, y0 + g), (x0 + s, y0 + s + g), (x0 + s, y0 + l - s - g), (x0, y0 + l - g), (x0 - s, y0 + l - s - g), (x0 - s, y0 + s + g)]
    hh = h / 2
    return {'a': hz(x, y, w), 'g': hz(x, y + hh, w), 'd': hz(x, y + h, w),
            'f': vt(x, y, hh), 'b': vt(x + w, y, hh), 'e': vt(x, y + hh, hh), 'c': vt(x + w, y + hh, hh)}

@functools.lru_cache(16)
def shot_clock(text, red=False):
    pw, ph = 860, 700
    panel = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(panel)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), 34, fill=(20, 20, 20, 255), outline=(64, 64, 64, 255), width=6)
    d.rounded_rectangle((34, 96, pw - 35, ph - 35), 16, fill=(7, 7, 7, 255), outline=(36, 36, 36, 255), width=3)
    d.rounded_rectangle((60, 30, pw - 61, 70), 10, fill=(235, 35, 35, 255) if red else (42, 12, 12, 255))
    for sx, sy in [(18, 18), (pw - 18, 18), (18, ph - 18), (pw - 18, ph - 18)]:
        d.ellipse((sx - 7, sy - 7, sx + 7, sy + 7), fill=(52, 52, 52, 255))
    lit = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); dl = ImageDraw.Draw(lit)
    dw, dh, th = 250, 440, 46
    if '.' in text: tens, units, dp = text[0], text[2], True
    else: tens, units, dp = (text[-2] if len(text) == 2 else None), text[-1], False
    for x, ch in [(150, tens), (pw - 150 - dw, units)]:
        for k, poly in seg_polys(x, 160, dw, dh, th).items():
            on = ch is not None and k in SEG.get(ch, '')
            (dl if on else d).polygon(poly, fill=(AMBER + (255,)) if on else (36, 25, 8, 255))
    dpx, dpy = pw // 2, 160 + dh
    (dl if dp else d).ellipse((dpx - 24, dpy - 24, dpx + 24, dpy + 24), fill=(AMBER + (255,)) if dp else (36, 25, 8, 255))
    halo = lit.filter(ImageFilter.GaussianBlur(22)); panel.alpha_composite(halo); panel.alpha_composite(halo); panel.alpha_composite(lit)
    if red:
        rb = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); ImageDraw.Draw(rb).rounded_rectangle((60, 30, pw - 61, 70), 10, fill=(255, 40, 40, 255))
        panel.alpha_composite(rb.filter(ImageFilter.GaussianBlur(18)))
    return panel

# ================================================================ habillage commun
@functools.lru_cache(None)
def grad(y0, y1, a0, a1):
    ys = np.arange(H, dtype=np.float32)
    return np.clip(np.interp(ys, [y0, y1], [a0, a1]), 0, 1)[:, None, None]

def darken_bottom(img, y0, y1, a1): return img * (1 - grad(y0, y1, 0, a1))
def darken_top(img, y0, y1, a0): return img * (1 - grad(y0, y1, a0, 0))

def to_pil(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), 'RGB').convert('RGBA')
def to_np(im): return np.asarray(im.convert('RGB')).astype(np.float32) / 255

def watermark(c, o=0.5):
    put(c, text_img('ASVEL_NEWS', 'oswb', 26, WHITE, tracking=0.22, shadow=0.4), W / 2, 150, o)

def name_tag(c, t, a, b, first, last, num):
    """Bandeau nom : petite ligne dorée, prénom, nom en grand, numéro doré."""
    o = win(t, a, b, 0.05, 0.12); k = ease_out((t - a) / 0.35)
    if o <= 0: return
    r = Image.new('RGBA', (max(2, int(90 * k)), 4), GOLD + (255,)); put(c, r, 90, 1395, o, align='left')
    if first:
        put(c, text_img(first + ('   ' + num if num else ''), 'oswb', 40, WHITE, tracking=0.22), 88, 1445, o, wipe=k, align='left')
    if last:
        put(c, fit(last, 'anton', 150, WHITE, maxw=900, tracking=0.01), 84, 1560, o, wipe=ease_out((t - a - 0.06) / 0.35), align='left')

# ================================================================ SCÈNES
def s_intro(t):  # 0–6.5 : noir, foule lointaine, cœur, chrono
    glow_ = ease_io((t - 1.2) / 3.5) * 0.16
    bg = arena(430, 260, 600, 22) * glow_ if glow_ > 0 else np.zeros((H, W, 3), np.float32)
    c = to_pil(bg)
    if t >= 1.6:
        o = ease_io((t - 1.6) / 0.4)
        if t < 2.0: txt = None
        elif t < 6.0:
            k = int((t - 2.0) / 0.8); txt = str(5 - k); lt = (t - 2.0) - 0.8 * k
        else: txt = '0.0'; lt = t - 6.0
        s = 0.74 + 0.03 * clamp((t - 1.6) / 4.4)
        pulse = 0.025 * math.exp(-lt * 14) if txt else 0
        flick = 0.7 if (txt == '0.0' and int((t - 6.0) * 14) % 2 == 1) else 1.0
        put(c, shot_clock(txt if txt else '  ', red=(txt == '0.0')) if txt else shot_clock('  '), W / 2, 900, o * flick, s + pulse)
        put(c, text_img('EUROLEAGUE  •  MOVISTAR ARENA', 'oswb', 30, GREY, tracking=0.32, shadow=0), W / 2, 1210, o * 0.85)
    return c, None

def s_madrid(t):  # 6.5–10 : révélation de la salle
    cx, cy, h = keys(t, [(6.5, 418, 300, 600), (10.0, 425, 345, 520)])
    bg = arena(cx, cy, h)
    bg = darken_top(bg, 120, 820, 0.55)
    expo = 1 + 0.9 * math.exp(-(t - 6.5) * 7)
    c = to_pil(bg * expo)
    line_text(c, t, 'MADRID.', 6.85, 8.25, 430, 210, tracking=0.05)
    gold_rule(c, t, 7.1, 8.25, 560, 260)
    line_text(c, t, 'UNE SOIRÉE\nEUROPÉENNE.', 8.45, 9.9, 470, 118, tracking=0.03)
    put(c, text_img("PHOTO D'ARCHIVES", 'osw', 20, GREY, tracking=0.2, shadow=0.5), W / 2, 1830, 0.6)
    watermark(c)
    return c, None

def s_defi(t):  # 10–17 : le défi, dans la salle
    if t < 15.5:
        cx, cy, h = keys(t, [(10.0, 430, 430, 340), (15.5, 424, 440, 300)])
        bg = arena(cx, cy, h, blur=3, dark=0.50)
    else:
        cx, cy, h = keys(t, [(15.5, 205, 455, 300), (17.0, 200, 462, 250)])
        bg = arena(cx, cy, h, blur=3, dark=0.35 + 0.35 * ease_io((t - 15.5) / 1.5))
    bg = darken_top(bg, 300, 700, 0.35); bg = darken_bottom(bg, 1050, 1500, 0.55)
    c = to_pil(bg)
    out = win(t, 10.0, 15.35, 0.01, 0.3)
    k = ease_out((t - 10.15) / 0.6)
    put(c, logo('rm', 270), 285 - 50 * (1 - k), 760, k * out)
    put(c, logo('asvel', 270), 795 + 50 * (1 - k), 760, k * out)
    put(c, text_img('REAL MADRID', 'oswb', 46, WHITE, tracking=0.12), 285, 975, ease_out((t - 10.45) / 0.4) * out)
    put(c, text_img('LDLC ASVEL', 'oswb', 46, WHITE, tracking=0.12), 795, 975, ease_out((t - 10.45) / 0.4) * out)
    vr = ease_out((t - 10.5) / 0.8)
    if vr * out > 0: put(c, Image.new('RGBA', (3, max(2, int(640 * vr))), GOLD + (255,)), W / 2, 1000, out * 0.85)
    line_text(c, t, 'LES 5 CONFRONTATIONS RETENUES', 12.0, 15.35, 470, 70, GOLD, tracking=0.03)
    line_text(c, t, 'BILAN SUR LES CINQ MATCHS SÉLECTIONNÉS', 12.15, 15.35, 545, 28, GREY, 'oswb', tracking=0.22, rise=8)
    for cx_, num, lab, a in [(285, '4', 'VICTOIRES', 12.5), (795, '1', 'VICTOIRE', 13.0)]:
        o = win(t, a, 15.35, 0.12, 0.3); p = ease_out((t - a) / 0.3)
        put(c, text_img(num, 'anton', 290, WHITE), cx_, 1185, o, 1 + 0.18 * (1 - p))
        put(c, text_img(lab, 'oswb', 42, GOLD, tracking=0.25), cx_, 1365, o)
    watermark(c)
    return c, None

def maledon_bg(t):
    cx, cy, h = keys(t, [(17.0, 560, 230, 420), (31.0, 520, 250, 400)])
    return arena(cx, cy, h, blur=20, dark=0.72)

def s_emotion(t):  # 17–31 : Théo Maledon, Timothé Luwawu-Cabarrot
    if t < 17.8: return to_pil(np.zeros((H, W, 3), np.float32)), None
    bg = maledon_bg(t); soft = cv2.GaussianBlur(bg, (0, 0), 12)
    out = bg
    # Théo Maledon : plan moyen, puis poussée très lente vers le visage
    if t < 27.9:
        s = keys(t, [(17.8, 1.0), (22.0, 1.04), (27.4, 1.30)], ease_io)[0]
        lay = cam(player_layer('maledon_cut.png', 190, 540, 520), s, 540, 520)
        o = ease_io((t - 17.8) / 0.9) * (1 - ease_io((t - 27.3) / 0.6))
        out = composite(out, lay, soft, shadow=0.0, wrap=0.4, opacity=o)
    # Timothé Luwawu-Cabarrot
    if 27.3 <= t < 29.5:
        s = keys(t, [(27.3, 1.0), (29.5, 1.06)])[0]
        lay = cam(player_layer('tlc_cut.png', 180, 540, 530), s, 540, 530)
        o = ease_io((t - 27.3) / 0.6) * (1 - ease_io((t - 29.05) / 0.45))
        out = composite(out, lay, soft, shadow=0.0, wrap=0.4, opacity=o)
    # les deux anciens Villeurbannais
    if t >= 29.05:
        s = keys(t, [(29.05, 1.0), (31.0, 1.04)])[0]
        o = ease_io((t - 29.05) / 0.45)
        for name, x in [('maledon_cut.png', 300), ('tlc_cut.png', 790)]:
            lay = cam(player_layer(name, 118, x, 660), s, 540, 700)
            out = composite(out, lay, soft, shadow=0.0, wrap=0.4, opacity=o)
    out = darken_bottom(out, 1150, 1600, 0.65)
    out = out * ease_io((t - 17.8) / 0.6)
    c = to_pil(out)
    line_text(c, t, 'TOUT A COMMENCÉ\nÀ VILLEURBANNE.', 18.4, 21.75, 1500, 104, fin=0.9, fout=0.45)
    line_text(c, t, "FORMÉ À L'ASVEL.", 22.3, 23.95, 1500, 112, fin=0.7, fout=0.35)
    line_text(c, t, "AUJOURD'HUI À MADRID.", 24.2, 25.85, 1500, 112, fin=0.7, fout=0.35)
    line_text(c, t, 'THÉO MALEDON', 26.0, 27.3, 1480, 150, fin=0.6, fout=0.35)
    line_text(c, t, '#12  •  REAL MADRID', 26.2, 27.3, 1600, 46, GOLD, 'oswb', tracking=0.2, rise=8, fout=0.35)
    line_text(c, t, 'LUI AUSSI A PORTÉ\nNOS COULEURS.', 27.75, 29.0, 1490, 104, fin=0.45, fout=0.25)
    line_text(c, t, 'TIMOTHÉ LUWAWU-CABARROT  •  #3', 27.95, 29.0, 1640, 36, GOLD, 'oswb', tracking=0.15, rise=6, fout=0.25)
    line_text(c, t, 'DEUX ANCIENS\nVILLEURBANNAIS.', 29.3, 30.15, 1500, 104, fin=0.35, fout=0.15)
    line_text(c, t, 'DES RETROUVAILLES\nPARTICULIÈRES.', 30.2, 31.0, 1500, 104, GOLD, fin=0.35, fout=0.0)
    if t > 29.2:
        o = ease_io((t - 29.3) / 0.4)
        put(c, text_img('#12 MALEDON', 'oswb', 30, GREY, tracking=0.15), 300, 1240, o)
        put(c, text_img('#3 LUWAWU-CABARROT', 'oswb', 30, GREY, tracking=0.15), 790, 1240, o)
    watermark(c, 0.4)
    return c, None

# --- la montée : cinq joueurs, cadrages variés, coupes sur le temps
HYPE = [  # début, fin, joueur, taille visage, x yeux, y yeux, caméra (s0, s1, dx0, dx1), arrière-plan (cx, cy, h), prénom, nom, numéro
    (31.0, 32.5, 'mills_cut.png', 108, 560, 520, (1.00, 1.07, 0, 0), (420, 420, 380), 'PATTY', 'MILLS', '#8'),
    (32.5, 34.0, 'waters_cut.png', 300, 540, 640, (1.00, 1.06, 0, 0), (600, 200, 330), 'TREMONT', 'WATERS', '#51'),
    (34.0, 35.5, 'besson_cut.png', 300, 650, 600, (1.00, 1.04, 30, -30), (250, 230, 330), 'HUGO', 'BESSON', '#25'),
    (35.5, 37.0, 'crowder_cut.png', 108, 560, 520, (1.22, 1.00, 0, 0), (430, 470, 360), 'JAE', 'CROWDER', '#99'),
    (37.0, 38.5, 'joueur1_cut.png', 220, 540, 600, (1.00, 1.06, 0, 0), (380, 330, 420), 'LDLC ASVEL', '', ''),
]
FLASH = [  # 38.5–40 : coupes rapides sur les visages (cadrages serrés, seulement sur les photos haute définition)
    (38.5, 'waters_cut.png', 330, 540, 760), (38.8, 'besson_cut.png', 330, 540, 760), (39.1, 'joueur1_cut.png', 280, 540, 760),
    (39.4, 'crowder_cut.png', 135, 540, 720), (39.7, 'mills_cut.png', 135, 540, 720),
]

def s_hype(t):  # 31–40
    if t < 38.5:
        for a, b, name, tg, ex, ey, (s0, s1, d0, d1), (bx, by, bh), first, last, num in HYPE:
            if a <= t < b:
                k = (t - a) / (b - a)
                bg = arena(bx + 12 * k, by, bh, blur=9, dark=0.52)
                lay = player_layer(name, tg, ex, ey)
                s = lerp(s0, s1, ease_io(k)) if s0 < s1 else lerp(s0, s1, ease_out(k * 1.4))
                if name == 'waters_cut.png' and t > 33.25: s = 1.06 + 0.05 * ease_out((t - 33.25) / 0.25)   # recadrage sur le temps
                out = composite(bg, cam(lay, s, ex, ey, lerp(d0, d1, ease_io(k))), shadow=0.5, wrap=0.35)
                out = darken_bottom(out, 1250, 1750, 0.6)
                c = to_pil(out)
                name_tag(c, t, a + 0.1, b, first, last, num)
                watermark(c, 0.4)
                return c, ('whip', a)
    for i, (a, name, tg, ex, ey) in enumerate(FLASH):
        b = FLASH[i + 1][0] if i + 1 < len(FLASH) else 40.0
        if a <= t < b:
            bg = arena(300 + 120 * i, 300, 320, blur=12, dark=0.62)
            s = 1.0 + 0.06 * (t - a) / (b - a)
            out = composite(bg, cam(player_layer(name, tg, ex, ey), s, ex, ey), shadow=0.4, wrap=0.35)
            out = darken_bottom(out, 1300, 1800, 0.6)
            return to_pil(out), ('whip', a)
    return to_pil(np.zeros((H, W, 3), np.float32)), None

# --- final : la formation entre dans l'arène
SQUAD = [  # joueur, taille visage, x yeux, y yeux, apparition
    ('besson_cut.png', 120, 112, 955, 40.3), ('crowder_cut.png', 120, 968, 955, 41.0),
    ('joueur1_cut.png', 130, 322, 975, 41.7), ('waters_cut.png', 130, 758, 975, 42.4),
    ('mills_cut.png', 140, 540, 1000, 43.1),
]

def squad(t, bg, soft, light_all):
    s = keys(t, [(40.0, 1.0), (44.0, 1.04), (49.0, 1.12), (54.0, 1.15)])[0]
    for name, tg, ex, ey, a in SQUAD:
        o = ease_io((t - a) / 0.6)
        if o <= 0: continue
        light = min(light_all, 0.12 + 0.88 * ease_io((t - a - 0.2) / 1.2) if t < 44 else 1.0)
        lay = cam(player_layer(name, tg, ex, ey), s, 540, 1000)
        bg = composite(bg, lay, soft, shadow=0.5 * light, wrap=0.3, light=max(light, 0.06), opacity=o)
    return bg

def s_arrivee(t):  # 40–54
    sh = keys(t, [(40.0, 600, 0, 0), (44.0, 600, 0, 0), (54.0, 560, 0, 0)])[0]
    lights = ease_io((t - 44.0) / 1.0)
    dark_bg = arena(560, 230, 420, blur=20, dark=0.9)
    if lights > 0:
        lit = arena(422, 330 - 20 * clamp((t - 44) / 10), sh, blur=3, dark=0.12)
        bg = dark_bg * (1 - lights) + lit * lights
    else: bg = dark_bg
    if t >= 49.0: bg = bg * (1 - 0.35 * ease_io((t - 49.0) / 0.5))    # la salle baisse d'un ton quand la musique se coupe
    soft = cv2.GaussianBlur(bg, (0, 0), 14)
    out = squad(t, bg, soft, 0.82 + 0.18 * lights if t < 44 else 1.0)
    out = darken_bottom(out, 1300, 1700, 0.85)
    expo = 1 + 0.45 * math.exp(-(t - 44.0) * 6) if t >= 44 else 1
    if t >= 53.3: expo = 1 + 1.4 * math.exp(-(t - 53.3) * 12)
    if t < 40.25: out = out * ease_io((t - 40.0) / 0.25)
    c = to_pil(out * expo)
    line_text(c, t, 'DEUX ÉQUIPES.', 49.3, 50.4, 1640, 150, fin=0.3, fout=0.2)
    line_text(c, t, 'UN SEUL TERRAIN.', 50.6, 51.7, 1640, 150, fin=0.3, fout=0.2)
    if 51.9 <= t < 53.0:
        o = 1 - clamp((t - 52.85) / 0.15)
        full = 'UNE SEULE REPARTIRA...'
        im = fit(full, 'anton', 130, WHITE, tracking=0.02)
        # révélation mot par mot : on dévoile la ligne jusqu'au mot courant
        f = font('anton', 130); total = f.getlength(full)
        marks = [(51.9, f.getlength('UNE ') / total), (52.2, f.getlength('UNE SEULE ') / total), (52.5, 1.0)]
        k = 0
        for a, m in marks:
            if t >= a: k = m if (t - a) > 0.25 else lerp(k, m, ease_out((t - a) / 0.25))
        put(c, im, W / 2, 1640, o, wipe=k)
    if t >= 53.3:
        p = ease_out((t - 53.3) / 0.2)
        put(c, text_img('AVEC LA', 'oswb', 64, WHITE, tracking=0.3), W / 2, 1500, clamp((t - 53.3) / 0.06))
        put(c, fit('VICTOIRE.', 'anton', 260, GOLD, maxw=1000, tracking=0.02), W / 2, 1665, clamp((t - 53.3) / 0.05), 1 + 0.25 * (1 - p))
    if t < 49.0: watermark(c, 0.45)
    fx = ('shake', 53.3) if t >= 53.3 else None
    return c, fx

def s_reveal(t):  # 54–60 : l'affiche
    cx, cy, h = keys(t, [(54.0, 422, 320, 560), (60.0, 425, 335, 520)])
    bg = arena(cx, cy, h, blur=16, dark=0.72)
    x = ease_io((t - 54.0) / 0.35)
    if x < 1:   # fondu enchaîné depuis la formation
        prev = to_np(s_arrivee(53.99)[0]); bg = prev * (1 - x) + bg * x
    c = to_pil(bg); a0 = 54.15
    def o(d): return clamp((t - (a0 + d)) / 0.35)
    def r(d): return 22 * (1 - ease_out((t - (a0 + d)) / 0.4))
    lp_ = ease_out((t - a0) / 0.5)
    put(c, logo('rm', 250), 290 - 60 * (1 - lp_), 650, lp_)
    put(c, logo('asvel', 250), 790 + 60 * (1 - lp_), 650, lp_)
    put(c, text_img('EUROLEAGUE', 'oswb', 44, GOLD, tracking=0.42), W / 2, 410 + r(0.05), o(0.05))
    put(c, text_img('REAL MADRID', 'anton', 130, WHITE, tracking=0.03), W / 2, 915 + r(0.15), o(0.15))
    put(c, text_img('VS', 'anton', 70, GOLD, tracking=0.1), W / 2, 1030 + r(0.22), o(0.22))
    put(c, text_img('LDLC ASVEL', 'anton', 130, WHITE, tracking=0.03), W / 2, 1145 + r(0.3), o(0.3))
    gold_rule(c, t, a0 + 0.4, 61, 1258, 520)
    put(c, text_img('JEUDI 15 OCTOBRE 2026', 'oswb', 64, WHITE, tracking=0.1), W / 2, 1335 + r(0.45), o(0.45))
    put(c, text_img('21H00', 'anton', 112, GOLD, tracking=0.06), W / 2, 1445 + r(0.55), o(0.55))
    put(c, text_img('MOVISTAR ARENA  •  MADRID', 'oswb', 50, WHITE, tracking=0.12), W / 2, 1555 + r(0.65), o(0.65))
    put(c, text_img('ASVEL_NEWS', 'oswb', 36, GREY, tracking=0.32), W / 2, 1700, o(0.85))
    return c, None

SCENES = [(0, 6.5, s_intro), (6.5, 10, s_madrid), (10, 17, s_defi), (17, 31, s_emotion), (31, 40, s_hype), (40, 54, s_arrivee), (54, 60.1, s_reveal)]

# ================================================================ finition : flou de mouvement, étalonnage, vignette, grain
@functools.lru_cache(None)
def vignette():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W / 2) / (W * 0.72)) ** 2 + ((y - H / 2) / (H * 0.60)) ** 2)
    return (1 - np.clip(d - 0.5, 0, 1) * 0.75)[..., None]

@functools.lru_cache(None)
def grain(i):
    g = np.random.default_rng(100 + i).normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    return cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * 0.022

WHIPS = [10.0, 15.5] + [h[0] for h in HYPE[1:]] + [f[0] for f in FLASH]

def finish(t, img, fx):
    a = to_np(img)
    for wt in WHIPS:                                   # flou de mouvement horizontal sur les coupes
        d = t - wt
        if -0.001 <= d < 0.1:
            L = int(70 * (1 - d / 0.1)) | 1
            if L > 2: a = cv2.blur(a, (L, 1))
    if fx and fx[0] == 'shake' and t - fx[1] < 0.3:
        k = (1 - (t - fx[1]) / 0.3) ** 2 * 12
        M = np.float32([[1, 0, k * math.sin(t * 190)], [0, 1, k * math.cos(t * 150)]])
        a = cv2.warpAffine(a, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    a = a * vignette()
    a = 0.012 + 0.988 * a                              # noirs légèrement relevés (rendu ciné)
    a = a * np.float32([1.015, 1.0, 0.975])            # étalonnage chaud très léger, commun à tout le film
    lum = a.mean(2, keepdims=True)
    a = a + grain(int(t * FPS) % 6) * (0.6 + 0.8 * lum * (1 - lum) * 4)
    return (np.clip(a, 0, 1) * 255).astype(np.uint8)

def render_frame(i):
    t = i / FPS
    for a, b, f in SCENES:
        if a <= t < b:
            img, fx = f(t); return finish(t, img, fx).tobytes()

def main():
    out, audio = sys.argv[1], sys.argv[2]
    nf = int(DUR * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-profile:v', 'high',
           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000',
           '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-t', str(DUR), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, fr in enumerate(pool.imap(render_frame, range(nf), chunksize=6)):
            p.stdin.write(fr)
            if i % 300 == 0: print(f'{i}/{nf}', flush=True)
    p.stdin.close(); p.wait(); print('done', out)

if __name__ == '__main__':
    if sys.argv[1] == '--stills':
        for tt in sys.argv[3:]:
            i = int(round(float(tt) * FPS))
            Image.frombytes('RGB', (W, H), render_frame(i)).save(os.path.join(sys.argv[2], f'f_{float(tt):05.2f}.jpg'), quality=88)
    else:
        main()
