import csv
import json
import math
from datetime import date
from collections import Counter
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

if __package__:
    from .data_loader import LoadedInputs, load_inputs
    from .parameters import load_parameters
    from .data_preparation import (
        DeduplicationResult,
        PreparedRows,
        UNCLASSIFIED,
        count_conditions,
        deduplicate_listings,
        normalize_conditions,
        normalize_output_text,
        normalize_text_for_comparison,
        prepare_valid_rows,
    )
else:
    from data_loader import LoadedInputs, load_inputs
    from parameters import load_parameters
    from data_preparation import (
        DeduplicationResult,
        PreparedRows,
        UNCLASSIFIED,
        count_conditions,
        deduplicate_listings,
        normalize_conditions,
        normalize_output_text,
        normalize_text_for_comparison,
        prepare_valid_rows,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "output" / "data_quality.md"
PREPARED_DIR = PROJECT_ROOT / "output" / "prepared"
DEDUPLICATED_PATH = PREPARED_DIR / "anuncios_sin_duplicados.csv"
SELECTED_LISTINGS_PATH = PREPARED_DIR / "anuncios_seleccionados.csv"
VALID_PROPERTIES_PATH = PREPARED_DIR / "inmuebles_validos.csv"
ISSUES_PATH = PREPARED_DIR / "incidencias_datos.csv"
DUPLICATE_REVIEW_PATH = PREPARED_DIR / "posibles_repeticiones.csv"
REVIEW_GROUP_SUMMARY_PATH = PREPARED_DIR / "grupos_posibles_repeticiones.csv"
NORMALIZATION_AUDIT_PATH = PREPARED_DIR / "normalizacion_texto.csv"
LISTING_FIELD_AUDIT_PATH = PREPARED_DIR / "auditoria_campos_anuncios.csv"
LISTING_VERIFICATIONS_PATH = PROJECT_ROOT / "data" / "anuncios_verificaciones.csv"

LISTING_REQUIRED_FIELDS = (
    "zona",
    "municipio",
    "area_m2",
    "precio",
    "tipo_precio",
    "origen",
)
PROPERTY_REQUIRED_FIELDS = (
    "id_inmueble",
    "origen",
    "zona",
    "municipio",
    "area_m2",
    "estado",
    "lat",
    "lon",
    "precision_coordenadas",
    "fuente_coordenadas",
)


@dataclass(frozen=True)
class QualityIssue:
    dataset: str
    row_number: int
    record_id: str
    field: str
    reason: str
    value: str
    kind: str


@dataclass(frozen=True)
class QualitySummary:
    listing_count: int
    property_count: int
    missing_fields: dict[str, Counter[str]]
    invalid_values: list[QualityIssue]
    missing_listing_states: list[QualityIssue]
    out_of_range_prices: list[QualityIssue]
    price_range: tuple[float, float]
    price_calculations: int
    invalid_numeric_count: int
    normalized_conditions: dict[str, Counter[str]]
    deduplication: DeduplicationResult
    exclusions: list[QualityIssue]
    prepared_listings: PreparedRows
    prepared_properties: PreparedRows
    include_candidates: bool
    verifications: list[dict[str, str]]


def _load_listing_verifications(
    source_rows: list[dict[str, Any]],
    retained_row_numbers: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    verified_rows = {
        row_number: dict(source_rows[row_number - 2])
        for row_number in retained_row_numbers
    }
    if not LISTING_VERIFICATIONS_PATH.exists():
        return list(verified_rows.values()), []

    required_columns = {
        "csv_row", "field", "original_value", "result_value", "status",
        "source_url", "source_record_id", "license", "checked_on", "rule",
        "snapshot_path",
    }
    seen: set[tuple[int, str]] = set()
    verifications: list[dict[str, str]] = []
    with LISTING_VERIFICATIONS_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                "data/anuncios_verificaciones.csv is missing required evidence columns."
            )
        for line_number, evidence in enumerate(reader, start=2):
            if not any((value or "").strip() for value in evidence.values()):
                continue
            try:
                row_number = int(evidence["csv_row"])
            except (TypeError, ValueError) as error:
                raise ValueError(f"Verification row {line_number} has an invalid csv_row.") from error
            field = evidence["field"].strip()
            key = (row_number, field)
            if key in seen:
                raise ValueError(f"Duplicate verification for CSV row {row_number}, field {field}.")
            seen.add(key)
            if row_number not in verified_rows:
                raise ValueError(f"Verification points to removed or unknown CSV row {row_number}.")
            if field not in verified_rows[row_number]:
                raise ValueError(f"Verification uses unknown listing field {field!r}.")
            original = evidence["original_value"]
            actual = source_rows[row_number - 2].get(field)
            if original != ("" if actual is None else str(actual)):
                raise ValueError(f"Verification source value does not match CSV row {row_number}, field {field}.")
            status = evidence["status"].strip()
            result_value = evidence["result_value"]
            if status not in {"confirmed", "corrected"} or not result_value:
                raise ValueError(f"Verification row {line_number} needs a confirmed or corrected value.")
            if status == "confirmed" and result_value != original:
                raise ValueError(f"Confirmed value differs from the source in CSV row {row_number}, field {field}.")
            if status == "corrected" and result_value == original:
                raise ValueError(f"Corrected value matches the source in CSV row {row_number}, field {field}.")
            source_url = evidence["source_url"].strip()
            source_host = (urlparse(source_url).hostname or "").lower()
            required_evidence = (
                evidence["source_record_id"], evidence["license"],
                evidence["checked_on"], evidence["rule"], evidence["snapshot_path"],
            )
            if (
                not source_url.startswith("https://")
                or not (source_host == "gov.co" or source_host.endswith(".gov.co"))
                or any(not value.strip() for value in required_evidence)
            ):
                raise ValueError(f"Verification row {line_number} has incomplete source evidence.")
            try:
                date.fromisoformat(evidence["checked_on"].strip())
            except ValueError as error:
                raise ValueError(f"Verification row {line_number} needs an ISO date.") from error
            verified_rows[row_number][field] = result_value
            verifications.append({**evidence, "csv_row": str(row_number), "field": field})

    return [verified_rows[row] for row in retained_row_numbers], verifications


def inspect_quality(
    inputs: LoadedInputs,
    parameters: dict[str, Any],
    include_candidates: Optional[bool] = None,
) -> QualitySummary:
    missing_fields: dict[str, Counter[str]] = {
        "Listings": Counter(),
        "Test properties": Counter(),
    }
    invalid_values: list[QualityIssue] = []
    missing_listing_states: list[QualityIssue] = []
    out_of_range_prices: list[QualityIssue] = []
    accepted_price_types = parameters["comparables"]["tipos_precio"]
    price_min, price_max = parameters["comparables"]["rango_precio_m2_valido"]
    price_calculations = 0
    deduplication = deduplicate_listings(
        inputs.listings, parameters["deduplicacion"]
    )
    verified_rows, verifications = _load_listing_verifications(
        inputs.listings, deduplication.source_row_numbers
    )
    verified_by_row = {
        row_number: row
        for row_number, row in zip(deduplication.source_row_numbers, verified_rows)
    }
    deduplication = replace(
        deduplication,
        rows=[
            {field: normalize_output_text(value) for field, value in row.items()}
            for row in verified_rows
        ],
    )
    if include_candidates is None:
        include_candidates = bool(
            parameters["deduplicacion"].get("incluir_candidatos_en_calculos", True)
        )
    condition_rules = parameters["estados"]
    normalized_conditions = {
        "Listings": count_conditions(
            [verified_by_row[row] for row in deduplication.source_row_numbers],
            condition_rules,
        ),
        "Test properties": count_conditions(inputs.properties, condition_rules),
    }

    _count_missing(inputs.listings, LISTING_REQUIRED_FIELDS, missing_fields["Listings"])
    _count_missing(inputs.properties, PROPERTY_REQUIRED_FIELDS, missing_fields["Test properties"])

    for row_number, source_row in enumerate(inputs.listings, start=2):
        row = verified_by_row.get(row_number, source_row)
        record_id = _record_id(row, "id_anuncio", "origen")
        _check_required_text(
            "Listings", row_number, row, record_id, LISTING_REQUIRED_FIELDS, invalid_values
        )
        area = _check_number(
            "Listings", row_number, row, record_id, "area_m2", invalid_values, minimum=0
        )
        price = _check_number(
            "Listings", row_number, row, record_id, "precio", invalid_values, minimum=0
        )
        _check_optional_integer(
            "Listings", row_number, row, record_id, "habitaciones", invalid_values
        )
        _check_optional_integer("Listings", row_number, row, record_id, "banos", invalid_values)

        price_type = row.get("tipo_precio")
        if not _is_missing(price_type) and price_type not in accepted_price_types:
            invalid_values.append(
                _issue(
                    "Listings",
                    row_number,
                    record_id,
                    "tipo_precio",
                    "Value is not listed in config/parametros.yaml.",
                    price_type,
                    "category",
                )
            )

        if _is_missing(row.get("estado")):
            missing_listing_states.append(
                _issue(
                    "Listings",
                    row_number,
                    record_id,
                    "estado",
                    "Cannot match this listing to a canonical condition.",
                    "",
                    "condition",
                )
            )

        if area is not None and price is not None:
            price_calculations += 1
            price_per_m2 = price / area
            if not price_min <= price_per_m2 <= price_max:
                out_of_range_prices.append(
                    _issue(
                        "Listings",
                        row_number,
                        record_id,
                        "precio / area_m2",
                        f"Value is outside the configured range "
                        f"{price_min:,.0f} to {price_max:,.0f} COP/m2.",
                        f"{price_per_m2:.2f}",
                        "range",
                    )
                )

    for row_number, row in enumerate(inputs.properties, start=2):
        record_id = _record_id(row, "id_inmueble")
        _check_required_text(
            "Test properties",
            row_number,
            row,
            record_id,
            PROPERTY_REQUIRED_FIELDS,
            invalid_values,
        )
        _check_number(
            "Test properties", row_number, row, record_id, "area_m2", invalid_values, minimum=0
        )
        _check_number(
            "Test properties",
            row_number,
            row,
            record_id,
            "lat",
            invalid_values,
            minimum=-90,
            maximum=90,
            minimum_inclusive=True,
        )
        _check_number(
            "Test properties",
            row_number,
            row,
            record_id,
            "lon",
            invalid_values,
            minimum=-180,
            maximum=180,
            minimum_inclusive=True,
        )

        precision = row.get("precision_coordenadas")
        if not _is_missing(precision) and precision not in ("cruce", "barrio"):
            invalid_values.append(
                _issue(
                    "Test properties",
                    row_number,
                    record_id,
                    "precision_coordenadas",
                    "Value must be cruce or barrio, as defined in the data dictionary.",
                    precision,
                    "category",
                )
            )

    normalized_deduplicated = normalize_conditions(
        deduplication.rows, condition_rules
    )
    condition_issues: list[QualityIssue] = []
    for row_number, row in zip(
        deduplication.source_row_numbers, normalized_deduplicated
    ):
        if row["estado_canonico"] == UNCLASSIFIED and not _is_missing(row.get("estado")):
            condition_issues.append(
                _issue(
                    "Listings", row_number, _record_id(row, "origen"), "estado",
                    "Condition is unmapped and remains sin_clasificar.", row.get("estado"),
                    "condition",
                )
            )

    property_source_rows = list(range(2, len(inputs.properties) + 2))
    normalized_properties = normalize_conditions(inputs.properties, condition_rules)
    for row_number, row in zip(property_source_rows, normalized_properties):
        if row["estado_canonico"] == UNCLASSIFIED and not _is_missing(row.get("estado")):
            condition_issues.append(
                _issue(
                    "Test properties", row_number, _record_id(row, "id_inmueble"),
                    "estado", "Condition is unmapped and remains sin_clasificar.",
                    row.get("estado"), "condition",
                )
            )

    retained_listing_rows = set(deduplication.source_row_numbers)
    base_exclusions = invalid_values + out_of_range_prices + missing_listing_states
    exclusions = [
        issue for issue in base_exclusions
        if issue.dataset == "Test properties"
        or issue.row_number in retained_listing_rows
    ] + condition_issues
    candidate_rows = {item.row_number for item in deduplication.for_review}
    excluded_listing_rows = candidate_rows if not include_candidates else set()
    excluded_property_rows = {
        issue.row_number for issue in exclusions if issue.dataset == "Test properties"
    }
    prepared_listings = prepare_valid_rows(
        deduplication.rows,
        deduplication.source_row_numbers,
        excluded_listing_rows,
        condition_rules,
        keep_unclassified=True,
    )
    prepared_properties = prepare_valid_rows(
        inputs.properties, property_source_rows, excluded_property_rows, condition_rules
    )
    invalid_numeric_count = sum(issue.kind == "numeric" for issue in invalid_values)

    return QualitySummary(
        listing_count=len(inputs.listings),
        property_count=len(inputs.properties),
        missing_fields=missing_fields,
        invalid_values=invalid_values,
        missing_listing_states=missing_listing_states,
        out_of_range_prices=out_of_range_prices,
        price_range=(price_min, price_max),
        price_calculations=price_calculations,
        invalid_numeric_count=invalid_numeric_count,
        normalized_conditions=normalized_conditions,
        deduplication=deduplication,
        exclusions=exclusions,
        prepared_listings=prepared_listings,
        prepared_properties=prepared_properties,
        include_candidates=include_candidates,
        verifications=verifications,
    )


def _count_missing(
    rows: list[dict[str, Any]],
    required_fields: tuple[str, ...],
    counts: Counter[str],
) -> None:
    for row in rows:
        for field in set(row) | set(required_fields):
            if _is_missing(row.get(field)):
                counts[field] += 1


def _check_required_text(
    dataset: str,
    row_number: int,
    row: dict[str, Any],
    record_id: str,
    fields: tuple[str, ...],
    issues: list[QualityIssue],
) -> None:
    for field in fields:
        if _is_missing(row.get(field)):
            issues.append(
                _issue(
                    dataset,
                    row_number,
                    record_id,
                    field,
                    "Required value is missing.",
                    "",
                    "missing",
                )
            )


def _check_number(
    dataset: str,
    row_number: int,
    row: dict[str, Any],
    record_id: str,
    field: str,
    issues: list[QualityIssue],
    *,
    minimum: float,
    maximum: Optional[float] = None,
    minimum_inclusive: bool = False,
) -> Optional[float]:
    raw_value = row.get(field)
    if _is_missing(raw_value):
        return None

    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        issues.append(
            _issue(dataset, row_number, record_id, field, "Value is not numeric.", raw_value, "numeric")
        )
        return None

    if not math.isfinite(value):
        issues.append(
            _issue(dataset, row_number, record_id, field, "Value is not finite.", raw_value, "numeric")
        )
        return None

    below_minimum = value < minimum or (value == minimum and not minimum_inclusive)
    if below_minimum:
        operator = "at least" if minimum_inclusive else "greater than"
        issues.append(
            _issue(
                dataset,
                row_number,
                record_id,
                field,
                f"Value must be {operator} {minimum:g}.",
                raw_value,
                "numeric",
            )
        )
        return None

    if maximum is not None and value > maximum:
        issues.append(
            _issue(
                dataset,
                row_number,
                record_id,
                field,
                f"Value must be at most {maximum:g}.",
                raw_value,
                "numeric",
            )
        )
        return None
    return value


def _check_optional_integer(
    dataset: str,
    row_number: int,
    row: dict[str, Any],
    record_id: str,
    field: str,
    issues: list[QualityIssue],
) -> None:
    raw_value = row.get(field)
    if _is_missing(raw_value):
        return
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        issues.append(
            _issue(dataset, row_number, record_id, field, "Value is not numeric.", raw_value, "numeric")
        )
        return
    if not math.isfinite(value) or value < 0 or not value.is_integer():
        issues.append(
            _issue(
                dataset,
                row_number,
                record_id,
                field,
                "Value must be a non-negative integer.",
                raw_value,
                "numeric",
            )
        )


def _record_id(row: dict[str, Any], *fields: str) -> str:
    for field in fields:
        value = row.get(field)
        if not _is_missing(value):
            return str(value)
    return "<missing identifier>"


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _issue(
    dataset: str,
    row_number: int,
    record_id: str,
    field: str,
    reason: str,
    value: Any,
    kind: str,
) -> QualityIssue:
    return QualityIssue(
        dataset=dataset,
        row_number=row_number,
        record_id=record_id,
        field=field,
        reason=reason,
        value="<blank>" if _is_missing(value) else str(value),
        kind=kind,
    )


def render_report(summary: QualitySummary, parameter_version: str) -> str:
    invalid_issues = summary.invalid_values + summary.out_of_range_prices
    lines = [
        "# Data quality report",
        "",
        "This report checks required fields, numeric values, coordinate ranges, "
        "accepted price types, and configured price per square meter limits.",
        "",
        "## Summary",
        "",
        f"- Listings checked: {summary.listing_count}.",
        f"- Test properties checked: {summary.property_count}.",
        f"- Rows with required field or value issues: "
        f"{_unique_row_count(invalid_issues, 'Listings')} listings and "
        f"{_unique_row_count(invalid_issues, 'Test properties')} test properties.",
        f"- Invalid numeric values: {summary.invalid_numeric_count}.",
        f"- Price per square meter checked for {summary.price_calculations} listings.",
        f"- Configured price range: {summary.price_range[0]:,.0f} to "
        f"{summary.price_range[1]:,.0f} COP/m2, parameter version {parameter_version}.",
        f"- Listings without a condition: {len(summary.missing_listing_states)}. "
        "They cannot enter condition-matched comparisons.",
        f"- Official listing field checks: {sum(item['status'] == 'confirmed' for item in summary.verifications)} confirmed, "
        f"{sum(item['status'] == 'corrected' for item in summary.verifications)} corrected with evidence.",
        "",
        "## Missing values",
        "",
        "Counts include optional fields. A missing optional value is not an invalid row.",
        "",
        "| Dataset | Field | Missing rows |",
        "|---|---|---:|",
    ]

    for dataset, counts in summary.missing_fields.items():
        for field, count in sorted(counts.items()):
            lines.append(f"| {dataset} | {field} | {count} |")

    lines.extend(["", "## Required field and value issues", ""])
    if summary.invalid_values:
        lines.extend(
            [
                "| Dataset | CSV row | Record | Field | Reason | Value |",
                "|---|---:|---|---|---|---|",
            ]
        )
        for issue in summary.invalid_values:
            lines.append(
                f"| {issue.dataset} | {issue.row_number} | {_escape(issue.record_id)} | "
                f"{_escape(issue.field)} | {_escape(issue.reason)} | "
                f"{_escape(issue.value)} |"
            )
    else:
        lines.append("No required field or value issues were found.")

    removed_by_rule = Counter(record.rule for record in summary.deduplication.removed)
    lines.extend(
        [
            "",
            "## Duplicate removal",
            "",
            "Candidate keys ignore case to find possible repeats. Exact removal trims and collapses spaces but preserves case and accents. A row is removed only when every source column matches.",
            "",
            "| Candidate key | Candidate groups | Rows removed after normalization |",
            "|---|---:|---:|",
            f"| id_anuncio | {summary.deduplication.group_counts['id_anuncio']} | {removed_by_rule['id_anuncio']} |",
            f"| claves_sin_id ({', '.join(summary.deduplication.tuple_fields)}) | {summary.deduplication.group_counts['claves_sin_id']} | {removed_by_rule['claves_sin_id']} |",
            f"| All source columns | {summary.deduplication.group_counts['all_columns']} | {removed_by_rule['all_columns']} |",
            f"| Total | {sum(summary.deduplication.group_counts.values())} | {len(summary.deduplication.removed)} |",
            f"| Rows retained | | {len(summary.deduplication.rows)} |",
            f"| Possible repeat groups kept separate | | {len({record.first_row_number for record in summary.deduplication.for_review})} |",
            f"| Possible repeat rows | | {len(summary.deduplication.for_review)} |",
            f"| Possible repeat rows selected for calculations | | {len(summary.deduplication.for_review) if summary.include_candidates else 0} |",
            f"| Possible repeat rows omitted from calculations | | {0 if summary.include_candidates else len(summary.deduplication.for_review)} |",
            "",
            "Possible repeat rows: output/prepared/posibles_repeticiones.csv. They remain separate ads.",
            "Choose their use with `--include-candidates` or `--exclude-candidates`; the default comes from config/parametros.yaml.",
            "Group details: output/prepared/grupos_posibles_repeticiones.csv. It lists differing columns and original values.",
            "Field-level source and processing log: output/prepared/auditoria_campos_anuncios.csv.",
            "Normalization before/after log: output/prepared/normalizacion_texto.csv.",
        ]
    )

    excluded_counts = Counter(
        (issue.dataset, issue.field, issue.reason) for issue in summary.exclusions
    )
    excluded_properties = _unique_row_count(summary.exclusions, "Test properties")
    lines.extend(
        [
            "",
            "## Prepared listing rows",
            "",
            f"Listings: {len(summary.deduplication.rows)} after exact duplicate removal, "
            f"{len(summary.prepared_listings.rows)} retained under the selected candidate option.",
            f"Test properties: {summary.property_count} checked, {excluded_properties} excluded, "
            f"{len(summary.prepared_properties.rows)} valid.",
            "Calculation rules check each required field. A missing value excludes only the calculation that needs it.",
            "",
            "- output/prepared/anuncios_seleccionados.csv",
            "- output/prepared/inmuebles_validos.csv",
            "- output/prepared/incidencias_datos.csv",
            "- output/prepared/posibles_repeticiones.csv",
            "- output/prepared/grupos_posibles_repeticiones.csv",
            "- output/prepared/auditoria_campos_anuncios.csv",
            "",
            "## Data issue counts by reason",
            "",
            "Counts are issue occurrences. One row can have more than one reason.",
            "",
            "| Dataset | Field | Reason | Occurrences |",
            "|---|---|---|---:|",
        ]
    )
    for (dataset, field, reason), count in sorted(excluded_counts.items()):
        lines.append(
            f"| {dataset} | {field} | {_escape(reason)} | {count} |"
        )

    lines.extend(["", "## Rows with data issues", ""])
    if summary.exclusions:
        lines.extend(
            [
                "| Dataset | CSV row | Record | Field | Reason | Value |",
                "|---|---:|---|---|---|---|",
            ]
        )
        for issue in sorted(
            summary.exclusions, key=lambda item: (item.dataset, item.row_number, item.field)
        ):
            lines.append(
                f"| {issue.dataset} | {issue.row_number} | {_escape(issue.record_id)} | "
                f"{_escape(issue.field)} | {_escape(issue.reason)} | {_escape(issue.value)} |"
            )
    else:
        lines.append("No rows were excluded from the prepared inputs.")

    lines.extend(["", "## Out-of-range prices", ""])
    if summary.out_of_range_prices:
        lines.extend(
            [
                "| CSV row | Listing | Price per square meter | Reason |",
                "|---:|---|---:|---|",
            ]
        )
        for issue in summary.out_of_range_prices:
            lines.append(
                f"| {issue.row_number} | {_escape(issue.record_id)} | "
                f"{issue.value} COP/m2 | {_escape(issue.reason)} |"
            )
    else:
        lines.append(
            "No calculated listing prices per square meter fall outside the configured range."
        )

    lines.extend(
        [
            "",
            "## Missing condition values",
            "",
            f"{len(summary.missing_listing_states)} listings have an empty estado. "
            "They remain visible in the source data but cannot match a canonical condition.",
            "",
            "## Normalized conditions",
            "",
            "Missing or unmapped values remain sin_clasificar.",
            "",
            "| Dataset | Canonical condition | Rows |",
            "|---|---|---:|",
        ]
    )
    for dataset, counts in summary.normalized_conditions.items():
        for condition, count in sorted(counts.items()):
            lines.append(f"| {dataset} | {condition} | {count} |")

    lines.extend(
        [
            "",
        ]
    )
    return "\n".join(lines)


def _unique_row_count(issues: list[QualityIssue], dataset: str) -> int:
    return len({issue.row_number for issue in issues if issue.dataset == dataset})


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _write_rows(
    path: Path, rows: list[dict[str, Any]], fieldnames: list[str]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_exclusions(exclusions: list[QualityIssue]) -> None:
    rows = [
        {
            "dataset": issue.dataset,
            "csv_row": issue.row_number,
            "record_id": issue.record_id,
            "field": issue.field,
            "reason": issue.reason,
            "value": issue.value,
        }
        for issue in exclusions
    ]
    _write_rows(
        ISSUES_PATH,
        rows,
        ["dataset", "csv_row", "record_id", "field", "reason", "value"],
    )


def _write_normalization_audit(inputs: LoadedInputs, parameters: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for dataset, source_file, source_rows in (
        ("Listings", "data/anuncios_muestra.csv", inputs.listings),
        ("Test properties", "data/inmuebles_prueba.csv", inputs.properties),
    ):
        for csv_row, row in enumerate(source_rows, start=2):
            for field, value in row.items():
                if not isinstance(value, str):
                    continue
                if field in ("area_m2", "precio", "habitaciones", "banos", "parqueadero"):
                    try:
                        comparison_value = format(Decimal(value.strip()).normalize(), "f") if value.strip() else ""
                        rule = "Número: se compara el valor decimal equivalente"
                    except (InvalidOperation, ValueError):
                        comparison_value = normalize_text_for_comparison(value)
                        rule = "Texto: recorta y agrupa espacios; ignora mayúsculas"
                else:
                    comparison_value = normalize_text_for_comparison(value)
                    rule = "Texto: recorta y agrupa espacios; ignora mayúsculas; conserva tildes"
                rows.append({
                    "dataset": dataset,
                    "source_file": source_file,
                    "source_row": csv_row,
                    "field": field,
                    "original_value": value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t"),
                    "comparison_value": comparison_value,
                    "prepared_value": normalize_output_text(value),
                    "comparison_changed": str(value != comparison_value).lower(),
                    "prepared_changed": str(value != normalize_output_text(value)).lower(),
                    "rule": f"{rule}; salida: recorta y agrupa espacios, conserva mayúsculas y tildes",
                })
                if field == "estado":
                    canonical = normalize_conditions([row], parameters["estados"])[0]["estado_canonico"]
                    rows.append({
                        "dataset": dataset,
                        "source_file": source_file,
                        "source_row": csv_row,
                        "field": "estado_canonico",
                        "original_value": value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t"),
                        "comparison_value": normalize_text_for_comparison(value),
                        "prepared_value": canonical,
                        "comparison_changed": str(value != normalize_text_for_comparison(value)).lower(),
                        "prepared_changed": str(value != canonical).lower(),
                        "rule": "Estado: se asigna la categoría configurada; no se corrige por intuición",
                    })
    _write_rows(
        NORMALIZATION_AUDIT_PATH,
        rows,
        ["dataset", "source_file", "source_row", "field", "original_value", "comparison_value", "prepared_value", "comparison_changed", "prepared_changed", "rule"],
    )


def _write_duplicate_review(inputs: LoadedInputs, summary: QualitySummary) -> None:
    fieldnames = list(inputs.listings[0]) + [
        "csv_row",
        "first_candidate_row",
        "candidate_rule",
        "candidate_key",
        "differing_fields",
    ]
    rows = []
    for review in summary.deduplication.for_review:
        source_row = inputs.listings[review.row_number - 2]
        rows.append(
            {
                **source_row,
                "csv_row": review.row_number,
                "first_candidate_row": review.first_row_number,
                "candidate_rule": review.rule,
                "candidate_key": review.key,
                "differing_fields": ", ".join(review.differing_fields),
            }
        )
    _write_rows(DUPLICATE_REVIEW_PATH, rows, fieldnames)
    groups: dict[int, list[Any]] = {}
    for review in summary.deduplication.for_review:
        groups.setdefault(review.first_row_number, []).append(review)
    group_rows = []
    for number, (first_row, reviews) in enumerate(sorted(groups.items()), start=1):
        source_rows = [inputs.listings[review.row_number - 2] for review in reviews]
        differing_fields = sorted({field for review in reviews for field in review.differing_fields})
        values_by_field = {
            field: list(dict.fromkeys(str(row.get(field, "")) for row in source_rows))
            for field in differing_fields
        }
        group_rows.append({
            "possible_repeat_group": f"REP-{number:02d}",
            "first_candidate_row": first_row,
            "csv_rows": ", ".join(str(review.row_number) for review in sorted(reviews, key=lambda item: item.row_number)),
            "zone": str(source_rows[0].get("zona", "")),
            "candidate_rules": "; ".join(sorted({review.rule for review in reviews})),
            "candidate_keys": " || ".join(sorted({review.key for review in reviews})),
            "listing_ids": "; ".join(dict.fromkeys(str(row.get("id_anuncio", "")) for row in source_rows)),
            "differing_fields": ", ".join(differing_fields),
            "original_values_by_field_json": json.dumps(values_by_field, ensure_ascii=False, sort_keys=True),
        })
    _write_rows(
        REVIEW_GROUP_SUMMARY_PATH,
        group_rows,
        ["possible_repeat_group", "first_candidate_row", "csv_rows", "zone", "candidate_rules", "candidate_keys", "listing_ids", "differing_fields", "original_values_by_field_json"],
    )


def _write_listing_field_audit(rows: list[dict[str, Any]], summary: QualitySummary) -> None:
    audit_rows = []
    checked_on = date.today().isoformat()
    issues_by_field = {
        (issue.row_number, issue.field): issue
        for issue in summary.invalid_values + summary.out_of_range_prices + summary.missing_listing_states
    }
    verifications = {
        (int(item["csv_row"]), item["field"]): item
        for item in summary.verifications
    }
    for row_number, source_row in enumerate(rows, start=2):
        for field, original in source_row.items():
            prepared = normalize_output_text(original)
            is_missing = _is_missing(original)
            issue = issues_by_field.get((row_number, field))
            if issue is None and field in {"area_m2", "precio"}:
                issue = issues_by_field.get((row_number, "precio / area_m2"))
            evidence = verifications.get((row_number, field))
            if evidence:
                prepared = evidence["result_value"]
                status = "officially_confirmed" if evidence["status"] == "confirmed" else "corrected_with_evidence"
                note = evidence["rule"]
            elif is_missing:
                status = "missing"
                note = "The source row has no value. No value was added."
            elif issue is not None:
                status = "invalid_or_out_of_range"
                note = issue.reason
            elif prepared != original:
                status = "format_normalized"
                note = "Leading, trailing, or repeated whitespace was removed."
            else:
                status = "reported_by_source_unverified"
                note = "This value came from the supplied listing sample. No official record uniquely confirms it."
            audit_rows.append({
                "csv_row": row_number,
                "id_anuncio": source_row.get("id_anuncio", ""),
                "field": field,
                "original_value": "" if original is None else str(original),
                "prepared_value": "" if prepared is None else str(prepared),
                "status": status,
                "rule": "Preserve the source value; collapse whitespace only; do not infer missing data.",
                "evidence_file": "data/anuncios_muestra.csv",
                "evidence_row": row_number,
                "official_source_url": evidence["source_url"] if evidence else "",
                "source_record_id": evidence["source_record_id"] if evidence else "",
                "source_license": evidence["license"] if evidence else "",
                "source_snapshot_path": evidence["snapshot_path"] if evidence else "",
                "official_check_status": evidence["status"] if evidence else "not_independently_confirmed",
                "audit_date": checked_on,
                "note": note,
            })
    _write_rows(
        LISTING_FIELD_AUDIT_PATH,
        audit_rows,
        [
            "csv_row", "id_anuncio", "field", "original_value", "prepared_value",
            "status", "rule", "evidence_file", "evidence_row", "official_source_url",
            "source_record_id", "source_license", "source_snapshot_path",
            "official_check_status", "audit_date", "note",
        ],
    )


def generate_report(include_candidates: Optional[bool] = None) -> Path:
    inputs = load_inputs()
    parameters = load_parameters()
    summary = inspect_quality(inputs, parameters, include_candidates)
    listing_fields = list(inputs.listings[0])
    property_fields = list(inputs.properties[0])
    _write_rows(DEDUPLICATED_PATH, summary.deduplication.rows, listing_fields)
    _write_rows(
        SELECTED_LISTINGS_PATH,
        summary.prepared_listings.rows,
        listing_fields + ["estado_canonico"],
    )
    _write_rows(
        VALID_PROPERTIES_PATH,
        summary.prepared_properties.rows,
        property_fields + ["estado_canonico"],
    )
    _write_exclusions(summary.exclusions)
    _write_duplicate_review(inputs, summary)
    _write_normalization_audit(inputs, parameters)
    _write_listing_field_audit(inputs.listings, summary)
    report = render_report(summary, str(parameters.get("version", "unknown")))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    return OUTPUT_PATH


if __name__ == "__main__":
    print(f"Wrote {generate_report()}")
    print(f"Wrote {DEDUPLICATED_PATH}")
    print(f"Wrote {SELECTED_LISTINGS_PATH}")
    print(f"Wrote {VALID_PROPERTIES_PATH}")
    print(f"Wrote {ISSUES_PATH}")
    print(f"Wrote {DUPLICATE_REVIEW_PATH}")
    print(f"Wrote {REVIEW_GROUP_SUMMARY_PATH}")
    print(f"Wrote {NORMALIZATION_AUDIT_PATH}")
    print(f"Wrote {LISTING_FIELD_AUDIT_PATH}")
