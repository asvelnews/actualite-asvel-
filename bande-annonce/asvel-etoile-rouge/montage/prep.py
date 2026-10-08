import numpy as np, sys, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
S=sys.argv[1]; R=sys.argv[2]
# --- Mills : photo fournie (maillot LDLC ASVEL n.8), deja detouree ; simple recadrage au-dessus des genoux
from PIL import Image as _I
_I.open(S+'/../images/2.png').convert('RGBA').crop((250,40,580,700)).save(S+'/assets/mills.png')
# --- Moneke: already RGBA
m=Image.open(S+'/../images/1.webp').convert('RGBA')
ma=np.asarray(m).astype(np.float32)
print('moneke alpha bbox', Image.fromarray(ma[...,3].astype(np.uint8)).getbbox(), )
m.save(S+'/assets/moneke.png')
# --- basket: remove ball, crop blurred band
b=cv2.imread(S+'/prev/open_src.png')
mask=np.zeros(b.shape[:2],np.uint8); cv2.circle(mask,(433,930),52,255,-1)
b2=cv2.inpaint(b,mask,9,cv2.INPAINT_TELEA)
cv2.imwrite(S+'/assets/basket_clean.png',b2)
