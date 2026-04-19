"""
Ngay 2 - Thu thap Top 50 Amazon Bestsellers
Actor: BG3WDrGdteHgZgbPK (amazon bestsellers scraper)
Output: category_rankings + upsert asins
"""
import os
from datetime import date
from dotenv import load_dotenv
from apify_client import ApifyClient
from db import supabase

load_dotenv()

ACTOR_ID     = os.getenv("ACTOR_ID")
CATEGORY_URL = os.getenv("CATEGORY_URL")
BROWSE_NODE  = os.getenv("BROWSE_NODE", "unknown")


def parse_price(val):
    if val is None:
        return None
    if isinstance(val, dict):               # {"value": 15.99, "currency": "$"}
        return round(float(val["value"]), 2)
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    cleaned = str(val).replace("$", "").replace(",", "").strip()
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def run():
    client = ApifyClient(os.getenv("APIFY_TOKEN"))
    today  = date.today().isoformat()

    print(f"[Category] Chay actor cho ngay {today} ...")

    actor_run = client.actor(ACTOR_ID).call(run_input={
        "categoryOrProductUrls":    [{"url": CATEGORY_URL}],
        "maxItemsPerStartUrl":      100,
        "scrapeProductDetails":     True,
        "maxOffers":                0,
        "proxyCountry":             "AUTO_SELECT_PROXY_COUNTRY",
    })

    items = list(client.dataset(actor_run["defaultDatasetId"]).iterate_items())
    print(f"[Category] Nhan duoc {len(items)} san pham")

    ranking_rows = []
    asin_rows    = []

    for idx, item in enumerate(items):
        asin = item.get("asin")
        if not asin:
            continue

        ranking_rows.append({
            "snapshot_date": today,
            "browse_node":   BROWSE_NODE,
            "rank":          idx + 1,
            "asin":          asin,
            "title":         item.get("title"),
            "brand":         item.get("brand"),
            "price":         parse_price(item.get("price")),
            "stars":         item.get("stars"),
            "reviews_count": item.get("reviewsCount"),
            "thumbnail_url": item.get("thumbnailImage"),
        })

        # breadCrumbs la string "A > B > C > D", lay phan cuoi lam category
        breadcrumbs_str = item.get("breadCrumbs") or ""
        category = breadcrumbs_str.split(" > ")[-1] if breadcrumbs_str else None

        asin_rows.append({
            "asin":         asin,
            "product_name": item.get("title"),
            "brand":        item.get("brand"),
            "category":     category,
        })

    # Upsert asins truoc (category_rankings co the reference)
    if asin_rows:
        supabase.table("asins").upsert(asin_rows, on_conflict="asin").execute()
        print(f"[Category] Upserted {len(asin_rows)} ASINs")

    # Upsert category rankings
    if ranking_rows:
        supabase.table("category_rankings").upsert(
            ranking_rows,
            on_conflict="snapshot_date,browse_node,rank"
        ).execute()
        print(f"[Category] Inserted {len(ranking_rows)} rows vao category_rankings")


if __name__ == "__main__":
    run()
