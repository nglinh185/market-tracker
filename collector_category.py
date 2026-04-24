"""
DEPRECATED — giu lai de backward-compat.
Entrypoint moi: `python scripts/ingest_category.py` (chay cho 3 categories tu config.py).
"""
import sys
from pathlib import Path

print("[DEPRECATED] collector_category.py -> forwarding to scripts/ingest_category.py", file=sys.stderr)
sys.path.insert(0, str(Path(__file__).parent))
from scripts.ingest_category import main

if __name__ == "__main__":
    main()
