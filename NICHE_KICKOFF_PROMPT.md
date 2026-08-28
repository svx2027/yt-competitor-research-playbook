# Niche kickoff prompt

Paste the block below into Claude when you start a new niche project inside a copy of this folder.
It tells Claude to read the playbook, then interview you before doing anything.

---

```
We are starting a new competitive-analysis project using this playbook folder. Before doing anything:

1. Read CLAUDE.md, then 01_pipeline_playbook.md, then 02_advanced_framework.md in this folder.
2. Do NOT run any pipeline phase, API call, or vidIQ call yet.
3. Interview me to fill context.md. Ask me, grouped and a few at a time so it is easy to answer:

   Scope
   - What is the niche / exam, and which of my channels are we growing?
   - What is my growth goal in one line?

   Competitors
   - Which competitor channels should we track? (names or handles; aim for 7 to 14)
   - Is there a same-market channel in another language to mine for ideas (e.g. a Hinglish parent of an
     English channel)? It is mined for topic/format only, re-expressed in your language, never a ratio.
   - Should you also discover more competitors with vidIQ similar_channels / breakout_channels?

   Window + methodology
   - What fixed 365-day core window? (or default to trailing 365 days from today)
   - Does this niche have a strong season (an exam window the audience clusters around)? If yes, which
     months, and shall we compare two years? (this drives the older-tail pull and the seasonal slice)
   - Keep the locked methodology: count-based 3x/5x outlier threshold (per channel-format, thin-baseline
     guard under 8 videos), live from API metadata, short = non-live under 180s? (default yes)

   Tiers + calendar
   - Idea-bank size per tier (default 80), and the weekly over-supply mix (default 20/week: 8 short,
     6 long, 4 live, 2 playlist, so the team picks the best 50 to 60%)?
   - Calendar horizon (default 12 weeks), a lighter Week 0 kickoff (yes/no), and the week-1 Monday?
   - Best titles via Gemini (free, default) or vidIQ score_title (5 credits each)?
   - Route lifestyle/meme content to a second creator? (default ask later)

   Cycle calendar (this drives the week themes)
   - What are the niche's key dates: registration, exam, result, interview/selection windows?
   - When is the target audience free to consume content (school/college/work calendar overlay)?

   Budgets + setup
   - Are my YouTube Data API key and Gemini key in .env yet?
   - What is my current vidIQ credit balance, and what credit budget for this run?

   Advanced layers (optional, from 02_advanced_framework.md)
   - Add any of: thumbnail scoring, native outlier cross-check, live trend signals, comment
     question-mining? (all low-effort, no OAuth) Or none for now?

4. Write my answers into context.md, show me the filled context.md, and wait for my confirmation.
5. Only then begin Phase A (channel resolution + vidIQ balance check), stopping at each STOP gate.
```

---

## Why an interview, not assumptions

Every wrong assumption at scoping (a blurry niche, the wrong competitor set, a rolling window, a
mismatched cycle calendar) silently corrupts everything downstream and is expensive to undo after the
data pull. The interview is cheap; a wrong pull is not. Claude should confirm `context.md` before
spending any API or vidIQ budget.
