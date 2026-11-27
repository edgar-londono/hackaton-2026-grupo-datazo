from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "geo"
OUTPUT_DIR = PROJECT_ROOT / "output" / "prepared" / "geo"
QUALITY_REPORT = PROJECT_ROOT / "output" / "geospatial_quality.md"
REVIEW_CSV = OUTPUT_DIR / "coincidencias_para_revision.csv"
INVALID_CSV = OUTPUT_DIR / "filas_invalidas.csv"
LAYERS = (
    ("equipamientos.geojson", "equipamientos_limpios.geojson", "categoria"),
    ("transporte.geojson", "transporte_limpio.geojson", "sistema"),
)


def _signature(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _read_layer(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        document = json.load(source)
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ValueError(f"Expected a GeoJSON FeatureCollection: {path}")
    if not isinstance(document.get("features"), list):
        raise ValueError(f"Expected a feature list: {path}")
    return document


def _validate_feature(
    feature: Any, category_field: str
) -> tuple[list[str], tuple[float, float] | None]:
    issues: list[str] = []
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        return ["El registro no tiene el tipo GeoJSON Feature."], None

    properties = feature.get("properties")
    if not isinstance(properties, dict):
        issues.append("Faltan las propiedades del registro.")
        properties = {}
    if not isinstance(properties.get("osm_id"), str) or not properties["osm_id"].strip():
        issues.append("Falta el identificador osm_id.")
    if not isinstance(properties.get(category_field), str) or not properties[category_field].strip():
        issues.append(f"Falta la categoría {category_field}.")

    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        issues.append("La geometría no es un punto.")
        return issues, None

    coordinates = geometry.get("coordinates")
    if (
        not isinstance(coordinates, list)
        or len(coordinates) != 2
        or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in coordinates)
    ):
        issues.append("Las coordenadas no tienen el formato longitud, latitud.")
        return issues, None

    longitude, latitude = coordinates
    if not math.isfinite(longitude) or not math.isfinite(latitude):
        issues.append("Las coordenadas no son números finitos.")
        return issues, None
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        issues.append("Las coordenadas están fuera del rango geográfico válido.")
        return issues, None
    return issues, (longitude, latitude)


def _review_row(
    layer_name: str,
    reason: str,
    group_id: str,
    row_number: int,
    feature: dict[str, Any],
    category_field: str,
) -> dict[str, str]:
    properties = feature["properties"]
    longitude, latitude = feature["geometry"]["coordinates"]
    return {
        "capa": layer_name,
        "motivo": reason,
        "grupo": group_id,
        "fila_origen": str(row_number),
        "longitud": str(longitude),
        "latitud": str(latitude),
        "osm_id": str(properties.get("osm_id", "")),
        "nombre": str(properties.get("nombre", "")),
        "categoria": str(properties.get(category_field, "")),
        "propiedades_json": json.dumps(properties, ensure_ascii=False, sort_keys=True),
    }


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def prepare_layer(
    source_path: Path,
    output_path: Path,
    layer_name: str,
    category_field: str,
) -> dict[str, Any]:
    document = _read_layer(source_path)
    valid_items: list[tuple[int, dict[str, Any], tuple[float, float]]] = []
    invalid_rows: list[dict[str, str]] = []
    seen: set[str] = set()
    exact_duplicates_removed = 0

    for row_number, feature in enumerate(document["features"], start=1):
        issues, coordinates = _validate_feature(feature, category_field)
        if issues:
            record = _signature(feature) if isinstance(feature, dict) else json.dumps(feature, ensure_ascii=False)
            invalid_rows.append({
                "capa": layer_name,
                "fila_origen": str(row_number),
                "motivos": "; ".join(issues),
                "registro_json": record,
            })
            continue

        signature = _signature(feature)
        if signature in seen:
            exact_duplicates_removed += 1
            continue
        seen.add(signature)
        valid_items.append((row_number, feature, coordinates))

    coordinate_groups: dict[tuple[float, float], list[tuple[int, dict[str, Any], tuple[float, float]]]] = defaultdict(list)
    id_groups: dict[str, list[tuple[int, dict[str, Any], tuple[float, float]]]] = defaultdict(list)
    for item in valid_items:
        row_number, feature, coordinates = item
        coordinate_groups[coordinates].append(item)
        id_groups[feature["properties"]["osm_id"]].append(item)

    review_rows: list[dict[str, str]] = []
    for coordinates, items in coordinate_groups.items():
        if len(items) > 1:
            group_id = f"{coordinates[0]},{coordinates[1]}"
            review_rows.extend(
                _review_row(layer_name, "Coordenadas coincidentes", group_id, row, feature, category_field)
                for row, feature, _ in items
            )
    for osm_id, items in id_groups.items():
        if len(items) > 1:
            review_rows.extend(
                _review_row(layer_name, "Identificador osm_id repetido", osm_id, row, feature, category_field)
                for row, feature, _ in items
            )

    output_document = dict(document)
    output_document["features"] = [feature for _, feature, _ in valid_items]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    categories = Counter(
        feature["properties"][category_field] for _, feature, _ in valid_items
    )
    unnamed = sum(
        not isinstance(feature["properties"].get("nombre"), str)
        or not feature["properties"]["nombre"].strip()
        for _, feature, _ in valid_items
    )
    return {
        "name": layer_name,
        "category_field": category_field,
        "input_count": len(document["features"]),
        "valid_count": len(valid_items),
        "invalid_count": len(invalid_rows),
        "exact_duplicates_removed": exact_duplicates_removed,
        "review_rows": review_rows,
        "invalid_rows": invalid_rows,
        "unnamed_count": unnamed,
        "category_counts": categories,
        "output_path": output_path,
    }


def _render_report(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Calidad de las capas geográficas",
        "",
        "La preparación valida los puntos y conserva los archivos fuente sin cambios. Solo quita filas GeoJSON idénticas en todos sus campos. Las coincidencias parciales se guardan para revisión.",
        "",
        "## Resumen",
        "",
        "| Capa | Filas de entrada | Filas preparadas | Filas inválidas | Duplicados idénticos retirados | Nombres vacíos |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result['name']} | {result['input_count']} | {result['valid_count']} | "
            f"{result['invalid_count']} | {result['exact_duplicates_removed']} | {result['unnamed_count']} |"
        )
    lines.extend(["", "## Categorías", ""])
    for result in results:
        lines.extend([f"### {result['name']}", "", f"Campo: {result['category_field']}.", ""])
        lines.extend(
            f"- {category}: {count}"
            for category, count in sorted(result["category_counts"].items())
        )
        lines.append("")

    review_count = sum(len(result["review_rows"]) for result in results)
    invalid_count = sum(len(result["invalid_rows"]) for result in results)
    lines.extend([
        "## Revisión y datos faltantes",
        "",
        f"- Registros con coordenadas compartidas o identificador osm_id repetido: {review_count}. Se conservan en la capa preparada.",
        f"- Registros con geometría o campos obligatorios inválidos: {invalid_count}. Se guardan en el CSV de filas inválidas y no entran en la capa preparada.",
        "- Los nombres vacíos se conservan. No se inventan nombres, y el conteo por categoría no depende de ellos.",
        "- Las coordenadas GeoJSON se interpretan en orden longitud, latitud y se validan contra los rangos geográficos globales.",
        "",
        f"Los registros marcados para revisión están en {REVIEW_CSV.relative_to(PROJECT_ROOT).as_posix()}.",
        f"Las filas inválidas están en {INVALID_CSV.relative_to(PROJECT_ROOT).as_posix()}.",
        "",
        "## Capas preparadas",
        "",
    ])
    lines.extend(
        f"- {result['output_path'].relative_to(PROJECT_ROOT).as_posix()}"
        for result in results
    )
    lines.append("")
    return "\n".join(lines)


def prepare_geospatial_data() -> Path:
    results = [
        prepare_layer(
            DATA_DIR / source_name,
            OUTPUT_DIR / output_name,
            source_name,
            category_field,
        )
        for source_name, output_name, category_field in LAYERS
    ]
    _write_csv(
        REVIEW_CSV,
        [row for result in results for row in result["review_rows"]],
        ["capa", "motivo", "grupo", "fila_origen", "longitud", "latitud", "osm_id", "nombre", "categoria", "propiedades_json"],
    )
    _write_csv(
        INVALID_CSV,
        [row for result in results for row in result["invalid_rows"]],
        ["capa", "fila_origen", "motivos", "registro_json"],
    )
    QUALITY_REPORT.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_REPORT.write_text(_render_report(results), encoding="utf-8")
    return QUALITY_REPORT


if __name__ == "__main__":
    print(prepare_geospatial_data())
