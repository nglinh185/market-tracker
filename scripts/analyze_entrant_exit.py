"""
Detect ASINs entering / exiting Top 50 so voi ngay hom qua.
Populate: entrant_exit_events
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from dotenv import load_dotenv
load_dotenv()

from lib.db import supabase, upsert


def main() -> None:
    today     = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    today_rows = (
        supabase.table("category_rankings")
        .select("asin,browse_node,rank")
        .eq("snapshot_date", today)
        .execute()
    ).data

    yesterday_rows = (
        supabase.table("category_rankings")
        .select("asin,browse_node,rank")
        .eq("snapshot_date", yesterday)
        .execute()
    ).data

    if not today_rows or not yesterday_rows:
        print("[EntrantExit] Chua du 2 ngay data.")
        return

    today_map     = {(r["browse_node"], r["asin"]): r["rank"] for r in today_rows}
    yesterday_map = {(r["browse_node"], r["asin"]): r["rank"] for r in yesterday_rows}

    events = []
    for key, rank_today in today_map.items():
        if key not in yesterday_map:
            events.append({
                "snapshot_date": today,
                "browse_node":   key[0],
                "asin":          key[1],
                "event_type":    "entrant",
                "rank_today":    rank_today,
                "rank_yesterday": None,
                "is_top10":      rank_today <= 10,
            })

    for key, rank_yesterday in yesterday_map.items():
        if key not in today_map:
            events.append({
                "snapshot_date":  today,
                "browse_node":    key[0],
                "asin":           key[1],
                "event_type":     "exit",
                "rank_today":     None,
                "rank_yesterday": rank_yesterday,
                "is_top10":       rank_yesterday <= 10,
            })

    n = upsert("entrant_exit_events", events, "snapshot_date,browse_node,asin,event_type")
    print(f"[EntrantExit] {n} events: "
          f"{sum(1 for e in events if e['event_type']=='entrant')} entrants, "
          f"{sum(1 for e in events if e['event_type']=='exit')} exits.")


if __name__ == "__main__":
    main()
