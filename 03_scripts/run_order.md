# Run order + per-niche generalization guide

These scripts are the corrected pipeline, proven end-to-end on two runs on a real entrance-exam-prep
channel (run 1.0 and run 2.0). Run 2.0 found three defects in the original run-1.0 scripts and fixed
them: a median-based outlier gate (should be count-based), duration-based format classification
(should be API-metadata-based), and a broken calendar-build chain (it imported a module that was
never copied into the playbook, so it could not run). The fixed versions are the scripts in this
folder; the originals were retired rather than carried forward.

The scripts carry niche constants inline. For a new niche you have two options:

- Quick (recommended first time): edit the constants at the top of each script directly (the channel
  list, the window dates, the season months, the taxonomy, the calendar dictionaries). Run in order below.
- Clean (optional one-time refactor): refactor each script to read `config.yaml` (schema in
  `config.example.yaml`) so future niches need zero code edits. Do it once with a live niche to test against.

Treat the first run for a new niche as a shakedown: check output row counts and a few sample rows at
each STOP.

## Run all scripts from the project root as
`./.venv/bin/python 03_scripts/<script>.py`  (so `out/` and `.env` resolve correctly).

## Order

```
# Phase A — resolve channels (also check vidIQ balance via the vidIQ MCP, not a script)
python 03_scripts/resolve_channels.py          # -> out/channels_resolved.csv  (handles -> UC ids, sub-match)

# Phase D1 — fetch videos, age-adaptive, into data layers
python 03_scripts/fetch_videos_layered.py      # -> out/competitors_core_365d.csv  (the ONLY ratio file)
                                               #    out/competitors_extended.csv   (older tail, no ratio)
                                               #    out/competitors_hinglish.csv   (cross-language, mining only)

# Phase D2 — per-channel-format baselines, core only
python 03_scripts/compute_stats_core.py        # -> out/channel_format_stats.csv

# Phase D3 — outliers, core only  (STOP: eyeball outliers before paying for depth)
python 03_scripts/compute_outliers_core.py     # -> out/outliers_core.csv  (count-based 3x/5x + thin flag)

# Phase E — Gemini tagging  (STOP: review tags on the top 30 outliers + your top performers)
python 03_scripts/phase_e_tag_videos.py --input out/competitors_core_365d.csv --output out/competitor_videos_tagged_core.csv
python 03_scripts/tag_report.py                # quick tag-distribution sanity
python 03_scripts/phase_e_sanity_report.py     # the STOP-D tag-quality review

# Phase S — seasonal slicing  (only if the niche has a season; else skip to Depth)
python 03_scripts/make_seasonal_subsets.py     # -> out/to_tag_extended_seasonal.csv, out/to_tag_hinglish_seasonal.csv
python 03_scripts/phase_e_tag_videos.py --input out/to_tag_extended_seasonal.csv --output out/competitor_videos_tagged_extended_seasonal.csv
python 03_scripts/phase_e_tag_videos.py --input out/to_tag_hinglish_seasonal.csv --output out/competitor_videos_tagged_hinglish_seasonal.csv
python 03_scripts/seasonal_slice.py            # -> out/seasonal_may_aug_*.csv, seasonal_topic_performance.csv, seasonal_summary.md

# Phase Depth — format-stratified depth on the winners  (STOP: sanity-check themes/hooks)
python 03_scripts/depth_winners.py             # -> out/depth_winners.csv/.json/.md  (comments + transcripts + Gemini)
# (transcript_recover.py is a last-resort retry; YouTube usually blocks it, expect ~0 recovered)

# Phase G synthesis is a writing task, not a script (8 to 12 findings, hypothesis-evidence-implication)

# Phase J — vidIQ demand backing (vidIQ MCP keyword_research; dedupe keywords first; cache results to a file)

# Phase K — build the calendar (fresh builder, replaces the broken IPMAT chain)
python 03_scripts/build_calendar.py            # -> FINAL/04_operational_calendars/<niche>_calendar.xlsx
                                               #    out/calendar_data.json (slotted ideas, for titling)
# Phase Titles — best titles via Gemini (free), then re-merge
python 03_scripts/gen_titles_gemini.py         # -> out/gemini_titles.json  (reads calendar_data.json)
python 03_scripts/build_calendar.py            # re-run: now merges gemini_titles.json into the xlsx
python 03_scripts/verify_calendar.py           # console check of the slotted ideas

# Phase L — founder strategy deck (Gamma MCP + docx). See ../06_deck_build_framework.md
```

## What to change per niche (the edit map, until config-refactored)

| Script | Edit at the top | What it is |
|---|---|---|
| `resolve_channels.py` | `CHANNELS` list | your competitor set: (search name, expected subs, tier, language, layer) |
| `fetch_videos_layered.py` | `CORE_START`, `CORE_END`, `EXT_START`, `SHORT_MAX_SECONDS` | the locked window, the older-tail start, the 180s Shorts proxy |
| `compute_outliers_core.py` | `COUNT_CUTOFF` (500), `THIN_MIN` (8) | methodology constants; change only with a reason |
| `phase_e_tag_videos.py` | `ALLOWED_TOPIC/FORMAT/HOOK/LANGUAGE` + `TAG_PROMPT` | your niche's tagging taxonomy. Keep the prompt byte-identical across every run and layer |
| `make_seasonal_subsets.py`, `seasonal_slice.py` | the `season_of()` months and years | your season window and the two years to compare |
| `depth_winners.py` | `STRATA`, `HINGLISH_N`, and the niche text in `THEME_PROMPT` / `ANALYSIS_PROMPT` | how many winners per format; the project-name line in the prompts |
| `gen_titles_gemini.py` | the `PROMPT` (channel name + niche references) | the title-writing brief; the rules are generic best practice |
| `build_calendar.py` | `KEYWORD_DEMAND`, `TOPIC_TO_KEYWORD`, `TITLE_FRAME`, `THUMB`, `PLAYLISTS`, `WEEK_SCHEDULE`, output filename | the most niche-specific edit; week themes anchored to your exam_calendar make the calendar a real calendar |

## Methodology held by the scripts (do not weaken)

- Ratios computed on the CORE file only. `compute_stats_core.py` and `compute_outliers_core.py` read
  `competitors_core_365d.csv` and nothing else. Extended and cross-language files carry no ratio.
- Outlier gate is count-based: 3x if the channel-format cell has 500+ videos, else 5x; cells under 8
  videos are flagged `thin_baseline=yes` and lean on absolute views.
- Format from API metadata: live from liveBroadcastContent / liveStreamingDetails; short = non-live
  duration at or under 180s (no Shorts flag exists in the Data API); else long.
- Gemini tagging prompt byte-identical across every batch and layer, or cross-comparison breaks.

## Dependencies

`pip install requests python-dotenv youtube-transcript-api openpyxl pyyaml`
`.env` with `YT_API_KEY` and `GEMINI_API_KEY`. vidIQ via MCP (check balance first). Gemini model used
by the scripts: `gemini-2.5-flash-lite` (free tier sufficient).

## Known limitations the scripts encode

- YouTube blocks bulk transcript scraping from a single IP after a few requests. `depth_winners.py`
  rests mostly on comment themes + tags; expect partial transcript coverage. State it as a limitation.
- vidIQ keyword volume has no country parameter; volumes are the tool's default geo.
