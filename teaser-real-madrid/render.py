"""Teaser Instagram Reels — REAL MADRID vs LDLC ASVEL (EuroLeague, 15/10/2026).
Motion design 100 % montage classique : photos authentiques, logos officiels,
typographie, zooms, fondus, flashs. Aucune génération d'image.

Usage : python3 render.py OUT.mp4 AUDIO.wav [--preview]
Logos attendus : logos/real-madrid.png et logos/ldlc-asvel.png (PNG transparent).
Sans eux, un cadre « LOGO À FOURNIR » est affiché (mode maquette)."""
import os, sys, subprocess, math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, DUR = 1080, 1920, 30, 50.0
BLACK, WHITE, GREY, GOLD = (5, 5, 5), (245, 245, 245), (150, 150, 150), (201, 162, 74)
AMBER = (255, 172, 20)

def P(*p): return os.path.join(HERE, *p)
FONT = {'anton': P('fonts', 'anton.woff'), 'osw': P('fonts', 'oswald400.woff'), 'oswb': P('fonts', 'oswald700.woff')}

@functools.lru_cache(None)
def font(name, size): return ImageFont.truetype(FONT[name], size)

# ---------------------------------------------------------------- easing / timing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return x * x * (3 - 2 * x)
def win(t, a, b, fin=0.25, fout=0.2):
    """Opacité d'un élément visible entre a et b avec fondus."""
    if t < a or t > b: return 0.0
    return min(1.0, (t - a) / fin if fin else 1.0, (b - t) / fout if fout else 1.0)

# ---------------------------------------------------------------- text
@functools.lru_cache(512)
def text_img(text, fname, size, color, tracking=0.0, line_gap=0.12, align='center'):
    f = font(fname, size)
    lines = text.split('\n')
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * (1 + line_gap)) if fname != 'anton' else int(size * (1.12 + line_gap))
    def line_w(s):
        return sum(f.getlength(c) for c in s) + tracking * size * max(len(s) - 1, 0)
    widths = [line_w(l) for l in lines]
    w = int(max(widths)) + 8; h = lh * len(lines) + int(size * 0.35)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = (w - widths[i]) / 2 if align == 'center' else 0
        y = i * lh
        for c in l:
            d.text((x, y), c, font=f, fill=color + (255,))
            x += f.getlength(c) + tracking * size
    return im.crop(im.getbbox()) if im.getbbox() else im

def fit_text(text, fname, size, color, maxw=960, tracking=0.0):
    im = text_img(text, fname, size, color, tracking)
    while im.width > maxw and size > 20:
        size = int(size * 0.94); im = text_img(text, fname, size, color, tracking)
    return im

def paste(canvas, im, cx, cy, alpha=1.0, scale=1.0, anchor='center'):
    if alpha <= 0.003: return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 0.999:
        a = im.getchannel('A').point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    x = int(cx - im.width / 2); y = int(cy - im.height / 2) if anchor == 'center' else int(cy)
    canvas.alpha_composite(im, (x, y)) if 0 <= x and 0 <= y and x + im.width <= W and y + im.height <= H \
        else _safe_composite(canvas, im, x, y)

def _safe_composite(canvas, im, x, y):
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0)); layer.paste(im, (x, y), im); canvas.alpha_composite(layer)

def title(canvas, t, text, a, b, cy, size=120, color=WHITE, fname='anton', rise=36, tracking=0.02, pop=False, fin=0.3, fout=0.25):
    o = win(t, a, b, fin, fout)
    if o <= 0: return
    im = fit_text(text, fname, size, color, tracking=tracking)
    p = ease_out((t - a) / max(fin, 1e-3))
    sc = 1.0 + (0.12 * (1 - p) if pop else 0)
    paste(canvas, im, W / 2, cy + rise * (1 - p), o, sc)

# ---------------------------------------------------------------- overlays
def solid(c, a=255): return Image.new('RGBA', (W, H), c + (a,))
def overlay(canvas, c, alpha):
    if alpha > 0.003: canvas.alpha_composite(solid(c, int(255 * clamp(alpha))))

