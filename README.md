# Niche Competitive Analysis General Format and Pipeline Playbook

A copy-and-go folder for running a YouTube competitor-research-to-content-calendar project for any
niche. Copy this whole folder, rename it `<niche>-competitive-research`, and work inside the copy.
It carries its own memory (`CLAUDE.md`), the full pipeline, the scripts, the templates, and a kickoff
prompt that makes Claude ask you the right questions before starting.

## What you get out the other end

A 12-week content calendar (xlsx) where every idea is sourced from a proven competitor breakout video,
backed by vidIQ search demand, and slotted into the week where it fits the niche's exam or season
cycle. The weekly sheet is over-supplied (about 20 ideas/week) so the team picks the best half. Plus
the full research trail (outliers, tags, seasonal slice, depth, synthesis) behind it, and an optional
founder strategy deck (see `06_deck_build_framework.md`).

## How to start a new niche in 6 steps

1. Copy this folder, rename it for your niche.
2. Do the first-time setup in `CLAUDE.md` section 7 (venv, keys, config).
3. Paste `NICHE_KICKOFF_PROMPT.md` into Claude. Answer its scoping questions.
4. Claude runs the pipeline phases (see `CLAUDE.md` section 3 and `01_pipeline_playbook.md`),
   stopping at each STOP gate for your sanity-check.
5. Claude generates the tiered ideas, backs them with vidIQ, and assembles the calendar.
6. The deliverable lands in `FINAL/04_operational_calendars/`.

## What is in this folder

| Path | What it is |
|---|---|
| `CLAUDE.md` | The portable memory: pipeline, data org, requirements, first-time setup. Read first. |
| `01_pipeline_playbook.md` | The full proven pipeline, generalised, with operator decisions, data schemas, and the full tool stack (what each tool is for, its cost, and its phase). |
| `02_advanced_framework.md` | Opt-in add-ons beyond the core pipeline. The seasonal, layered, depth, and Gemini-title methods have since graduated into the core pipeline; the rest stay optional. |
| `03_scripts/` | The corrected pipeline scripts (proven on two runs) + `config.example.yaml` + `run_order.md`. |
| `04_templates/` | Blank `context.md`, the `FINAL/` folder skeleton, the calendar schema template. |
| `05_worked_example.md` | Two completed runs (an entrance-exam-prep channel, twice) as the reference instantiations. |
| `06_deck_build_framework.md` | Stage L: turning the research and calendar into a sourced founder strategy deck (Gamma) plus a presenter explainer. The reusable deck-build framework. |
| `NICHE_KICKOFF_PROMPT.md` | Paste this to start a new niche; it makes Claude ask the scoping questions. |

## Requirements

YouTube Data API v3 key, Gemini API key (both free tier), a vidIQ account with credits. Optional
advanced layers (YouTube Analytics API for retention/CTR, Ahrefs for web demand, Gemini vision for
thumbnails) are documented in `02_advanced_framework.md` but not required for the core pipeline.

## Honest scope

This is a real, twice-proven pipeline, not a toy. It has real limitations, stated plainly: YouTube
throttles bulk transcript scraping (depth analysis leans on comment themes, not full transcripts),
vidIQ keyword volume has no country parameter (default-geo only), and the outlier-ratio threshold is
deliberately generous and can over-fire on very high-volume channels (see the SSC-run learning in
`CLAUDE.md`). The scripts carry niche constants inline; refactoring them to read `config.yaml` is an
optional one-time job (see `03_scripts/run_order.md`).
