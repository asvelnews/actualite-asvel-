# -*- coding: utf-8 -*-
"""Montage de « ASVEL : la naissance d'une légende » — partie 1 (1948-1957).

    python3 voix.py      # prépare les segments de voix (enregistrements ou synthèse)
    python3 montage.py   # calcule la timeline, rend l'image, mixe et encode

Options : --apercu <t0> <t1>  rend uniquement cet intervalle (en secondes)
          --image <t>         exporte une seule image PNG à l'instant t
"""
import functools
import json
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from narration import segments
import musique

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
W, H, FPS, SR = 1920, 1080, 25, 48000
XF = 0.8                      # durée des fondus enchaînés
DEBUT_VOIX = 2.0              # la voix démarre après un court fondu d'ouverture

# ───────────────────────── timeline (calée sur la voix) ─────────────────────────
INFO = json.load(open(os.path.join(BUILD, "voix.json")))
TEXTE = {sid: text for sid, text, _, _ in segments()}
T, E = {}, {}
_t = DEBUT_VOIX
for _sid, _text, _pause, _ in segments():
    T[_sid] = _t
    E[_sid] = _t + INFO[_sid]["duree"]
    _t = E[_sid] + _pause
FIN_VOIX = _t


def mot(sid, fragment):
    """Instant approximatif où « fragment » est prononcé dans le segment sid
    (au prorata des caractères)."""
    txt = TEXTE[sid]
    i = txt.index(fragment)
    return T[sid] + (E[sid] - T[sid]) * i / len(txt)


# ───────────────────────── outils graphiques ─────────────────────────
CREME = (237, 230, 214)
OR = (201, 164, 92)
GRIS = (168, 160, 146)
FONTS = os.path.join(HERE, "fonts")


@functools.lru_cache(None)
def police(nom, taille, poids=400):
    f = ImageFont.truetype(os.path.join(FONTS, nom + ".ttf"), taille)
    try:
        f.set_variation_by_axes([poids])
    except Exception:
        pass
    return f


def couche(img):
    """PIL RGBA -> (rgb float32, alpha float32)."""
    a = np.asarray(img.convert("RGBA"), dtype=np.float32) / 255.0
    return a[..., :3].copy(), a[..., 3:].copy()


@functools.lru_cache(None)
def texte(s, nom, taille, poids=400, couleur=CREME, espace=0):
    f = police(nom, taille, poids)
    asc, desc = f.getmetrics()
    largeur = int(sum(f.getlength(c) for c in s) + espace * max(0, len(s) - 1)) + 4
    img = Image.new("RGBA", (largeur, asc + desc + 4), couleur + (0,))
    d = ImageDraw.Draw(img)
    x = 2
    for c in s:
        d.text((x, 2), c, font=f, fill=couleur + (255,), anchor="la")
        x += f.getlength(c) + espace
    return couche(img)


def poser(cv, lay, x, y, o=1.0, ancre="hg"):
    """Compose une couche sur le canevas. ancre : hg (haut-gauche) / hc (haut-centre)
    / cc (centre) / hd (haut-droite)."""
    if o <= 0.003:
        return
    rgb, a = lay
    h, w = a.shape[:2]
    if ancre[1] == "c":
        x -= w / 2
    elif ancre[1] == "d":
        x -= w
    if ancre[0] == "c":
        y -= h / 2
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sa = a[y0 - y:y1 - y, x0 - x:x1 - x] * o
    zone = cv[y0:y1, x0:x1]
    zone *= 1 - sa
    zone += rgb[y0 - y:y1 - y, x0 - x:x1 - x] * sa


def rect(cv, x, y, w, h, couleur, o=1.0):
    if o <= 0.003 or w <= 0 or h <= 0:
        return
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(W, int(x + w)), min(H, int(y + h))
    c = np.array(couleur, np.float32) / 255
    cv[y0:y1, x0:x1] = cv[y0:y1, x0:x1] * (1 - o) + c * o


