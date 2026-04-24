"""
Shared DB helpers cho dashboard.
Dùng supabase-py (không phải raw SQL).
"""
import os
import sys
from pathlib import Path
from functools import lru_cache

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client


@st.cache_resource
def get_client():
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


supabase = get_client()


def fetch(table: str, columns: str = "*", filters: dict | None = None,
          order_col: str | None = None, desc: bool = True, limit: int = 10000) -> list[dict]:
    """Query helper với cache 60s."""
    q = supabase.table(table).select(columns)
    if filters:
        for col, val in filters.items():
            if isinstance(val, (list, tuple)):
                q = q.in_(col, list(val))
            else:
                q = q.eq(col, val)
    if order_col:
        q = q.order(order_col, desc=desc)
    if limit:
        q = q.limit(limit)
    return q.execute().data


def query(sql: str, params=None):
    """Placeholder — prefer fetch() above. SQL fallback via RPC (cần tạo function)."""
    # Since supabase-py không support raw SQL, mô phỏng bằng count
    if "COUNT(DISTINCT asin)" in sql and "asins" in sql:
        rows = supabase.table("asins").select("asin").execute().data
        return [{"c": len({r["asin"] for r in rows})}]
    if "COUNT(*)" in sql and "reviews_raw" in sql:
        result = supabase.table("reviews_raw").select("*", count="exact", head=True).execute()
        return [{"c": result.count}]
    if "COUNT(*)" in sql and "alerts" in sql and params:
        result = (supabase.table("alerts").select("*", count="exact", head=True)
                  .eq("snapshot_date", params[0]).execute())
        return [{"c": result.count}]
    return [{"c": 0}]


@st.cache_data(ttl=60)
def latest_snapshot_date() -> str:
    """Ngày mới nhất trong daily_snapshots."""
    rows = supabase.table("daily_snapshots").select("snapshot_date").order(
        "snapshot_date", desc=True).limit(1).execute().data
    return rows[0]["snapshot_date"] if rows else "N/A"


@st.cache_data(ttl=60)
def get_asins_with_metadata() -> dict:
    """Map asin → {product_name, brand, category}"""
    rows = supabase.table("asins").select("asin,product_name,brand,category").execute().data
    return {r["asin"]: r for r in rows}
