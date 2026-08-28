# Final calendar schema (the deliverable)

A single xlsx, 6 sheets, lands in `FINAL/04_operational_calendars/`. Built by `build_calendar.py`.

## Sheets
1. **Read me first** — what the file is, top ideas for the current week, how to read, counts.
2. **Weekly calendar** — frozen header row + N merged week-section headers, each:
   `Week N | Mon DD MMM to Sun DD MMM YYYY | Theme: ... | Series: ...`. Over-supplied at ~20 ideas per
   week (8 short, 6 long, 4 live, 2 playlist) so the team picks the best 50 to 60%. A lighter Week 0 is
   optional. Every idea is a pre-validated outlier, so choice costs nothing.
3. **Complete idea bank** — every qualifying idea, Tier 1 / 2 / 3, same columns. The pool the weekly
   sheet draws from.
4. **Evergreen pool** — off-cycle ideas (concept content), ranked by vidIQ opportunity. Same columns.
5. **Playlists** — ready-to-run series (Hero / Lane), each with a target keyword, run window, the proof
   it rests on, and its episode list.
6. **Legend & Sources** — column reference + the full week-theme table + citations to the cycle
   research docs.

## The 17 columns (Weekly calendar + idea bank + Evergreen pool)

| # | Column | Filled from |
|---|---|---|
| 1 | Format | Short / Long / Live (API metadata) |
| 2 | Best title | the recommended title, written to vidIQ/YouTube guidelines (Gemini, free; or vidIQ score_title) |
| 3 | Original title | the source competitor title, preserved verbatim for comparison |
| 4 | Thumbnail text | auto-drafted short uppercase phrase |
| 5 | Primary keyword | regex from source title / topic fallback |
| 6 | Secondary keywords | hashtag list from topic + entities |
| 7 | Why this idea | 3 lines: cycle anchor + vidIQ data + outlier evidence |
| 8 | Search volume | vidIQ keyword_research monthly search (default geo) |
| 9 | Ranking opportunity | vidIQ keyword_research overall score verdict |
| 10 | Competitor data | source video: channel, views, outlier ratio, channel-format median |
| 11 | Notes | replication caveat per (topic, format); thin-baseline or promo flags |
| 12 | Owner / Status | blank; team fills |
| 13 | Publish window | day-precise slot inside the week |
| 14 | Production effort | Low / Medium / High |
| 15 | Faculty needed | the on-camera voice or none / second-creator |
| 16 | Channel | Main / Second-creator |
| 17 | Source video | clickable hyperlink ("Open on YouTube") to the source competitor video, verified live |

Non-negotiable: every row carries a verified, clickable source-video URL. `build_calendar.py`
HTTP-checks every link before writing the sheet.
