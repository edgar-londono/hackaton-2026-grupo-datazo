# Data quality report

This report checks required fields, numeric values, coordinate ranges, accepted price types, and configured price per square meter limits.
Duplicate analysis remains pending checklist item 4.4.

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

## Out-of-range prices

No calculated listing prices per square meter fall outside the configured range.

## Missing condition values

25 listings have an empty estado. They remain visible in the source data but cannot match a canonical condition.

## Pending checks

- Apply invalid-row exclusions to calculations under checklist item 4.5.
- Count duplicate groups and apply the supplied rules under checklist item 4.4.