def lisse(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def apparait(t, t0, d=0.7, t1=None, d1=0.6):
    o = lisse((t - t0) / d)
    if t1 is not None:
        o *= 1 - lisse((t - t1) / d1)
    return o


def interp(t, cles):
    """Interpolation douce entre images-clés [(t, valeur), ...]."""
    if t <= cles[0][0]:
        return cles[0][1]
    for (ta, va), (tb, vb) in zip(cles, cles[1:]):
        if t <= tb:
            p = lisse((t - ta) / (tb - ta))
            return tuple(a + (b - a) * p for a, b in zip(va, vb))
    return cles[-1][1]


# fond sobre : anthracite chaud, léger vignettage
def _fond():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.45) / (H * 0.75)) ** 2)
    v = np.clip(1 - 0.55 * r ** 1.6, 0.25, 1)[..., None]
    base = np.array([31, 31, 30], np.float32) / 255
    return (base * v).astype(np.float32)


FOND = _fond()
_rng = np.random.default_rng(3)
GRAIN = [(_rng.standard_normal((H, W, 1)) * 0.005).astype(np.float32) for _ in range(6)]


# ───────────────────────── photographies ─────────────────────────
IMG = os.path.join(HERE, "images")


@functools.lru_cache(None)
def source(nom, recadre=None):
    im = Image.open(os.path.join(IMG, nom)).convert("RGB")
    if recadre:
        im = im.crop(recadre)
    # suréchantillonnage unique (Lanczos) puis recadrages successifs
    return im.resize((im.width * 4, im.height * 4), Image.LANCZOS)


@functools.lru_cache(None)
def ombre(w, h, bord):
    m = 40
    img = Image.new("L", (w + 2 * bord + 2 * m, h + 2 * bord + 2 * m), 0)
    ImageDraw.Draw(img).rectangle([m, m + 10, m + w + 2 * bord, m + h + 2 * bord + 10], fill=150)
    img = img.filter(ImageFilter.GaussianBlur(22))
    a = np.asarray(img, np.float32)[..., None] / 255
    return np.zeros(a.shape[:2] + (3,), np.float32), a


def photo(cv, nom, x, y, w, h, zoom=1.0, cx=0.5, cy=0.5, o=1.0, recadre=None, bord=10):
    """Photo encadrée (bord crème + ombre) ; zoom/cx/cy = mouvement de caméra
    à l'intérieur du cadre fixe."""
    if o <= 0.003:
        return
    src = source(nom, recadre)
    sw, sh = src.size
    bw, bh = sw / zoom, sh / zoom
    x0 = min(max(cx * sw - bw / 2, 0), sw - bw)
    y0 = min(max(cy * sh - bh / 2, 0), sh - bh)
    x, y = int(round(x)), int(round(y))
    im = src.resize((w, h), Image.BICUBIC, box=(x0, y0, x0 + bw, y0 + bh))
    poser(cv, ombre(w, h, bord), x - bord - 40, y - bord - 40, o * 0.9)
    rect(cv, x - bord, y - bord, w + 2 * bord, h + 2 * bord, (232, 226, 211), o)
    arr = np.asarray(im, np.float32) / 255
    poser(cv, (arr, np.ones((h, w, 1), np.float32)), x, y, o)


def taille(nom, hauteur=None, largeur=None, recadre=None):
    im = Image.open(os.path.join(IMG, nom))
    sw, sh = (recadre[2] - recadre[0], recadre[3] - recadre[1]) if recadre else im.size
    if hauteur:
        return int(sw * hauteur / sh), hauteur
    return largeur, int(sh * largeur / sw)


def credit(cv, s, o, x=W - 60, y=H - 52):
    poser(cv, texte(s, "SourceSans3", 22, 400, GRIS), x, y, o * 0.9, "hd")


CARTE = "carte-annees-1950.png"
CARTE_CROP = (4, 4, 299, 219)            # retire la marge et la tache noire du bord
# zones de la carte (fractions) : groupe du haut, groupe du bas, inscriptions
Z_HAUT = (0.62, 0.30)
Z_BAS = (0.42, 0.78)
Z_INSCR = (0.86, 0.73)

# ───────────────────────── scènes ─────────────────────────


