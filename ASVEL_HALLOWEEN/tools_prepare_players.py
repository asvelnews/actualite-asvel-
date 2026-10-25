"""Calques VFX des joueurs. Les photos originales restent intactes : on produit
uniquement des calques superposables (fissures, silhouette pour l'ombre/aura)."""
from PIL import Image, ImageFilter
import numpy as np
from scipy import ndimage
rng = np.random.default_rng(8)

def cracks(shape, n, seed):
    h, w = shape
    r = np.random.default_rng(seed)
    pts = r.random((n, 2)) * [h, w]
    yy, xx = np.mgrid[0:h, 0:w]
    d1 = np.full(shape, 1e9); d2 = np.full(shape, 1e9)
    for py, px in pts:
        d = np.hypot(yy - py, xx - px)
        m = d < d1
        d2 = np.where(m, d1, np.minimum(d2, d)); d1 = np.where(m, d, d1)
    e = d2 - d1
    line = np.clip(1 - e / 2.2, 0, 1)
    # rupture irrégulière des lignes pour éviter le motif trop régulier
    noise = ndimage.gaussian_filter(r.random(shape), 6)
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    return line * np.clip((noise - 0.35) * 3, 0, 1)

def build(src, out, scale, face_box, skin_tol, seed, ncell):
    im = Image.open(src).convert('RGBA')
    if scale != 1:
        im = im.resize((im.width*scale, im.height*scale), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.5, 40, 2))
    im.save(f'public/{out}.png')
    a = np.asarray(im).astype(float)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3] / 255
    lum = (r + g + b) / 3
    skin = (al > 0.95) & (r > g) & (g > b) & (r - b > skin_tol) & (lum > 45) & (lum < 235)
    skin = ndimage.binary_opening(skin, iterations=2)
    x0, y0, x1, y1 = [v*scale for v in face_box]
    skin[y0:y1, x0:x1] = False      # jamais de fissures sur le visage / cou
    skin = ndimage.binary_erosion(skin, iterations=3*scale)
    soft = ndimage.gaussian_filter(skin.astype(float), 2*scale)
    c = cracks(skin.shape, ncell, seed) * soft
    core = np.clip(c * 1.6, 0, 1)
    glow = ndimage.gaussian_filter(c, 3*scale)
    rgba = np.zeros(skin.shape + (4,))
    rgba[..., 0] = 255; rgba[..., 1] = 60 + 150 * core; rgba[..., 2] = 20 + 90 * core
    rgba[..., 3] = np.clip(core + glow * 1.5, 0, 1) * 255
    Image.fromarray(rgba.astype(np.uint8)).save(f'public/{out}_cracks.png')
    # silhouette noire (ombre géante, halo)
    sil = np.zeros(skin.shape + (4,), np.uint8); sil[..., 3] = (al * 255).astype(np.uint8)
    Image.fromarray(sil).save(f'public/{out}_silhouette.png')
    print(out, im.size, 'skin px', int(skin.sum()))

build('assets/players/03_PATTY_MILLS.png', 'patty', 1, (330, 20, 500, 230), 22, 3, 260)
build('assets/players/04_TADAS_SEDEKERSKIS.png', 'tadas', 2, (110, 0, 245, 150), 25, 5, 220)

# --- Liseré lumineux (rim light) : bord de la silhouette éclairé depuis un côté.
def rim(name, color, side):
    al = np.asarray(Image.open(f'public/{name}.png'))[..., 3].astype(float) / 255
    inside = al > 0.5
    dist = ndimage.distance_transform_edt(inside)
    band = np.exp(-dist / (6 if name == 'patty' else 9)) * al
    gy, gx = np.gradient(ndimage.gaussian_filter(al, 4))
    facing = np.clip(-(gx * side[0] + gy * side[1]) * 40, 0, 1)  # bords tournés vers la lumière
    a = np.clip(band * (0.35 + 0.65 * facing) * 1.4, 0, 1)
    out = np.zeros(al.shape + (4,)); out[..., :3] = color; out[..., 3] = a * 255
    Image.fromarray(out.astype(np.uint8)).save(f'public/{name}_rim.png')

rim('patty', (255, 40, 30), (1, 0.3))
rim('tadas', (255, 110, 40), (-1, 0.3))
print('rim ok')
