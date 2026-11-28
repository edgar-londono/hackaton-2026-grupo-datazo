# MVP checklist

Use this checklist with [mvp_plan.md](mvp_plan.md). It has no task assignments by role.

## How to use this checklist

- Complete an item only after its deliverable exists and its completion rule passes.
- Add a link or path in each item's evidence field.
- Complete a phase after its deliverable exists and every child item is complete.
- Keep a parent item open when any child item is open.
- Do not mark unsupported data as valid to complete an item.

## 1. Confirm scope and source rules

- [x] **1. Confirm the MVP scope.**
  - Deliverable: accepted scope in `mvp_plan.md`.
  - Done when: the team agrees on the goal, outputs, limits, and acceptance criteria.
  - Evidence: `mvp_plan.md`
  - [x] **1.1 Build an independent solution.**
    - Deliverable: source-use rule in `mvp_plan.md`.
    - Done when: the team solution does not import or copy the archived `src/ficha/` or `scripts/` implementation.
    - Evidence: `mvp_plan.md`
  - [x] **1.2 Define allowed reference materials.**
    - Deliverable: source-use rule in `mvp_plan.md`.
    - Done when: the team may use archived data, documentation, parameters, templates, and manual results, while keeping the archive unchanged.
    - Evidence: `mvp_plan.md`
  - [x] **1.3 Define the insufficient-data behavior.**
    - Deliverable: data sufficiency rule in `mvp_plan.md`.
    - Done when: unsupported values remain null, the card states the reason, and valid independent sections remain visible.
    - Evidence: `mvp_plan.md`
  - [x] **1.4 Keep manual data entry after the MVP.**
    - Deliverable: post-MVP idea in `mvp_plan.md`.
    - Done when: the MVP has no form or workflow for entering missing values.
    - Evidence: `mvp_plan.md`

## 2. Prepare the required inputs

- [x] **2. Prepare a traceable input set.**
  - Deliverable: copied inputs and `data/source_manifest.md`.
  - Done when: every input has a source path and the archived source remains unchanged.
  - Evidence: `data/source_manifest.md` and `docs/output_contract.md`
  - [x] **2.1 Copy the listing sample.**
    - Deliverable: `data/anuncios_muestra.csv`.
    - Done when: the copy matches the supplied source file and its source path appears in the manifest.
    - Evidence: `data/anuncios_muestra.csv` and `data/source_manifest.md`
  - [x] **2.2 Copy the test properties.**
    - Deliverable: `data/inmuebles_prueba.csv`.
    - Done when: the copy contains all supplied test properties and its source path appears in the manifest.
    - Evidence: `data/inmuebles_prueba.csv` and `data/source_manifest.md`
  - [x] **2.3 Copy the geographic layers.**
    - Deliverable: `data/geo/transporte.geojson` and `data/geo/equipamientos.geojson`.
    - Done when: both files match their supplied sources and appear in the manifest.
    - Evidence: `data/geo/transporte.geojson`, `data/geo/equipamientos.geojson`, and `data/source_manifest.md`
  - [x] **2.4 Copy the calculation parameters.**
    - Deliverable: `config/parametros.yaml`.
    - Done when: the copied file preserves the supplied version and values.
    - Evidence: `config/parametros.yaml` and `data/source_manifest.md`
  - [x] **2.5 Keep the missing POT layer explicit.**
    - Deliverable: input manifest entry for the absent POT layer.
    - Done when: the manifest states that the archived source marks this layer as pending and no substitute layer is added.
    - Evidence: `data/source_manifest.md` and `../resources/venture-one-reference/README.md`
  - [x] **2.6 Record the output contract.**
    - Deliverable: `docs/output_contract.md` based on the supplied template and example.
    - Done when: the JSON fields and readable card fields are mapped to source data or marked as unavailable.
    - Evidence: `docs/output_contract.md`

## 3. Set up the smallest runnable solution