def sc_naissance(cv, t):
    # titre discret
    o = apparait(t, T["s1_01"] + 0.3, 1.0, T["s1_06"] + 0.4)
    poser(cv, texte("AUX ORIGINES DU NOM", "Oswald", 30, 500, OR, 9), W / 2, 250, o, "hc")
    rect(cv, W / 2 - 40, 305, 80, 2, OR, o)

    # fusion : les deux blocs se rejoignent au centre
    p = lisse((t - (T["s1_06"] + 0.4)) / 2.0)
    yb = 430
    f1 = (T["s1_02"] + 0.2)
    f2 = (T["s1_03"] + 0.2)
    o1 = apparait(t, f1, 0.8) * (1 - p)
    o2 = apparait(t, f2, 0.8) * (1 - p)
    xl = 520 + (W / 2 - 520) * p
    xr = 1400 + (W / 2 - 1400) * p
    poser(cv, texte("ASSOCIATION SPORTIVE", "PlayfairDisplay", 56, 500, CREME, 3), xl, yb, o1, "hc")
    poser(cv, texte("VILLEURBANNAISE", "PlayfairDisplay", 56, 500, CREME, 3), xl, yb + 74, o1, "hc")
    poser(cv, texte("ÉVEIL LYONNAIS", "PlayfairDisplay", 56, 500, CREME, 3), xr, yb + 37, o2, "hc")
    poser(cv, texte("+", "PlayfairDisplay", 90, 400, OR), W / 2, yb + 10, apparait(t, f2 - 0.1, 0.6) * (1 - p), "hc")
    # traditions
    oa = apparait(t, mot("s1_05", "tradition"), 0.8, T["s1_06"] + 0.1)
    ob = apparait(t, mot("s1_05", "patronage"), 0.8, T["s1_06"] + 0.1)
    poser(cv, texte("Tradition sportive laïque", "SourceSans3", 34, 400, GRIS), xl, yb + 180, oa, "hc")
    poser(cv, texte("Patronage catholique", "SourceSans3", 34, 400, GRIS), xr, yb + 180, ob, "hc")

    # nom complet, initiales en évidence, puis ASVEL
    t_nom = mot("s1_07", "l'Association") - 0.2
    o_nom = apparait(t, t_nom, 1.0)
    q = min(1.0, max(0.0, (t - (T["s1_08"] + 0.2)) / 2.4))   # formation du sigle
    o_date = apparait(t, T["s1_07"] + 0.1, 0.9)
    if o_nom > 0:
        # 1) le reste du nom s'efface, les initiales restent en place
        for lay, x, y in nom_complet()[0]:
            poser(cv, lay, x, y, o_nom * (1 - lisse(q / 0.35)))
        o_ini = o_nom * (1 - lisse((q - 0.45) / 0.3))
        for lay, x, y, _ in nom_complet()[1]:
            poser(cv, lay, x, y, o_ini)
        # 2) elles laissent place au sigle ASVEL
        qs = lisse((q - 0.5) / 0.5)
        if qs > 0:
            poser(cv, echelle(sigle(), 0.9 + 0.1 * qs), W / 2, 440, qs, "cc")
    yd = 700 + 40 * q
    poser(cv, texte("21 DÉCEMBRE 1948", "Oswald", 54, 500, OR, 10), W / 2, yd, o_date, "hc")

    # Pierre Millet (sans photographie)
    o = apparait(t, T["s1_09"] + 0.2, 0.7, E["s1_10"] + 0.3)
    dx = 30 * (1 - o)
    rect(cv, 150 - dx, 872, 6, 104, OR, o)
    poser(cv, texte("Pierre Millet", "PlayfairDisplay", 54, 600, CREME), 178 - dx, 862, o)
    poser(cv, texte("Premier président de l'ASVEL", "SourceSans3", 32, 400, GRIS), 180 - dx, 935, o)


NOM_L1 = "ASSOCIATION SPORTIVE VILLEURBANNE"
NOM_L2 = "ÉVEIL LYONNAIS"
INIT = {(0, 0), (0, 12), (0, 21), (1, 0), (1, 6)}
NOM_TAILLE, CIBLE_TAILLE = 70, 230


@functools.lru_cache(None)
def glyphe(c, taille, couleur, poids=600):
    return texte(c, "PlayfairDisplay", taille, poids, couleur)


def echelle(lay, s):
    rgb, a = lay
    h, w = a.shape[:2]
    nw, nh = max(1, int(w * s)), max(1, int(h * s))
    im = np.concatenate([rgb, a], axis=2)
    im = Image.fromarray((im * 255).astype(np.uint8), "RGBA").resize((nw, nh), Image.BICUBIC)
    return couche(im)


