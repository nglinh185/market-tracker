"""
Detect image + content changes so sanh voi ngay hom qua.
Populate: image_change_events, content_change_events
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from dotenv import load_dotenv
load_dotenv()

import imagehash
from lib.db import supabase, upsert
from config import PHASH_THRESHOLD


def main() -> None:
    today     = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    today_snaps = {
        r["asin"]: r for r in (
            supabase.table("daily_snapshots")
            .select("asin,image_hash,ebc_html_hash,bullet_count,description")
            .eq("snapshot_date", today)
            .execute()
        ).data
    }
    yesterday_snaps = {
        r["asin"]: r for r in (
            supabase.table("daily_snapshots")
            .select("asin,image_hash,ebc_html_hash,bullet_count,description")
            .eq("snapshot_date", yesterday)
            .execute()
        ).data
    }

    image_events   = []
    content_events = []

    for asin, t in today_snaps.items():
        y = yesterday_snaps.get(asin, {})

        # Image change
        h_today = t.get("image_hash")
        h_yest  = y.get("image_hash")
        if h_today and h_yest:
            dist = imagehash.hex_to_hash(h_today) - imagehash.hex_to_hash(h_yest)
            if dist > PHASH_THRESHOLD:
                image_events.append({
                    "snapshot_date": today,
                    "asin":          asin,
                    "hash_before":   h_yest,
                    "hash_after":    h_today,
                    "hash_distance": dist,
                    "change_flag":   True,
                })

        # A+ content change
        aplus_t = t.get("ebc_html_hash")
        aplus_y = y.get("ebc_html_hash")
        if aplus_t and aplus_y and aplus_t != aplus_y:
            content_events.append({
                "snapshot_date": today,
                "asin":          asin,
                "change_area":   "aplus",
                "change_level":  "major",
                "diff_summary":  f"{aplus_y[:8]} -> {aplus_t[:8]}",
            })

        # Bullet count change
        bc_t = t.get("bullet_count") or 0
        bc_y = y.get("bullet_count") or 0
        if bc_t != bc_y:
            content_events.append({
                "snapshot_date": today,
                "asin":          asin,
                "change_area":   "bullets",
                "change_level":  "major" if abs(bc_t - bc_y) >= 2 else "minor",
                "diff_summary":  f"{bc_y} -> {bc_t} bullets",
            })

    n1 = upsert("image_change_events", image_events, "snapshot_date,asin")
    n2 = len(content_events)
    if content_events:
        supabase.table("content_change_events").insert(content_events).execute()

    print(f"[Changes] {n1} image changes, {n2} content changes detected.")


if __name__ == "__main__":
    main()
