# ASVEL TOUR – Reel Instagram (Remotion)

Vidéo verticale 1080 × 1920, **60 i/s**, **≈ 99 s**, MP4 H.264 (yuv420p, BT.709,
faststart), directement publiable sur Instagram : `export/asvel-tour.mp4`.

> **Simulation illustrative.** Les vols, trajets, consommations et coûts sont
> des estimations correspondant à un vol comparable. Ce ne sont ni des trajets
> réellement effectués par l'équipe, ni des dépenses réelles de l'ASVEL.
> Mention permanente à l'écran : « Simulation de déplacements – données estimatives – non officielle ».

## Déroulé

1. **Intro** – ASVEL TOUR · 4 VICTOIRES CONSÉCUTIVES · @ASVEL_NEWS
2. **Cholet** : base → LYS (car) · vol LYS → **Cholet-Le Pontreau** · car → La Meilleraie ·
   **Cholet 85-97 ASVEL** · car → aérodrome · vol retour → LYS · car → base
3. **Gravelines** : même schéma via **Calais-Dunkerque** et Sportica · **Gravelines 65-70 ASVEL**
4. **Roanne** : car base → Astroballe (sans avion) · **ASVEL 96-77 Roanne** · retour à la base
5. **Limoges** : via **Limoges-Bellegarde** et Beaublanc · **Limoges 94-97 ASVEL**
6. **Nancy** : car base → Astroballe · PROCHAIN MATCH ASVEL vs NANCY · OBJECTIF 5/5
7. **Bilan** – France entière, statistiques, puis tableau des 6 vols

CHOLET, GRAVELINES et LIMOGES apparaissent en grandes lettres sur la carte ;
les aérodromes en plus petit (code + nom). Vert = aller, blanc = retour,
jaune = prochain match. Les quatre victoires restent affichées en permanence
(bandeau du haut + marqueurs verts).

## Commandes

```bash
npm install
npm run studio        # aperçu interactif
npm run export        # rendu + conversion Instagram → export/asvel-tour.mp4
npm run fetch:routes  # régénère les itinéraires routiers (accès réseau OSRM requis)
npm run build:map     # régénère le fond de carte
```

Sans téléchargement de Chrome possible : `REMOTION_BROWSER=/chemin/chrome-headless-shell npm run export`.

### Musique

La vidéo n'embarque **aucune piste audio** (aucune n'existait dans le projet).
Pour en ajouter une : déposer un fichier sous licence dans `public/` (par ex.
`public/musique.mp3`), renseigner `MUSIC_FILE = 'musique.mp3'` dans
`src/data/tour.ts`, puis `npm run export` (fondu d'entrée et de sortie
automatique, musique sur toute la durée). Autre option : ajouter un son
directement dans Instagram lors de la publication (droits gérés par Instagram).

## Choix des aérodromes (le plus proche compatible)

Règle : l'aérodrome adapté le plus proche de la salle, à condition que l'appareil
retenu puisse y opérer.

| Match | Aérodrome retenu | Piste | Route vers la salle |
|---|---|---|---|
| Cholet | Cholet-Le Pontreau (CET / LFOU) | 03/21, 1 380 m × 30 m asphalte, seuil 03 décalé de 180 m (LDA ≈ 1 200 m) | 4,8 km ≈ 10 min |
| Gravelines | Calais-Dunkerque (CQF / LFAC) | 06/24, 1 535 m × 45 m asphalte | 21,9 km ≈ 25 min |
| Limoges | Limoges-Bellegarde (LIG / LFBL) | 03/21, 2 500 m × 45 m | 10,1 km ≈ 15 min |
| Départ / retour | Lyon-Saint-Exupéry (LYS / LFLL) | 17R/35L, 4 000 m × 45 m | 28,2 km ≈ 30 min (base) |

Sources : OpenStreetMap (aeroway=runway, longueurs/largeurs/seuils), OurAirports,
eAIP France (piste LFOU 03/21 de 1 380 m, trafic IFR/VFR, AFIS ; LFAC 06/24 de
1 535 m, PPR 48 h hors horaires pour les vols commerciaux, assistance obligatoire
au-delà de 3 t, Jet A-1 disponible).

**À confirmer pour une opération réelle** : résistance de chaussée (PCN) de
LFOU, horaires AFIS / PPR, assistance au sol et avitaillement à Cholet.

### Appareil retenu : ATR 42-600

