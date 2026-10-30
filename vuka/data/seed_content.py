from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from database import SessionLocal
from vuka.models.contents import Content
import vuka.models  
from vuka.models.verifiedassessment import VerifiedAssessment  
from vuka.models.userprogress import UserProgress  

DEFAULT_CSV = Path(__file__).parent / "content_seed.csv"


def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")


def run(csv_path: Path) -> None:
    db = SessionLocal()
    inserted, updated = 0, 0
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                content_id = int(row["content_id"])
                data = {
                    "external_media_url": row["external_media_url"].strip(),
                    "source_platform": row["source platform"].strip(),
                    "media_description": (row.get("media_description") or "No description provided.").strip()
                    or "No description provided.",
                    "datetime": parse_datetime(row["datetime"]),
                }

                existing = db.get(Content, content_id)
                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    updated += 1
                else:
                    db.add(Content(content_id=content_id, **data))
                    inserted += 1

        db.commit()
        print(f"Seed complete: {inserted} inserted, {updated} updated from {csv_path}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the content table from a CSV export.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to the content CSV file.")
    args = parser.parse_args()
    run(args.csv)