- [x] **3. Create a reproducible project structure.**
  - Deliverable: team code, input, configuration, output, and notebook folders.
  - Done when: every project file lives under `grupo-datazo/` and reference files remain unchanged.
  - Evidence: `src/`, `data/`, `config/`, `output/`, and `notebooks/`
  - [x] **3.1 Create the Python entry point.**
    - Deliverable: `src/mvp.py` and a documented run command.
    - Done when: the entry point starts the completed pipeline. Verify the full run under item 8.4.
    - Evidence: `src/mvp.py` and `setup.md`
    - [x] **3.1.1 Set the run command.**
      - Deliverable: command and Colab path in `mvp_plan.md`.
      - Done when: local runs use `python src/mvp.py` and Colab calls the same entry point.
      - Evidence: `mvp_plan.md`
    - [x] **3.1.2 Implement the entry point.**
      - Deliverable: working `src/mvp.py`.
      - Done when: the documented command starts the completed pipeline.
      - Evidence: `src/mvp.py`, `src/market_analysis.py`, and `src/neighborhood_analysis.py`
  - [x] **3.2 Keep rules in the parameter file.**
    - Deliverable: pipeline reads `config/parametros.yaml`.
    - Done when: area tolerance, valid price range, confidence thresholds, and search radius come from configuration.
    - Evidence: `src/parameters.py`, `src/market_analysis.py`, and `src/neighborhood_analysis.py`
  - [x] **3.3 Define the minimal runtime requirements.**
    - Deliverable: `requirements.txt` and a short setup note.
    - Done when: a clean environment can install only the packages needed to run the pipeline.
    - Evidence: `requirements.txt` and `setup.md`
  - [x] **3.4 Use one calculation path.**
    - Deliverable: notebook calls the same pipeline entry point.
    - Done when: notebook cells do not contain a second copy of market or geographic calculation rules.
    - Evidence: `notebooks/mvp_colab.ipynb` calls `python src/mvp.py`

## 4. Validate and prepare the source data

- [x] **4. Produce a quality report for the inputs.**
  - Deliverable: `output/data_quality.md`.
  - Done when: the report lists row counts, missing fields, invalid rows, and duplicate counts by reason.
  - Evidence: `output/data_quality.md` and `output/prepared/`
  - [x] **4.1 Load the supplied files.**
    - Deliverable: input-loading code and a successful load record.
    - Done when: both CSV files and both GeoJSON files load from the team folder.
    - Evidence: `src/data_loader.py` and `output/input_load.md`
  - [x] **4.2 Validate required fields and values.**
    - Deliverable: validation results in `output/data_quality.md`.
    - Done when: missing fields, invalid numbers, and out-of-range prices have clear reasons.
    - Evidence: `src/data_quality.py` and `output/data_quality.md`
  - [x] **4.3 Normalize property conditions.**
    - Deliverable: normalized condition mapping in the pipeline.
    - Done when: supplied mappings create the three canonical conditions and unmapped values remain unclassified.
    - Evidence: `src/data_preparation.py` and `output/data_quality.md`
  - [x] **4.4 Remove only exact full-row duplicates.**
    - Deliverable: exact duplicate report and possible-repeat files.
    - Done when: every field matches after whitespace and numeric formatting cleanup. Case and accent differences remain visible. Partial matches stay separate.
    - Evidence: `src/data_preparation.py`, `output/prepared/anuncios_sin_duplicados.csv`, `output/prepared/posibles_repeticiones.csv`, and `output/prepared/grupos_posibles_repeticiones.csv`
  - [x] **4.5 Keep both candidate calculation options.**
    - Deliverable: include and exclude options with a recorded default.
    - Done when: the run supports `--include-candidates` and `--exclude-candidates`, and its report records the selected option.
    - Evidence: `src/mvp.py`, `src/data_quality.py`, `config/parametros.yaml`, and `output/validation_report.md`
  - [x] **4.6 Track field-level data limits.**
    - Deliverable: one audit row for each of the 1,638 source field values.
    - Done when: each value is marked missing, safely normalized, invalid, source-reported, officially confirmed, or corrected with evidence. Missing fields affect only dependent calculations.
    - Evidence: `src/data_quality.py`, `data/anuncios_verificaciones.csv`, and `output/prepared/auditoria_campos_anuncios.csv`

## 5. Calculate the market summary

