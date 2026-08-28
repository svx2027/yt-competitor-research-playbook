"""
fetch_videos_layered.py
Stage 1.2: pull videos for all resolved channels with age-adaptive windows.

Reads:  out/channels_resolved.csv  (from resolve_channels.py)
Writes: out/competitors_core_365d.csv   (data_layer=core; the ONLY file stats/outliers read)
        out/competitors_extended.csv     (data_layer=extended; older tail, absolute-views/seasonal)
        out/competitors_hinglish.csv      (data_layer=hinglish; mining only)

Windows:
  core      2025-05-20 .. 2026-05-20   (locked 365d, ratio math)
  extended  2024-04-01 .. 2025-05-20   (older tail for >2yr channels; no overlap with core)
  hinglish  2024-04-01 .. 2026-05-20   (full span for the 2 Hinglish fallback channels)

Format from API metadata: live from liveStreamingDetails/liveBroadcastContent;
short = non-live duration <= 180s (fixed proxy, the Data API exposes no Shorts flag); else long.
Never prints API keys. Resumable via .fetch_layered.progress.json.
"""
import os, csv, json, time, re
from pathlib import Path
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

PROJ = Path(__file__).resolve().parent.parent
load_dotenv(PROJ / ".env")
API_KEY = os.getenv("YT_API_KEY")
if not API_KEY or "your_" in API_KEY:
    raise SystemExit("ERROR: YT_API_KEY missing or placeholder in .env")

OUT_DIR = PROJ / "out"; OUT_DIR.mkdir(exist_ok=True)
CHANNELS_CSV = OUT_DIR / "channels_resolved.csv"
PROGRESS_FILE = PROJ / ".fetch_layered.progress.json"
BASE = "https://www.googleapis.com/youtube/v3"

CORE_START = datetime(2025, 5, 20, tzinfo=timezone.utc)
CORE_END   = datetime(2026, 5, 20, 23, 59, 59, tzinfo=timezone.utc)
EXT_START  = datetime(2024, 4, 1, tzinfo=timezone.utc)
SHORT_MAX_SECONDS = 180

OUT_FILES = {
    "core":     OUT_DIR / "competitors_core_365d.csv",
    "extended": OUT_DIR / "competitors_extended.csv",
    "hinglish": OUT_DIR / "competitors_hinglish.csv",
}
COLS = ["channel", "channel_id", "data_layer", "tier", "source_language", "video_id", "title",
        "description", "published_at", "duration_iso", "duration_seconds", "format", "view_count",
        "like_count", "comment_count", "thumbnail_url", "video_url", "language_hint"]

ISO_DUR_RE = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


def iso_to_seconds(iso):
    if not iso:
        return 0
    m = ISO_DUR_RE.match(iso)
    if not m:
        return 0
    h = int(m.group(1) or 0); mi = int(m.group(2) or 0); s = int(m.group(3) or 0)
    return h * 3600 + mi * 60 + s


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def classify_format(v):
    """Format from API metadata. live: liveStreamingDetails/liveBroadcastContent (never duration).
    short: non-live duration <= 180s (fixed proxy). else long."""
    sn = v.get("snippet", {}) or {}
    cd = v.get("contentDetails", {}) or {}
    lsd = v.get("liveStreamingDetails")
    lbc = sn.get("liveBroadcastContent", "none")
    dur = iso_to_seconds(cd.get("duration", ""))
    if lbc in ("live", "upcoming"):
        return "live", dur
    if lsd and (lsd.get("actualStartTime") or lsd.get("actualEndTime")):
        return "live", dur
    if 0 < dur <= SHORT_MAX_SECONDS:
        return "short", dur
    return "long", dur


def api_get(endpoint, params, max_retries=5):
    params = {**params, "key": API_KEY}
    err = None
    for attempt in range(max_retries):
        try:
            r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt); continue
            print(f"   HTTP {r.status_code}: {r.text[:200]}")
            r.raise_for_status()
        except requests.RequestException as e:
            err = e; time.sleep(2 ** attempt)
    raise RuntimeError(f"failed {endpoint}: {err}")


def walk_uploads(uploads_id, since_dt):
    items, token = [], None
    while True:
        params = {"part": "contentDetails", "playlistId": uploads_id, "maxResults": 50}
        if token:
            params["pageToken"] = token
        data = api_get("playlistItems", params)
        oldest = None
        for it in data.get("items", []):
            cd = it.get("contentDetails", {})
            vid = cd.get("videoId"); pub = cd.get("videoPublishedAt")
            if not vid:
                continue
            items.append({"video_id": vid, "published_at": pub})
            dt = parse_dt(pub)
            if dt and (oldest is None or dt < oldest):
                oldest = dt
        token = data.get("nextPageToken")
        if not token:
            break
        if oldest and oldest < since_dt:
            break
    return items


