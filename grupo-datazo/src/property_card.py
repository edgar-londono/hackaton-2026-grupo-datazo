"""Markdown rendering for property analysis records."""

from __future__ import annotations

from typing import Any, Optional


def render_card(record: dict[str, Any]) -> str:
    property_data = record["inmueble"]
    market = record["mercado"]
    price = market["precio_m2"]
    confidence = market["confianza"]
    neighborhood = record["entorno"]
    nearest = neighborhood["estacion_mas_cercana"]
    zoning = record["norma"]
    quality = record["calidad_datos_zona"]

    lines = [
        f"# Property market and neighborhood card: {record['id_inmueble']}",
        "",
        f"Generated: {record['metadatos']['fecha_generacion']}",
        "",
        "## Property",
        "",
        f"- Address: {_display(property_data.get('direccion'))}",
        f"- Neighborhood: {_display(property_data.get('barrio'))}",
        f"- Municipality: {_display(property_data.get('municipio'))}",
        f"- Market zone: {_display(property_data.get('zona'))}",
        f"- Area: {_display(property_data.get('area_m2'), 'm²')}",
        f"- Condition: {_display(property_data.get('estado'))} (source text: {_display(property_data.get('estado_texto'))})",
        f"- Coordinates: {_coordinate_display(property_data.get('coordenadas'))}",
        "",
        "## Market summary",
        "",
        f"- Reference condition: {_display(market.get('estado_referencia'))}",
        f"- Comparable listings: {price['n']}",
        f"- Median asking price per m²: {_cop(price.get('mediana'))}",
        f"- Range: {_cop(price.get('minimo'))} to {_cop(price.get('maximo'))}",
        f"- Mean: {_cop(price.get('promedio'))}",
        f"- Sample standard deviation: {_cop(price.get('desviacion'))}",
        f"- Coefficient of variation: {_percent(price.get('coef_variacion'))}",
        f"- Confidence: {_display(confidence.get('nivel'))}. {confidence.get('motivo', '')}",
        "",
        "### Zone context by condition",
        "",
        "| Condition | Valid listings | Median asking price per m² |",
        "|---|---:|---:|",
    ]
    for condition, summary in market["precio_m2_por_estado_en_zona"].items():
        lines.append(f"| {condition} | {summary['n']} | {_cop(summary.get('mediana'))} |")

    lines.extend(["", "### Comparables", ""])
    if market["comparables"]:
        lines.extend([
            "| Source record | Listing ID | Source | Area | Asking price | Price per m² |",
            "|---|---|---|---:|---:|---:|",
        ])
        for comparable in market["comparables"]:
            lines.append(
                f"| {_display(comparable.get('origen'))} | {_display(comparable.get('id_anuncio'))} | "
                f"{_display(comparable.get('fuente'))} | {_display(comparable.get('area_m2'), 'm²')} | "
                f"{_cop(comparable.get('precio'))} | {_cop(comparable.get('precio_m2'))} |"
            )
    else:
        lines.append("Insufficient data: no valid comparable listings match the configured rules.")

    lines.extend([
        "",
        "## Neighborhood summary",
        "",
        f"- Search radius: {neighborhood['radio_busqueda_m']} m",
        f"- Coordinate precision: {'Approximate neighborhood point' if neighborhood['aproximado'] else 'Intersection or supplied point'}",
        f"- Nearest supported transit station: {_station_display(nearest)}",
        f"- Supported stations within radius: {_display(neighborhood.get('estaciones_en_radio'))}",
        "",
        "| Facility category | Count within radius |",
        "|---|---:|",
    ])
    facilities = neighborhood.get("equipamientos_en_radio")
    for category, count in (facilities or {}).items():
        lines.append(f"| {category} | {count} |")
    if facilities is None:
        lines.append("| Not available | Insufficient data |")

    lines.extend([
        "",
        "## Urban planning",
        "",
        f"- POT treatment: {_display(zoning.get('tratamiento_pot'))}",
        f"- Status: {zoning['estado']}. {zoning['motivo']}",
        "",
        "## Data quality and limits",
        "",
        f"- Listings in zone: {quality['anuncios_en_zona']}",
        f"- Exact duplicate rows removed: {quality['duplicados_eliminados']}",
        f"- Unique source rows after exact deduplication: {quality['anuncios_unicos']}",
        f"- Valid listings used for analysis: {quality['anuncios_validos']}",
        f"- Candidate listings held out for review: {quality['anuncios_pendientes_revision']} rows in {quality['grupos_pendientes_revision']} groups",
        f"- Invalid unique rows not held for review: {quality['filas_invalidas_unicas']}",
        f"- Invalid listings by reason: {_format_counts(quality['anuncios_invalidos'])}",
        f"- Missing or unavailable data: {_format_missing(record['datos_faltantes'])}",
        "",
        "## Sources",
        "",
        f"- Files: {', '.join(record['metadatos']['fuentes'])}",
        f"- Parameter version: {record['metadatos']['version_parametros']}",
        f"- Geographic layer date: {_display(record['metadatos'].get('fecha_capas_osm'))}",
        "",
        "This card reports asking prices. It does not estimate closing prices or recommend an investment decision.",
        "",
    ])
    return "\n".join(lines)


def _display(value: Any, suffix: str = "") -> str:
    if value is None or value == "":
        return "Insufficient data"
    return f"{value}{suffix}"


def _coordinate_display(coordinates: Optional[dict[str, Any]]) -> str:
    if not coordinates or coordinates.get("lat") is None or coordinates.get("lon") is None:
        return "Insufficient data"
    label = "approximate" if coordinates.get("precision") == "barrio" else "source point"
    return f"{coordinates['lat']}, {coordinates['lon']} ({label})"


def _cop(value: Any) -> str:
    return "Insufficient data" if value is None else f"COP {value:,.0f}"


def _percent(value: Any) -> str:
    return "Insufficient data" if value is None else f"{value:.2%}"


def _station_display(station: Optional[dict[str, Any]]) -> str:
    if not station:
        return "Insufficient data"
    return f"{station['nombre']} ({station['sistema']}) at {station['distancia_m']} m"


def _format_counts(counts: dict[str, int]) -> str:
    return "; ".join(f"{reason}: {count}" for reason, count in counts.items()) or "None reported"


def _format_missing(fields: list[str]) -> str:
    return "; ".join(fields) if fields else "None reported"
