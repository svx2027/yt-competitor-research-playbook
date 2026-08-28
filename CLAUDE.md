# CLAUDE.md — Niche competitive-analysis playbook

This is the canonical, copy-and-go master playbook. It carries no run data: every real project lives
in its own copy of this folder, named `<niche>-competitor-research`. To start a new niche, copy this
whole folder and work inside the copy.

You are reading the portable playbook for running a YouTube competitor-research-to-content-calendar
project for any niche. The operator copies this whole folder to start a new project, then works
inside the copy. This file is the durable memory: it tells you the pipeline, how to organise the
data, what is required, and what to set up first if it is not set up yet.

Read order for a fresh session: this `CLAUDE.md` → `README.md` → `01_pipeline_playbook.md`. If the
operator pastes the kickoff prompt, follow `NICHE_KICKOFF_PROMPT.md`.

---

## 1. Who the operator is

A YouTube strategist, generally a non-coder, who wants plain-language, senior-engineer-to-layperson
explanations. Preferences worth carrying into every session:

- Terse, direct, no filler. State the result, not the process.
- No em dashes. No emojis. Lists use colons, not dashes. Sentence case for headings.
- Numbers always with denominators and a cited source, never adjectives alone.
- Decisions framed as recommendations with the main tradeoff, then let the operator choose.
- Preserve original casing in source content (YouTube titles etc.).
- One-step-at-a-time when uncertain; batch 3 to 7 steps when 95%+ confident no error.

---

## 2. What this folder is for

A repeatable system that turns "I want to grow channel X in niche Y" into a 12-week, exam-cycle or
season-anchored content calendar, where every idea is sourced from a proven competitor outlier and
backed by vidIQ demand data. It has been run twice end-to-end on a real entrance-exam-prep channel
(see `05_worked_example.md`). The second run corrected three script defects and added the seasonal
and data-layer methods that are now baked in. This folder is the generalised distillation of both runs.

---

## 3. The pipeline in one screen

```
Phase 0  Scoping              fill context.md with the operator decisions (see template)
Phase A  Channel resolution   resolve_channels.py -> channels_resolved.csv; confirm subs; vidiq_balance
Phase D1 Fetch videos         fetch_videos_layered.py -> core / extended / cross-language CSVs (layered)
Phase D2 Stats (core only)    compute_stats_core.py -> channel_format_stats.csv
Phase D3 Outliers (STOP)      compute_outliers_core.py -> outliers_core.csv (count-based 3x/5x + thin flag)
Phase E  Tagging (STOP)       phase_e_tag_videos.py -> *_tagged.csv (topic/format/hook/language)
Phase S  Seasonal slice       make_seasonal_subsets.py + seasonal_slice.py -> seasonal_summary.md (if seasonal)
Phase Dp Depth winners (STOP) depth_winners.py -> depth_winners.md (format-stratified: comments+transcripts+Gemini)
Phase F  Targeted probes      niche-specific cross-checks
Phase G  Synthesis (STOP)     8 to 12 findings, hypothesis-evidence-implication
Phase H  Cycle research       month-by-month exam/season anchors + audience availability
Phase J  vidIQ backing        keyword_research (5 credits each; dedupe first; default-geo volumes)
Phase K  Calendar assembly    build_calendar.py -> the deliverable xlsx (over-supplied, 20/week)
Phase T  Best titles          gen_titles_gemini.py -> gemini_titles.json (free); re-run build_calendar.py
Phase L  Founder deck (STOP)  Gamma strategy deck + presenter explainer; see 06_deck_build_framework.md
```

Full detail in `01_pipeline_playbook.md`. STOP = sanity-check with the operator before spending more
API or credit budget.

---

## 4. How to organise the data (folder convention)

Inside the working copy, keep this layout (skeleton provided in `04_templates/final_bundle_skeleton/`):

- `context.md` at root — the operator-decision constitution. Fill it first.
- scripts at root (or in a `scripts/` dir) — copied from `03_scripts/`.
- `out/` — all raw + intermediate pipeline outputs. Working area.
- `FINAL/` — clean, upload-ready bundle. Promote clean copies here. Subfolders `01_…08_`:
  - 01 strategy deck, 02 synthesis docs, 03 master playbook (cycle research),
    04 operational calendars (the money output), 05 your-channel Studio data,
    06 your-channel tagged videos, 07 competitor pipeline data, 08 pipeline reference.
- Secrets in `.env` (YT_API_KEY, GEMINI_API_KEY). Never read `.env` in tool calls. Only `.env.example`
  is ever committed, placeholders only.

---

## 5. What is required before any code runs

1. Two API keys in `.env`: YouTube Data API v3 + Gemini. Both free tiers suffice.
2. A vidIQ account with credits (keyword_research + score_title are 5 credits each).
3. Resolved competitor channel IDs (handles lie; confirm against real sub counts).
4. The operator's own channel YouTube Studio exports (only place CTR exists).
5. The niche's cycle calendar (exam/season dates) + audience-availability overlay.

If any of these is missing, that is the first setup step — see section 7.

---

## 6. Locked methodology (do not change mid-project)

