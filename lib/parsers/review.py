import html


def _clean(text: str | None) -> str | None:
    """Decode HTML entities — &#39; → ', &amp; → &, etc."""
    if not text:
        return text
    return html.unescape(text)


def parse_review(item: dict) -> dict | None:
    """
    Parse 1 item từ web_wanderer/amazon-reviews-extractor output.

    Field mapping (web_wanderer → DB):
      reviewId          → review_id
      productAsin       → asin
      reviewDate        → review_date  ("YYYY-MM-DD", pre-parsed)
      rating            → rating       (int 1-5)
      reviewTitle       → title
      reviewText        → review_text  (input cho RoBERTa — HTML decoded)
      verifiedPurchase  → verified
      vineReview        → is_vine      (bias flag cho ML)
      helpfulVoteCount  → helpful_votes (weight signal)
      images (list)     → has_images   (quality signal)
      country           → country
      aspects           → aspects_json (aspect-level sentiment từ Amazon AI)
    """
    review_id = item.get("reviewId")
    asin      = item.get("productAsin") or item.get("variantAsin")

    if not review_id or not asin:
        return None

    review_text = _clean(item.get("reviewText") or "")
    if not review_text.strip():
        return None

    # Chỉ lấy English — RoBERTa model
    if item.get("language") and item["language"] != "en":
        return None

    aspects_raw  = item.get("aspects")
    aspects_json = None
    if isinstance(aspects_raw, list) and aspects_raw:
        aspects_json = [
            {
                "name":      a.get("aspectName"),
                "sentiment": a.get("aspectSentiment"),  # "positive" | "negative" | "mixed"
                "mentions":  int(a.get("aspectMention") or 0),
                "positive":  int(a.get("aspectMentionPositive") or 0),
                "negative":  int(a.get("aspectMentionNegative") or 0),
                "summary":   _clean(a.get("aspectSummary")),
            }
            for a in aspects_raw
            if a.get("aspectName")
        ]

    images = item.get("images")

    return {
        "asin":          asin,
        "review_id":     review_id,
        "review_date":   item.get("reviewDate"),
        "rating":        item.get("rating"),
        "title":         _clean(item.get("reviewTitle")),
        "review_text":   review_text,
        "verified":      bool(item.get("verifiedPurchase", False)),
        "is_vine":       bool(item.get("vineReview", False)),
        "helpful_votes": item.get("helpfulVoteCount") or 0,
        "has_images":    bool(images) if isinstance(images, list) else False,
        "country":       item.get("country"),
        "aspects_json":  aspects_json,
    }


def extract_product_summary(item: dict) -> dict | None:
    """
    Tách product-level fields (giống nhau cho mọi review cùng ASIN).
    Dùng để lưu vào product_review_summary.
    """
    asin = item.get("productAsin") or item.get("variantAsin")
    if not asin:
        return None

    rating_summary = item.get("ratingSummary") or {}

    return {
        "asin":            asin,
        "ai_summary":      _clean(item.get("reviewsAISummary")),
        "average_rating":  item.get("averageRating"),
        "total_ratings":   item.get("totalRatings"),
        "pct_five_stars":  rating_summary.get("five_stars"),
        "pct_four_stars":  rating_summary.get("four_stars"),
        "pct_three_stars": rating_summary.get("three_stars"),
        "pct_two_stars":   rating_summary.get("two_stars"),
        "pct_one_star":    rating_summary.get("one_star"),
    }


def _validate_batch(items: list[dict]) -> None:
    """Log rõ field nào bị thiếu — tránh fail silently trước RoBERTa."""
    missing_text = sum(1 for i in items if not i.get("reviewText"))
    missing_asin = sum(1 for i in items if not i.get("productAsin"))
    missing_id   = sum(1 for i in items if not i.get("reviewId"))
    non_english  = sum(1 for i in items if i.get("language") and i["language"] != "en")
    has_aspects  = sum(1 for i in items if i.get("aspects"))

    print(f"  [Validate] {len(items)} raw items | "
          f"missing reviewText={missing_text} | "
          f"missing asin={missing_asin} | "
          f"missing reviewId={missing_id} | "
          f"non-english={non_english} (skipped) | "
          f"has aspects={has_aspects}")
