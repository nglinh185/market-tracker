"""
Analytics orchestrator — chay sau ingest_category + ingest_watchlist.
Thu tu: entrant_exit -> changes -> sponsored -> price_tier -> sentiment -> bms -> lqs -> alerts -> forecast
"""
import sys
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
PYTHON = sys.executable

ANALYTICS = [
    "analyze_entrant_exit.py",
    "analyze_changes.py",
    "analyze_sponsored.py",
    "analyze_price_tier.py",
    # sentiment phai chay truoc bms + lqs vi ca 2 doc tu review_sentiment_daily
    "analyze_sentiment.py",
    "analyze_bms.py",
    "analyze_lqs.py",
    "analyze_alerts.py",
    "analyze_price_forecast.py",
]


def main() -> None:
    failed = []
    for script in ANALYTICS:
        path = SCRIPTS_DIR / script
        print(f"\n{'='*50}")
        print(f"Running {script} ...")
        result = subprocess.run([PYTHON, str(path)], capture_output=False)
        if result.returncode != 0:
            print(f"  [ERROR] {script} failed with code {result.returncode}")
            failed.append(script)
            break

    if failed:
        print(f"\n[run_analytics] FAILED at {failed[0]}. Stopping pipeline.")
        sys.exit(1)

    print("\n[run_analytics] Completed successfully.")


if __name__ == "__main__":
    main()
