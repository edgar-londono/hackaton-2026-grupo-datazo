import unicodedata
from collections import Counter
from typing import Any, Mapping, Sequence


UNCLASSIFIED = "sin_clasificar"


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
