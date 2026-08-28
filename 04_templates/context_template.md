# context.md — operator-decision constitution for {NICHE}

Fill this in before any code runs. These are the human decisions; the pipeline is deterministic once
they are set. This file is the project's source of truth for scope. Convert any relative dates to
absolute dates.

## Niche
- Niche / exam: {e.g. CAT}
- Your channel: {name + UC id}
- Why this project: {growth goal in one line}

## Analysis windows
- Core (locked, trailing 365 days, ratio math): {YYYY-MM-DD} to {YYYY-MM-DD}
- Extended (older tail for channels older than ~2 years, absolute-views and seasonal only, no ratios):
  {YYYY-MM-DD} to core start
- Seasonal slices (the research focus, if the niche has a season): {months, e.g. May 1 to Aug 31} of
  {year} and {prior year}. Set to "none" if the niche has no strong season.

## Competitors (7 to 14; mix institutional + named-creator)
Layer: which data layers the channel feeds. core only = young channels (under ~2 years).
| Channel | UC id / handle | Type (institutional / named-creator) | Language | Layer |
|---|---|---|---|---|
| | | | english | core+extended |

## Cross-language / parent-channel mining (optional)
- {A same-market channel in another language to mine for topic/format only, e.g. a Hinglish parent of
  an English spin-off. Re-express ideas in the target language, flag source_language, never quote for
  CTR, never give a ratio. Or "none".}

## Locked methodology choices
- Outlier threshold: count-based. 3x channel-format median if that channel-format cell has 500+
  in-window videos, else 5x. Thin-baseline guard: cells under 8 videos lean on absolute views, not ratio.
- Ratio math runs on the CORE window only. Extended and cross-language layers never get a ratio
  (enforced by keeping them in separate files).
- Format from API metadata: live from liveBroadcastContent / liveStreamingDetails; short = non-live
  duration at or under 180 seconds (fixed proxy, the Data API exposes no Shorts flag); else long. Hold
  the 180s cutoff fixed for the whole project.
- Gemini tagging prompt byte-identical across all batches and layers.
- Always state the ranking lens: outlier ratio (channel-relative breakout) vs absolute views (reach).
- Every idea carries a verified, clickable source-video URL.

## Tier + calendar decisions
- Complete idea bank: {default 80} ideas per tier (Tier 1 / 2 / 3).
- Weekly calendar over-supply: {default 20/week: 8 short, 6 long, 4 live, 2 playlist}. The team picks
  the best 50 to 60%; every idea is pre-validated, so choice costs nothing.
- Calendar horizon: {default 12 weeks} {plus a lighter Week 0 kickoff: yes / no}.
- Calendar start Monday: {YYYY-MM-DD}
- Best titles: {Gemini, free, default} or {vidIQ score_title, 5 credits each}. Keep the original
  competitor title in the sheet alongside the best title.
- Second-creator routing: {yes / no}

## vidIQ budget
- Credits available: {check vidiq_balance}
- Budget for this run: {keyword_research at 5 credits each; dedupe first}. Note: vidIQ keyword volume
  has no country parameter (default geo).

## Cycle calendar (drives week themes — Phase H)
| Date | Event |
|---|---|
| {YYYY-MM-DD} | Registration opens |
| {YYYY-MM-DD} | Exam day |
| {YYYY-MM-DD} | Result |
| {YYYY-MM-DD} | Interview / selection window |
- Audience-availability overlay: {when is the target audience free to consume? e.g. school/college calendar}

## Advanced layers chosen (from 02_advanced_framework.md)
- {list any opt-in items, e.g. thumbnail scoring, native outlier cross-check; or "none for now"}
