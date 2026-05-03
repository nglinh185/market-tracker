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

from config import WATCHLIST, ACTOR_REVIEWS, require_env
from lib.apify import run_actor, fetch_dataset
from lib.parsers.review import parse_review, extract_product_summary, _validate_batch
from lib.db import upsert

PAGES_PER_PRODUCT = 5   # actor requires ≥5 pages; 2 pages returns 0 items


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
    require_env(["APIFY_TOKEN", "SUPABASE_URL", "SUPABASE_KEY"])
    all_asins = [a for asins in WATCHLIST.values() for a in asins]
    print(f"[Reviews] {len(all_asins)} ASINs × ~{PAGES_PER_PRODUCT * 10} reviews (actor={ACTOR_REVIEWS}) ...")

    try:
        dataset_id = run_actor(
            actor_id=ACTOR_REVIEWS,
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

    # Thu upsert full row (gom ca aspects_json). Neu cot aspects_json chua ton tai
    # (migration 003 chua chay) -> strip ra va upsert lai.
    try:
        n = upsert("reviews_raw", review_rows, "asin,review_id")
    except Exception:
        rows_no_aspects = [{k: v for k, v in r.items() if k != "aspects_json"} for r in review_rows]
        n = upsert("reviews_raw", rows_no_aspects, "asin,review_id")
        print("[Reviews] aspects_json column missing — da upsert khong kem aspects.")
    print(f"[Reviews] {n} reviews saved to reviews_raw.")

    n_aspects = sum(1 for r in review_rows if r.get("aspects_json"))
    if n_aspects:
        print(f"[Reviews] {n_aspects} reviews co aspects data.")

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
