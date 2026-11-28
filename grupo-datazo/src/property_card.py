"""Markdown rendering for property analysis records."""

from __future__ import annotations

from typing import Any, Optional


CONDITIONS = {
    "habitable": "Habitable",
    "por_remodelar": "Por remodelar",
    "remodelado": "Remodelado",
    "sin_clasificar": "Sin clasificar",
}
FIELD_LABELS = {
    "coordenadas_exactas": "Coordenadas exactas",
    "direccion": "Dirección",
    "fecha_publicacion_comparables": "Fecha de publicación de anuncios comparables",
    "precios_de_cierre": "Precios de cierre",
    "estado_sin_clasificar": "Estado sin clasificar",
    "sin_area": "Área faltante",
}
CATEGORIES = {
    "educacion": "Educación",
    "salud": "Salud",
    "parques": "Parques",
    "abastecimiento": "Abastecimiento",
    "seguridad": "Seguridad",
    "cultura": "Cultura",
}
SOURCE_LABELS = {
    "OpenStreetMap transit layer (ODbL)": "Capa de transporte de OpenStreetMap (ODbL)",
    "OpenStreetMap facility layer (ODbL)": "Capa de equipamientos de OpenStreetMap (ODbL)",
}


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
        f"# Ficha de mercado y entorno: {record['id_inmueble']}",
        "",
        f"Generada: {record['metadatos']['fecha_generacion']}",
        "",
        "## Inmueble",
        "",
        f"- Dirección reportada: {_display(property_data.get('direccion'))}",
        f"- Barrio: {_display(property_data.get('barrio'))}",
        f"- Municipio: {_municipality(property_data.get('municipio'))}",
        f"- Zona de mercado: {_label(property_data.get('zona'))}",
        f"- Área: {_display(property_data.get('area_m2'), ' m²')}",
        f"- Estado reportado: {_condition(property_data.get('estado'))} (texto de la fuente: {_display(property_data.get('estado_texto'))})",
        f"- Coordenadas: {_coordinate_display(property_data.get('coordenadas'))}",
        "",
        "## Resumen de mercado",
        "",
        f"- Estado de referencia: {_condition(market.get('estado_referencia'))}",
        f"- Anuncios comparables: {price['n']}",
        f"- Mediana del precio anunciado por m²: {_cop(price.get('mediana'))}",
        f"- Rango de precios anunciados: {_cop(price.get('minimo'))} a {_cop(price.get('maximo'))}",
        f"- Promedio: {_cop(price.get('promedio'))}",
        f"- Desviación estándar muestral: {_cop(price.get('desviacion'))}",
        f"- Coeficiente de variación: {_percent(price.get('coef_variacion'))}",
        f"- Nivel de confianza: {_label(confidence.get('nivel'))}. {confidence.get('motivo', '')}",
        "",
        "### Comparación por estado en la zona",
        "",
        "| Estado | Anuncios válidos | Mediana del precio anunciado por m² |",
        "|---|---:|---:|",
    ]
    for condition, summary in market["precio_m2_por_estado_en_zona"].items():
        lines.append(f"| {_condition(condition)} | {summary['n']} | {_cop(summary.get('mediana'))} |")

    lines.extend(["", "### Anuncios comparables", ""])
    if market["comparables"]:
        lines.extend([
            "| Registro de origen | Identificador | Fuente | Área | Precio anunciado | Precio por m² |",
            "|---|---|---|---:|---:|---:|",
        ])
        for comparable in market["comparables"]:
            lines.append(
                f"| {_display(comparable.get('origen'))} | {_display(comparable.get('id_anuncio'))} | "
                f"{_label(comparable.get('fuente'))} | {_display(comparable.get('area_m2'), ' m²')} | "
                f"{_cop(comparable.get('precio'))} | {_cop(comparable.get('precio_m2'))} |"
            )
    else:
        lines.append("No hay anuncios comparables válidos que cumplan los criterios configurados.")

    lines.extend([
        "",
        "## Entorno geográfico",
        "",
        f"- Radio de análisis: {neighborhood['radio_busqueda_m']} m",
        f"- Precisión de las coordenadas: {_coordinate_precision(neighborhood['aproximado'])}",
        f"- Estación de transporte más cercana: {_station_display(nearest)}",
        f"- Estaciones de transporte dentro del radio: {_display(neighborhood.get('estaciones_en_radio'))}",
        "",
        "| Categoría de equipamiento | Puntos dentro del radio |",
        "|---|---:|",
    ])
    facilities = neighborhood.get("equipamientos_en_radio")
    for category, count in (facilities or {}).items():
        lines.append(f"| {CATEGORIES.get(category, _label(category))} | {count} |")
    if facilities is None:
        lines.append("| No disponible | Datos insuficientes |")

    lines.extend([
        "",
        "## Planeación urbana",
        "",
        f"- Tratamiento del Plan de Ordenamiento Territorial (POT): {_display(zoning.get('tratamiento_pot'))}",
        f"- Estado: {_label(zoning['estado'])}. {zoning['motivo']}",
        "",
        "## Calidad de los datos y límites",
        "",
        f"- Anuncios en la zona: {quality['anuncios_en_zona']}",
        f"- Filas idénticas retiradas: {quality['duplicados_eliminados']}",
        f"- Filas de origen únicas tras la deduplicación exacta: {quality['anuncios_unicos']}",
        f"- Filas conservadas tras retirar duplicados exactos: {quality['anuncios_conservados']}",
        f"- Filas con posibles coincidencias: {quality['posibles_repeticiones']} en {quality['grupos_posibles_repeticiones']} grupos",
        f"- Tratamiento de posibles coincidencias: {'Incluidas' if quality['candidatos_incluidos_en_calculos'] else 'Excluidas'}",
        f"- Filas con posibles coincidencias seleccionadas en esta zona: {quality['candidatos_seleccionados_en_zona']}",
        f"- Filas únicas con problemas de datos: {quality['filas_invalidas_unicas']}",
        f"- Incidencias por campo en esta zona: {_format_counts(quality['anuncios_invalidos'])}",
        f"- Datos faltantes o no disponibles: {_format_missing(record['datos_faltantes'])}",
        "",
        "## Fuentes",
        "",
        f"- Archivos y capas: {', '.join(SOURCE_LABELS.get(source, source) for source in record['metadatos']['fuentes'])}",
        f"- Versión de parámetros: {record['metadatos']['version_parametros']}",
        f"- Fecha de las capas de OpenStreetMap: {_display(record['metadatos'].get('fecha_capas_osm'))}",
        "",
        "Los precios corresponden a los anuncios suministrados. No se confirmaron con fuentes oficiales.",
        "",
    ])
    return "\n".join(lines)


