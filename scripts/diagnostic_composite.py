"""
Diagnostic: check variance and data quality for LQS + BMS validation.

Prints:
  1. Per-component variance and near-constant check for LQS
  2. BSR stickiness (% ASINs with BSR std < 100)
  3. Distribution of per-ASIN BMS-BSR Spearman rho
"""
from __future__ import annotations
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()
from lib.db import supabase

LQS_COMPONENTS = (
    "title_score", "bullet_score", "image_score",
    "aplus_score", "rating_score", "review_score", "sentiment_score",
)


def fetch_all(table, columns):
    rows, start, size = [], 0, 1000
    while True:
        chunk = supabase.table(table).select(columns).range(start, start+size-1).execute().data or []
        rows.extend(chunk)
        if len(chunk) < size:
            break
        start += size
    return rows


def spearman(x, y):
    if len(x) < 3:
        return float("nan")
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    denom = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / denom) if denom else float("nan")


def main():
    # ── 1. LQS component variance ──────────────────────────────────────────
    print("=== LQS component variance ===")
    lqs_rows = fetch_all("listing_quality_score_daily",
                         ",".join(LQS_COMPONENTS) + ",asin,snapshot_date")
    mat = np.array([[float(r.get(c) or 0) for c in LQS_COMPONENTS]
                    for r in lqs_rows], dtype=float)

    for i, name in enumerate(LQS_COMPONENTS):
        col = mat[:, i]
        unique_vals = len(np.unique(col))
        print(f"  {name:20s}  mean={col.mean():.2f}  std={col.std():.3f}  "
              f"min={col.min():.1f}  max={col.max():.1f}  unique_vals={unique_vals}")

    print(f"\n  (n_rows={len(lqs_rows)}, "
          f"n_unique_asins={len(set(r['asin'] for r in lqs_rows))}, "
          f"n_unique_dates={len(set(r['snapshot_date'] for r in lqs_rows))})")

    # ── 2. BSR stickiness ──────────────────────────────────────────────────
    print("\n=== BSR stickiness per ASIN ===")
    bsr_rows = fetch_all("daily_snapshots", "asin,snapshot_date,bsr")
    bsr_by_asin = defaultdict(list)
    for r in bsr_rows:
        if r.get("bsr"):
            bsr_by_asin[r["asin"]].append(float(r["bsr"]))

    stds = []
    for asin, vals in sorted(bsr_by_asin.items()):
        arr = np.array(vals)
        s = arr.std()
        stds.append(s)
        print(f"  {asin}  n={len(vals)}  mean_bsr={arr.mean():.0f}  std={s:.1f}")

    stds = np.array(stds)
    print(f"\n  Median BSR std: {np.median(stds):.1f}")
    print(f"  % ASINs with BSR std < 100: {(stds < 100).mean()*100:.0f}%")
    print(f"  % ASINs with BSR std < 500: {(stds < 500).mean()*100:.0f}%")

    # ── 3. Per-ASIN BMS-BSR rho distribution ──────────────────────────────
    print("\n=== Per-ASIN BMS-BSR(t+5) Spearman rho ===")
    bms_rows = fetch_all("brand_momentum_daily", "asin,snapshot_date,bms_score")
    bms_map = {(r["asin"], r["snapshot_date"]): float(r["bms_score"])
               for r in bms_rows if r.get("bms_score") is not None}
    bsr_date = {(r["asin"], r["snapshot_date"]): float(r["bsr"])
                for r in bsr_rows if r.get("bsr")}

    from datetime import date as Date
    per_asin = defaultdict(list)
    for (asin, dt), bms in bms_map.items():
        try:
            future = Date.fromisoformat(dt).fromordinal(
                Date.fromisoformat(dt).toordinal() + 5).isoformat()
        except Exception:
            continue
        bsr_f = bsr_date.get((asin, future))
        if bsr_f:
            per_asin[asin].append((bms, bsr_f))

    rhos = {}
    for asin, pairs in sorted(per_asin.items()):
        if len(pairs) >= 3:
            a = np.array(pairs)
            rho = spearman(a[:, 0], a[:, 1])
            rhos[asin] = rho
            print(f"  {asin}  n={len(pairs)}  rho={rho:+.3f}")
        else:
            print(f"  {asin}  n={len(pairs)}  rho=N/A (too few pairs)")

    if rhos:
        vals = np.array(list(rhos.values()))
        print(f"\n  mean rho={vals.mean():+.3f}  median={np.median(vals):+.3f}  "
              f"std={vals.std():.3f}")
        print(f"  % negative rho: {(vals < 0).mean()*100:.0f}%")


if __name__ == "__main__":
    main()
