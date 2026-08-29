# Advanced competitive-analysis framework: everything we could add

The core pipeline ([`01_pipeline_playbook.md`](01_pipeline_playbook.md)) is the proven, level-1 system. This document is the
level-2 menu: every capability we did NOT use in the first run but could, across vidIQ MCP,
the YouTube APIs, Gemini, and adjacent tools. Each item says what it is, why it helps, and is tagged:

- **Effort**: S (under 30 min), M (half a day), L (multi-day).
- **Cost**: API quota or vidIQ credits or free.
- **Dependency**: what must be set up first.

Pick from this menu deliberately. Do not bolt all of it on at once. The biggest wins are at the top.

In the first run we used only 3 of ~25 vidIQ MCP tools, a fraction of the YouTube Data API, none
of the YouTube Analytics API, and a narrow slice of Gemini. The list below is what that leaves on the
table.

---

## Already graduated to the core pipeline (run 2.0)

These were level-2 ideas after run 1.0; run 2.0 promoted them into the proven core
pipeline ([`01_pipeline_playbook.md`](01_pipeline_playbook.md)). Do not treat them as optional any more for a seasonal niche:

- **Two-year seasonal analysis.** Pull an age-adaptive older tail and slice the season (e.g. May to
  Aug) across two years. For a seasonal niche this is where the strongest findings live. Now Phase S.
- **Cross-language / parent-channel mining.** Mine a same-market channel in another language (e.g. a
  Hinglish parent) for topic and format, re-expressed in the target language, never given a ratio. Now
  a data layer with a firewall.
- **Format-stratified depth.** Sample winners per format so long-form and livestream playbooks are not
  drowned out by Shorts. Now Phase Dp (`depth_winners.py`).
- **Free Gemini title generation.** Best titles per vidIQ guidelines without spending credits. Now
  Phase T (`gen_titles_gemini.py`).

The items below remain genuinely optional add-ons, still not used in either run.

---

## Tier 1: biggest wins, low effort (do these next time)

### 1. Thumbnail scoring — vidIQ `score_thumbnail`
- **What**: Score each competitor (and your own draft) thumbnail 0-100 for click potential.
- **Why**: The thumbnail is the single biggest CTR lever, ahead of the title. We scored titles only,
  so half the click equation was missing. Every idea already has a thumbnail-text column with no
  validation behind it.
- **Effort S · Cost 5 credits/call · Dependency vidIQ MCP.** Note: emoji-heavy or off-topic text can
  trip a content filter; fall back to a manual review for those.

### 2. Native outlier cross-check — vidIQ `outliers`
- **What**: vidIQ's own outlier engine for a channel or keyword.
- **Why**: We hand-built 3x/5x detection from the Data API. Running vidIQ's outlier finder in parallel
  cross-validates ours and catches breakouts our fixed window or threshold missed.
- **Effort S · Cost low credits · Dependency vidIQ MCP.** Use channelId-scoped calls; keyword-scoped
  outlier search is noise for small niches.

### 3. Age-normalized performance — vidIQ `channel_performance_trends`
- **What**: View trends normalized for video age.
- **Why**: Raw views over-credit older videos that had more time to compound. The earlier
  pipeline_learnings flagged this as "required" for fair cross-video comparison; we under-used it.
- **Effort S · Cost ~20 credits for a channel set · Dependency vidIQ MCP.**

### 4. Systematic competitor discovery — vidIQ `similar_channels` + `breakout_channels`
- **What**: Find channels similar to a seed, and fast-rising channels in the niche.
- **Why**: Our 11 channels were hand-picked, which is selection bias. These surface emergent competitors
  and remove the "we only studied who we already knew" blind spot.
- **Effort S · Cost low credits · Dependency vidIQ MCP.**

### 5. Live trend signals — vidIQ `trending_videos` + `trend_categories`
- **What**: What is trending now in the niche/region.
- **Why**: Lets you inject timely trend-jack ideas into the calendar, beyond evergreen + cycle-anchored
  content. Captures spikes the 365-day window cannot see.
- **Effort S · Cost low credits · Dependency vidIQ MCP.**

### 6. Richer per-video signal — vidIQ `video_stats` / `get_videos_by_ids`
- **What**: VPH (views per hour), engagement rate, and other per-video metrics.
- **Why**: Ranking outliers by VPH or engagement rate is a sharper "is this actually winning" signal
  than raw views, especially for recent videos.
- **Effort S · Cost low credits · Dependency vidIQ MCP.**

---

## Tier 2: high impact, more effort

### 7. Audience retention curves — YouTube Analytics API
- **What**: Per-video retention curve (where viewers drop), for your own channel.
- **Why**: The best single signal for fixing hooks and pacing. We had zero retention data; we used
  static Studio CSV exports, not the live API. Knowing the 30-second drop cliff changes how you brief
  every video.
- **Effort M · Cost free quota · Dependency Google Cloud OAuth setup (the one real prerequisite).**

