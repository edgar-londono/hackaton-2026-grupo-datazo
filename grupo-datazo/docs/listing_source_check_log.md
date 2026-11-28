# Listing source check log

## Scope

This log covers only existing fields in `data/anuncios_muestra.csv`. No listing portal was opened or scraped. No listing value was corrected in this phase.

## Why the ad claims remain unverified

The sample has source IDs, municipality and neighborhood labels, asking prices, and property details. It does not provide a street address or an official record ID that links each ad to a public registry record. A municipality or neighborhood name match cannot prove that an individual ad is located there.

For this reason, the field audit labels supplied values as reported by the source. It does not describe them as officially confirmed. Missing values remain missing.

## Public references considered

These public references may help validate names or administrative labels. They do not confirm the truth of an individual listing.

- DANE's [DIVIPOLA municipality codes](https://www.datos.gov.co/Mapas-Nacionales/DIVIPOLA-C-digos-municipios/gdxc-w37w) can verify a municipality name and code.
- Medellín's [neighborhood information page](https://www.medellin.gov.co/es/conoce-algunos-datos-generales-de-la-ciudad/) can check whether a neighborhood label appears in the city's published list.
- Itagüí's [community participation page](https://itagui.gov.co/micrositios/micrositio/ciudadania) lists neighborhoods by comuna.

The sample fields do not uniquely connect each property ad to a record in these references. No source snapshot was stored because no record was used to correct an ad, and redistribution terms for the reference pages were not confirmed.

## Values that need a future decision

- Asking price, publication date, property condition, area, rooms, bathrooms, parking, source, and source record ID remain reported ad values unless an authoritative record uniquely identifies the same property and claim.
- Municipality and neighborhood labels may be checked for valid names. A name match alone must not change the listing's stated location.
- Do not add a corrected value unless the evidence identifies the same property without doubt. Record the old value, corrected value, source URL, record ID, license, check date, and rule.
