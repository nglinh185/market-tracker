import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

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
