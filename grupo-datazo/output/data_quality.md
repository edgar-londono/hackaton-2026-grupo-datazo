# Data quality report

This report checks required fields, numeric values, coordinate ranges, accepted price types, and configured price per square meter limits.

## Summary

- Listings checked: 117.
- Test properties checked: 11.
- Rows with required field or value issues: 1 listings and 0 test properties.
- Invalid numeric values: 0.
- Price per square meter checked for 116 listings.
- Configured price range: 1,000,000 to 20,000,000 COP/m2, parameter version 1.0.
- Listings without a condition: 25. They cannot enter condition-matched comparisons.

## Missing values

Counts include optional fields. A missing optional value is not an invalid row.

| Dataset | Field | Missing rows |
|---|---|---:|
| Listings | area_m2 | 1 |
| Listings | banos | 9 |
| Listings | barrio | 25 |
| Listings | estado | 25 |
| Listings | fecha | 117 |
| Listings | habitaciones | 5 |
| Listings | id_anuncio | 50 |
| Listings | parqueadero | 82 |
| Test properties | direccion | 7 |

## Required field and value issues

| Dataset | CSV row | Record | Field | Reason | Value |
|---|---:|---|---|---|---|
| Listings | 47 | extension_poligono.xlsx:REMODELAR:53 | area_m2 | Required value is missing. | <blank> |

## Duplicate removal

Configured keys find candidates only. Comparison trims and collapses spaces and ignores letter case, while preserving accents. Rows are removed only when every source column matches after that comparison. Candidate groups with any remaining difference are held for review.

| Candidate key | Candidate groups | Rows removed after normalization |
|---|---:|---:|
| id_anuncio | 10 | 0 |
| claves_sin_id (zona, area_m2, precio) | 21 | 0 |
| All source columns | 0 | 0 |
| Total | 31 | 0 |
| Rows retained | | 117 |
| Connected groups held for review | | 21 |
| Candidate rows held for review | | 54 |

Review file: output/prepared/duplicados_para_revision.csv.
Normalization before/after log: output/prepared/normalizacion_texto.csv.

## Prepared valid inputs

Listings: 117 after deduplication, 70 excluded, 47 valid.
Test properties: 11 checked, 0 excluded, 11 valid.
Use only the valid files below for later market and neighborhood calculations.

- output/prepared/anuncios_validos.csv
- output/prepared/inmuebles_validos.csv
- output/prepared/exclusiones.csv
- output/prepared/duplicados_para_revision.csv

## Exclusion counts by reason

Counts are issue occurrences. One row can have more than one reason.

| Dataset | Field | Reason | Occurrences |
|---|---|---|---:|
| Listings | all_columns | Candidate duplicate differs across columns and needs human review. | 54 |
| Listings | area_m2 | Required value is missing. | 1 |
| Listings | estado | Cannot match this listing to a canonical condition. | 25 |

## Excluded rows

