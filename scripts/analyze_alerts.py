"""
Rule-based alert engine.
Populate: alerts table.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from dotenv import load_dotenv
load_dotenv()

from lib.db import supabase


PRICE_DROP_THRESHOLD = 15   # % drop in 1 day
BSR_SPIKE_THRESHOLD  = 500  # BSR got worse by this much
STOCKOUT_AFTER_DAYS  = 1    # flag if out of stock


def _insert_alerts(alerts: list[dict]) -> None:
    if not alerts:
        return
    supabase.table("alerts").insert(alerts).execute()


def main() -> None:
    today     = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    today_snaps = {
        r["asin"]: r for r in (
            supabase.table("daily_snapshots")
            .select("asin,price,bsr,in_stock,image_changed")
            .eq("snapshot_date", today)
            .execute()
        ).data
    }
    yesterday_snaps = {
        r["asin"]: r for r in (
            supabase.table("daily_snapshots")
            .select("asin,price,bsr,in_stock")
            .eq("snapshot_date", yesterday)
            .execute()
        ).data
    }
    entrants = (
        supabase.table("entrant_exit_events")
        .select("asin,browse_node,event_type,rank_today,is_top10")
        .eq("snapshot_date", today)
        .execute()
    ).data

    alerts = []

    for asin, t in today_snaps.items():
        y = yesterday_snaps.get(asin, {})

        # Price drop alert
        p_t = t.get("price")
        p_y = y.get("price")
        if p_t and p_y and p_y > 0:
            drop_pct = (p_y - p_t) / p_y * 100
            if drop_pct >= PRICE_DROP_THRESHOLD:
                alerts.append({
                    "snapshot_date": today, "asin": asin,
                    "alert_type": "price_drop",
                    "severity": "high" if drop_pct >= 30 else "medium",
                    "message": f"Price dropped {drop_pct:.1f}%: ${p_y} -> ${p_t}",
                    "metadata_json": {"price_before": p_y, "price_after": p_t, "drop_pct": round(drop_pct,1)},
                })

        # Stockout alert
        if not t.get("in_stock") and y.get("in_stock"):
            alerts.append({
                "snapshot_date": today, "asin": asin,
                "alert_type": "stockout",
                "severity": "high",
                "message": f"ASIN went out of stock (was in stock yesterday)",
                "metadata_json": {},
            })

        # BSR spike (rank dropped = higher number)
        bsr_t = t.get("bsr")
        bsr_y = y.get("bsr")
        if bsr_t and bsr_y and (bsr_t - bsr_y) > BSR_SPIKE_THRESHOLD:
            alerts.append({
                "snapshot_date": today, "asin": asin,
                "alert_type": "bsr_drop",
                "severity": "medium",
                "message": f"BSR worsened: #{bsr_y} -> #{bsr_t}",
                "metadata_json": {"bsr_before": bsr_y, "bsr_after": bsr_t},
            })

        # Image change
        if t.get("image_changed"):
            alerts.append({
                "snapshot_date": today, "asin": asin,
                "alert_type": "image_change",
                "severity": "low",
                "message": "Main product image changed",
                "metadata_json": {},
            })

    # Entrant/exit alerts
    for e in entrants:
        if e["event_type"] == "entrant":
            alerts.append({
                "snapshot_date": today,
                "asin": e["asin"], "browse_node": e["browse_node"],
                "alert_type": "new_entrant",
                "severity": "high" if e["is_top10"] else "low",
                "message": f"New entrant at rank #{e['rank_today']}",
                "metadata_json": {"rank": e["rank_today"]},
            })
        else:
            alerts.append({
                "snapshot_date": today,
                "asin": e["asin"], "browse_node": e["browse_node"],
                "alert_type": "exit",
                "severity": "medium",
                "message": f"ASIN exited Top 50 (was rank #{e['rank_today']})",
                "metadata_json": {},
            })

    _insert_alerts(alerts)
    print(f"[Alerts] {len(alerts)} alerts generated.")
    for a in alerts:
        print(f"  [{a['severity'].upper()}] {a['asin']} - {a['alert_type']}: {a['message']}")


if __name__ == "__main__":
    main()
