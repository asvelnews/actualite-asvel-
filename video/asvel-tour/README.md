# ASVEL TOUR – Reel Instagram (Remotion)

Vidéo 1080 × 1920, 30 i/s, MP4 H.264 : les victoires de l'ASVEL s'affichent sur
la carte de France et restent visibles jusqu'à la fin de l'animation.

Rendu prêt à publier : `export/asvel-tour.mp4`.

## Commandes

```bash
npm install
npm run studio   # aperçu interactif
npm run render   # → out/asvel-tour.mp4
```

Dans un environnement sans téléchargement de Chrome, indiquer un navigateur local :
`REMOTION_BROWSER=/chemin/vers/chrome-headless-shell npm run render`.

## Réutiliser pour les prochains matchs

Tout est piloté par `src/data/tour.ts` :

- `PLACES` : aéroports et salles (coordonnées WGS84 `[longitude, latitude]`).
- `GAMES` : un match par étape (adversaire, salle, aéroport d'arrivée, domicile/extérieur,
  score ASVEL en premier, `score: null` pour un match à venir) et la position `label`
  de l'encart sur la carte (en pixels, vue France entière).

Le compteur (x/N), le tableau des victoires, les trajets, les distances, les durées
de vol et de bus, les statistiques finales (série, extérieur, domicile) et le
prochain match sont recalculés automatiquement. La durée de la vidéo s'adapte.

## Données géographiques

- Carte : Natural Earth 1:10m (domaine public, paquet npm `world-atlas`), France
  métropolitaine + Corse, régénérable avec `npm run build:map`.
- Projection : conique conforme de Lambert, paramètres du Lambert-93 (IGN).
- Distances de vol : orthodromie (haversine, rayon terrestre moyen 6 371 km),
  trajectoire tracée le long du grand cercle.
- Durée de vol estimée : 20 min (roulage, montée, approche) + distance / 750 km/h.
- Bus : distance à vol d'oiseau × 1,3 (détour routier moyen), 45 km/h de moyenne.
  Le tracé du bus est stylisé (pas de données routières embarquées).

Aucune image, photo ni visuel généré : uniquement SVG, texte et animation 2D
(polices Barlow / Barlow Condensed, licence OFL, embarquées via `@fontsource`).