- [x] **5. Generate a comparable summary for each test property.**
  - Deliverable: market results in the property JSON files.
  - Done when: each property has supported values or an explicit insufficient-data status.
  - Evidence: `output/fichas/` and `output/validation_report.md`
  - [x] **5.1 Select the same market zone.**
    - Deliverable: comparable-selection output.
    - Done when: candidates from other zones do not enter that property's market calculation.
    - Evidence: `src/market_analysis.py` and the `comparables` arrays in `output/fichas/`
  - [x] **5.2 Match the canonical property condition.**
    - Deliverable: comparable-selection output.
    - Done when: only records with the same mapped condition enter the calculation.
    - Evidence: `config/parametros.yaml`, `src/market_analysis.py`, and `output/fichas/`
  - [x] **5.3 Apply configured area and price rules.**
    - Deliverable: filter results with excluded-row reasons.
    - Done when: the pipeline applies the supplied area tolerance and valid price range.
    - Evidence: `src/market_analysis.py` and `output/fichas/`
  - [x] **5.4 Exclude the test property's own listing when required.**
    - Deliverable: comparable list for each property.
    - Done when: the property does not appear as its own comparable under the reference rules.
    - Evidence: `src/market_analysis.py` and `output/fichas/`
  - [x] **5.5 Calculate the configured market statistics.**
    - Deliverable: price-per-square-meter statistics.
    - Done when: count, median, range, mean, deviation, and coefficient of variation follow the supplied template and calculation rules.
    - Evidence: `src/market_analysis.py`, `config/parametros.yaml`, and `output/fichas/`
  - [x] **5.6 Assign the confidence level.**
    - Deliverable: confidence value and explanation per property.
    - Done when: the supplied confidence thresholds determine high, medium, or low confidence.
    - Evidence: `src/market_analysis.py` and `output/validation_report.md`
  - [x] **5.7 Handle unsupported market results.**
    - Deliverable: insufficient-data result example.
    - Done when: zero valid comparables produce no invented statistic and state the reason and missing fields.
    - Evidence: empty-data behavior in `src/mvp.py` and `output/validation_report.md`
  - [x] **5.8 Keep low confidence distinct from missing data.**
    - Deliverable: result for a small valid sample.
    - Done when: calculable statistics remain visible with low confidence instead of being reported as missing.
    - Evidence: INM-04 in `output/fichas/INM-04.json` and `output/cards/INM-04.md`

## 6. Calculate the neighborhood summary

- [x] **6. Generate supported geographic results for each test property.**
  - Deliverable: neighborhood fields in the property JSON files.
  - Done when: each geographic result is exact, approximate, or explicitly unavailable.
  - Evidence: `output/fichas/` and `output/validation_report.md`
  - [x] **6.1 Check coordinate values and precision.**
    - Deliverable: coordinate validation results.
    - Done when: invalid or absent coordinates do not produce distances or counts.
    - Evidence: `src/neighborhood_analysis.py` and `output/fichas/`
  - [x] **6.2 Find the nearest supported transit station.**
    - Deliverable: nearest-station result with system and distance.
    - Done when: distance uses the documented Haversine method, supplied coordinates, and configured transit systems.
    - Evidence: `config/parametros.yaml`, `src/neighborhood_analysis.py`, and the manual comparison in `output/validation_report.md`
  - [x] **6.3 Count stations and facilities in the configured radius.**
    - Deliverable: category counts for each property.
    - Done when: the configured radius and category mappings control the counts.
    - Evidence: `output/fichas/` and `output/cards/`
  - [x] **6.4 Mark approximate coordinates.**
    - Deliverable: approximate flag in JSON and card.
    - Done when: neighborhood-level coordinates are clearly labeled approximate.
    - Evidence: approximate precision flags in `output/fichas/` and `output/cards/`
  - [x] **6.5 Report missing geographic results honestly.**
    - Deliverable: unavailable-result example.
    - Done when: missing coordinates or layers produce an explanation and no fabricated value.
    - Evidence: empty-coordinate behavior in `src/mvp.py` and `output/validation_report.md`
  - [x] **6.6 Report the POT layer as pending.**
    - Deliverable: POT status in each property output.
    - Done when: the output shows pending or unavailable and gives the reason from the supplied inputs.
    - Evidence: `src/mvp.py` and the POT status in `output/fichas/`

