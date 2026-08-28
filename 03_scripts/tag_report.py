"""tag_report.py — tag-distribution sanity report for a tagged CSV.
Usage: tag_report.py [path-to-tagged-csv]  (default: out/competitor_videos_tagged_core.csv)
"""
import csv, sys
from pathlib import Path
from collections import Counter

PROJ = Path(__file__).resolve().parent.parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJ / "out" / "competitor_videos_tagged_core.csv"
rows = list(csv.DictReader(path.open(encoding="utf-8")))
n = len(rows)
print(f"{path.name}: {n} rows")
all_other = sum(1 for r in rows if r.get("topic") == "other" and r.get("format_archetype") == "other"
                and r.get("hook_type") == "other" and r.get("language") == "other")
print(f"all-other rows (failed calls): {all_other} ({100*all_other/n:.1f}%)")
for col in ["topic", "format_archetype", "hook_type", "language"]:
    c = Counter((r.get(col, "") or "blank") for r in rows)
    print(f"\n{col}:")
    for k, v in c.most_common(18):
        print(f"   {v:5d} {100*v/n:5.1f}%  {k}")
