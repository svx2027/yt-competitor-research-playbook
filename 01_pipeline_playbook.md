# Reusable competitor-research-to-calendar pipeline playbook

A niche-agnostic version of a real competitor-research project, written so it can be re-run
for any exam or YouTube niche (CAT, GATE, UPSC, NEET, a SaaS channel, etc.). Replace the placeholders,
make the operator decisions, run the phases in order, and you get the same final deliverable: a
12-week exam-cycle-anchored content calendar backed by competitor outlier data and vidIQ.

It has been run twice end-to-end on a real entrance-exam-prep channel (run 1.0 and run 2.0). Run 2.0
corrected three defects in the 1.0 scripts (a median-based outlier gate, duration-based format
classification, a broken calendar build chain) and added two methods now baked into this playbook: a
three-layer data model (core / extended / cross-language with a strict ratio firewall) and a two-year
seasonal slice for niches with a strong season. The retrospective in section 9 carries both runs' lessons.

This document covers the full arc from a cold start to the final calendar, including the calls the
operator (you) must make, the data needed, what to extract from YouTube and Gemini, how tagging
works, how performance is measured, the final output format, and a candid retrospective of what
went right, what went wrong, and how each problem was resolved.

---

## 0. How to use this playbook

This is a template. Everywhere you see a placeholder, substitute your own value:

- `{NICHE}` — the exam or topic, e.g. `CAT`.
- `{CHANNEL}` — your own channel being optimised, e.g. `YourChannelName`.
- `{COMPETITORS}` — the list of competitor channels (handles + channel IDs).
- `{WINDOW_START}` / `{WINDOW_END}` — the trailing-365-day analysis window.
- `{EXAM_CALENDAR}` — the niche's exam-cycle dates (registration, exam, answer key, result, interview).

To start a new niche, copy this whole repo to a new folder named
`{niche}-competitor-research` (kebab-case), wipe `out/` and `FINAL/`, keep the scripts and this
playbook, then work the phases below.

---

## 1. Operator decision checklist (make these calls before any code runs)

These are the human decisions. The pipeline is deterministic once these are set; the quality of the
output is bounded by the quality of these calls. Defaults are what worked for IPMAT.

| Decision | Default | Notes |
|---|---|---|
| Niche definition | one exam | Keep it tight. "CAT" not "MBA entrance". A blurry niche pollutes the keyword and competitor set. |
| Competitor list | 7 to 14 channels | Mix of institutional + named-creator. Too few misses patterns; too many burns API + Gemini budget. Run 1.0 tracked 11, run 2.0 tracked 13. |
| Core analysis window | trailing 365 days | Fixed start + end. The only window that carries an outlier ratio. Never "rolling" mid-project — it breaks comparability. |
| Extended window | older tail for channels over ~2 years | Absolute-views and seasonal only, never a ratio. Ends where the core window starts (no overlap). Skip for niches with no season and no long-lived channels. |
| Seasonal focus | yes if the niche has a season | If yes, set the season months and the two years to compare (CAT: May to Aug, 2025 and 2024). The seasonal slice is often where the real findings are. If no, run core-window only. |
| Cross-language mining | optional | A same-market channel in another language (e.g. a Hinglish parent of an English channel). Mined for topic/format only, re-expressed in the target language, never a ratio, never quoted for CTR. |
| Outlier threshold | count-based: 3x channel-format median if that cell has 500+ in-window videos, else 5x | Per channel-format, not channel-wide. Cells under 8 videos are flagged thin-baseline and lean on absolute views. (1.0 keyed this on the wrong variable; see retrospective.) |
| Format taxonomy | short / long / live | Live from API metadata (liveBroadcastContent / liveStreamingDetails), never duration. Short = non-live duration at or under 180s (fixed proxy; the Data API exposes no Shorts flag). |
| Tier definitions | Tier 1 = dual-lens top (views ∪ ratio); Tier 2 = next by ratio; Tier 3 = next by views | 80 ideas/tier worked for IPMAT. Scale to your idea appetite. |
| Calendar horizon | 12 weeks (+ optional Week 0) | Long enough to span an exam cycle's hot months; short enough to stay actionable. |
| Weekly over-supply | 20/week: 8 short, 6 long, 4 live, 2 playlist | Over-supply so the team picks the best 50 to 60%. Every idea is pre-validated, so choice costs nothing. (IPMAT shipped ~8/week; CAT over-supplied.) |
| Best-title source | Gemini (free) | Gemini writes the best title per vidIQ guidelines; keep the original competitor title alongside. Use vidIQ score_title (5 credits each) only if you specifically want CTR scores on draft titles. |
| vidIQ budget | ~200 to 1,000 credits | keyword_research is 5 credits each; dedupe keywords first. CAT spent ~165 (keywords only, Gemini titles). Volumes are default-geo (no country parameter). |
| Second-creator routing | yes/no | Decide whether lifestyle/meme content routes to a separate vehicle or the main channel. |

