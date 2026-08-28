"""
phase_e_tag_videos.py
Tag videos with topic, format_archetype, hook_type, language via Gemini.
Reusable: takes --input and --output paths.
"""

import os, csv, json, time, argparse, socket, threading
from pathlib import Path
from collections import deque
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from dotenv import load_dotenv

# Force IPv4-only DNS resolution. Local network had IPv6 SYN black-hole to
# Gemini endpoints which caused multi-minute hangs per request.
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only_getaddrinfo(host, port, family=0, *args, **kwargs):
    return _orig_getaddrinfo(host, port, socket.AF_INET, *args, **kwargs)
socket.getaddrinfo = _ipv4_only_getaddrinfo

PROJ = Path(__file__).resolve().parent.parent
load_dotenv(PROJ / ".env")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY: raise SystemExit("Missing GEMINI_API_KEY in .env")

# gemini-2.0-flash deprecated June 1, 2026, migrated to 2.5-flash-lite (same pricing $0.10/$0.40 per 1M tokens)
GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Tier 1 paid: 2.5-flash-lite Tier 1 cap is ~1000 RPM. 500 leaves headroom.
RATE_LIMIT_RPM_INITIAL = 500
RATE_LIMIT_RPM_FLOOR = 60
CHECKPOINT_EVERY = 200
CONCURRENCY = 10

ALLOWED_TOPIC = {
    "VARC","DILR","QA","OMET","WAT-PI","GD","IIM-life","admissions","mba-strategy",
    "mock-test","mock-analysis","sectional-strategy","percentile-strategy","exam-pattern",
    "results","cutoff-analysis","college-comparison","fees-roi","placement-stories",
    "topper-interview","profile-building","faculty-intro","batch-launch","lead-magnet",
    "live-doubt-solving","marathon","motivation","day-in-life","meme-relatable",
    "current-affairs-gk","promo-only","other"
}
ALLOWED_FORMAT = {
    "concept-video","problem-solving","full-mock","mock-analysis-session","sectional-drill",
    "live-class","short-tip","shorts-explainer","score-reveal","percentile-predictor",
    "topper-interview","results-reaction","vlog","day-in-life","podcast","faculty-intro",
    "batch-promo","lead-magnet-funnel","webinar","strategy-talk","meme-vignette",
    "text-overlay-short","other"
}
ALLOWED_HOOK = {
    "number-based","transformation","score-reveal","percentile-reveal","fear-based","FOMO",
    "contrarian","controversy","authority","curiosity-gap","lifestyle","urgency",
    "problem-promise","explainer-direct","relatable","myth-busting","other"
}
ALLOWED_LANGUAGE = {"english","hinglish","hindi-devanagari","mixed-other"}

TAG_PROMPT = """Tag this YouTube video for a CAT (Common Admission Test, the Indian MBA entrance exam) competitor research project. The channel set is English-medium CAT and OMET (other management entrance test) preparation.

Title: {title}
Description: {desc}
Duration: {duration} seconds
Format: {fmt}

Return JSON only, no commentary, with exactly these four keys:
{{
  "topic": "<ONE of the allowed topic labels>",
  "format_archetype": "<ONE of the allowed format_archetype labels>",
  "hook_type": "<ONE of the allowed hook_type labels>",
  "language": "<ONE of the allowed language labels>"
}}

Allowed labels (use exactly, do not paraphrase):
topic: [VARC, DILR, QA, OMET, WAT-PI, GD, IIM-life, admissions, mba-strategy, mock-test, mock-analysis, sectional-strategy, percentile-strategy, exam-pattern, results, cutoff-analysis, college-comparison, fees-roi, placement-stories, topper-interview, profile-building, faculty-intro, batch-launch, lead-magnet, live-doubt-solving, marathon, motivation, day-in-life, meme-relatable, current-affairs-gk, promo-only, other]
format_archetype: [concept-video, problem-solving, full-mock, mock-analysis-session, sectional-drill, live-class, short-tip, shorts-explainer, score-reveal, percentile-predictor, topper-interview, results-reaction, vlog, day-in-life, podcast, faculty-intro, batch-promo, lead-magnet-funnel, webinar, strategy-talk, meme-vignette, text-overlay-short, other]
hook_type: [number-based, transformation, score-reveal, percentile-reveal, fear-based, FOMO, contrarian, controversy, authority, curiosity-gap, lifestyle, urgency, problem-promise, explainer-direct, relatable, myth-busting, other]
language: [english, hinglish, hindi-devanagari, mixed-other]

Rules:
- If unsure, return 'other' for that field, not a guess.
- Hinglish means Romanized Hindi mixed with English in the same string.
- Section names: VARC = Verbal Ability and Reading Comprehension; DILR = Data Interpretation and Logical Reasoning; QA = Quantitative Aptitude. OMET covers XAT, SNAP, NMAT, CMAT, MAT, IIFT, TISSNET.
- Use 'percentile-reveal' (hook) or 'percentile-predictor' (format) when the video centers on a CAT percentile or score estimate; use 'score-reveal' for generic marks/result reveals.
- A spoken teaching short (sub-180s, a person explaining a concept) maps to format_archetype 'shorts-explainer'; a silent text-on-screen or trending-audio short maps to 'text-overlay-short'.
- 'promo-only' topic is for pure ads (no teaching content); 'lead-magnet' is for free PDF/demo/mock/webinar offers.
- Live streams over 1800 seconds usually map to topic 'marathon' or 'live-doubt-solving' and format_archetype 'live-class'.
- 'WAT-PI' covers written ability test, group discussion, and personal interview prep; 'IIM-life' is campus or day-in-life content at IIMs; 'admissions' is the application and selection process and shortlists."""

