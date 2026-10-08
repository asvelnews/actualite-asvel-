"""ASVEL - Etoile Rouge de Belgrade: vertical trailer (1080x1920, 30 fps).
Only supplied media: frames of ASVEL_actions.mp4 / Belgrade_actions.mp4 and the two player photos.
Everything else (timer digits, glass shatter, typography) is classic 2D compositing. No AI.
usage: trailer.py out.mp4 audio.wav  |  trailer.py --stills dir f1,f2,..."""
import os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # scratchpad (fonts, opening.py)
IMG = os.path.join(os.path.dirname(ROOT), 'images')
sys.path.insert(0, ROOT)
import opening                                     # Voronoi glass shatter (shared with the Roanne teaser)

W, H, FPS = 1080, 1920, 30
F = lambda n, s: ImageFont.truetype(os.path.join(ROOT, 'fonts', n), s)
ANTON, BB = 'Anton-Regular.ttf', 'BarlowCondensed-Bold.ttf'
WHITE, GREY, LGREY, RED = (255, 255, 255), (140, 140, 140), (200, 200, 200), (228, 30, 42)
X0 = 92

# ------------------------------------------------------------------ timeline
# (name, seconds, kind, extra)
# v2: short intro (open 6 s + history 4 s), actions from 10.0 s, teams alternate, no mid portraits.
TL = [('open', 5.6, 'open', None),
      ('hist', 4.4, 'hist', None),
      ('a1', 116 / 30, 'clip', None),   # ASVEL   tir apres dribble
      ('b3', 125 / 30, 'clip', None),   # BELGRADE tir de Jared
      ('a3', 111 / 30, 'clip', None),   # ASVEL   tir de Patty Mills
      ('b4', 84 / 30, 'clip', None),    # BELGRADE finition de Moneke
      ('a4', 69 / 30, 'clip', None),    # ASVEL   tir a 3 pts (Rookie)
      ('b2', 108 / 30, 'clip', None),   # BELGRADE step-back de Jared
      ('a7', 48 / 30, 'clip', None),    # ASVEL   contre
      ('b5', 112 / 30, 'clip', None),   # BELGRADE tir de Moneke (attaque apres le contre)
      ('a2', 110 / 30, 'clip', None),   # ASVEL   finition au cercle
      ('b1', 105 / 30, 'clip', None),   # BELGRADE dunk d'Izundu (ralenti court)
      ('a5', 61 / 30, 'clip', None),    # ASVEL   tir final (coupure musicale avant)
      ('a6', 38 / 30, 'clip', None),    # ASVEL   reaction
      ('breath', 0.4, 'black', None),
      ('poster', 7.0, 'poster', None)]
START = {}
_t = 0
for name, d, kind, extra in TL:
    n = int(round(d * FPS)); START[name] = (_t, n, kind, extra); _t += n
TOTAL = _t

# ------------------------------------------------------------------ helpers
def tw(font, s, track=0): return sum(font.getlength(c) for c in s) + track * (len(s) - 1)
def fit(name, s, max_w, start):
    size = start
    while tw(F(name, size), s) > max_w: size -= 2
    return F(name, size)
def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def text(img, xy, s, font, fill, track=0, alpha=1.0, anchor_center=False):
    if alpha <= 0: return
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    x, y = xy
    if anchor_center: x = x - tw(font, s, track) / 2
    for c in s:
        d.text((x, y), c, font=font, fill=fill + (int(255 * alpha),)); x += font.getlength(c) + track
    img.alpha_composite(layer)
def black(): return Image.new('RGBA', (W, H), (0, 0, 0, 255))

# ------------------------------------------------------------------ 1. opening: real basket + shot clock
_SRC = None
def _open_src():
    global _SRC
    if _SRC is None:
        im = Image.open(os.path.join(HERE, 'open_src.png')).convert('RGB')    # ASVEL_actions.mp4 @ 22.45 s
        d = ImageDraw.Draw(im)
        d.rectangle([606, 664, 722, 852], fill=(9, 10, 12))                  # switch the clock's own digits off
        _SRC = im
    return _SRC

