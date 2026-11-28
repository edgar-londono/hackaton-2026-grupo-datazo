# Output contract

This document maps the challenge template to our JSON record and readable property card. It defines where each value comes from and how to show missing or invalid information.

## Output files

- Create one JSON file per test property under `output/fichas/`.
- Create one Markdown card per test property under `output/cards/`.
- Create the selected listing set, possible-repeat tables, normalization log, field audit, and quality report under `output/`.
- Add an evidence row to `data/anuncios_verificaciones.csv` before applying an official confirmation or correction.
- Use the supplied `plantilla_ficha.md` and `ficha_ejemplo.json` as the field and layout references.
- Keep the reference files unchanged.

## JSON field mapping

| JSON field | Source or calculation | Missing or invalid behavior |
|---|---|---|
| `id_inmueble` | `inmuebles_prueba.csv:id_inmueble` | Required identifier. Stop that record if absent. |
| `inmueble.direccion` | `inmuebles_prueba.csv:direccion` | Use `null` when absent. Add `direccion` to `datos_faltantes`. |
| `inmueble.barrio`, `municipio`, `zona`, `area_m2` | Matching columns in `inmuebles_prueba.csv` | Use `null` when the source has no value. Do not infer it. |
| `inmueble.estado_texto` | Raw `estado` from the listing matched by `id_anuncio` or, when needed, `origen` | Use `null` if no unique source listing matches. Record the missing value. |
| `inmueble.estado` | Normalize the source condition with `config/parametros.yaml` | Keep an unmapped value unclassified. Exclude it from comparable matching. |
| `inmueble.coordenadas.lat`, `lon` | `inmuebles_prueba.csv:lat,lon` | Use `null` when absent or invalid. Skip location calculations that need those coordinates. |
| `inmueble.coordenadas.precision`, `fuente` | `precision_coordenadas`, `fuente_coordenadas` in `inmuebles_prueba.csv` | Preserve the source. Mark neighborhood-level coordinates as approximate. |
| `mercado.estado_referencia` | Normalize the test-property condition using `config/parametros.yaml` | Use `null` when the condition is unclassified. |
| `mercado.precio_m2.n` | Count of valid matched comparables | Use `0` when the matching process ran and found none. |
| `mercado.precio_m2.mediana`, `promedio`, `minimo`, `maximo`, `desviacion`, `coef_variacion` | Statistics over matched comparables after zone, condition, area, price, and duplicate rules | Use `null` when no valid comparable supports the calculation. Report COP values as integers and the coefficient of variation to four decimals. Keep valid calculations and show low confidence when configured. |
| `mercado.confianza.nivel`, `motivo` | Supplied confidence thresholds, sample count, and coefficient of variation | Use `null` for the level when no market calculation is possible. State the reason and missing fields in `motivo` and `datos_faltantes`. |
| `mercado.comparables` | Matched rows from `anuncios_muestra.csv` | Use an empty list when none qualify. Sort by `precio_m2` in ascending order. |
| `mercado.precio_m2_por_estado_en_zona` | Count and median for each normalized condition in the zone, without the comparable area filter | Use `n: 0` and `mediana: null` when a condition has no valid records. |
| `calidad_datos_zona.anuncios_en_zona` | All input listing rows in the property's zone | Count before deduplication. |
| `calidad_datos_zona.duplicados_eliminados`, `anuncios_unicos` | Approved full-row comparison rule | Remove a row only when all source columns match after whitespace and numeric formatting normalization. Preserve case and accents. |
| `calidad_datos_zona.anuncios_invalidos` | Field and value checks for rows in the zone | Count issue types. Exclude a row only from calculations whose required fields are missing or invalid. |
| `calidad_datos_zona.posibles_repeticiones`, `grupos_posibles_repeticiones` | Candidate groups with differing source columns | Keep them separate. Report rows and groups. They are not confirmed duplicates. |
| `calidad_datos_zona.candidatos_incluidos_en_calculos`, `candidatos_seleccionados_en_zona` | Run option and candidate rows in the selected analysis set | The team can include or exclude candidates with `--include-candidates` or `--exclude-candidates`. The configured default is in `config/parametros.yaml`. |
| `calidad_datos_zona.filas_invalidas_unicas` | Unique rows with one or more field or value issues | Count each affected row once. A field issue does not remove unrelated usable values. |
| `calidad_datos_zona.anuncios_conservados` | Rows available under the selected candidate option | Report the actual count after exact duplicate removal and candidate selection. |
| `entorno.radio_busqueda_m` | `config/parametros.yaml:entorno.radio_busqueda_m` | Report the configured value used for this result. |
| `entorno.estacion_mas_cercana` | Test coordinates and supported station features in `data/geo/transporte.geojson`, using the documented Haversine method | Use `null` when the location or layer cannot support a calculation. Report the nearest station even when it is outside the search radius. |
| `entorno.estaciones_en_radio` | Transit features in the configured radius and supported systems | Use `null` when the count cannot be calculated. Use `0` only when a valid calculation finds none. |
| `entorno.equipamientos_en_radio` | `data/geo/equipamientos.geojson` and configured categories | Use `null` for counts that cannot be calculated. Use `0` only for a valid count of none. |
| `entorno.aproximado` | Coordinate precision | Set `true` when the source location is neighborhood-level. |
| `norma.tratamiento_pot`, `estado`, `motivo` | POT layer and `municipios_cubiertos` in `config/parametros.yaml` | Use `pendiente_capa` for a covered municipality when the layer is absent. Use `no_disponible` for a municipality outside coverage. Use `capa_disponible_sin_interseccion` if a layer exists but the MVP cannot calculate the polygon intersection. Keep treatment null and explain the status. |
| `datos_faltantes` | Missing fields and unsupported calculations found during processing | Preserve supplied codes. Add a clear code for insufficient comparables or unavailable coordinates when needed. Include missing listing dates and closing prices when relevant. |
| `metadatos.version_parametros` | `config/parametros.yaml:version` | Record the exact version used. |
| `metadatos.fecha_generacion` | Date of the pipeline run | Use the same date format as the supplied example. |
| `metadatos.fecha_capas_osm` | `metadata.fecha_osm` in supplied GeoJSON files | Use the layer date when available. Use `null` when the source layer has no date. |
| `metadatos.fuentes` | Files and data sources used to produce the record | List the actual sources used. Do not name a source that did not contribute. |

