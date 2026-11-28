import csv
import json
from pathlib import Path


PRESENTATION_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PRESENTATION_DIR.parent
HTML_PATH = PRESENTATION_DIR / "limpieza_datos.html"
REVIEW_PATH = PROJECT_DIR / "output" / "prepared" / "posibles_repeticiones.csv"
DATA_SCRIPT_OPEN = '<script id="review-data" type="application/json">'
DATA_SCRIPT_CLOSE = "</script>"
GEO_REVIEW_PATH = PROJECT_DIR / "output" / "prepared" / "geo" / "coincidencias_para_revision.csv"
GEO_DATA_SCRIPT_OPEN = '<script id="geo-review-data" type="application/json">'


def embed_review_rows() -> None:
    with REVIEW_PATH.open(encoding="utf-8", newline="") as review_file:
        rows = list(csv.DictReader(review_file))

    with GEO_REVIEW_PATH.open(encoding="utf-8-sig", newline="") as geo_review_file:
        geo_rows = list(csv.DictReader(geo_review_file))

    html = HTML_PATH.read_text(encoding="utf-8")
    start = html.index(DATA_SCRIPT_OPEN) + len(DATA_SCRIPT_OPEN)
    end = html.index(DATA_SCRIPT_CLOSE, start)
    data = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    html = html[:start] + data + html[end:]
    geo_start = html.index(GEO_DATA_SCRIPT_OPEN) + len(GEO_DATA_SCRIPT_OPEN)
    geo_end = html.index(DATA_SCRIPT_CLOSE, geo_start)
    geo_data = json.dumps(geo_rows, ensure_ascii=False).replace("</", "<\\/")
    HTML_PATH.write_text(html[:geo_start] + geo_data + html[geo_end:], encoding="utf-8")
    print(f"Embedded {len(rows)} listing rows and {len(geo_rows)} geographic review rows in {HTML_PATH}")


if __name__ == "__main__":
    embed_review_rows()
