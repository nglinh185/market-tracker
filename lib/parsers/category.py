def _parse_price(val) -> float | None:
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


def parse_item(
    item: dict,
    category_id: str,
    snapshot_date: str,
    rank: int | None = None,
) -> tuple[dict, dict]:
    """
    Parse 1 item từ Apify category output.
    Returns: (ranking_row, asin_row)
    Actual field names từ junglee/Amazon-crawler:
      imageUrl, isSponsored, position, reviewsCount, stars, price{value,currency}
    """
    asin = item.get("asin")

    # Dùng position từ actor nếu có, fallback về rank argument
    effective_rank = item.get("position") or rank

    ranking_row = {
        "snapshot_date": snapshot_date,
        "browse_node":   category_id,
        "rank":          effective_rank,
        "asin":          asin,
        "title":         item.get("title"),
        "brand":         item.get("brand"),          # None nếu actor không trả về
        "price":         _parse_price(item.get("price")),
        "stars":         item.get("stars"),
        "reviews_count": item.get("reviewsCount"),
        "is_sponsored":  bool(item.get("isSponsored", False)),
        "thumbnail_url": item.get("imageUrl") or item.get("thumbnailImage"),
    }

    asin_row = {
        "asin":         asin,
        "product_name": item.get("title"),
        "brand":        item.get("brand"),
        "category":     category_id,
    }

    return ranking_row, asin_row