@functools.lru_cache(None)
def nom_complet():
    """Lettres du nom complet : (couches non-initiales, initiales avec position et
    facteur d'échelle relatif aux glyphes cibles)."""
    f = police("PlayfairDisplay", NOM_TAILLE, 600)
    esp = 6
    autres, inits = [], []
    for li, (ligne, y) in enumerate(((NOM_L1, 400), (NOM_L2, 500))):
        largeur = sum(f.getlength(c) for c in ligne) + esp * (len(ligne) - 1)
        x = W / 2 - largeur / 2
        for ci, c in enumerate(ligne):
            if (li, ci) in INIT:
                inits.append((glyphe(c, NOM_TAILLE, OR), x - 2, y - 2, NOM_TAILLE / CIBLE_TAILLE))
            elif c != " ":
                autres.append((glyphe(c, NOM_TAILLE, CREME), x - 2, y - 2))
            x += f.getlength(c) + esp
    return autres, inits


@functools.lru_cache(None)
def sigle():
    return texte("ASVEL", "PlayfairDisplay", CIBLE_TAILLE, 600, OR, 18)


@functools.lru_cache(None)
def initiales_cible():
    f = police("PlayfairDisplay", CIBLE_TAILLE, 600)
    esp = 18
    largeur = sum(f.getlength(c) for c in "ASVEL") + esp * 4
    x = W / 2 - largeur / 2
    out = []
    for c in "ASVEL":
        out.append((glyphe(c, CIBLE_TAILLE, OR), x - 2, 330 - 2, 1.0))
        x += f.getlength(c) + esp
    return out


def compo_1948(cv, t, t0, t1, titre, sous_titre, kicker):
    w, h = taille("1948.jpg", hauteur=860)
    z = 1.0 + 0.035 * lisse((t - t0) / (t1 - t0))
    photo(cv, "1948.jpg", 170, 110, w, h, zoom=z, cx=0.5, cy=0.4)
    xt = 170 + w + 110
    poser(cv, texte(kicker, "Oswald", 30, 500, OR, 8), xt, 330, apparait(t, t0 + 0.6))
    poser(cv, texte(titre, "Oswald", 150, 500, CREME, 4), xt - 6, 370, apparait(t, t0 + 0.9))
    for i, ligne in enumerate(sous_titre):
        poser(cv, texte(ligne, "PlayfairDisplay", 50, 500, CREME), xt, 580 + i * 66, apparait(t, t0 + 1.3 + 0.2 * i))
    poser(cv, texte("Photographie et légende d'époque", "SourceSans3", 24, 400, GRIS), xt, 990 - 24, apparait(t, t0 + 1.6) * 0.9)


def sc_titre_1949(cv, t):
    compo_1948(cv, t, T["s2_01"], T["s2_02"] + 0.5, "1949",
               ["Premier titre de", "champion de France"], "QUELQUES MOIS APRÈS LA FUSION")