## Readable card mapping

| Card section | Fields to display | Display rule |
|---|---|---|
| Property | Identifier, address, neighborhood, municipality, area, condition, coordinates, precision | Show unavailable fields as “insufficient data.” Label neighborhood-level coordinates as approximate. |
| Market | Reference condition, median price per square meter, range, comparable count, coefficient of variation, confidence, and zone context by condition | Show numeric results only when supported. Include the confidence reason. |
| Neighborhood | Search radius, nearest station and distance, station count, facility counts by category | Mark approximate results. Show “insufficient data” when a calculation cannot run. Preserve zero when a valid calculation finds none. |
| Zoning | POT treatment, status, and reason | Show the pending status while the layer is absent. |
| Data quality | Zone rows, exact duplicates, possible repeats, selected candidate option, rows with field issues, and missing fields | Show the option used. Missing or invalid fields affect only calculations that need them. |
| Sources | Input files, parameter version, and source-layer date | List the sources used for the record. |

## Data integrity rules

- Use `null` for unsupported JSON values. Never substitute zero for an unavailable calculation.
- Show “insufficient data” and the reason on the affected card section when a required input for that calculation is missing or invalid.
- Keep other supported sections visible when one section cannot be calculated.
- Show a low-confidence calculation when valid data supports it and the supplied rule assigns low confidence.
- Check each calculation's required fields. Keep source rows available when an unrelated field is missing.
- Keep possible repeats in `output/prepared/posibles_repeticiones.csv` and group details in `output/prepared/grupos_posibles_repeticiones.csv`.
- Record each of the 1,638 source field values in `output/prepared/auditoria_campos_anuncios.csv`.
- Label unconfirmed prices as reported asking prices from the supplied sample.

## Reference sources

- `../resources/venture-one-reference/docs/plantilla_ficha.md` defines the JSON fields and card layout.
- `../resources/venture-one-reference/ejemplos/ficha_ejemplo.json` shows one complete property record.
- `../resources/venture-one-reference/docs/diccionario_datos.md` maps input columns and known data limits.
- `../resources/venture-one-reference/config/parametros.yaml` defines calculation parameters.