## 7. Generate the property outputs

- [x] **7. Create one JSON record and one readable card per property.**
  - Deliverable: `output/fichas/` and `output/cards/`.
  - Done when: each of the 11 test properties has both output files.
  - Evidence: `output/fichas/` and `output/cards/`
  - [x] **7.1 Match the supplied JSON contract.**
    - Deliverable: one schema-aligned JSON record per property.
    - Done when: all required fields use the supplied names and types.
    - Evidence: `docs/output_contract.md` and `output/fichas/`
  - [x] **7.2 Render the readable card in Markdown.**
    - Deliverable: one Markdown card per property.
    - Done when: a reader can identify the property, market result, neighborhood result, quality, sources, and limits.
    - Evidence: `src/property_card.py` and `output/cards/`
  - [x] **7.3 Show missing, invalid, and approximate data.**
    - Deliverable: data quality and status fields in JSON and cards.
    - Done when: unsupported values stay empty and each affected section explains why.
    - Evidence: `output/fichas/` and `output/cards/`
  - [x] **7.4 Record sources and parameter version.**
    - Deliverable: source and version metadata in JSON and cards.
    - Done when: each output names the data source and parameter version used.
    - Evidence: `output/fichas/` and `output/cards/`
  - [x] **7.5 Keep generated files separate from inputs.**
    - Deliverable: outputs stored under `output/`.
    - Done when: a run does not modify supplied or copied input files.
    - Evidence: `src/mvp.py` writes only under `output/`

## 8. Validate the complete MVP

- [x] **8. Confirm correctness and reproducibility.**
  - Deliverable: `output/validation_report.md`.
  - Done when: the report links results to manual examples, test properties, and run details.
  - Evidence: `output/validation_report.md`
  - [x] **8.1 Compare the three manual examples.**
    - Deliverable: comparison for INM-04, INM-06, and INM-09.
    - Done when: every difference from the supplied manual values is explained or corrected.
    - Evidence: manual comparison table in `output/validation_report.md`
  - [x] **8.2 Generate all 11 property outputs.**
    - Deliverable: full JSON and Markdown output set.
    - Done when: all test IDs have both files and no run error remains.
    - Evidence: all 11 files in `output/fichas/` and `output/cards/`
  - [x] **8.3 Check insufficient-data and invalid-data cases.**
    - Deliverable: validation records for missing, invalid, and sparse inputs.
    - Done when: no unsupported value appears as a valid result and valid independent sections remain visible.
    - Evidence: `output/data_quality.md`, `output/validation_report.md`, and the empty-input validation path in `src/mvp.py`
  - [x] **8.4 Repeat the run from the documented setup.**
    - Deliverable: run log with command, environment, input version, and parameter version.
    - Done when: another team member can reproduce the output from the instructions.
    - Evidence: SHA-256 repeat-run result in `output/validation_report.md`

## 9. Prepare the demonstration and handoff

- [ ] **9. Make the MVP easy to run and review.**
  - Deliverable: working notebook and `README.md` in the team folder.
  - Done when: the demonstration starts from the supplied inputs and shows the final outputs.
  - Evidence: [add link or path]
  - [ ] **9.1 Run the guided notebook from start to finish.**
    - Deliverable: completed notebook run.
    - Done when: it uses the team's pipeline and produces the same outputs as the documented command.
    - Evidence: [add link or path]
  - [ ] **9.2 Document local setup and execution.**
    - Deliverable: team `README.md` instructions.
    - Done when: setup, run, output, and validation steps are clear and reproducible.
    - Evidence: [add link or path]
  - [ ] **9.3 Link the evidence to this checklist.**
    - Deliverable: evidence paths filled for completed items.
    - Done when: every checked item has a reviewable artifact.
    - Evidence: [add link or path]

## Post-MVP ideas

Review this idea only after the MVP acceptance criteria pass:

- Manual entry for missing information, with validation and source tracking.
