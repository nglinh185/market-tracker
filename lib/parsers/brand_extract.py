"""
Brand extraction fallback when Apify omits the `brand` field.

Used by both category and watchlist parsers. Pattern-matches the start of
`product_name` against a curated list of known brands relevant to the 3
tracked categories (gaming keyboards, true wireless earbuds, portable chargers).

Fallback chain (in caller):
    item.get("brand")                       # 1. Apify direct field
    extract_brand_from_name(title)          # 2. This module
    None                                    # 3. Give up — leave NULL
"""
from __future__ import annotations
import re

# Brands ranked longest-first to match "Soundcore by Anker" before "Soundcore"
# and "Apple AirPods" before "Apple". Add new brands here as the watchlist grows.
KNOWN_BRANDS = [
    # Audio / earbuds
    "Soundcore by Anker", "Apple AirPods", "Audio-Technica", "Bang & Olufsen",
    "Sennheiser", "Soundpeats", "Skullcandy", "EarFun", "Anker", "Soundcore",
    "Apple", "Beats", "Bose", "Sony", "Samsung", "JBL", "JLab", "TOZO",
    "TAGRY", "Jabra",
    # Keyboards
    "RK ROYAL KLUDGE", "RK Royal Kludge", "Royal Kludge", "Logitech G",
    "SteelSeries", "Logitech", "Razer", "Redragon", "Corsair", "HyperX",
    "Womier", "AULA", "Aula", "TECKNET", "EPOMAKER", "Keychron", "Drop",
    "Nuphy", "ASUS", "MageGee", "Niceday",
    # Chargers / power banks
    "INIU", "Charmast", "VEGER", "VRURC", "ROMOSS", "Baseus", "UGREEN",
    "Mophie", "Belkin", "OtterBox",
]

# Pre-sort once at import — longer matches win
_BRANDS_SORTED = sorted(KNOWN_BRANDS, key=lambda x: -len(x))
_RE_NORMALIZE = re.compile(r"\s+")


def extract_brand_from_name(name: str | None) -> str | None:
    """Return canonical brand name if `name` starts with one, else None."""
    if not name:
        return None
    nl = _RE_NORMALIZE.sub(" ", name).strip().lower()
    for brand in _BRANDS_SORTED:
        if nl.startswith(brand.lower()):
            return brand
    return None


def resolve_brand(apify_brand: str | None, product_name: str | None) -> str | None:
    """One-shot fallback chain. Use this from parsers."""
    if apify_brand and apify_brand.strip():
        return apify_brand.strip()
    return extract_brand_from_name(product_name)
