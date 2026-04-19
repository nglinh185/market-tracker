"""
K-Means price tiering cho tung category.
k=3: entry / mid / premium
Populate: price_tier_daily
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from dotenv import load_dotenv
load_dotenv()

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from lib.db import supabase, upsert


TIER_NAMES = ["entry", "mid", "premium"]


def _assign_tier_names(centers: np.ndarray) -> dict[int, str]:
    order = np.argsort(centers.flatten())
    return {int(order[i]): TIER_NAMES[i] for i in range(len(TIER_NAMES))}


def main() -> None:
    today = date.today().isoformat()

    rankings = (
        supabase.table("category_rankings")
        .select("asin,browse_node,price")
        .eq("snapshot_date", today)
        .not_.is_("price", "null")
        .execute()
    ).data

    if not rankings:
        print("[PriceTier] No data today.")
        return

    from collections import defaultdict
    by_node: dict[str, list] = defaultdict(list)
    for r in rankings:
        by_node[r["browse_node"]].append(r)

    rows = []
    for node, items in by_node.items():
        prices = np.array([[float(r["price"])] for r in items])
        k = min(3, len(set(float(r["price"]) for r in items)))
        if k < 2:
            for r in items:
                rows.append({
                    "snapshot_date": today, "browse_node": node,
                    "asin": r["asin"], "price": float(r["price"]),
                    "cluster_label": 0, "cluster_name": "entry",
                })
            continue

        scaler  = StandardScaler()
        X       = scaler.fit_transform(prices)
        km      = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels  = km.fit_predict(X)
        centers = scaler.inverse_transform(km.cluster_centers_)
        tier_map = _assign_tier_names(centers)

        for i, r in enumerate(items):
            cluster = int(labels[i])
            rows.append({
                "snapshot_date": today,
                "browse_node":   node,
                "asin":          r["asin"],
                "price":         float(r["price"]),
                "cluster_label": cluster,
                "cluster_name":  tier_map[cluster],
            })

    # Dedupe theo (snapshot_date, browse_node, asin) vì 1 ASIN có thể xuất hiện nhiều rank
    dedup_map = {}
    for r in rows:
        key = (r["snapshot_date"], r["browse_node"], r["asin"])
        dedup_map[key] = r
    deduped = list(dedup_map.values())

    n = upsert("price_tier_daily", deduped, "snapshot_date,browse_node,asin")
    print(f"[PriceTier] {n} ASINs tiered (dedupe: {len(rows)} -> {len(deduped)}).")


if __name__ == "__main__":
    main()
