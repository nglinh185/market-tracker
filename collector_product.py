"""
DEPRECATED — giu lai de backward-compat.
Entrypoint moi: `python scripts/ingest_watchlist.py` (product detail + pHash + upload Storage).
"""
import sys
from pathlib import Path

print("[DEPRECATED] collector_product.py -> forwarding to scripts/ingest_watchlist.py", file=sys.stderr)
sys.path.insert(0, str(Path(__file__).parent))
from scripts.ingest_watchlist import main

if __name__ == "__main__":
    main()
