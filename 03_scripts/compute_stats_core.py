"""
compute_stats_core.py
Stage 1.3a: per-channel-format baseline stats on the CORE window only.
Firewall: reads ONLY out/competitors_core_365d.csv. Extended/Hinglish never enter the ratio basis.
Writes: out/channel_format_stats.csv
"""
import csv, statistics
from pathlib import Path
from collections import defaultdict

PROJ = Path(__file__).resolve().parent.parent
IN = PROJ / "out" / "competitors_core_365d.csv"
OUT = PROJ / "out" / "channel_format_stats.csv"


def main():
    if not IN.exists():
        raise SystemExit(f"Missing {IN}. Run fetch_videos_layered.py first.")
    groups = defaultdict(list)
    with IN.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            groups[(r["channel"], r["format"])].append(int(r["view_count"] or 0))
    rows = []
    for (ch, fmt), views in sorted(groups.items()):
        n = len(views)
        rows.append({
            "channel": ch, "format": fmt, "n_videos": n,
            "median": int(statistics.median(views)) if views else 0,
            "mean": int(statistics.mean(views)) if views else 0,
            "p75": int(statistics.quantiles(views, n=4)[2]) if n >= 4 else "",
            "p90": int(statistics.quantiles(views, n=10)[8]) if n >= 10 else "",
            "max": max(views) if views else 0,
        })
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["channel", "format", "n_videos", "median", "mean", "p75", "p90", "max"])
        w.writeheader(); w.writerows(rows)
    print(f"Wrote {OUT}")
    print("\n=== channel-format baselines (core window) ===")
    for r in rows:
        print(f"  {r['channel']:32s} {r['format']:6s} n={r['n_videos']:4d} median={r['median']:>9,} max={r['max']:>10,}")


if __name__ == "__main__":
    main()