Record your answers in `context.md` at the new repo root before starting. They are the project's
constitution.

---

## 2. Folder structure

```
{niche}-competitor-research/
├── .env                                 # YT_API_KEY, GEMINI_API_KEY (never commit, never read in tool calls)
├── .env.example                         # placeholder keys only — the only env file committed
├── .venv/                               # python venv: requests, python-dotenv, youtube-transcript-api, openpyxl
├── context.md                           # the operator-decision constitution (section 1 answers)
├── README.md                            # repo overview
├── CLAUDE.md                            # durable rules for the source repo + pipeline
├── 03_scripts/                          # the corrected pipeline (see run_order.md for the edit map)
│   ├── resolve_channels.py              # Phase A: handles → UC ids, sub-count match
│   ├── fetch_videos_layered.py          # Phase D1: layered pull (core / extended / cross-language)
│   ├── compute_stats_core.py            # Phase D2: per-(channel, format) baselines, core only
│   ├── compute_outliers_core.py         # Phase D3: count-based 3x/5x outliers + thin-baseline flag
│   ├── phase_e_tag_videos.py            # Phase E: Gemini topic/format/hook/language tagging (--input/--output)
│   ├── make_seasonal_subsets.py         # Phase S: extract the season rows to tag
│   ├── seasonal_slice.py                # Phase S: rank what wins by season/topic/format
│   ├── depth_winners.py                 # Phase Dp: format-stratified depth (comments + transcripts + Gemini)
│   ├── gen_titles_gemini.py             # Phase T: best titles via Gemini (free)
│   └── build_calendar.py                # Phase K: the fresh calendar builder (6-sheet xlsx)
├── out/                                 # all raw + intermediate pipeline outputs (layered CSVs)
└── FINAL/                               # upload-ready clean bundle. The deliverable lives here.
    ├── 00_README.md                     # bundle overview
    ├── CLAUDE.md                        # authoritative deliverable-side rules
    ├── 01_strategy_deck/                # deck + outline + explainer + action playbook + calendar md
    ├── 02_synthesis_docs/               # master_synthesis (v1 locked) + synthesis_v2 + supporting docs
    ├── 03_master_playbook/              # exam-cycle research pack + keyword playbook + vidIQ data tables
    ├── 04_operational_calendars/        # the FINAL calendars (xlsx + csv) — the money output
    ├── 05_{channel}_youtube_studio_data/ # your channel's first-party analytics exports
    ├── 06_{channel}_first_party_tagged/ # your own videos tagged on the same axes
    ├── 07_competitor_pipeline_data/     # D1..D5 + Phase E clean copies, with batch2 parallels
    └── 08_pipeline_reference/           # this playbook + context + learnings + execution playbook
```

Conventions: scripts at repo root, raw output to `out/`, clean copies promoted to `FINAL/`. The
`FINAL/` bundle is what you share. `out/` is the working area.

---

## 3. Inputs you must gather before starting

1. **Two API keys** in `.env`: a YouTube Data API v3 key and a Gemini API key. Both free-tier are
   enough (YouTube 10K units/day; Gemini free tier covers tagging, depth themes/hooks, and titles).
   Note: `.env` cannot be copied across projects by the agent (a safety classifier blocks it); paste
   the keys in by hand.
2. **A vidIQ account with credits** (for keyword volume + title scoring at the calendar stage).
3. **Competitor channel IDs** — resolve every handle to its `UC...` channel ID. Handles lie
   (phantom channels, renamed handles). Confirm each ID against the channel's real subscriber count.
4. **Your own channel's YouTube Studio exports** — demographics, geography, traffic source, and a
   per-video CTR + impressions export. This is the only place CTR exists; competitors never expose it.
