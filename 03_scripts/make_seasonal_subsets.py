"""make_seasonal_subsets.py
Extract May 1 - Aug 31 (2024 and 2025) rows from the raw extended and Hinglish files,
so only the seasonally relevant videos get tagged (the research question is seasonal).
Core is already fully tagged and covers the 2025 season for English.
Writes: out/to_tag_extended_seasonal.csv, out/to_tag_hinglish_seasonal.csv
"""
import csv
from pathlib import Path
from datetime import datetime

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / "out"


def season_of(pub):
    try:
        dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.month in (5, 6, 7, 8) and dt.year in (2024, 2025):
        return f"may_aug_{dt.year}"
    return None


def subset(src, dst):
    p = OUT / src
    if not p.exists():
        print(f"   (missing {src}, skipping)")
        return
    rows = []
    with p.open(encoding="utf-8") as f:
        rd = csv.DictReader(f)
        fields = rd.fieldnames
        for r in rd:
            if season_of(r.get("published_at", "")):
                rows.append(r)
    with (OUT / dst).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"{src} -> {dst}: {len(rows)} seasonal rows")


if __name__ == "__main__":
    subset("competitors_extended.csv", "to_tag_extended_seasonal.csv")
    subset("competitors_hinglish.csv", "to_tag_hinglish_seasonal.csv")
