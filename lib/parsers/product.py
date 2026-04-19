import hashlib


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


def _parse_bsr(item: dict) -> int | None:
    ranks = item.get("bestsellerRanks")
    if not ranks or not isinstance(ranks, list):
        return None

    # Ưu tiên subcategory rank (specific hơn)
    for r in ranks:
        if isinstance(r, dict):
            category = r.get("category", "").lower()
            # Bỏ qua top-level "Amazon" rank, lấy subcategory
            if "amazon" not in category:
                try:
                    return int(str(r["rank"]).replace(",", "").strip())
                except (ValueError, TypeError, KeyError):
                    pass

    # Fallback: rank đầu tiên
    first = ranks[0]
    if isinstance(first, dict):
        try:
            return int(str(first.get("rank", "")).replace(",", "").strip())
        except (ValueError, TypeError):
            pass
    return None


def _parse_stock(item: dict) -> bool:
    for field in ["availability", "inStock", "isAvailable"]:
        val = item.get(field)
        if val is None:
            continue
        if isinstance(val, bool):
            return val
        return "in stock" in str(val).lower()
    return True


def parse_item(item: dict, snapshot_date: str) -> dict:
    """
    Parse 1 item từ Apify product detail output → daily_snapshots row.
    Field names thực tế từ junglee/Amazon-crawler (verified):
      inStock(bool), seller(dict), bestsellerRanks(list), features(list),
      videosCount, highResolutionImages(list), thumbnailImage, aPlusContent(dict)
    """
    features     = item.get("features") or []
    bullet_count = len(features) if isinstance(features, list) else 0

    # seller là dict {"name":..., "id":..., "url":...}
    seller_raw   = item.get("seller") or {}
    buy_box      = seller_raw.get("name") if isinstance(seller_raw, dict) else str(seller_raw)

    # A+ content text để content change detection
    aplus        = item.get("aPlusContent") or {}
    aplus_text   = aplus.get("rawText") if isinstance(aplus, dict) else None

    # Main image: ưu tiên highResolution để pHash chính xác hơn
    hi_res       = item.get("highResolutionImages") or []
    main_image   = hi_res[0] if hi_res else item.get("thumbnailImage")

    # Promo/badge
    cat_data     = item.get("categoryPageData") or {}
    sale_summary = cat_data.get("saleSummary") if isinstance(cat_data, dict) else None
    has_promo    = bool(sale_summary and sale_summary.lower() not in ("", "none"))

    price_val     = _parse_price(item.get("price"))
    list_price    = _parse_price(item.get("listPrice"))
    discount_pct  = None
    if price_val and list_price and list_price > price_val:
        discount_pct = round((list_price - price_val) / list_price * 100, 1)

    stars_bd = item.get("starsBreakdown")

    return {
        "asin":            item.get("asin"),
        "snapshot_date":   snapshot_date,
        "bsr":             _parse_bsr(item),
        "price":           price_val,
        "list_price":      list_price,
        "discount_pct":    discount_pct,
        "buy_box_winner":  buy_box,
        "in_stock":        _parse_stock(item),
        "has_promo":       has_promo,
        "stars":           item.get("stars"),
        "stars_breakdown": stars_bd if isinstance(stars_bd, dict) else None,
        "reviews_count":   item.get("reviewsCount"),
        "bullet_count":    bullet_count,
        "description":     item.get("description"),
        "ebc_html_hash":   hashlib.md5(aplus_text.encode()).hexdigest() if aplus_text else None,
        "_main_image_url": main_image,
    }
