"""Market comparison calculations for the supplied property sample."""

from __future__ import annotations

import math
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

if __package__:
    from .data_preparation import normalize_text_for_comparison
else:
    from data_preparation import normalize_text_for_comparison


CANONICAL_CONDITIONS = ("remodelado", "habitable", "por_remodelar")


def analyze_market(
    property_row: dict[str, Any],
    input_listings: list[dict[str, Any]],
    valid_listings: list[dict[str, Any]],
    quality: Any,
    parameters: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the market section and zone-level data-quality counts."""
    zone = _text(property_row.get("zona"))
    condition = property_row.get("estado_canonico")
    area = _number(property_row.get("area_m2"))
    zone_rows = [row for row in input_listings if _text(row.get("zona")) == zone]

    issue_counts: Counter[str] = Counter()
    pending_review_rows: set[int] = set()
    for issue in quality.exclusions:
        if issue.dataset != "Listings":
            continue
        source_index = issue.row_number - 2
        if not 0 <= source_index < len(input_listings):
            continue
        if _text(input_listings[source_index].get("zona")) != zone:
            continue
        if issue.kind == "duplicate_review":
            pending_review_rows.add(issue.row_number)
        elif issue.field == "estado":
            issue_counts["estado_sin_clasificar"] += 1
        elif issue.field == "area_m2":
            issue_counts["sin_area"] += 1
        elif issue.field == "precio / area_m2":
            issue_counts["precio_m2_fuera_de_rango"] += 1
        elif issue.field == "tipo_precio":
            issue_counts["tipo_precio_no_aceptado"] += 1
        elif issue.kind == "numeric":
            issue_counts[f"valor_numerico_invalido_{issue.field}"] += 1

    removed_rows = {
        duplicate.row_number
        for duplicate in quality.deduplication.removed
        if _text(input_listings[duplicate.row_number - 2].get("zona")) == zone
    }
    quality_by_zone = {
        "anuncios_en_zona": len(zone_rows),
        "duplicados_eliminados": len(removed_rows),
        "anuncios_unicos": len(zone_rows) - len(removed_rows),
        "anuncios_invalidos": dict(sorted(issue_counts.items())),
        "anuncios_pendientes_revision": len(pending_review_rows),
        "grupos_pendientes_revision": len({
            (item.first_row_number, item.rule, item.key)
            for item in quality.deduplication.for_review
            if _text(input_listings[item.row_number - 2].get("zona")) == zone
        }),
        "filas_invalidas_unicas": len({
            issue.row_number
            for issue in quality.exclusions
            if issue.dataset == "Listings"
            and issue.kind != "duplicate_review"
            and issue.row_number not in pending_review_rows
            and _text(input_listings[issue.row_number - 2].get("zona")) == zone
        }),
        "anuncios_validos": sum(1 for row in valid_listings if _text(row.get("zona")) == zone),
    }

    zone_valid = [
        row for row in valid_listings
        if _text(row.get("zona")) == zone
    ]
    state_context = {
        state: _price_context([row for row in zone_valid if row.get("estado_canonico") == state])
        for state in CANONICAL_CONDITIONS
    }

    comparable_rules = parameters["comparables"]
    area_tolerance = float(comparable_rules["tolerancia_area"])
    minimum_price_m2, maximum_price_m2 = comparable_rules["rango_precio_m2_valido"]
    accepted_price_types = {normalize_text_for_comparison(value) for value in comparable_rules["tipos_precio"]}
    own_ids = {_text(property_row.get("id_anuncio"))} - {""}
    own_origins = {_text(property_row.get("origen"))} - {""}
    excluded_own_keys = {
        _text(row.get("id_anuncio")) for row in input_listings
        if _text(row.get("zona")) == zone and _text(row.get("origen")) in own_origins and _text(row.get("id_anuncio"))
    }
    excluded_own_keys |= own_ids

    candidates: list[dict[str, Any]] = []
    if area is not None and area > 0 and condition not in (None, "sin_clasificar"):
        for row in zone_valid:
            if row.get("estado_canonico") != condition:
                continue
            if _text(row.get("id_anuncio")) in excluded_own_keys or _text(row.get("origen")) in own_origins:
                continue
            listing_area = _number(row.get("area_m2"))
            price = _number(row.get("precio"))
            price_type = normalize_text_for_comparison(row.get("tipo_precio"))
            if listing_area is None or listing_area <= 0 or price is None or price_type not in accepted_price_types:
                continue
            if not area * (1 - area_tolerance) <= listing_area <= area * (1 + area_tolerance):
                continue
            price_per_m2 = price / listing_area
            if not minimum_price_m2 <= price_per_m2 <= maximum_price_m2:
                continue
            candidates.append({
                "origen": _clean(row.get("origen")),
                "id_anuncio": _clean(row.get("id_anuncio")),
                "fuente": _clean(row.get("fuente")),
                "area_m2": listing_area,
                "precio": _round_integer(price),
                "precio_m2": _round_integer(price_per_m2),
                "_raw_precio_m2": price_per_m2,
            })
    candidates.sort(key=lambda row: (row["_raw_precio_m2"], row["origen"] or ""))
    stats = _statistics([row["_raw_precio_m2"] for row in candidates])
    confidence = _confidence(stats["n"], stats["coef_variacion"], parameters)
    market = {
        "estado_referencia": condition if condition != "sin_clasificar" else None,
        "precio_m2": stats,
        "confianza": confidence,
        "comparables": [
            {key: value for key, value in row.items() if not key.startswith("_")}
            for row in candidates
        ],
        "precio_m2_por_estado_en_zona": state_context,
    }
    return market, quality_by_zone


def _price_context(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = []
    for row in rows:
        area, price = _number(row.get("area_m2")), _number(row.get("precio"))
        if area and area > 0 and price is not None:
            values.append(price / area)
    return {"n": len(values), "mediana": _round_integer(_median(values)) if values else None}


def _statistics(values: list[float]) -> dict[str, Any]:
    count = len(values)
    mean = sum(values) / count if count else None
    median = _median(values) if values else None
    deviation = math.sqrt(sum((value - mean) ** 2 for value in values) / (count - 1)) if count > 1 else None
    coefficient = deviation / mean if deviation is not None and mean else None
    return {
        "n": count,
        "mediana": _round_integer(median) if median is not None else None,
        "promedio": _round_integer(mean) if mean is not None else None,
        "minimo": _round_integer(min(values)) if values else None,
        "maximo": _round_integer(max(values)) if values else None,
        "desviacion": _round_integer(deviation) if deviation is not None else None,
        "coef_variacion": round(coefficient, 4) if coefficient is not None else None,
    }


def _confidence(count: int, coefficient: Optional[float], parameters: dict[str, Any]) -> dict[str, Any]:
    if count == 0:
        return {"nivel": None, "motivo": "No hay comparables válidos para calcular un resultado."}
    rules = parameters["confianza"]
    if count >= rules["alta"]["min_comparables"] and coefficient is not None and coefficient <= rules["alta"]["max_coef_variacion"]:
        level = "alta"
        reason = f"{count} comparables y coeficiente de variación {coefficient:.2%}; cumple la regla alta."
    elif count >= rules["media"]["min_comparables"] and coefficient is not None and coefficient <= rules["media"]["max_coef_variacion"]:
        level = "media"
        reason = f"{count} comparables y coeficiente de variación {coefficient:.2%}; cumple la regla media."
    else:
        level = "baja"
        variability = "no disponible" if coefficient is None else f"{coefficient:.2%}"
        reason = f"{count} comparables y coeficiente de variación {variability}; no cumple los umbrales superiores."
    return {"nivel": level, "motivo": reason}


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _number(value: Any) -> Optional[float]:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _round_integer(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _text(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def _clean(value: Any) -> Any:
    if value is None:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None