@functools.lru_cache(None)
def vignette():
    y, x = np.mgrid[0:H, 0:W]; d = np.sqrt(((x - W / 2) / (W * 0.75)) ** 2 + ((y - H / 2) / (H * 0.62)) ** 2)
    a = (np.clip(d - 0.55, 0, 1) * 1.6).clip(0, 0.85)
    im = np.zeros((H, W, 4), np.uint8); im[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(im, 'RGBA')

@functools.lru_cache(None)
def vgrad(y0, y1, a0, a1):
    """Dégradé noir vertical (assombrissement derrière le texte)."""
    col = np.zeros(H, np.float32); ys = np.arange(H)
    col = np.where(ys < y0, a0, np.where(ys > y1, a1, a0 + (a1 - a0) * (ys - y0) / max(y1 - y0, 1)))
    im = np.zeros((H, W, 4), np.uint8); im[..., 3] = (np.clip(col, 0, 1) * 255).astype(np.uint8)[:, None]
    return Image.fromarray(im, 'RGBA')

@functools.lru_cache(None)
def glow(cx, cy, rx, ry, strength):
    """Halo graphique blanc très discret (dégradé radial, pas un éclairage réaliste)."""
    y, x = np.mgrid[0:H, 0:W]; d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
    a = np.exp(-d * 1.6) * strength
    im = np.zeros((H, W, 4), np.uint8); im[..., :3] = 255; im[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(im, 'RGBA')

def zoomed(img, s, cx=W / 2, cy=H / 2):
    if abs(s - 1) < 1e-4: return img.copy()
    w, h = W / s, H / s
    box = (cx - w * cx / W, cy - h * cy / H, cx - w * cx / W + w, cy - h * cy / H + h)
    return img.resize((W, H), Image.BICUBIC, box=box)

# ---------------------------------------------------------------- assets
@functools.lru_cache(None)
def arena_base():
    src = Image.open(P('assets', 'movistar_arena.webp')).convert('RGB')
    # fond : même photo, recadrée, floutée et assombrie (remplissage 9:16)
    s = H / src.height; bg = src.resize((int(src.width * s), H), Image.LANCZOS)
    x0 = (bg.width - W) // 2; bg = bg.crop((x0, 0, x0 + W, H)).filter(ImageFilter.GaussianBlur(28))
    bg = Image.blend(bg, Image.new('RGB', (W, H), BLACK), 0.55).convert('RGBA')
    # premier plan : la vraie photo, centrée sur le parquet, sans déformation
    fh = 1160; s = fh / src.height
    fg = src.resize((int(src.width * s), fh), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.6, 35, 2))
    cxs = int(415 * s); fg = fg.crop((cxs - W // 2, 0, cxs + W // 2, fh)).convert('RGBA')
    a = np.full((fh, W), 255, np.float32); fade = 150
    a[:fade] *= np.linspace(0, 1, fade)[:, None]; a[-fade:] *= np.linspace(1, 0, fade)[:, None]
    fg.putalpha(Image.fromarray(a.astype(np.uint8)))
    top = (H - fh) // 2 - 40; bg.alpha_composite(fg, (0, top))
    return bg

@functools.lru_cache(None)
def player(name, scale):
    im = Image.open(P('assets', name)).convert('RGBA')
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    rgb = im.convert('RGB').filter(ImageFilter.UnsharpMask(1.4, 30, 2)); rgb.putalpha(im.getchannel('A'))
    return rgb

PLAYER_CX = {'maledon_cut.png': 333, 'tlc_cut.png': 345}   # centre horizontal du joueur dans la photo source

@functools.lru_cache(None)
def player_scene(name):
    """Joueur détouré sur fond noir uni + halo blanc discret."""
    c = solid(BLACK); c.alpha_composite(glow(W // 2, 760, 520, 620, 0.16))
    sc = 1.95; im = player(name, sc)
    c.alpha_composite(im, (int(W / 2 - PLAYER_CX[name] * sc), 225))
    return c

LOGO_FILES = {'rm': P('logos', 'real-madrid.png'), 'asvel': P('logos', 'ldlc-asvel.png')}
LOGO_NAMES = {'rm': 'REAL MADRID', 'asvel': 'LDLC ASVEL'}

@functools.lru_cache(None)
def logo(key, size):
    f = LOGO_FILES[key]
    if os.path.exists(f):
        im = Image.open(f).convert('RGBA'); bb = im.getbbox(); im = im.crop(bb) if bb else im
        s = size / max(im.size); return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    # maquette : emplacement réservé, volontairement neutre (aucun faux logo)
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(0, size * 4, 24):
        seg = [(i, 0), (i + 12, 0)] if i < size else [(size - 1, i - size), (size - 1, i - size + 12)] if i < 2 * size else \
              [(3 * size - i, size - 1), (3 * size - i - 12, size - 1)] if i < 3 * size else [(0, 4 * size - i), (0, 4 * size - i - 12)]
        d.line(seg, fill=(110, 110, 110, 255), width=3)
    t = text_img('LOGO À FOURNIR\n' + LOGO_NAMES[key], 'oswb', max(14, size // 9), (130, 130, 130))
    im.alpha_composite(t, ((size - t.width) // 2, (size - t.height) // 2)); return im

# ---------------------------------------------------------------- shot clock (afficheur 7 segments)
SEG = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg'}

def seg_polys(x, y, w, h, th):
    s = th / 2; g = th * 0.18
    hz = lambda x0, y0, l: [(x0 + g, y0), (x0 + s + g, y0 - s), (x0 + l - s - g, y0 - s), (x0 + l - g, y0), (x0 + l - s - g, y0 + s), (x0 + s + g, y0 + s)]
    vt = lambda x0, y0, l: [(x0, y0 + g), (x0 + s, y0 + s + g), (x0 + s, y0 + l - s - g), (x0, y0 + l - g), (x0 - s, y0 + l - s - g), (x0 - s, y0 + s + g)]
    hh = h / 2
    return {'a': hz(x, y, w), 'g': hz(x, y + hh, w), 'd': hz(x, y + h, w),
            'f': vt(x, y, hh), 'b': vt(x + w, y, hh), 'e': vt(x, y + hh, hh), 'c': vt(x + w, y + hh, hh)}

@functools.lru_cache(64)
def shot_clock(text, red_bar=False):
    """Panneau électronique : chiffres LED ambre, segments éteints visibles, halo léger."""
    pw, ph = 860, 700
    panel = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(panel)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), 34, fill=(22, 22, 22, 255), outline=(70, 70, 70, 255), width=6)
    d.rounded_rectangle((34, 96, pw - 35, ph - 35), 16, fill=(8, 8, 8, 255), outline=(40, 40, 40, 255), width=3)
    bar = (230, 30, 30, 255) if red_bar else (45, 12, 12, 255)
    d.rounded_rectangle((60, 30, pw - 61, 70), 10, fill=bar)
    for sx, sy in [(18, 18), (pw - 18, 18), (18, ph - 18), (pw - 18, ph - 18)]:
        d.ellipse((sx - 7, sy - 7, sx + 7, sy + 7), fill=(55, 55, 55, 255))
    lit = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); dl = ImageDraw.Draw(lit)
    dw, dh, th = 250, 440, 46
    slots = [(150, 'tens'), (pw - 150 - dw, 'units')]
    if '.' in text: tens, units, dp = text[0], text[2], True
    else: tens, units, dp = (text[-2] if len(text) == 2 else None), text[-1], False
    for (x, which) in slots:
        ch = tens if which == 'tens' else units
        polys = seg_polys(x, 160, dw, dh, th)
        for k, poly in polys.items():
            on = ch is not None and k in SEG[ch]
            (dl if on else d).polygon(poly, fill=(AMBER + (255,)) if on else (38, 26, 8, 255))
    dpx, dpy = pw // 2, 160 + dh
    (dl if dp else d).ellipse((dpx - 24, dpy - 24, dpx + 24, dpy + 24), fill=(AMBER + (255,)) if dp else (38, 26, 8, 255))
    halo = lit.filter(ImageFilter.GaussianBlur(22))
    panel.alpha_composite(halo); panel.alpha_composite(halo); panel.alpha_composite(lit)
    if red_bar:
        rb = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); ImageDraw.Draw(rb).rounded_rectangle((60, 30, pw - 61, 70), 10, fill=(255, 40, 40, 255))
        panel.alpha_composite(rb.filter(ImageFilter.GaussianBlur(18)))
    return panel

def watermark(c, alpha=0.55):
    paste(c, text_img('ASVEL_NEWS', 'oswb', 30, WHITE, tracking=0.18), W / 2, 1640, alpha)

# ================================================================== SCÈNES
def scene1(t):  # 0–7 compte à rebours
    c = solid(BLACK)
    if 1.0 <= t < 5.0:
        k = int((t - 1.0) / 0.8); n = str(5 - k); lt = (t - 1.0) - 0.8 * k
        sc = 1.0 + 0.035 * math.exp(-lt * 14)
        paste(c, shot_clock(n), W / 2, H / 2 - 40, min(1, (t - 1.0) / 0.12) if k == 0 else 1, sc * (0.98 + 0.02 * ease_out((t - 1) / 0.5)))
        paste(c, text_img('EUROLEAGUE', 'oswb', 34, GREY, tracking=0.35), W / 2, H / 2 + 380, min(1, (t - 1.0) / 0.4) * 0.8)
    elif 5.0 <= t < 6.0:
        flick = 1.0 if int((t - 5.0) * 12) % 2 == 0 or t > 5.4 else 0.75
        paste(c, shot_clock('0.0', True), W / 2, H / 2 - 40, flick, 1.0 + 0.04 * math.exp(-(t - 5) * 12))
        paste(c, text_img('EUROLEAGUE', 'oswb', 34, GREY, tracking=0.35), W / 2, H / 2 + 380, 0.8)
    elif t >= 6.0:
        s = 1.0 + 0.05 * clamp((t - 6.0) / 8.0)
        c = zoomed(arena_base(), s)
        c.alpha_composite(vgrad(700, 1300, 0.25, 0.25))
        o = win(t, 6.0, 7.0, 0.02, 0.25)
        paste(c, text_img('MADRID.', 'anton', 230, WHITE, tracking=0.04), W / 2, H / 2 - 30, o, 1.0 + 0.1 * math.exp(-(t - 6.0) * 10))
        c.alpha_composite(vignette())
    if 5.9 <= t < 6.2: overlay(c, (255, 255, 255), 1 - abs(t - 6.0) / 0.1 if t < 6.0 else 1 - (t - 6.0) / 0.2)
    if t < 0.15: overlay(c, BLACK, 1)
    return c

def scene2(t):  # 7–14 Movistar Arena
    s = 1.0 + 0.05 * clamp((t - 6.0) / 8.0)
    c = zoomed(arena_base(), s)
    c.alpha_composite(vgrad(880, 1500, 0.0, 0.0))
    dark = 0.35 + 0.2 * ease_in_out((t - 7.0) / 0.8)
    band = vgrad(0, H, dark, dark); c.alpha_composite(band)
    c.alpha_composite(vignette())
    title(c, t, 'UNE NOUVELLE\nSOIRÉE EUROPÉENNE.', 7.15, 9.85, H / 2 - 20, 128)
    title(c, t, 'MADRID\nNOUS ATTEND.', 10.05, 11.85, H / 2 - 20, 150)
    title(c, t, 'UN NOUVEAU DÉFI.', 12.05, 13.6, H / 2 - 20, 140, pop=True)
    paste(c, text_img("PHOTO D'ARCHIVES — MOVISTAR ARENA", 'osw', 22, GREY, tracking=0.12), W / 2, 1560, 0.7)
    watermark(c)
    overlay(c, BLACK, ease_in_out((t - 13.5) / 0.5))
    return c

def scene3(t):  # 14–20 historique
    c = solid(BLACK)
    o_logo = ease_out((t - 14.15) / 0.45)
    dx = 60 * (1 - o_logo)
    title(c, t, 'LES 5 CONFRONTATIONS\nRETENUES', 14.3, 18.75, 430, 82, GOLD, tracking=0.03)
    paste(c, logo('rm', 300), 290 - dx, 760, o_logo if t < 18.7 else win(t, 0, 18.95, 0, 0.25))
    paste(c, logo('asvel', 300), 790 + dx, 760, o_logo if t < 18.7 else win(t, 0, 18.95, 0, 0.25))
    keep = win(t, 14.0, 18.95, 0.01, 0.25)
    paste(c, text_img('REAL MADRID', 'oswb', 46, WHITE, tracking=0.08), 290, 970, keep * o_logo)
    paste(c, text_img('LDLC ASVEL', 'oswb', 46, WHITE, tracking=0.08), 790, 970, keep * o_logo)
    # filet vertical doré
    if keep * o_logo > 0:
        ln = Image.new('RGBA', (3, 520), GOLD + (255,)); paste(c, ln, W / 2, 1000, keep * o_logo * 0.8)
    for (cx, num, lab, a) in [(290, '4', 'VICTOIRES', 15.5), (790, '1', 'VICTOIRE', 16.5)]:
        o = win(t, a, 18.95, 0.12, 0.25)
        p = ease_out((t - a) / 0.25)
        paste(c, text_img(num, 'anton', 300, WHITE), cx, 1170, o, 1 + 0.25 * (1 - p))
        paste(c, text_img(lab, 'oswb', 46, GOLD, tracking=0.2), cx, 1360, o)
    title(c, t, 'MAIS CHAQUE MATCH\nA SA PROPRE HISTOIRE.', 19.0, 19.82, H / 2, 108, fin=0.2, fout=0.18)
    watermark(c, 0.4)
    return c

def player_frame(t, name, t0, t1):
    s = 1.0 + 0.04 * clamp((t - t0) / (t1 - t0))
    c = zoomed(player_scene(name), s, W / 2, 760)
    c.alpha_composite(vgrad(1150, 1370, 0.0, 1.0))
    return c

def scene4(t):  # 20–27 Théo Maledon
    c = player_frame(t, 'maledon_cut.png', 20.0, 27.0)
    title(c, t, 'FORMÉ À VILLEURBANNE.', 20.35, 22.85, 1500, 96)
    title(c, t, "SES DÉBUTS PROFESSIONNELS\nÀ L'ASVEL.", 23.05, 24.85, 1500, 84)
    title(c, t, 'THÉO MALEDON', 25.05, 26.75, 1460, 150, pop=True, fin=0.2)
    title(c, t, '#12 • REAL MADRID', 25.25, 26.75, 1600, 58, GOLD, 'oswb', tracking=0.12)
    watermark_top(c)
    overlay(c, BLACK, max(1 - (t - 20.0) / 0.5, ease_in_out((t - 26.6) / 0.4)))
    return c

def watermark_top(c):
    paste(c, text_img('ASVEL_NEWS', 'oswb', 28, WHITE, tracking=0.18), W / 2, 150, 0.5)

def scene5(t):  # 27–34 Timothé Luwawu-Cabarrot + duo
    if t < 32.0:
        c = player_frame(t, 'tlc_cut.png', 27.0, 32.0)
        title(c, t, 'IL A LUI AUSSI\nPORTÉ NOS COULEURS.', 27.35, 29.85, 1480, 100)
        title(c, t, 'TIMOTHÉ\nLUWAWU-CABARROT', 30.05, 31.85, 1475, 128, pop=True, fin=0.2, fout=0.15)
        title(c, t, '#3 • REAL MADRID', 30.25, 31.85, 1665, 58, GOLD, 'oswb', tracking=0.12, fout=0.15)
        overlay(c, BLACK, max(1 - (t - 27.0) / 0.5, 0))
    else:
        c = solid(BLACK); c.alpha_composite(glow(W // 2, 820, 700, 560, 0.12))
        p = ease_out((t - 32.0) / 0.45); sc = 1.22
        for name, cx, sgn in [('maledon_cut.png', 300, -1), ('tlc_cut.png', 790, 1)]:
            im = player(name, sc); x = int(cx - PLAYER_CX[name] * sc + sgn * 260 * (1 - p))
            o = p
            layer = im if o >= 0.999 else _fade(im, o)
            _safe_composite(c, layer, x, 360)
        c.alpha_composite(vgrad(1000, 1240, 0.0, 1.0))
        title(c, t, 'DEUX ANCIENS\nVILLEURBANNAIS.', 32.15, 32.95, 1460, 112, fin=0.2, fout=0.12)
        title(c, t, 'DES RETROUVAILLES\nPARTICULIÈRES.', 33.05, 34.0, 1460, 112, GOLD, fin=0.15, fout=0.0)
        paste(c, text_img('#12 MALEDON', 'oswb', 34, GREY, tracking=0.1), 300, 1200, p)
        paste(c, text_img('#3 LUWAWU-CABARROT', 'oswb', 34, GREY, tracking=0.1), 790, 1200, p)
    watermark_top(c)
    return c

def _fade(im, o):
    im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * o))); return im

def shake(c, t, t0, amp=14, dur=0.35):
    if t0 <= t < t0 + dur:
        k = (t - t0) / dur; a = amp * (1 - k) ** 2
        dx, dy = int(a * math.sin(t * 190)), int(a * math.cos(t * 150))
        out = solid(BLACK); out.alpha_composite(c, (max(dx, 0), max(dy, 0)), (max(-dx, 0), max(-dy, 0))); return out
    return c

def scene6(t):  # 34–43 suspense
    c = solid(BLACK)
    if t < 37.0:
        p = ease_out((t - 34.25) / 0.2)
        o = win(t, 34.25, 36.85, 0.06, 0.2)
        paste(c, text_img('DEUX\nÉQUIPES.', 'anton', 270, WHITE, tracking=0.02, line_gap=0.0), W / 2, H / 2, o, 1.0 + 0.15 * (1 - p))
        c = shake(c, t, 34.25, 10)
    elif t < 39.0:
        p = ease_out((t - 37.0) / 0.5); o = win(t, 37.0, 38.9, 0.2, 0.2)
        paste(c, logo('rm', 300), 290 - 80 * (1 - p), 760, o)
        paste(c, logo('asvel', 300), 790 + 80 * (1 - p), 760, o)
        title(c, t, 'UN SEUL TERRAIN.', 37.35, 38.9, 1180, 130)
    elif t < 42.0:
        words = [('UNE', 39.15), ('SEULE', 39.75), ('REPARTIRA...', 40.4)]
        line1 = [w for w, a in words[:2] if t >= a]
        for (w, a), (cx, cy, size) in zip(words, [(330, 840, 160), (700, 840, 160), (W / 2, 1040, 175)]):
            o = clamp((t - a) / 0.45) * (1 - clamp((t - 41.85) / 0.15))
            paste(c, text_img(w, 'anton', size, WHITE, tracking=0.03), cx, cy + 20 * (1 - ease_out((t - a) / 0.45)), o)
    else:
        p = ease_out((t - 42.0) / 0.18)
        paste(c, text_img('AVEC LA', 'oswb', 80, WHITE, tracking=0.25), W / 2, 760, clamp((t - 42.0) / 0.08))
        paste(c, fit_text('VICTOIRE.', 'anton', 300, GOLD, maxw=1000), W / 2, 1010, clamp((t - 42.0) / 0.05), 1.0 + 0.35 * (1 - p))
        if t < 42.15: overlay(c, (255, 255, 255), 1 - (t - 42.0) / 0.15)
        c = shake(c, t, 42.0, 22, 0.5)
        overlay(c, BLACK, ease_in_out((t - 42.85) / 0.15))
    watermark_top(c) if t < 42 else None
    return c

def final_layout(c, t, a0):
    """Affiche finale (≥ 4 s à l'écran)."""
    def o(d): return clamp((t - (a0 + d)) / 0.35)
    def r(d): return 26 * (1 - ease_out((t - (a0 + d)) / 0.4))
    paste(c, text_img('EUROLEAGUE', 'oswb', 44, GOLD, tracking=0.4), W / 2, 330 + r(0.0), o(0.0))
    paste(c, text_img('REAL MADRID', 'anton', 128, WHITE, tracking=0.03), W / 2, 830 + r(0.15), o(0.15))
    paste(c, text_img('VS', 'anton', 70, GOLD, tracking=0.1), W / 2, 948 + r(0.25), o(0.25))
    paste(c, text_img('LDLC ASVEL', 'anton', 128, WHITE, tracking=0.03), W / 2, 1065 + r(0.35), o(0.35))
    ln = Image.new('RGBA', (520, 3), GOLD + (255,)); paste(c, ln, W / 2, 1180, o(0.5) * 0.9)
    paste(c, text_img('JEUDI 15 OCTOBRE 2026', 'oswb', 66, WHITE, tracking=0.08), W / 2, 1255 + r(0.55), o(0.55))
    paste(c, text_img('21H00', 'anton', 120, GOLD, tracking=0.06), W / 2, 1375 + r(0.65), o(0.65))
    paste(c, text_img('MOVISTAR ARENA • MADRID', 'oswb', 52, WHITE, tracking=0.1), W / 2, 1495 + r(0.75), o(0.75))
    paste(c, text_img('ASVEL_NEWS', 'oswb', 40, GREY, tracking=0.3), W / 2, 1640, o(0.95))

@functools.lru_cache(None)
def final_bg():
    bg = arena_base().filter(ImageFilter.GaussianBlur(6)); c = solid(BLACK)
    c.alpha_composite(_fade(bg, 0.22)); c.alpha_composite(vignette()); return c

def scene7(t):  # 43–50 final
    c = final_bg().copy() if t >= 44.8 else solid(BLACK)
    if t < 44.8:
        p = ease_out((t - 43.0) / 0.5)
        paste(c, logo('rm', 340), 270 - 300 * (1 - p), 960, p)
        paste(c, logo('asvel', 340), 810 + 300 * (1 - p), 960, p)
        if t >= 43.5:
            q = ease_out((t - 43.5) / 0.2)
            paste(c, text_img('VS', 'anton', 200, WHITE, tracking=0.05), W / 2, 960, q, 1.0 + 0.6 * (1 - q))
        if 43.5 <= t < 43.62: overlay(c, (255, 255, 255), 1 - (t - 43.5) / 0.12)
        c = shake(c, t, 43.5, 12, 0.3)
    else:
        k = ease_in_out((t - 44.8) / 0.4)
        size = int(340 + (240 - 340) * k)
        paste(c, logo('rm', size), 270 + (250 - 270) * k, 960 + (560 - 960) * k)
        paste(c, logo('asvel', size), 810 + (830 - 810) * k, 960 + (560 - 960) * k)
        vs_o = 1 - k
        paste(c, text_img('VS', 'anton', 200, WHITE, tracking=0.05), W / 2, 960 + (560 - 960) * k, vs_o)
        final_layout(c, t, 45.0)
        if 45.0 <= t < 45.1: overlay(c, (255, 255, 255), 0.6 * (1 - (t - 45.0) / 0.1))
    overlay(c, BLACK, ease_in_out((t - 49.4) / 0.6))
    return c

SCENES = [(0, 7, scene1), (7, 14, scene2), (14, 20, scene3), (20, 27, scene4), (27, 34, scene5), (34, 43, scene6), (43, 50.1, scene7)]
def frame(t):
    for a, b, f in SCENES:
        if a <= t < b: return f(t)

def main():
    out, audio = sys.argv[1], sys.argv[2]
    nf = int(DUR * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-profile:v', 'high',
           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000',
           '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-t', str(DUR), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(nf):
        p.stdin.write(frame(i / FPS).convert('RGB').tobytes())
        if i % 150 == 0: print(f'{i}/{nf}', flush=True)
    p.stdin.close(); p.wait(); print('done', out)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--stills':
        for tt in sys.argv[3:]:
            frame(float(tt)).convert('RGB').save(os.path.join(sys.argv[2], f'f_{float(tt):05.2f}.jpg'), quality=88)
    else:
        main()