5. **The niche's exam-cycle calendar** — registration opens, exam date, answer-key release, result
   date, interview/WAT-PI window, plus the academic-calendar overlay (when the target students are
   free to consume content). For IPMAT this was the CBSE Class 11/12 calendar.

---

## 4. The pipeline, phase by phase

Run phases in order. Fetch and depth scripts checkpoint to a `.progress.json`, so an interrupted run
resumes. STOP points are where the operator sanity-checks before spending more API/credit budget. The
exact commands and the per-niche edit map are in `03_scripts/run_order.md`.

### Phase 0 — Scoping
Write `context.md` with the section-1 decisions: the channel set with each channel's data layer, the
core and extended window dates, whether the niche has a season (and which months/years), and any
cross-language channel to mine. Lock these before any code runs.

### Phase A — Channel resolution + vidIQ balance  (`resolve_channels.py`)  → STOP A
- Edit the `CHANNELS` list (search name, expected subs, tier, language, layer), then run the script: it
  searches each name, prints candidates, and auto-picks the one whose sub count matches, flagging
  low-confidence picks. Handles lie; the sub-count match is the real check.
- Output `out/channels_resolved.csv` (name, uc_id, uploads, subs, layers, language, match_conf).
- Run `vidiq_balance` to confirm credits. Optional: a few `vidiq_keyword_research` calls on the core
  terms to confirm the niche has search volume worth pursuing.
- **STOP A**: confirm the resolved channel list and layer assignments before pulling data.

### Phase D1 — Layered video fetch  (`fetch_videos_layered.py`)
- YouTube API `playlistItems` (uploads playlist) + `videos` endpoints, with age-adaptive windows.
- Writes three layered files: `out/competitors_core_365d.csv` (locked 365 days, the ONLY ratio basis),
  `out/competitors_extended.csv` (older tail for channels over ~2 years, no overlap with core), and
  `out/competitors_hinglish.csv` (the cross-language layer, full span, mining only).
- Each row carries `data_layer`, `tier`, and `source_language` so layers never silently mix.
- `format` is from API metadata: live from `liveBroadcastContent` / `liveStreamingDetails`; short =
  non-live duration at or under 180s (fixed proxy, the Data API has no Shorts flag); else long.
- Firewall: only the core file is ever read by the stats and outlier scripts.

### Phase D2 — Per-channel-format stats, core only  (`compute_stats_core.py`)
- Reads only `competitors_core_365d.csv`. For each (channel, format) computes median, mean, p75, p90,
  max, n_videos. Output `out/channel_format_stats.csv`. The median is the outlier denominator.

### Phase D3 — Outlier detection, core only  (`compute_outliers_core.py`)  → STOP B
- `outlier_ratio = view_count / channel_format_median`, computed on the core file only.
- Threshold is count-based: 3x if that channel-format cell has 500+ in-window videos, else 5x. Cells
  under 8 videos get `thin_baseline=yes` and lean on absolute views (this stops a degenerate
  small-channel median, e.g. a course-dump channel, from faking 1000x "breakouts").
- Output `out/outliers_core.csv` (adds `channel_format_median, channel_format_n, outlier_ratio,
  threshold_applied, thin_baseline`).
- **STOP B**: eyeball the outliers before paying for depth. Real breakouts or data artifacts? Are the
  thin-baseline rows promo/funnel content rather than organic wins?

### Phase E — Gemini tagging  (`phase_e_tag_videos.py`)  → STOP D
- Tag every video on four axes: `topic`, `format_archetype`, `hook_type`, `language`, against a fixed
  per-niche taxonomy (`ALLOWED_*` + `TAG_PROMPT`). The prompt is **byte-identical across every run and
  layer** — never improve it mid-stream or cross-comparison breaks.
- Reusable via `--input` / `--output`: run it on the core file, then (if seasonal) on the seasonal
  subsets. Model `gemini-2.5-flash-lite`, concurrent with adaptive rate limiting, resumable.
- Output `out/competitor_videos_tagged_core.csv` and the seasonal tagged files.
- **STOP D**: review tags on the top 30 outliers + your top performers. `tag_report.py` and
  `phase_e_sanity_report.py` give the distribution and quality checks.