SEG7 = {'a': [(14, 0), (86, 0), (76, 12), (24, 12)], 'b': [(88, 2), (100, 14), (100, 84), (90, 90), (80, 82), (80, 14)],
        'c': [(90, 90), (100, 96), (100, 166), (88, 178), (80, 166), (80, 98)], 'd': [(24, 168), (76, 168), (86, 180), (14, 180)],
        'e': [(10, 90), (20, 98), (20, 166), (12, 178), (0, 166), (0, 96)], 'f': [(12, 2), (20, 14), (20, 82), (10, 90), (0, 84), (0, 14)],
        'g': [(14, 90), (24, 82), (76, 82), (86, 90), (76, 98), (24, 98)]}
DIG = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd'}

def _clock_digit(src, ch):
    """Red LED digit drawn inside the real shot-clock housing (source px)."""
    s = 0.86; x0, y0 = 621, 678                                            # 86 x 155 px digit
    lit = Image.new('L', src.size, 0); dl = ImageDraw.Draw(lit)
    ghost = Image.new('L', src.size, 0); dg = ImageDraw.Draw(ghost)
    for k, poly in SEG7.items():
        pts = [(x0 + px * s, y0 + py * s) for px, py in poly]
        dg.polygon(pts, fill=40)
        if k in DIG[ch]: dl.polygon(pts, fill=255)
    out = np.asarray(src, np.float32).copy()
    glow = np.asarray(lit.filter(ImageFilter.GaussianBlur(9)), np.float32)[..., None] / 255
    core = np.asarray(lit, np.float32)[..., None] / 255
    g = np.asarray(ghost, np.float32)[..., None] / 255
    red = np.array([255, 28, 22], np.float32)
    out = out * (1 - g * 0.5) + np.array([60, 5, 5]) * g * 0.5
    out = out + red * glow * 0.9
    out = out * (1 - core) + red * core
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))

def _cam(im, t):
    """slow push towards backboard and clock, framing kept inside the source's sharp band (no blur)."""
    e = 0.5 - 0.5 * np.cos(np.pi * min(t / 5.0, 1.0))
    z = 1.45 + 0.15 * e
    cx = 630; cy = 960 + 40 * e
    w, h = W / z, H / z
    return im.resize((W, H), Image.LANCZOS, box=(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))

def _to_out(x, y):           # source px -> output px at the end of the push (z 1.6, centre 630,1000)
    return ((x - (630 - W / 3.2)) * 1.6, (y - (1000 - H / 3.2)) * 1.6)
BOARD = (*_to_out(313, 998), *_to_out(950, 1376))     # backboard glass in output px
IMPACT = _to_out(632, 1170)
_rng = np.random.default_rng(5)
_seeds = np.concatenate([_rng.normal(IMPACT, [70, 55], (18, 2)),
                         _rng.uniform(BOARD[:2], BOARD[2:], (30, 2))])
_seeds = np.clip(_seeds, np.array(BOARD[:2]) + 2, np.array(BOARD[2:]) - 2)
_bx0, _by0, _bx1, _by1 = [int(round(v)) for v in BOARD]
_yy, _xx = np.mgrid[_by0:_by1, _bx0:_bx1]
_LAB = np.argmin((_xx[..., None] - _seeds[:, 0]) ** 2 + (_yy[..., None] - _seeds[:, 1]) ** 2, axis=-1)
_EDGE = ((np.diff(_LAB, axis=0, prepend=_LAB[:1]) != 0) | (np.diff(_LAB, axis=1, prepend=_LAB[:, :1]) != 0))
_EDGE = np.array(Image.fromarray(_EDGE.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(3))) > 0
_RAD = np.hypot(_xx - IMPACT[0], _yy - IMPACT[1])

