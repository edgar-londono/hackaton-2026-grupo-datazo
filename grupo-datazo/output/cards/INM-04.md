# Property market and neighborhood card: INM-04

Generated: 2026-11-27

## Property

- Address: Calle 37 con Cra 33B
- Neighborhood: El Salvador
- Municipality: medellin
- Market zone: buenos_aires_el_salvador
- Area: 71.0m²
- Condition: habitable (source text: OK)
- Coordinates: 6.234861, -75.560101 (source point)

## Market summary

- Reference condition: habitable
- Comparable listings: 5
- Median asking price per m²: COP 5,769,231
- Range: COP 3,902,439 to COP 6,615,385
- Mean: COP 5,331,537
- Sample standard deviation: COP 1,340,002
- Coefficient of variation: 25.13%
- Confidence: baja. 5 comparables y coeficiente de variación 25.13%; no cumple los umbrales superiores.

### Zone context by condition

| Condition | Valid listings | Median asking price per m² |
|---|---:|---:|
| remodelado | 0 | Insufficient data |
| habitable | 7 | COP 3,909,091 |
| por_remodelar | 14 | COP 4,933,140 |

### Comparables

| Source record | Listing ID | Source | Area | Asking price | Price per m² |
|---|---|---|---:|---:|---:|
| extension_poligono.xlsx:Bombona:9 | fincaraiz:191455596 | fincaraiz | 82.0m² | COP 320,000,000 | COP 3,902,439 |
| extension_poligono.xlsx:REMODELAR:35 | Insufficient data | aviso_calle | 55.0m² | COP 215,000,000 | COP 3,909,091 |
| extension_poligono.xlsx:Bombona:12 | fincaraiz:11002434 | fincaraiz | 78.0m² | COP 450,000,000 | COP 5,769,231 |
| extension_poligono.xlsx:Bombona:10 | fincaraiz:193060833 | fincaraiz | 65.0m² | COP 420,000,000 | COP 6,461,538 |
| extension_poligono.xlsx:Bombona:15 | fincaraiz:192171314 | fincaraiz | 65.0m² | COP 430,000,000 | COP 6,615,385 |

## Neighborhood summary

- Search radius: 800 m
- Coordinate precision: Intersection or supplied point
- Nearest supported transit station: Buenos Aires (tranvia) at 1000 m
- Supported stations within radius: 0

| Facility category | Count within radius |
|---|---:|
| educacion | 22 |
| salud | 2 |
| parques | 12 |
| abastecimiento | 1 |
| seguridad | 1 |
| cultura | 0 |

## Urban planning

- POT treatment: Insufficient data
- Status: pendiente_capa. Falta el archivo data/geo/pot_tratamientos.geojson.

## Data quality and limits

- Listings in zone: 82
- Exact duplicate rows removed: 0
- Unique source rows after exact deduplication: 82
- Valid listings used for analysis: 21
- Candidate listings held out for review: 45 rows in 17 groups
- Invalid unique rows not held for review: 16
- Invalid listings by reason: estado_sin_clasificar: 25; sin_area: 1
- Missing or unavailable data: fecha_publicacion_comparables; precios_de_cierre

## Sources

- Files: data/inmuebles_prueba.csv, data/anuncios_muestra.csv, OpenStreetMap transit layer (ODbL), OpenStreetMap facility layer (ODbL), config/parametros.yaml (POT coverage and missing layer status)
- Parameter version: 1.0
- Geographic layer date: 2026-11-13T23:03:06Z

This card reports asking prices. It does not estimate closing prices or recommend an investment decision.
