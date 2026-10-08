"""Compose the ASVEL - Roanne TikTok teaser: picture track from prepared segments + typography.
usage: render.py out.mp4 audio.wav [--frames a,b,c --still-dir dir]"""
import numpy as np, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
TOTAL = 34 * FPS
HERE = os.path.dirname(os.path.abspath(__file__))
F = lambda n, s: ImageFont.truetype(os.path.join(HERE, 'fonts', n), s)
ANTON = 'Anton-Regular.ttf'; BARLOW_B = 'BarlowCondensed-Bold.ttf'; BARLOW_SB = 'BarlowCondensed-SemiBold.ttf'
WHITE = (255, 255, 255); GREY = (150, 150, 150); LGREY = (190, 190, 190)
X0 = 92  # left margin: everything left-aligned, far from TikTok's right rail

# ---------- picture segments: (first frame, n frames, file) ----------
# v3: 5-s retro countdown (5 -> 1) first, then the v2 edit shifted by 5 s; clip audio is never used.
OFF = 150  # countdown frames; cards below are written in frames relative to the end of the countdown
SEGS = [(0, 150, 'cd'),    # countdown 5-4-3-2-1 (source 5.04-10.04 s), centred 9:16 crop, no "0"
        (300, 64, 's1'),   # Find the shooter: Mills sets up (0.8x)
        (364, 41, 's2'),   #   ball flight, swish at 13.0 s, held to 13.5
        (405, 75, 'a'),    # Tremont Waters: drive, pull-up, ball in at 15.55 s, cut 16.0
        (480, 75, 'c1'),   # Mills -> Crowder: pass, corner three
        (555, 30, 'c2'),   #   ball drops in at 19.05 s, cut 19.5
        (585, 45, 'b'),    # Yves Pons: drive + dunk at 20.55 s, cut 21.0
        (630, 30, 'd1'),   # Touchdown: full-court pass, catch
        (660, 90, 'd2'),   #   Sestina finish (ball in 23.5 s) + celebration, one continuous take
        (750, 90, 'm')]    # Crowder roar under the message (25-28 s)

def read_seg(name, n):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'seg2', name + '.mp4'),
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
    draw_text(img, (X0, 250), 'CETTE FOIS,', big, WHITE, alpha=appear(f, 608, 4))   # 20.27
    draw_text(img, (X0, 470), 'CHEZ NOUS.', big, WHITE, alpha=appear(f, 630, 4))    # 21.00

def rdv(f):
    # end card 28.0-34.0 s: large type, clear hierarchy, all inside TikTok's safe area (x 92-912, y < 1460)
    img = card_canvas()
    a0 = appear(f, 690, 4); a1 = appear(f, 696, 4); a2 = appear(f, 702, 4); a3 = appear(f, 708, 4); a4 = appear(f, 714, 4)
    ts = 150
    y = 255
    img.alpha_composite(fade_rgba(tile(ASVEL_BOX, ts), a0), (X0, y))
    img.alpha_composite(fade_rgba(tile(ROANNE_BOX, ts), a0), (X0 + ts + 28, y))
    y += ts + 30
    draw_text(img, (X0 - 4, y), 'ASVEL – ROANNE', fit(ANTON, 'ASVEL – ROANNE', 860, 200), WHITE, alpha=a0)
    y += 255
    pygame_rule(img, y, a1)
    y += 38
    draw_text(img, (X0, y), 'DIMANCHE 11 OCTOBRE', fit(ANTON, 'DIMANCHE 11 OCTOBRE', 820, 140), WHITE, alpha=a1)
    y += 165
    draw_text(img, (X0, y), '19H · ASTROBALLE', fit(ANTON, '19H · ASTROBALLE', 820, 140), WHITE, alpha=a2)
    y += 205
    draw_text(img, (X0 + 2, y), 'EN DIRECT SUR', F(BARLOW_B, 62), LGREY, track=5, alpha=a3)
    y += 78
    draw_text(img, (X0, y), 'LA CHAÎNE L’ÉQUIPE ET DAZN', fit(ANTON, 'LA CHAÎNE L’ÉQUIPE ET DAZN', 820, 100), WHITE, alpha=a3)
    y += 150
    draw_text(img, (X0 + 2, y), 'ASVEL_NEWS', F(BARLOW_B, 64), LGREY, track=6, alpha=a4)   # all in by 28.6 s
    return img

def pygame_rule(img, y, a):
    d = ImageDraw.Draw(img)
    d.rectangle([X0 + 2, y, X0 + 122, y + 7], fill=(int(255 * a),) * 3 + (255,))

# ---------- main ----------
def frame_image(f, base):
    if f < OFF: return Image.fromarray(base).convert('RGBA')      # countdown: real footage, untouched
    r = f - OFF
    if r < 75: return hook(r)
    if r < 150: return rappel(r)
    if r >= 690: return rdv(r)
    img = Image.fromarray(base).convert('RGBA')
    if r >= 600: message(img, r)
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
                            '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', '34', '-movflags', '+faststart', out],
                           stdin=subprocess.PIPE)
    for f in range(TOTAL):
        enc.stdin.write(np.asarray(frame_image(f, base.get(f)).convert('RGB')).tobytes())
    enc.stdin.close(); enc.wait()
    print('done', out)

if __name__ == '__main__':
    main()
