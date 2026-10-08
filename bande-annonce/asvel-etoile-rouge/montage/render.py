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
W, H, FPS, DUR = 1080, 1920, 30, 35
N = FPS * DUR
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

def text(s, name, size, fill, track=0):
    """Returns (img, cx, baseline, left, right) : anchor points inside img."""
    k = (s, name, size, fill, track)
    if k in _tc: return _tc[k]
    f = font(name, size)
    wid = sum(f.getlength(ch) for ch in s) + track * (len(s) - 1) if track else f.getlength(s)
    asc, desc = f.getmetrics()
    pad = int(size * 0.35)
    img = Image.new('RGBA', (int(wid) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base = pad + asc
    if track:
        x = pad
        for ch in s:
            d.text((x, base), ch, font=f, fill=fill, anchor='ls'); x += f.getlength(ch) + track
    else:
        d.text((pad, base), s, font=f, fill=fill, anchor='ls')
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

    def layer(self, scale, ex, ey, fade_bottom=None, side_fade=0):
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

# ================================================================== SCENE 2 : historique
COLL, COLR = 290, 760
def scene2(t):
    u = t - 6.0
    can = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    # lumiere du 5 / du 9 au moment de l'impact
    g5 = 1 - seg(u, 0.6, 1.4) if u >= 0.6 else 0
    g9 = 1 - seg(u, 1.6, 2.4) if u >= 1.6 else 0
    if g5 > 0 or g9 > 0:
        acc = np.zeros((H, W, 3), np.float32)
        if g5 > 0: acc += glow(COLL, 1080, 420, (255, 255, 255), 0.16) * g5
        if g9 > 0: acc += glow(COLR, 1080, 420, (255, 30, 30), 0.26) * g9
        can = Image.fromarray(acc.clip(0, 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(can)
    # titre
    k = e_cub(seg(u, 0.05, 0.45))
    tt = text('FACE-À-FACE', B8, 58, (215, 215, 215, 255), track=14)
    put(can, tt, CX, 600 + 24 * (1 - k), alpha=k)
    lw = 70 * k
    d.line([(CX - 270 - lw, 579), (CX - 270, 579)], fill=RED, width=4)
    d.line([(CX + 270, 579), (CX + 270 + lw, 579)], fill=RED, width=4)
    # separateur
    kd = e_expo(seg(u, 0.2, 0.75)); half = 300 * kd
    d.line([(CX, 1020 - half), (CX, 1020 + half)], fill=(70, 70, 70), width=2)
    # noms
    ns = min(fit('ÉTOILE ROUGE', ANTON, 400, 84), 84)
    kn = e_expo(seg(u, 0.22, 0.75)); an = c01(seg(u, 0.22, 0.4))
    put(can, text('ASVEL', ANTON, ns, WHITE + (255,)), COLL - 70 * (1 - kn), 820, alpha=an)
    put(can, text('ÉTOILE ROUGE', ANTON, ns, WHITE + (255,)), COLR + 70 * (1 - kn), 820, alpha=an)
    # chiffres : un impact par chiffre
    for t0, col, x, ch in ((0.6, WHITE, COLL, '5'), (1.6, RED, COLR, '9')):
        if u < t0: continue
        k = e_expo(seg(u, t0, t0 + 0.24))
        put(can, text(ch, ANTON, 430, col + (255,)), x, 1250 - 50 * (1 - k), scale=1.16 - 0.16 * k,
            alpha=c01(seg(u, t0, t0 + 0.05)))
        kv = e_cub(seg(u, t0 + 0.08, t0 + 0.4))
        put(can, text('VICTOIRES', B8, 46, (175, 175, 175, 255), track=8), x, 1345 + 16 * (1 - kv), alpha=kv)
    can = zoom(can, 1 + 0.035 * e_io(u / 4.0), CX, 1000)
    out = darken(can, 1 - seg(u, 3.88, 4.0))
    return out.convert('RGB')

# ================================================================== SCENES 3 & 4 : portraits
def wipe(can, u, from_left, bar_cols):
    """Masque graphique lateral : un bord oblique balaie l'image, suivi de deux barres."""
    k = e_expo(seg(u, 0.0, 0.55))
    e = lerp(-420, W + 420, k)
    xs = np.arange(W, dtype=np.float32)[None, :]
    ys = _ys[:, None]
    edge = e + (ys - H / 2) * 0.22
    if from_left: m = xs < edge
    else:
        edge = W - e - (ys - H / 2) * 0.22; m = xs > edge
    arr = np.asarray(can).copy()
    arr[..., :3] = (arr[..., :3] * m[..., None]).astype(np.uint8)
    can = Image.fromarray(arr, 'RGBA')
    if k < 0.999:
        d = ImageDraw.Draw(can)
        sgn = 1 if from_left else -1
        for off, wid, col in ((0, 16, bar_cols[0]), (-34, 6, bar_cols[1])):
            xa = (e if from_left else W - e) + sgn * off
            top, bot = xa + (0 - H / 2) * 0.22 * sgn, xa + (H / 2) * 0.22 * sgn
            d.polygon([(top - wid / 2, 0), (top + wid / 2, 0), (bot + wid / 2, H), (bot - wid / 2, H)], fill=col)
    return can

def caption(can, u, name, align, x):
    k = e_cub(seg(u, 0.7, 1.05))
    sgn = -1 if align == 'l' else 1
    d = ImageDraw.Draw(can)
    bw = 90 * e_expo(seg(u, 0.65, 1.0))
    if align == 'l': d.rectangle([x, 1357, x + bw, 1365], fill=RED)
    else: d.rectangle([x - bw, 1357, x, 1365], fill=RED)
    put(can, text(name, B8, 96, WHITE + (255,), track=3), x + sgn * 40 * (1 - k), 1460, alpha=k, align=align)

def scene3(t):
    u = t - 10.0
    can = bg(glow(540, 690, 620, (255, 255, 255), 0.20), level=e_cub(seg(u, 0.1, 0.8)))
    sz = fit('ASVEL', ANTON, 950, 520)
    kt = e_expo(seg(u, 0.12, 0.7))
    put(can, text('ASVEL', ANTON, sz, (245, 245, 245, 255)), 540 - 70 * (1 - kt) + 22 * e_io(u / 4), 492,
        alpha=c01(seg(u, 0.12, 0.35)))
    sc = lerp(3.42, 2.94, e_io(seg(u, 0.5, 3.2)))
    can.alpha_composite(MILLS.layer(sc, 540 - 10 * e_io(u / 4), 770, fade_bottom=(1270, 1640)))
    can = darken(can, vgrad(1180, 1620, 1.0, 0.18))
    caption(can, u, 'PATTY MILLS', 'l', 92)
    can = wipe(can, u, True, ((255, 255, 255), RED))
    return can.convert('RGB')

def scene4(t):
    u = t - 14.0
    can = bg(glow(540, 690, 620, (255, 25, 30), 0.30), level=e_cub(seg(u, 0.1, 0.8)))
    sz = fit('ÉTOILE ROUGE', ANTON, 950, 400)
    kt = e_expo(seg(u, 0.12, 0.7)); at = c01(seg(u, 0.12, 0.35))
    dx = 70 * (1 - kt) - 22 * e_io(u / 4)
    put(can, text('ÉTOILE ROUGE', ANTON, sz, RED + (255,)), 540 + dx, 418, alpha=at)
    put(can, text('DE BELGRADE', B8, 74, (245, 245, 245, 255), track=14), 540 + dx, 500, alpha=at)
    sc = lerp(3.72, 3.20, e_io(seg(u, 0.5, 3.2)))
    can.alpha_composite(MONEKE.layer(sc, 540 + 10 * e_io(u / 4), 770, fade_bottom=(1270, 1640)))
    can = darken(can, vgrad(1180, 1620, 1.0, 0.18))
    caption(can, u, 'CHIMA MONEKE', 'r', 905)
    can = wipe(can, u, False, (RED, (255, 255, 255)))
    return can.convert('RGB')

# ================================================================== SCENE 5 : montee en tension
def shot(kind, v):
    """v : 0..1 progression du plan. Leger changement d'echelle, jamais de deformation."""
    z = 1 + 0.045 * v
    if kind == 'black':
        return Image.new('RGBA', (W, H), (0, 0, 0, 255))
    if kind.startswith('split'):
        tight = kind == 'split2'
        can = bg(glow(270, 760, 500, (255, 255, 255), 0.12), glow(810, 760, 500, (255, 25, 30), 0.22))
        l = MILLS.layer((3.40 if tight else 2.80) * z, 290, 790)
        r = MONEKE.layer((3.7 if tight else 3.05) * z, 790, 790)
        xs = np.arange(W)[None, :]; edge = 540 + (_ys[:, None] - H / 2) * -0.10
        la = np.asarray(l).copy(); la[..., 3] = (la[..., 3] * (xs < edge - 3)).astype(np.uint8)
        ra = np.asarray(r).copy(); ra[..., 3] = (ra[..., 3] * (xs > edge + 3)).astype(np.uint8)
        can.alpha_composite(Image.fromarray(la)); can.alpha_composite(Image.fromarray(ra))
        d = ImageDraw.Draw(can)
        d.line([(540 + H / 2 * 0.10, 0), (540 - H / 2 * 0.10, H)], fill=RED, width=5)
        return can
    if kind == 'mills_tight':
        can = bg(glow(540, 760, 560, (255, 255, 255), 0.14))
        can.alpha_composite(MILLS.layer(3.63 * z, 540, 820)); return can
    if kind == 'moneke_tight':
        can = bg(glow(540, 760, 560, (255, 25, 30), 0.26))
        can.alpha_composite(MONEKE.layer(3.95 * z, 540, 820)); return can
    if kind == 'mills_side':
        can = bg(glow(380, 760, 560, (255, 255, 255), 0.14))
        can.alpha_composite(MILLS.layer(3.22 * z, 360 + 30 * v, 800)); return can
    if kind == 'moneke_side':
        can = bg(glow(700, 760, 560, (255, 25, 30), 0.26))
        can.alpha_composite(MONEKE.layer(3.5 * z, 720 - 30 * v, 800)); return can
    raise ValueError(kind)

CUTS = [(18.00, 'split'), (19.19, 'black'),
        (20.00, 'mills_tight'), (20.41, 'moneke_tight'), (21.02, 'black'), (21.63, 'split2'),
        (22.00, 'moneke_side'), (22.24, 'mills_side'), (22.55, 'moneke_tight'), (22.85, 'mills_tight'),
        (23.16, 'black'), (23.46, 'split'), (23.77, 'black'), (24.0, None)]
PHRASES = [(18.0, ['DEUX ÉQUIPES.'], [WHITE]),
           (20.0, ['UNE VICTOIRE', 'À PRENDRE.'], [WHITE, RED]),
           (22.0, ['UNE NOUVELLE', 'BATAILLE.'], [WHITE, RED])]
LINE_TARGETS = [(18.0, 150), (20.0, 300), (22.0, 430), (23.62, 525)]

def phrase_block(can, lines, cols, k, alpha):
    size = min(fit(s, ANTON, 860, 230) for s in lines)
    lh = size * 1.02
    y0 = 1000 - (len(lines) - 1) * lh / 2 + size * 0.36
    for i, (s, c) in enumerate(zip(lines, cols)):
        put(can, text(s, ANTON, size, c + (255,)), CX, y0 + i * lh, scale=1.10 - 0.10 * k, alpha=alpha)

def scene5(t):
    for i in range(len(CUTS) - 1):
        if CUTS[i][0] <= t < CUTS[i + 1][0]:
            a, kind = CUTS[i]; b = CUTS[i + 1][0]; break
    can = shot(kind, (t - a) / (b - a))
    if kind != 'black': can = darken(can, 0.40)
    # lignes qui rapprochent les deux camps
    L = 80.0
    for t0, tgt in LINE_TARGETS:
        if t >= t0: L = lerp(L, tgt, e_expo(seg(t, t0, t0 + 0.32)))
    d = ImageDraw.Draw(can)
    d.rectangle([0, 1236, L, 1242], fill=WHITE)
    d.rectangle([W - L, 1236, W, 1242], fill=RED)
    d.rectangle([0, 712, L * 0.8, 714], fill=RED)
    d.rectangle([W - L * 0.8, 712, W, 714], fill=WHITE)
    for p0, lines, cols in reversed(PHRASES):
        if t >= p0:
            phrase_block(can, lines, cols, e_expo(seg(t, p0, p0 + 0.26)), c01(seg(t, p0, p0 + 0.07))); break
    return can.convert('RGB')

# ================================================================== SCENES 6 & 7 : face-a-face, revelation, affiche
T_DARK, T_REVEAL, T_INFO, T_END = 25.9, 26.5, 28.0, 34.45

def scene6a(t):
    u = t - 24.0
    lv = 1 - e_io(seg(t, 24.6, T_DARK))
    can = bg(glow(280, 780, 520, (255, 255, 255), 0.13), glow(800, 780, 520, (255, 25, 30), 0.24))
    k = e_io(u / 1.9)
    l = MILLS.layer(2.83, 250 + 45 * k, 820, fade_bottom=(1350, 1650))
    r = MONEKE.layer(3.08, 830 - 45 * k, 820, fade_bottom=(1350, 1650))
    xs = np.arange(W)[None, :]
    la = np.asarray(l).copy(); la[..., 3] = (la[..., 3] * np.clip((560 - xs) / 40, 0, 1)).astype(np.uint8)
    ra = np.asarray(r).copy(); ra[..., 3] = (ra[..., 3] * np.clip((xs - 520) / 40, 0, 1)).astype(np.uint8)
    can.alpha_composite(Image.fromarray(la)); can.alpha_composite(Image.fromarray(ra))
    d = ImageDraw.Draw(can)
    d.line([(540, 300), (540, 1500)], fill=(120, 18, 22), width=2)
    return darken(can, lv).convert('RGB')

def poster(t, date_line):
    ur = t - T_REVEAL
    can = bg(glow(285, 420, 520, (255, 255, 255), 0.15), glow(800, 420, 520, (255, 25, 30), 0.26))
    kp = e_expo(seg(ur, 0.0, 0.55))
    l = MILLS.layer(2.53, 285 - 620 * (1 - kp), 335, fade_bottom=(600, 790))
    r = MONEKE.layer(2.75, 805 + 620 * (1 - kp), 335, fade_bottom=(600, 790))
    can.alpha_composite(l); can.alpha_composite(r)
    # noms des equipes
    kn = e_expo(seg(ur, 0.0, 0.34)); an = c01(seg(ur, 0.0, 0.08))
    sc = 1.18 - 0.18 * kn
    def P(s, f, size, col, y, track=0):
        yy = 1000 + (y - 1000) * sc
        put(can, text(s, f, size, col + (255,), track), CX, yy, scale=sc, alpha=an)
    P('ASVEL', ANTON, 190, WHITE, 985)
    P('VS', ANTON, 60, RED, 1056, track=6)
    er = fit('ÉTOILE ROUGE', ANTON, 640, 112)
    P('ÉTOILE ROUGE', ANTON, er, WHITE, 1166)
    P('DE BELGRADE', ANTON, er, WHITE, 1264)
    # informations du match
    if t >= T_INFO:
        ui = t - T_INFO
        d = ImageDraw.Draw(can)
        hw = 210 * e_expo(seg(ui, 0.0, 0.3))
        d.rectangle([CX - hw, 1298, CX + hw, 1302], fill=RED)
        items = [(date_line, B8, 58, WHITE, 1372, 2), ('ASTROBALLE', B6, 50, (225, 225, 225), 1430, 6),
                 ('EUROLEAGUE', B8, 42, RED, 1480, 10), ('beIN SPORTS & EuroLeague TV', B6, 42, (225, 225, 225), 1528, 1)]
        for i, (s, f, size, col, y, tr) in enumerate(items):
            k = e_cub(seg(ui, 0.06 + i * 0.08, 0.30 + i * 0.08))
            put(can, text(s, f, size, col + (255,), track=tr), CX, y + 26 * (1 - k), alpha=k)
        k = e_cub(seg(ui, 0.45, 0.75))
        put(can, text('ASVEL_NEWS', B6, 30, (150, 150, 150, 255), track=4), CX, 1578, alpha=k)
    arr = np.asarray(can.convert('RGB')).astype(np.float32)
    fl = 0.32 * (1 - seg(ur, 0.0, 0.12))                           # flash d'impact, une seule fois
    arr = arr * (1 - fl) + 255 * fl
    arr *= 1 - e_io(seg(t, T_END, 34.97))                          # extinction courte
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGB')

# ================================================================== timeline
def frame(i, date_line):
    t = i / FPS
    if t < 6.0: return scene1(t)
    if t < 10.0: return scene2(t)
    if t < 14.0: return scene3(t)
    if t < 18.0: return scene4(t)
    if t < 24.0: return scene5(t)
    if t < T_DARK: return scene6a(t)
    if t < T_REVEAL: return Image.new('RGB', (W, H), (0, 0, 0))
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
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '12',
                          '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(N):
        p.stdin.write(frame(i, date_line).tobytes())
        if i % 60 == 0: print(i, flush=True)
    p.stdin.close(); p.wait()