### Phase S — Seasonal slice  (`make_seasonal_subsets.py`, `seasonal_slice.py`)  — if the niche has a season
- `make_seasonal_subsets.py` extracts the season rows (e.g. May 1 to Aug 31, both years) from the
  extended and cross-language files; tag those subsets with `phase_e_tag_videos.py`.
- `seasonal_slice.py` isolates each season across all layers and ranks what won by topic, format, and
  hook. Output `out/seasonal_may_aug_*.csv`, `seasonal_topic_performance.csv`, `seasonal_summary.md`.
- This is often where the strongest findings live: what topic/format wins in the ramp month-by-month.
- Skip this phase entirely for niches with no strong season.

### Phase Dp — Depth on winners  (`depth_winners.py`)  → STOP C
- Replaces the old split D4/D5 with one format-stratified pass. Samples winners per format (so the
  long-form, livestream, and Shorts playbooks are each learned on their own terms, not drowned out by
  Shorts), with a per-channel cap on the ratio picks so a degenerate-median channel cannot flood them.
- For each: top comments → Gemini themes (a theme counts at 2+ mentions), plus transcript →
  Gemini opening/hook/arc/CTA. Concurrent (6 workers), resumable.
- Output `out/depth_winners.csv` / `.json` / `.md`.
- Reality: YouTube blocks bulk transcript scraping from one IP after a few requests, so transcript
  coverage is partial; the depth rests mostly on comment themes + tags. State this as a limitation.
- **STOP C**: sanity-check theme + hook quality.

### Phase F — Targeted probes
- Niche-specific cross-checks: under-served subtopics, lead-magnet/funnel patterns, named-creator vs
  institutional performance, format gaps (e.g. "we run 1 trending-audio short, competitors run 494").

### Phase G — Synthesis  (`02_synthesis_docs/synthesis.md`)  → STOP E
- 8 to 12 findings, each as hypothesis → evidence (with magnitudes + denominators) → implication →
  counter-evidence → confidence. Rank findings by both lenses (outlier ratio AND absolute views) and
  state which lens each uses. This is where the ranking-lens lesson lives (see retrospective).
- **STOP E**: do not build a calendar until findings are locked.

### Phase H — Exam-cycle / seasonality research  (`03_master_playbook/`)
- Build the cycle research pack: month-by-month audience availability + every dated cycle anchor
  (registration, exam, answer key, result, interview). For a seasonal niche, ground the month themes in
  your own `seasonal_summary.md` (what actually won by month), not guesses. This is what makes the final
  calendar a *calendar* and not a heap.

### Phase J — vidIQ demand backing  (MCP)
- Dedupe primary keywords first (IPMAT: 240 ideas → 37 unique keywords, saving ~50% of credits).
- `vidiq_keyword_research` per unique keyword → search volume + competition + opportunity. Cache to a
  results file so rebuilds don't re-spend credits. Volumes are default-geo (no country parameter).
- `vidiq_score_title` (5 credits each) is optional — use it only if you want CTR scores on draft titles.
  CAT skipped it and titled with Gemini for free.

### Phase K — Calendar assembly  (`build_calendar.py`)
- A fresh, self-contained builder (replaces the 1.0 build chain, which is broken). Reads the seasonal,
  outlier, and depth outputs, tiers the ideas, and slots an over-supplied 20 per week (8 short, 6 long,
  4 live, 2 playlist) against each week's cycle theme. Ideas with no week fit go to the Evergreen pool;
  series go to a Playlists sheet.
- Verifies every source URL live (HTTP check) before writing. Writes the 6-sheet xlsx (see section 8)
  plus `out/calendar_data.json` (the slotted ideas, for titling).
- Edit its dictionaries per niche: `KEYWORD_DEMAND`, `TOPIC_TO_KEYWORD`, `TITLE_FRAME`, `THUMB`,
  `PLAYLISTS`, `WEEK_SCHEDULE`. The week schedule is the most niche-specific edit; anchor it to your
  exam_calendar.

### Phase T — Best titles  (`gen_titles_gemini.py`)
- Writes the single best title per slotted idea following vidIQ/YouTube title guidelines, using Gemini
  (free). The original competitor title stays in the sheet for comparison. Reads `calendar_data.json`,
  writes `out/gemini_titles.json`. Re-run `build_calendar.py` afterward to merge the titles in.
- Titles can drift or repeat when source ideas share a keyword; they are drafts the team polishes.