def _display(value: Any, suffix: str = "") -> str:
    if value is None or value == "":
        return "No disponible"
    return f"{value}{suffix}"


def _condition(value: Any) -> str:
    return CONDITIONS.get(str(value), _label(value)) if value else "No disponible"


def _label(value: Any) -> str:
    if value is None or value == "":
        return "No disponible"
    return " ".join(part.capitalize() for part in str(value).replace("_", " ").split())


def _municipality(value: Any) -> str:
    return {"medellin": "Medellín", "itagui": "Itagüí"}.get(str(value), _display(value))


def _coordinate_display(coordinates: Optional[dict[str, Any]]) -> str:
    if not coordinates or coordinates.get("lat") is None or coordinates.get("lon") is None:
        return "No disponible"
    precision = "aproximadas" if coordinates.get("precision") == "barrio" else "del punto de referencia"
    return f"{coordinates['lat']}, {coordinates['lon']} ({precision})"


def _coordinate_precision(approximate: bool) -> str:
    return "Aproximada por barrio" if approximate else "Punto de referencia o intersección"


def _cop(value: Any) -> str:
    return "Datos insuficientes" if value is None else f"COP {value:,.0f}".replace(",", ".")


def _percent(value: Any) -> str:
    return "Datos insuficientes" if value is None else f"{value:.2%}".replace(".", ",")


def _station_display(station: Optional[dict[str, Any]]) -> str:
    if not station:
        return "No disponible"
    return f"{station['nombre']} ({_label(station['sistema'])}), a {station['distancia_m']} m"


def _format_counts(counts: dict[str, int]) -> str:
    return "; ".join(f"{FIELD_LABELS.get(reason, _label(reason))}: {count}" for reason, count in counts.items()) or "Ninguna"


def _format_missing(fields: list[str]) -> str:
    return "; ".join(FIELD_LABELS.get(field, _label(field)) for field in fields) if fields else "Ninguno"