- Data layers + firewall. Pull into layers: core (locked trailing 365 days, the ONLY ratio basis),
  extended (older tail for channels over ~2 years, absolute-views and seasonal only), and an optional
  cross-language layer (a same-market channel in another language, mining only). Only core ever gets a
  ratio; layers stay in separate files so they cannot cross-contaminate.
- Fixed core window (trailing 365 days). Never rolling mid-project.
- Outlier threshold is count-based: 3x channel-format median if that channel-format cell has 500+
  in-window videos, else 5x. Per channel-format, not channel-wide. Cells under 8 videos are flagged
  thin-baseline and lean on absolute views (this stops degenerate small-channel medians faking 1000x).
- Format from API metadata: live from liveBroadcastContent / liveStreamingDetails; short = non-live
  duration at or under 180 seconds (a fixed proxy, because the Data API exposes no Shorts flag); else
  long. Never classify live by duration. Hold the 180s cutoff fixed for the whole project.
- Always state the ranking lens: outlier ratio (channel-relative breakout) vs absolute views (reach).
  They surface different winners. Conflating them is the classic mistake.
- Gemini tagging prompts byte-identical across all batches and layers.
- Cross-language ideas are re-expressed in the target language, flagged by source_language, and never
  quoted for CTR or given a ratio.
- CTR is available for the operator's own channel only; never claim competitor CTR.
- Every generated idea carries a verified, clickable source-video URL.

### Learnings from a large, institution-heavy niche run

- The count-based outlier threshold is deliberately GENEROUS and, at institution scale, over-fires. A
  niche with daily-live mega-channels (one run: 38,682 in-window videos, one channel-format cell of
  ~7,000) produced 6,434 flagged outliers, 17% of all videos. The raw flag count is NEVER the
  deliverable. Rank by ratio and report the meaningful tiers (10x / 20x / 50x), and mine ideas from the
  evergreen-filtered, ratio-ranked top, not the flag list.
- The deterministic title-keyword classifier is a ROUGH FIRST PASS ONLY. On bilingual, emoji-heavy,
  phrase-style titles it agreed with Gemini only 61% and dumped 20-40% of each channel into "other",
  misranking the obvious teaching stars. For the content-mix scorecard that drives the top-N selection,
  use Gemini classification on a seeded stratified sample as the CLASSIFIER OF RECORD, and measure
  agreement; never trust the keyword pass for the ranking.
- When selecting the top-N channels to deep-study, rank by TEACHING VOLUME (long-form count) plus purity
  plus subject fit, NOT by overall educational share alone. A random channel sample is shorts-dominated,
  and for many channels the shorts are topical/motivational/promo, so overall edu% penalizes a teaching
  star whose long-form is the gold.
- Gemini tagging is NOISY on cryptic shorts (festival greetings, motivational shorts get mislabeled as
  teaching, sometimes as the top-by-views rows). Rank winners by ratio, hand-exclude misclassified
  top-by-views items, and always spot-check the top winners by reading their titles before reporting.
- Deliverable rendering: HTML to PDF via headless Chrome (`--print-to-pdf`) can hang on shutdown, so
  background it and kill once the file lands. `soffice` xlsx-to-PDF can clip wide sheets, so verify
  wide-workbook content programmatically (read the cells), not from the soffice preview. `openpyxl` and
  `python-docx` are commonly in system python; `python-pptx` usually is not, so create the project
  `.venv` and install it there.

---

## 7. First-time setup (only if not already set up)

Keep setup minimal. Do NOT set up advanced/OAuth tooling unless the operator asks; those are
documented in `02_advanced_framework.md` as opt-in.

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install requests python-dotenv youtube-transcript-api openpyxl pyyaml`
3. Copy `.env.example` to `.env`, paste the two API keys.
4. Copy `03_scripts/config.example.yaml` to `config.yaml`, fill the niche values.
5. Confirm vidIQ access by checking the balance (vidIQ MCP `vidiq_balance`).
6. Copy `04_templates/final_bundle_skeleton/` to `FINAL/` and `04_templates/context_template.md` to
   `context.md`.

The scripts in `03_scripts/` are the corrected pipeline, proven on two runs. They carry niche
constants inline. For a new niche, edit the constants at the top of each script per the edit map in
`03_scripts/run_order.md` (channel list, window dates, season months, tagging taxonomy, calendar
dictionaries); refactoring them to read `config.yaml` is an optional one-time job. The first run's
scripts were retired for three known defects (a median-based outlier gate, duration-based format
classification, a broken calendar-build chain); the corrected scripts here supersede them — see
`03_scripts/run_order.md` for what was wrong and what replaced it. Gemini model used by the scripts:
gemini-2.5-flash-lite (free tier).

---

## 8. When the operator pastes the kickoff prompt

`NICHE_KICKOFF_PROMPT.md` is the prompt the operator pastes to start a new niche. When they do, do not
assume — ask the scoping questions listed in that file (niche, channel, competitors, window, cycle
dates, budgets), confirm the answers into `context.md`, then begin Phase A. Ask before spending any
API or vidIQ budget.

---

## 9. Output style

Match the conventions of the worked example: sentence-case headers, no em dashes, lists with colons,
magnitudes with denominators and a cited source file, findings as hypothesis-evidence-implication with
counter-evidence acknowledged. The final calendar follows the 17-column schema in
`04_templates/calendar_schema_template.md`.