L'Embraer ERJ 145 de la version précédente demande **2 270 m** au décollage à la
masse maximale : incompatible avec Cholet-Le Pontreau. Il est remplacé par un
**ATR 42-600** (48 sièges, suffisant pour l'effectif et le staff) :

| Donnée constructeur (fiche ATR 2022) | Valeur | Piste la plus contraignante |
|---|---|---|
| Distance de décollage (MTOW, ISA, niveau mer) | 1 107 m | LFOU : 1 380 m ✔ |
| Distance d'atterrissage (MLW, EASA) | 966 m | LFOU 03 : LDA ≈ 1 200 m ✔ |
| Largeur de piste | 30 m mini | LFOU : 30 m ✔ |
| Croisière maxi FL240 | 535 km/h | — |
| Consommation de croisière | 620 kg/h | — |

## Les 6 vols (estimations, vol comparable)

| Vol | Distance | Vent | Durée en vol | Kérosène | Carburant (inclus) | Affrètement | Prix moyen |
|---|---|---|---|---|---|---|---|
| ASVEL 101 LYS → CET | 482 km | −37 km/h | 1 h 15 | 1 052 L | 1 300 – 1 900 € | 11 600 – 17 300 € | ≈ 14 500 € |
| ASVEL 102 CET → LYS | 482 km | +38 km/h | 1 h 06 | 923 L | 1 100 – 1 700 € | 11 400 – 17 300 € | ≈ 14 400 € |
| ASVEL 103 LYS → CQF | 627 km | −14 km/h | 1 h 30 | 1 256 L | 1 500 – 2 300 € | 12 800 – 19 100 € | ≈ 16 000 € |
| ASVEL 104 CQF → LYS | 627 km | +16 km/h | 1 h 26 | 1 185 L | 1 400 – 2 100 € | 13 000 – 19 500 € | ≈ 16 300 € |
| ASVEL 105 LYS → LIG | 304 km | −40 km/h | 0 h 52 | 742 L | 900 – 1 300 € | 9 800 – 14 800 € | ≈ 12 300 € |
| ASVEL 106 LIG → LYS | 304 km | +40 km/h | 0 h 46 | 655 L | 800 – 1 200 € | 10 100 – 15 400 € | ≈ 12 800 € |

**Totaux (3 allers + 3 retours)** : 2 823 km · 6 h 55 de vol · 5 813 L ·
affrètements 68 700 – 103 400 € (prix moyen cumulé ≈ 86 300 €).
**Autocar** : 278,7 km au total (15 transferts).

Hypothèses (`src/lib/aviation.ts`) :

- Distance : orthodromie (haversine) entre points de référence d'aérodrome ;
  distance parcourue = × 1,05. Temps de vol = distance / vitesse sol + 12 min
  (montée, descente, approche). Croisière 520 km/h vraie. Vent moyen d'altitude
  40 km/h d'ouest : les retours vers Lyon sont plus courts.
- Roulage : 12 min au départ de LYS, 6 min à LIG, 4 min sur les petits terrains.
- Consommation : 650 kg/h en vol, 2 kg/min au roulage, densité 0,80 kg/L.
- Jet A-1 : 1,20 – 1,80 €/L HT (tarifs publics Air BP 2026 entre 1,60 et 1,92 €/L HT).
- Affrètement, **carburant inclus (jamais ajouté une seconde fois)** :
  4 800 – 7 000 € par heure bloc (coût d'exploitation calculé ≈ 4 400 – 5 200 €/h
  + marge opérateur ; les tarifs courtiers grand public, 17 000 – 20 000 $/h, ne
  sont pas retenus), minimum 1 h facturée par vol, + 0,75 h de repositionnement
  par vol, + 800 – 1 600 € de redevances et d'assistance par vol, + 900 – 1 500 €
  d'immobilisation (attente du match, équipage) sur le retour.
- Prix moyen = milieu de la fourchette d'affrètement.

## Lieux (OpenStreetMap, octobre 2026)

| Lieu | Coordonnées (lat, lon) | Référence OSM |
|---|---|---|
| La Meilleraie, Cholet | 47.0577, -0.8962 | way 69972018 |
| Sportica, Gravelines | 50.99852, 2.12286 | relation 16890974 |
| Astroballe, Villeurbanne | 45.76642, 4.90736 | way 85200814 |
| Palais des sports de Beaublanc, Limoges | 45.84752, 1.24339 | way 70372530 |
| Base lyonnaise (Tony Parker Adéquat Academy, Gerland) | 45.72529, 4.82712 | way 527494526 |
| Aérogare Cholet-Le Pontreau | 47.08061, -0.87994 | way 70208481 |
| Aérogare Calais-Dunkerque (Louis-Blériot) | 50.9581, 1.95526 | way 220978419 |

Roanne et Nancy sont reçus à l'Astroballe : aucun trajet vers ces villes.
La base lyonnaise est un choix de scénario, modifiable dans `PLACES.BASE`.

Itinéraires routiers : OSRM (données © contributeurs OpenStreetMap, ODbL) ;
durée autocar = durée OSRM (voiture) × 1,15.

## Réutiliser pour les prochains matchs

Tout est piloté par `src/data/tour.ts` : `PLACES`, `AIRPORTS` (piste, seuils),
`GAMES` (adversaire, salle, aérodrome ou `null` à domicile, score ou `null`,
positions de l'encart et du nom de ville). Puis `npm run fetch:routes` et
`npm run export`.

## Carte et visuels

- Départements IGN ADMIN EXPRESS (Licence ouverte, via gregoiredavid/france-geojson),
  pays voisins Natural Earth 1:50m, projection Lambert-93.
- ATR 42-600 vectoriel (vue de dessus : aile haute, deux turbopropulseurs avec
  hélices six pales animées, empennage en T, train sorti au sol et en approche).
  Autocar vectoriel de profil (vitres, roues animées, phares, feux de freinage).
  Pistes à leur longueur et orientation réelles (largeur exagérée pour la lisibilité).
- Aucune image, aucune photo, aucun emoji, aucun visuel généré : uniquement SVG,
  texte et animation 2D (polices Barlow / Barlow Condensed, OFL).
