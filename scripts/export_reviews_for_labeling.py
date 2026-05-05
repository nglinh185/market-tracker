"""
Export a stratified sample of 200 reviews for manual sentiment labeling.

Sampling protocol:
  - 40 reviews per star bucket (1, 2, 3, 4, 5) = 200 total
  - Random shuffle (seeded) within each star bucket
  - Only reviews with non-empty review_text are eligible

Output: data/eval/reviews_to_label.csv
Columns:
  review_id, asin, rating, review_text_short (first 400 chars),
  roberta_label, roberta_score, manual_label (EMPTY — fill manually)

After manual labeling, run:
  python scripts/evaluate_sentiment_manual.py
"""
from __future__ import annotations
import csv
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from lib.db import supabase

OUT_FILE = Path(__file__).parent.parent / "data" / "eval" / "reviews_to_label.csv"
PER_STAR  = 40
SEED      = 42
TEXT_CAP  = 400  # chars per review (truncated for spreadsheet readability)


def main() -> None:
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    random.seed(SEED)

    # Pull all reviews with text + rating + roberta sentiment for context
    print("[Export] Fetching reviews from Supabase...")
    page_size = 1000
    offset = 0
    all_rows: list[dict] = []
    while True:
        chunk = (supabase.table("reviews_raw")
                 .select("review_id,asin,rating,review_text,sentiment_label,sentiment_score")
                 .not_.is_("review_text", "null")
                 .not_.is_("rating", "null")
                 .range(offset, offset + page_size - 1)
                 .execute()).data or []
        if not chunk:
            break
        all_rows.extend(chunk)
        if len(chunk) < page_size:
            break
        offset += page_size
    print(f"[Export] Got {len(all_rows)} reviews with text+rating.")

    # De-duplicate on review_id (some rows may repeat across asins in dataset)
    seen: set[str] = set()
    unique: list[dict] = []
    for r in all_rows:
        rid = r.get("review_id") or ""
        if rid and rid not in seen and (r.get("review_text") or "").strip():
            seen.add(rid)
            unique.append(r)
    print(f"[Export] {len(unique)} unique reviews with non-empty text.")

    # Bucket by star
    buckets: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: [], 5: []}
    for r in unique:
        s = int(r.get("rating") or 0)
        if s in buckets:
            buckets[s].append(r)

    print("[Export] Bucket sizes:")
    for s in sorted(buckets):
        print(f"  {s}-star: {len(buckets[s])} eligible reviews")

    # Stratified sample
    sampled: list[dict] = []
    for s in sorted(buckets):
        pool = buckets[s]
        random.shuffle(pool)
        take = pool[:PER_STAR]
        if len(take) < PER_STAR:
            print(f"  [WARN] Only {len(take)} reviews available for {s}-star (need {PER_STAR}).")
        sampled.extend(take)

    # Write CSV
    with OUT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow([
            "review_id", "asin", "rating", "review_text_short",
            "roberta_label", "roberta_score", "manual_label"
        ])
        for r in sampled:
            text = (r.get("review_text") or "").replace("\n", " ").replace("\r", " ")
            if len(text) > TEXT_CAP:
                text = text[:TEXT_CAP] + "..."
            writer.writerow([
                r.get("review_id", ""),
                r.get("asin", ""),
                r.get("rating", ""),
                text,
                r.get("sentiment_label", ""),
                r.get("sentiment_score", ""),
                "",  # manual_label — fill in: positive | neutral | negative
            ])

    print(f"\n[Export] Wrote {len(sampled)} reviews -> {OUT_FILE}")
    print("[Export] Open the CSV and fill the 'manual_label' column with:")
    print("         positive | neutral | negative")
    print("         Save it back to the same path, then run evaluate_sentiment_manual.py.")


if __name__ == "__main__":
    main()
