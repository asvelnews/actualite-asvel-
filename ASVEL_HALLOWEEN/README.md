# ASVEL_HALLOWEEN — Trailer Halloween ASVEL_NEWS

Trailer vertical de 60 secondes pour **LDLC ASVEL vs Baskonia Vitoria-Gasteiz** (Turkish Airlines EuroLeague, LDLC Arena, Décines-Charpieu, 20H00).
Projet Remotion modifiable, 1080 × 1920, **60 FPS natifs**, H.264 + AAC 48 kHz stéréo.

## Livrables (dossier `renders/`)

| Fichier | Contenu |
|---|---|
| `ASVEL_HALLOWEEN_60FPS.mp4` | Version finale verticale 1080×1920, 60 FPS, ~20 Mb/s, AAC 320 kb/s 48 kHz stéréo |
| `ASVEL_HALLOWEEN_60FPS_SANS_MUSIQUE.mp4` | Même image, effets sonores seuls |
| `ASVEL_HALLOWEEN_CARRE_1080.mp4` | Version carrée 1080×1080 (vertical centré sur fond flouté, aucun texte coupé) |
| `ASVEL_HALLOWEEN_4K_60FPS.mp4` | 2160×3840 (si rendue — voir « 4K » plus bas) |
| `ASVEL_HALLOWEEN_THUMBNAIL.png` | Miniature 1080×1920 |
| `TEST_VFX_ARENA_5s_60FPS.mp4` | Test VFX de la phase 3 |
| `verification.json` | Mesures ffprobe + loudness de chaque export |
| `../RAPPORT_RENDU.md` | Rapport de rendu et de contrôle qualité |

Les MP4 ne sont pas versionnés dans Git (plus de 100 Mo) : ils sont livrés à part.

## Prérequis (Windows ou Linux)

- Node.js 18+ (testé avec 22)
- Python 3.10+ avec `numpy`, `scipy`, `pillow` : `pip install numpy scipy pillow`
- FFmpeg + ffprobe dans le PATH
- Blender n'est **pas** nécessaire.

```bash
npm install
npm run studio            # prévisualisation interactive (http://localhost:3000)
```

Sur Windows, supprimez rien : la ligne `setBrowserExecutable` de `remotion.config.ts` ne s'applique que sous Linux ; Remotion télécharge son propre Chromium.

## Refaire le rendu complet

```bash
npm run prepare-assets    # (seulement si vous changez les photos) masques, calques joueurs, polices
npm run audio             # synthèse de la bande-son -> public/audio/*.wav
npm run render:video      # vidéo muette 1080x1920 60 FPS -> renders/_video.mp4
python tools_export.py renders/_video.mp4            # mux audio + sans musique + carré + vérifs
npm run thumbnail
# 4K optionnelle (≈4x plus long) :
npm run render:4k && python tools_export.py renders/_video.mp4 renders/_video_4k.mp4
```

## Structure

```
ASVEL_HALLOWEEN/
  assets/            sources ORIGINALES conservées (arena, players, posters, logos, horror)
    smoke/ fire/ particles/   vides : la fumée, le feu et les particules sont procéduraux (voir VFX)
  public/            ressources préparées servies à Remotion (masques, calques, polices, audio)
  src/
    timeline.json    LA timeline : scènes + repères (cues). Partagée par l'image ET le son.
    Root.tsx         compositions : Trailer, S1..S6 (scènes isolées), VfxTest
    compositions/    Trailer (montage + transitions globales), VfxTest
    scenes/          S1Arena, S2Horror, S3Patty, S4Tadas, S5FaceOff, S6GameDay
    components/      PlayerRig (joueur + calques VFX), FireBall, TextFX, Fonts
    effects/         cpuShaders (fumée/feu/ciel/ballon 3D), Smoke, Particles, Lightning,
                     Claws, Bats, Moon, Overlays (grain, vignette, toiles d'araignée)
  tools_*.py         préparation des ressources, synthèse audio, exports
  previews/          images de contrôle générées pendant la production
  renders/           exports
```

## Modifier le trailer

