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
- Official listing field checks: 0 confirmed, 0 corrected with evidence.

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

Candidate keys ignore case to find possible repeats. Exact removal trims and collapses spaces but preserves case and accents. A row is removed only when every source column matches.

| Candidate key | Candidate groups | Rows removed after normalization |
|---|---:|---:|
| id_anuncio | 10 | 0 |
| claves_sin_id (zona, area_m2, precio) | 21 | 0 |
| All source columns | 0 | 0 |
| Total | 31 | 0 |
| Rows retained | | 117 |
| Possible repeat groups kept separate | | 21 |
| Possible repeat rows | | 54 |
| Possible repeat rows selected for calculations | | 54 |
| Possible repeat rows omitted from calculations | | 0 |

Possible repeat rows: output/prepared/posibles_repeticiones.csv. They remain separate ads.
Choose their use with `--include-candidates` or `--exclude-candidates`; the default comes from config/parametros.yaml.
Group details: output/prepared/grupos_posibles_repeticiones.csv. It lists differing columns and original values.
Field-level source and processing log: output/prepared/auditoria_campos_anuncios.csv.
Normalization before/after log: output/prepared/normalizacion_texto.csv.

## Prepared listing rows

Listings: 117 after exact duplicate removal, 117 retained under the selected candidate option.
Test properties: 11 checked, 0 excluded, 11 valid.
Calculation rules check each required field. A missing value excludes only the calculation that needs it.

- output/prepared/anuncios_seleccionados.csv
- output/prepared/inmuebles_validos.csv
- output/prepared/incidencias_datos.csv
- output/prepared/posibles_repeticiones.csv
- output/prepared/grupos_posibles_repeticiones.csv
- output/prepared/auditoria_campos_anuncios.csv

## Data issue counts by reason

Counts are issue occurrences. One row can have more than one reason.

| Dataset | Field | Reason | Occurrences |
|---|---|---|---:|
| Listings | area_m2 | Required value is missing. | 1 |
| Listings | estado | Cannot match this listing to a canonical condition. | 25 |

## Rows with data issues

| Dataset | CSV row | Record | Field | Reason | Value |
|---|---:|---|---|---|---|
| Listings | 39 | extension_poligono.xlsx:REMODELAR:33 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 41 | extension_poligono.xlsx:REMODELAR:38 | estado | Cannot match this listing to a canonical condition. | <blank> |
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
| Listings | 51 | extension_poligono.xlsx:REMODELAR:60 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 52 | fincaraiz:192814617 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 53 | fincaraiz:192824557 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 54 | fincaraiz:191722056# | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 55 | fincaraiz:7387557 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 56 | fincaraiz:10766727 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 57 | fincaraiz:192687997 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 58 | fincaraiz:7387557 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 61 | extension_poligono.xlsx:REMODELAR:74 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 62 | extension_poligono.xlsx:REMODELAR:75 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 63 | extension_poligono.xlsx:REMODELAR:76 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 116 | extension_poligono.xlsx:VIVIR:10 | estado | Cannot match this listing to a canonical condition. | <blank> |
| Listings | 117 | extension_poligono.xlsx:VIVIR:11 | estado | Cannot match this listing to a canonical condition. | <blank> |
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