---

## 5. Data schemas at each stage

| Stage | File | Key columns added |
|---|---|---|
| A | channels_resolved.csv | name, uc_id, uploads, subs, expected_subs, tier, language, layers, match_conf |
| D1 | competitors_core_365d.csv (+ _extended, + _hinglish) | channel, channel_id, data_layer, tier, source_language, video_id, title, description, published_at, duration_*, format, view/like/comment_count, urls, language_hint |
| D2 | channel_format_stats.csv | channel, format, n_videos, median, mean, p75, p90, max |
| D3 | outliers_core.csv | + channel_format_median, channel_format_n, outlier_ratio, threshold_applied, thin_baseline |
| E | competitor_videos_tagged_core.csv (+ seasonal tagged) | + topic, format_archetype, hook_type, language |
| S | seasonal_may_aug_{year}.csv, seasonal_topic_performance.csv | season, source_language, topic, n_videos, total/median/max views |
| Dp | depth_winners.csv / .json | + comments_status, comment_themes, transcript_available, opening, hook_mechanic, content_arc, cta_type |
| your channel | {channel}_videos_tagged.csv | + ctr_pct, impressions, view_count_drift_pct |
| J | vidiq_keyword_results (cached) | keyword → volume, competition, overall |
| K | calendar_data.json + the final xlsx | slotted ideas; see section 8 |
| T | gemini_titles.json | video_id → best title |

---

## 6. Performance measurement — how "good" is defined

- **Outlier ratio** = views ÷ the channel's own median for that format. This is the channel-relative
  breakout lens. A 10x means the video did 10 times the channel's normal.
- **Absolute view count** = raw reach. Different videos win on each lens (the F8 split).
- **Views per subscriber** = the channel-economics lens. Segments channels into named-creator-lifestyle
  (high) vs institutional (low). Tells you which competitors are structurally comparable to you.
- **Outlier yield** = % of a month's uploads that became outliers. Falls with video age; correct for
  the compounding window before comparing months.
- **vidIQ keyword volume + opportunity** = forward-looking demand signal for the idea's topic.
- **vidIQ title score** = CTR-potential of the drafted title (0-100).
- **CTR + impressions** = available for your own channel only (Studio export), never competitors.

---

## 7. The tool stack: what each tool is for, its cost, and its phase

This is the full set of tools the pipeline uses end to end. Each does one job the others cannot; know
which gives what before you spend on it.

| Tool | Phase | What it is for | What it cannot do | Cost |
|---|---|---|---|---|
| YouTube Data API v3 | A, D1, Dp | The raw facts: channel resolution, every video's views/format/dates, top comments | No search demand, no topic labels, no Shorts flag, no CTR | ~250 units for ~7 channels; free tier 10K units/day |
| youtube-transcript-api | Dp | Video transcripts for hook/arc analysis | Blocked after a few requests from one IP (anti-scraping); coverage is partial | no quota, but unreliable in bulk |
| Gemini (gemini-2.5-flash-lite) | E, Dp, T | The AI layer: topic/format/hook/language tagging, comment-theme and hook extraction, and best-title writing | Not a data source; tag the same prompt every time or comparison breaks | free tier sufficient |
| vidIQ MCP `keyword_research` | A, J | The demand layer the YouTube API cannot give: real search volume + opportunity per keyword | No country parameter, so volumes are default-geo | 5 credits per call; dedupe keywords first |
| vidIQ MCP `score_title` | J (optional) | 0-100 CTR-potential score for a draft title | Low value on titles the team will rewrite; emoji/filter trips it | 5 credits per call; CAT skipped it |
| vidIQ MCP `balance` | A | Pre-flight credit check | — | 0 credits |
| Claude Code | all | Orchestration: runs the scripts, does the statistics and synthesis, assembles the bundle | — | — |
| Gamma MCP | L | Generates the founder strategy deck (presentation → pptx) | Cannot edit an existing deck; regenerate to change it | Gamma subscription |
| docx skill (python-docx) | L | The presenter explainer (talking script, exact numbers + sources, founder Q&A, limitations) | — | free |
| LibreOffice + pdftoppm | L | Render the deck to images to review every slide as pixels | — | free |

