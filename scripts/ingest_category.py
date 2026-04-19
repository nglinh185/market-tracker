"""
Daily category scraper — chạy cho 3 categories tuần tự.
Output: category_rankings + asins tables.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from dotenv import load_dotenv
load_dotenv()

from config import CATEGORIES, ACTOR_CATEGORY
from lib.apify import run_actor, fetch_dataset
from lib.parsers.category import parse_item
from lib.db import upsert


def _run_for_category(cat: dict, today: str) -> None:
    print(f"\n[Category] {cat['name']} ...")

    dataset_id = run_actor(
        actor_id=ACTOR_CATEGORY,
        run_input={
            "categoryOrProductUrls": [{"url": cat["search_url"]}],
            "maxItemsPerStartUrl":   cat["top_n"],
            "scrapeProductDetails":  False,   # search result data đủ cho category ranking
            "maxOffers":             0,
            "proxyCountry":          "AUTO_SELECT_PROXY_COUNTRY",
        },
    )

    items = fetch_dataset(dataset_id)

    ranking_map, asin_map = {}, {}
    for rank, item in enumerate(items, start=1):
        if not item.get("asin"):
            continue
        ranking_row, asin_row = parse_item(item, cat["id"], today, rank)

        # Dedupe by rank: Apify có thể trả item trùng position, giữ row đầu tiên
        rank_key = (ranking_row["snapshot_date"], ranking_row["browse_node"], ranking_row["rank"])
        if rank_key not in ranking_map:
            ranking_map[rank_key] = ranking_row

        asin_map[asin_row["asin"]] = asin_row   # dedup ASIN

    ranking_rows = list(ranking_map.values())
    upsert("asins", list(asin_map.values()), "asin")
    n = upsert("category_rankings", ranking_rows, "snapshot_date,browse_node,rank")
    print(f"  → {n} ranking rows | {len(asin_map)} ASINs upserted")


def main() -> None:
    today = date.today().isoformat()
    print(f"[Category] Starting for {today}")

    for cat in CATEGORIES:
        try:
            _run_for_category(cat, today)
        except Exception as e:
            # Lỗi 1 category không dừng các category còn lại
            print(f"  [ERROR] {cat['name']}: {e}")

    print("\n[Category] Done.")


if __name__ == "__main__":
    main()
