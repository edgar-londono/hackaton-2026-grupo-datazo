# MVP plan: Market and neighborhood property card

## Product goal

The MVP should be one reliable market and neighborhood summary for each test property. The team should prove that it works with the supplied data before adding extra features.

The MVP organizes the supplied evidence. It does not decide whether anyone should buy a property.

## Intended user and use

- **User:** a Venture One analyst who reviews a property before an investment decision.
- **Input:** one property from the supplied test set.
- **Output:** a structured result and a readable property card with its data limits made clear.

## What we will build

### 1. Data input

- Read the supplied sample of public property listings.
- Read the supplied test properties and available geographic layers.
- Read thresholds and mappings from the supplied parameter file.
- Keep the reference resource files unchanged.

The archived reference describes 117 sample listings and 11 test properties. It also includes transit and facility layers. Its POT treatment layer is marked as pending.

### 2. Data preparation

- Check required fields, numeric values, and valid ranges.
- Normalize property condition labels with the supplied mappings.
- Detect duplicates with the supplied rules.
- Record invalid rows, duplicate counts, and missing fields.
- Exclude invalid rows from calculations and record why each row was excluded.
- Preserve source identifiers and input references for traceability.

### 3. Comparable market summary

For each test property:

- Select listings from the same market zone.
- Match the canonical property condition.
- Apply the area range and other filters from the supplied parameters.
- Exclude the property's own listing when the reference rules require it.
- Calculate each comparable's asking price per square meter.
- Report the count, median, minimum, maximum, and confidence level.
- Explain the confidence level with its sample count and dispersion measure.

Use the supplied parameter file as the source of thresholds. Do not hard-code a second set of rules.

If no valid comparable supports a market result, set unsupported numeric fields to `null` and show “insufficient data” with the reason and missing fields. If valid comparables support a calculation but the sample is weak, show the result with the configured low confidence level.

Keep other supported sections visible when one section lacks enough data. Exclude invalid inputs from calculations and record why they were excluded. Do not treat approximate coordinates as exact.

### 4. Neighborhood summary

For each test property:

- Find the nearest supplied transit station and show its distance.
- Count supplied stations and facility types within the configured search radius.
- Mark results as approximate when the input coordinate represents a neighborhood instead of an exact location.
- Report unavailable geographic results as unavailable. Do not present approximate coordinates as exact.

### 5. Urban planning data

Read the POT layer if the challenge resources provide it. The archived reference currently marks this layer as pending. Until a valid layer is supplied, show a clear pending or unavailable status. Do not infer a treatment from another source.

### 6. Outputs

Generate one JSON record and one readable property card for each test property.

Each output must show:

- Property identifier and input details.
- Market summary and comparable count.
- Confidence level and its reason.
- Transit and facility results.
- POT status.
- Missing fields, data quality counts, and coordinate precision.
- Data sources and parameter version.

Store generated files under the team folder. Keep generated results separate from source data.

## Implementation shape

Build an independent Python pipeline in the team folder. Use the archived code only as a read-only reference. Use its data, documentation, parameters, templates, and manual results as inputs and validation sources.

Use `python src/mvp.py` for local runs. The Colab notebook calls the same entry point. Provide one notebook for a guided run in Colab. Keep local execution available where the existing Python setup supports it.

Use Markdown for the readable property card. Do not build a separate web application for the MVP.

## What is out of scope

- Scraping property portals or collecting live listings.
- Using real investment opportunities or personal data.
- Giving buy, sell, investment, or return recommendations.
- Predicting a property's sale price or future market value.
- Connecting to Venture One systems, private databases, or internal models.
- Building user accounts, access controls, a production database, or cloud services.
- Building a full dashboard, interactive map, or mobile application.
- Automatically downloading or reconstructing missing geographic layers.
- Filling missing source data with guesses or external assumptions.
- Adding a manual data-entry flow during the MVP.
- Supporting markets, cities, or data formats beyond the supplied challenge sample.

## Known data limits

- The reference data contains asking prices, not confirmed closing prices.
- Listing dates are missing from the sample.
- Some test property coordinates represent a neighborhood, not an exact address.
- The POT treatment layer is pending in the archived reference.
- Transit and facility counts depend on coverage in the supplied geographic data.

Show these limits in the property card when they affect a result.

## Acceptance criteria

The MVP is ready for review when:

1. It creates one JSON record and one readable card for each of the 11 supplied test properties.
2. It matches the provided manual calculations for INM-04, INM-06, and INM-09 under the supplied parameters.
3. It reports missing, invalid, and duplicate data without hiding those issues.
4. It labels approximate coordinates and unavailable POT results.
5. It can reproduce results from the supplied input files and parameter version.
6. It marks unsupported results as insufficient data and gives the reason.
7. It keeps valid independent results when another section lacks enough data.
8. It makes no unsupported claims when the input data is incomplete.

## Ideas after the MVP

- Add a manual data-entry flow for missing information. Validate each new value and record its source. Consider this only after the MVP works with the supplied data.

## KISS rule

Add a feature only when it is needed to produce a correct, clear, and traceable property card from the supplied challenge data.

## Source references

- `../resources/additional/10.pdf`, pages 1 and 2, defines the challenge problem, resources, and usage limits.
- `../resources/venture-one-reference/README.md` describes the sample data, notebook, local commands, and known missing POT layer.
- `../resources/venture-one-reference/docs/plantilla_ficha.md` defines the expected property card fields.
- `../resources/venture-one-reference/config/parametros.yaml` contains the reference calculation parameters.
- `../resources/venture-one-reference/validacion/calculo_manual.md` documents the three manual examples.
