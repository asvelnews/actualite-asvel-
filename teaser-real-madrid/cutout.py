import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
src, out, prev = sys.argv[1:4]
im = Image.open(src).convert('RGB'); rgb = np.asarray(im).astype(np.float32); a = rgb.astype(np.int16)
near = (a.min(2) >= 251) & ((a.max(2)-a.min(2)) <= 6)
lab, n = ndi.label(near)
edge = set(np.unique(np.concatenate([lab[0], lab[:,0], lab[:,-1]]))) - {0}
bg = ndi.binary_opening(np.isin(lab, list(edge)), iterations=1)
fg = ndi.binary_fill_holes(~bg)
lab2, n2 = ndi.label(fg); sizes = ndi.sum(fg, lab2, range(1, n2+1)); fg = lab2 == (np.argmax(sizes)+1)
dist = ndi.distance_transform_edt(fg)
W = 7.0
band = (dist > 0) & (dist < W)
# classic "colour to alpha" (white) inside the edge band only
ca = ((255 - rgb) / 255.0).max(2)
ca = np.clip(ca * 1.6, 0, 1)                 # dark/skin pixels reach full opacity
t = np.clip(dist / W, 0, 1)
alpha = np.where(band, ca * (1 - t) + t * 1.0, fg.astype(np.float32))
alpha = np.where(band, np.minimum(alpha, np.clip(ca*3, 0, 1)), alpha)  # near-white edge pixels go transparent
alpha = cv2.GaussianBlur(alpha.astype(np.float32), (0,0), 0.7) * (dist > 0.5)
# un-premultiply against white to remove white spill
al = np.clip(alpha, 1e-3, 1)[..., None]
col = np.where(band[..., None], np.clip((rgb - 255*(1-al)) / al, 0, 255), rgb)
rgba = np.dstack([col.astype(np.uint8), (alpha*255).clip(0,255).astype(np.uint8)])
Image.fromarray(rgba, 'RGBA').save(out)
b = Image.new('RGBA', im.size, (0,0,0,255)); b.alpha_composite(Image.fromarray(rgba,'RGBA')); b.convert('RGB').save(prev)
