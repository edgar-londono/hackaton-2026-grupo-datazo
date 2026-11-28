"""Run the complete supplied-data MVP pipeline."""

from __future__ import annotations

import json
import hashlib
import math
import sys
import argparse
from collections import Counter
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

if __package__:
    from .data_loader import DATA_DIR, PROJECT_ROOT, load_inputs
    from .data_preparation import normalize_conditions
    from .data_quality import generate_report, inspect_quality
    from .geospatial_preparation import prepare_geospatial_data
    from .market_analysis import analyze_market
    from .neighborhood_analysis import analyze_neighborhood
    from .parameters import load_parameters
    from .property_card import render_card
else:
    from data_loader import DATA_DIR, PROJECT_ROOT, load_inputs
    from data_preparation import normalize_conditions
    from data_quality import generate_report, inspect_quality
    from geospatial_preparation import prepare_geospatial_data
    from market_analysis import analyze_market
    from neighborhood_analysis import analyze_neighborhood
    from parameters import load_parameters
    from property_card import render_card


OUTPUT_DIR = PROJECT_ROOT / "output"
CARDS_DIR = OUTPUT_DIR / "cards"
RECORDS_DIR = OUTPUT_DIR / "fichas"
VALIDATION_REPORT = OUTPUT_DIR / "validation_report.md"
MANUAL_EXPECTED_PATH = PROJECT_ROOT.parent / "resources" / "venture-one-reference" / "validacion" / "esperado.json"


