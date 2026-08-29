# Worked examples: two real runs

This playbook is the generalised distillation of two completed projects for a real entrance-exam-prep
YouTube channel. Client and channel identities are withheld here (this is the public template); use
the shape and scale of these runs as the reference instantiation when you are unsure what a phase's
output should look like. Run 1.0 set the spine; run 2.0 corrected its scripts and added the layered
and seasonal methods.

---

## 1. Run 1.0

YouTube competitor research and content strategy for an entrance-exam-prep channel, in its first
full run.

### What it produced
- 11 competitor channels, 6,687 in-window videos (a trailing 365-day window), 570 outliers.
- A synthesis of 8 to 12 cross-channel findings.
- A tiered idea bank (Tier 1 / 2 / 3, 80 each).
- A vidIQ-backed tiered xlsx, then a final 12-week exam-cycle-anchored calendar.

### The lessons it taught
1. State the ranking lens. Channel-relative breakout (outlier ratio) and absolute reach (views) surface
   different winners. Conflating them was the original mistake.
2. Match the organising principle, not just the columns. An early draft matched the reference
   calendar's columns but grouped ideas by tier, not week, so it read as a heap. The fix anchored rows
   to the exam cycle instead. Lock the organising principle at the start.
3. Check tool costs before spending. vidIQ is 5 credits per call, not 1; verify balance and confirm
   budget before a bulk run.

---

## 2. Run 2.0

A seasonal competitor audit of the same niche, in a same-language subset, then a 13-week calendar.
This run is the reference for the layered data model and the seasonal slice.

### What it produced
- 13 channels: 10 same-language competitors, the operator's own index channel, and 2 cross-language
  fallback channels mined for topic and format only.
- 11,323 videos across three layers (3,432 core + 3,528 extended + 4,363 cross-language), 230 core
  outliers, 5,748 tagged.
- A May-to-August seasonal slice across 2025 and 2024 (3,328 seasonal videos; a 2,077-idea seasonal
  bank), 314 format-stratified depth winners, 34 vidIQ keyword lookups (~165 credits).
- 11 synthesis insights, then a 13-week (Week 0 + 12) over-supplied calendar: 20 ideas/week, 230
  slotted + 26 playlist rows, 222/230 Gemini best titles, every source link verified live (0 dead).
- A founder strategy deck (Gamma) plus a presenter explainer (docx).

### The lessons it taught
1. The data layers + firewall. Keep core (ratios), extended (older/seasonal, no ratio), and
   cross-language (mining only) in separate files so a ratio never touches data it should not.
2. The seasonal slice is often the real product. Slicing the ramp months across two years surfaced the
   month-by-month wins that the single-window view could not.
3. The 1.0 scripts had three defects (median-based gate, duration-based format, broken build chain); the
   corrected scripts in `03_scripts/` are the ones to use. When the doc and the code disagree, trust the
   code and fix it.
4. Some signals are not available: transcripts are blocked in bulk (rest on comments + tags), and vidIQ
   volumes are default-geo. Name both as limitations rather than overclaiming.

---

## Where the real artifacts live

Both runs' full deliverables (the tiered idea banks, the vidIQ-backed xlsx, the final calendars, the
synthesis docs, the cold-start handoffs) are client work product and are not part of this public
template — this repo ships the reusable pipeline only, with no run data. If you run this playbook
yourself, your own project's `FINAL/` folder is where your equivalents land (see the layout in
[`01_pipeline_playbook.md`](01_pipeline_playbook.md) section 2 and the skeleton in
[`04_templates/final_bundle_skeleton/`](04_templates/final_bundle_skeleton/)).
