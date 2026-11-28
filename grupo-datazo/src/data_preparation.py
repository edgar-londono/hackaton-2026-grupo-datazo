import unicodedata
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Optional, Sequence


UNCLASSIFIED = "sin_clasificar"
NUMERIC_DEDUP_FIELDS = {"area_m2", "precio", "habitaciones", "banos", "parqueadero"}


@dataclass(frozen=True)
class DuplicateRecord:
    row_number: int
    first_row_number: int
    rule: str
    key: str


@dataclass(frozen=True)
class DuplicateReviewRecord:
    row_number: int
    first_row_number: int
    rule: str
    key: str
    differing_fields: tuple[str, ...]


@dataclass(frozen=True)
class DeduplicationResult:
    rows: list[dict[str, Any]]
    removed: list[DuplicateRecord]
    for_review: list[DuplicateReviewRecord]
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


def normalize_text_for_comparison(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).casefold().split())


def normalize_text_for_similarity(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", normalize_text_for_comparison(value))
    return "".join(
        character for character in normalized if not unicodedata.combining(character)
    )


def normalize_output_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return " ".join(value.split())


def normalize_text(value: Any) -> str:
    return " ".join(normalize_text_for_comparison(value).replace("?", "").split())


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
    for_review: list[DuplicateReviewRecord] = []
    tuple_fields = tuple(rules["claves_sin_id"])
    candidates: dict[tuple[str, Any], list[int]] = {}

    for index, row in enumerate(rows):
        full_row_key = _comparison_row_key(row)
        candidates.setdefault(("all_columns", full_row_key), []).append(index)
        listing_id = row.get("id_anuncio")
        if not _is_missing(listing_id):
            candidates.setdefault(("id_anuncio", normalize_text_for_comparison(listing_id)), []).append(index)
        tuple_key = _deduplication_key(row, tuple_fields)
        if tuple_key is not None:
            candidates.setdefault(("claves_sin_id", tuple_key), []).append(index)

    # Candidate keys only find rows to compare. They never prove that rows match.
    parents = list(range(len(rows)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    candidate_group_counts: Counter[str] = Counter()
    candidate_rules: dict[tuple[int, int], tuple[str, str]] = {}
    candidate_indexes: set[int] = set()
    for (rule, raw_key), indexes in candidates.items():
        if len(indexes) < 2:
            continue
        candidate_indexes.update(indexes)
        candidate_group_counts[rule] += 1
        if rule == "id_anuncio":
            key = str(raw_key)
        elif rule == "claves_sin_id":
            key = _format_key(tuple_fields, raw_key)
        else:
            key = "all source columns"
        for index in indexes[1:]:
            union(indexes[0], index)
            candidate_rules.setdefault(
                (min(indexes[0], index), max(indexes[0], index)), (rule, key)
            )

    components: dict[int, list[int]] = {}
    for index in candidate_indexes:
        root = find(index)
        components.setdefault(root, []).append(index)

    removed_indexes: set[int] = set()
    for indexes in sorted(components.values(), key=lambda group: min(group)):
        indexes.sort()
        if len(indexes) < 2:
            continue
        first_index = indexes[0]
        first_row = rows[first_index]
        rule, key = "all_columns", "exact row match"
        for other_index in indexes[1:]:
            pair = (min(first_index, other_index), max(first_index, other_index))
            if pair in candidate_rules:
                rule, key = candidate_rules[pair]
                break
        first_comparison_key = _comparison_row_key(first_row)
        if all(_comparison_row_key(rows[index]) == first_comparison_key for index in indexes[1:]):
            for index in indexes[1:]:
                removed_indexes.add(index)
                removed.append(
                    DuplicateRecord(index + 2, first_index + 2, rule, key)
                )
            continue

        differing_fields = tuple(
            field for field in first_row
            if any(
                _comparison_value(field, rows[index].get(field))
                != _comparison_value(field, first_row.get(field))
                for index in indexes[1:]
            )
        )
        for index in indexes:
            for_review.append(
                DuplicateReviewRecord(
                    index + 2,
                    first_index + 2,
                    rule,
                    key,
                    differing_fields,
                )
            )

    kept = [
        (index + 2, row)
        for index, row in enumerate(rows)
        if index not in removed_indexes
    ]

    return DeduplicationResult(
        rows=[
            {field: normalize_output_text(value) for field, value in row.items()}
            for _, row in kept
        ],
        removed=removed,
        for_review=for_review,
        group_counts=candidate_group_counts,
        tuple_fields=tuple_fields,
        source_row_numbers=[row_number for row_number, _ in kept],
    )


def prepare_valid_rows(
    rows: list[dict[str, Any]],
    source_row_numbers: list[int],
    excluded_row_numbers: set[int],
    rules: Mapping[str, Sequence[str]],
    keep_unclassified: bool = False,
) -> PreparedRows:
    if len(rows) != len(source_row_numbers):
        raise ValueError("Each prepared row must have one source row number.")

    normalized_rows = normalize_conditions(rows, rules)
    kept = [
        (row_number, row)
        for row_number, row in zip(source_row_numbers, normalized_rows)
        if row_number not in excluded_row_numbers
        and (keep_unclassified or row["estado_canonico"] != UNCLASSIFIED)
    ]
    return PreparedRows(
        rows=[
            {field: normalize_output_text(value) for field, value in row.items()}
            for _, row in kept
        ],
        source_row_numbers=[row_number for row_number, _ in kept],
    )


def _comparison_value(field: str, value: Any) -> tuple[str, Any]:
    if _is_missing(value):
        return ("missing", "")
    if field in NUMERIC_DEDUP_FIELDS:
        try:
            number = Decimal(str(value).strip())
        except (InvalidOperation, ValueError):
            return ("text", normalize_text_for_comparison(value))
        if number.is_finite():
            return ("number", number.normalize())
    if isinstance(value, str):
        return ("text", " ".join(value.split()))
    return ("value", value)


def _comparison_row_key(row: Mapping[str, Any]) -> tuple[tuple[str, tuple[str, Any]], ...]:
    return tuple(
        (field, _comparison_value(field, row.get(field)))
        for field in sorted(row)
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
            values.append(normalize_text_for_comparison(raw_value))
    return tuple(values)


def _format_key(fields: tuple[str, ...], values: tuple[Any, ...]) -> str:
    return ", ".join(f"{field}={value}" for field, value in zip(fields, values))


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())
