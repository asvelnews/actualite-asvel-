# ASVEL : la naissance d'une légende — partie 1 (1948-1957)

Montage du premier épisode du documentaire (YouTube 16:9, 1920 × 1080, 25 i/s).
Il s'arrête sur l'écran « LA SUITE — Raphaël de Barros et Alain Gilles ».

## Contenu

| Fichier | Rôle |
|---|---|
| `narration.py` | Texte de la narration, découpé en phrases, avec les pauses |
| `voix.py` | Prépare la voix : enregistrements réels ou voix de synthèse provisoire |
| `musique.py` | Musique instrumentale discrète, générée (libre de droits) |
| `montage.py` | Timeline calée sur la voix, rendu image, mixage, encodage |
| `images/` | Documents fournis (voir correspondance ci-dessous) |
| `fonts/` | Playfair Display, Oswald, Source Sans 3 (licence OFL) |

Correspondance des images :

- `1948.jpg` : photo dont la légende indique « Première équipe championne de France en 1949 ». Elle est présentée avec l'année 1949, jamais 1948, et sa légende reste visible.
- `1949.jpg` : photo collective, utilisée pour illustrer les premiers titres, sans date ni identification des joueurs.
- `andre-buffiere.jpg` : portrait d'André Buffière.
- `carte-annees-1950.png` : correspond à « Capture d'écran 2026-10-12 143049.png », la carte historique.

## Plan de montage

| Séquence | Images |
|---|---|
| 1. Naissance | Fond sobre. Les deux associations apparaissent, se rejoignent, puis le nom complet s'affiche avec ses initiales en or. Le sigle ASVEL se forme ensuite, puis on voit « 21 DÉCEMBRE 1948 » et un bandeau texte pour Pierre Millet (sans photo). |
| 2. Premiers champions | `1948.jpg` avec sa légende, puis `1949.jpg` (léger mouvement). Composition avec le portrait de Buffière à gauche et « Joueur, entraîneur, recruteur » à droite. Retour sur `1949.jpg`, puis les cartes 1949 et 1950. |
| 3. Les titres s'accumulent | Carte historique entière, puis légers rapprochements sur le groupe du haut, celui du bas et les inscriptions. Une frise affiche chaque année au moment où elle est prononcée. Rappel des origines avec `1948.jpg` (daté 1949), puis la frise complète avec 4 s de musique seule. |
| 4. Coupes de France | La carte se rapproche des inscriptions, puis glisse à gauche. Cartes « 1953 — COUPE DE FRANCE » et « 1957 — COUPE DE FRANCE », mention du doublé, puis récapitulatif 6 + 2, 1949–1957. |
| 5. Héritage | `1949.jpg`, portrait de Buffière et carte, puis « Les années 1960 », les deux noms et l'écran de transition « LA SUITE ». |

Aucune image de Barcelone 1996, de Rome 1997 ou de l'Astroballe n'est utilisée.

## Remplacer la voix de synthèse par la vraie narration

La version actuelle utilise une **voix de synthèse provisoire** pour caler le
montage. Pour poser la vraie voix :

1. Enregistrer chaque phrase dans `voix/<id>.wav`. Les identifiants (`s1_01`, `s1_02`, etc.) et leur texte sont dans `narration.py`. Un fichier manquant garde la voix de synthèse.
2. Lancer :

   ```bash
   pip install numpy pillow soundfile kokoro-onnx   # kokoro uniquement pour la synthèse
   python3 voix.py
   python3 montage.py
   ```

Les silences en début et en fin de chaque prise sont retirés automatiquement, et
le niveau de chaque phrase est harmonisé. **Toute la timeline se recale sur la
durée réelle des prises** : apparition des années, cartes, fondus, musique et
durée totale. Aucune image n'est étirée pour atteindre une durée fixe.

Pour la voix de synthèse, le modèle Kokoro (`kokoro-v1.0.onnx` et `voices-v1.0.bin`,
publiés sur GitHub par thewh1teagle/kokoro-onnx) doit se trouver dans `build/kokoro/`
ou à l'emplacement indiqué par `KOKORO_DIR`.

Outils de vérification :

- `python3 montage.py --image 37.5` : exporte l'image à 37,5 s.
- `python3 montage.py --apercu 120 150` : rend un extrait.

Le rendu produit `build/ASVEL_naissance_legende_partie1.mp4`, ainsi que les pistes
séparées `build/piste_voix.wav` et `build/piste_musique.wav`.

## Crédits

Aucune source ni aucun photographe n'ont été fournis pour les documents. Les
mentions à l'écran restent donc génériques (« Document d'archives », « Carte
d'époque »), et la légende d'origine de `1948.jpg` est conservée. Il faudra les
compléter dès que les crédits seront connus.