def sc_equipe(t0, t1, z0, z1, c0, c1):
    def f(cv, t):
        w, h = 1290, int(1290 * 449 / 600)
        p = lisse((t - t0) / (t1 - t0)) * 0.6 + 0.4 * (t - t0) / (t1 - t0)
        z = z0 + (z1 - z0) * p
        cx = c0[0] + (c1[0] - c0[0]) * p
        cy = c0[1] + (c1[1] - c0[1]) * p
        photo(cv, "1949.jpg", (W - w) // 2, (H - h) // 2 - 6, w, h, zoom=z, cx=cx, cy=cy)
        credit(cv, "Document d'archives", 1, y=H - 46)
    return f


def sc_buffiere(t_nom, t_roles, t0, t1):
    def f(cv, t):
        w, h = 454, 738
        z = 1.0 + 0.04 * lisse((t - t0) / (t1 - t0))
        photo(cv, "andre-buffiere.jpg", 330, (H - h) // 2, w, h, zoom=z, cx=0.5, cy=0.42)
        xt = 330 + w + 150
        o = apparait(t, t_nom, 0.8)
        poser(cv, texte("ANDRÉ BUFFIÈRE", "PlayfairDisplay", 84, 600, CREME, 3), xt, 395, o)
        rect(cv, xt + 2, 520, 140 * lisse((t - t_nom - 0.2) / 0.8), 4, OR, o)
        poser(cv, texte("Joueur, entraîneur, recruteur", "SourceSans3", 46, 400, CREME), xt, 555, apparait(t, t_roles, 0.8))
        poser(cv, texte("Champion de France avec l'ASVEL en 1950", "SourceSans3", 30, 400, GRIS), xt, 630, apparait(t, t_roles + 0.8, 0.8))
        credit(cv, "Document d'archives", 1)
    return f


def sc_1950(cv, t):
    yb = 330
    for x, an, rang, tin in ((W / 2 - 330, "1949", "1er titre", T["s2_09"] - 0.3),
                             (W / 2 + 330, "1950", "2e titre", mot("s2_11", "cinquante,") - 0.2)):
        o = apparait(t, tin, 0.8)
        poser(cv, texte(an, "Oswald", 190, 500, OR if an == "1950" else CREME, 6), x, yb + 20 * (1 - o), o, "hc")
        poser(cv, texte(rang.upper(), "Oswald", 36, 400, GRIS, 8), x, yb + 270, o, "hc")
    oq = apparait(t, T["s2_09"] + 0.6, 0.8) * (1 - apparait(t, mot("s2_11", "cinquante,") - 0.6, 0.5))
    poser(cv, texte("?", "PlayfairDisplay", 190, 400, GRIS), W / 2 + 330, yb + 10, oq * 0.8, "hc")
    o = apparait(t, T["s2_12"], 0.8)
    rect(cv, W / 2 - 60, 735, 120, 3, OR, o)
    poser(cv, texte("Deux championnats en deux ans", "PlayfairDisplay", 54, 500, CREME), W / 2, 770, o, "hc")


ANNEES = ["1949", "1950", "1952", "1955", "1956", "1957"]


def t_annees():
    return {"1949": -1, "1950": -1, "1952": mot("s3_01", "mille") - 0.1,
            "1955": mot("s3_02a", "mille") + 0.3, "1956": T["s3_02b"], "1957": T["s3_02c"] + 0.25}


def frise(cv, t, y, x0, x1, grand, o_glob=1.0, apparitions=None, accolade=None):
    apparitions = apparitions or {a: -1 for a in ANNEES}
    rect(cv, x0 - 40, y - 1, (x1 - x0 + 80), 3, OR, 0.75 * o_glob)
    pas = (x1 - x0) / 5
    for i, an in enumerate(ANNEES):
        x = x0 + i * pas
        o = apparait(t, apparitions[an], 0.6) * o_glob
        r = (13 if grand else 10) * (0.6 + 0.4 * o)
        rect(cv, x - r, y - r, 2 * r, 2 * r, OR, o)
        rect(cv, x - r + 4, y - r + 4, 2 * r - 8, 2 * r - 8, (25, 25, 24), o)
        taille_txt = 84 if grand else 58
        dy = taille_txt + (36 if not grand else 44)
        poser(cv, texte(an, "Oswald", taille_txt, 500, CREME, 2), x, y - dy + 12 * (1 - o), o, "hc")
    if accolade:
        ta, label = accolade
        o = apparait(t, ta, 0.8) * o_glob
        xa, xb = x0 + 3 * pas - 30, x0 + 5 * pas + 30
        ya = y + (40 if not grand else 60)
        rect(cv, xa, ya, (xb - xa) * lisse((t - ta) / 0.9), 3, OR, o)
        rect(cv, xa, ya - 14, 3, 14, OR, o)
        rect(cv, xb - 3, ya - 14, 3, 14 * lisse((t - ta - 0.6) / 0.3), OR, o)
        poser(cv, texte(label, "Oswald", 32 if not grand else 38, 400, OR, 6), (xa + xb) / 2, ya + 18, o, "hc")


def carte_keys(t0, t1):
    d = t1 - t0
    return [(t0, (1.0, 0.5, 0.5)), (t0 + d * 0.22, (1.0, 0.5, 0.5)),
            (t0 + d * 0.40, (1.3,) + Z_HAUT), (t0 + d * 0.55, (1.3,) + Z_HAUT),
            (t0 + d * 0.72, (1.3,) + Z_BAS), (t0 + d * 0.82, (1.3,) + Z_BAS),
            (t1, (1.35,) + Z_INSCR)]


def sc_titres(cv, t):
    t0, t1 = T["s3_01"] - 0.4, T["s3_05"]
    w, h = taille(CARTE, largeur=760, recadre=CARTE_CROP)
    z, cx, cy = interp(t, carte_keys(t0, t1))
    photo(cv, CARTE, (W - w) // 2, 60, w, h, zoom=z, cx=cx, cy=cy, recadre=CARTE_CROP)
    frise(cv, t, 830, 330, 1590, False, 1.0, t_annees(),
          accolade=(mot("s3_04", "Trois") + 0.2, "3 TITRES CONSÉCUTIFS"))
    o = apparait(t, mot("s3_03", "six"), 0.8)
    poser(cv, texte("6 CHAMPIONNATS DE FRANCE", "Oswald", 32, 400, OR, 6), 290, 870, o)
    credit(cv, "Carte d'époque — document d'archives", 1, x=W - 40, y=H - 40)


def sc_origines(cv, t):
    compo_1948(cv, t, T["s3_05"] - 0.3, T["s3_08"], "1949",
               ["Aux origines", "du palmarès"], "RAPPEL")


def sc_frise_complete(cv, t):
    t0 = T["s3_08"] - 0.3
    o = apparait(t, t0 + 0.2, 0.8)
    poser(cv, texte("CHAMPIONNATS DE FRANCE", "Oswald", 38, 500, OR, 12), W / 2, 230, o, "hc")
    rect(cv, W / 2 - 50, 290, 100, 2, OR, o)
    app = {an: t0 + 0.3 + 0.18 * i for i, an in enumerate(ANNEES)}
    frise(cv, t, 560, 330, 1590, True, 1.0, app, accolade=(t0 + 1.6, "1955 – 1957 : TROIS TITRES DE SUITE"))
    poser(cv, texte("1949 – 1957", "PlayfairDisplay", 44, 500, GRIS), W / 2, 880, apparait(t, t0 + 2.0, 0.8), "hc")


def carte_coupe(cv, x, y, an, o):
    if o <= 0:
        return
    dx = 40 * (1 - o)
    rect(cv, x + dx, y, 800, 190, (40, 39, 36), o * 0.95)
    rect(cv, x + dx, y, 6, 190, OR, o)
    poser(cv, texte(an, "Oswald", 104, 500, OR, 3), x + dx + 50, y + 22, o)
    poser(cv, texte("COUPE DE FRANCE", "Oswald", 54, 400, CREME, 6), x + dx + 300, y + 58, o)


def sc_coupes(cv, t):
    # la carte est d'abord seule (rapprochement léger sur les inscriptions),
    # puis glisse à gauche pour accompagner les deux cartes « Coupe de France »
    ta, tb, t1 = T["s4_01"] - 0.5, T["s4_02"] - 0.6, T["s4_05"]
    wa, _ = taille(CARTE, largeur=860, recadre=CARTE_CROP)
    w, x, y, z, cx, cy = interp(t, [(ta, (860, (W - 860) / 2, 540, 1.0, 0.5, 0.5)),
                                    (tb - 0.3, (860, (W - 860) / 2, 540, 1.2) + Z_INSCR),
                                    (tb + 1.0, (640, 150, 540, 1.0, 0.5, 0.5)),
                                    (t1, (640, 150, 540, 1.05, 0.55, 0.5))])
    w = int(w)
    h = taille(CARTE, largeur=w, recadre=CARTE_CROP)[1]
    photo(cv, CARTE, x, y - h / 2, w, h, zoom=z, cx=cx, cy=cy, recadre=CARTE_CROP)
    carte_coupe(cv, 940, 260, "1953", apparait(t, mot("s4_02", "mille") - 0.1, 0.8))
    carte_coupe(cv, 940, 500, "1957", apparait(t, mot("s4_03", "mille") - 0.1, 0.8))
    o = apparait(t, mot("s4_04", "doublé") - 0.1, 0.8)
    poser(cv, texte("1957 : DOUBLÉ CHAMPIONNAT – COUPE DE FRANCE", "Oswald", 34, 400, OR, 4), 946, 745, o)
    credit(cv, "Carte d'époque — document d'archives", 1)


def sc_bilan(cv, t):
    y0 = 270
    o1 = apparait(t, mot("s4_05", "six") - 0.1, 0.8)
    o2 = apparait(t, mot("s4_05", "deux Coupes") - 0.1, 0.8)
    o3 = apparait(t, E["s4_05"] - 0.2, 0.8)
    for o, n, lib, y in ((o1, "6", "CHAMPIONNATS DE FRANCE", y0), (o2, "2", "COUPES DE FRANCE", y0 + 190)):
        poser(cv, texte(n, "Oswald", 170, 500, OR), 560, y + 15 * (1 - o), o, "hc")
        poser(cv, texte(lib, "Oswald", 74, 400, CREME, 6), 680, y + 62 + 15 * (1 - o), o)
    rect(cv, 500, 690, 920 * lisse((t - E["s4_05"] + 0.2) / 1.0), 2, OR, o3)
    poser(cv, texte("1949 – 1957", "PlayfairDisplay", 64, 500, CREME), W / 2, 720, o3, "hc")
    o = apparait(t, T["s4_06"], 0.8)
    poser(cv, texte("8 TROPHÉES NATIONAUX EN 9 ANS", "Oswald", 36, 400, OR, 8), W / 2, 870, o, "hc")


def sc_carte_lente(cv, t):
    t0, t1 = T["s5_05"] - 0.4, T["s5_07"]
    w, h = taille(CARTE, largeur=1000, recadre=CARTE_CROP)
    z = 1.12 - 0.12 * lisse((t - t0) / (t1 - t0))
    photo(cv, CARTE, (W - w) // 2, (H - h) // 2, w, h, zoom=z, cx=0.5, cy=0.5, recadre=CARTE_CROP)
    credit(cv, "Carte d'époque — document d'archives", 1)


def sc_annees60(cv, t):
    o = apparait(t, T["s5_07"] + 0.3, 1.0)
    poser(cv, texte("LES ANNÉES 1960", "Oswald", 34, 500, OR, 12), W / 2, 330, o, "hc")
    rect(cv, W / 2 - 50, 390, 100, 2, OR, o)
    for i, (sid, nom) in enumerate((("s5_08", "Raphaël de Barros"), ("s5_09", "Alain Gilles"))):
        o = apparait(t, T[sid] - 0.1, 0.9)
        poser(cv, texte(nom, "PlayfairDisplay", 92, 500, CREME), W / 2, 450 + i * 130 + 12 * (1 - o), o, "hc")


T_SUITE = E["s5_09"] + 1.8
FIN = T_SUITE + 7.0


def sc_suite(cv, t):
    o = apparait(t, T_SUITE + 0.4, 1.0)
    poser(cv, texte("LA SUITE", "Oswald", 46, 500, OR, 16), W / 2, 410, o, "hc")
    rect(cv, W / 2 - 60, 482, 120, 2, OR, o)
    poser(cv, texte("RAPHAËL DE BARROS ET ALAIN GILLES", "PlayfairDisplay", 66, 500, CREME, 3), W / 2, 515, apparait(t, T_SUITE + 0.9, 1.0), "hc")


def avant(sid, d=0.25):
    return T[sid] - d


SCENES = [
    (0.0, sc_naissance),
    (avant("s2_01", 0.5), sc_titre_1949),
    (avant("s2_02"), sc_equipe(avant("s2_02"), avant("s2_04"), 1.0, 1.08, (0.42, 0.5), (0.56, 0.45))),
    (avant("s2_04"), sc_buffiere(mot("s2_04", "André") - 0.2, T["s2_05"], avant("s2_04"), avant("s2_08"))),
    (avant("s2_08"), sc_equipe(avant("s2_08"), avant("s2_09", 0.4), 1.12, 1.02, (0.5, 0.42), (0.5, 0.5))),
    (avant("s2_09", 0.4), sc_1950),
    (avant("s3_01", 0.6), sc_titres),
    (avant("s3_05", 0.4), sc_origines),
    (avant("s3_08", 0.4), sc_frise_complete),
    (avant("s4_01", 0.5), sc_coupes),
    (avant("s4_05", 0.4), sc_bilan),
    (avant("s5_01", 0.6), sc_equipe(avant("s5_01", 0.6), avant("s5_03"), 1.0, 1.10, (0.5, 0.5), (0.45, 0.42))),
    (avant("s5_03"), sc_buffiere(-1, -1, avant("s5_03"), avant("s5_05"))),
    (avant("s5_05"), sc_carte_lente),
    (avant("s5_07", 0.4), sc_annees60),
    (T_SUITE, sc_suite),
]


def rendu(t):
    i = max(k for k, (s, _) in enumerate(SCENES) if s <= t) if t >= 0 else 0
    cv = FOND.copy()
    SCENES[i][1](cv, t)
    # fondu enchaîné centré sur chaque changement de scène
    if i + 1 < len(SCENES) and t >= SCENES[i + 1][0] - XF / 2:
        w = lisse((t - (SCENES[i + 1][0] - XF / 2)) / XF)
        cv2 = FOND.copy()
        SCENES[i + 1][1](cv2, t)
        cv = cv * (1 - w) + cv2 * w
    elif i > 0 and t < SCENES[i][0] + XF / 2:
        w = lisse((t - (SCENES[i][0] - XF / 2)) / XF)
        cv0 = FOND.copy()
        SCENES[i - 1][1](cv0, t)
        cv = cv0 * (1 - w) + cv * w
    cv += GRAIN[int(t * FPS) % len(GRAIN)]
    # ouverture et fermeture au noir
    cv *= lisse(t / 1.2) * (1 - lisse((t - (FIN - 1.8)) / 1.8))
    return (np.clip(cv, 0, 1) * 255 + 0.5).astype(np.uint8)


def _rendu_octets(t):
    return rendu(t).tobytes()


# ───────────────────────── audio ─────────────────────────
def mixage(duree):
    n = int(duree * SR)
    voix = np.zeros(n, np.float32)
    actif = np.zeros(n, np.float32)
    for sid in T:
        x, _ = sf.read(os.path.join(BUILD, "voix", sid + ".wav"), dtype="float32")
        rms = np.sqrt(np.mean(x ** 2)) + 1e-9
        x = x * (10 ** (-19 / 20) / rms)               # niveau homogène
        a = int(T[sid] * SR)
        b = min(n, a + len(x))
        voix[a:b] += x[:b - a]
        actif[max(0, a - int(0.35 * SR)):min(n, b + int(0.6 * SR))] = 1
    # enveloppe de la musique : discrète sous la voix, plus présente seule
    k = int(0.6 * SR)
    noyau = np.hanning(k) / np.hanning(k).sum()
    env = np.convolve(actif, noyau, mode="same")
    gain = 10 ** ((-27 + 9 * (1 - env)) / 20)
    t = np.arange(n) / SR
    gain *= np.clip(t / 2.5, 0, 1) * np.clip((duree - t) / 3.0, 0, 1)
    mus = musique.generer(duree).astype(np.float32) * gain
    mix = voix + mus
    mix *= 0.95 / max(1e-9, np.abs(mix).max())
    sf.write(os.path.join(BUILD, "piste_voix.wav"), voix / max(1e-9, np.abs(voix).max()) * 0.9, SR)
    sf.write(os.path.join(BUILD, "piste_musique.wav"), mus / max(1e-9, np.abs(mus).max()) * 0.9, SR)
    sf.write(os.path.join(BUILD, "mixage.wav"), mix, SR)
    return os.path.join(BUILD, "mixage.wav")


def main():
    args = sys.argv[1:]
    if args[:1] == ["--image"]:
        t = float(args[1])
        out = os.path.join(BUILD, f"image_{t:07.2f}.png")
        Image.fromarray(rendu(t)).save(out)
        print(out)
        return
    t0, t1 = (float(args[1]), float(args[2])) if args[:1] == ["--apercu"] else (0.0, FIN)
    print(f"durée totale : {FIN:.1f} s ({int(FIN // 60)} min {FIN % 60:04.1f} s)")
    json.dump({"debut": T, "fin": E, "fin_video": FIN}, open(os.path.join(BUILD, "timeline.json"), "w"), indent=1)
    audio = mixage(FIN)
    sortie = os.path.join(BUILD, "apercu.mp4" if t0 > 0 or t1 < FIN else "ASVEL_naissance_legende_partie1.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-ss", str(t0), "-t", str(t1 - t0), "-i", audio,
           "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-tune", "film",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", sortie]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    temps = [t0 + i / FPS for i in range(int((t1 - t0) * FPS))]
    with Pool(os.cpu_count()) as pool:
        for i, b in enumerate(pool.imap(_rendu_octets, temps, chunksize=8)):
            ff.stdin.write(b)
            if i % 250 == 0:
                print(f"  {temps[i]:6.1f} / {t1:.1f} s", file=sys.stderr)
    ff.stdin.close()
    ff.wait()
    print(sortie)


if __name__ == "__main__":
    main()
