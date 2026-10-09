"""Bande-annonce ASVEL - Etoile Rouge de Belgrade (9:16, 1080x1920, 30 i/s, 35 s).
Motion design 2D classique (PIL + numpy) : aucun element genere par IA.
Usage : python3 render.py <date|today> <sortie.mp4 video seule> [--frames 0,150,...]"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.spatial import cKDTree
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'sources')
FONTS = os.path.join(HERE, 'fonts')
W, H, FPS, DUR = 1080, 1920, 30, 100.5
N = int(round(FPS * DUR))
CX = 525                      # axe central legerement decale a gauche (rail TikTok a droite)
RED = (226, 28, 38)
WHITE = (255, 255, 255)
GREY = (150, 150, 150)
ANTON, B8, B6 = 'Anton.ttf', 'Barlow800.ttf', 'Barlow600.ttf'

# ------------------------------------------------------------------ easing
def c01(x): return 0.0 if x < 0 else 1.0 if x > 1 else x
def seg(t, a, b): return c01((t - a) / (b - a))
def e_expo(x): x = c01(x); return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)
def e_cub(x): x = c01(x); return 1 - (1 - x) ** 3
def e_io(x): x = c01(x); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k

# ------------------------------------------------------------------ text
_fc, _tc = {}, {}
def font(name, size):
    k = (name, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(os.path.join(FONTS, name), size)
    return _fc[k]

def text(s, name, size, fill, track=0, stroke=0):
    """Returns (img, cx, baseline, left, right) : anchor points inside img. stroke > 0 : contour seul."""
    k = (s, name, size, fill, track, stroke)
    if k in _tc: return _tc[k]
    f = font(name, size)
    wid = sum(f.getlength(ch) for ch in s) + track * (len(s) - 1) if track else f.getlength(s)
    asc, desc = f.getmetrics()
    pad = int(size * 0.35)
    img = Image.new('RGBA', (int(wid) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base = pad + asc
    kw = dict(fill=(0, 0, 0, 0), stroke_width=stroke, stroke_fill=fill) if stroke else dict(fill=fill)
    if track:
        x = pad
        for ch in s:
            d.text((x, base), ch, font=f, anchor='ls', **kw); x += f.getlength(ch) + track
    else:
        d.text((pad, base), s, font=f, anchor='ls', **kw)
    r = (img, pad + wid / 2, base, pad, pad + wid)
    _tc[k] = r
    return r

def fit(s, name, maxw, maxsize, track=0):
    size = maxsize
    while size > 10:
        f = font(name, size)
        wid = sum(f.getlength(ch) for ch in s) + track * (len(s) - 1) if track else f.getlength(s)
        if wid <= maxw: return size
        size -= 2
    return size

def comp(canvas, img, x, y):
    x, y = int(round(x)), int(round(y))
    sx, sy, dx, dy = max(0, -x), max(0, -y), max(0, x), max(0, y)
    w, h = min(img.width - sx, W - dx), min(img.height - sy, H - dy)
    if w > 0 and h > 0:
        canvas.alpha_composite(img, dest=(dx, dy), source=(sx, sy, sx + w, sy + h))

def with_alpha(img, a):
    if a >= 0.999: return img
    img = img.copy()
    img.putalpha(img.getchannel('A').point(lambda v: int(v * a)))
    return img

def put(canvas, t, x, y, scale=1.0, alpha=1.0, align='c'):
    img, cx, base, left, right = t
    if alpha <= 0.003: return
    if abs(scale - 1) > 1e-3:
        img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.BICUBIC)
        cx, base, left, right = cx * scale, base * scale, left * scale, right * scale
    ax = {'c': cx, 'l': left, 'r': right}[align]
    comp(canvas, with_alpha(img, alpha), x - ax, y - base)

# ------------------------------------------------------------------ players
class Player:
    def __init__(self, path, up, eye, sharpen):
        im = Image.open(path).convert('RGBA')
        self.w, self.h = im.size
        self.eye = eye
        pm = im.convert('RGBa')
        f = 1
        while f < up:
            pm = pm.resize((pm.width * 2, pm.height * 2), Image.LANCZOS); f *= 2
        hi = pm.convert('RGBA')
        a = hi.getchannel('A')
        rgb = hi.convert('RGB').filter(ImageFilter.UnsharpMask(radius=sharpen[0], percent=sharpen[1], threshold=2))
        rgb.putalpha(a)
        self.hi, self.up = rgb, f

    def layer(self, scale, ex, ey, fade_bottom=None, side_fade=0, sweep=None):
        """Full-canvas RGBA layer with the player placed so the eyes land on (ex, ey).
        Uniform scale only: faces and jerseys are never distorted."""
        tw, th = max(1, round(self.w * scale)), max(1, round(self.h * scale))
        img = self.hi.resize((tw, th), Image.BICUBIC, reducing_gap=2.0)
        x, y = ex - self.eye[0] * scale, ey - self.eye[1] * scale
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        comp(lay, img, x, y)
        arr = np.asarray(lay).copy()
        a = arr[..., 3].astype(np.float32)
        # the photo's own bottom edge always dissolves (no hard cut line)
        b1 = y + th; b0 = b1 - 0.22 * th
        if fade_bottom: b0, b1 = min(b0, fade_bottom[0]), min(b1, fade_bottom[1])
        ys = np.arange(H, dtype=np.float32)
        vf = np.clip((b1 - ys) / max(1, b1 - b0), 0, 1)
        a *= vf[:, None]
        if side_fade:
            xs = np.arange(W, dtype=np.float32)
            hf = np.clip((xs - x) / side_fade, 0, 1) * np.clip((x + tw - xs) / side_fade, 0, 1)
            a *= hf[None, :]
        if sweep is not None and 0 < sweep < 1:                  # reflet lumineux qui balaie le joueur
            xs = np.arange(W, dtype=np.float32)[None, :]
            xr = xs + (_ys[:, None] - H / 2) * 0.45
            c = lerp(-500, W + 500, sweep)
            band = np.exp(-((xr - c) / 80) ** 2) * 70 * (a / 255)
            rgb = arr[..., :3].astype(np.float32) + band[..., None]
            arr[..., :3] = rgb.clip(0, 255).astype(np.uint8)
        arr[..., 3] = a.astype(np.uint8)
        return Image.fromarray(arr, 'RGBA')

MILLS = Player(os.path.join(SRC, 'patty-mills-detoure.png'), 4, (162, 80), (2.5, 70))
MONEKE = Player(os.path.join(SRC, 'chima-moneke-detoure.png'), 4, (170, 80), (2.5, 70))

# ------------------------------------------------------------------ lights / backgrounds
_gc = {}
def glow(cx, cy, r, color, k):
    key = (cx, cy, r, color, k)
    if key not in _gc:
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        d2 = ((xs - cx) ** 2 + (ys - cy) ** 2) / (r * r)
        g = np.exp(-d2 * 1.6) * k
        _gc[key] = g[..., None] * np.array(color, np.float32)[None, None, :]
    return _gc[key]

def bg(*glows, level=1.0):
    acc = np.zeros((H, W, 3), np.float32)
    for g in glows: acc += g * level
    return Image.fromarray(acc.clip(0, 255).astype(np.uint8), 'RGB').convert('RGBA')

_ys = np.arange(H, dtype=np.float32)
def vgrad(y0, y1, a0, a1):
    k = np.clip((_ys - y0) / (y1 - y0), 0, 1)
    return a0 + (a1 - a0) * k

def darken(canvas, mult_col):
    """mult_col : array (H,) or scalar, multiplies RGB."""
    arr = np.asarray(canvas).astype(np.float32)
    m = mult_col if np.isscalar(mult_col) else np.asarray(mult_col)[:, None, None]
    arr[..., :3] *= m
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')

def zoom(canvas, s, cx=W / 2, cy=H / 2):
    if abs(s - 1) < 1e-4: return canvas
    w, h = W / s, H / s
    x0 = min(max(cx - w / 2, 0), W - w); y0 = min(max(cy - h / 2, 0), H - h)
    return canvas.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))

# ================================================================== SCENE 1 : chronometre
SEGS = {'a': [(14, 0), (86, 0), (76, 12), (24, 12)],
        'b': [(88, 2), (100, 14), (100, 84), (90, 90), (80, 82), (80, 14)],
        'c': [(90, 90), (100, 96), (100, 166), (88, 178), (80, 166), (80, 98)],
        'd': [(24, 168), (76, 168), (86, 180), (14, 180)],
        'e': [(10, 90), (20, 98), (20, 166), (12, 178), (0, 166), (0, 96)],
        'f': [(12, 2), (20, 14), (20, 82), (10, 90), (0, 84), (0, 14)],
        'g': [(14, 90), (24, 82), (76, 82), (86, 90), (76, 98), (24, 98)]}
DIG = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd'}
BASKET_H = 1630                       # partie reelle de l'image (le bas est une bande floue)
FACE = (497, 663, 727, 858)           # face avant du boitier du chronometre (coordonnees source)
IMPACT = (642, 1120)                  # point d'impact sur la vitre du panneau
GLASS = (338, 1032, 936, 1368)        # interieur de la vitre

def _basket_base():
    im = Image.open(os.path.join(SRC, 'panier-chronometre.png')).convert('RGB').crop((0, 0, W, BASKET_H))
    a = np.asarray(im).astype(np.float32)
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    lum = (np.clip(lum / 255, 0, 1) ** 1.12) * 255 * 0.92          # noir et blanc, contraste doux
    out = np.repeat(lum[..., None], 3, 2)
    img = Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(FACE, radius=6, fill=(7, 7, 8))           # on eteint l'affichage d'origine
    return img

_BASE = _basket_base()
_dig_cache = {}
def basket_with_digit(ch):
    if ch in _dig_cache: return _dig_cache[ch]
    img = _BASE.copy().convert('RGBA')
    lit = Image.new('RGBA', img.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lit)
    ghost = Image.new('RGBA', img.size, (0, 0, 0, 0)); dg = ImageDraw.Draw(ghost)
    s = 0.86                                                       # cellule 86 x 155 px
    x0 = (FACE[0] + FACE[2]) / 2 - 50 * s
    y0 = (FACE[1] + FACE[3]) / 2 - 90 * s
    for k, poly in SEGS.items():
        pts = [(x0 + px * s, y0 + py * s) for px, py in poly]
        dg.polygon(pts, fill=(52, 8, 8, 255))
        if k in DIG[ch]: dl.polygon(pts, fill=(255, 34, 28, 255))
    img.alpha_composite(ghost)
    bl = lit.filter(ImageFilter.GaussianBlur(9))
    img.alpha_composite(bl); img.alpha_composite(bl)
    img.alpha_composite(lit)
    r = img.convert('RGB')
    _dig_cache[ch] = r
    return r

def _cracks():
    rng = np.random.default_rng(7)
    segs = []                                                      # (x0,y0,x1,y1,dist)
    rays = []
    n = 15
    for i in range(n):
        ang = 2 * math.pi * i / n + rng.uniform(-0.18, 0.18)
        x, y, d = IMPACT[0], IMPACT[1], 0.0
        pts = [(x, y, 0.0)]
        while GLASS[0] < x < GLASS[2] and GLASS[1] < y < GLASS[3] and d < 700:
            st = rng.uniform(14, 30)
            ang += rng.uniform(-0.22, 0.22)
            nx, ny = x + math.cos(ang) * st, y + math.sin(ang) * st
            segs.append((x, y, nx, ny, d)); d += st; x, y = nx, ny
            pts.append((x, y, d))
            if rng.random() < 0.10:                               # petite branche
                bx, by, ba, bd = x, y, ang + rng.choice([-1, 1]) * rng.uniform(0.4, 0.8), d
                for _ in range(rng.integers(2, 5)):
                    st = rng.uniform(10, 22); ba += rng.uniform(-0.25, 0.25)
                    nx2, ny2 = bx + math.cos(ba) * st, by + math.sin(ba) * st
                    segs.append((bx, by, nx2, ny2, bd)); bd += st; bx, by = nx2, ny2
        rays.append(pts)
    for ring in (34, 78, 140):                                     # fissures concentriques
        for i in range(n):
            if rng.random() < 0.3: continue
            p, q = rays[i], rays[(i + 1) % n]
            pa = min(p, key=lambda v: abs(v[2] - ring)); qa = min(q, key=lambda v: abs(v[2] - ring))
            if abs(pa[2] - ring) > 25 or abs(qa[2] - ring) > 25: continue
            mx = (pa[0] + qa[0]) / 2 + rng.uniform(-6, 6); my = (pa[1] + qa[1]) / 2 + rng.uniform(-6, 6)
            segs.append((pa[0], pa[1], mx, my, ring)); segs.append((mx, my, qa[0], qa[1], ring))
    return segs
CRACKS = _cracks()

def crack_layer(p):
    """p : 0..1 propagation depuis l'impact."""
    lay = Image.new('RGBA', (W, BASKET_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    lim = p * 720
    for x0, y0, x1, y1, dist in CRACKS:
        if dist <= lim:
            d.line([(x0, y0), (x1, y1)], fill=(255, 255, 255, 60), width=5)
    soft = lay.filter(ImageFilter.GaussianBlur(2.5))
    d = ImageDraw.Draw(soft)
    for x0, y0, x1, y1, dist in CRACKS:
        if dist <= lim:
            d.line([(x0, y0), (x1, y1)], fill=(245, 248, 255, 225), width=2)
    if p > 0:
        d.ellipse([IMPACT[0] - 7, IMPACT[1] - 7, IMPACT[0] + 7, IMPACT[1] + 7], fill=(255, 255, 255, 200))
    return soft

def cam(t):
    k = e_io(t / 5.6)
    s = 1.185 + 0.235 * k
    cx, cy = lerp(622, 614, k), lerp(816, 905, k)
    if 5.0 <= t < 5.2:                                             # un seul coup a l'impact, puis retour
        s *= 1 + 0.018 * (1 - seg(t, 5.0, 5.2))
    w, h = W / s, H / s
    x0 = min(max(cx - w / 2, 0), W - w); y0 = min(max(cy - h / 2, 0), BASKET_H - h)
    return (x0, y0, x0 + w, y0 + h)

_vig = None
def vignette():
    global _vig
    if _vig is None:
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xs - W / 2) / (W * 0.75)) ** 2 + ((ys - H * 0.52) / (H * 0.62)) ** 2)
        _vig = np.clip(1.08 - 0.55 * d ** 2, 0.25, 1.0)[..., None]
    return _vig

