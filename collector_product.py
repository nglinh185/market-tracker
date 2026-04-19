"""
Ngay 2 - Thu thap chi tiet san pham cho target ASINs
Dung cung actor voi collector_category, chi khac URL input (/dp/ASIN)
Output: daily_snapshots (bsr, price, stock, buy_box, image_hash...)
"""
import os
import requests
import imagehash
from PIL import Image
from io import BytesIO
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv
from apify_client import ApifyClient
from db import supabase

load_dotenv()

ACTOR_ID        = os.getenv("ACTOR_ID")
IMAGE_DIR       = Path("data/images")
PHASH_THRESHOLD = 10


def get_target_asins():
    result = supabase.table("asins").select("asin").eq("is_active", True).execute()
    return [row["asin"] for row in result.data]


def download_and_hash(url: str, save_path: Path):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(save_path)
        return str(imagehash.phash(img))
    except Exception as e:
        print(f"  [Image] Loi: {e}")
        return None


def get_yesterday_hash(asin: str):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    result = (
        supabase.table("daily_snapshots")
        .select("image_hash")
        .eq("asin", asin)
        .eq("snapshot_date", yesterday)
        .execute()
    )
    return result.data[0]["image_hash"] if result.data else None


def parse_price(val):
    if val is None:
        return None
    if isinstance(val, dict):
        return round(float(val.get("value", 0)), 2)
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    try:
        return round(float(str(val).replace("$", "").replace(",", "").strip()), 2)
    except ValueError:
        return None


def parse_bsr(item: dict):
    """Thu tu cac ten field BSR ma actor co the tra ve."""
    for field in ["bestSellerRank", "bsr", "salesRank", "bestSellersRank"]:
        val = item.get(field)
        if val is None:
            continue
        if isinstance(val, int):
            return val
        if isinstance(val, list) and val:
            first = val[0]
            rank = first.get("rank") or first.get("position") if isinstance(first, dict) else first
            try:
                return int(str(rank).replace(",", "").replace("#", "").strip())
            except (ValueError, TypeError):
                continue
        try:
            return int(str(val).replace(",", "").replace("#", "").strip())
        except (ValueError, TypeError):
            continue
    return None


def parse_stock(item: dict):
    for field in ["availability", "inStock", "isAvailable"]:
        val = item.get(field)
        if val is None:
            continue
        if isinstance(val, bool):
            return val
        return "in stock" in str(val).lower()
    return True  # default neu khong co field


def run():
    client = ApifyClient(os.getenv("APIFY_TOKEN"))
    today  = date.today().isoformat()

    target_asins = get_target_asins()
    if not target_asins:
        print("[Product] Bang asins trong. Chay collector_category.py truoc.")
        return

    print(f"[Product] Thu thap chi tiet {len(target_asins)} ASINs cho ngay {today} ...")

    # Chuyen ASIN -> product URL dang /dp/
    product_urls = [{"url": f"https://www.amazon.com/dp/{asin}"} for asin in target_asins]

    actor_run = client.actor(ACTOR_ID).call(run_input={
        "categoryOrProductUrls": product_urls,
        "maxItemsPerStartUrl":   1,
        "scrapeProductDetails":  True,
        "maxOffers":             0,
        "proxyCountry":          "AUTO_SELECT_PROXY_COUNTRY",
    })

    items = list(client.dataset(actor_run["defaultDatasetId"]).iterate_items())
    print(f"[Product] Nhan duoc {len(items)} ket qua")

    # In field names cua item dau tien de debug (xoa sau khi xac nhan OK)
    if items:
        print(f"  [DEBUG] Fields co san: {list(items[0].keys())}")

    rows = []
    for item in items:
        asin = item.get("asin")
        if not asin:
            continue

        # Image + pHash
        image_url     = item.get("mainImage") or item.get("thumbnailImage")
        image_hash    = None
        image_changed = False
        if image_url:
            save_path  = IMAGE_DIR / asin / f"{today}.jpg"
            image_hash = download_and_hash(image_url, save_path)
            prev_hash  = get_yesterday_hash(asin)
            if prev_hash and image_hash:
                distance      = imagehash.hex_to_hash(image_hash) - imagehash.hex_to_hash(prev_hash)
                image_changed = distance > PHASH_THRESHOLD

        # Promo
        promos    = item.get("promotions") or item.get("badges") or item.get("deals") or []
        has_promo = len(promos) > 0

        rows.append({
            "asin":           asin,
            "snapshot_date":  today,
            "bsr":            parse_bsr(item),
            "price":          parse_price(item.get("price") or item.get("finalPrice")),
            "buy_box_winner": item.get("seller") or item.get("buyBoxSeller") or item.get("buyBox"),
            "in_stock":       parse_stock(item),
            "has_promo":      has_promo,
            "stars":          item.get("stars"),
            "reviews_count":  item.get("reviewsCount"),
            "image_url":      image_url,
            "image_hash":     image_hash,
            "image_changed":  image_changed,
        })

    if rows:
        supabase.table("daily_snapshots").upsert(
            rows, on_conflict="asin,snapshot_date"
        ).execute()
        print(f"[Product] Inserted {len(rows)} rows")
        for r in rows:
            flag = " *** IMAGE CHANGED" if r["image_changed"] else ""
            print(f"  {r['asin']} | BSR={r['bsr']} | ${r['price']} | stock={r['in_stock']}{flag}")


if __name__ == "__main__":
    run()
