"""
gen_titles_gemini.py
Write the best English title for each slotted calendar idea, following vidIQ/YouTube title guidelines,
using Gemini (the free API key). No vidIQ credits. The original competitor title stays in the sheet for
comparison; this provides your own channel's "best title".

Reads:  out/calendar_data.json (slotted ideas from build_calendar.py)
Writes: out/gemini_titles.json (video_id -> best title). Resumable.
"""
import os, json, time, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from dotenv import load_dotenv

PROJ = Path(__file__).resolve().parent.parent
load_dotenv(PROJ / ".env")
KEY = os.getenv("GEMINI_API_KEY")
if not KEY:
    raise SystemExit("Missing GEMINI_API_KEY in .env")
MODEL = "gemini-2.5-flash-lite"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
OUT = PROJ / "out"
IN_JSON = OUT / "calendar_data.json"
OUT_JSON = OUT / "gemini_titles.json"
CONC = 8

# EXAMPLE VALUE: replace "your channel" with your own channel name/niche description.
PROMPT = '''Write the single best YouTube video title for a 100% English CAT (Indian MBA entrance) prep video on your channel.

Source competitor video title (use only for the idea, do NOT copy it): {src}
Topic: {topic}. Format: {fmt}. Primary keyword to target: {kw}. Hook style: {hook}.

Title rules (vidIQ and YouTube best practice):
- Put the primary keyword near the front.
- 50 to 60 characters ideal (hard maximum 70).
- Include exactly one of: a specific number, a curiosity gap, or a clear outcome.
- 100% English, clear and credible, not clickbait. No Hindi words, no emoji, no ALL CAPS.
- Make it specific to CAT 2026 where natural.

Return JSON only: {{"title": "..."}}'''


def gem(prompt, tries=4):
    u = f"{URL}?key={KEY}"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"}}
    for a in range(tries):
        try:
            r = requests.post(u, json=body, timeout=60)
            if r.status_code == 200:
                try:
                    return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"]).get("title")
                except Exception:
                    return None
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** a); continue
            return None
        except requests.RequestException:
            time.sleep(2 ** a)
    return None


def main():
    items = json.loads(IN_JSON.read_text())
    out = json.loads(OUT_JSON.read_text()) if OUT_JSON.exists() else {}
    todo = [it for it in items if it["video_id"] and it["video_id"] not in out]
    print(f"{len(items)} slotted ideas, {len(todo)} to title", flush=True)
    lock = threading.Lock(); done = 0

    def work(it):
        t = gem(PROMPT.format(src=it["source_title"], topic=it["topic"], fmt=it["format"],
                              kw=it["primary_keyword"], hook=it.get("hook_type", "")))
        return it["video_id"], t

    with ThreadPoolExecutor(max_workers=CONC) as ex:
        futs = [ex.submit(work, it) for it in todo]
        for f in as_completed(futs):
            vid, t = f.result()
            with lock:
                if t:
                    out[vid] = t.strip()
                done += 1
                if done % 40 == 0:
                    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False))
                    print(f"  {done}/{len(todo)}", flush=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"wrote {len(out)} best titles to {OUT_JSON}", flush=True)


if __name__ == "__main__":
    main()
