"""
transcript_recover.py
Serial, throttled transcript fetch + Gemini analysis for the long/live depth winners that lack a
transcript (the concurrent depth run got blocked by YouTube anti-scraping). Updates
out/depth_winners.json/.csv/.md in place. Early-aborts if the block clearly persists.
"""
import csv, json, time, sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ / "03_scripts"))
from depth_winners import get_transcript_text, gemini_post, ANALYSIS_PROMPT  # noqa: E402

OUT = PROJ / "out"
DELAY = 1.5


def write_outputs(recs):
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


def main():
    recs = json.loads((OUT / "depth_winners.json").read_text())
    targets = [r for r in recs if r["format"] in ("long", "live") and not r.get("transcript_available")]
    print(f"{len(targets)} long/live records lacking a transcript", flush=True)
    recovered = 0
    for i, r in enumerate(targets, 1):
        try:
            tr = get_transcript_text(r["video_id"])
        except Exception:
            tr = None
        if tr and len(tr) >= 80:
            res = gemini_post(ANALYSIS_PROMPT.format(title=r["title"], transcript=tr[:18000]))
            if res:
                r["transcript_available"] = True
                r["opening"] = res.get("opening_first_15_words", "")
                r["hook_mechanic"] = res.get("hook_mechanic", "")
                r["content_arc"] = res.get("content_arc_summary", "")
                r["cta_type"] = res.get("cta_type", "")
                recovered += 1
        if i % 20 == 0:
            print(f"  {i}/{len(targets)} recovered={recovered}", flush=True)
            write_outputs(recs)
        if i == 25 and recovered == 0:
            print("block persists after 25 serial attempts, aborting recovery", flush=True)
            break
        time.sleep(DELAY)
    write_outputs(recs)
    total = sum(1 for r in recs if r.get("transcript_available"))
    print(f"\nrecovered {recovered}; total transcripts now {total}/{len(recs)}", flush=True)


if __name__ == "__main__":
    main()