def scene1_frame(t, cracks_p=0.0):
    n = 5 - min(int(t), 5)
    src = basket_with_digit(str(n)).convert('RGBA')
    if cracks_p > 0: src.alpha_composite(crack_layer(cracks_p))
    box = cam(t)
    fr = src.convert('RGB').resize((W, H), Image.BICUBIC, box=box)
    arr = np.asarray(fr).astype(np.float32) * vignette()
    arr *= e_cub(t / 0.6)                                          # sortie du noir
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGB')

class Shatter:
    def __init__(self, base, impact_xy):
        rng = np.random.default_rng(3)
        ix, iy = impact_xy
        near = np.c_[rng.normal(ix, 170, 34), rng.normal(iy, 170, 34)]
        far = np.c_[rng.uniform(0, W, 42), rng.uniform(0, H, 42)]
        seeds = np.r_[near, far]
        ys, xs = np.mgrid[0:H:2, 0:W:2]
        _, lab = cKDTree(seeds).query(np.c_[xs.ravel(), ys.ravel()])
        lab = lab.reshape(ys.shape).repeat(2, 0).repeat(2, 1)[:H, :W]
        edge = np.zeros_like(lab, bool)
        edge[:, 1:] |= lab[:, 1:] != lab[:, :-1]; edge[1:, :] |= lab[1:, :] != lab[:-1, :]
        edge = nd.binary_dilation(edge)
        b = np.asarray(base.convert('RGB')).astype(np.float32)
        b[edge] = b[edge] * 0.4 + 255 * 0.6                          # aretes eclairees
        rgba = np.dstack([b, np.full((H, W), 255, np.float32)]).astype(np.uint8)
        self.shards = []
        for i in range(len(seeds)):
            m = lab == i
            if not m.any(): continue
            yy, xx = np.where(m)
            y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
            piece = rgba[y0:y1, x0:x1].copy(); piece[..., 3] = (m[y0:y1, x0:x1] * 255).astype(np.uint8)
            cx, cy = xx.mean(), yy.mean()
            dx, dy = cx - ix, cy - iy; dist = math.hypot(dx, dy) + 1
            sp = 900 + 260000 / (dist + 120) + rng.uniform(-150, 150)
            self.shards.append(dict(img=Image.fromarray(piece, 'RGBA'), x=x0, y=y0, cx=cx - x0, cy=cy - y0,
                                    vx=dx / dist * sp, vy=dy / dist * sp - 200, w=rng.uniform(-260, 260),
                                    z=rng.uniform(0.2, 1.1) + 300 / (dist + 200)))

    def frame(self, tt):
        can = Image.new('RGBA', (W, H), (0, 0, 0, 255))
        a = 1 - seg(tt, 0.16, 0.38)
        for s in self.shards:
            sc = 1 + s['z'] * tt
            img = s['img']
            if sc != 1: img = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
            img = img.rotate(s['w'] * tt, resample=Image.BILINEAR, expand=True)
            px = s['x'] + s['cx'] + s['vx'] * tt - img.width / 2
            py = s['y'] + s['cy'] + s['vy'] * tt + 1400 * tt * tt - img.height / 2
            comp(can, with_alpha(img, a), px, py)
        arr = np.asarray(can.convert('RGB')).astype(np.float32)
        fl = 0.45 * (1 - seg(tt, 0.0, 0.08))                       # bref flash
        arr = arr * (1 - fl) + 255 * fl
        return Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGB')

