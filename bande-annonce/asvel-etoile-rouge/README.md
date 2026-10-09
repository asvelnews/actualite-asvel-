# Bande-annonce ASVEL – Étoile Rouge de Belgrade (EuroLeague, mardi 13 octobre, 20h00, Astroballe)

| Fichier | Usage |
|---|---|
| `ASVEL_NEWS_ASVEL-EtoileRouge_13-octobre.mp4` | publication avant le jour du match (MARDI 13 OCTOBRE • 20H00) |
| `ASVEL_NEWS_ASVEL-EtoileRouge_AUJOURDHUI.mp4` | publication le 13 octobre uniquement (AUJOURD’HUI • 20H00) |
| `illustration-asvel-etoile-rouge.jpg` | image d’illustration 1600×900 (article, partage) (`montage/illustration.py`) |
| `couverture-asvel-etoile-rouge.jpg` | couverture verticale 1080×1920 (TikTok) : affiche finale |
| `ASVEL_NEWS_Teaser_RDV-lundi-12-octobre.mp4` | teaser 18 s : BANDE-ANNONCE COMPLÈTE / RENDEZ-VOUS LUNDI 12 OCTOBRE (`montage/teaser.py`) |

1080×1920, 30 i/s, 106,45 s, H.264 High + AAC 192 kb/s 48 kHz, ≈ 29,8 Mo, −14 LUFS, crête −1 dBFS.

## Langage motion design
Typo cinétique (chaque lettre surgit derrière un masque), échos en contour à chaque impact, blocs et panneaux obliques qui glissent,
rangées de mots en contour qui défilent en fond, trames diagonales animées, reflet lumineux qui balaie les joueurs,
transitions en barres obliques rouge/blanc (10 s, 14 s, 18 s), cadres de visée qui se resserrent sur le chronomètre à chaque seconde,
coups de zoom sur les phrases. L'affiche finale se construit puis reste fixe et lisible.

## Déroulé (1 min 46)
| Temps | Scène |
|---|---|
| 0–5 s | Panier réel (N&B), chiffres rouges 5·4·3·2·1 dans le boîtier du chronomètre, cadres de visée |
| 5,0–6 s | 0 : buzzer, impact, fissure, bris de verre |
| 6–10 s | FACE-À-FACE : ASVEL 5 VICTOIRES / ÉTOILE ROUGE 9 VICTOIRES |
| 10–14 s | Patty Mills (ASVEL) |
| 14–18 s | Chima Moneke (ÉTOILE ROUGE DE BELGRADE) |
| 18–24 s | DEUX ÉQUIPES. / UN MATCH. / UN SEUL REPARTIRA AVEC LA VICTOIRE. |
| 24–25 s | Les deux portraits face à face, extinction |
| 25–26,5 s | ARE / YOU / READY? dans le noir, quasi-silence |
| 26,5–31 s | Entrée de basse : carte « D’UN CÔTÉ / UN CHAMPION NBA » : Patty Mills, 1 020 matchs en NBA, palmarès |
| 31–61,6 s | Les 9 actions de Patty Mills (le tir de Jae Crowder de la vidéo de Cholet, 10,23–14,14 s, est retiré) |
| 61,6–66,1 s | Carte « DE L’AUTRE CÔTÉ / UN CHAMPION DE FRANCE » : Chima Moneke, MVP Basketball Champions League 2022, palmarès |
| 66,1–100,31 s | Les 8 actions de Chima Moneke |
| 100,31–106,45 s | Affiche du match sur un temps fort (infos à 101,31 s, stable ≥ 4,5 s), dernier impact, extinction |

### Clips utilisés (vidéos fournies, son d'origine coupé)
Toutes les actions des 4 vidéos, dans leur durée d’origine (de coupe à coupe), panneau 1080×700 recadré ×1,46 sur l’action.
À chaque changement de clip : balayage en barres obliques rouge/blanc (0,32 s, sens alterné), flash et coup de zoom.
Ordre et plages : `MILLS_CLIPS` et `MONEKE_CLIPS` dans `montage/render.py`. Seule exception : la dernière action de Moneke
(Olympiacos, 8,63–14,97 s) démarre à 10,11 s pour que l'affiche tombe sur le temps fort de la musique.
Les clips ne sont pas versionnés : `CLIPS_DIR=<dossier> python3 montage/render.py ...`

## Son
Musique fournie (« MONTAGEM ALLUVIA – Slowed + Reverb ») à partir de 3,10 s : l’entrée de basse (29,6 s) lance les clips à 26,5 s ; le creux du morceau (88,47–96,44 s) est sauté sur un temps, l’affiche tombe sur l’impact de 111,38 s.
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
