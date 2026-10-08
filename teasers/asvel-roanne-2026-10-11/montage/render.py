"""Compose the ASVEL - Roanne TikTok teaser: picture track from prepared segments + typography.
usage: render.py out.mp4 audio.wav [--frames a,b,c --still-dir dir]"""
import numpy as np, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
TOTAL = 53 * FPS
HERE = os.path.dirname(os.path.abspath(__file__))
F = lambda n, s: ImageFont.truetype(os.path.join(HERE, 'fonts', n), s)
ANTON = 'Anton-Regular.ttf'; BARLOW_B = 'BarlowCondensed-Bold.ttf'; BARLOW_SB = 'BarlowCondensed-SemiBold.ttf'
WHITE = (255, 255, 255); GREY = (150, 150, 150); LGREY = (190, 190, 190)
X0 = 92  # left margin: everything left-aligned, far from TikTok's right rail

# ---------- picture segments: (first frame, n frames, file) ----------
# v5: countdown + 11 actions (4 original clips, Pons, 2 actions from each of the 3 new clips); clip audio never used.
# Order: shots -> rim finishes -> most spectacular (dunk of the 2nd new video last). Every cut on the 0.5-s beat grid.
OFF = 150
SEGS = [(0, 150, 'seg2/cd'),     #  0.0  countdown 5 -> 1
        (300, 64, 'seg2/s1'),    # 10.0  Find the shooter: Mills sets up (0.8x)
        (364, 41, 'seg2/s2'),    #       swish 13.0 (music drop)
        (405, 75, 'seg3/n2a'),   # 13.5  new video 2, action A: #25 three, ball in 15.75
        (480, 75, 'seg2/a'),     # 16.0  Tremont MVP: drive + pull-up, ball in 18.05
        (555, 105, 'seg3/n3a'),  # 18.5  new video 3, action A: jump shot, ball in 21.3
        (660, 75, 'seg2/c1'),    # 22.0  Mills -> Crowder corner three
        (735, 30, 'seg2/c2'),    #       ball in 25.05
        (765, 120, 'seg3/n3b'),  # 25.5  new video 3, action B: Mills pull-up, ball in 28.7
        (885, 75, 'seg3/n1b'),   # 29.5  new video 1, action B: fast-break lay-up, ball in 30.95
        (960, 90, 'seg3/n1a'),   # 32.0  new video 1, action A: drive + finish, ball in 34.5
        (1050, 45, 'seg2/b'),    # 35.0  Yves Pons dunk 36.05
        (1095, 30, 'seg2/d1'),   # 36.5  Touchdown: long pass
        (1125, 90, 'seg2/d2'),   #       Sestina finish 39.0 + celebration
        (1215, 105, 'seg3/n2b'), # 40.5  new video 2, action B: #25 DUNK 41.8 + landing + reaction
        (1320, 90, 'seg2/m')]    # 44.0  Crowder roar under CETTE FOIS, CHEZ NOUS.   poster 47.0-53.0

def read_seg(name, n):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, name + '.mp4'),
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    if len(fr) < n:  # pad by holding last frame (never needed by more than 1 frame)
        fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    return fr[:n]

# ---------- logos recomposed from image 1 ----------
ref = Image.open(os.path.join(HERE, '..', 'images', '1.png')).convert('RGB')
def tile(box, size):
    t = ref.crop(box).resize((size, size), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.16), fill=255)
    out = Image.new('RGBA', (size, size)); out.paste(t, (0, 0), mask); return out
ROANNE_BOX = (93, 10, 175, 92); ASVEL_BOX = (517, 10, 599, 92)

# ---------- text helpers ----------
def text_w(font, s, track=0):
    return sum(font.getlength(c) for c in s) + track * (len(s) - 1)

def draw_text(img, xy, s, font, fill, track=0, alpha=1.0):
    if alpha <= 0: return
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    if track == 0:
        d.text((x, y), s, font=font, fill=fill + (255,))
    else:
        for c in s:
            d.text((x, y), c, font=font, fill=fill + (255,)); x += font.getlength(c) + track
    if alpha < 1:
        a = layer.getchannel('A').point(lambda v: int(v * alpha)); layer.putalpha(a)
    img.alpha_composite(layer)

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def appear(f, f0, dur=4):  # quick, sober fade-in
    return ease((f - f0) / dur)

def fit(font_name, s, max_w, start):
    size = start
    while text_w(F(font_name, size), s) > max_w: size -= 2
    return F(font_name, size)

def card_canvas(): return Image.new('RGBA', (W, H), (0, 0, 0, 255))

