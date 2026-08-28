"""
resolve_channels.py
Phase A: resolve your competitor set to UC ids.

For each channel: search by name, fetch snippet+statistics+uploads-playlist for
candidates, print all candidates, auto-pick the one whose subscriber count best
matches your expected value, and flag low-confidence picks for manual review.

Output: out/channels_resolved.csv  (+ printed table)
Never prints API keys.
"""
import os, csv
from pathlib import Path
import requests
from dotenv import load_dotenv

PROJ = Path(__file__).resolve().parent.parent
load_dotenv(PROJ / ".env")
API_KEY = os.getenv("YT_API_KEY")
if not API_KEY or "your_" in API_KEY:
    raise SystemExit("ERROR: YT_API_KEY missing or placeholder in .env")

OUT_DIR = PROJ / "out"; OUT_DIR.mkdir(exist_ok=True)
OUT_CSV = OUT_DIR / "channels_resolved.csv"
BASE = "https://www.googleapis.com/youtube/v3"

# EXAMPLE VALUES — replace with your own competitor set (7 to 14 channels is the sweet spot; see
# 01_pipeline_playbook.md section 1). (search name, expected subs from your own primer research,
# tier, language, layers). tier: 1/2 = competitors, 0 = your own index channel, 9 = cross-language
# fallback. layers: which data layers this channel feeds (see CLAUDE.md section 6, the firewall).
CHANNELS = [
    ("Example Competitor 1", 200000, 1, "english", "core+extended"),
    ("Example Competitor 2", 185000, 1, "english", "core+extended"),
    ("Example Competitor 3", 118000, 1, "english", "core+extended"),
    ("Example Young Channel", 5500, 1, "english", "core"),
    ("Example Competitor 4", 168000, 2, "english", "core+extended"),
    ("Example Competitor 5", 29000, 2, "english", "core+extended"),
    ("Example Competitor 6", 44000, 2, "english", "core+extended"),
    ("Example Competitor 7", 14000, 2, "english", "core+extended"),
    ("Example Competitor 8", 91000, 2, "english", "core+extended"),
    ("Example Competitor 9", 64000, 2, "english", "core+extended"),
    ("Your Channel", 2000, 0, "english", "core"),
    ("Example Cross-Language Fallback 1", 150000, 9, "cross-language", "cross-language"),
    ("Example Cross-Language Fallback 2", 400000, 9, "cross-language", "cross-language"),
]


def api_get(endpoint, params):
    params = {**params, "key": API_KEY}
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=30)
    if r.status_code != 200:
        print(f"   HTTP {r.status_code}: {r.text[:200]}")
    r.raise_for_status()
    return r.json()


def search_channel_ids(q, n=5):
    data = api_get("search", {"part": "snippet", "q": q, "type": "channel", "maxResults": n})
    return [it["snippet"]["channelId"] for it in data.get("items", [])]


def channel_details(ids):
    if not ids:
        return {}
    data = api_get("channels", {"part": "snippet,statistics,contentDetails", "id": ",".join(ids)})
    out = {}
    for c in data.get("items", []):
        stats = c.get("statistics", {})
        out[c["id"]] = {
            "title": c["snippet"]["title"],
            "published_at": c["snippet"].get("publishedAt", ""),
            "subs": int(stats.get("subscriberCount", 0) or 0),
            "subs_hidden": stats.get("hiddenSubscriberCount", False),
            "videos": int(stats.get("videoCount", 0) or 0),
            "uploads": c["contentDetails"]["relatedPlaylists"].get("uploads", ""),
        }
    return out


def best_match(expected, cands):
    best, best_score = None, None
    for cid, d in cands.items():
        if d["subs"] <= 0:
            continue
        score = abs(1 - d["subs"] / expected) if expected else 0
        if best_score is None or score < best_score:
            best, best_score = cid, score
    return best, best_score


def main():
    rows = []
    for name, exp_subs, tier, lang, layers in CHANNELS:
        print(f"\n=== {name} (expected ~{exp_subs:,} subs) ===")
        try:
            ids = search_channel_ids(name)
            cands = channel_details(ids)
        except Exception as e:
            print(f"   ERROR: {e}")
            cands = {}
        for cid, d in cands.items():
            print(f"   {d['subs']:>9,} subs | {d['videos']:>5} vids | {d['published_at'][:10]} | {cid} | {d['title']}")
        pick, score = best_match(exp_subs, cands)
        conf = "OK" if (score is not None and score <= 0.4) else "REVIEW"
        if pick:
            d = cands[pick]
            print(f"   -> PICK [{conf}]: {d['title']} | {pick} | {d['subs']:,} subs | created {d['published_at'][:10]}")
            rows.append({"name": name, "uc_id": pick, "uploads": d["uploads"], "title": d["title"],
                         "subs": d["subs"], "videos": d["videos"], "published_at": d["published_at"],
                         "expected_subs": exp_subs, "tier": tier, "language": lang, "layers": layers,
                         "match_conf": conf})
        else:
            print("   -> NO MATCH FOUND")
            rows.append({"name": name, "uc_id": "", "uploads": "", "title": "", "subs": 0, "videos": 0,
                         "published_at": "", "expected_subs": exp_subs, "tier": tier, "language": lang,
                         "layers": layers, "match_conf": "NOT_FOUND"})

    cols = ["name", "uc_id", "uploads", "title", "subs", "videos", "published_at",
            "expected_subs", "tier", "language", "layers", "match_conf"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {OUT_CSV}")
    print("\n========== RESOLVED SUMMARY ==========")
    for r in rows:
        print(f"  [{r['match_conf']:9s}] {r['name']:28s} {r['uc_id']:26s} subs={r['subs']:>9,} (exp {r['expected_subs']:>9,}) created={r['published_at'][:10]}")


if __name__ == "__main__":
    main()
