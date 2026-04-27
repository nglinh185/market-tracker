"""
Sponsored ad share tu category_rankings.is_sponsored.
Populate: sponsored_ad_share_daily
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

from lib.db import supabase, upsert
from config import CATEGORIES


def main() -> None:
    today = date.today().isoformat()

    rankings = (
        supabase.table("category_rankings")
        .select("browse_node,asin,brand,is_sponsored")
        .eq("snapshot_date", today)
        .execute()
    ).data

    if not rankings:
        print("[Sponsored] No data today.")
        return

    # Build ASIN → brand fallback map from organic entries (Apify often omits brand on sponsored rows)
    asin_brand: dict[str, str] = {
        r["asin"]: r["brand"]
        for r in rankings
        if r.get("asin") and r.get("brand")
    }

    node_map = {c["id"]: c["name"] for c in CATEGORIES}

    by_node: dict[str, list] = defaultdict(list)
    for r in rankings:
        by_node[r["browse_node"]].append(r)

    rows = []
    for node, items in by_node.items():
        total = len(items)
        keyword = node_map.get(node, node)

        brand_sponsored: dict[str, int] = defaultdict(int)
        brand_organic:   dict[str, int] = defaultdict(int)
        for r in items:
            brand = r.get("brand") or asin_brand.get(r.get("asin")) or "Unknown"
            if r.get("is_sponsored"):
                brand_sponsored[brand] += 1
            else:
                brand_organic[brand] += 1

        all_brands = set(brand_sponsored) | set(brand_organic)
        sponsored_total = sum(brand_sponsored.values())

        for brand in all_brands:
            s_count = brand_sponsored.get(brand, 0)
            o_count = brand_organic.get(brand, 0)
            rows.append({
                "snapshot_date":        today,
                "keyword":              keyword,
                "brand":                brand,
                "sponsored_slot_count": s_count,
                "share_of_voice":       round(s_count / sponsored_total, 4) if sponsored_total else 0,
                "organic_overlap_count": 1 if (s_count > 0 and o_count > 0) else 0,
            })

    n = upsert("sponsored_ad_share_daily", rows, "snapshot_date,keyword,brand")
    print(f"[Sponsored] {n} brand-keyword pairs. "
          f"Sponsored slots today: {sum(r['sponsored_slot_count'] for r in rows)}")


if __name__ == "__main__":
    main()