### 8. Traffic source + impressions/CTR over time — YouTube Analytics API
- **What**: Browse vs search vs suggested vs external split; impressions and CTR trend per video.
- **Why**: Tells you whether a video won on SEO, the algorithm, or external sharing, and closes the
  thumbnail/title feedback loop with real numbers.
- **Effort M · Cost free quota · Dependency same OAuth as #7.**

### 9. Subscriber-growth attribution — YouTube Analytics API
- **What**: Which videos drove subscribers, not just views.
- **Why**: Reorders your tiers. A video with modest views that converts subscribers may matter more
  than a high-view video that converts none.
- **Effort M · Cost free quota · Dependency same OAuth.**

### 10. Thumbnail vision analysis at scale — Gemini multimodal
- **What**: Feed competitor thumbnail images to Gemini; classify face/no-face, text density, dominant
  color, emotion, objects.
- **Why**: Quantify which thumbnail patterns correlate with outlier status across hundreds of videos,
  instead of describing thumbnails by hand. Turns thumbnail strategy from opinion into data.
- **Effort M · Cost free (Gemini) · Dependency thumbnail image URLs (already in our CSVs).**

### 11. Quantified white-space — Gemini embeddings + clustering
- **What**: Embed all in-window video titles/descriptions, cluster them, map cluster size (supply)
  against demand (vidIQ/Ahrefs volume).
- **Why**: Replaces inferred content gaps with measured ones: clusters with high demand and low supply
  are your openings. We inferred white-space qualitatively; this measures it.
- **Effort L · Cost free (Gemini) · Dependency embeddings pipeline.**

---

## Tier 3: useful additions

### 12. Web-search demand + AI visibility — Ahrefs MCP
- **What**: Google search volume, SERP analysis, "people also ask," and brand-radar (whether the
  channel/brand appears in AI answers).
- **Why**: vidIQ measures YouTube search; Ahrefs measures Google demand, which is a different and
  complementary signal. Brand-radar matters more each year as discovery shifts to AI answers.
- **Effort M · Cost Ahrefs subscription · Dependency Ahrefs MCP (available in this environment).**

### 13. Keyword-based content discovery — YouTube Data API `search.list`
- **What**: Search YouTube by target keyword to see who ranks, not just channels you already track.
- **Why**: Surfaces unknown competitors and content gaps where demand exists but your tracked set is
  silent.
- **Effort S · Cost ~100 units/query (heavier than other Data API calls) · Dependency YT API key.**

### 14. Cross-platform analysis — vidIQ Instagram tools
- **What**: `ig_outlier_reels_search`, `ig_profile_reels`, `ig_reel_watch` for Instagram competitors.
- **Why**: The real project already had an Instagram calendar, but we never analyzed IG competitors or
  Shorts-to-Reels repurposing. A whole second platform of demand sits unexamined.
- **Effort M · Cost credits · Dependency vidIQ MCP.**

### 15. Comment question-mining — Gemini
- **What**: Extract unanswered questions from comments, not just recurring themes.
- **Why**: An unanswered question with many upvotes is a direct, validated content-gap signal. We
  counted themes; we did not mine questions.
- **Effort S · Cost free · Dependency comment data (already pulled in D4).**

### 16. Script and A/B asset generation — Gemini
- **What**: Turn each calendar idea into a hook + beat-sheet + CTA draft, and generate 3 title + 3
  thumbnail-text variants for A/B testing.
- **Why**: Shortens the path from calendar row to shootable brief, and builds a test loop instead of
  shipping one guess.
- **Effort M · Cost free · Dependency the calendar (Phase K output).**

### 17. Cadence and posting-time correlation — derive from D1 data
- **What**: Correlate upload frequency and day/hour against performance, per channel.
- **Why**: Tells you the productive posting rhythm in the niche. We have the timestamps; we never ran
  the correlation.
- **Effort S · Cost free · Dependency D1 output only.**

### 18. Deck and thumbnail production — Gamma, Canva
- **What**: Auto-generate the strategy deck (Gamma) and thumbnail mockups from briefs (Canva).
- **Why**: Closes the loop from analysis to shippable assets. We hand-built the deck.
- **Effort M · Cost subscriptions · Dependency Gamma/Canva MCP (available here).**

---

## Process gaps to close regardless of tooling

- We had no thumbnail analysis at all (items 1, 10). Highest-leverage gap.
- We had no retention data (items 7-9). Cannot explain WHY a video held attention.
- We never measured white-space quantitatively (item 11), only inferred it.
- We never analyzed cross-platform (item 14) despite shipping an Instagram calendar.
- We shipped one title/thumbnail per idea with no A/B test loop (item 16).
- We never correlated cadence/posting-time with performance (item 17).

## Recommended next-run additions (the 30-minute set)

If you only add a handful next time, add items 1, 2, 5, and 15: thumbnail scoring, native outlier
cross-check, live trend signals, and comment question-mining. All are effort-S, low cost, no OAuth,
and they close the four most glaring gaps without expanding the timeline.
