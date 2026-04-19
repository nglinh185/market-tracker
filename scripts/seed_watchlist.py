"""
Chạy 1 lần duy nhất để insert watchlist ASINs vào DB.
Trước khi chạy: điền WATCHLIST trong config.py.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from config import WATCHLIST
from lib.db import supabase


def main() -> None:
    rows = []
    for category_id, asins in WATCHLIST.items():
        for asin in asins:
            rows.append({
                "asin":        asin.strip(),
                "category":    category_id,
                "is_active":   True,
            })

    if not rows:
        print("WATCHLIST trong config.py đang trống. Thêm ASINs vào trước.")
        return

    supabase.table("asins").upsert(rows, on_conflict="asin").execute()
    print(f"Seeded {len(rows)} ASINs into asins table:")
    for r in rows:
        print(f"  {r['asin']} ({r['category']})")


if __name__ == "__main__":
    main()
