"""Neighborhood distance and count calculations for supplied GeoJSON layers."""

from __future__ import annotations

import math
from typing import Any, Optional


EARTH_RADIUS_METERS = 6_371_008.8


def analyze_neighborhood(
    property_row: dict[str, Any],
    transit_layer: Optional[dict[str, Any]],
    facility_layer: Optional[dict[str, Any]],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    latitude = _number(property_row.get("lat"))
    longitude = _number(property_row.get("lon"))
    radius = int(parameters["entorno"]["radio_busqueda_m"])
    precision = property_row.get("precision_coordenadas")
    result: dict[str, Any] = {
        "radio_busqueda_m": radius,
        "estacion_mas_cercana": None,
        "estaciones_en_radio": None,
        "equipamientos_en_radio": None,
        "aproximado": precision == "barrio",
    }
    if latitude is None or longitude is None or not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        return result

    supported_systems = {_text(item) for item in parameters["entorno"]["sistemas_transporte"]}
    transit_items: list[tuple[float, str, str]] = []
    if transit_layer is not None:
        for feature in transit_layer.get("features", []):
            coordinates = _coordinates(feature)
            properties = feature.get("properties", {}) if isinstance(feature, dict) else {}
            system = _text(properties.get("sistema"))
            if coordinates is None or system not in supported_systems:
                continue
            lon, lat = coordinates
            distance = haversine_meters(latitude, longitude, lat, lon)
            transit_items.append((distance, str(properties.get("nombre") or ""), system))
    if transit_layer is not None:
        result["estaciones_en_radio"] = sum(distance <= radius for distance, _, _ in transit_items)
        if transit_items:
            distance, name, system = min(transit_items, key=lambda item: (item[0], item[1], item[2]))
            result["estacion_mas_cercana"] = {
                "nombre": name or None,
                "sistema": system,
                "distancia_m": int(math.floor(distance + 0.5)),
            }

    if facility_layer is not None:
        categories = _facility_categories(parameters)
        counts = {category: 0 for category in categories}
        for feature in facility_layer.get("features", []):
            coordinates = _coordinates(feature)
            if coordinates is None:
                continue
            lon, lat = coordinates
            if haversine_meters(latitude, longitude, lat, lon) > radius:
                continue
            properties = feature.get("properties", {}) if isinstance(feature, dict) else {}
            category = _text(properties.get("categoria"))
            if category in counts:
                counts[category] += 1
        result["equipamientos_en_radio"] = counts
    return result


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in meters using the reference radius."""
    latitude_1, latitude_2 = math.radians(lat1), math.radians(lat2)
    delta_latitude = math.radians(lat2 - lat1)
    delta_longitude = math.radians(lon2 - lon1)
    haversine = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(latitude_1) * math.cos(latitude_2) * math.sin(delta_longitude / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * math.asin(math.sqrt(min(1.0, haversine)))


def _facility_categories(parameters: dict[str, Any]) -> list[str]:
    return list(parameters["entorno"]["categorias_equipamientos"])


def _coordinates(feature: Any) -> Optional[tuple[float, float]]:
    if not isinstance(feature, dict):
        return None
    geometry = feature.get("geometry")
    coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
    if not isinstance(coordinates, list) or len(coordinates) != 2:
        return None
    longitude, latitude = _number(coordinates[0]), _number(coordinates[1])
    if longitude is None or latitude is None or not (-180 <= longitude <= 180) or not (-90 <= latitude <= 90):
        return None
    return longitude, latitude


def _number(value: Any) -> Optional[float]:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _text(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())
