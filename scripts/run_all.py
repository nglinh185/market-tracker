"""
Orchestrator — chạy toàn bộ pipeline theo thứ tự.
GitHub Actions gọi file này mỗi ngày.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
from datetime import date

SCRIPTS = [
    ("Category scraper",   "scripts/ingest_category.py"),
    ("Watchlist scraper",  "scripts/ingest_watchlist.py"),
    ("Analytics",          "scripts/run_analytics.py"),
]


def run_script(label: str, path: str) -> bool:
    print(f"\n{'='*50}")
    print(f"[run_all] {label}")
    print(f"{'='*50}")
    result = subprocess.run([sys.executable, path], capture_output=False)
    if result.returncode != 0:
        print(f"[run_all] ERROR: {label} exited with code {result.returncode}")
        return False
    return True


def main() -> None:
    today   = date.today().isoformat()
    errors  = []

    print(f"[run_all] Pipeline bắt đầu: {today}")

    for label, path in SCRIPTS:
        ok = run_script(label, path)
        if not ok:
            errors.append(label)

    print(f"\n[run_all] Hoàn thành. Errors: {errors if errors else 'none'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