- **Décaler un moment** : changez la frame dans `src/timeline.json` (60 frames = 1 s), puis relancez `npm run audio` : les sons suivent automatiquement.
- **Textes** : dans chaque fichier `src/scenes/S*.tsx`.
- **Remplacer une photo** : remplacez le fichier dans `assets/…`, puis `npm run prepare-assets`. Pour un joueur, mettez à jour la position des yeux dans `src/components/PlayerRig.tsx` (`eyes`, en pixels de l'image).
- **Couleurs** : palette dans `src/components/Fonts.tsx` (`C`) : noir #080608, rouge sang #D71920, orange #FF641B, blanc #F4F1EC, or #D6A85A.

## VFX : ce qui est réellement fait

Aucune vidéo VFX externe n'a été téléchargée (droits non vérifiables). Tous les effets sont **générés et animés image par image** :

- **Fumée volumétrique** (`effects/cpuShaders.ts → smokePx`) : bruit simplex fractal à double déformation de domaine, dérive avec bouffées (vitesse variable), turbulence, éclairage directionnel par différence de densité, zones de densité (sol, bande, colonne) et ouverture animée (révélations). 30+ couches indépendantes avec graines, échelles, vitesses et profondeurs différentes (fumée noire, rouge, orange, brouillard rampant, volutes devant la caméra, explosion rouge, colonne entre les joueurs, fumée de fin).
- **Flammes** (`firePx`) : bruit étiré qui défile, hauteur modulée, rampe de couleur corps noir.
- **Ciel** (`skyPx`) : transition nuit bleue → rouge sang, deux couches de nuages en parallaxe, illumination par les éclairs.
- **Ballon 3D** (`ballPx`) : vraie sphère calculée par lancer de rayons (normales, rotation 3D, coutures, grain du cuir, spéculaire, liseré, veines de lave).
- **Éclairs** : ramifiés par déplacement du point milieu, double flash + persistance.
- **Particules** sans état (braises, étincelles, explosions radiales, cendres, pluie), chauves-souris animées, griffures effilées, toiles d'araignée balancées, grain film, vignette.

Pourquoi sur CPU et pas en WebGL : dans l'environnement de rendu (sans GPU), WebGL passe par SwiftShader et toute la composition devenait ~6x plus lente. Le portage CPU donne exactement le même rendu, déterministe, et fonctionne partout.

## Son

Bande-son **entièrement synthétisée** (`tools_audio.py`, numpy/scipy) : aucun échantillon ni musique externe, donc aucune question de licence. Battements de cœur, vent, grondements, pas, grincements, respiration, tonnerre, griffures métalliques, crépitement du feu, souffles, cris lointains non reconnaissables, impacts « braam », taikos, cordes, chœur, boîte à musique désaccordée (motif original), montée finale. Mixage : automation de tension acte par acte, compression douce, limiteur, crête -1 dBTP.

## Limites connues (en toute transparence)

- **Tadas Sedekerskis** : la photo fournie fait 352×469 px. Elle est agrandie ×2 (Lanczos) puis affichée ~×3,2 : l'image est plus douce que celle de Patty Mills. L'agrandissement ne crée aucun détail réel. Une photo HD améliorerait nettement les scènes 4 et 5.
- **Personnages d'horreur** : ce sont des extraits de l'affiche fournie (pas de ressources individuelles). Ils ne sont pas détourés : ils apparaissent dans des fenêtres à bords fondus dans l'obscurité, agrandis ×3 à partir de ~200 px. Aucun personnage n'a été fabriqué.
- **4K** : rendu natif des textes, vecteurs et effets en 2160×3840, mais les photos restent agrandies.
- **Distorsion de chaleur** : non réalisée (coût de rendu trop élevé en composition logicielle).
- **Fumée** : simulation procédurale 2D animée (pas une simulation fluide 3D type Blender).
- **Musique** : synthèse « orchestrale », pas un enregistrement d'orchestre. Pour un rendu encore plus riche, remplacer `public/audio/ASVEL_HALLOWEEN_MUSIC` par une musique sous licence et remixer.

## Polices

Anton, Creepster, Oswald — SIL Open Font License (`public/fonts/LICENSE-OFL.txt`), intégrées en base64 (`npm run prepare-assets` les régénère).