def crack_layer(k):
    """cracks spreading from the impact point inside the glass only (k 0..1)."""
    rad = 40 + 700 * ease(k)
    m = _EDGE & (_RAD < rad)
    a = np.zeros((H, W), np.uint8); a[_by0:_by1, _bx0:_bx1] = (m * 235).astype(np.uint8)
    lay = Image.new('RGBA', (W, H), (235, 242, 255, 0)); lay.putalpha(Image.fromarray(a))
    return lay

def shatter_board(k, cracked):
    """k = 0.. frames since the glass gives way: shards of the backboard fall and spin out of frame."""
    t = k / 30
    out = cracked.copy()
    # the glass is gone: the panel area shows the (darkened) arena behind it
    hole = cracked.crop((_bx0, _by0, _bx1, _by1)).point(lambda v: int(v * 0.55))
    out.paste(hole, (_bx0, _by0))
    src = np.asarray(cracked)
    for i, (sx, sy) in enumerate(_seeds):
        m = _LAB == i
        rows = np.flatnonzero(m.any(1)); cols = np.flatnonzero(m.any(0))
        if rows.size == 0: continue
        y0, y1, x0, x1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        piece = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        piece[..., :3] = src[_by0 + y0:_by0 + y1, _bx0 + x0:_bx0 + x1, :3]
        piece[..., 3] = m[y0:y1, x0:x1] * 255
        im = Image.fromarray(piece, 'RGBA')
        rim = Image.fromarray(m[y0:y1, x0:x1].astype(np.uint8) * 255).filter(ImageFilter.FIND_EDGES)
        rl = Image.new('RGBA', im.size, (240, 245, 255, 0)); rl.putalpha(rim.point(lambda p: min(255, p) * 0.8))
        im.alpha_composite(rl)
        d = np.array([sx - IMPACT[0], sy - IMPACT[1]]); n = np.linalg.norm(d) + 1
        v = d / n * (250 + 500 * _rng.random()) if k == 0 else d / n * (350 + 2 * (i % 7) * 60)
        spin = ((i * 37) % 120) - 60
        im = im.rotate(spin * t * 3, resample=Image.BILINEAR, expand=True)
        cx = _bx0 + (x0 + x1) / 2 + v[0] * t; cy = _by0 + (y0 + y1) / 2 + v[1] * t + 2600 * t * t
        px, py = int(cx - im.width / 2), int(cy - im.height / 2)
        if px >= W or py >= H or px + im.width <= 0 or py + im.height <= 0: continue
        sx0, sy0 = max(0, -px), max(0, -py)
        out.alpha_composite(im.crop((sx0, sy0, min(im.width, W - px), min(im.height, H - py))), (max(px, 0), max(py, 0)))
    return out

