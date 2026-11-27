import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


@dataclass(frozen=True)
class LoadedInputs:
    listings: list[dict[str, Any]]
    properties: list[dict[str, Any]]
    transit: dict[str, Any]
    facilities: dict[str, Any]


def load_inputs(data_dir: Path = DATA_DIR) -> LoadedInputs:
    """Load the supplied CSV and GeoJSON inputs from the team data folder."""
    listings = _read_csv(data_dir / "anuncios_muestra.csv")
    properties = _read_csv(data_dir / "inmuebles_prueba.csv")
    transit = _read_geojson(data_dir / "geo" / "transporte.geojson")
    facilities = _read_geojson(data_dir / "geo" / "equipamientos.geojson")

    return LoadedInputs(
        listings=listings,
        properties=properties,
        transit=transit,
        facilities=facilities,
    )


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header row: {path}")
        return list(reader)


def _read_geojson(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as geojson_file:
        document = json.load(geojson_file)

    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ValueError(f"Expected a GeoJSON FeatureCollection: {path}")
    if not isinstance(document.get("features"), list):
        raise ValueError(f"GeoJSON FeatureCollection has no feature list: {path}")
    return document
