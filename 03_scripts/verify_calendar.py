"""Quick check: print sample slotted ideas so we can eyeball draft quality before finalizing."""
import sys
from pathlib import Path
P = Path(__file__).resolve().parent
sys.path.insert(0, str(P))
import build_calendar as b

ideas = b.load_ideas()
a, e, log = b.slot(ideas)
for wn in (0, 1, 6, 9, 10, 12):
    wk = b.WEEK_SCHEDULE[wn]
    print(f"\n=== WEEK {wn}: {wk['theme']} ===")
    for i in a[wn]:
        print(f"  [{i['format']:5}] {i['title_idea'][:62]}")
        vol = i['kw_volume'] if i['kw_volume'] is not None else '-'
        print(f"          kw: {i['primary_keyword']} ({vol}/mo) | src: {i['source_channel']} {i['source_views']:,} views | {i['source_title'][:42]}")