Always run `vidiq_balance` before a Phase J run, and confirm the credit budget with the operator before
any bulk spend. With Gemini titles and keyword-only vidIQ, a full run costs a few hundred credits, not
thousands (CAT spent ~165). The advanced/optional tools (thumbnail scoring, retention via the YouTube
Analytics API, Ahrefs, etc.) live in `02_advanced_framework.md`. The deck stage is detailed in
`06_deck_build_framework.md`.

---

## 8. Final output specification (the deliverable)

A single xlsx, 6 sheets, in `FINAL/04_operational_calendars/`, built by `build_calendar.py`. Full
column reference in `04_templates/calendar_schema_template.md`.

1. **Read me first** — what the file is, top ideas for the current week, how to read, counts.
2. **Weekly calendar** — the money sheet. Frozen header row + merged week-section headers, each
   `Week N | Mon DD MMM to Sun DD MMM YYYY | Theme: ... | Series: ...`. Over-supplied at ~20 ideas per
   week (8 short, 6 long, 4 live, 2 playlist) plus an optional lighter Week 0, so the team picks the
   best 50 to 60%. 17 columns: Format, Best title, Original title, Thumbnail text, Primary keyword,
   Secondary keywords, Why this idea (cycle anchor + vidIQ data + outlier evidence), Search volume,
   Ranking opportunity, Competitor data, Notes, Owner/Status (blank), Publish window, Production effort,
   Faculty needed, Channel, Source video (clickable, verified-live hyperlink).
3. **Complete idea bank** — every qualifying idea, Tier 1 / 2 / 3, same columns; the pool the weekly
   sheet draws from.
4. **Evergreen pool** — off-cycle ideas (concept content) ranked by opportunity, same schema.
5. **Playlists** — ready-to-run series (Hero / Lane), each with a target keyword, run window, the proof
   it rests on, and its episode list.
6. **Legend & Sources** — column reference + the week-theme table + citations to the cycle research docs.

Every idea must carry a verified, clickable source-video URL (build_calendar.py HTTP-checks them all).
That is the non-negotiable the operator set and the thing that makes each idea auditable.

---

## 9. Retrospective: what went right, what went wrong, how resolved

### What went right
- **Reusing the tier-construction logic across v1 → v2 → v3.** The outlier-ranking and slot code
  carried forward unchanged; only the presentation layer changed. Build the data layer once, stable.
- **Locked methodology held.** Byte-identical Gemini prompts and the fixed window meant batch-2
  channels merged cleanly with batch-1.
- **URL verification.** HTTP-checking all 240 source URLs caught dead links before they reached the
  operator (0 dead in the final run, but the check is cheap insurance).
- **Keyword + title dedup before vidIQ.** 240 ideas collapsed to 37 keywords + 175 titles, roughly
  halving the credit spend without losing coverage.
- **STOP gates.** Sanity-checking outliers before paying for comments/transcripts avoided wasted
  Gemini + API calls.

### What went wrong, and how it was resolved
- **F8 / the ranking-lens conflation (v1).** The original synthesis treated "the viral title template"
  as one thing. It is two: pipe-separated keyword-stacked titles win the outlier-ratio ranking;
  short conversational titles win the absolute-views ranking. **Resolved** by always stating which
  lens a finding uses, and by drafting two title styles depending on the source's lens.
- **View-count drift between pulls.** A re-pull on the real run found 38.4% of videos had shifted >10% in views.
  **Resolved** by designating the v2 re-pull as the truth file and quoting only it for first-party
  magnitudes.
- **Mass-deletion baseline distortion.** A competitor wiped ~900 old shorts mid-window, distorting its
  median. **Resolved** by flagging any >10% total-video drop on re-pull and deciding adjustment vs
  accept-as-is explicitly.
- **vidIQ cost assumption (this round).** The plan assumed ~1 credit/call; actual is 5 credits/call,
  so the real cost was ~4x the estimate. **Resolved** by catching it at the schema-fetch step,
  re-checking balance, and confirming the budget with the operator before spending.
- **Columns-not-rows mistake (v2 → v3).** The v2 xlsx matched the reference file's 11 columns but
  grouped rows by tier instead of by week, so it read as a heap, not a calendar. The exam-cycle
  research docs were never wired in. **Resolved** by rebuilding as v3: 12 week-sections anchored to
  the exam cycle, a clickable source-video column, day-precise publish windows, and an evergreen pool.
  Root cause: matched the reference's surface (columns) without its structure (weekly, cycle-anchored
  rows). Lesson: when mimicking a reference artifact, replicate its organising principle, not just its
  column list.
