import unicodedata
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Optional, Sequence


UNCLASSIFIED = "sin_clasificar"
NUMERIC_DEDUP_FIELDS = {"area_m2", "precio"}


@dataclass(frozen=True)
class DuplicateRecord:
    row_number: int
    first_row_number: int
    rule: str
    key: str


@dataclass(frozen=True)
class DeduplicationResult:
    rows: list[dict[str, Any]]
    removed: list[DuplicateRecord]
    group_counts: Counter[str]
    tuple_fields: tuple[str, ...]
    source_row_numbers: list[int]


@dataclass(frozen=True)
class PreparedRows:
    rows: list[dict[str, Any]]
    source_row_numbers: list[int]


def build_condition_map(
    rules: Mapping[str, Sequence[str]],
) -> dict[str, str]:
    condition_map: dict[str, str] = {}
    for canonical, aliases in rules.items():
        for alias in aliases:
            key = normalize_text(alias)
            previous = condition_map.get(key)
            if previous is not None and previous != canonical:
                raise ValueError(f"Condition alias maps to more than one value: {alias}")
            condition_map[key] = canonical
    return condition_map


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKD", str(value))
    plain_text = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return plain_text.lower().replace("?", "").strip()


def normalize_conditions(
    rows: list[dict[str, Any]],
    rules: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    condition_map = build_condition_map(rules)
    normalized_rows = []
    for row in rows:
        canonical = condition_map.get(normalize_text(row.get("estado")), UNCLASSIFIED)
        normalized_rows.append({**row, "estado_canonico": canonical})
    return normalized_rows


def count_conditions(
    rows: list[dict[str, Any]],
    rules: Mapping[str, Sequence[str]],
) -> Counter[str]:
    normalized_rows = normalize_conditions(rows, rules)
    return Counter(row["estado_canonico"] for row in normalized_rows)


def deduplicate_listings(
    rows: list[dict[str, Any]],
    rules: Mapping[str, Any],
) -> DeduplicationResult:
    removed: list[DuplicateRecord] = []
    id_groups: set[str] = set()
    tuple_groups: set[tuple[Any, ...]] = set()
    id_first_rows: dict[str, int] = {}
    after_id_rule: list[tuple[int, dict[str, Any]]] = []

    for row_number, row in enumerate(rows, start=2):
        listing_id = row.get("id_anuncio")
        if not _is_missing(listing_id):
            listing_id = str(listing_id).strip()
            first_row = id_first_rows.get(listing_id)
            if first_row is not None:
                id_groups.add(listing_id)
                removed.append(
                    DuplicateRecord(row_number, first_row, "id_anuncio", listing_id)
                )
                continue
            id_first_rows[listing_id] = row_number
        after_id_rule.append((row_number, row))

    tuple_fields = tuple(rules["claves_sin_id"])
    tuple_first_rows: dict[tuple[Any, ...], int] = {}
    kept: list[tuple[int, dict[str, Any]]] = []

    for row_number, row in after_id_rule:
        key = _deduplication_key(row, tuple_fields)
        if key is not None:
            first_row = tuple_first_rows.get(key)
            if first_row is not None:
                tuple_groups.add(key)
                removed.append(
                    DuplicateRecord(
                        row_number,
                        first_row,
                        "claves_sin_id",
                        _format_key(tuple_fields, key),
                    )
                )
                continue
            tuple_first_rows[key] = row_number
        kept.append((row_number, row))

    return DeduplicationResult(
        rows=[row for _, row in kept],
        removed=removed,
        group_counts=Counter(
            {
                "id_anuncio": len(id_groups),
                "claves_sin_id": len(tuple_groups),
            }
        ),
        tuple_fields=tuple_fields,
        source_row_numbers=[row_number for row_number, _ in kept],
    )


def prepare_valid_rows(
    rows: list[dict[str, Any]],
    source_row_numbers: list[int],
    excluded_row_numbers: set[int],
    rules: Mapping[str, Sequence[str]],
) -> PreparedRows:
    if len(rows) != len(source_row_numbers):
        raise ValueError("Each prepared row must have one source row number.")

    normalized_rows = normalize_conditions(rows, rules)
    kept = [
        (row_number, row)
        for row_number, row in zip(source_row_numbers, normalized_rows)
        if row_number not in excluded_row_numbers and row["estado_canonico"] != UNCLASSIFIED
    ]
    return PreparedRows(
        rows=[row for _, row in kept],
        source_row_numbers=[row_number for row_number, _ in kept],
    )


def _deduplication_key(
    row: dict[str, Any],
    fields: tuple[str, ...],
) -> Optional[tuple[Any, ...]]:
    values: list[Any] = []
    for field in fields:
        raw_value = row.get(field)
        if _is_missing(raw_value):
            return None
        if field in NUMERIC_DEDUP_FIELDS:
            try:
                value = Decimal(str(raw_value).strip())
            except (InvalidOperation, ValueError):
                return None
            if not value.is_finite():
                return None
            values.append(value.normalize())
        else:
            values.append(str(raw_value).strip())
    return tuple(values)


def _format_key(fields: tuple[str, ...], values: tuple[Any, ...]) -> str:
    return ", ".join(f"{field}={value}" for field, value in zip(fields, values))


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())
