"""
phase_e_sanity_report.py
Generates ./out/phase_e_sanity_report.txt from the two tagged CSVs.

EXAMPLE VALUES: the two "expected" row counts below are illustrative placeholders. Replace them with
your own known row counts once you have run phase_e_tag_videos.py on your competitor and own-channel
files, so this report actually catches a short or truncated tagging run.
"""

import csv, json
from pathlib import Path
from collections import Counter, defaultdict

OUT_DIR = Path("./out")
COMP = OUT_DIR / "competitor_videos_tagged.csv"
OWN = OUT_DIR / "own_channel_videos_tagged.csv"
FAIL = OUT_DIR / "phase_e_failures.txt"
VIOL = OUT_DIR / "phase_e_label_violations.txt"
RUNTIME = OUT_DIR / "phase_e_runtime.json"
REPORT = OUT_DIR / "phase_e_sanity_report.txt"
TAG_COLS = ["topic", "format_archetype", "hook_type", "language"]
EXPECTED_COMP_ROWS = None  # fill in once known, e.g. 4738
EXPECTED_OWN_ROWS = None   # fill in once known, e.g. 497

def count_lines(p):
    if not p.exists(): return 0
    return sum(1 for _ in p.open(encoding="utf-8"))

def load(p):
    if not p.exists(): return []
    with p.open(encoding="utf-8") as f: return list(csv.DictReader(f))

def main():
    comp = load(COMP); own = load(OWN)
    lines = ["PHASE E SANITY REPORT", "=" * 60]
    exp_comp = f" (expected {EXPECTED_COMP_ROWS})" if EXPECTED_COMP_ROWS else ""
    exp_own = f" (expected {EXPECTED_OWN_ROWS})" if EXPECTED_OWN_ROWS else ""
    lines.append(f"competitor_videos_tagged.csv rows: {len(comp)}{exp_comp}")
    lines.append(f"own_channel_videos_tagged.csv rows: {len(own)}{exp_own}")
    lines.append(f"competitor file exists: {COMP.exists()}")
    lines.append(f"own-channel file exists: {OWN.exists()}")
    lines.append("")

    by_ch = {col: defaultdict(Counter) for col in TAG_COLS}
    for r in comp:
        ch = r.get("channel", "?") or "?"
        for col in TAG_COLS: by_ch[col][ch][r.get(col, "other")] += 1
    for col in TAG_COLS:
        lines.append(f"--- {col} (competitor, per channel) ---")
        for ch in sorted(by_ch[col].keys()):
            c = by_ch[col][ch]; total = sum(c.values())
            inline = ", ".join(f"{k}={v}" for k, v in c.most_common()[:10])
            lines.append(f"  {ch:14s} total={total:4d}  {inline}")
        lines.append("")

    if own:
        lines.append("--- Own-channel distributions ---")
        for col in TAG_COLS:
            c = Counter(r.get(col, "other") for r in own)
            lines.append(f"  {col:18s} {', '.join(f'{k}={v}' for k, v in c.most_common())}")
        lines.append("")

    all_rows = comp + own; n = len(all_rows) or 1
    lines.append("--- 'other' rates across both files (target <15%) ---")
    for col in TAG_COLS:
        n_other = sum(1 for r in all_rows if r.get(col, "") == "other")
        pct = 100 * n_other / n
        flag = "  *** FLAG ***" if pct > 15 else ""
        lines.append(f"  {col:18s} other={n_other}/{n} ({pct:.1f}%){flag}")
    lines.append("")

    n_fail = count_lines(FAIL); n_viol = count_lines(VIOL)
    lines.append(f"Total Gemini failures logged: {n_fail} ({100*n_fail/n:.2f}%, target <1%)")
    lines.append(f"Total label violations logged: {n_viol} ({100*n_viol/n:.2f}%, target <2%)")

    total_calls = 0; total_seconds = 0; model_used = "unknown"
    if RUNTIME.exists():
        try:
            rt = json.loads(RUNTIME.read_text())
            for k, v in rt.items():
                total_calls += v.get("calls_this_run", 0)
                total_seconds += v.get("elapsed_seconds", 0)
                model_used = v.get("model", model_used)
        except Exception: pass
    lines.append(f"Total Gemini calls (across runs): {total_calls}")
    lines.append(f"Model used: {model_used}")
    lines.append(f"Total wall-clock runtime: {total_seconds/60:.1f} minutes")
    lines.append("")
    lines.append("Files written this phase:")
    for p in [COMP, OWN, REPORT, FAIL, VIOL]:
        lines.append(f"  {p}  exists={p.exists()}")

    REPORT.write_text("\n".join(lines))
    print("\n".join(lines))

if __name__ == "__main__":
    main()
