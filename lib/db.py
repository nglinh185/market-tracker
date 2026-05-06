import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Explicit path so load_dotenv works regardless of CWD (e.g. when OpenClaw
# runs skills as subprocesses from a different working directory).
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)


def upsert(table: str, rows: list[dict], conflict_cols: str) -> int:
    """Upsert rows vào table. Trả về số rows đã xử lý."""
    if not rows:
        return 0
    supabase.table(table).upsert(rows, on_conflict=conflict_cols).execute()
    return len(rows)
