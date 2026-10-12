# Teaser Reels — REAL MADRID vs LDLC ASVEL (EuroLeague, jeu. 15/10/2026, 21h00)

Format : 1080×1920 vertical, 30 FPS, 50 s, MP4 H.264 + AAC 320 kb/s, son à -14 LUFS.

## Fichiers
- `out/TEASER_MAQUETTE_sans-logos.mp4` : version maquette. Les logos sont remplacés par des cadres « LOGO À FOURNIR ».
- `out/bande-son_musique_sfx.wav` : musique et effets mixés.
- `out/bande-son_sfx_seuls.wav` : effets seuls, pour poser un titre de la bibliothèque Instagram.
- `assets/` : les 3 photos authentiques fournies et les deux détourages (`*_cut.png`).

## Version finale avec les logos
1. Déposer les logos officiels en PNG transparent : `logos/real-madrid.png` et `logos/ldlc-asvel.png`.
2. Lancer :
   ```
   python3 audio.py out/bande-son_musique_sfx.wav out/bande-son_sfx_seuls.wav
   python3 render.py out/TEASER_REAL-MADRID_ASVEL.mp4 out/bande-son_musique_sfx.wav
   ```
   Dépendances : Python 3, Pillow, numpy, scipy, opencv-python-headless, ffmpeg.

## Méthode (aucune IA générative)
- Détourage : sélection du fond blanc studio par seuillage et remplissage depuis les bords, puis « couleur vers alpha » sur le contour (`cutout.py`). Les pixels des visages, des maillots et des numéros ne sont pas modifiés.
- Mouvements : zooms de 100 à 105 % maximum, glissements, fondus, flashs, typographie. Aucun clip de match.
- Musique : composition originale synthétisée par code (`audio.py`) à 120 BPM, calée sur les repères du montage. Elle n'utilise aucun sample externe et n'a aucun ayant droit tiers.
- Polices : Anton et Oswald (licence SIL OFL).
