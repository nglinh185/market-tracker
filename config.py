import os

# Actor IDs — override trong .env neu can
ACTOR_CATEGORY = os.getenv("ACTOR_CATEGORY", "BG3WDrGdteHgZgbPK")   # junglee/Amazon-crawler
ACTOR_REVIEWS  = os.getenv("ACTOR_REVIEWS",  "gFtgG31RZJYlphznm")    # web_wanderer/amazon-reviews-extractor

# Bat DEBUG=1 trong .env de in them log trong collectors
DEBUG = os.getenv("DEBUG", "0") == "1"


def require_env(keys: list[str]) -> None:
    """Fail fast khi thieu env var can thiet. Goi o dau cac script collector."""
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            f"Missing required env vars: {missing}. "
            "Copy .env.example -> .env va dien cac gia tri nay."
        )

# 3 Electronics categories
CATEGORIES = [
    {
        "id":         "gaming_keyboard",
        "name":       "Gaming Keyboards",
        "search_url": "https://www.amazon.com/s?k=gaming+keyboard",
        "keywords":   ["gaming keyboard", "mechanical keyboard", "wireless gaming keyboard"],
        "top_n":      50,
    },
    {
        "id":         "true_wireless_earbuds",
        "name":       "True Wireless Earbuds",
        "search_url": "https://www.amazon.com/s?k=true+wireless+earbuds",
        "keywords":   ["true wireless earbuds", "wireless earbuds noise cancelling", "earbuds under 50"],
        "top_n":      50,
    },
    {
        "id":         "portable_charger",
        "name":       "Portable Chargers",
        "search_url": "https://www.amazon.com/s?k=portable+charger",
        "keywords":   ["portable charger", "power bank", "portable charger fast charging"],
        "top_n":      50,
    },
]

# Watchlist ASINs per category
# Thêm ASIN vào đây sau khi chạy category scraper lần đầu và chọn từ Top 50
WATCHLIST = {
    # 10 ASINs — mix 3 price tiers, brand diversity, đủ reviews cho sentiment
    "gaming_keyboard": [
        "B0D17C3ZVJ",   # TECKNET $29     — budget tier, 4.5K reviews
        "B0CF3VGQFL",   # Redragon $25    — budget tier, 6.4K reviews
        "B0CDX5XGLK",   # Redragon K673   — mid $50, 1.9K reviews
        "B07QGHK6Q8",   # Logitech G213   — mid $50, 7.2K reviews (established brand)
        "B07XVCP7F5",   # RK Royal Kludge — mid $48, 7.7K reviews
        "B0D14N2QZF",   # AULA F75 Pro    — mid $64, #1 rank
        "B0CLLHSWRL",   # AULA F99        — mid $69, 2.9K reviews
        "B0C9ZJHQHM",   # Womier SK80     — mid $57, 1.5K reviews
        "B07QQB9VCV",   # Logitech G PRO  — premium $100, 5.3K reviews
        "B07ZGDPT4M",   # SteelSeries Apex 3 — premium $50, 7.9K reviews
    ],
    "true_wireless_earbuds": [
        "B0BTYCRJSS",   # Soundcore P20i  — budget $20, 102K reviews (#1)
        "B09DT48V16",   # TAGRY           — budget $25, 85K reviews
        "B0DD41G2NZ",   # TOZO NC9        — budget $28, 42K reviews
        "B08KDZ2NZX",   # Soundcore Life A1 — mid $40, 43K reviews
        "B0CRTR3PMF",   # Soundcore P30i  — mid $28, 30K reviews
        "B0BQPNMXQV",   # JBL Vibe Beam   — mid $55, 37K reviews
        "B0C1QNRGHC",   # JBL Tune Flex   — mid $50, 13K reviews
        "B0DGHMNQ5Z",   # Apple AirPods 4 — premium $99, 28K reviews
        "B0FQFB8FMG",   # Apple AirPods Pro 3 — premium $200, 8K reviews
        "B0G1PJLWLZ",   # Samsung Galaxy Buds 4 Pro — premium $250, 315 reviews (new)
    ],
    "portable_charger": [
        "B0CB1FW5FC",   # INIU 45W slim   — budget $20, 77K reviews (#5)
        "B0CY2JJ4WS",   # charmast built-in cables — budget $21, 21K reviews (#1)
        "B0CFHHCMNS",   # charmast small  — budget $17, 3.4K reviews
        "B0D5CLSMFB",   # Anker PowerCore 10K — mid $20, 6K reviews
        "B0C6XK6DDL",   # Anker Nano      — mid $23, 14K reviews
        "B097TQZ38L",   # VEGER w/ AC plug — mid $26, 9.4K reviews
        "B0CSW947RH",   # podoru MagSafe  — mid $18, 9.4K reviews
        "B0BL7P8K16",   # VRURC 10000mAh  — mid $21, 11K reviews
        "B0CJBQJZ5F",   # charmast 20000mAh — premium $31, 5.9K reviews
        "B0DCZ56QNL",   # INIU 20000mAh   — premium $31, 767 reviews
    ],
}

# Image / pHash
IMAGE_BUCKET    = "product-images"
PHASH_THRESHOLD = 10  # hamming distance: >10 = image changed
