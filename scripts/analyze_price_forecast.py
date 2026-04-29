"""
Price trend + short-term forecast dung Facebook Prophet.
Persists forecast to Supabase (price_forecast_daily) AND data/forecasts/ JSON.
Acknowledge: n=14 days -> forecast accuracy han che, dung de trend analysis.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import os
from datetime import date
from dotenv import load_dotenv
load_dotenv()

from lib.db import supabase, upsert
from config import WATCHLIST

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "forecasts"


def _configure_cmdstan() -> None:
    """Prefer explicit CMDSTAN path from CI/local env when valid."""
    cmdstan_home = os.getenv("CMDSTAN")
    if not cmdstan_home:
        return
    makefile = Path(cmdstan_home) / "makefile"
    if not makefile.exists():
        print(f"[Forecast] CMDSTAN is set but invalid (missing makefile): {cmdstan_home}")
        return
    try:
        import cmdstanpy
        cmdstanpy.set_cmdstan_path(str(Path(cmdstan_home)))
        print(f"[Forecast] Using CMDSTAN at {cmdstan_home}")
    except Exception as e:
        print(f"[Forecast] Failed to configure CMDSTAN path {cmdstan_home}: {e}")


def _wire_prophet_cmdstan() -> None:
    """
    Prophet 1.1.5 looks for cmdstan inside its own package
    (`site-packages/prophet/stan_model/cmdstan-2.33.1`) rather than honoring
    cmdstanpy's path. If we have a valid cmdstan elsewhere (CI installs it to
    ~/.cmdstan), symlink it into Prophet's expected location so Prophet can
    find a real makefile + binaries.
    """
    cmdstan_home = os.getenv("CMDSTAN")
    if not cmdstan_home or not (Path(cmdstan_home) / "makefile").exists():
        return
    try:
        import prophet
    except ImportError:
        return
    prophet_stan_dir = Path(prophet.__file__).parent / "stan_model"
    expected = prophet_stan_dir / Path(cmdstan_home).name
    try:
        if expected.is_symlink() or expected.exists():
            if expected.is_symlink():
                expected.unlink()
            elif expected.is_dir():
                import shutil
                shutil.rmtree(expected)
        prophet_stan_dir.mkdir(parents=True, exist_ok=True)
        os.symlink(cmdstan_home, expected)
        print(f"[Forecast] Linked {cmdstan_home} -> {expected}")
    except Exception as e:
        print(f"[Forecast] Failed to wire Prophet cmdstan path: {e}")


def main() -> None:
    _configure_cmdstan()
    _wire_prophet_cmdstan()

    try:
        from prophet import Prophet
    except ImportError:
        print("[Forecast] prophet not installed. Run: pip install prophet")
        sys.exit(1)

    import pandas as pd
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    asins = [a for asins in WATCHLIST.values() for a in asins]

    all_snaps = (
        supabase.table("daily_snapshots")
        .select("asin,snapshot_date,price,bsr")
        .in_("asin", asins)
        .not_.is_("price", "null")
        .order("snapshot_date")
        .execute()
    ).data

    from collections import defaultdict
    by_asin: dict[str, list] = defaultdict(list)
    for r in all_snaps:
        by_asin[r["asin"]].append(r)

    results: dict[str, list[dict]] = {}
    skipped_short: list[str] = []
    failed: list[str] = []

    for asin, rows in by_asin.items():
        if len(rows) < 3:
            skipped_short.append(asin)
            continue
        df = pd.DataFrame([
            {"ds": r["snapshot_date"], "y": float(r["price"])} for r in rows
        ])
        df["ds"] = pd.to_datetime(df["ds"])

        try:
            m = Prophet(daily_seasonality=False, weekly_seasonality=False,
                        yearly_seasonality=False, uncertainty_samples=100,
                        stan_backend="CMDSTANPY")
            m.fit(df)
            future = m.make_future_dataframe(periods=7)
            forecast = m.predict(future)
            tail = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(7)
            results[asin] = tail.to_dict("records")
        except Exception as e:
            print(f"  [WARN] {asin}: Prophet failed ({e})")
            failed.append(asin)

    out_file = OUTPUT_DIR / f"price_forecast_{today}.json"
    out_file.write_text(json.dumps(
        {k: [{**r, "ds": str(r["ds"])} for r in v] for k, v in results.items()},
        indent=2
    ))
    total = len(by_asin)
    print(f"[Forecast] success={len(results)} failed={len(failed)} "
          f"skipped_short_history={len(skipped_short)} (of {total} ASINs) -> {out_file}")
    if failed:
        print(f"[Forecast] failed ASINs: {', '.join(failed)}")

    # Persist to Supabase so the OpenClaw VM (different machine than CI) can
    # read the forecasts via query_price_forecast skill. Falls back silently
    # if the price_forecast_daily table hasn't been migrated yet.
    db_rows = []
    for asin, points in results.items():
        for p in points:
            db_rows.append({
                "snapshot_date": today,
                "asin":          asin,
                "ds":            str(p["ds"])[:10],
                "yhat":          round(float(p["yhat"]), 2),
                "yhat_lower":    round(float(p["yhat_lower"]), 2),
                "yhat_upper":    round(float(p["yhat_upper"]), 2),
            })
    if db_rows:
        try:
            upsert("price_forecast_daily", db_rows, "snapshot_date,asin,ds")
            print(f"[Forecast] {len(db_rows)} forecast points upserted to price_forecast_daily.")
        except Exception as e:
            print(f"[Forecast] price_forecast_daily upsert failed (run migration 005?): {e}")

    if not results:
        print("[Forecast] No forecasts produced — failing job to surface CmdStan/Prophet issue.")
        sys.exit(1)


if __name__ == "__main__":
    main()
