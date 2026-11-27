# Calidad de las capas geográficas

La preparación valida los puntos y conserva los archivos fuente sin cambios. Solo quita filas GeoJSON idénticas en todos sus campos. Las coincidencias parciales se guardan para revisión.

## Resumen

| Capa | Filas de entrada | Filas preparadas | Filas inválidas | Duplicados idénticos retirados | Nombres vacíos |
|---|---:|---:|---:|---:|---:|
| equipamientos.geojson | 2714 | 2714 | 0 | 0 | 640 |
| transporte.geojson | 42 | 42 | 0 | 0 | 0 |

## Categorías

### equipamientos.geojson

Campo: categoria.

- abastecimiento: 392
- cultura: 220
- educacion: 1018
- parques: 799
- salud: 224
- seguridad: 61

### transporte.geojson

Campo: sistema.

- metro: 23
- metrocable: 9
- metroplus: 1
- tranvia: 9

## Revisión y datos faltantes

- Registros con coordenadas compartidas o identificador osm_id repetido: 10. Se conservan en la capa preparada.
- Registros con geometría o campos obligatorios inválidos: 0. Se guardan en el CSV de filas inválidas y no entran en la capa preparada.
- Los nombres vacíos se conservan. No se inventan nombres, y el conteo por categoría no depende de ellos.
- Las coordenadas GeoJSON se interpretan en orden longitud, latitud y se validan contra los rangos geográficos globales.

Los registros marcados para revisión están en output/prepared/geo/coincidencias_para_revision.csv.
Las filas inválidas están en output/prepared/geo/filas_invalidas.csv.

## Capas preparadas

- output/prepared/geo/equipamientos_limpios.geojson
- output/prepared/geo/transporte_limpio.geojson