T_SHATTER = 5.55
_shatter = None
def scene1(t):
    global _shatter
    if t < 5.0: return scene1_frame(t)
    if t < T_SHATTER: return scene1_frame(t, e_expo(seg(t, 5.0, 5.18)))
    if t < 5.95:
        if _shatter is None:
            base = scene1_frame(T_SHATTER, 1.0)
            b = cam(T_SHATTER); s = W / (b[2] - b[0])
            _shatter = Shatter(base, ((IMPACT[0] - b[0]) * s, (IMPACT[1] - b[1]) * s))
        return _shatter.frame(t - T_SHATTER)
    return Image.new('RGB', (W, H), (0, 0, 0))

# ================================================================== BOITE A OUTILS MOTION DESIGN
def capline(name, size):
    b = font(name, size).getbbox('H', anchor='ls')
    return -b[1]

def kinetic(can, s, name, size, col, x, y, tr, stagger=0.035, dur=0.45, align='c', track=0, alpha=1.0, scale=1.0):
    """Typo cinetique : chaque lettre surgit de sous sa ligne de base (masque), en decale."""
    if tr <= 0 or alpha <= 0.003: return
    fill = col + (255,) if len(col) == 3 else col
    if tr >= (len(s) - 1) * stagger + dur:
        put(can, text(s, name, size, fill, track), x, y, scale, alpha, align); return
    f = font(name, size)
    asc, desc = f.getmetrics()
    adv = [f.getlength(ch) for ch in s]
    wid = sum(adv) + track * (len(s) - 1)
    pad = int(size * 0.35)
    base = pad + asc
    img = Image.new('RGBA', (int(wid) + 2 * pad, base + int(desc * 0.35)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    xx = pad
    for i, ch in enumerate(s):
        k = e_expo(seg(tr, i * stagger, i * stagger + dur))
        if k > 0: d.text((xx, base + (1 - k) * size * 1.15), ch, font=f, fill=fill, anchor='ls')
        xx += adv[i] + track
    put(can, (img, pad + wid / 2, base, pad, pad + wid), x, y, scale, alpha, align)

def echo(can, s, name, size, col, x, y, tr, n=3, track=0, dur=0.6):
    """Echos en contour qui s'ecartent une seule fois a l'impact."""
    if tr < 0 or tr > dur: return
    k = e_cub(tr / dur)
    t_o = text(s, name, size, col + (255,), track, stroke=max(2, size // 70))
    ch = capline(name, size)
    for i in range(n):
        sc = 1 + (0.08 + 0.09 * i) * k
        put(can, t_o, x, y - ch / 2 + ch / 2 * sc, scale=sc, alpha=(1 - k) * (0.6 - 0.15 * i))

def shape(can, pts, rgba):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = int(min(xs)) - 2, int(min(ys)) - 2
    lay = Image.new('RGBA', (int(max(xs)) - x0 + 4, int(max(ys)) - y0 + 4), (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(px - x0, py - y0) for px, py in pts], fill=rgba)
    comp(can, lay, x0, y0)

def para(cx, cy, w, h, skew=0.35):
    """Parallelogramme oblique centre en (cx, cy)."""
    o = h / 2 * skew
    return [(cx - w / 2 + o, cy - h / 2), (cx + w / 2 + o, cy - h / 2), (cx + w / 2 - o, cy + h / 2), (cx - w / 2 - o, cy + h / 2)]

_stp = {}
def stripes(can, t, speed, a, color=(255, 255, 255), period=64):
    key = (color, a, period)
    if key not in _stp:
        ys, xs = np.mgrid[0:H, 0:W + period]
        on = ((xs + ys) % period) < 2
        arr = np.zeros((H, W + period, 4), np.uint8)
        arr[..., :3] = color; arr[..., 3] = on * a
        _stp[key] = Image.fromarray(arr, 'RGBA')
    o = int(speed * t) % period
    can.alpha_composite(_stp[key].crop((o, 0, o + W, H)))

_rw = {}
def rows(can, word, color, a, ys, t, speed, size=250):
    """Rangees de mots en contour qui defilent en sens alternes (arriere-plan)."""
    key = (word, color, size)
    if key not in _rw:
        f = font(ANTON, size)
        unit = f.getlength(word) + size * 0.5
        n = int((W * 2) / unit) + 2
        asc, desc = f.getmetrics()
        img = Image.new('RGBA', (int(unit * n), asc + desc), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for i in range(n):
            d.text((i * unit, asc), word, font=f, anchor='ls', fill=(0, 0, 0, 0), stroke_width=2, stroke_fill=color + (255,))
        _rw[key] = (img, unit)
    img, unit = _rw[key]
    for j, y in enumerate(ys):
        o = (speed * t * (1 if j % 2 == 0 else -1)) % unit
        comp(can, with_alpha(img.crop((int(o), 0, int(o) + W, img.height)), a), 0, y)

_XR = None
def bars(old, new, p, from_left, cols):
    """Transition : barres obliques qui balaient l'ecran et devoilent la scene suivante."""
    global _XR
    if p <= 0: return old
    if p >= 1: return new
    if _XR is None:
        _XR = np.arange(W, dtype=np.float32)[None, :] + (_ys[:, None] - H / 2) * 0.35
    xr = _XR if from_left else (W - 1 - np.arange(W, dtype=np.float32))[None, :] + (_ys[:, None] - H / 2) * 0.35
    e = lerp(-340, W + 340 + 230, p)
    o = np.asarray(old.convert('RGB')).copy(); nw = np.asarray(new.convert('RGB'))
    m = xr < e - 230
    o[m] = nw[m]
    for a0, a1, c in ((0, 70, cols[0]), (70, 100, (0, 0, 0)), (100, 150, cols[1]), (150, 230, (12, 12, 12))):
        mb = (xr <= e - a0) & (xr > e - a1)
        o[mb] = c
    return Image.fromarray(o, 'RGB')

# ================================================================== SCENE 1 : cadres de visee autour du chronometre
def scene1_mg(t):
    fr = scene1(t)
    if t >= 5.0 or t < 0.15: return fr
    b = cam(t); s = W / (b[2] - b[0])
    x0, y0 = (FACE[0] - b[0]) * s, (FACE[1] - b[1]) * s
    x1, y1 = (FACE[2] - b[0]) * s, (FACE[3] - b[1]) * s
    k = e_expo(seg(t % 1.0, 0.0, 0.35))                        # se resserre a chaque seconde
    m = 26 + 46 * (1 - k)
    a = c01(seg(t, 0.15, 0.5))
    can = fr.convert('RGBA')
    L, th = 46, 5
    col = (255, 255, 255, int(230 * a))
    for cx, cy, sx, sy in ((x0 - m, y0 - m, 1, 1), (x1 + m, y0 - m, -1, 1), (x0 - m, y1 + m, 1, -1), (x1 + m, y1 + m, -1, -1)):
        shape(can, [(cx, cy), (cx + sx * L, cy), (cx + sx * L, cy + sy * th), (cx, cy + sy * th)], col)
        shape(can, [(cx, cy), (cx + sx * th, cy), (cx + sx * th, cy + sy * L), (cx, cy + sy * L)], col)
    # reticule rouge : ligne horizontale qui se referme vers le chronometre
    w = (W / 2) * (1 - e_cub(seg(t, 0.2, 4.9)))
    yc = (y0 + y1) / 2
    shape(can, [(0, yc - 1), (max(0, x0 - m - 30 - w * 0.0) * (1 - 0) , yc - 1), (max(0, x0 - m - 30), yc + 1), (0, yc + 1)], (226, 28, 38, int(160 * a)))
    shape(can, [(min(W, x1 + m + 30), yc - 1), (W, yc - 1), (W, yc + 1), (min(W, x1 + m + 30), yc + 1)], (226, 28, 38, int(160 * a)))
    return can.convert('RGB')

# ================================================================== SCENE 2 : historique
COLL, COLR = 290, 760
def scene2(t):
    u = t - 6.0
    can = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    stripes(can, t, 22, 16)
    g5 = 1 - seg(u, 0.6, 1.6) if u >= 0.6 else 0
    g9 = 1 - seg(u, 1.6, 2.6) if u >= 1.6 else 0
    if g5 > 0 or g9 > 0:
        acc = np.asarray(can.convert('RGB')).astype(np.float32)
        if g5 > 0: acc += glow(COLL, 1080, 420, (255, 255, 255), 0.18) * g5
        if g9 > 0: acc += glow(COLR, 1080, 420, (255, 30, 30), 0.30) * g9
        can = Image.fromarray(acc.clip(0, 255).astype(np.uint8)).convert('RGBA')
    # blocs obliques qui glissent derriere les chiffres
    for t0, x, col, side in ((0.5, COLL, (34, 34, 36, 255), -1), (1.5, COLR, (92, 10, 16, 255), 1)):
        k = e_expo(seg(u, t0, t0 + 0.45))
        if k > 0: shape(can, para(x + side * 700 * (1 - k), 1095, 330, 380, 0.25), col)
    # titre
    kinetic(can, 'FACE-À-FACE', B8, 58, (215, 215, 215), CX, 600, u - 0.05, stagger=0.03, dur=0.4, track=14)
    lw = 70 * e_expo(seg(u, 0.25, 0.7))
    shape(can, [(CX - 270 - lw, 577), (CX - 270, 577), (CX - 270, 581), (CX - 270 - lw, 581)], RED + (255,))
    shape(can, [(CX + 270, 577), (CX + 270 + lw, 577), (CX + 270 + lw, 581), (CX + 270, 581)], RED + (255,))
    kd = e_expo(seg(u, 0.2, 0.75)); half = 330 * kd
    shape(can, [(CX - 1, 1020 - half), (CX + 1, 1020 - half), (CX + 1, 1020 + half), (CX - 1, 1020 + half)], (90, 90, 90, 255))
    ns = min(fit('ÉTOILE ROUGE', ANTON, 400, 84), 84)
    kinetic(can, 'ASVEL', ANTON, ns, WHITE, COLL, 820, u - 0.25, stagger=0.04, dur=0.4)
    kinetic(can, 'ÉTOILE ROUGE', ANTON, ns, WHITE, COLR, 820, u - 0.35, stagger=0.03, dur=0.4)
    for t0, col, x, ch in ((0.6, WHITE, COLL, '5'), (1.6, RED, COLR, '9')):
        if u < t0: continue
        k = e_expo(seg(u, t0, t0 + 0.24))
        put(can, text(ch, ANTON, 430, col + (255,)), x, 1250, scale=1.35 - 0.35 * k, alpha=c01(seg(u, t0, t0 + 0.04)))
        echo(can, ch, ANTON, 430, col, x, 1250, u - t0 - 0.05)
        kinetic(can, 'VICTOIRES', B8, 46, (180, 180, 180), x, 1345, u - t0 - 0.12, stagger=0.025, dur=0.35, track=8)
    return zoom(can, 1 + 0.045 * e_io(u / 4.2), CX, 1000).convert('RGB')

# ================================================================== SCENES 3 & 4 : portraits
def caption(can, u, name, align, x):
    bw = 90 * e_expo(seg(u, 0.75, 1.1))
    if align == 'l': shape(can, [(x, 1357), (x + bw, 1357), (x + bw, 1365), (x, 1365)], RED + (255,))
    else: shape(can, [(x - bw, 1357), (x, 1357), (x, 1365), (x - bw, 1365)], RED + (255,))
    kinetic(can, name, B8, 96, WHITE, x, 1460, u - 0.8, stagger=0.03, dur=0.4, align=align, track=3)

def scene3(t):
    u = t - 10.0
    can = bg(glow(540, 690, 620, (255, 255, 255), 0.20), level=e_cub(seg(u, 0.0, 0.7)))
    stripes(can, t, 30, 12)
    rows(can, 'ASVEL', (255, 255, 255), 0.10, [1000, 1290, 1580], t, 70)
    # panneau oblique blanc translucide derriere le joueur
    k = e_expo(seg(u, 0.1, 0.7))
    shape(can, para(560 - 900 * (1 - k) + 25 * u, 980, 520, 1500, 0.30), (255, 255, 255, 22))
    shape(can, para(820 - 1100 * (1 - e_expo(seg(u, 0.2, 0.8))) + 40 * u, 1100, 26, 1300, 0.30), RED + (255,))
    sz = fit('ASVEL', ANTON, 950, 520)
    kinetic(can, 'ASVEL', ANTON, sz, (245, 245, 245), 540 + 18 * u, 492, u - 0.15, stagger=0.06, dur=0.55)
    echo(can, 'ASVEL', ANTON, sz, (255, 255, 255), 540 + 18 * u, 492, u - 0.5, n=2)
    sc = lerp(3.42, 2.94, e_io(seg(u, 0.4, 3.0)))
    can.alpha_composite(MILLS.layer(sc, 540 - 160 * (1 - e_expo(seg(u, 0.0, 0.7))) - 12 * u, 770,
                                    fade_bottom=(1270, 1640), sweep=seg(u, 1.0, 1.9)))
    can = darken(can, vgrad(1180, 1620, 1.0, 0.18))
    caption(can, u, 'PATTY MILLS', 'l', 92)
    return can.convert('RGB')

def scene4(t):
    u = t - 14.0
    can = bg(glow(540, 690, 620, (255, 25, 30), 0.30), level=e_cub(seg(u, 0.0, 0.7)))
    stripes(can, t, -30, 12, (255, 60, 60))
    rows(can, 'ÉTOILE ROUGE', (255, 40, 40), 0.13, [1000, 1290, 1580], t, -70)
    k = e_expo(seg(u, 0.1, 0.7))
    shape(can, para(520 + 900 * (1 - k) - 25 * u, 980, 520, 1500, -0.30), (255, 30, 40, 30))
    shape(can, para(260 + 1100 * (1 - e_expo(seg(u, 0.2, 0.8))) - 40 * u, 1100, 26, 1300, -0.30), WHITE + (255,))
    sz = fit('ÉTOILE ROUGE', ANTON, 950, 400)
    kinetic(can, 'ÉTOILE ROUGE', ANTON, sz, RED, 540 - 18 * u, 418, u - 0.15, stagger=0.035, dur=0.5)
    echo(can, 'ÉTOILE ROUGE', ANTON, sz, RED, 540 - 18 * u, 418, u - 0.5, n=2)
    kinetic(can, 'DE BELGRADE', B8, 74, (245, 245, 245), 540 - 18 * u, 500, u - 0.45, stagger=0.03, dur=0.4, track=14)
    sc = lerp(3.72, 3.20, e_io(seg(u, 0.4, 3.0)))
    can.alpha_composite(MONEKE.layer(sc, 540 + 160 * (1 - e_expo(seg(u, 0.0, 0.7))) + 12 * u, 770,
                                     fade_bottom=(1270, 1640), sweep=1 - seg(u, 1.0, 1.9) if u > 1.0 else None))
    can = darken(can, vgrad(1180, 1620, 1.0, 0.18))
    caption(can, u, 'CHIMA MONEKE', 'r', 905)
    return can.convert('RGB')

# ================================================================== SCENE 5 : montee en tension
def shot(kind, v, t):
    z = 1 + 0.06 * v
    if kind == 'black':
        can = Image.new('RGBA', (W, H), (0, 0, 0, 255))
        stripes(can, t, 160, 22, (255, 40, 40)); return can
    if kind.startswith('split'):
        tight = kind == 'split2'
        can = bg(glow(270, 760, 500, (255, 255, 255), 0.12), glow(810, 760, 500, (255, 25, 30), 0.22))
        l = MILLS.layer((3.40 if tight else 2.80) * z, 290 + 30 * v, 790)
        r = MONEKE.layer((3.7 if tight else 3.05) * z, 790 - 30 * v, 790)
        xs = np.arange(W)[None, :]; edge = 540 + (_ys[:, None] - H / 2) * -0.10
        la = np.asarray(l).copy(); la[..., 3] = (la[..., 3] * (xs < edge - 3)).astype(np.uint8)
        ra = np.asarray(r).copy(); ra[..., 3] = (ra[..., 3] * (xs > edge + 3)).astype(np.uint8)
        can.alpha_composite(Image.fromarray(la)); can.alpha_composite(Image.fromarray(ra))
        shape(can, [(540 + H / 2 * 0.10 - 3, 0), (540 + H / 2 * 0.10 + 3, 0), (540 - H / 2 * 0.10 + 3, H), (540 - H / 2 * 0.10 - 3, H)], RED + (255,))
        return can
    if kind == 'mills_tight':
        can = bg(glow(540, 760, 560, (255, 255, 255), 0.14))
        can.alpha_composite(MILLS.layer(3.63 * z, 540 - 20 * v, 820)); return can
    if kind == 'moneke_tight':
        can = bg(glow(540, 760, 560, (255, 25, 30), 0.26))
        can.alpha_composite(MONEKE.layer(3.95 * z, 540 + 20 * v, 820)); return can
    if kind == 'mills_side':
        can = bg(glow(380, 760, 560, (255, 255, 255), 0.14))
        can.alpha_composite(MILLS.layer(3.22 * z, 360 + 40 * v, 800)); return can
    if kind == 'moneke_side':
        can = bg(glow(700, 760, 560, (255, 25, 30), 0.26))
        can.alpha_composite(MONEKE.layer(3.5 * z, 720 - 40 * v, 800)); return can
    raise ValueError(kind)

CUTS = [(18.00, 'split'), (19.19, 'black'),
        (20.00, 'mills_tight'), (20.41, 'moneke_tight'), (21.02, 'black'), (21.63, 'split2'),
        (22.00, 'moneke_side'), (22.24, 'mills_side'), (22.55, 'moneke_tight'), (22.85, 'mills_tight'),
        (23.16, 'black'), (23.46, 'split'), (23.77, 'black'), (24.0, None)]
PHRASES = [(18.0, ['DEUX ÉQUIPES.'], [WHITE]),
           (20.0, ['UN MATCH.'], [WHITE]),
           (22.0, ['UN SEUL REPARTIRA', 'AVEC LA VICTOIRE.'], [WHITE, RED])]
LINE_TARGETS = [(18.0, 150), (20.0, 300), (22.0, 430), (23.62, 525)]

def scene5(t):
    for i in range(len(CUTS) - 1):
        if CUTS[i][0] <= t < CUTS[i + 1][0]:
            a, kind = CUTS[i]; b = CUTS[i + 1][0]; break
    can = shot(kind, (t - a) / (b - a), t)
    if kind != 'black': can = darken(can, 0.40)
    L = 80.0
    for t0, tgt in LINE_TARGETS:
        if t >= t0: L = lerp(L, tgt, e_expo(seg(t, t0, t0 + 0.32)))
    shape(can, [(0, 1236), (L, 1236), (L, 1242), (0, 1242)], WHITE + (255,))
    shape(can, [(W - L, 1236), (W, 1236), (W, 1242), (W - L, 1242)], RED + (255,))
    shape(can, [(0, 712), (L * 0.8, 712), (L * 0.8, 714), (0, 714)], RED + (255,))
    shape(can, [(W - L * 0.8, 712), (W, 712), (W, 714), (W - L * 0.8, 714)], WHITE + (255,))
    for p0, lines, cols in reversed(PHRASES):
        if t >= p0:
            size = min(fit(s, ANTON, 860, 230) for s in lines)
            lh = size * 1.02
            y0 = 1000 - (len(lines) - 1) * lh / 2 + size * 0.36
            for j, (s, c) in enumerate(zip(lines, cols)):
                kinetic(can, s, ANTON, size, c, CX, y0 + j * lh, t - p0 - j * 0.12, stagger=0.028, dur=0.32)
                echo(can, s, ANTON, size, c, CX, y0 + j * lh, t - p0 - j * 0.12 - 0.25, n=2, dur=0.45)
            break
    # coup de zoom sur chaque nouvelle phrase
    p0 = max(p for p, _, _ in PHRASES if t >= p)
    return zoom(can, 1 + 0.07 * (1 - e_expo(seg(t, p0, p0 + 0.35))), CX, 1000).convert('RGB')

# ================================================================== SCENES 6 & 7 : face-a-face, revelation, affiche
T_DARK, READY_END, T_REVEAL, T_INFO, T_END = 25.0, 26.5, 93.36, 94.36, 99.95   # revelation sur un temps fort (musique 106,26 s)

def scene6a(t):
    u = t - 24.0
    lv = 1 - e_io(seg(t, 24.45, T_DARK))
    can = bg(glow(280, 780, 520, (255, 255, 255), 0.13), glow(800, 780, 520, (255, 25, 30), 0.24))
    stripes(can, t, 12, 10)
    k = e_io(u / 1.9)
    l = MILLS.layer(2.83, 250 + 45 * k, 820, fade_bottom=(1350, 1650))
    r = MONEKE.layer(3.08, 830 - 45 * k, 820, fade_bottom=(1350, 1650))
    xs = np.arange(W)[None, :]
    la = np.asarray(l).copy(); la[..., 3] = (la[..., 3] * np.clip((560 - xs) / 40, 0, 1)).astype(np.uint8)
    ra = np.asarray(r).copy(); ra[..., 3] = (ra[..., 3] * np.clip((xs - 520) / 40, 0, 1)).astype(np.uint8)
    can.alpha_composite(Image.fromarray(la)); can.alpha_composite(Image.fromarray(ra))
    hl = 700 * e_expo(seg(u, 0.0, 0.6))
    shape(can, [(539, 900 - hl), (541, 900 - hl), (541, 900 + hl), (539, 900 + hl)], (200, 25, 30, 255))
    return darken(can, lv).convert('RGB')

READY = [(25.05, 'ARE', WHITE), (25.36, 'YOU', WHITE), (25.67, 'READY?', RED)]
def ready(t):
    """Ecran sombre avant la revelation : ARE / YOU / READY? tombent un mot par temps."""
    can = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    size = fit('READY?', ANTON, 860, 300)
    lh = capline(ANTON, size) * 1.18
    y0 = 960 - lh + capline(ANTON, size) / 2
    for i, (t0, w, col) in enumerate(READY):
        kinetic(can, w, ANTON, size, col, CX, y0 + i * lh, t - t0, stagger=0.04, dur=0.28)
        echo(can, w, ANTON, size, col, CX, y0 + i * lh, t - t0 - 0.12, n=2, dur=0.45)
    return zoom(can, 1 + 0.05 * e_io(seg(t, T_DARK, READY_END)), CX, 960).convert('RGB')

def poster(t, date_line):
    ur = t - T_REVEAL
    can = bg(glow(285, 420, 520, (255, 255, 255), 0.15), glow(800, 420, 520, (255, 25, 30), 0.26))
    stripes(can, 0, 0, 9)
    # formes obliques qui arrivent de cotes opposes, puis s'arretent net
    k = e_expo(seg(ur, 0.0, 0.5))
    shape(can, para(250 - 900 * (1 - k), 470, 300, 760, 0.3), (255, 255, 255, 20))
    shape(can, para(830 + 900 * (1 - k), 470, 300, 760, 0.3), (226, 28, 38, 45))
    kp = e_expo(seg(ur, 0.0, 0.55))
    sw = seg(ur, 0.55, 1.25) if 0.55 < ur < 1.25 else None
    can.alpha_composite(MILLS.layer(2.53, 285 - 620 * (1 - kp), 335, fade_bottom=(600, 790), sweep=sw))
    can.alpha_composite(MONEKE.layer(2.75, 805 + 620 * (1 - kp), 335, fade_bottom=(600, 790), sweep=sw))
    kn = e_expo(seg(ur, 0.0, 0.34))
    sc = 1.14 - 0.14 * kn
    def P(s, f, size, col, y, delay, track=0):
        yy = 1000 + (y - 1000) * sc
        kinetic(can, s, f, size, col, CX, yy, ur - delay, stagger=0.025, dur=0.3, track=track, scale=sc)
    er = fit('ÉTOILE ROUGE', ANTON, 640, 112)
    P('ASVEL', ANTON, 190, WHITE, 985, 0.0)
    P('VS', ANTON, 60, RED, 1056, 0.12, track=6)
    P('ÉTOILE ROUGE', ANTON, er, WHITE, 1166, 0.08)
    P('DE BELGRADE', ANTON, er, WHITE, 1264, 0.14)
    echo(can, 'ASVEL', ANTON, 190, WHITE, CX, 985, ur - 0.2, n=3)
    if t >= T_INFO:
        ui = t - T_INFO
        hw = 210 * e_expo(seg(ui, 0.0, 0.3))
        shape(can, [(CX - hw, 1298), (CX + hw, 1298), (CX + hw, 1302), (CX - hw, 1302)], RED + (255,))
        items = [(date_line, B8, 58, WHITE, 1372, 2), ('ASTROBALLE', B6, 50, (225, 225, 225), 1430, 6),
                 ('EUROLEAGUE', B8, 42, RED, 1480, 10), ('beIN SPORTS & EuroLeague TV', B6, 42, (225, 225, 225), 1528, 1)]
        for i, (s, f, size, col, y, tr) in enumerate(items):
            kinetic(can, s, f, size, col, CX, y, ui - 0.06 - i * 0.09, stagger=0.012, dur=0.3, track=tr)
        kinetic(can, 'ASVEL_NEWS', B6, 30, (150, 150, 150), CX, 1578, ui - 0.5, stagger=0.02, dur=0.3, track=4)
    arr = np.asarray(can.convert('RGB')).astype(np.float32)
    fl = 0.32 * (1 - seg(ur, 0.0, 0.12))
    arr = arr * (1 - fl) + 255 * fl
    arr *= 1 - e_io(seg(t, T_END, DUR - 0.03))
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGB')

# ================================================================== SCENE CLIPS : le duel (actions reelles fournies)
UP = os.environ.get('CLIPS_DIR', '/root/.claude/uploads/885fa05c-4277-5de5-8886-1583c42ed6b9') + '/'   # clips fournis (non versionnes)
VSRC = {'M1': ('3d6d2ed1-Patty_Mills_Cholet_TikTok_nettoye.mp4', 718, 484),   # bande d'image nette (y, hauteur)
        'M2': ('19eec89f-Patty_Mills_TikTok_sans_son.mp4', 656, 480),       # caches flous du bas exclus
        'K1': ('3f4bb3e7-Moneke_Fenerbahce_TikTok.mp4', 706, 504),
        'K2': ('ca0e0f4a-Moneke_Olympiacos_TikTok.mp4', 706, 504)}
PW, PH, PY = 1080, 700, 930                     # panneau video 1080 x 700 centre en y = 930 : cadrage resserre (x1,46)
# (source, debut, fin, ralenti (debut, fin, facteur) ou None, suivi [(temps source, x du joueur dans l'image d'origine)])
def C(src, a, b, slow=None, track=None):
    """Une action : la camera de retransmission garde l'action au centre (x = 540) sauf suivi explicite."""
    return (src, a, b, slow, track or [(a, 540), (b, 540)])
# toutes les actions des 4 videos fournies, en entier (coupes d'origine a +-0,05 s)
MILLS_CLIPS = [C('M1', 15.57, 16.37, None, [(15.57, 340), (16.37, 420)]),            # gros plan Patty Mills
               C('M2', 0.00, 4.37),
               C('M2', 4.45, 6.75, None, [(4.45, 690), (4.9, 650), (5.3, 620), (5.9, 610), (6.3, 700), (6.75, 720)]),  # tir dans le coin
               C('M2', 8.93, 13.07),
               C('M2', 17.43, 21.85),
               C('M1', 0.00, 5.28), C('M1', 5.33, 10.17), C('M1', 10.23, 14.14), C('M1', 14.20, 15.55),
               C('M2', 13.10, 15.60, (14.15, 14.75, 0.5), [(13.1, 260), (13.45, 280), (14.2, 330), (14.6, 390), (14.85, 430),
                                                         (15.05, 690), (15.6, 680)])]    # final : tir en suspension sur le n.1
MONEKE_CLIPS = [C('K2', 0.00, 3.87),                                                   # gros plan puis tir filme sous le panier
                C('K1', 0.00, 4.90, (2.00, 2.60, 0.5), [(0.0, 700), (0.9, 790), (1.5, 762), (2.0, 740), (2.4, 750), (4.9, 700)]),
                C('K1', 5.03, 8.37), C('K1', 8.43, 11.67), C('K1', 11.73, 16.07), C('K1', 16.13, 20.85),
                C('K2', 4.23, 8.57),
                C('K2', 8.63, 14.97)]                                                  # le debut s'ajuste pour finir a la revelation
T_MILLS = 26.5

def _dur(a, b, slow):
    if slow: s0, s1, f = slow; return (s0 - a) + (s1 - s0) / f + (b - s1)
    return b - a

def _plan(clips, t0, t_end=None):
    """Liste (debut, fin, source, temps local -> temps source, a, b, suivi). Avec t_end, le dernier clip
    garde sa fin (le panier) et son debut est avance pour que le bloc finisse a t_end."""
    out, t = [], t0
    for i, (src, a, b, slow, track) in enumerate(clips):
        if t_end is not None and i == len(clips) - 1: a = b - (t_end - t)
        d = _dur(a, b, slow)
        def fmap(u, a=a, slow=slow):
            if not slow: return a + u
            s0, s1, f = slow
            if u < s0 - a: return a + u
            if u < s0 - a + (s1 - s0) / f: return s0 + (u - (s0 - a)) * f
            return s1 + (u - (s0 - a) - (s1 - s0) / f)
        out.append((t, t + d, src, fmap, a, b, track)); t += d
    return out
_PM = _plan(MILLS_CLIPS, T_MILLS)
T_MONEKE = _PM[-1][1]
PLAN = _PM + _plan(MONEKE_CLIPS, T_MONEKE, T_REVEAL)
CLIP_CUTS = [c[0] for c in PLAN[1:] if abs(c[0] - T_MONEKE) > 1e-6]   # debuts de clip (hors debut de bloc)

_vc = {}
def _decode(src, a, b):
    key = (src, a, b)
    if key not in _vc:
        if len(_vc) >= 2: _vc.pop(next(iter(_vc)))
        fn, y0, h = VSRC[src]
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{max(0, a - 0.05):.3f}', '-i', UP + fn, '-t', f'{b - a + 0.6:.3f}',
                              '-an', '-vf', f'crop=1080:{h}:0:{y0}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True).stdout
        _vc[key] = (np.frombuffer(raw, np.uint8).reshape(-1, h, 1080, 3), max(0, a - 0.05))
    return _vc[key]

def clip_frame(src, a, b, ts, track, z=1.0):
    """Image du clip au temps source ts, recadree sur le joueur (suivi interpole) et mise a l'echelle du panneau."""
    fr, base = _decode(src, a, b)
    x = max(0.0, (min(ts, b) - base) * 30)
    i = int(x); k = x - i
    i = min(i, len(fr) - 1); j = min(i + 1, len(fr) - 1)
    im = fr[i] if (k < 0.05 or i == j) else (fr[i] * (1 - k) + fr[j] * k).astype(np.uint8)
    h = im.shape[0]
    cx = float(np.interp(ts, [p[0] for p in track], [p[1] for p in track]))
    wh, hh = h * PW / PH / z, h / z
    x0 = min(max(cx - wh / 2, 0), 1080 - wh); y0 = (h - hh) / 2
    return Image.fromarray(im).resize((PW, PH), Image.BICUBIC, box=(x0, y0, x0 + wh, y0 + hh))

def clips(t):
    mills = t < T_MONEKE
    tb = T_MILLS if mills else T_MONEKE
    ub = t - tb
    for c0, c1, src, fmap, a, b, track in PLAN:
        if c0 <= t < c1 or c1 >= T_REVEAL - 1e-6 and t >= c0: break
    u = t - c0
    if mills: can = bg(glow(540, 930, 700, (255, 255, 255), 0.12))
    else: can = bg(glow(540, 930, 700, (255, 25, 30), 0.24))
    stripes(can, t, 140 if mills else -140, 14, (255, 255, 255) if mills else (255, 60, 60))
    rows(can, 'MILLS' if mills else 'MONEKE', (255, 255, 255) if mills else (255, 40, 40), 0.12, [1350, 1600], t, 120 if mills else -120, size=230)
    # panneau video : coup de zoom a chaque nouvelle action, puis lente poussee
    z = (1 + 0.10 * (1 - e_expo(u / 0.28))) * (1 + 0.035 * u)
    img = clip_frame(src, a, b, fmap(u), track, z)
    pk = e_expo(seg(ub, 0.0, 0.35))
    py = PY - PH / 2 + (1 - pk) * 120
    comp(can, img.convert('RGBA'), 0, py)
    fl = 0.55 * (1 - seg(u, 0.0, 0.12))
    if fl > 0: shape(can, [(0, py), (W, py), (W, py + PH), (0, py + PH)], (255, 255, 255, int(255 * fl)))
    col = (255, 255, 255) if mills else RED
    lw = W * e_expo(seg(ub, 0.05, 0.5))
    shape(can, [(0, py - 10), (lw, py - 10), (lw, py - 4), (0, py - 4)], col + (255,))
    shape(can, [(W - lw, py + PH + 4), (W, py + PH + 4), (W, py + PH + 10), (W - lw, py + PH + 10)], (RED if mills else WHITE) + (255,))
    # en-tete : equipe + nom du joueur
    team, name = ('ASVEL', 'PATTY MILLS') if mills else ('ÉTOILE ROUGE', 'CHIMA MONEKE')
    kinetic(can, team, B8, 54, RED if mills else WHITE, CX, 340, ub - 0.05, stagger=0.03, dur=0.35, track=12)
    sz = fit(name, ANTON, 900, 170)
    kinetic(can, name, ANTON, sz, WHITE if mills else RED, CX, 500, ub - 0.1, stagger=0.035, dur=0.4)
    echo(can, name, ANTON, sz, WHITE if mills else RED, CX, 500, ub - 0.3, n=2)
    return can.convert('RGB')

# ================================================================== timeline
TRANS = [(T_MONEKE, clips, clips, False, (RED, (255, 255, 255))),
         (10.0, scene2, scene3, True, ((255, 255, 255), RED)),
         (14.0, scene3, scene4, False, (RED, (255, 255, 255))),
         (18.0, scene4, scene5, True, ((255, 255, 255), RED))]

def frame(i, date_line):
    return frame_t(i / FPS, date_line)

def frame_t(t, date_line):
    # transition a chaque changement de clip : balayage en barres obliques, sens et couleurs alternes
    for k, B in enumerate(CLIP_CUTS):
        if B - 0.10 <= t < B + 0.22:
            p = e_cub(seg(t, B - 0.10, B + 0.22))
            mills = B < T_MONEKE
            cols = [((255, 255, 255), RED), (RED, (255, 255, 255))][k % 2] if mills else [(RED, (255, 255, 255)), ((255, 255, 255), RED)][k % 2]
            return bars(clips(min(t, B - 0.001)), clips(max(t, B)), p, k % 2 == 0, cols)
    for B, a, b, fl, cols in TRANS:
        if B - 0.12 <= t < B + 0.36:
            p = e_cub(seg(t, B - 0.12, B + 0.36))
            return bars(a(min(t, B - 0.001) if a is b else t), b(max(t, B)), p, fl, cols)
    if t < 6.0: return scene1_mg(t)
    if t < 10.0: return scene2(t)
    if t < 14.0: return scene3(t)
    if t < 18.0: return scene4(t)
    if t < 24.0: return scene5(t)
    if t < T_DARK: return scene6a(t)
    if t < READY_END: return ready(t)
    if t < T_REVEAL: return clips(t)
    return poster(t, date_line)

DATES = {'date': 'MARDI 13 OCTOBRE • 20H00', 'today': 'AUJOURD’HUI • 20H00'}

if __name__ == '__main__':
    date_line = DATES[sys.argv[1]]
    out = sys.argv[2]
    if '--frames' in sys.argv:
        idx = [int(v) for v in sys.argv[sys.argv.index('--frames') + 1].split(',')]
        os.makedirs(out, exist_ok=True)
        for i in idx: frame(i, date_line).save(os.path.join(out, f'f{i:04d}.png'))
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '14',
                          '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(N):
        p.stdin.write(frame(i, date_line).tobytes())
        if i % 60 == 0: print(i, flush=True)
    p.stdin.close(); p.wait()
