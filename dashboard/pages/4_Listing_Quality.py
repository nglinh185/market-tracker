"""Page 4: Listing Quality — LQS radar + image/content changes."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db import fetch, latest_snapshot_date, get_asins_with_metadata

st.set_page_config(page_title="Listing Quality", page_icon="⭐", layout="wide")

st.title("⭐ Listing Quality Score (LQS)")
st.caption("Composite 0-100 score across title, bullets, images, A+, rating, reviews, sentiment, freshness")

latest = latest_snapshot_date()
asins_meta = get_asins_with_metadata()

# --- LQS Heatmap for all watchlist ---
st.subheader("🔥 LQS Overview — All Watchlist ASINs")
lqs_all = fetch("listing_quality_score_daily", filters={"snapshot_date": latest})
if lqs_all:
    df = pd.DataFrame(lqs_all)
    df["product"] = df["asin"].map(lambda a: asins_meta.get(a, {}).get("product_name", a)[:40])
    df["category"] = df["asin"].map(lambda a: asins_meta.get(a, {}).get("category", ""))
    df = df.sort_values("lqs_total", ascending=False)

    fig = px.bar(df, x="lqs_total", y="product", orientation="h", color="lqs_total",
                color_continuous_scale=["red", "yellow", "green"], range_color=[0, 100],
                title="Total LQS Score (higher = better listing)")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- LQS Radar for selected ASIN ---
st.subheader("🎯 LQS Breakdown — Per ASIN")
if lqs_all:
    asin_opts = {f"{asins_meta.get(r['asin'], {}).get('product_name', r['asin'])[:50]} ({r['asin']})": r["asin"]
                for r in lqs_all}
    selected_label = st.selectbox("Select product", options=list(asin_opts.keys()))
    selected_asin = asin_opts[selected_label]

    row = next(r for r in lqs_all if r["asin"] == selected_asin)

    categories = ["Title", "Bullets", "Image", "A+ Content", "Rating",
                  "Reviews", "Sentiment"]
    values = [row["title_score"] or 0, row["bullet_score"] or 0,
             row["image_score"] or 0, row["aplus_score"] or 0,
             row["rating_score"] or 0, row["review_score"] or 0,
             row["sentiment_score"] or 0]

    # Normalize các score về cùng thang 0-15 để radar hiển thị đẹp hơn
    max_scores = [10, 15, 15, 15, 20, 15, 10]
    normalized = [v / m * 100 for v, m in zip(values, max_scores)]

    fig = go.Figure(go.Scatterpolar(
        r=normalized + [normalized[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name="LQS",
        marker_color="#3b82f6",
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                     title=f"Total: {row['lqs_total']}/100")
    st.plotly_chart(fig, use_container_width=True)

    # Raw scores table
    score_df = pd.DataFrame({
        "Component": categories,
        "Score": values,
        "Max": max_scores,
        "%": [f"{n:.0f}%" for n in normalized],
    })
    st.dataframe(score_df, hide_index=True, use_container_width=True)

st.divider()

# --- Content change events ---
st.subheader("📝 Content Change Events")
changes = fetch("content_change_events", order_col="snapshot_date")
if changes:
    df_c = pd.DataFrame(changes)
    df_c["product"] = df_c["asin"].map(lambda a: asins_meta.get(a, {}).get("product_name", a)[:40])
    st.dataframe(df_c[["snapshot_date", "product", "change_area", "change_level", "diff_summary"]],
                hide_index=True, use_container_width=True)
else:
    st.info("Chưa có content change event nào.")

# --- Image change events ---
st.subheader("🖼️ Image Change Events")
img_changes = fetch("image_change_events")
if img_changes:
    df_i = pd.DataFrame(img_changes)
    st.dataframe(df_i[["snapshot_date", "asin", "hash_distance", "change_flag"]],
                hide_index=True, use_container_width=True)
else:
    st.info("Chưa có ảnh nào thay đổi (pHash Hamming distance ≤ 10).")
