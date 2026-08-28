"""
compute_outliers_core.py
Stage 1.3b: flag breakout outliers on the CORE window only.

Threshold (count-based, per locked methodology): 3x channel-format median if that
channel-format has >= 500 in-window videos, else 5x. Channel-format cells with fewer
than 8 in-window videos are marked thin_baseline=yes so they lean on absolute views.

Firewall: reads ONLY out/competitors_core_365d.csv.
Writes: out/outliers_core.csv  (sorted by outlier_ratio desc)
"""
import csv, statistics
from pathlib import Path
from collections import defaultdict

PROJ = Path(__file__).resolve().parent.parent
IN = PROJ / "out" / "competitors_core_365d.csv"
OUT = PROJ / "out" / "outliers_core.csv"
COUNT_CUTOFF = 500   # >= 500 in-window videos in the cell -> 3x, else 5x
THIN_MIN = 8         # below this many videos in the cell, lean on absolute views


def main():
    if not IN.exists():
        raise SystemExit(f"Missing {IN}. Run fetch_videos_layered.py first.")
    groups = defaultdict(list); rows = []
    with IN.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["view_count"] = int(r["view_count"] or 0)
            rows.append(r)
            groups[(r["channel"], r["format"])].append(r["view_count"])
    medians = {k: statistics.median(v) for k, v in groups.items() if v}
    counts = {k: len(v) for k, v in groups.items()}

    outliers = []
    for r in rows:
        key = (r["channel"], r["format"]); med = medians.get(key, 0); n = counts.get(key, 0)
        if med <= 0:
            continue
        thr = 3.0 if n >= COUNT_CUTOFF else 5.0
        if r["view_count"] >= thr * med:
            outliers.append({
                "channel": r["channel"], "video_id": r["video_id"], "title": r["title"],
                "format": r["format"], "published_at": r["published_at"], "view_count": r["view_count"],
                "channel_format_median": int(med), "channel_format_n": n,
                "outlier_ratio": round(r["view_count"] / med, 2), "threshold_applied": thr,
                "thin_baseline": "yes" if n < THIN_MIN else "no",
                "duration_seconds": r["duration_seconds"], "video_url": r["video_url"],
                "thumbnail_url": r["thumbnail_url"],
            })
    outliers.sort(key=lambda x: -x["outlier_ratio"])
    cols = ["channel", "video_id", "title", "format", "published_at", "view_count", "channel_format_median",
            "channel_format_n", "outlier_ratio", "threshold_applied", "thin_baseline", "duration_seconds",
            "video_url", "thumbnail_url"]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(outliers)

    print(f"Wrote {len(outliers)} outliers to {OUT}")
    bych = defaultdict(int); thin = 0
    for o in outliers:
        bych[o["channel"]] += 1
        if o["thin_baseline"] == "yes":
            thin += 1
    print("\n=== outliers by channel ===")
    for ch, n in sorted(bych.items()):
        print(f"  {ch:32s} {n}")
    print(f"\nthin-baseline outliers (cell < {THIN_MIN} videos): {thin}/{len(outliers)}")
    print("\n=== top 15 cross-channel by ratio ===")
    for o in outliers[:15]:
        flag = " [thin]" if o["thin_baseline"] == "yes" else ""
        print(f"  {o['channel']:24s} {o['format']:5s} {o['outlier_ratio']:6.1f}x views={o['view_count']:>9,}{flag}  {o['title'][:58]}")


if __name__ == "__main__":
    main()
