"""Page 2: Price Intelligence — K-Means tiers + discount tracker."""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import fetch, latest_snapshot_date, get_asins_with_metadata

st.set_page_config(page_title="Price Intelligence", page_icon="💰", layout="wide")

st.title("💰 Price Intelligence")
st.caption("K-Means clustering (entry/mid/premium) + discount tracking")

latest = latest_snapshot_date()
asins_meta = get_asins_with_metadata()

CATEGORIES = {"gaming_keyboard": "🎮 Gaming Keyboards",
              "true_wireless_earbuds": "🎧 True Wireless Earbuds",
              "portable_charger": "🔋 Portable Chargers"}
cat = st.selectbox("Category", options=list(CATEGORIES.keys()),
                   format_func=lambda x: CATEGORIES[x])

# --- K-Means scatter ---
st.subheader("🎯 Price Tier Clustering (K-Means)")
tiers = fetch("price_tier_daily",
              filters={"snapshot_date": latest, "browse_node": cat})
rankings = fetch("category_rankings",
                filters={"snapshot_date": latest, "browse_node": cat})

if tiers and rankings:
    df_t = pd.DataFrame(tiers)
    df_r = pd.DataFrame(rankings)[["asin", "rank", "reviews_count", "stars", "brand"]]
    df = df_t.merge(df_r, on="asin", how="left")

    fig = px.scatter(df, x="price", y="rank", color="cluster_name",
                     size="reviews_count", hover_data=["asin", "brand", "stars"],
                     color_discrete_map={"entry": "#22c55e", "mid": "#f59e0b", "premium": "#ef4444"},
                     title="Price vs Rank — bubble size = reviews count",
                     labels={"rank": "Category Rank (lower = better)"})
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

    # Summary per tier
    col1, col2, col3 = st.columns(3)
    for tier, col in [("entry", col1), ("mid", col2), ("premium", col3)]:
        sub = df[df["cluster_name"] == tier]
        if not sub.empty:
            col.metric(f"{tier.title()} Tier",
                      f"${sub['price'].min():.0f} — ${sub['price'].max():.0f}",
                      f"{len(sub)} products")

st.divider()

# --- Discount tracker ---
st.subheader("🏷️ Discount Tracker (Watchlist)")
snapshots = fetch("daily_snapshots", filters={"snapshot_date": latest},
                 columns="asin,price,list_price,discount_pct")
if snapshots:
    df_d = pd.DataFrame(snapshots)
    df_d = df_d[df_d["discount_pct"].notna() & (df_d["discount_pct"] > 0)]
    if not df_d.empty:
        df_d["product"] = df_d["asin"].map(lambda a: asins_meta.get(a, {}).get("product_name", a)[:40])
        df_d = df_d.sort_values("discount_pct", ascending=True)
        fig = px.bar(df_d, x="discount_pct", y="product", orientation="h",
                    color="discount_pct", color_continuous_scale="Reds",
                    title="Current Discounts on Watchlist")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Không có ASIN đang giảm giá hôm nay.")

st.divider()

# --- Price trends for watchlist ---
st.subheader("📉 Price Trends — Watchlist")
all_snaps = fetch("daily_snapshots", columns="asin,snapshot_date,price",
                 order_col="snapshot_date", desc=False)
if all_snaps:
    df_p = pd.DataFrame(all_snaps)
    df_p = df_p[df_p["asin"].isin([a for a, m in asins_meta.items() if m["category"] == cat])]
    df_p["product"] = df_p["asin"].map(lambda a: asins_meta.get(a, {}).get("product_name", a)[:30])
    fig = px.line(df_p, x="snapshot_date", y="price", color="product", markers=True)
    st.plotly_chart(fig, use_container_width=True)