_OPEN_CACHE = {}
def opening_frame(f):
    """0-5 s: 5,4,3,2,1 on the real shot clock ; 5.0 s: 0 + buzzer, the backboard glass cracks from the
    impact point (5.0-5.43 s) ; 5.43-5.6 s: brief light impact from the same point, then a hard cut."""
    n = 5 - min(f // 30, 5)
    key = str(n)
    if key not in _OPEN_CACHE: _OPEN_CACHE[key] = _clock_digit(_open_src(), key)
    fr = _cam(_OPEN_CACHE[key], min(f, 150) / 30).convert('RGBA')
    if f < 150: return fr
    fr.alpha_composite(crack_layer(min(1.0, (f - 150 + 1) / 11)))
    if f >= 163:                                                           # light impact from the glass
        k = (f - 162) / 5
        yy, xx = np.mgrid[0:H:4, 0:W:4]
        r = np.hypot(xx - IMPACT[0], yy - IMPACT[1])
        a = np.clip(k ** 1.2 * np.exp(-(r / (120 + 520 * k)) ** 2) * 1.3 + 0.4 * k ** 4, 0, 1)
        glow = Image.fromarray((a * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
        lay = Image.new('RGBA', (W, H), (255, 250, 240, 0)); lay.putalpha(glow); fr.alpha_composite(lay)
    return fr

# ------------------------------------------------------------------ 2. history
def hist_frame(r):
    """4 s: one composition. Labels at 0, '5' at 0.35 s, '9' at 0.9 s, both held; then UNE NOUVELLE BATAILLE."""
    img = black(); s = r / FPS
    if s < 3.05:
        text(img, (X0 + 2, 470), 'FACE-À-FACE', F(ANTON, 96), WHITE, alpha=ease(s / 0.12))
        text(img, (X0 + 4, 590), 'BILAN DES CONFRONTATIONS', F(BB, 44), GREY, track=4, alpha=ease(s / 0.12))
        colw = 410
        for i, (team, num, col, t0) in enumerate((('ASVEL', '5', WHITE, 0.35), ('ÉTOILE ROUGE', '9', RED, 0.9))):
            x = X0 + i * (colw + 20)
            text(img, (x, 700), team, fit(ANTON, team, colw - 10, 100), WHITE, alpha=ease(s / 0.12))
            if s >= t0:
                text(img, (x - 6, 830), num, F(ANTON, 380), col)
                text(img, (x + 2, 1290), 'VICTOIRES', F(BB, 58), LGREY, track=5)
        d = ImageDraw.Draw(img); d.rectangle([X0 + colw - 2, 720, X0 + colw + 2, 1340], fill=(70, 70, 70))
    else:
        a = ease((s - 3.05) / 0.12)
        f = fit(ANTON, 'UNE NOUVELLE', 860, 170)
        text(img, (X0, 760), 'UNE NOUVELLE', f, WHITE, alpha=a)
        text(img, (X0, 960), 'BATAILLE.', f, WHITE, alpha=a)
    return img

# ------------------------------------------------------------------ 3. photo cards & poster
def load_player(which):
    if which == 'mills':
        im = Image.open(os.path.join(IMG, '5.png')).convert('RGBA'); eye, em = (411, 121), 34
    else:
        im = Image.open(os.path.join(IMG, '4.webp')).convert('RGBA'); eye, em = (170, 79), 33
    return im, eye, em

def place(canvas, im, eye, em, eye_dst, em_dst):
    s = em_dst / em
    im2 = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 50, 2))
    ox, oy = round(eye_dst[0] - eye[0] * s), round(eye_dst[1] - eye[1] * s)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sx, sy = max(0, -ox), max(0, -oy)
    lay.alpha_composite(im2.crop((sx, sy, min(im2.width, W - ox), min(im2.height, H - oy))), (max(ox, 0), max(oy, 0)))
    canvas.alpha_composite(lay)

def fade_bottom(img, y0, y1):
    g = np.zeros((H, W), np.float32); g[:] = np.clip((np.arange(H) - y0) / (y1 - y0), 0, 1)[:, None] ** 1.3
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(Image.fromarray((g * 255).astype(np.uint8))); img.alpha_composite(sh)

def photo_card(which, r, n):
    t = r / max(n - 1, 1)
    img = Image.new('RGBA', (W, H), (10, 10, 12, 255))
    if which == 'moneke':                                                  # faint red glow behind the Belgrade player
        g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([140, 300, 940, 1100], fill=(120, 10, 16, 120))
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(160)))
    im, eye, em = load_player(which)
    z = 1.0 + 0.04 * t                                                     # very slow push
    place(img, im, eye, em, (540, 560 - 10 * t), 74 * z)
    fade_bottom(img, 1080, 1260)
    name = 'PATTY MILLS' if which == 'mills' else 'CHIMA MONEKE'
    team = 'ASVEL' if which == 'mills' else 'ÉTOILE ROUGE'
    a = ease(r / 6)
    text(img, (X0, 1250), name, fit(ANTON, name, 860, 170), WHITE, alpha=a)
    text(img, (X0 + 4, 1450), team, F(BB, 58), RED if which == 'moneke' else LGREY, track=6, alpha=a)
    return img

