# Teaser Reels — REAL MADRID vs LDLC ASVEL (EuroLeague, jeu. 15/10/2026, 21h00)

Format : 1080×1920 vertical, 30 FPS, 60 s, MP4 H.264 + AAC 320 kb/s, son à -14 LUFS.

## Fichiers
- `out/TEASER_REAL-MADRID_vs_LDLC-ASVEL.mp4` : version 2 (refonte complète), 60 s, H.264 à 11 Mb/s.
- `out/bande-son_musique_sfx.wav` : musique et effets mixés.
- `out/bande-son_sfx_seuls.wav` : effets seuls, pour poser un titre de la bibliothèque Instagram.
- `assets/` : les 3 photos authentiques fournies et les deux détourages (`*_cut.png`).

## Logos
- `logos/*_source.webp` : les fichiers officiels fournis.
- `logos/real-madrid.png` : l'écusson tel quel (déjà transparent).
- `logos/ldlc-asvel.png` : le logo monochrome passé en blanc pour le fond noir (version inversée). Le dessin n'est pas modifié.

## Refaire le rendu
Lancer :
   ```
   python3 audio.py out/bande-son_musique_sfx.wav out/bande-son_sfx_seuls.wav
   python3 render.py out/TEASER_brut.mp4 out/bande-son_musique_sfx.wav
   ```
   Dépendances : Python 3, Pillow, numpy, scipy, opencv-python-headless, ffmpeg.

## Final 43–60 s : les cinq joueurs ASVEL
- Photos : `assets/*_source.*`. Détourages : `assets/{joueur1,waters,mills,besson,crowder}_cut.png`.
  - Joueur 1, Mills et Crowder sont livrés déjà détourés.
  - Besson (fond blanc) est détouré avec `cutout.py`.
  - Waters (fond noir) est détouré avec `cutout_black.py`.
- Formation, de gauche à droite : Besson, joueur 1, Mills (au centre, en avant), Waters, Crowder.
- L'échelle de chaque joueur est calée sur la distance yeux–menton mesurée sur sa photo, pour que les visages aient une taille cohérente.
- Seuls le cadrage (caméra virtuelle), l'opacité et la luminosité bougent. Les corps restent fixes.

## Méthode (aucune IA générative)
- Détourage : sélection du fond blanc studio par seuillage et remplissage depuis les bords, puis « couleur vers alpha » sur le contour (`cutout.py`). Les pixels des visages, des maillots et des numéros ne sont pas modifiés.
- Mouvements : zooms de 100 à 105 % maximum, glissements, fondus, flashs, typographie. Aucun clip de match.
- Musique : composition originale synthétisée par code (`audio.py`) à 120 BPM, calée sur les repères du montage. Elle n'utilise aucun sample externe et n'a aucun ayant droit tiers.
- Polices : Anton et Oswald (licence SIL OFL).
