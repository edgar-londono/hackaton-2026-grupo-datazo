import csv
import json
from pathlib import Path


PRESENTATION_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PRESENTATION_DIR.parent
HTML_PATH = PRESENTATION_DIR / "limpieza_datos.html"
REVIEW_PATH = PROJECT_DIR / "output" / "prepared" / "duplicados_para_revision.csv"
DATA_SCRIPT_OPEN = '<script id="review-data" type="application/json">'
DATA_SCRIPT_CLOSE = "</script>"


def embed_review_rows() -> None:
    with REVIEW_PATH.open(encoding="utf-8", newline="") as review_file:
        rows = list(csv.DictReader(review_file))

    html = HTML_PATH.read_text(encoding="utf-8")
    start = html.index(DATA_SCRIPT_OPEN) + len(DATA_SCRIPT_OPEN)
    end = html.index(DATA_SCRIPT_CLOSE, start)
    data = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    HTML_PATH.write_text(html[:start] + data + html[end:], encoding="utf-8")
    print(f"Embedded {len(rows)} rows in {HTML_PATH}")


if __name__ == "__main__":
    embed_review_rows()
