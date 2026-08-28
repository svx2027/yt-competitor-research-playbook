"""
depth_winners.py
Stage 1.6: format-stratified depth on the seasonal winners (~300, about 10% of the core corpus).

Per-format sampling so each playbook (long, livestream, Shorts) is learned on its own terms instead
of being drowned out by Shorts on a raw top-by-views list. Dual lens: top by views, plus top by
outlier ratio for English core videos (per-channel capped so a degenerate-median channel cannot
flood the ratio picks with course-launch promos).

For each target: comments (themes via Gemini) + transcript (opening/hook/arc/CTA via Gemini).
Shorts often lack captions, so transcript coverage is partial; long-form and live carry captions.

Reads:  out/seasonal_may_aug_2025.csv, out/seasonal_may_aug_2024.csv, out/outliers_core.csv
Writes: out/depth_winners.csv, out/depth_winners.json, out/depth_winners.md
Concurrency 6 workers. Resumable via .depth_winners.progress.json. Never prints API keys.
"""
import os, csv, json, time, re, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from dotenv import load_dotenv

PROJ = Path(__file__).resolve().parent.parent
load_dotenv(PROJ / ".env")
YT_KEY = os.getenv("YT_API_KEY"); GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not YT_KEY or not GEMINI_KEY:
    raise SystemExit("Missing YT_API_KEY or GEMINI_API_KEY in .env")

OUT = PROJ / "out"
PROGRESS = PROJ / ".depth_winners.progress.json"
YT_BASE = "https://www.googleapis.com/youtube/v3"
GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
CONCURRENCY = 6

# English strata by format: (top_by_views, top_by_ratio). Hinglish: top by views only.
# View targets carry most of the count; ratio supplements add channel-relative breakouts (capped).
STRATA = {"long": (95, 20), "live": (70, 10), "short": (85, 25)}
HINGLISH_N = 52
RATIO_PER_CHANNEL_CAP = 4


def vid_from_url(u):
    m = re.search(r"v=([A-Za-z0-9_-]{6,})", u or "")
    return m.group(1) if m else ""


def load_ratios():
    p = OUT / "outliers_core.csv"
    out = {}
    if p.exists():
        with p.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    out[r["video_id"]] = float(r["outlier_ratio"])
                except Exception:
                    pass
    return out


def load_targets():
    rows = []
    for fn in ("seasonal_may_aug_2025.csv", "seasonal_may_aug_2024.csv"):
        p = OUT / fn
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                r["view_count"] = int(r["view_count"] or 0)
                r["video_id"] = vid_from_url(r.get("video_url", ""))
                rows.append(r)
    ratios = load_ratios()
    for r in rows:
        r["ratio"] = ratios.get(r["video_id"], 0.0)
    eng = [r for r in rows if r.get("source_language") == "english"]
    hin = [r for r in rows if r.get("source_language") == "hinglish"]
    picked = {}

    def take(pool, n_views, n_ratio):
        added = 0
        for r in sorted(pool, key=lambda x: -x["view_count"]):
            if added >= n_views:
                break
            if r["video_id"] and r["video_id"] not in picked:
                picked[r["video_id"]] = r; added += 1
        added_r, ch = 0, {}
        for r in sorted(pool, key=lambda x: -x["ratio"]):
            if added_r >= n_ratio:
                break
            if r["ratio"] <= 0 or ch.get(r["channel"], 0) >= RATIO_PER_CHANNEL_CAP:
                continue
            if r["video_id"] and r["video_id"] not in picked:
                picked[r["video_id"]] = r; added_r += 1; ch[r["channel"]] = ch.get(r["channel"], 0) + 1

    for fmt, (nv, nr) in STRATA.items():
        take([r for r in eng if r["format"] == fmt], nv, nr)
    take(hin, HINGLISH_N, 0)
    return list(picked.values())


def yt_get(endpoint, params, max_retries=5):
    params = {**params, "key": YT_KEY}
    for attempt in range(max_retries):
        try:
            r = requests.get(f"{YT_BASE}/{endpoint}", params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt); continue
            if r.status_code == 403 and "commentsDisabled" in r.text:
                return {"items": [], "_disabled": True}
            return {"items": [], "_error": r.status_code}
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return {"items": [], "_error": "max_retries"}


