"""
seasonal_slice.py
Stage 1.5: isolate the May 1 - Aug 31 seasons (2025 and 2024) across all layers and
rank what won, by topic, format, and hook. Free (operates on already-tagged data).

Full May is captured: for established channels, May 1-19 2025 sits in the extended file
and May 20-31 2025 in the core file; both are caught by the season filter.

Reads (whichever exist):
  out/competitor_videos_tagged_core.csv      (English, 2025 season)
  out/competitor_videos_tagged_extended.csv  (English, 2024 season + early-May 2025)
  out/competitor_videos_tagged_hinglish.csv  (Hinglish, both seasons)
Writes:
  out/seasonal_may_aug_2025.csv, out/seasonal_may_aug_2024.csv
  out/seasonal_topic_performance.csv
  out/seasonal_summary.md
"""
import csv, statistics
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / "out"
FILES = ["competitor_videos_tagged_core.csv", "competitor_videos_tagged_extended_seasonal.csv",
         "competitor_videos_tagged_hinglish_seasonal.csv"]


def season_of(pub):
    try:
        dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.month in (5, 6, 7, 8):
        if dt.year == 2025:
            return "may_aug_2025"
        if dt.year == 2024:
            return "may_aug_2024"
    return None


def load_rows():
    rows = []
    for fn in FILES:
        p = OUT / fn
        if not p.exists():
            print(f"   (missing {fn}, skipping)")
            continue
        with p.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                r["view_count"] = int(r["view_count"] or 0)
                rows.append(r)
    return rows


def main():
    rows = load_rows()
    for r in rows:
        r["season"] = season_of(r.get("published_at", ""))
    seasonal = [r for r in rows if r["season"]]

    cols = ["season", "source_language", "channel", "format", "topic", "format_archetype", "hook_type",
            "language", "view_count", "like_count", "comment_count", "published_at", "title", "video_url"]
    for season in ("may_aug_2025", "may_aug_2024"):
        sub = sorted([r for r in seasonal if r["season"] == season], key=lambda x: -x["view_count"])
        with (OUT / f"seasonal_{season}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader(); w.writerows(sub)

    perf = defaultdict(list)
    for r in seasonal:
        perf[(r["season"], r.get("source_language", "?"), r.get("topic", "other"))].append(r["view_count"])
    with (OUT / "seasonal_topic_performance.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["season", "group", "topic", "n_videos", "total_views", "median_views", "max_views"])
        for (s, g, t), v in sorted(perf.items(), key=lambda kv: (kv[0][0], kv[0][1], -sum(kv[1]))):
            w.writerow([s, g, t, len(v), sum(v), int(statistics.median(v)), max(v)])

    lines = ["# Seasonal performance: May to August (2025 and 2024)\n"]
    for season in ("may_aug_2025", "may_aug_2024"):
        for group in ("english", "hinglish"):
            sub = [r for r in seasonal if r["season"] == season and r.get("source_language") == group]
            if not sub:
                continue
            lines.append(f"\n## {season} | {group} | {len(sub)} videos\n")
            lines.append("Top 15 by views:\n")
            for r in sorted(sub, key=lambda x: -x["view_count"])[:15]:
                lines.append(f"- {r['view_count']:>9,} | {r['format']:5s} | {r.get('topic','')}/{r.get('hook_type','')} | {r['channel']} | {r['title'][:80]}")
            tp = defaultdict(list)
            for r in sub:
                tp[r.get("topic", "other")].append(r["view_count"])
            lines.append("\nTopics by total views:\n")
            for t, v in sorted(tp.items(), key=lambda kv: -sum(kv[1]))[:12]:
                lines.append(f"- {t}: {len(v)} vids, {sum(v):,} total, median {int(statistics.median(v)):,}")
            fp = defaultdict(list)
            for r in sub:
                fp[r["format"]].append(r["view_count"])
            lines.append("\nFormat split (videos | total views | median):\n")
            for fmt in ("short", "long", "live"):
                if fmt in fp:
                    v = fp[fmt]
                    lines.append(f"- {fmt}: {len(v)} | {sum(v):,} | {int(statistics.median(v)):,}")
    (OUT / "seasonal_summary.md").write_text("\n".join(lines), encoding="utf-8")

    n25 = sum(1 for r in seasonal if r["season"] == "may_aug_2025")
    n24 = sum(1 for r in seasonal if r["season"] == "may_aug_2024")
    print(f"Seasonal videos: {len(seasonal)} ({n25} in 2025, {n24} in 2024)")
    print("Wrote seasonal_may_aug_2025.csv, seasonal_may_aug_2024.csv, seasonal_topic_performance.csv, seasonal_summary.md")


if __name__ == "__main__":
    main()