_POSTER = None
def poster():
    global _POSTER
    if _POSTER is not None: return _POSTER.copy()
    img = Image.new('RGBA', (W, H), (8, 8, 10, 255))
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.polygon([(600, 0), (W, 0), (W, H), (480, H)], fill=(95, 8, 14, 150))   # subtle red side for Belgrade
    img.alpha_composite(g.filter(ImageFilter.GaussianBlur(90)))
    EYE_Y, EM = 300, 80                                                     # bigger players, eyes aligned
    m, me, mem = load_player('moneke'); place(img, m, me, mem, (800, EYE_Y), EM)
    p, pe, pem = load_player('mills'); place(img, p, pe, pem, (285, EYE_Y), EM)
    fade_bottom(img, 820, 990)
    text(img, (X0, 860), 'ASVEL', F(ANTON, 190), WHITE)
    text(img, (X0 + 4, 1082), 'VS', F(ANTON, 70), GREY)
    t = fit(ANTON, 'ÉTOILE ROUGE DE BELGRADE', 816, 120)
    text(img, (X0, 1158), 'ÉTOILE ROUGE DE BELGRADE', t, RED)
    d = ImageDraw.Draw(img); d.rectangle([X0, 1306, X0 + 130, 1313], fill=WHITE)
    l = fit(ANTON, 'MARDI 13 OCTOBRE • 20H00', 816, 96)
    text(img, (X0, 1328), 'MARDI 13 OCTOBRE • 20H00', l, WHITE)
    text(img, (X0, 1430), 'ASTROBALLE', F(ANTON, l.size), WHITE)
    b = fit(BB, 'beIN SPORTS & EuroLeague TV', 816, 60)
    text(img, (X0 + 2, 1548), 'beIN SPORTS & EuroLeague TV', b, LGREY, track=1)
    text(img, (X0 + 2, 1622), 'ASVEL_NEWS', F(BB, 42), GREY, track=6)
    _POSTER = img
    return img.copy()

# ------------------------------------------------------------------ clips
def read_seg(name):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'seg2', name + '.mp4'), '-f', 'rawvideo',
                          '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)

def name_tag(img, label, col, r):
    if r > 45: return
    a = ease(r / 5) * (1 - ease((r - 38) / 7)) if r > 38 else ease(r / 5)
    text(img, (X0 + 2, 1400), label, F(ANTON, 64), WHITE, alpha=a)
    d = ImageDraw.Draw(img); d.rectangle([X0 + 2, 1482, X0 + 82, 1487], fill=col + (int(255 * a),))

# ------------------------------------------------------------------ main
def frame(f, cache):
    for name, (f0, n, kind, extra) in START.items():
        if f0 <= f < f0 + n:
            r = f - f0
            if kind == 'open': return opening_frame(r)
            if kind == 'hist': return hist_frame(r)
            if kind == 'photo': return photo_card(extra, r, n)
            if kind == 'black': return black()
            if kind == 'poster':
                img = poster()
                if r >= n - 8:                                             # short extinction
                    img.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (r - (n - 8) + 1) / 8))))
                return img
            if name not in cache: cache.clear(); cache[name] = read_seg(name)
            fr = cache[name]; img = Image.fromarray(fr[min(r, len(fr) - 1)]).convert('RGBA')
            return img
    return black()

def main():
    cache = {}
    if sys.argv[1] == '--stills':
        os.makedirs(sys.argv[2], exist_ok=True)
        for f in map(int, sys.argv[3].split(',')):
            frame(f, cache).convert('RGB').save(os.path.join(sys.argv[2], f'f{f:04d}.png'))
        return
    out, audio = sys.argv[1], sys.argv[2]
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                            '-i', '-', '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16',
                            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL / FPS:.3f}', out], stdin=subprocess.PIPE)
    for f in range(TOTAL):
        enc.stdin.write(np.asarray(frame(f, cache).convert('RGB')).tobytes())
    enc.stdin.close(); enc.wait(); print('done', TOTAL / FPS)

if __name__ == '__main__':
    main()