class RateLimiter:
    def __init__(self, rpm):
        self.rpm = rpm; self.times = deque(); self._lock = threading.Lock()
    def adjust(self, new_rpm):
        with self._lock:
            self.rpm = max(RATE_LIMIT_RPM_FLOOR, new_rpm)
    def wait(self):
        with self._lock:
            now = time.monotonic()
            while self.times and self.times[0] < now - 60: self.times.popleft()
            if len(self.times) >= self.rpm:
                sleep_for = 60 - (now - self.times[0]) + 0.05
            else:
                sleep_for = 0
            self.times.append(time.monotonic() + max(sleep_for, 0))
        if sleep_for > 0: time.sleep(sleep_for)

def gemini_post(prompt, limiter, failure_log, video_id, max_retries=3):
    url = f"{GEMINI_URL}?key={GEMINI_KEY}"
    body = {"contents":[{"parts":[{"text":prompt}]}],
            "generationConfig":{"temperature":0.1,"responseMimeType":"application/json"}}
    delays = [1, 4, 16]; last_reason = ""
    for attempt in range(max_retries):
        limiter.wait()
        try:
            r = requests.post(url, json=body, timeout=60)
            if r.status_code == 200:
                d = r.json()
                try:
                    return json.loads(d["candidates"][0]["content"]["parts"][0]["text"])
                except Exception as e: last_reason = f"parse:{e}"
            elif r.status_code == 429:
                last_reason = "429"; limiter.adjust(int(limiter.rpm * 0.7))
                print(f"    429, throttling RPM to {limiter.rpm}")
            elif r.status_code in (500, 502, 503, 504): last_reason = f"http:{r.status_code}"
            else: last_reason = f"http:{r.status_code}:{r.text[:120]}"
        except requests.RequestException as e: last_reason = f"exc:{e}"
        time.sleep(delays[attempt])
    failure_log.write(f"{video_id}\t{last_reason}\n"); failure_log.flush()
    return None

def validate(result, video_id, violation_log):
    if not isinstance(result, dict): return None, ["not_dict"]
    out, viol = {}, []
    pairs = [("topic", ALLOWED_TOPIC), ("format_archetype", ALLOWED_FORMAT),
             ("hook_type", ALLOWED_HOOK), ("language", ALLOWED_LANGUAGE)]
    for key, allowed in pairs:
        v = (result.get(key) or "").strip()
        if v in allowed: out[key] = v
        else: out[key] = "other"; viol.append(f"{key}={v!r}")
    if viol:
        violation_log.write(f"{video_id}\t{';'.join(viol)}\n"); violation_log.flush()
    return out, viol