- **Transient MCP + content-filter failures (this round).** A handful of `score_title` calls failed
  on emoji-heavy titles or a content filter. **Resolved** by retrying the transient ones and using a
  median-score fallback for the single filter-blocked title.

### What run 2.0 corrected and added
- **The outlier gate was keyed on the wrong variable.** The 1.0 script used `5x if median < 1000 else
  3x` (a view-median gate), but the documented rule is count-based. **Resolved** in
  `compute_outliers_core.py`: 3x if the channel-format cell has 500+ videos, else 5x, plus a
  thin-baseline flag for cells under 8 videos. Lesson: when the doc and the code disagree, the code is
  what ran; check it.
- **Format was classified by duration, contradicting the doc.** 1.0 used `dur_s > 1800` for live.
  **Resolved** in `fetch_videos_layered.py`: live from API metadata, short = non-live ≤180s proxy. Also
  corrected the doc's false claim that the Data API has a "Shorts flag" — it does not, so the duration
  proxy is mandatory, not a shortcut.
- **The calendar build chain was broken.** The 1.0 build script imported a module that was never
  copied into the playbook, so it could not run. **Resolved** by writing `build_calendar.py`
  fresh and self-contained, mirroring the proven 6-sheet schema. The defective 1.0 scripts were
  retired rather than carried forward.
- **Seasonal layering with a firewall (the big method add).** For a seasonal niche, pull a core 365-day
  window for ratios plus an age-adaptive older tail and a cross-language layer for inspiration, kept in
  separate files so a ratio never touches the older or cross-language data. The May-to-August slice
  across two years was where the strongest CAT findings came from.
- **Degenerate medians fake breakouts.** A small channel that dumps a course playlist gets a tiny
  long-form median, so its promo videos show absurd ratios (1000x). **Resolved** by the thin-baseline
  flag and by reading these as funnel content, not organic wins.
- **Depth must be format-stratified.** A raw top-by-views list is almost all Shorts, so the long-form
  and livestream playbooks never surface. `depth_winners.py` samples per format.
- **Transcripts are unreliable.** YouTube blocked bulk scraping after ~13 of 314; a serial retry
  recovered 0. The depth analysis rests on comment themes + tags. Name it as a limitation, do not plan
  around full transcripts.
- **Gemini titles beat paid title scoring for draft titles.** Titles get rewritten by the team, so
  spending 5 credits each to score drafts is low value. `gen_titles_gemini.py` writes a best title per
  vidIQ guidelines for free; keep the original competitor title alongside.
- **Two operational gotchas.** vidIQ keyword volume has no country parameter (volumes are default-geo,
  state it). And `.env` cannot be copied across projects by the agent (a safety classifier blocks it);
  the operator pastes keys in by hand.

### The meta-lesson
Decide the *organising principle* of the final artifact at the very start (here: the exam cycle), and
let every upstream phase serve it. The v2 detour happened because the organising principle was settled
late. For a new niche, lock the exam-cycle calendar (Phase H) conceptually before generating ideas.

---

## 10. Worked examples: the two real runs

This playbook is distilled from two completed runs on a real entrance-exam-prep channel. Full detail
is in `05_worked_example.md`; the short version:

- **Run 1.0.** 11 channels, 6,687 in-window videos, 570 outliers, a tiered idea bank, and a
  12-week exam-cycle-anchored calendar. Established the locked window, the ranking-lens discipline, the
  STOP gates, and the calendar-as-organising-principle lesson.
- **Run 2.0.** 13 channels (10 same-language competitors + the index channel + 2 cross-language
  fallback), 11,323 videos across the three data layers, 230 core outliers, 5,748 tagged, a May-to-Aug
  seasonal slice across 2025 and 2024, 314 format-stratified depth winners, and a 13-week over-supplied
  calendar (20/week). Added the layered data model + firewall and the seasonal slice, corrected the
  three 1.0 script defects, and switched titles to free Gemini.

For a new niche the pipeline is identical; only the niche constants, the data layers, the season window,
and the cycle anchors change. Whether to run the seasonal phases depends on whether the niche has a
strong season (an exam-prep niche usually does; an always-on SaaS channel may not).
