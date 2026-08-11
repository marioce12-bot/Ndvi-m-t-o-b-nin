# Etape 0 - Exploration de la source USGS

Date de verification : 11 aout 2026

## Conclusion

Les deux produits eVIIRS West Africa sont disponibles publiquement, en GeoTIFF EPSG:4326 dans des archives ZIP. La source d'anomalie de la specification etait toutefois incorrecte : USGS publie **Percent of Mean** et non **Percent of Median**. Le choix de Percent of Mean a ete valide par le proprietaire le 11 aout 2026.

## Repertoires et nommage confirmes

| Produit applicatif | Produit USGS | Repertoire | Motif ZIP | GeoTIFF interne observe |
|---|---|---|---|---|
| `ndvi` | Temporally Smoothed NDVI | `https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/africa/west/pentadal/eviirs/ndvi/temporallysmoothedndvi/downloads/pentadal/` | `wa{YY}{PP}.zip` | `wa{YY}{PP}m.tif` |
| `anomaly` | Percent of Mean | `https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/africa/west/pentadal/eviirs/ndvi/percentofmean/downloads/pentadal/` | `wa{YY}{PP}pct.zip` | `wa{YY}{PP}pctm.tif` |

L'URL prevue `.../percentofmedian/...` retourne HTTP 404. Le portail officiel [NDVI eVIIRS West Africa](https://earlywarning.usgs.gov/fews/product/903/) pointe vers `percentofmean`.

Le test a utilise la pentade complete la plus recente disponible : `2026-P44`, soit les archives `wa2644.zip` et `wa2644pct.zip`.

## Metadonnees des rasters testes

Les deux fichiers ont les memes caracteristiques spatiales :

- CRS : `EPSG:4326`
- type : `uint8`, une bande
- taille : `12442 x 5249` pixels
- resolution : `0.003619000083` degre, environ 375 m
- emprise : `(-17.529074665363, 2.001592353729, 27.498524367323, 20.997723789396)`
- compression : LZW
- `nodata` declare : `255`

Archives inspectees :

| Archive | Taille | SHA-256 |
|---|---:|---|
| `wa2644.zip` | 34 433 590 octets | `91794B12017D9193FD6D35D9206062C9493954BF7DEAC6985C69816ED32379A1` |
| `wa2644pct.zip` | 47 491 004 octets | `5386932223B52FC2B035AC0A6593A07E5EF1AD685F04557C6D411364958C5981` |

## Valeurs, sentinelles et histogrammes

### NDVI

- valeurs non sentinelles observees : `92..190`
- valeurs speciales observees : `0` et `255`
- documentation USGS : valeurs NDVI mappees lineairement de `[-1, 1]` vers `[0, 200]`; valeurs `201..255` invalides
- formule confirmee : `NDVI = (DN - 100) / 100`
- plage decodee observee hors masque : `-0.08..0.90`
- percentiles DN non sentinelles `[min, P1, P5, P25, P50, P75, P95, P99, max]` : `[92, 107, 108, 112, 143, 177, 188, 189, 190]`

Histogramme global resume :

| DN | Nombre de pixels |
|---|---:|
| `0..91` | 2 312 002, tous a `0` |
| `92..99` | 64 404 |
| `100..109` | 7 139 223 |
| `110..119` | 12 098 970 |
| `120..139` | 6 254 773 |
| `140..159` | 6 300 645 |
| `160..179` | 9 527 411 |
| `180..190` | 11 909 896 |
| `191..200` | 0 |
| `201..255` | 9 700 734, tous a `255` |

### Percent of Mean

- decodage : valeur directe en pourcentage
- valeurs non sentinelles observees : `1..200`
- valeurs speciales observees : `0` et `255`
- `100` signifie la moyenne historique; la documentation USGS classe `95..105` comme conditions moyennes
- percentiles globaux inferieurs a 250 : `[0, 0, 42, 81, 93, 105, 125, 150, 200]`

Histogramme global resume :

| Pourcentage | Nombre de pixels |
|---|---:|
| `0` | 2 370 824 |
| `1..49` | 885 775 |
| `50..79` | 8 936 562 |
| `80..89` | 12 034 456 |
| `90..94` | 5 260 521 |
| `95..99` | 4 528 751 |
| `100..104` | 6 585 968 |
| `105..109` | 5 472 532 |
| `110..119` | 5 349 340 |
| `120..149` | 3 602 611 |
| `150..199` | 526 963 |
| `200` | 52 711 |
| `201..254` | 0 |
| `255` | 9 701 044 |

### Masques a appliquer en production

- `255` : `nodata` explicite du GeoTIFF; la table de couleurs integree lui donne aussi un alpha nul.
- `201..255` : invalides pour le NDVI selon la documentation USGS.
- `0` : masque qualite/nuages dans les fichiers intermediaires actuels. Il apparait aux memes zones dans les deux produits et doit etre masque; la documentation precise que les composites intermediaires utilisent les indicateurs de nuages avant correction finale.
- Pour `anomaly`, `200` est une valeur valide plafonnee et ne doit pas etre masquee.
- Pour `ndvi`, les DN `92..99` sont des NDVI negatifs valides d'apres l'encodage USGS; ils ne sont pas des sentinelles. Le rendu pourra les saturer sous son `vmin`, mais le traitement ne doit pas les confondre avec le masque.

Regles retenues pour `processing.py` :

```text
ndvi:    mask = nodata OR DN == 0 OR DN >= 201
         value = (DN - 100) / 100
anomaly: mask = nodata OR DN == 0
         value = DN
```

## Sources de verification

- Index Apache des deux repertoires USGS cites ci-dessus.
- Portail officiel : `https://earlywarning.usgs.gov/fews/product/903/`.
- Documentation embarquee du portail, section "Spatial Parameters for eVIIRS Data" : `[-1.0, 1.0] -> [0, 200]`, valeurs invalides `201..255`, et formule `NDVI = (value - 100) / 100`.
- Documentation "Percent of Mean" : moyenne 2012-2021 et intervalle normal `95..105`.

## Gate Etape 0

Le nommage, les metadonnees, les sentinelles et le decodage sont verifies. L'etape 1 ne doit commencer qu'apres validation explicite de ce rapport.
