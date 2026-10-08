# Teaser TikTok : ASVEL – Roanne (dim. 11 octobre 2026, 19h, Astroballe)

- `teaser-asvel-roanne-tiktok.mp4` : 1080×1920, 30 i/s, 34,0 s, H.264 High + AAC 192 kb/s, −14 LUFS, crête −1,8 dBTP
- `couverture-affiche-asvel-roanne.jpg` : affiche finale avec les deux joueurs (1080×1920), utilisable comme couverture TikTok
- `couverture-lheure-de-la-revanche.jpg` : ancienne couverture, tirée d'un vrai plan (célébration de Jae Crowder)

## Version 4
- Le carton final est remplacé par une affiche (28–34 s, entièrement affichée pendant 6 s, avec la musique seule). Elle sert aussi de couverture.
- Joueur de l'ASVEL à gauche, Darius Johnson à droite, recadrés au buste. Les visages ont la même taille et les yeux sont sur la même ligne (y = 345).
- Seules les photos fournies sont utilisées. Chaque photo reçoit seulement une mise à l'échelle uniforme, sans retournement ni retouche des visages ou des maillots.
- Le détourage est nettoyé (`montage/poster.py`) : les traits blancs et le halo clair au bord de la silhouette sont retirés. Cela touche 0,65 % des pixels de Darius et 0,25 % de ceux du joueur de l'ASVEL, uniquement sur le contour.
- Textes : ASVEL – ROANNE / DIMANCHE 11 OCTOBRE · 19H / ASTROBALLE / EN DIRECT SUR LA CHAÎNE L’ÉQUIPE ET DAZN / ASVEL_NEWS. Ils occupent x 88–897 et y 935–1517, à distance du rail droit et de la légende TikTok.

## Version 3
- Compte à rebours rétro 5 → 1 en ouverture (1 s par chiffre, sans l'intro rouge ni le « 0 »), recadré au centre en 9:16 plein cadre, sans bande ni flou.
- Les 5 vidéos sont présentes, chaque panier est montré jusqu'au filet, puis environ 0,5 s avant la coupe. Les coupes tombent sur la grille musicale.
- Le son d'origine de toutes les vidéos est coupé, compte à rebours compris : on n'entend que la musique.
- Carton final agrandi, avec les diffuseurs, entièrement affiché de 28,8 s à 34 s.

## Déroulé
| Temps | Partie | Image | Panier → coupe |
|---|---|---|---|
| 0–5 s | Décompte | 5 · 4 · 3 · 2 · 1 (film rétro fourni), musique en montée | – |
| 5–7,5 s | Accroche | ROANNE 73 — 71 ASVEL · 19 SEPTEMBRE · SUPERCOUPE (impact) | – |
| 7,5–10 s | Rappel | DEUX DUELS. / DEUX DÉFAITES. / ON N’A PAS OUBLIÉ. | – |
| 10–13,5 s | Attente | Find the shooter : Patty Mills prépare (0,8×), tire, swish | 13,0 → 13,5 s |
| 13,5–16 s | Montée | Tremont Waters : pénétration, tir, ballon dans le filet | 15,55 → 16,0 s |
| 16–19,5 s | Montée | Mills → Crowder : passe, tir à 3 pts, ballon dans le filet | 19,05 → 19,5 s |
| 19,5–21 s | Montée | Yves Pons : pénétration et dunk | 20,55 → 21,0 s |
| 21–25 s | Sommet | Touchdown : passe longue, Nate Sestina finit (plan continu), célébration | 23,5 s |
| 25–28 s | Message | Crowder rugit : CETTE FOIS, / CHEZ NOUS. | – |
| 28–34 s | Rendez-vous | Affiche avec les deux joueurs : ASVEL – ROANNE / DIMANCHE 11 OCTOBRE · 19H / ASTROBALLE / EN DIRECT SUR LA CHAÎNE L’ÉQUIPE ET DAZN / ASVEL_NEWS | – |

## Musique
Composition instrumentale originale, synthétisée en code (`montage/music.py`, sans IA ni échantillon
tiers). C'est l'unique piste audio du teaser. Les accents musicaux suivent le montage : les coupes
ne sont jamais calées sur la musique au détriment d'un panier.

## Points de vigilance
- Aucune incrustation d'origine, aucun logo DAZN, aucun floutage. Le bandeau de score du clip Tremont est sorti du cadre par recadrage.
- Aucun texte n'associe les highlights au duel contre Roanne ni à l'Astroballe.
- Le plan de Sestina (17–20 s) montre la signalétique de la LDLC Arena, sans texte de lieu. Le plan « CHEZ NOUS » (Crowder, LDLC Arena) est recadré pour exclure tout marquage du lieu.
- Yves Pons : le recadrage exclut la trace de logo effacé en haut à droite de la source.
- Le plan de Crowder au panier démarre après l'affichage de la feuille de match sur l'écran géant, recadré pour l'exclure.
