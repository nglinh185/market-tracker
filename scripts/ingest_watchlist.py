"""
Daily watchlist scraper — lấy product detail cho active ASINs.
Output: daily_snapshots table + ảnh lên Supabase Storage.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import imagehash
from datetime import date, timedelta
from dotenv import load_dotenv
load_dotenv()

from config import ACTOR_CATEGORY, WATCHLIST, require_env
from lib.apify import run_actor, fetch_dataset
from lib.parsers.product import parse_item
from lib.parsers.brand_extract import resolve_brand
from lib.image_store import download_hash_store, get_yesterday_hash, is_image_changed, ensure_bucket
from lib.db import supabase, upsert

require_env(["APIFY_TOKEN", "SUPABASE_URL", "SUPABASE_KEY"])

CACHE_DIR = Path(__file__).parent.parent / "data" / "raw"


def _get_watchlist_asins() -> list[str]:
    # Lấy thẳng từ config — tránh lấy nhầm toàn bộ asins table
    return [asin for asins in WATCHLIST.values() for asin in asins]


def main() -> None:
    today     = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    ensure_bucket()

    asins = _get_watchlist_asins()
    watchlist_set = set(asins)
    if not asins:
        print("[Watchlist] WATCHLIST trong config.py dang trong. Them ASINs vao truoc.")
        return

    print(f"[Watchlist] Thu thap {len(asins)} ASINs cho {today} ...")

    # Check cache trước — tránh re-scrape nếu chỉ fail ở bước upsert
    cache_file = CACHE_DIR / f"watchlist_{today}.json"
    if cache_file.exists():
        print(f"  [Cache] Dung du lieu cache tu {cache_file}")
        all_raw_items = json.loads(cache_file.read_text())
    else:
        BATCH = 10
        all_raw_items = []
        n_batches = -(-len(asins) // BATCH)

        for i in range(0, len(asins), BATCH):
            batch = asins[i:i + BATCH]
            print(f"  Batch {i//BATCH + 1}/{n_batches}: {batch}")
            urls = [{"url": f"https://www.amazon.com/dp/{a}"} for a in batch]
            try:
                dataset_id = run_actor(
                    actor_id=ACTOR_CATEGORY,
                    run_input={
                        "categoryOrProductUrls": urls,
                        "maxItemsPerStartUrl":   1,
                        "scrapeProductDetails":  True,
                        "maxOffers":             0,
                        "proxyCountry":          "AUTO_SELECT_PROXY_COUNTRY",
                    },
                )
                all_raw_items.extend(fetch_dataset(dataset_id))
            except Exception as e:
                print(f"  [ERROR] Batch {i//BATCH + 1} failed: {e}")

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(all_raw_items))
        print(f"  [Cache] Da luu {len(all_raw_items)} items -> {cache_file}")

    items = all_raw_items
    rows  = []
    asin_brand_updates = []

    for item in items:
        if not item.get("asin"):
            continue

        row  = parse_item(item, today)
        asin = row["asin"]

        # Refresh brand on `asins` table — Apify product detail may include
        # `brand`; otherwise fall back to product_name pattern match.
        brand = resolve_brand(item.get("brand"), item.get("title"))
        if brand:
            asin_brand_updates.append({"asin": asin, "brand": brand,
                                       "product_name": item.get("title")})

        # _main_image_url là internal field từ parser, lấy ra rồi xoá
        image_url = row.pop("_main_image_url", None)
        if image_url:
            phash_val, storage_url = download_hash_store(asin, image_url, today)
            prev_hash              = get_yesterday_hash(asin, yesterday)
            changed                = is_image_changed(phash_val, prev_hash)

            row["image_url"]     = storage_url or image_url
            row["image_hash"]    = phash_val
            row["image_changed"] = changed
        else:
            row["image_url"]     = None
            row["image_hash"]    = None
            row["image_changed"] = False

        rows.append(row)

        flag = " *** IMAGE CHANGED" if row["image_changed"] else ""
        print(f"  {asin} | BSR={row.get('bsr')} | ${row.get('price')} | stock={row.get('in_stock')}{flag}")

    # Filter out wrong ASINs (s?k= search can return a different ASIN than queried)
    rows = [r for r in rows if r["asin"] in watchlist_set]

    n = upsert("daily_snapshots", rows, "asin,snapshot_date")
    print(f"\n[Watchlist] Done. {n} rows upserted.")

    # Update asins.brand (and product_name when missing) for the watchlist
    if asin_brand_updates:
        kept = [u for u in asin_brand_updates if u["asin"] in watchlist_set]
        for u in kept:
            payload = {"brand": u["brand"]}
            if u.get("product_name"):
                payload["product_name"] = u["product_name"]
            supabase.table("asins").update(payload).eq("asin", u["asin"]).execute()
        print(f"[Watchlist] Refreshed brand on {len(kept)} ASINs in asins table.")


if __name__ == "__main__":
    main()