def fetch_details(video_ids):
    details = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        data = api_get("videos", {"part": "snippet,contentDetails,statistics,liveStreamingDetails",
                                  "id": ",".join(batch)})
        for v in data.get("items", []):
            details[v["id"]] = v
    return details


def layer_for(dt, layers, language):
    if "hinglish" in layers:
        return "hinglish" if EXT_START <= dt <= CORE_END else None
    if CORE_START <= dt <= CORE_END:
        return "core"
    if "extended" in layers and EXT_START <= dt < CORE_START:
        return "extended"
    return None


def load_progress():
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text())
        except Exception:
            pass
    return {"done": [], "rows": {"core": [], "extended": [], "hinglish": []}}


def save_progress(state):
    PROGRESS_FILE.write_text(json.dumps(state, default=str))


def main():
    channels = []
    with CHANNELS_CSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["uc_id"] or not r["uploads"]:
                print(f"SKIP {r['name']}: no uc_id/uploads"); continue
            channels.append(r)

    state = load_progress(); done = set(state["done"]); rows = state["rows"]
    for ch in channels:
        name = ch["name"]
        if name in done:
            print(f"SKIP (done) {name}"); continue
        layers = ch["layers"]; language = ch["language"]
        since = EXT_START if ("extended" in layers or "hinglish" in layers) else CORE_START
        print(f"\n=== {name} [{layers}] since {since.date()} ===")
        try:
            ups = walk_uploads(ch["uploads"], since)
            keep = []
            for it in ups:
                dt = parse_dt(it["published_at"])
                if not dt:
                    continue
                lyr = layer_for(dt, layers, language)
                if lyr:
                    keep.append((it["video_id"], lyr))
            print(f"   {len(ups)} uploads walked, {len(keep)} in target windows")
            details = fetch_details([k[0] for k in keep])
            n_by = {}
            for vid, lyr in keep:
                v = details.get(vid)
                if not v:
                    continue
                sn = v.get("snippet", {}) or {}; st = v.get("statistics", {}) or {}; cd = v.get("contentDetails", {}) or {}
                fmt, dur = classify_format(v)
                thumbs = sn.get("thumbnails", {}) or {}
                thumb = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")
                desc = (sn.get("description", "") or "").replace("\n", " ").replace("\r", " ")[:500]
                rows[lyr].append({
                    "channel": name, "channel_id": ch["uc_id"], "data_layer": lyr, "tier": ch["tier"],
                    "source_language": language, "video_id": vid, "title": sn.get("title", ""),
                    "description": desc, "published_at": sn.get("publishedAt", ""),
                    "duration_iso": cd.get("duration", ""), "duration_seconds": dur, "format": fmt,
                    "view_count": int(st.get("viewCount", 0) or 0), "like_count": int(st.get("likeCount", 0) or 0),
                    "comment_count": int(st.get("commentCount", 0) or 0), "thumbnail_url": thumb,
                    "video_url": f"https://www.youtube.com/watch?v={vid}",
                    "language_hint": sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "",
                })
                n_by[lyr] = n_by.get(lyr, 0) + 1
            parts = ", ".join(f"{k}={v}" for k, v in n_by.items()) or "0"
            print(f"   added: {parts}")
            done.add(name); state = {"done": sorted(done), "rows": rows}; save_progress(state)
        except Exception as e:
            save_progress(state); print(f"FAIL {name}: {e}"); raise

    for lyr, path in OUT_FILES.items():
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS, quoting=csv.QUOTE_MINIMAL)
            w.writeheader(); w.writerows(rows[lyr])

    print("\n========== D1 LAYERED SUMMARY ==========")
    for lyr, path in OUT_FILES.items():
        data = rows[lyr]
        bych = {}
        for r in data:
            d = bych.setdefault(r["channel"], {"long": 0, "short": 0, "live": 0})
            d[r["format"]] += 1
        print(f"\n-- {lyr}: {len(data)} rows -> {path.name}")
        for c in sorted(bych):
            cc = bych[c]
            print(f"   {c:32s} total={sum(cc.values()):4d} long={cc['long']:4d} short={cc['short']:4d} live={cc['live']:4d}")
    print("\nDone.")


if __name__ == "__main__":
    main()