def build_records(include_candidates: Optional[bool] = None) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Prepare all supplied inputs and return one record per test property."""
    generate_report(include_candidates)
    prepare_geospatial_data()
    inputs = load_inputs()
    parameters = load_parameters()
    quality = inspect_quality(inputs, parameters, include_candidates)
    normalized_properties = normalize_conditions(inputs.properties, parameters["estados"])
    valid_listings = quality.prepared_listings.rows
    transit = _read_geojson(OUTPUT_DIR / "prepared" / "geo" / "transporte_limpio.geojson")
    facilities = _read_geojson(OUTPUT_DIR / "prepared" / "geo" / "equipamientos_limpios.geojson")
    transit_metadata = _read_geojson(DATA_DIR / "geo" / "transporte.geojson").get("metadata", {})
    facility_metadata = _read_geojson(DATA_DIR / "geo" / "equipamientos.geojson").get("metadata", {})
    layer_date = transit_metadata.get("fecha_osm") or facility_metadata.get("fecha_osm")
    parameter_version = str(parameters.get("version", "unknown"))

    records = []
    for property_row in normalized_properties:
        record = _build_record(
            property_row,
            inputs.listings,
            valid_listings,
            quality,
            parameters,
            transit,
            facilities,
            layer_date,
            parameter_version,
        )
        records.append(record)
    input_ids = [_clean(row.get("id_inmueble")) for row in inputs.properties]
    output_ids = [record.get("id_inmueble") for record in records]
    if len(records) != len(input_ids) or sorted(output_ids) != sorted(input_ids):
        raise ValueError("The output records do not match the supplied test-property identifiers.")
    coverage = _listing_coverage(inputs.listings, quality)
    return records, coverage


def _listing_coverage(listings: list[dict[str, Any]], quality: Any) -> dict[str, int]:
    candidates = {item.row_number for item in quality.deduplication.for_review}
    removed = {item.row_number for item in quality.deduplication.removed}
    retained = set(quality.deduplication.source_row_numbers)
    selected = set(quality.prepared_listings.source_row_numbers)
    if len(removed) + len(retained) != len(listings):
        raise ValueError("Retained and exact duplicate rows do not account for all listings.")
    return {
        "rows_received": len(listings),
        "rows_retained": len(retained),
        "exact_duplicates_removed": len(removed),
        "possible_repeat_rows": len(candidates),
        "possible_repeat_groups": len({item.first_row_number for item in quality.deduplication.for_review}),
        "possible_repeat_rows_in_calculation": len(candidates & selected),
        "candidate_option_included": int(quality.include_candidates),
        "rows_with_data_issues": len({issue.row_number for issue in quality.exclusions if issue.dataset == "Listings"}),
    }


def _build_record(
    property_row: dict[str, Any],
    input_listings: list[dict[str, Any]],
    valid_listings: list[dict[str, Any]],
    quality: Any,
    parameters: dict[str, Any],
    transit: dict[str, Any],
    facilities: dict[str, Any],
    layer_date: Any,
    parameter_version: str,
) -> dict[str, Any]:
    market, zone_quality = analyze_market(property_row, input_listings, valid_listings, quality, parameters)
    neighborhood = analyze_neighborhood(property_row, transit, facilities, parameters)
    condition = property_row.get("estado_canonico")
    lat = _valid_coordinate(property_row.get("lat"), -90, 90)
    lon = _valid_coordinate(property_row.get("lon"), -180, 180)
    matched_source = _match_source_listing(property_row, input_listings)
    municipality = _clean(property_row.get("municipio"))
    zoning = _zoning_status(municipality, parameters)
    missing: set[str] = set()
    if not _clean(property_row.get("direccion")):
        missing.add("direccion")
    if property_row.get("precision_coordenadas") == "barrio":
        missing.add("coordenadas_exactas")
    if matched_source is None or not _clean(matched_source.get("estado")):
        # The test-property source condition remains available in the input itself.
        source_condition = _clean(property_row.get("estado"))
    else:
        source_condition = _clean(matched_source.get("estado"))
    if not source_condition:
        missing.add("estado")
    if not any(_clean(row.get("fecha")) for row in input_listings):
        missing.add("fecha_publicacion_comparables")
    if not any(_text(row.get("tipo_precio")) == "cierre" for row in input_listings):
        missing.add("precios_de_cierre")
    if market["precio_m2"]["n"] == 0:
        missing.add("comparables_insuficientes")
    if lat is None or lon is None:
        missing.add("coordenadas")

    sources = ["data/inmuebles_prueba.csv", "data/anuncios_muestra.csv"]
    if neighborhood.get("estaciones_en_radio") is not None or neighborhood.get("estacion_mas_cercana") is not None:
        sources.append("OpenStreetMap transit layer (ODbL)")
    if neighborhood.get("equipamientos_en_radio") is not None:
        sources.append("OpenStreetMap facility layer (ODbL)")
    if zoning["estado"] == "pendiente_capa":
        sources.append("config/parametros.yaml (POT coverage and missing layer status)")

    return {
        "id_inmueble": _clean(property_row.get("id_inmueble")),
        "inmueble": {
            "direccion": _clean(property_row.get("direccion")),
            "barrio": _clean(property_row.get("barrio")),
            "municipio": municipality,
            "zona": _clean(property_row.get("zona")),
            "area_m2": _number(property_row.get("area_m2")),
            "estado_texto": source_condition,
            "estado": condition if condition != "sin_clasificar" else None,
            "coordenadas": {
                "lat": lat,
                "lon": lon,
                "precision": _clean(property_row.get("precision_coordenadas")),
                "fuente": _clean(property_row.get("fuente_coordenadas")),
            },
        },
        "mercado": market,
        "calidad_datos_zona": zone_quality,
        "entorno": neighborhood,
        "norma": zoning,
        "datos_faltantes": sorted(missing),
        "metadatos": {
            "version_parametros": parameter_version,
            "fecha_generacion": date.today().isoformat(),
            "fecha_capas_osm": layer_date,
            "fuentes": sources,
        },
    }


def _match_source_listing(
    property_row: dict[str, Any], listings: list[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    listing_id, origin = _text(property_row.get("id_anuncio")), _text(property_row.get("origen"))
    by_both = [row for row in listings if _text(row.get("id_anuncio")) == listing_id and _text(row.get("origen")) == origin]
    if len(by_both) == 1:
        return by_both[0]
    by_id = [row for row in listings if listing_id and _text(row.get("id_anuncio")) == listing_id]
    if len(by_id) == 1:
        return by_id[0]
    by_origin = [row for row in listings if origin and _text(row.get("origen")) == origin]
    return by_origin[0] if len(by_origin) == 1 else None


def _zoning_status(municipality: Optional[str], parameters: dict[str, Any]) -> dict[str, Any]:
    zoning_rules = parameters["norma"]
    covered = {_text(value) for value in zoning_rules.get("municipios_cubiertos", [])}
    configured_path = Path(zoning_rules["archivo_pot"])
    pot_path = PROJECT_ROOT / configured_path
    if pot_path.is_file():
        return {
            "tratamiento_pot": None,
            "estado": "capa_disponible_sin_interseccion",
            "motivo": "La capa existe, pero el MVP no ejecuta una intersección espacial de polígonos.",
        }
    if _text(municipality) in covered:
        return {
            "tratamiento_pot": None,
            "estado": "pendiente_capa",
            "motivo": f"Falta el archivo {zoning_rules['archivo_pot']}.",
        }
    return {
        "tratamiento_pot": None,
        "estado": "no_disponible",
        "motivo": f"El municipio {_clean(municipality) or 'no informado'} está fuera de la cobertura configurada para la capa POT.",
    }


def _render_validation(
    records: list[dict[str, Any]],
    coverage: dict[str, int],
    reproducibility: Optional[bool] = None,
) -> str:
    record_ids = {record["id_inmueble"] for record in records}
    manual_results: list[tuple[str, str, str]] = []
    if MANUAL_EXPECTED_PATH.is_file():
        expected = json.loads(MANUAL_EXPECTED_PATH.read_text(encoding="utf-8"))
        for property_id, baseline in expected.get("inmuebles", {}).items():
            current = next((item for item in records if item["id_inmueble"] == property_id), None)
            if current is None:
                manual_results.append((property_id, "FAIL", "Generated record is missing."))
                continue
            actual_market = current["mercado"]["precio_m2"]
            expected_market = baseline["mercado"]
            differences = []
            for field in ("n", "mediana", "promedio", "desviacion", "coef_variacion"):
                if actual_market.get(field) != expected_market.get(field):
                    differences.append(f"market.{field}: reference={expected_market.get(field)}, current={actual_market.get(field)}")
            if current["mercado"]["confianza"]["nivel"] != expected_market.get("confianza"):
                differences.append(f"market.confidence: reference={expected_market.get('confianza')}, current={current['mercado']['confianza']['nivel']}")
            actual_origins = sorted(item.get("origen") or "" for item in current["mercado"]["comparables"])
            expected_origins = sorted(expected_market.get("comparables", []))
            if actual_origins != expected_origins:
                differences.append(f"market.comparables: {len(expected_origins)} reference, {len(actual_origins)} current; row membership differs")
            actual_quality = current["calidad_datos_zona"]
            for field, expected_value in baseline.get("calidad_datos_zona", {}).items():
                actual_field = "anuncios_conservados" if field == "anuncios_validos" else field
                if actual_quality.get(actual_field) != expected_value:
                    differences.append(f"quality.{field}: reference={expected_value}, current={actual_quality.get(actual_field)}")
            actual_geo = current["entorno"]
            expected_geo = baseline.get("entorno", {})
            for field in ("estaciones_en_radio", "equipamientos_en_radio"):
                if actual_geo.get(field) != expected_geo.get(field):
                    differences.append(f"neighborhood.{field}: reference={expected_geo.get(field)}, current={actual_geo.get(field)}")
            actual_station = actual_geo.get("estacion_mas_cercana") or {}
            expected_station = expected_geo.get("estacion_mas_cercana") or {}
            if actual_station.get("nombre") != expected_station.get("nombre"):
                differences.append(f"neighborhood.nearest_station: reference={expected_station.get('nombre')}, current={actual_station.get('nombre')}")
            tolerance = expected.get("_tolerancias", {}).get("distancia_m", 0)
            expected_distance = expected_station.get("distancia_m")
            actual_distance = actual_station.get("distancia_m")
            if expected_distance is not None and (actual_distance is None or abs(actual_distance - expected_distance) > tolerance):
                differences.append(f"neighborhood.nearest_distance: reference={expected_distance}, current={actual_distance}, tolerance={tolerance}")
            expected_zoning = baseline.get("norma", {}).get("estado")
            if current["norma"].get("estado") != expected_zoning:
                differences.append(f"zoning.status: reference={expected_zoning}, current={current['norma'].get('estado')}")
            if sorted(current["datos_faltantes"]) != sorted(baseline.get("datos_faltantes", [])):
                differences.append("missing_data_codes: reference and current lists differ")
            if not differences:
                manual_results.append((property_id, "PASS", "Market and neighborhood values match the supplied manual reference."))
            else:
                manual_results.append((property_id, "DIFFERENCE", "; ".join(differences)))

    validation_errors = _validate_records(records)
    lines = [
        "# MVP validation report",
        "",
        f"- Run date: {date.today().isoformat()}",
        f"- Records generated: {len(records)} of 11 supplied properties.",
        f"- JSON records present: {len([item for item in record_ids if (RECORDS_DIR / f'{item}.json').is_file()])}.",
        f"- Markdown cards present: {len([item for item in record_ids if (CARDS_DIR / f'{item}.md').is_file()])}.",
        "- Run command: `python src/mvp.py`.",
        "- Configuration: `config/parametros.yaml` version " + str(load_parameters().get("version", "unknown")) + ".",
        "- Listing input coverage: "
        f"{coverage['rows_received']} rows received, {coverage['rows_retained']} retained, "
        f"{coverage['exact_duplicates_removed']} exact duplicates removed, "
        f"{coverage['possible_repeat_rows']} possible repeat rows in "
        f"{coverage['possible_repeat_groups']} groups, "
        f"{coverage['possible_repeat_rows_in_calculation']} selected for calculations; "
        f"possible repeats {'included' if coverage['candidate_option_included'] else 'excluded'}.",
        "",
        "## MVP acceptance checks",
        "",
        f"- Record and card contract: {'PASS' if not validation_errors else 'FAIL'}.",
        f"- Checks completed: {len(records)} records, input/output ID match, empty-data behavior, market null rules, coordinate precision flags, and geographic availability.",
        f"- Issues: {'None.' if not validation_errors else '; '.join(validation_errors)}",
        "- Data quality limitations: recorded in each card and in `data_quality.md`; they remain explicit where supplied inputs cannot support a value.",
        "- Repeat-run output hash check: " + ("PASS, generated artifacts matched across two full runs." if reproducibility is True else "FAIL, generated artifacts differed across two full runs." if reproducibility is False else "Not run."),
        "",
        "## Manual reference comparison",
        "",
        "The archived manual examples remove rows by candidate ID or by zone, area, and price. The team removes a row only when every source field matches after whitespace normalization. Case differences remain visible.",
        "Possible repeats remain separate. This run " + ("includes" if coverage["candidate_option_included"] else "excludes") + " candidate rows from calculations. Use `--include-candidates` or `--exclude-candidates` to choose.",
        "",
        "| Property | Result | Details |",
        "|---|---|---|",
    ]
    if manual_results:
        for property_id, status, detail in manual_results:
            lines.append(f"| {property_id} | {status} | {detail} |")
    else:
        lines.append("| All | NOT RUN | Archived manual baseline file was not found. |")

    lines.extend([
        "",
        "## Data sufficiency and limits",
        "",
        "- Every output keeps unsupported numeric values as `null` and includes a reason in the card.",
        "- Listing rows with missing condition or area remain in the source and are excluded from calculations with a recorded reason.",
        "- Candidate rows with differing source columns remain separate in `prepared/posibles_repeticiones.csv`; they are possible repeats, not confirmed duplicates.",
        "- Choose whether possible repeats enter calculations with `--include-candidates` or `--exclude-candidates`. The default comes from `config/parametros.yaml`.",
        "- Candidate groups and original differing values are listed in `prepared/grupos_posibles_repeticiones.csv`.",
        "- Approximate neighborhood coordinates are marked in each affected card.",
        "- The POT layer is not supplied. Covered Medellin records report `pendiente_capa`; Itagui reports `no_disponible`.",
        "- The supplied listing sample has no publication dates and no closing prices. These limits appear in each card.",
        "",
        "## Reproducibility evidence",
        "",
        "This report is generated by the MVP pipeline. Run `python src/mvp.py --repeat-check` to regenerate quality reports, prepared inputs, JSON records, and cards twice, then compare their SHA-256 hashes.",
        "",
    ])
    return "\n".join(lines)


def _validate_records(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if len(records) != 11:
        errors.append(f"Expected 11 records, found {len(records)}")
    ids = [record.get("id_inmueble") for record in records]
    if len(set(ids)) != len(ids):
        errors.append("Duplicate property identifiers were generated")
    for record in records:
        property_id = record.get("id_inmueble") or "<missing id>"
        market = record.get("mercado", {})
        price_summary = market.get("precio_m2", {})
        if price_summary.get("n", 0) == 0:
            numeric_fields = ("mediana", "promedio", "minimo", "maximo", "desviacion", "coef_variacion")
            if any(price_summary.get(field) is not None for field in numeric_fields):
                errors.append(f"{property_id}: unsupported market values must be null")
            if market.get("confianza", {}).get("nivel") is not None:
                errors.append(f"{property_id}: confidence must be null without comparables")
            if "comparables_insuficientes" not in record.get("datos_faltantes", []):
                errors.append(f"{property_id}: missing insufficient-comparables reason")
        elif any(price_summary.get(field) is None for field in ("mediana", "promedio", "minimo", "maximo")):
            errors.append(f"{property_id}: comparable statistics are incomplete")
        coordinates = record.get("inmueble", {}).get("coordenadas", {})
        expected_approximate = coordinates.get("precision") == "barrio"
        if record.get("entorno", {}).get("aproximado") != expected_approximate:
            errors.append(f"{property_id}: coordinate precision flag does not match the input")
        if coordinates.get("lat") is not None and coordinates.get("lon") is not None:
            if record.get("entorno", {}).get("estaciones_en_radio") is None:
                errors.append(f"{property_id}: transit result is unavailable despite valid coordinates")
            if record.get("entorno", {}).get("equipamientos_en_radio") is None:
                errors.append(f"{property_id}: facility result is unavailable despite valid coordinates")
        if record.get("norma", {}).get("estado") not in {
            "encontrado", "fuera_de_capa", "pendiente_capa", "no_disponible", "capa_disponible_sin_interseccion"
        }:
            errors.append(f"{property_id}: unknown POT status")
    errors.extend(_validate_insufficient_data_behavior(load_parameters()))
    return errors


def _validate_insufficient_data_behavior(parameters: dict[str, Any]) -> list[str]:
    """Check that absent market and location inputs stay unsupported in output."""
    empty_quality = SimpleNamespace(
        exclusions=[],
        deduplication=SimpleNamespace(removed=[], for_review=[]),
        prepared_listings=SimpleNamespace(source_row_numbers=[]),
        include_candidates=True,
    )
    sample_property = {
        "id_inmueble": "VALIDATION-EMPTY",
        "id_anuncio": "",
        "origen": "",
        "zona": "zone_without_listings",
        "municipio": "unknown",
        "area_m2": "70",
        "estado_canonico": "habitable",
    }
    market, quality = analyze_market(sample_property, [], [], empty_quality, parameters)
    neighborhood = analyze_neighborhood(
        {"lat": "", "lon": "", "precision_coordenadas": ""},
        None,
        None,
        parameters,
    )
    errors = []
    stats = market["precio_m2"]
    if stats["n"] != 0 or any(stats[field] is not None for field in (
        "mediana", "promedio", "minimo", "maximo", "desviacion", "coef_variacion"
    )):
        errors.append("Empty market input produced unsupported numeric output")
    if market["confianza"]["nivel"] is not None or market["comparables"]:
        errors.append("Empty market input produced confidence or comparable records")
    if neighborhood["estacion_mas_cercana"] is not None or neighborhood["estaciones_en_radio"] is not None:
        errors.append("Missing coordinates produced transit results")
    if neighborhood["equipamientos_en_radio"] is not None:
        errors.append("Missing coordinates produced facility counts")
    if quality["anuncios_en_zona"] != 0 or quality["anuncios_conservados"] != 0:
        errors.append("Empty input produced nonzero zone quality counts")
    return errors


def run() -> int:
    parser = argparse.ArgumentParser(description="Run the supplied-data MVP pipeline.")
    candidate_options = parser.add_mutually_exclusive_group()
    candidate_options.add_argument(
        "--include-candidates",
        action="store_true",
        help="include possible repeat rows in calculations",
    )
    candidate_options.add_argument(
        "--exclude-candidates",
        action="store_true",
        help="exclude possible repeat rows from calculations",
    )
    parser.add_argument("--repeat-check", action="store_true", help="run the pipeline twice and compare outputs")
    args = parser.parse_args()
    repeat_check = args.repeat_check
    include_candidates = True if args.include_candidates else False if args.exclude_candidates else None
    records, coverage = build_records(include_candidates)
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    _write_property_outputs(records)
    reproducibility = None
    if repeat_check:
        first_hashes = _output_hashes()
        second_records, second_coverage = build_records(include_candidates)
        _write_property_outputs(second_records)
        second_hashes = _output_hashes()
        reproducibility = first_hashes == second_hashes and second_coverage == coverage
        records = second_records
    validation_errors = _validate_records(records)
    VALIDATION_REPORT.write_text(_render_validation(records, coverage, reproducibility), encoding="utf-8")
    print(f"Generated {len(records)} property records and cards under output/.")
    print(f"Validation report: {VALIDATION_REPORT.relative_to(PROJECT_ROOT)}")
    if validation_errors:
        print("Validation issues: " + "; ".join(validation_errors))
        return 1
    if reproducibility is False:
        print("Repeat-run hashes did not match.")
        return 1
    return 0


def _write_property_outputs(records: list[dict[str, Any]]) -> None:
    for record in records:
        property_id = record["id_inmueble"]
        if not property_id:
            raise ValueError("A test property has no id_inmueble.")
        (RECORDS_DIR / f"{property_id}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        (CARDS_DIR / f"{property_id}.md").write_text(render_card(record), encoding="utf-8")


def _output_hashes() -> dict[str, str]:
    hashes = {}
    for path in sorted(OUTPUT_DIR.rglob("*")):
        if not path.is_file() or path == VALIDATION_REPORT:
            continue
        relative = path.relative_to(OUTPUT_DIR).as_posix()
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _read_geojson(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_coordinate(value: Any, minimum: float, maximum: float) -> Optional[float]:
    number = _number(value)
    if number is None or not minimum <= number <= maximum:
        return None
    return number


def _number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None


def _text(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


if __name__ == "__main__":
    sys.exit(run())
