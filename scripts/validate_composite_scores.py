"""
Composite-score validation for thesis defense.

Two analyses:
  1. Cronbach's alpha on the 7 active LQS sub-scores
     (title, bullet, image, aplus, rating, review, sentiment).
     - Internal-consistency reliability of the LQS construct.
     - Threshold: alpha >= 0.7 = acceptable, >= 0.8 = good.

  2. BMS forward predictive validity
     - Spearman rank correlation between BMS_t and BSR_{t+lag}
       (negative correlation = high BMS today predicts BSR improvement
       in the future, since lower BSR is better).
     - Default lag = 5 days. Pearson is also reported for reference.

Inputs:  Supabase tables `listing_quality_score_daily`,
                          `brand_momentum_daily`,
                          `daily_snapshots`.
Output:  data/eval/composite_validation.json + console summary.
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from lib.db import supabase

OUT_FILE = Path(__file__).parent.parent / "data" / "eval" / "composite_validation.json"
LQS_COMPONENTS = (
    "title_score",
    "bullet_score",
    "image_score",
    "aplus_score",
    "rating_score",
    "review_score",
    "sentiment_score",
)
BMS_LAG_DAYS = 5


def cronbach_alpha(matrix: np.ndarray) -> float:
    """
    matrix: (n_observations, n_items)
    alpha = (k / (k-1)) * (1 - sum(var_i) / var_total)
    """
    if matrix.shape[0] < 2 or matrix.shape[1] < 2:
        return float("nan")
    k = matrix.shape[1]
    item_variances = matrix.var(axis=0, ddof=1)
    total_variance = matrix.sum(axis=1).var(ddof=1)
    if total_variance == 0:
        return float("nan")
    return float((k / (k - 1)) * (1 - item_variances.sum() / total_variance))


def fetch_all(table: str, columns: str) -> list[dict]:
    rows: list[dict] = []
    page_size = 1000
    start = 0
    while True:
        resp = (
            supabase.table(table)
            .select(columns)
            .range(start, start + page_size - 1)
            .execute()
        )
        chunk = resp.data or []
        rows.extend(chunk)
        if len(chunk) < page_size:
            break
        start += page_size
    return rows


def lqs_alpha() -> dict:
    cols = ",".join(LQS_COMPONENTS) + ",asin,snapshot_date"
    rows = fetch_all("listing_quality_score_daily", cols)

    if not rows:
        return {"error": "no LQS rows found"}

    matrix = np.array(
        [[float(r.get(c) or 0) for c in LQS_COMPONENTS] for r in rows],
        dtype=float,
    )

    alpha = cronbach_alpha(matrix)

    item_drop_alpha = {}
    for i, name in enumerate(LQS_COMPONENTS):
        keep = [j for j in range(matrix.shape[1]) if j != i]
        item_drop_alpha[name] = round(cronbach_alpha(matrix[:, keep]), 4)

    item_stats = {}
    for i, name in enumerate(LQS_COMPONENTS):
        col = matrix[:, i]
        item_stats[name] = {
            "mean": round(float(col.mean()), 3),
            "std":  round(float(col.std(ddof=1)), 3),
            "min":  round(float(col.min()), 3),
            "max":  round(float(col.max()), 3),
        }

    if alpha >= 0.9:
        verdict = "excellent"
    elif alpha >= 0.8:
        verdict = "good"
    elif alpha >= 0.7:
        verdict = "acceptable"
    elif alpha >= 0.6:
        verdict = "questionable"
    elif alpha >= 0.5:
        verdict = "poor"
    else:
        verdict = "unacceptable"

    return {
        "n_observations":     int(matrix.shape[0]),
        "n_items":            int(matrix.shape[1]),
        "cronbach_alpha":     round(alpha, 4),
        "verdict":            verdict,
        "alpha_if_dropped":   item_drop_alpha,
        "item_descriptives":  item_stats,
    }


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation, no scipy dep."""
    if len(x) < 3:
        return float("nan")
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    denom = np.sqrt((rx**2).sum() * (ry**2).sum())
    if denom == 0:
        return float("nan")
    return float((rx * ry).sum() / denom)


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 3:
        return float("nan")
    xm = x - x.mean()
    ym = y - y.mean()
    denom = np.sqrt((xm**2).sum() * (ym**2).sum())
    if denom == 0:
        return float("nan")
    return float((xm * ym).sum() / denom)


