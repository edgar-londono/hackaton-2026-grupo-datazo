"""Copy generated MVP records into the static GitHub Pages site."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECORDS = ROOT / "grupo-datazo" / "output" / "fichas"
CARDS = ROOT / "grupo-datazo" / "output" / "cards"
SITE_DATA = ROOT / "docs" / "data"


def main() -> None:
    records_dir = SITE_DATA / "fichas"
    cards_dir = SITE_DATA / "cards"
    records_dir.mkdir(parents=True, exist_ok=True)
    cards_dir.mkdir(parents=True, exist_ok=True)

    records = sorted(RECORDS.glob("INM-*.json"))
    if not records:
        raise SystemExit(f"No MVP records found in {RECORDS}")

    for record in records:
        card = CARDS / f"{record.stem}.md"
        if not card.is_file():
            raise SystemExit(f"Missing generated property card: {card}")
        shutil.copyfile(record, records_dir / record.name)
        shutil.copyfile(card, cards_dir / card.name)

    print(f"Published {len(records)} MVP property records and cards to {SITE_DATA}")


if __name__ == "__main__":
    main()
