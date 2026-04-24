"""Page 1: Market Overview — Top 50 rankings + entrant/exit tracking."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db import fetch, latest_snapshot_date, get_asins_with_metadata

st.set_page_config(page_title="Market Overview", page_icon="📈", layout="wide")

st.title("📈 Market Overview")
st.caption("Top 50 rankings + entrant/exit tracking across 3 categories")

latest = latest_snapshot_date()
asins_meta = get_asins_with_metadata()

# Category selector
CATEGORIES = {"gaming_keyboard": "🎮 Gaming Keyboards",
              "true_wireless_earbuds": "🎧 True Wireless Earbuds",
              "portable_charger": "🔋 Portable Chargers"}
cat = st.selectbox("Category", options=list(CATEGORIES.keys()),
                   format_func=lambda x: CATEGORIES[x])

# Metrics row
rankings_today = fetch("category_rankings",
                      filters={"snapshot_date": latest, "browse_node": cat},
                      order_col="rank", desc=False)
events_today = fetch("entrant_exit_events",
                    filters={"snapshot_date": latest, "browse_node": cat})

col1, col2, col3, col4 = st.columns(4)
col1.metric("Products Tracked", len(rankings_today))
col2.metric("New Entrants", sum(1 for e in events_today if e["event_type"] == "entrant"))
col3.metric("Exits", sum(1 for e in events_today if e["event_type"] == "exit"))
sponsored = sum(1 for r in rankings_today if r.get("is_sponsored"))
col4.metric("Sponsored Slots", sponsored)

st.divider()

# BSR Trend for Watchlist ASINs
st.subheader("BSR Trend — Watchlist ASINs (15 ngày)")
snapshots = fetch("daily_snapshots", columns="asin,snapshot_date,bsr",
                 order_col="snapshot_date", desc=False)
if snapshots:
    df = pd.DataFrame(snapshots)
    df = df[df["asin"].isin([a for a, m in asins_meta.items() if m["category"] == cat])]
    df["product"] = df["asin"].map(lambda a: asins_meta.get(a, {}).get("product_name", a)[:40])
    fig = px.line(df, x="snapshot_date", y="bsr", color="product",
                  title="Lower BSR = Better rank")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Không có data BSR.")

st.divider()

# Top 50 Table
st.subheader(f"Top 50 Rankings — {CATEGORIES[cat]}")
if rankings_today:
    df_rank = pd.DataFrame(rankings_today)[
        ["rank", "asin", "title", "brand", "price", "stars",
         "reviews_count", "is_sponsored"]
    ].head(50)
    df_rank.columns = ["#", "ASIN", "Title", "Brand", "Price ($)", "Stars",
                       "Reviews", "Sponsored"]
    st.dataframe(df_rank, hide_index=True, use_container_width=True,
                column_config={"Title": st.column_config.TextColumn(width="large")})

# Entrant/Exit detail
if events_today:
    st.divider()
    st.subheader("🔄 Entrant / Exit Events")
    df_evt = pd.DataFrame(events_today)[["asin", "event_type", "rank_today",
                                          "rank_yesterday", "is_top10"]]
    st.dataframe(df_evt, hide_index=True, use_container_width=True)