| Dataset | CSV row | Record | Field | Reason | Value |
|---|---:|---|---|---|---|
| Listings | 2 | fincaraiz:10710482 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 3 | fincaraiz:193287983 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 9 | fincaraiz:193440669 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 10 | fincaraiz:193287983 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 11 | fincaraiz:10710482 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 12 | fincaraiz:193440669 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 21 | fincaraiz:192959138 | all_columns | Candidate duplicate differs across columns and needs human review. | id_anuncio, barrio, estado, origen |
| Listings | 23 | fincaraiz:193131396 | all_columns | Candidate duplicate differs across columns and needs human review. | id_anuncio, barrio, estado, origen |
| Listings | 25 | fincaraiz:192937244 | all_columns | Candidate duplicate differs across columns and needs human review. | id_anuncio, barrio, estado, origen |
| Listings | 39 | extension_poligono.xlsx:REMODELAR:33 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 41 | extension_poligono.xlsx:REMODELAR:38 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 42 | extension_poligono.xlsx:REMODELAR:39 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 42 | extension_poligono.xlsx:REMODELAR:39 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 43 | extension_poligono.xlsx:REMODELAR:43 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 44 | extension_poligono.xlsx:REMODELAR:45 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 45 | extension_poligono.xlsx:REMODELAR:49 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 46 | extension_poligono.xlsx:REMODELAR:52 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 47 | extension_poligono.xlsx:REMODELAR:53 | area_m2 | Required value is missing. | <blank> |
| Listings | 47 | extension_poligono.xlsx:REMODELAR:53 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 48 | extension_poligono.xlsx:REMODELAR:55 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 49 | extension_poligono.xlsx:REMODELAR:56 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 50 | extension_poligono.xlsx:REMODELAR:59 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 51 | extension_poligono.xlsx:REMODELAR:60 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 51 | extension_poligono.xlsx:REMODELAR:60 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 52 | fincaraiz:192814617 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 52 | fincaraiz:192814617 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 53 | fincaraiz:192824557 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 54 | fincaraiz:191722056# | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 55 | fincaraiz:7387557 | all_columns | Candidate duplicate differs across columns and needs human review. | id_anuncio, fuente, estado, origen |
| Listings | 55 | fincaraiz:7387557 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 56 | fincaraiz:10766727 | all_columns | Candidate duplicate differs across columns and needs human review. | id_anuncio, fuente, estado, origen |
| Listings | 56 | fincaraiz:10766727 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 57 | fincaraiz:192687997 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 58 | fincaraiz:7387557 | all_columns | Candidate duplicate differs across columns and needs human review. | id_anuncio, fuente, estado, origen |
| Listings | 58 | fincaraiz:7387557 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 60 | extension_poligono.xlsx:REMODELAR:73 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 61 | extension_poligono.xlsx:REMODELAR:74 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 62 | extension_poligono.xlsx:REMODELAR:75 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 63 | extension_poligono.xlsx:REMODELAR:76 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 64 | arrendamientos_santafe:V12132 | all_columns | Candidate duplicate differs across columns and needs human review. | id_anuncio, fuente, estado, origen |
| Listings | 65 | arrendamientos_santafe:V10746 | all_columns | Candidate duplicate differs across columns and needs human review. | id_anuncio, fuente, estado, origen |
| Listings | 69 | fincaraiz:193042067 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 70 | fincaraiz:192609616 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 71 | fincaraiz:8146402 | all_columns | Candidate duplicate differs across columns and needs human review. | habitaciones, banos, estado, origen |
| Listings | 72 | extension_poligono.xlsx:REMODELAR:85 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 73 | extension_poligono.xlsx:REMODELAR:86 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 74 | extension_poligono.xlsx:REMODELAR:87 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 75 | extension_poligono.xlsx:REMODELAR:88 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 76 | extension_poligono.xlsx:REMODELAR:89 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 77 | extension_poligono.xlsx:REMODELAR:90 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 78 | extension_poligono.xlsx:REMODELAR:91 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, habitaciones, estado, origen |
| Listings | 79 | extension_poligono.xlsx:REMODELAR:92 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 80 | fincaraiz:193042067 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 81 | fincaraiz:192609616 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 82 | fincaraiz:8146402 | all_columns | Candidate duplicate differs across columns and needs human review. | habitaciones, banos, estado, origen |
| Listings | 93 | extension_poligono.xlsx:El salvador:3 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 95 | fincaraiz:7387557 | all_columns | Candidate duplicate differs across columns and needs human review. | id_anuncio, fuente, estado, origen |
| Listings | 96 | arrendamientos_santafe:V12132 | all_columns | Candidate duplicate differs across columns and needs human review. | id_anuncio, fuente, estado, origen |
| Listings | 97 | arrendamientos_santafe:V10746 | all_columns | Candidate duplicate differs across columns and needs human review. | id_anuncio, fuente, estado, origen |
| Listings | 98 | extension_poligono.xlsx:El salvador:8 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 100 | extension_poligono.xlsx:El salvador:10 | all_columns | Candidate duplicate differs across columns and needs human review. | origen |
| Listings | 101 | extension_poligono.xlsx:El salvador:11 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 102 | fincaraiz:192814617 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 103 | extension_poligono.xlsx:El salvador:13 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 104 | extension_poligono.xlsx:El salvador:14 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 105 | extension_poligono.xlsx:El salvador:15 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 106 | extension_poligono.xlsx:El salvador:16 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 107 | extension_poligono.xlsx:El salvador:17 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, habitaciones, estado, origen |
| Listings | 109 | extension_poligono.xlsx:El salvador:19 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 111 | extension_poligono.xlsx:VIVIR:5 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 112 | extension_poligono.xlsx:VIVIR:6 | all_columns | Candidate duplicate differs across columns and needs human review. | estado, origen |
| Listings | 113 | extension_poligono.xlsx:VIVIR:7 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 114 | extension_poligono.xlsx:VIVIR:8 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 115 | extension_poligono.xlsx:VIVIR:9 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 116 | extension_poligono.xlsx:VIVIR:10 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 116 | extension_poligono.xlsx:VIVIR:10 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 117 | extension_poligono.xlsx:VIVIR:11 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, habitaciones, estado, origen |
| Listings | 117 | extension_poligono.xlsx:VIVIR:11 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 118 | extension_poligono.xlsx:VIVIR:12 | all_columns | Candidate duplicate differs across columns and needs human review. | barrio, estado, origen |
| Listings | 118 | extension_poligono.xlsx:VIVIR:12 | estado | Cannot match this listing to a canonical condition. | <blank> |

## Out-of-range prices

No calculated listing prices per square meter fall outside the configured range.

## Missing condition values

25 listings have an empty estado. They remain visible in the source data but cannot match a canonical condition.

## Normalized conditions

Missing or unmapped values remain sin_clasificar.

| Dataset | Canonical condition | Rows |
|---|---|---:|
| Listings | habitable | 35 |
| Listings | por_remodelar | 33 |
| Listings | remodelado | 24 |
| Listings | sin_clasificar | 25 |
| Test properties | habitable | 2 |
| Test properties | por_remodelar | 6 |
| Test properties | remodelado | 3 |
