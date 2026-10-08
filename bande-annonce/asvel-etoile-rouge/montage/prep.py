import numpy as np, sys, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
S=sys.argv[1]; R=sys.argv[2]
# --- Mills: remove white background (only components connected to border)
im=np.asarray(Image.open(R+'/images/patty-mills.jpg').convert('RGB')).astype(np.float32)
mn=im.min(2); near=mn>228
lab,n=nd.label(near)
border=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]))-{0}
bg=np.isin(lab,list(border))
fg=~bg   # bg ne contient que le blanc relie au bord : le blanc des yeux reste opaque
# bande de bord : alpha doux tire de la "blancheur", puis on retire le blanc melange (unmix)
band=fg & nd.binary_dilation(bg,iterations=5)
a=fg.astype(np.float32)
soft=np.clip((250-mn)/70,0,1)
a[band]=soft[band]
a=cv2.GaussianBlur(a,(0,0),0.6)*fg
rgb=im.copy()
aa=np.maximum(a,0.05)[...,None]
un=(im-(1-aa)*255)/aa
rgb[band]=np.clip(un,0,255)[band]
out=np.dstack([rgb,a*255]).clip(0,255).astype(np.uint8)
Image.fromarray(out,'RGBA').save(S+'/assets/mills.png')
# --- Moneke: already RGBA
m=Image.open(S+'/../images/1.webp').convert('RGBA')
ma=np.asarray(m).astype(np.float32)
print('moneke alpha bbox', Image.fromarray(ma[...,3].astype(np.uint8)).getbbox(), 'mills bbox', Image.fromarray((a*255).astype(np.uint8)).getbbox())
m.save(S+'/assets/moneke.png')
# --- basket: remove ball, crop blurred band
b=cv2.imread(S+'/prev/open_src.png')
mask=np.zeros(b.shape[:2],np.uint8); cv2.circle(mask,(433,930),52,255,-1)
b2=cv2.inpaint(b,mask,9,cv2.INPAINT_TELEA)
cv2.imwrite(S+'/assets/basket_clean.png',b2)
