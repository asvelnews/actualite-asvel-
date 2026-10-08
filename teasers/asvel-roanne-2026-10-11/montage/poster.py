"""End-card poster for the ASVEL - Roanne teaser (1080x1920), also used as the TikTok cover.
Uses only the two supplied player photos: no flip, no retouching of faces or jerseys; the only change
to the photos is cleaning the cut-out edge (halo / white strokes) and a uniform scale per photo.
usage: poster.py out.png"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, '..', 'images')
W, H = 1080, 1920
F = lambda n, s: ImageFont.truetype(os.path.join(HERE, 'fonts', n), s)
ANTON = 'Anton-Regular.ttf'; BARLOW_B = 'BarlowCondensed-Bold.ttf'
WHITE = (255, 255, 255); LGREY = (200, 200, 200); GREY = (150, 150, 150)
X0 = 92

def clean_cutout(path):
    """Remove the white strokes / pale halo left on the cut-out edge. Only pale, unsaturated pixels
    hugging the background are touched; skin, beard, hair and the inside of the photo keep their pixels."""
    im = np.array(Image.open(path).convert('RGBA')).astype(np.float32)
    rgb, a = im[..., :3], im[..., 3].copy()
    lum = rgb.mean(-1); sat = rgb.max(-1) - rgb.min(-1)
    pale = (lum > 195) & (sat < 35)                                  # white / light-grey, not jersey blue
    d_bg = ndimage.distance_transform_edt(a >= 20)                   # distance to the transparent background
    kill = pale & (d_bg <= 8) & ((a < 250) | (d_bg <= 4))
    a[kill] = 0
    # pale semi-transparent pixels that survive take the colour of their nearest solid neighbour
    solid = a >= 250
    _, (iy, ix) = ndimage.distance_transform_edt(~solid, return_indices=True)
    near = rgb[iy, ix]
    fix = (~solid) & (a > 0) & (lum > near.mean(-1) + 30) & (sat < 35)
    rgb[fix] = near[fix]
    # re-smooth the matte only where pixels were removed (anti-aliasing of the new edge)
    zone = ndimage.binary_dilation(kill, iterations=3)
    soft = np.array(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32)
    a = np.where(zone, np.minimum(a, soft), a)
    out = np.dstack([rgb, a]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')

def place(canvas, im, eye_xy_src, eye_mouth_src, eye_xy_dst, eye_mouth_dst):
    s = eye_mouth_dst / eye_mouth_src                       # uniform scale: proportions untouched
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    ox = round(eye_xy_dst[0] - eye_xy_src[0] * s); oy = round(eye_xy_dst[1] - eye_xy_src[1] * s)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); layer.alpha_composite(im, (max(ox, 0), max(oy, 0)),
                                                                             (max(-ox, 0), max(-oy, 0)))
    canvas.alpha_composite(layer)
    return s, ox, oy

def text_w(font, s, track=0): return sum(font.getlength(c) for c in s) + track * (len(s) - 1)
def fit(name, s, max_w, start):
    size = start
    while text_w(F(name, size), s) > max_w: size -= 1
    return F(name, size)
def draw(d, xy, s, font, fill, track=0):
    x, y = xy
    if not track: d.text((x, y), s, font=font, fill=fill); return
    for c in s: d.text((x, y), c, font=font, fill=fill); x += font.getlength(c) + track

def build():
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    EYE_Y, EM = 322, 88          # same eye line, same eye-to-mouth distance for both faces
    asvel = clean_cutout(os.path.join(IMG, '2.webp'))
    darius = clean_cutout(os.path.join(IMG, '3.webp'))
    # ASVEL player left (frontal); Darius Johnson right, his photo's cut right edge sits on the frame edge
    place(canvas, asvel, (579, 206), 99, (268, EYE_Y), EM)
    s, ox, oy = place(canvas, darius, (812, 305), 205, (812, EYE_Y), EM)
    assert ox + round(darius.width * s) >= W, 'Darius cut edge must sit outside the frame'
    # bust crop: fade to black under the chests (hides the photos' cut bottoms), black info zone below
    g = np.zeros((H, W), np.float32)
    y0, y1 = 760, 930
    ramp = np.clip((np.arange(H) - y0) / (y1 - y0), 0, 1) ** 1.4
    g[:] = ramp[:, None]
    shade = Image.new('RGBA', (W, H), (0, 0, 0, 0)); shade.putalpha(Image.fromarray((g * 255).astype(np.uint8)))
    canvas.alpha_composite(shade)
    # ---- information zone: left-aligned, away from TikTok's right rail and bottom caption
    d = ImageDraw.Draw(canvas)
    t = fit(ANTON, 'ASVEL – ROANNE', 818, 230)
    draw(d, (X0 - 6, 868), 'ASVEL – ROANNE', t, WHITE)
    d.rectangle([X0, 1098, X0 + 130, 1105], fill=WHITE)
    l1 = fit(ANTON, 'DIMANCHE 11 OCTOBRE · 19H', 800, 104)
    draw(d, (X0, 1122), 'DIMANCHE 11 OCTOBRE · 19H', l1, WHITE)
    draw(d, (X0, 1232), 'ASTROBALLE', F(ANTON, l1.size), WHITE)
    draw(d, (X0 + 2, 1362), 'EN DIRECT SUR', F(BARLOW_B, 54), LGREY, track=4)
    l3 = fit(ANTON, 'LA CHAÎNE L’ÉQUIPE ET DAZN', 800, 84)
    draw(d, (X0, 1420), 'LA CHAÎNE L’ÉQUIPE ET DAZN', l3, WHITE)
    draw(d, (X0 + 2, 1514), 'ASVEL_NEWS', F(BARLOW_B, 52), GREY, track=6)
    return canvas.convert('RGB')

if __name__ == '__main__':
    build().save(sys.argv[1])
    print('ok', sys.argv[1])
