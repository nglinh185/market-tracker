"""
Analytics orchestrator — chay sau ingest_category + ingest_watchlist.
Thu tu: entrant_exit -> changes -> sponsored -> price_tier -> bms -> lqs -> alerts -> forecast
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
    "analyze_bms.py",
    "analyze_lqs.py",
    "analyze_alerts.py",
    "analyze_price_forecast.py",
]


def main() -> None:
    for script in ANALYTICS:
        path = SCRIPTS_DIR / script
        print(f"\n{'='*50}")
        print(f"Running {script} ...")
        result = subprocess.run([PYTHON, str(path)], capture_output=False)
        if result.returncode != 0:
            print(f"  [ERROR] {script} failed with code {result.returncode}")


if __name__ == "__main__":
    main()