def gemini_post(prompt, max_retries=5):
    url = f"{GEMINI_URL}?key={GEMINI_KEY}"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}}
    for attempt in range(max_retries):
        try:
            r = requests.post(url, json=body, timeout=60)
            if r.status_code == 200:
                try:
                    return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
                except Exception:
                    return None
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt); continue
            return None
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return None


def fetch_comments(vid, n=25):
    data = yt_get("commentThreads", {"part": "snippet", "videoId": vid, "order": "relevance",
                                     "maxResults": n, "textFormat": "plainText"})
    if data.get("_disabled"):
        return None
    out = []
    for it in data.get("items", []):
        top = it["snippet"]["topLevelComment"]["snippet"]
        out.append({"text": top.get("textDisplay", ""), "likes": top.get("likeCount", 0)})
    return out


def get_transcript_text(video_id):
    from youtube_transcript_api import YouTubeTranscriptApi
    langs = ["en", "en-IN", "en-US", "hi"]
    try:
        ytt = YouTubeTranscriptApi()
        fetched = ytt.fetch(video_id, languages=langs)
        if hasattr(fetched, "snippets"):
            return " ".join(s.text for s in fetched.snippets)
        try:
            return " ".join(s.text for s in fetched)
        except TypeError:
            pass
        try:
            return " ".join(s["text"] for s in fetched.to_raw_data())
        except Exception:
            pass
    except AttributeError:
        pass
    return " ".join(s["text"] for s in YouTubeTranscriptApi.get_transcript(video_id, languages=langs))


THEME_PROMPT = """You are analyzing YouTube comments for CAT-prep content strategy research.
Video title: {title}
Comments (top by relevance):
{comments}

Extract recurring themes mentioned by 2+ commenters. For each: theme (2-5 word noun phrase), frequency (int), example_quote (paraphrased in your own words, under 15 words, NOT verbatim).
Return up to 8 themes sorted by frequency desc. If under 5 comments or no theme reaches 2+, return {{"themes": [], "reason": "insufficient"}}.
Otherwise: {{"themes": [{{"theme":"...","frequency":N,"example_quote":"..."}}]}}. Only valid JSON, no prose."""

ANALYSIS_PROMPT = """You are analyzing a YouTube video transcript for CAT-prep content strategy research.
Video title: {title}
Transcript:
{transcript}

Return only valid JSON:
{{
  "opening_first_15_words": "the literal first 15 words",
  "hook_mechanic": "under 12 words: what makes the open grab attention",
  "content_arc_summary": "under 40 words: how the video structures its message",
  "cta_type": "what the CTA asks for, or 'none'"
}}"""


def process_one(t):
    vid = t["video_id"]
    rec = {"video_id": vid, "channel": t["channel"], "season": t["season"],
           "source_language": t["source_language"], "format": t["format"], "topic": t.get("topic", ""),
           "hook_type": t.get("hook_type", ""), "view_count": t["view_count"],
           "outlier_ratio": round(t.get("ratio", 0.0), 1), "title": t["title"], "video_url": t["video_url"],
           "comment_themes": [], "comments_status": "", "transcript_available": False,
           "opening": "", "hook_mechanic": "", "content_arc": "", "cta_type": ""}
    comments = fetch_comments(vid)
    if comments is None:
        rec["comments_status"] = "disabled"
    elif len(comments) < 5:
        rec["comments_status"] = f"only {len(comments)} comments"
    else:
        block = "\n".join(f"[{j+1}] {c['text'][:250]}" for j, c in enumerate(comments))
        res = gemini_post(THEME_PROMPT.format(title=t["title"], comments=block))
        if res and res.get("themes"):
            rec["comment_themes"] = res["themes"][:8]; rec["comments_status"] = "ok"
        else:
            rec["comments_status"] = (res or {}).get("reason", "gemini_error") if res else "gemini_error"
    try:
        tr = get_transcript_text(vid)
    except Exception:
        tr = None
    if tr and len(tr) >= 80:
        rec["transcript_available"] = True
        res = gemini_post(ANALYSIS_PROMPT.format(title=t["title"], transcript=tr[:18000]))
        if res:
            rec["opening"] = res.get("opening_first_15_words", "")
            rec["hook_mechanic"] = res.get("hook_mechanic", "")
            rec["content_arc"] = res.get("content_arc_summary", "")
            rec["cta_type"] = res.get("cta_type", "")
    return vid, rec


