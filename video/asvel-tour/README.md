# ASVEL TOUR – Reel Instagram (Remotion)

Vidéo verticale 1080 × 1920, **60 i/s**, **97 s**, MP4 H.264 (yuv420p, BT.709,
faststart), directement publiable sur Instagram : `export/asvel-tour.mp4`.

> Simulation de déplacements – données estimatives – non officielle.
> Les vols, coûts et consommations sont des estimations ; ils ne représentent
> pas les dépenses réelles de l'ASVEL.

## Déroulé

1. **Intro** – ASVEL TOUR · 4 VICTOIRES CONSÉCUTIVES · @ASVEL_NEWS
2. **Étape 1 – Cholet** : base → LYS (autocar) · vol LYS → NTE · NTE → La Meilleraie (autocar) ·
   **victoire 85-97** · retour autocar → NTE · vol NTE → LYS · LYS → base · « DE RETOUR À LA BASE »
3. **Étape 2 – Gravelines** : même schéma via Lille-Lesquin (LIL) et Sportica · **victoire 65-70**
4. **Étape 3 – Roanne** : autocar base → Astroballe (aucun avion) · **victoire 96-77** · retour à la base
5. **Étape 4 – Limoges** : via Limoges-Bellegarde (LIG) et Beaublanc · **victoire 94-97**
6. **Étape 5 – Nancy** : autocar base → Astroballe · PROCHAIN MATCH ASVEL vs NANCY · OBJECTIF 5/5 (aucun résultat)
7. **Bilan** – France entière, tous les trajets, statistiques recalculées

Couleurs : **vert** = aller, **blanc** = retour, **jaune** = prochain match.
Les victoires apparaissent à l'arrivée du car à la salle et ne disparaissent plus
(bandeau permanent en haut + marqueurs verts sur la carte). Le compteur n'évolue
qu'au moment d'une victoire, jamais pendant un retour.

## Commandes

```bash
npm install
npm run studio        # aperçu interactif
npm run export        # rendu + conversion Instagram → export/asvel-tour.mp4
npm run fetch:routes  # régénère les itinéraires routiers (accès réseau OSRM requis)
npm run build:map     # régénère le fond de carte
```

Sans téléchargement de Chrome possible : `REMOTION_BROWSER=/chemin/chrome-headless-shell npm run export`.

## Réutiliser pour les prochains matchs

