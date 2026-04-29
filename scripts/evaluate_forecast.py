"""
Forecast evaluation: walk-forward backtest of the Prophet price model.

For each watchlist ASIN with >= MIN_HISTORY days of price history:
  - Hold out the last HOLDOUT days.
  - Fit Prophet on the remaining days.
  - Predict HOLDOUT steps ahead.
  - Compute MAE, MAPE, and naive-baseline (last-observed-carry-forward) MAE.

We also report % of held-out points that fall within the 80% prediction
interval (yhat_lower, yhat_upper) — a coverage check on uncertainty.

Limitation (already in methodology chapter): with only ~15 days of history,
this is a sanity check, not a definitive measure of model accuracy. The point
is to show we *can* quantify error and that the forecast adds value over the
naive baseline (or, if it doesn't, to disclose that honestly).

Output: data/eval/forecast_eval.json + console summary.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import os
from datetime import date
from dotenv import load_dotenv
load_dotenv()

from lib.db import supabase
from config import WATCHLIST


OUT_DIR = Path(__file__).parent.parent / "data" / "eval"
MIN_HISTORY = 7      # need at least this many days to bother fitting
HOLDOUT     = 3      # forecast horizon for backtest


def _configure_cmdstan() -> None:
    """Prefer explicit CMDSTAN path from CI/local env when valid."""
    cmdstan_home = os.getenv("CMDSTAN")
    if not cmdstan_home:
        return
    makefile = Path(cmdstan_home) / "makefile"
    if not makefile.exists():
        print(f"[Eval-Forecast] CMDSTAN is set but invalid (missing makefile): {cmdstan_home}")
        return
    try:
        import cmdstanpy
        cmdstanpy.set_cmdstan_path(str(Path(cmdstan_home)))
        print(f"[Eval-Forecast] Using CMDSTAN at {cmdstan_home}")
    except Exception as e:
        print(f"[Eval-Forecast] Failed to configure CMDSTAN path {cmdstan_home}: {e}")


def _mae(y_true: list[float], y_pred: list[float]) -> float:
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / len(y_true)


def _mape(y_true: list[float], y_pred: list[float]) -> float:
    return sum(abs(a - b) / a for a, b in zip(y_true, y_pred) if a) / len(y_true) * 100


def main() -> None:
    _configure_cmdstan()

    try:
        from prophet import Prophet
    except ImportError:
        print("[Eval-Forecast] prophet not installed. Skip.")
        return

    import pandas as pd

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    asins = [a for v in WATCHLIST.values() for a in v]

    snaps = (supabase.table("daily_snapshots")
             .select("asin,snapshot_date,price")
             .in_("asin", asins)
             .not_.is_("price", "null")
             .order("snapshot_date").execute()).data or []

    by_asin: dict[str, list] = {}
    for r in snaps:
        by_asin.setdefault(r["asin"], []).append(r)

    per_asin = []
    pooled_true, pooled_pred, pooled_naive = [], [], []
    pooled_in_band = 0

    for asin, rows in by_asin.items():
        if len(rows) < MIN_HISTORY + HOLDOUT:
            continue
        train = rows[:-HOLDOUT]
        test  = rows[-HOLDOUT:]

        df = pd.DataFrame([{"ds": r["snapshot_date"], "y": float(r["price"])} for r in train])
        df["ds"] = pd.to_datetime(df["ds"])

        try:
            m = Prophet(daily_seasonality=False, weekly_seasonality=False,
                        yearly_seasonality=False, uncertainty_samples=100,
                        stan_backend="CMDSTANPY")
            m.fit(df)
            future = m.make_future_dataframe(periods=HOLDOUT)
            forecast = m.predict(future).tail(HOLDOUT)
        except Exception as e:
            print(f"  [WARN] {asin}: {e}")
            continue

        y_true = [float(r["price"]) for r in test]
        y_pred = forecast["yhat"].tolist()
        y_lo   = forecast["yhat_lower"].tolist()
        y_hi   = forecast["yhat_upper"].tolist()
        # Naive baseline: last observed price carried forward.
        last_train_price = float(train[-1]["price"])
        y_naive = [last_train_price] * HOLDOUT

        in_band = sum(1 for yt, lo, hi in zip(y_true, y_lo, y_hi) if lo <= yt <= hi)

        per_asin.append({
            "asin":       asin,
            "n_train":    len(train),
            "horizon":    HOLDOUT,
            "mae":        round(_mae(y_true, y_pred), 3),
            "mape_pct":   round(_mape(y_true, y_pred), 2),
            "naive_mae":  round(_mae(y_true, y_naive), 3),
            "in_80_band": in_band,
        })
        pooled_true.extend(y_true)
        pooled_pred.extend(y_pred)
        pooled_naive.extend(y_naive)
        pooled_in_band += in_band

    if not per_asin:
        print(f"[Eval-Forecast] No ASIN had >= {MIN_HISTORY + HOLDOUT} days of price history.")
        return

    summary = {
        "as_of":             date.today().isoformat(),
        "asins_evaluated":   len(per_asin),
        "horizon_days":      HOLDOUT,
        "min_history":       MIN_HISTORY,
        "pooled_mae":        round(_mae(pooled_true, pooled_pred), 3),
        "pooled_mape_pct":   round(_mape(pooled_true, pooled_pred), 2),
        "pooled_naive_mae":  round(_mae(pooled_true, pooled_naive), 3),
        "pi_coverage_pct":   round(pooled_in_band / len(pooled_true) * 100, 1),
        "per_asin":          sorted(per_asin, key=lambda x: x["mape_pct"]),
    }

    out_file = OUT_DIR / "forecast_eval.json"
    out_file.write_text(json.dumps(summary, indent=2))

    print(f"[Eval-Forecast] {summary['asins_evaluated']} ASINs | "
          f"MAE={summary['pooled_mae']} | MAPE={summary['pooled_mape_pct']}% | "
          f"naive MAE={summary['pooled_naive_mae']} | 80% PI coverage={summary['pi_coverage_pct']}%")
    print(f"[Eval-Forecast] Written -> {out_file}")


if __name__ == "__main__":
    main()
