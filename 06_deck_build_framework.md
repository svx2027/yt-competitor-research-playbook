# Deck build framework (Stage L): founder strategy deck plus presenter explainer

After the calendar (Phase K), Stage L turns the research and calendar into a founder-facing strategy
deck (via the Gamma MCP) plus a presenter explainer (a Word doc). This is the durable, niche-agnostic
framework for that stage, distilled from two real deck builds (see `05_worked_example.md`). The deck
exists to justify the engagement to a non-technical founder: every claim sourced, every number with a
denominator, the source named on each slide.

## The principle

A deck is a presentation layer over the pipeline data. It must not introduce a single number that is
not already in a data file. The handoff or spec is a pointer, not a source. If a number is not in a
file, either compute it read-only from the existing pull (no new API calls, no credits) and write the
result into a file, or cut it.

## The phases

1. Audience and purpose first.
   Name the reader and the decision. A handoff to a founder who already bought is forward-looking: the
   path and the next action. A pitch to win the work is justification-heavy. The closing slide must
   match the audience: a handoff ends on the path, not on caveats. Limitations belong in the explainer.

2. Cross-check every number to a data file.
   For each figure in the spec, open the cited file and confirm it. Numbers that appear only in the
   handoff are suspect. If a number is not reproducible from a file, recompute it read-only and write
   it into a sourced file so the citation is real, or drop the claim. Worked example: in the second
   build, the spec's month medians (including one figure in the hundreds of thousands) were in no file
   and did not reproduce; the fix was to recompute the by-month table, write it into
   seasonal_summary.md, and cite the corrected numbers.

3. deck_content.md is the single source of truth.
   One card per section. Each card carries a title, a one-line message, up to 5 sentence-case points
   (no nested bullets), and a Source line. Keep it to the operator's style: no em dashes, no emojis,
   numbers with denominators. A clean source file is regeneration-safe. You maintain this file, not the
   live deck: edit it, then regenerate.

4. Constrain the generator.
   textMode "preserve" is not literal. The generator still paraphrases, adds connectors, em dashes,
   emojis, and labels. Pass explicit guardrails: no em dashes, no emojis, no AI-generated infographic
   images, native text and stat blocks only. Spell out hero diagrams stage by stage; auto-layout
   summarizes and reorders (a 7-stage funnel left to the tool collapsed to 3 stages out of order).
   Choose theme and image source deliberately: for a numbers-defensible deck use pictographic or no
   images, never AI-generated infographics, which garble and invert numbers and cannot be edited.

5. Render to pixels and review every slide.
   Do not judge a visual deck from its structure or HTML. Export the pptx, convert it to images, and
   look at every slide. Check each one: numbers exact and legible, no em dashes or emojis, hero visuals
   correct and in order, a Source line present, content fills the card, tone fits the audience. Note
   that the web view scales to fit while the pptx export can under-fill cards, so treat the live link
   as the presentation surface.

6. Defensibility pass.
   Every stat has a denominator and a named source visible on the slide. No AI-generated visual carries
   baked-in numbers. Any chart or diagram reproduces the real data, verified against the source file.
   The presenter explainer carries the glossary, the per-slide talking script, the exact numbers with
   sources, 3 to 5 founder questions, and the per-slide limitation. Limitations live here, not on the
   closing slide.

7. Fix loop: regenerate over patch.
   When the problems are generation artifacts (em dashes, paraphrase, bad auto-diagrams, AI
   infographics), regenerate from the corrected source-of-truth with explicit guardrails. One clean
   pass beats many editor patches. Use the editor agent for targeted, low-risk tweaks (recolor a
   heading, add a footer, restructure one card); it can re-paraphrase while editing, so guard numbers
   explicitly. The generate tool cannot edit an existing deck, it makes a new one, so expect a new URL
   on regenerate.

8. Ship the bundle.
   Keep together: deck_content.md (source of truth), the pptx, the presenter explainer docx, and the
   rendered review images. Re-state the limitations in the explainer, name the sources on the slides,
   and leave the closing slide on the path forward.

## Gamma gotchas (the generator we use)

1. "preserve" still paraphrases and adds em dashes, emojis, and labels.
2. Auto funnels and diagrams summarize and reorder; spell out each stage in order.
3. imageOptions can still yield an AI infographic via the infographic element; forbid it, use native
   stat blocks.
4. Inline heading colors can drift off-theme.
5. The pptx export can under-fill cards that look full in the web view.
6. Source lines can be dropped in layout; re-add them as muted footers.

## Tooling

Generate with the Gamma MCP: format presentation, textMode preserve, exportAs pptx, numCards set,
theme and image source chosen. Render to review with LibreOffice headless:
`soffice --headless --convert-to pdf <deck>.pptx`, then `pdftoppm -png -r 135 <deck>.pdf slide`.
Build the explainer with the docx skill (python-docx is fine), then validate the file.

## Pre-flight checklist (before the deck goes out)

1. Every number on every slide traces to a named file.
2. No em dashes and no emojis anywhere.
3. The hero diagram shows all stages in the right order.
4. No AI-generated image carries numbers.
5. Every slide names its source.
6. The closing slide is forward-looking; limitations are in the explainer.
7. You looked at every slide as a rendered image, not just the outline.

Reference builds: both runs described in `05_worked_example.md`; the second run's own deck-stage
learnings live at `FINAL/01_strategy_deck/deck_build_learnings.md` inside that project's working copy.