def tag_row(row, limiter, failure_log, violation_log):
    title = row.get("title", "") or ""
    desc = (row.get("description", "") or "")[:300]
    duration = row.get("duration_seconds", "") or "unknown"
    fmt = row.get("format", "") or "unknown"
    prompt = TAG_PROMPT.format(title=title, desc=desc, duration=duration, fmt=fmt)
    vid = row.get("video_id", "?")
    result = gemini_post(prompt, limiter, failure_log, vid)
    if result is None:
        return {"topic":"other","format_archetype":"other","hook_type":"other","language":"other"}, ["call_failed"]
    return validate(result, vid, violation_log)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True); p.add_argument("--output", required=True)
    args = p.parse_args()

    in_path = Path(args.input); out_path = Path(args.output)
    if not in_path.exists(): raise SystemExit(f"Missing input: {in_path}")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    partial = out_path.with_suffix(".partial.csv")
    progress = out_path.with_name(out_path.stem + ".progress.json")
    failures_path = PROJ / "out" / "phase_e_failures.txt"
    violations_path = PROJ / "out" / "phase_e_label_violations.txt"
    runtime_log = PROJ / "out" / "phase_e_runtime.json"

    state = {"done_ids": [], "rows": {}}
    if progress.exists():
        try: state = json.loads(progress.read_text())
        except Exception: pass
    done = set(state["done_ids"]); done_rows = state["rows"]
    print(f"Resuming from {len(done)} previously tagged rows" if done else "Starting fresh")

    with in_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f); rows = list(reader)
        in_fields = list(reader.fieldnames or [])
    new_fields = in_fields + [c for c in ["topic","format_archetype","hook_type","language"] if c not in in_fields]

    limiter = RateLimiter(RATE_LIMIT_RPM_INITIAL)

    class _LockedWriter:
        def __init__(self, f): self._f = f; self._lock = threading.Lock()
        def write(self, s):
            with self._lock: self._f.write(s)
        def flush(self):
            with self._lock: self._f.flush()
        def close(self): self._f.close()

    fl = _LockedWriter(failures_path.open("a", encoding="utf-8"))
    vl = _LockedWriter(violations_path.open("a", encoding="utf-8"))
    n_total = len(rows); n_calls = 0; n_failed = 0; n_violations = 0
    start = time.monotonic(); batch_start = start
    start_iso = datetime.now().isoformat(timespec="seconds")
    state_lock = threading.Lock()

    def assemble():
        out = []
        for r in rows:
            vid = r.get("video_id"); tags = done_rows.get(vid); merged = dict(r)
            if tags: merged.update(tags)
            else: merged.update({"topic":"","format_archetype":"","hook_type":"","language":""})
            out.append(merged)
        return out

    def write_csv(target, complete_rows):
        with target.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=new_fields, quoting=csv.QUOTE_MINIMAL)
            w.writeheader(); w.writerows(complete_rows)

    def process_one(row):
        vid = row.get("video_id")
        if not vid: return None
        tags, viol = tag_row(row, limiter, fl, vl)
        return (vid, tags, viol)

    pending = [r for r in rows if r.get("video_id") and r["video_id"] not in done]
    print(f"Submitting {len(pending)} videos to {CONCURRENCY} workers (model={GEMINI_MODEL})...", flush=True)

    completed_since_checkpoint = 0
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futures = [ex.submit(process_one, r) for r in pending]
        for fut in as_completed(futures):
            result = fut.result()
            if result is None: continue
            vid, tags, viol = result
            with state_lock:
                n_calls += 1
                done_rows[vid] = tags; done.add(vid)
                if viol == ["call_failed"]: n_failed += 1
                elif viol: n_violations += 1
                completed_since_checkpoint += 1
                if completed_since_checkpoint >= CHECKPOINT_EVERY:
                    completed_since_checkpoint = 0
                    elapsed_batch = time.monotonic() - batch_start
                    batch_start = time.monotonic()
                    elapsed_total = time.monotonic() - start
                    done_count = len(done); remaining = n_total - done_count
                    calls_per_sec = n_calls / max(elapsed_total, 1)
                    eta_min = (remaining / calls_per_sec / 60) if calls_per_sec > 0 else 0
                    pct = 100 * done_count / n_total
                    print(f"Processed {done_count}/{n_total} ({pct:.1f}%). Last batch took {elapsed_batch:.1f}s. ETA {eta_min:.1f} minutes.", flush=True)
                    progress.write_text(json.dumps({"done_ids": sorted(done), "rows": done_rows}))
                    write_csv(partial, assemble())

    progress.write_text(json.dumps({"done_ids": sorted(done), "rows": done_rows}))
    write_csv(out_path, assemble())
    fl.close(); vl.close()
    elapsed = time.monotonic() - start
    end_iso = datetime.now().isoformat(timespec="seconds")

    rt = {}
    if runtime_log.exists():
        try: rt = json.loads(runtime_log.read_text())
        except Exception: pass
    rt[str(in_path)] = {"output": str(out_path), "rows_total": n_total,
        "calls_this_run": n_calls, "failures_this_run": n_failed,
        "violations_this_run": n_violations, "elapsed_seconds": int(elapsed),
        "start": start_iso, "end": end_iso, "model": GEMINI_MODEL}
    runtime_log.write_text(json.dumps(rt, indent=2))

    print(f"\n=== Done: {in_path.name} ===")
    print(f"  Output: {out_path}")
    print(f"  Rows: {n_total}  Calls: {n_calls}  Failures: {n_failed}  Violations: {n_violations}")
    print(f"  Elapsed: {elapsed/60:.1f} minutes  Model: {GEMINI_MODEL}")

if __name__ == "__main__":
    main()
