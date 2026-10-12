"""Détourage d'une photo livrée sur fond noir uni : sélection du fond noir
connecté aux bords (tolérance serrée), puis contour adouci. Aucune IA."""
import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
src, out = sys.argv[1:3]
rgb = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
near = rgb.max(2) <= 10
lab, n = ndi.label(near)
edge = set(np.unique(np.concatenate([lab[0], lab[:, 0], lab[:, -1], lab[-1]]))) - {0}
bg = ndi.binary_opening(np.isin(lab, list(edge)), iterations=1)
fg = ndi.binary_fill_holes(~bg)
lab2, n2 = ndi.label(fg); sizes = ndi.sum(fg, lab2, range(1, n2 + 1)); fg = lab2 == (np.argmax(sizes) + 1)
fg = ndi.binary_erosion(fg, iterations=3)
alpha = cv2.GaussianBlur(fg.astype(np.float32), (0, 0), 0.9)
# la photo source porte un liseré clair (ancien détourage) : on l'efface sur les 5 px du bord
dist = ndi.distance_transform_edt(fg)
white = np.clip((rgb.min(2) - 120) / 100.0, 0, 1)
band = (dist > 0) & (dist < 5)
alpha = np.where(band, alpha * (1 - white * (1 - dist / 5)), alpha)
Image.fromarray(np.dstack([rgb.astype(np.uint8), (alpha * 255).astype(np.uint8)]), 'RGBA').save(out)
