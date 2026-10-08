# Bande-annonce ASVEL – Étoile Rouge de Belgrade (EuroLeague, mardi 13 octobre, 20h00, Astroballe)

| Fichier | Usage |
|---|---|
| `ASVEL_NEWS_ASVEL-EtoileRouge_13-octobre.mp4` | publication avant le jour du match (MARDI 13 OCTOBRE • 20H00) |
| `ASVEL_NEWS_ASVEL-EtoileRouge_AUJOURDHUI.mp4` | publication le 13 octobre uniquement (AUJOURD’HUI • 20H00) |

1080×1920, 30 i/s, 35,0 s, H.264 High + AAC 192 kb/s 48 kHz, ≈ 14,4 Mo, −15 LUFS, crête −1,2 dBFS.

## Langage motion design
Typo cinétique (chaque lettre surgit derrière un masque), échos en contour à chaque impact, blocs et panneaux obliques qui glissent,
rangées de mots en contour qui défilent en fond, trames diagonales animées, reflet lumineux qui balaie les joueurs,
transitions en barres obliques rouge/blanc (10 s, 14 s, 18 s), cadres de visée qui se resserrent sur le chronomètre à chaque seconde,
coups de zoom sur les phrases. L'affiche finale se construit puis reste fixe et lisible.

## Déroulé
| Temps | Scène |
|---|---|
| 0–5 s | Panier réel (N&B), chiffres rouges 7 segments dans le boîtier du chronomètre : 5·4·3·2·1, rapprochement lent |
| 5,0 s | 0 : buzzer, impact, fissure de la vitre depuis le point d'impact |
| 5,55–5,95 s | Bris de verre (éclats de Voronoï, flash bref), puis noir |
| 6–10 s | FACE-À-FACE : ASVEL 5 VICTOIRES (6,6 s, blanc) / ÉTOILE ROUGE 9 VICTOIRES (7,6 s, rouge), un impact grave par chiffre |
| 10–14 s | Patty Mills, masque latéral depuis la gauche, ASVEL en grand derrière, plan serré puis recul |
| 14–18 s | Chima Moneke, masque depuis la droite, lumière rouge, ÉTOILE ROUGE / DE BELGRADE |
| 18–24 s | DEUX ÉQUIPES. / UN MATCH. / UN SEUL REPARTIRA AVEC LA VICTOIRE. : coupes de plus en plus rapprochées, calées sur le tempo, lignes blanche et rouge qui se rejoignent |
| 24–25,0 s | Les deux portraits face à face, ralenti, extinction |
| 25,0–26,5 s | Écran noir : ARE / YOU / READY? (un mot par temps, coup sourd discret), puis quasi-silence de 25,95 à 26,45 s |
| 26,5 s | Révélation sur l'entrée de basse de la musique : les joueurs arrivent de côtés opposés, ASVEL VS ÉTOILE ROUGE DE BELGRADE |
| 28–28,8 s | Infos du match ; affiche stable de 28,8 à 34,45 s, puis extinction courte |

## Son
Musique fournie (« MONTAGEM ALLUVIA – Slowed + Reverb ») de 3,10 s à 38,1 s : l'entrée de basse (29,6 s) tombe sur la révélation.
Automation volume + passe-bas : quasi-silence filtré au compteur, tension filtrée sur l'historique, montée sur les portraits,
crescendo sur les phrases, coupure puis ~0,6 s quasi silencieuse, reprise pleine sur l'affiche, extinction.
Effets synthétisés (`montage/audio.py`) : bourdonnement, bips, basse pulsée, buzzer, impacts, fissure, verre, deux souffles de transition.
Aucune voix off, aucun son de match.

## Sources
- `sources/patty-mills-asvel-original.png` : photo fournie de Patty Mills en maillot LDLC ASVEL n°8 (déjà détourée, 819×1024).
- `sources/patty-mills-detoure.png` : la même, simplement recadrée au-dessus des genoux.
- `sources/chima-moneke-detoure.png` : photo fournie de Chima Moneke (déjà détourée, 352×469).
- Les deux visages ont une résolution proche (≈ 60 et 55 px de large) : même cadrage et même taille de visage pour les deux joueurs,
  agrandissement Lanczos uniforme (aucune retouche, aucune reconstruction).
- `sources/panier-chronometre.png` : image réelle du panier issue du projet (branche du teaser précédent) ; le ballon en vol a été retiré
  par retouche (inpainting) et l'affichage d'origine du chronomètre a été éteint pour y intégrer le compte à rebours.
- Polices : Anton, Barlow Condensed (Google Fonts, licence OFL).

## Refaire le montage
```
python3 montage/prep.py <dossier_sortie> <racine_du_depot>     # détourages
ffmpeg -i musique.mp4 -vn -ac 2 -ar 48000 music.wav
python3 montage/audio.py music.wav mix.wav
python3 montage/render.py date v_date.mp4       # ou : today
ffmpeg -i v_date.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -movflags +faststart sortie.mp4
```
