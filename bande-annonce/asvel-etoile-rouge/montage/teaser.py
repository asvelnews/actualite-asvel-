"""Teaser (18 s) : RENDEZ-VOUS LUNDI 12 OCTOBRE pour la bande-annonce complete.
Reprend des passages de la bande-annonce (render.py) et ajoute un carton final.
Usage : python3 teaser.py <sortie.mp4 video seule> [--frames i,j,...]"""
import sys, os, subprocess
import numpy as np
from PIL import Image
import render as R
from render import (W, H, FPS, CX, RED, WHITE, ANTON, B8, B6, MILLS, MONEKE, bg, glow, stripes, shape, para,
                    kinetic, echo, fit, e_expo, e_io, seg, c01)

TD = 18.0
N = int(TD * FPS)
T_CARD = 12.3
# (debut teaser, fin teaser, temps bande-annonce correspondant au debut)
SEGS = [(0.0, 6.0, 0.0),        # chronometre 5 -> 0, bris de verre
        (6.0, 7.5, 25.0),       # ARE YOU READY?
        (7.5, 9.9, 27.30),      # Patty Mills : tir en suspension (sur l'entree de basse)
        (9.9, T_CARD, 32.55)]   # transition rouge, Chima Moneke : penetration et finition

def card(t):
    u = t - T_CARD
    can = bg(glow(285, 420, 520, (255, 255, 255), 0.15), glow(800, 420, 520, (255, 25, 30), 0.26))
    stripes(can, 0, 0, 9)
    k = e_expo(seg(u, 0.0, 0.5))
    shape(can, para(250 - 900 * (1 - k), 470, 300, 760, 0.3), (255, 255, 255, 20))
    shape(can, para(830 + 900 * (1 - k), 470, 300, 760, 0.3), (226, 28, 38, 45))
    kp = e_expo(seg(u, 0.0, 0.55))
    sw = seg(u, 0.55, 1.25) if 0.55 < u < 1.25 else None
    can.alpha_composite(MILLS.layer(2.53, 285 - 620 * (1 - kp), 335, fade_bottom=(600, 790), sweep=sw))
    can.alpha_composite(MONEKE.layer(2.75, 805 + 620 * (1 - kp), 335, fade_bottom=(600, 790), sweep=sw))
    kinetic(can, 'BANDE-ANNONCE COMPLÈTE', B8, 50, RED, CX, 950, u - 0.05, stagger=0.02, dur=0.3, track=10)
    rs = fit('RENDEZ-VOUS', ANTON, 880, 200)
    kinetic(can, 'RENDEZ-VOUS', ANTON, rs, WHITE, CX, 1135, u - 0.12, stagger=0.035, dur=0.35)
    echo(can, 'RENDEZ-VOUS', ANTON, rs, WHITE, CX, 1135, u - 0.4, n=3)
    ls = fit('LUNDI 12 OCTOBRE', ANTON, 860, 150)
    kinetic(can, 'LUNDI 12 OCTOBRE', ANTON, ls, RED, CX, 1300, u - 0.35, stagger=0.03, dur=0.35)
    hw = 210 * e_expo(seg(u, 0.6, 0.9))
    shape(can, [(CX - hw, 1346), (CX + hw, 1346), (CX + hw, 1350), (CX - hw, 1350)], RED + (255,))
    kinetic(can, 'ASVEL – ÉTOILE ROUGE DE BELGRADE', B8, 44, (225, 225, 225), CX, 1420, u - 0.75, stagger=0.012, dur=0.3, track=2)
    kinetic(can, 'ASVEL_NEWS', B6, 30, (150, 150, 150), CX, 1480, u - 0.95, stagger=0.02, dur=0.3, track=4)
    arr = np.asarray(can.convert('RGB')).astype(np.float32)
    fl = 0.32 * (1 - seg(u, 0.0, 0.12))
    arr = arr * (1 - fl) + 255 * fl
    arr *= 1 - e_io(seg(t, TD - 0.55, TD - 0.03))
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGB')

def tframe(i):
    t = i / FPS
    for a, b, o in SEGS:
        if a <= t < b:
            return R.frame_t(t - a + o, 'date')
    return card(t)

if __name__ == '__main__':
    out = sys.argv[1]
    if '--frames' in sys.argv:
        idx = [int(v) for v in sys.argv[sys.argv.index('--frames') + 1].split(',')]
        os.makedirs(out, exist_ok=True)
        for i in idx: tframe(i).save(os.path.join(out, f't{i:04d}.png'))
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '14',
                          '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(N):
        p.stdin.write(tframe(i).tobytes())
        if i % 60 == 0: print(i, flush=True)
    p.stdin.close(); p.wait()