def main():
    targets = load_targets()
    by = {}
    for t in targets:
        by[(t["source_language"], t["format"])] = by.get((t["source_language"], t["format"]), 0) + 1
    print(f"{len(targets)} targets: " + ", ".join(f"{k[0]}/{k[1]}={v}" for k, v in sorted(by.items())), flush=True)
    state = json.loads(PROGRESS.read_text()) if PROGRESS.exists() else {"done": [], "records": {}}
    done = set(state["done"]); records = state["records"]
    pending = [t for t in targets if t["video_id"] and t["video_id"] not in done]
    print(f"{len(pending)} to process ({len(done)} already done)", flush=True)

    lock = threading.Lock(); n = 0
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = [ex.submit(process_one, t) for t in pending]
        for fut in as_completed(futs):
            try:
                vid, rec = fut.result()
            except Exception as e:
                print(f"   worker error: {e}", flush=True); continue
            with lock:
                records[vid] = rec; done.add(vid); n += 1
                if n % 25 == 0:
                    PROGRESS.write_text(json.dumps({"done": sorted(done), "records": records}, ensure_ascii=False))
                    print(f"   {n}/{len(pending)} done", flush=True)
    PROGRESS.write_text(json.dumps({"done": sorted(done), "records": records}, ensure_ascii=False))

    recs = [records[t["video_id"]] for t in targets if t["video_id"] in records]
    cols = ["video_id", "channel", "season", "source_language", "format", "topic", "hook_type",
            "view_count", "outlier_ratio", "title", "video_url", "comments_status",
            "transcript_available", "top_themes", "opening", "hook_mechanic", "content_arc", "cta_type"]
    with (OUT / "depth_winners.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in recs:
            themes = "; ".join(f"{t['theme']}({t.get('frequency','')})" for t in r.get("comment_themes", []))
            row = {k: r.get(k, "") for k in cols if k != "top_themes"}
            row["top_themes"] = themes
            w.writerow(row)
    (OUT / "depth_winners.json").write_text(json.dumps(recs, indent=2, ensure_ascii=False), encoding="utf-8")

    n_tr = sum(1 for r in recs if r.get("transcript_available"))
    n_cm = sum(1 for r in recs if r.get("comments_status") == "ok")
    lines = ["# Depth on seasonal winners (why they worked)\n",
             f"{len(recs)} videos, format-stratified. Transcripts available: {n_tr}. Comment themes: {n_cm}.\n"]
    for r in sorted(recs, key=lambda x: -x["view_count"]):
        rr = f" | {r.get('outlier_ratio','')}x" if r.get("outlier_ratio") else ""
        lines.append(f"\n## {r['view_count']:,} views{rr} | {r['format']} | {r['source_language']} | {r['channel']}")
        lines.append(f"**{r['title']}**  ({r.get('topic','')}/{r.get('hook_type','')})  {r['video_url']}")
        if r.get("hook_mechanic"):
            lines.append(f"- Hook: {r['hook_mechanic']}  | Open: \"{r['opening']}\"")
        if r.get("content_arc"):
            lines.append(f"- Arc: {r['content_arc']}  | CTA: {r['cta_type']}")
        if r.get("comment_themes"):
            lines.append("- Comment themes: " + "; ".join(f"{t['theme']} ({t.get('frequency','')})" for t in r["comment_themes"]))
        elif r.get("comments_status") != "ok":
            lines.append(f"- Comments: {r.get('comments_status','')}")
    (OUT / "depth_winners.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nDone. {len(recs)} videos, transcripts={n_tr}/{len(recs)}, comment-themes={n_cm}/{len(recs)}", flush=True)


if __name__ == "__main__":
    main()
