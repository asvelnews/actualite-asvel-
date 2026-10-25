"""Prépare la photo réelle de la LDLC Arena : upscale 2x Lanczos, masques ciel / lumières / sol.
Les pixels du bâtiment ne sont jamais repeints : on ne fait que découper le ciel."""
from PIL import Image, ImageFilter
import numpy as np
src = Image.open('assets/arena/01_LDLC_ARENA.jpg').convert('RGB')
W, H = src.size
S = 2
big = src.resize((W*S, H*S), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
a = np.asarray(src).astype(float)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
lum = a.mean(2)
blue = b - (r + g) / 2
from scipy import ndimage
sky = (blue > 10) & ((b - r) > 0.42 * b) & (lum < 175)
sky = sky | ndimage.binary_closing(sky, iterations=2)
# le ciel = composantes connectées touchant le bord supérieur ou gauche (au-dessus de l'horizon)
lab, n = ndimage.label(sky)
keep = set(lab[0, :].tolist()) | set(lab[:int(H*0.72), 0].tolist())
keep.discard(0)
mask = np.isin(lab, list(keep))
mask = ndimage.binary_fill_holes(mask)
m = Image.fromarray((mask*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
m = m.resize((W*S, H*S), Image.LANCZOS)
rgba = big.copy(); rgba.putalpha(Image.fromarray(255 - np.asarray(m)))
rgba.save('public/arena_building.png')
# lumières : pixels très lumineux et chauds/blancs (fenêtres, verrière, lampadaires, enseigne)
lights = np.clip((lum - 150) / 70, 0, 1) * (~mask)
L = Image.fromarray((lights*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)).resize((W*S, H*S), Image.LANCZOS)
L.save('public/arena_lights.png')
# sol (parvis) : bas de l'image
yy = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
ground = np.clip((yy - 0.80) / 0.08, 0, 1)
Image.fromarray((ground*255).astype(np.uint8)).resize((W*S, H*S), Image.LANCZOS).save('public/arena_ground.png')
print('arena', big.size, 'sky frac', mask.mean())

# --- Calques teintés précalculés (chargement garanti par <Img>, pas de mask CSS asynchrone)
bal = np.asarray(Image.open('public/arena_building.png'))[..., 3].astype(float) / 255
h2, w2 = bal.shape
yy2 = np.linspace(0, 1, h2)[:, None]
tint = np.zeros((h2, w2, 4))
tint[..., 0] = 160 - 120 * yy2; tint[..., 1] = 8; tint[..., 2] = 12
tint[..., 3] = bal * (0.62 - 0.35 * yy2) * 255
Image.fromarray(tint.astype(np.uint8)).save('public/arena_tint.png')
li = np.asarray(Image.open('public/arena_lights.png')).astype(float) / 255
lay = np.zeros((h2, w2, 4)); lay[..., 0] = 255; lay[..., 1] = 70; lay[..., 2] = 30; lay[..., 3] = li * 255
Image.fromarray(lay.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)).save('public/arena_lights_red.png')
gr = np.asarray(Image.open('public/arena_ground.png')).astype(float) / 255
xx2 = np.linspace(0, 1, w2)[None, :]
pool = np.exp(-(((xx2 - 0.64) / 0.25) ** 2) - (((yy2 - 0.86) / 0.12) ** 2))
lay = np.zeros((h2, w2, 4)); lay[..., 0] = 200 + 55 * pool; lay[..., 1] = 20 + 40 * pool; lay[..., 2] = 18
lay[..., 3] = gr * (0.45 + 0.5 * pool) * 255
Image.fromarray(lay.astype(np.uint8)).save('public/arena_ground_red.png')
print('tint layers ok')
