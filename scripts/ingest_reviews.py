"""
Weekly review collector cho 30 watchlist ASINs.
Actor: web_wanderer/amazon-reviews-extractor (gFtgG31RZJYlphznm)
  5 pages x 10 reviews = ~50 reviews/ASIN
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from config import WATCHLIST
from lib.apify import run_actor, fetch_dataset
from lib.parsers.review import parse_review, extract_product_summary, _validate_batch
from lib.db import upsert

ACTOR_ID          = "gFtgG31RZJYlphznm"
PAGES_PER_PRODUCT = 2   # 2 pages × ~30 reviews = ~60 reviews/ASIN, tiết kiệm ~60% cost


def _build_run_input(asins: list[str]) -> dict:
    return {
        "products":          asins,
        "pagesPerProduct":   PAGES_PER_PRODUCT,
        "sortBy":            "recent",
        "languageFilter":    "en",
        "verifiedPurchases": True,
        "includeVariants":   False,
        "amazonRegion":      "amazon.com",
        "allStarsMode":      False,
    }


def main() -> None:
    all_asins = [a for asins in WATCHLIST.values() for a in asins]
    print(f"[Reviews] {len(all_asins)} ASINs × ~{PAGES_PER_PRODUCT * 10} reviews ...")

    try:
        dataset_id = run_actor(
            actor_id=ACTOR_ID,
            run_input=_build_run_input(all_asins),
            timeout_min=30,
        )
    except Exception as e:
        print(f"[Reviews] FATAL: {e}")
        sys.exit(1)

    raw_items = fetch_dataset(dataset_id)
    _validate_batch(raw_items)

    # --- reviews_raw ---
    review_rows = []
    for item in raw_items:
        row = parse_review(item)
        if row:
            review_rows.append(row)

    parsed_pct = round(len(review_rows) / len(raw_items) * 100) if raw_items else 0
    print(f"  Parsed {len(review_rows)}/{len(raw_items)} items ({parsed_pct}%)")

    rows_for_db = [{k: v for k, v in r.items() if k != "aspects_json"} for r in review_rows]
    n = upsert("reviews_raw", rows_for_db, "asin,review_id")
    print(f"[Reviews] {n} reviews saved to reviews_raw.")

    # --- aspects (nếu đã chạy migration 003) ---
    aspects_rows = [
        {"asin": r["asin"], "review_id": r["review_id"], "aspects_json": r["aspects_json"]}
        for r in review_rows if r.get("aspects_json")
    ]
    if aspects_rows:
        try:
            upsert("reviews_raw", aspects_rows, "asin,review_id")
        except Exception:
            pass  # skip nếu cột chưa có
        print(f"[Reviews] {len(aspects_rows)} reviews có aspects data.")

    # --- product_review_summary (nếu đã chạy migration 004) ---
    seen_asins: set[str] = set()
    summary_rows = []
    for item in raw_items:
        asin = item.get("productAsin") or item.get("variantAsin")
        if asin and asin not in seen_asins:
            row = extract_product_summary(item)
            if row and row.get("ai_summary"):
                summary_rows.append(row)
                seen_asins.add(asin)

    if summary_rows:
        try:
            n2 = upsert("product_review_summary", summary_rows, "asin")
            print(f"[Reviews] {n2} ASINs saved to product_review_summary.")
        except Exception as e:
            print(f"[Reviews] product_review_summary chưa tạo — bỏ qua ({e})")

    # --- export aspects ra file để kiểm tra ---
    out_path = Path(__file__).parent.parent / "data" / "raw" / "aspects_latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(
        [{"asin": r["asin"], "review_id": r["review_id"], "aspects": r["aspects_json"]}
         for r in review_rows if r.get("aspects_json")],
        indent=2, ensure_ascii=False
    ))
    print(f"[Reviews] Aspects exported → {out_path}")


if __name__ == "__main__":
    main()