def bms_forward_validity(lag_days: int = BMS_LAG_DAYS) -> dict:
    bms_rows = fetch_all("brand_momentum_daily", "asin,snapshot_date,bms_score")
    bsr_rows = fetch_all("daily_snapshots",      "asin,snapshot_date,bsr")

    bms_map: dict[tuple[str, str], float] = {}
    for r in bms_rows:
        if r.get("bms_score") is None:
            continue
        bms_map[(r["asin"], r["snapshot_date"])] = float(r["bms_score"])

    bsr_by_asin: dict[str, dict[str, float]] = defaultdict(dict)
    for r in bsr_rows:
        if r.get("bsr") is None:
            continue
        bsr_by_asin[r["asin"]][r["snapshot_date"]] = float(r["bsr"])

    pairs: list[tuple[float, float]] = []
    per_asin_pairs: dict[str, list[tuple[float, float]]] = defaultdict(list)

    for (asin, dt_str), bms in bms_map.items():
        try:
            d = date.fromisoformat(dt_str)
        except ValueError:
            continue
        future_dt = (d.fromordinal(d.toordinal() + lag_days)).isoformat()
        bsr_future = bsr_by_asin.get(asin, {}).get(future_dt)
        if bsr_future is None:
            continue
        pairs.append((bms, bsr_future))
        per_asin_pairs[asin].append((bms, bsr_future))

    if len(pairs) < 5:
        return {
            "lag_days":       lag_days,
            "n_pairs":        len(pairs),
            "error":          "insufficient pairs for correlation",
        }

    arr = np.array(pairs, dtype=float)
    bms_arr, bsr_arr = arr[:, 0], arr[:, 1]
    rho = spearman(bms_arr, bsr_arr)
    r   = pearson(bms_arr, bsr_arr)

    per_asin_rho = {}
    for asin, ps in per_asin_pairs.items():
        if len(ps) >= 3:
            a = np.array(ps, dtype=float)
            per_asin_rho[asin] = round(spearman(a[:, 0], a[:, 1]), 4)

    median_per_asin = (
        round(float(np.median(list(per_asin_rho.values()))), 4)
        if per_asin_rho else None
    )

    if rho < -0.3:
        verdict = "supports forward validity"
    elif rho < -0.1:
        verdict = "weak forward validity"
    elif rho > 0.1:
        verdict = "wrong-sign — BMS does not predict BSR improvement"
    else:
        verdict = "no meaningful relationship"

    return {
        "lag_days":              lag_days,
        "n_pairs":               len(pairs),
        "n_asins_with_data":     len(per_asin_pairs),
        "n_asins_with_rho":      len(per_asin_rho),
        "spearman_rho_pooled":   round(rho, 4),
        "pearson_r_pooled":      round(r, 4),
        "median_per_asin_rho":   median_per_asin,
        "verdict":               verdict,
        "interpretation_note":   (
            "Lower BSR = better rank, so a NEGATIVE correlation means high "
            "BMS today predicts a future rank improvement (validates BMS)."
        ),
    }


def main() -> None:
    print("[Validate] Computing Cronbach's alpha on LQS components...")
    lqs_result = lqs_alpha()

    print(f"[Validate] Computing BMS forward validity (lag={BMS_LAG_DAYS} days)...")
    bms_result = bms_forward_validity(BMS_LAG_DAYS)

    summary = {
        "as_of":            date.today().isoformat(),
        "lqs_reliability":  lqs_result,
        "bms_forward_validity": bms_result,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(summary, indent=2))

    print("\n=== LQS reliability ===")
    if "error" in lqs_result:
        print(f"  {lqs_result['error']}")
    else:
        print(f"  n_observations    : {lqs_result['n_observations']}")
        print(f"  n_items           : {lqs_result['n_items']}")
        print(f"  Cronbach's alpha  : {lqs_result['cronbach_alpha']}  ({lqs_result['verdict']})")
        print(f"  alpha_if_dropped  :")
        for name, a in lqs_result["alpha_if_dropped"].items():
            print(f"    drop {name:18s} -> alpha = {a}")

    print("\n=== BMS forward predictive validity ===")
    if "error" in bms_result:
        print(f"  lag={bms_result['lag_days']}d, n_pairs={bms_result['n_pairs']}: {bms_result['error']}")
    else:
        print(f"  lag_days             : {bms_result['lag_days']}")
        print(f"  n_pairs              : {bms_result['n_pairs']}  (across {bms_result['n_asins_with_data']} ASINs)")
        print(f"  Spearman rho (pooled): {bms_result['spearman_rho_pooled']}")
        print(f"  Pearson  r   (pooled): {bms_result['pearson_r_pooled']}")
        print(f"  Median per-ASIN rho  : {bms_result['median_per_asin_rho']}")
        print(f"  Verdict              : {bms_result['verdict']}")

    print(f"\n[Validate] Written -> {OUT_FILE}")


if __name__ == "__main__":
    main()