# ---------- cards ----------
def hook(f):
    img = card_canvas(); a = 1.0  # score on screen from the very first frame after the "1"
    # rows: [tile] ROANNE / 73 — 71 / [tile] ASVEL / date line
    big = F(ANTON, 168); score = F(ANTON, 300); sub = F(BARLOW_B, 58)
    ts = 150
    y = 520
    img.alpha_composite(fade_rgba(tile(ROANNE_BOX, ts), a), (X0, y + 14))
    draw_text(img, (X0 + ts + 34, y - 18), 'ROANNE', big, WHITE, alpha=a)
    y += 205
    draw_text(img, (X0 - 8, y - 40), '73 — 71', score, WHITE, alpha=a)
    y += 375
    img.alpha_composite(fade_rgba(tile(ASVEL_BOX, ts), a), (X0, y + 14))
    draw_text(img, (X0 + ts + 34, y - 18), 'ASVEL', big, WHITE, alpha=a)
    y += 235
    draw_text(img, (X0 + 2, y), '19 SEPTEMBRE · SUPERCOUPE', sub, GREY, track=3, alpha=appear(f, 6, 5))
    return img

def fade_rgba(im, a):
    if a >= 1: return im
    im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a))); return im

def rappel(f):
    img = card_canvas(); big = F(ANTON, 190); sub = F(BARLOW_B, 60)
    if f < 98:            # 2.50-3.25  DEUX DUELS.
        draw_text(img, (X0, 780), 'DEUX DUELS.', big, WHITE, alpha=appear(f, 75, 3))
    elif f < 120:         # 3.25-4.00  DEUX DÉFAITES.
        draw_text(img, (X0, 740), 'DEUX', big, WHITE, alpha=appear(f, 98, 3))
        draw_text(img, (X0, 960), 'DÉFAITES.', big, WHITE, alpha=appear(f, 98, 3))
        draw_text(img, (X0 + 4, 1235), '92–76  ·  73–71', sub, GREY, track=3, alpha=appear(f, 101, 4))
    else:                 # 4.00-5.00  ON N'A PAS OUBLIÉ.
        draw_text(img, (X0, 740), 'ON N’A PAS', big, WHITE, alpha=appear(f, 120, 3))
        draw_text(img, (X0, 960), 'OUBLIÉ.', big, WHITE, alpha=appear(f, 120, 3))
    return img

def gradient_top(img, h=760, strength=0.82):
    g = np.zeros((H, W), np.uint8)
    ramp = (np.clip(1 - np.arange(h) / h, 0, 1) ** 1.3 * 255 * strength).astype(np.uint8)
    g[:h] = ramp[:, None]
    black = Image.new('RGBA', (W, H), (0, 0, 0, 0)); black.putalpha(Image.fromarray(g))
    img.alpha_composite(black)

def message(img, f):
    gradient_top(img)
    big = F(ANTON, 176)
    draw_text(img, (X0, 250), 'CETTE FOIS,', big, WHITE, alpha=appear(f, 1178, 4))   # 44.27
    draw_text(img, (X0, 470), 'CHEZ NOUS.', big, WHITE, alpha=appear(f, 1200, 4))    # 45.00

_POSTER = None
def rdv(f):
    # end card 28.0-34.0 s = the players poster (poster.py), on screen in full from its first frame
    global _POSTER
    if _POSTER is None:
        _POSTER = Image.open(os.path.join(HERE, 'poster.png')).convert('RGBA')
    return _POSTER.copy()

def pygame_rule(img, y, a):
    d = ImageDraw.Draw(img)
    d.rectangle([X0 + 2, y, X0 + 122, y + 7], fill=(int(255 * a),) * 3 + (255,))

# ---------- main ----------
def frame_image(f, base):
    if f < OFF: return Image.fromarray(base).convert('RGBA')      # countdown: real footage, untouched
    r = f - OFF
    if r < 75: return hook(r)
    if r < 150: return rappel(r)
    if r >= 1260: return rdv(r)
    img = Image.fromarray(base).convert('RGBA')
    if r >= 1170: message(img, r)
    return img

def main():
    out, audio = sys.argv[1], sys.argv[2]
    stills = None
    if '--frames' in sys.argv:
        stills = [int(x) for x in sys.argv[sys.argv.index('--frames') + 1].split(',')]
    base = {}
    for f0, n, name in SEGS:
        if stills and not any(f0 <= s < f0 + n for s in stills): continue
        fr = read_seg(name, n)
        for i in range(n): base[f0 + i] = fr[i]
    if stills:
        os.makedirs(out, exist_ok=True)
        for s in stills:
            frame_image(s, base.get(s)).convert('RGB').save(os.path.join(out, f'f{s:03d}.png'))
        return
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', str(FPS), '-i', '-', '-i', audio,
                            '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
                            '-profile:v', 'high', '-level', '4.1', '-pix_fmt', 'yuv420p',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
                            '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', '53', '-movflags', '+faststart', out],
                           stdin=subprocess.PIPE)
    for f in range(TOTAL):
        enc.stdin.write(np.asarray(frame_image(f, base.get(f)).convert('RGB')).tobytes())
    enc.stdin.close(); enc.wait()
    print('done', out)

if __name__ == '__main__':
    main()
