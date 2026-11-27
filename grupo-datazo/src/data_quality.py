import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

if __package__:
    from .data_loader import LoadedInputs, load_inputs
    from .parameters import load_parameters
else:
    from data_loader import LoadedInputs, load_inputs
    from parameters import load_parameters


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "output" / "data_quality.md"

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


def inspect_quality(inputs: LoadedInputs, parameters: dict[str, Any]) -> QualitySummary:
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

    _count_missing(inputs.listings, LISTING_REQUIRED_FIELDS, missing_fields["Listings"])
    _count_missing(inputs.properties, PROPERTY_REQUIRED_FIELDS, missing_fields["Test properties"])

    for row_number, row in enumerate(inputs.listings, start=2):
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
        "Duplicate analysis remains pending checklist item 4.4.",
        "",
        "## Summary",
        "",
        f"- Listings checked: {summary.listing_count}.",
        f"- Test properties checked: {summary.property_count}.",
        f"- Rows with required field or value issues: "
        f"{_invalid_row_count(invalid_issues, 'Listings')} listings and "
        f"{_invalid_row_count(invalid_issues, 'Test properties')} test properties.",
        f"- Invalid numeric values: {summary.invalid_numeric_count}.",
        f"- Price per square meter checked for {summary.price_calculations} listings.",
        f"- Configured price range: {summary.price_range[0]:,.0f} to "
        f"{summary.price_range[1]:,.0f} COP/m2, parameter version {parameter_version}.",
        f"- Listings without a condition: {len(summary.missing_listing_states)}. "
        "They cannot enter condition-matched comparisons.",
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
            "## Pending checks",
            "",
            "- Apply invalid-row exclusions to calculations under checklist item 4.5.",
            "- Count duplicate groups and apply the supplied rules under checklist item 4.4.",
            "",
        ]
    )
    return "\n".join(lines)


def _invalid_row_count(issues: list[QualityIssue], dataset: str) -> int:
    return len({issue.row_number for issue in issues if issue.dataset == dataset})


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def generate_report() -> Path:
    inputs = load_inputs()
    parameters = load_parameters()
    summary = inspect_quality(inputs, parameters)
    report = render_report(summary, str(parameters.get("version", "unknown")))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    return OUTPUT_PATH


if __name__ == "__main__":
    print(f"Wrote {generate_report()}")
