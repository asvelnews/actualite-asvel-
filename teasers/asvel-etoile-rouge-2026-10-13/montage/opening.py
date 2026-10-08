"""Opening: red seven-segment timer 00:05 -> 00:00 on black, then a classic shatter effect (Voronoi shards
flying out from the centre over 0.5 s) that reveals the score card. Pure 2D compositing, no AI.
Timeline (frames at 30 fps): 0-149 = 00:05..00:01 (1 s each), 150-164 = 00:00, 165-179 = shatter."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
RED = (255, 32, 28)
GHOST = (48, 6, 6)

# seven segments: a b c d e f g on a 100x180 digit cell
SEG = {
    'a': [(14, 0), (86, 0), (76, 12), (24, 12)],
    'b': [(88, 2), (100, 14), (100, 84), (90, 90), (80, 82), (80, 14)],
    'c': [(90, 90), (100, 96), (100, 166), (88, 178), (80, 166), (80, 98)],
    'd': [(24, 168), (76, 168), (86, 180), (14, 180)],
    'e': [(10, 90), (20, 98), (20, 166), (12, 178), (0, 166), (0, 96)],
    'f': [(12, 2), (20, 14), (20, 82), (10, 90), (0, 84), (0, 14)],
    'g': [(14, 90), (24, 82), (76, 82), (86, 90), (76, 98), (24, 98)],
}
DIG = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd',
       '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg'}

def _timer_image(text):
    s = 1.55                                      # digit cell 155 x 279 px
    cw, gap, colon = 100 * s, 26 * s, 46 * s
    total = 4 * cw + 2 * gap + 2 * (colon / 2) + colon
    x0 = (W - total) / 2; y0 = (H - 180 * s) / 2
    lit = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(lit)
    ghost = Image.new('RGB', (W, H), (0, 0, 0)); g = ImageDraw.Draw(ghost)
    x = x0
    for i, ch in enumerate(text):
        if ch == ':':
            cx = x + colon / 2
            for cy in (y0 + 55 * s, y0 + 125 * s):
                d.ellipse([cx - 9 * s, cy - 9 * s, cx + 9 * s, cy + 9 * s], fill=RED)
            x += colon + colon / 2
            continue
        for k, poly in SEG.items():
            pts = [(x + px * s, y0 + py * s) for px, py in poly]
            g.polygon(pts, fill=GHOST)
            if k in DIG[ch]:
                d.polygon(pts, fill=RED)
        x += cw + (gap if i in (0, 3) else colon / 2)
    glow = lit.filter(ImageFilter.GaussianBlur(28))
    out = np.maximum(np.asarray(ghost, np.float32), 0)
    out = out + np.asarray(glow, np.float32) * 1.3 + np.asarray(lit, np.float32)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))

_CACHE = {}
def timer_frame(f):
    n = 5 - min(f // 30, 5)                       # 5,4,3,2,1 then 0 from frame 150
    key = f'00:0{n}'
    if key not in _CACHE:
        _CACHE[key] = _timer_image(key)
    return _CACHE[key].copy().convert('RGBA')

# ---------------- shatter ----------------
_rng = np.random.default_rng(11)
_N = 70
_pts = np.concatenate([
    _rng.normal([W / 2, H / 2], [140, 160], (30, 2)),          # dense, small shards at the impact point
    _rng.uniform([0, 0], [W, H], (_N - 30, 2))])
_pts = np.clip(_pts, 1, [W - 2, H - 2])
_ys, _xs = np.mgrid[0:H // 4, 0:W // 4]
_lab_small = np.argmin(((_xs[..., None] * 4 - _pts[:, 0]) ** 2 + (_ys[..., None] * 4 - _pts[:, 1]) ** 2), axis=-1)
_LAB = np.kron(_lab_small, np.ones((4, 4), np.int32))[:H, :W]
_vel = []
for i, (px, py) in enumerate(_pts):
    v = np.array([px - W / 2, py - H / 2]); dist = np.linalg.norm(v) + 1
    v = v / dist * (900 + 1400 * _rng.random()) + _rng.normal(0, 150, 2)
    _vel.append((v, _rng.normal(0, 120), dist))         # px/s, deg/s, distance from impact
_EDGES = None

def _edges():
    global _EDGES
    if _EDGES is None:
        e = (np.diff(_LAB, axis=0, prepend=_LAB[:1]) != 0) | (np.diff(_LAB, axis=1, prepend=_LAB[:, :1]) != 0)
        _EDGES = Image.fromarray((e * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
    return _EDGES

def shatter(k, under, glass):
    """k = 0..14 (frame within the 0.5-s shatter), under = score card (RGBA), glass = 00:00 timer image (RGBA)."""
    t = k / 30.0
    out = under.copy()
    g = np.asarray(glass)
    for i in range(_N):
        v, spin, dist = _vel[i]
        delay = dist / 4000.0                              # the break propagates from the centre outwards
        tt = max(0.0, t - delay)
        alpha = max(0.0, 1.0 - tt / 0.42)
        if alpha <= 0: continue
        ys, xs = np.nonzero(_LAB[::1, ::1] == i) if False else (None, None)
        m = (_LAB == i)
        rows = np.flatnonzero(m.any(1)); cols = np.flatnonzero(m.any(0))
        if rows.size == 0: continue
        y0, y1, x0, x1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        piece = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        piece[..., :3] = g[y0:y1, x0:x1, :3]
        piece[..., 3] = (m[y0:y1, x0:x1] * 255 * alpha).astype(np.uint8)
        im = Image.fromarray(piece, 'RGBA')
        # thin bright rim on each shard (glass edge catching the light)
        rim = Image.fromarray(m[y0:y1, x0:x1].astype(np.uint8) * 255).filter(ImageFilter.FIND_EDGES)
        rim_l = Image.new('RGBA', im.size, (235, 240, 255, 0)); rim_l.putalpha(rim.point(lambda p: int(min(255, p) * 0.7 * alpha)))
        im.alpha_composite(rim_l)
        scale = 1.0 + 0.5 * tt
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
        im = im.rotate(spin * tt, resample=Image.BILINEAR, expand=True)
        cx = (x0 + x1) / 2 + v[0] * tt; cy = (y0 + y1) / 2 + v[1] * tt + 600 * tt * tt
        out.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2))) if (
            -im.width < cx < W + im.width and -im.height < cy < H + im.height and
            int(cx - im.width / 2) >= 0 and int(cy - im.height / 2) >= 0 and
            int(cx - im.width / 2) + im.width <= W and int(cy - im.height / 2) + im.height <= H) else _paste_clipped(out, im, cx, cy)
    if k < 3:                                              # white crack flash on impact
        fl = Image.new('RGBA', (W, H), (255, 255, 255, 0))
        fl.putalpha(_edges().point(lambda p: int(p * (0.9 - 0.3 * k))))
        out.alpha_composite(fl)
    return out

def _paste_clipped(out, im, cx, cy):
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(im.width, W - x), min(im.height, H - y)
    if ex <= sx or ey <= sy: return
    out.alpha_composite(im.crop((sx, sy, ex, ey)), (x + sx, y + sy))