Tout est piloté par `src/data/tour.ts` : `PLACES` (salles, base, aérogares),
`AIRPORTS` (codes, piste utilisée), `GAMES` (adversaire, salle, aéroport ou `null`
à domicile, score ASVEL/adversaire ou `null` si à venir, position de l'encart).
Après modification : `npm run fetch:routes`, puis `npm run export`.
Trajets, vols, compteurs, coûts, bilan et durée de la vidéo sont recalculés.

## Données vérifiées

### Lieux (OpenStreetMap, Nominatim / Overpass, octobre 2026)

| Lieu | Coordonnées (lat, lon) | Référence OSM |
|---|---|---|
| La Meilleraie, Cholet | 47.0577, -0.8962 | way 69972018 |
| Sportica, Gravelines | 50.99852, 2.12286 | relation 16890974 |
| Astroballe, Villeurbanne | 45.76642, 4.90736 | way 85200814 |
| Palais des sports de Beaublanc, Limoges | 45.84752, 1.24339 | way 70372530 |
| Base lyonnaise : Tony Parker Adéquat Academy, Gerland | 45.72529, 4.82712 | way 527494526 |

La « base lyonnaise » est un choix de scénario (pôle d'entraînement et de formation
du club à Gerland) : à adapter dans `PLACES.BASE` si besoin. Roanne et Nancy
sont des adversaires reçus à l'Astroballe : aucun trajet vers ces villes.

### Aéroports et pistes (OurAirports, seuils WGS84)

| Aéroport | IATA / OACI | Piste | Longueur | Compatible ERJ 145 |
|---|---|---|---|---|
| Lyon-Saint-Exupéry | LYS / LFLL | 17R/35L | 4 000 m × 45 m | oui |
| Nantes-Atlantique | NTE / LFRS | 03/21 | 2 900 m × 45 m | oui |
| Lille-Lesquin | LIL / LFQQ | 08/26 | 2 825 m × 45 m | oui |
| Limoges-Bellegarde | LIG / LFBL | 03/21 | 2 500 m × 45 m | oui |
| Cholet-Le Pontreau | — / LFOU | 02/20 | 1 380 m × 30 m | **écarté** |

ERJ 145 LR (fiche Embraer) : 2 270 m au décollage et 1 400 m à l'atterrissage
aux masses maximales → Cholet-Le Pontreau n'est pas retenu, la compatibilité
n'étant pas confirmée ; Nantes-Atlantique dessert Cholet. Le QFU affiché est
celui aligné sur l'axe du vol (le vent réel déciderait).

### Itinéraires routiers (OSRM, données © contributeurs OpenStreetMap, ODbL)

| Transfert | Distance | Durée autocar estimée |
|---|---|---|
| Base → LYS / LYS → base | 28,2 / 28,0 km | ≈ 30 min |
| NTE → La Meilleraie / retour | 62,6 / 61,3 km | ≈ 1 h 00 |
| LIL → Sportica / retour | 97,7 / 97,6 km | ≈ 1 h 25 |
| LIG → Beaublanc / retour | 10,1 / 9,4 km | ≈ 15 min |
| Base → Astroballe / retour | 12,5 / 11,9 km | ≈ 20 min |

Durée = durée OSRM (profil voiture) × 1,15 pour un autocar. Géométrie simplifiée
à ≈ 15 m (Douglas-Peucker). **Distance totale en autocar : 544,2 km.**

## Modèle aéronautique (estimations, `src/lib/aviation.ts`)

| Vol | Distance | Vent | Temps de vol | Kérosène | Carburant (inclus) | Affrètement |
|---|---|---|---|---|---|---|
| ASVEL 101 LYS → NTE | 537 km | −47 km/h | 1 h 00 | 1 489 L | 1 800 – 2 700 € | 11 200 – 17 300 € |
| ASVEL 102 NTE → LYS | 537 km | +48 km/h | 0 h 55 | 1 346 L | 1 600 – 2 400 € | 11 500 – 18 000 € |
| ASVEL 103 LYS → LIL | 558 km | −13 km/h | 1 h 00 | 1 480 L | 1 800 – 2 700 € | 11 200 – 17 200 € |
| ASVEL 104 LIL → LYS | 558 km | +14 km/h | 0 h 58 | 1 423 L | 1 700 – 2 600 € | 11 800 – 18 500 € |
| ASVEL 105 LYS → LIG | 304 km | −50 km/h | 0 h 40 | 1 036 L | 1 200 – 1 900 € | 9 800 – 15 100 € |
| ASVEL 106 LIG → LYS | 304 km | +50 km/h | 0 h 37 | 943 L | 1 100 – 1 700 € | 10 800 – 16 900 € |

**Totaux (6 vols, 3 allers + 3 retours)** : 2 798 km · 5 h 10 de vol · 7 716 L ·
affrètements 66 300 – 103 000 €.

Hypothèses :

- Distance : orthodromie (haversine) entre points de référence d'aérodrome ;
  distance parcourue = × 1,05 (routes aériennes). Séparation latérale de 4 km
  entre couloirs aller et retour sur la carte.
- Temps de vol = distance parcourue / vitesse sol + 14 min (montée, descente,
  approche). Croisière 780 km/h vraie (≈ Mach 0,72 ; maxi constructeur Mach 0,78).
  Vent moyen d'altitude 50 km/h d'ouest : les vols vers l'est sont plus rapides.
- Roulage : 12 min au départ de LYS, 8 min ailleurs ; 6 / 5 min à l'arrivée.
- Consommation : 1 090 kg/h en vol (≈ 359 gal US/h, donnée courtier), 6 kg/min au
  roulage, densité 0,803 kg/L. Les valeurs indicatives fournies (1 100 L) sont
  donc revues à la hausse.
- Jet A-1 : 1,20 – 1,80 €/L HT (tarifs publics Air BP 2026 relevés entre 1,60 et
  1,92 €/L HT ; un opérateur sous contrat paie moins).
- Affrètement, **carburant inclus (jamais ajouté une seconde fois)** :
  5 000 – 7 500 € par heure bloc (fourchettes courtiers 5 500 – 9 000 $/h),
  minimum 1 h facturée par vol, + 0,75 h de repositionnement de l'appareil par
  vol, + 1 000 – 2 000 € de redevances aéroportuaires et d'assistance par vol,
  + 1 000 – 1 800 € d'immobilisation (attente du match, équipage) sur le retour.
- Profil de vitesse animé (décollage 250 km/h, croisière, approche, toucher
  240 km/h, freinage) ajusté pour que le temps total corresponde au modèle.

## Carte et visuels

- Départements : IGN ADMIN EXPRESS (Licence ouverte), via gregoiredavid/france-geojson ;
  pays voisins : Natural Earth 1:50m. Projection conique conforme de Lambert,
  paramètres Lambert-93.
- Embraer ERJ 145 vectoriel (vue de dessus, cotes constructeur : 29,87 m × 20,04 m,
  nacelles AE3007 arrière, empennage en T, train sorti au sol et en approche).
  Autocar vectoriel de profil (vitres, pare-brise, roues animées, phares, feux
  de freinage, livrée verte). Pistes dessinées à leur longueur réelle, largeur
  exagérée pour la lisibilité.
- Aucune image, aucune photo, aucun emoji, aucun visuel généré : uniquement SVG,
  texte et animation 2D (polices Barlow / Barlow Condensed, OFL).
