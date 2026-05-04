"""Page 5: Sentiment & Reviews — RoBERTa + aspects + AI summaries."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db import fetch, latest_snapshot_date, get_asins_with_metadata

st.set_page_config(page_title="Sentiment & Reviews", page_icon="💬", layout="wide")

st.title("💬 Sentiment & Reviews Analysis")
st.caption("RoBERTa sentiment (HuggingFace) + Amazon aspect-based summaries")

asins_meta = get_asins_with_metadata()

# --- ASIN selector — only show ASINs that actually have review data ---
@st.cache_data(ttl=300)
def _asins_with_reviews() -> set[str]:
    rows = fetch("reviews_raw", columns="asin", limit=50000)
    return {r["asin"] for r in rows if r.get("asin")}

reviewed = _asins_with_reviews()
asin_opts = {
    f"{m.get('product_name', a)[:60]} ({a})": a
    for a, m in asins_meta.items()
    if m.get("category") and a in reviewed
}

if not asin_opts:
    st.warning(
        "Chưa có ASIN nào có review data. "
        "Chạy `python scripts/ingest_reviews.py` để pull reviews cho watchlist ASINs."
    )
    st.stop()

st.caption(f"📦 {len(asin_opts)} ASIN có review data (watchlist).")
selected_label = st.selectbox("Select product", options=list(asin_opts.keys()))
selected_asin = asin_opts[selected_label]

# --- Overall sentiment metrics ---
reviews = fetch("reviews_raw", filters={"asin": selected_asin},
               columns="sentiment_label,sentiment_score,rating,review_date,verified,helpful_votes",
               limit=10000)

col1, col2, col3, col4 = st.columns(4)

if reviews:
    df_r = pd.DataFrame(reviews)
    analyzed = df_r[df_r["sentiment_label"].notna()]

    col1.metric("Total Reviews", len(df_r))
    col2.metric("Analyzed (RoBERTa)", len(analyzed))
    if not analyzed.empty:
        avg_score = analyzed["sentiment_score"].mean()
        col3.metric("Avg Sentiment", f"{avg_score:+.3f}",
                   "📈 Positive" if avg_score > 0.1 else "📉 Negative" if avg_score < -0.1 else "➖ Neutral")
        pos_pct = (analyzed["sentiment_label"] == "positive").mean() * 100
        col4.metric("Positive %", f"{pos_pct:.0f}%")

st.divider()

# --- Sentiment distribution ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Sentiment Distribution")
    if reviews:
        analyzed = pd.DataFrame(reviews)
        analyzed = analyzed[analyzed["sentiment_label"].notna()]
        if not analyzed.empty:
            counts = analyzed["sentiment_label"].value_counts()
            fig = px.pie(values=counts.values, names=counts.index,
                        color=counts.index,
                        color_discrete_map={"positive": "#22c55e",
                                          "neutral": "#94a3b8",
                                          "negative": "#ef4444"},
                        hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu sentiment.")

with col_b:
    st.subheader("Rating Distribution")
    if reviews:
        df_rt = pd.DataFrame(reviews)
        if "rating" in df_rt.columns:
            rt_counts = df_rt["rating"].value_counts().sort_index()
            fig = px.bar(x=rt_counts.index.astype(str) + "★", y=rt_counts.values,
                        labels={"x": "Stars", "y": "Count"}, color=rt_counts.values,
                        color_continuous_scale="Viridis")
            st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Aspect-based sentiment (from web_wanderer) ---
st.subheader("🔍 Aspect Sentiment (Amazon AI)")
aspects_rows = fetch("reviews_raw", filters={"asin": selected_asin},
                    columns="aspects_json", limit=1)
if aspects_rows and aspects_rows[0].get("aspects_json"):
    aspects = aspects_rows[0]["aspects_json"]
    df_a = pd.DataFrame(aspects)
    if not df_a.empty:
        df_a = df_a.sort_values("mentions", ascending=True)
        fig = px.bar(df_a, x="mentions", y="name", orientation="h",
                    color="sentiment",
                    color_discrete_map={"positive": "#22c55e",
                                       "negative": "#ef4444",
                                       "mixed": "#f59e0b"},
                    hover_data=["positive", "negative"])
        st.plotly_chart(fig, use_container_width=True)

        # Aspect summary table
        df_disp = df_a[["name", "sentiment", "mentions", "summary"]].sort_values(
            "mentions", ascending=False)
        st.dataframe(df_disp, hide_index=True, use_container_width=True)
else:
    st.info("ASIN này không có aspect data.")

st.divider()

# --- AI Summary from Amazon ---
st.subheader("🤖 Amazon AI Summary")
summary = fetch("product_review_summary", filters={"asin": selected_asin}, limit=1)
if summary:
    s = summary[0]
    st.info(s.get("ai_summary", "N/A"))

    # Rating breakdown
    pcts = {k.replace("pct_", "").replace("_", " ").title(): s.get(k) for k in
           ["pct_five_stars", "pct_four_stars", "pct_three_stars", "pct_two_stars", "pct_one_star"]}
    pcts = {k: v for k, v in pcts.items() if v is not None}
    if pcts:
        fig = px.bar(x=list(pcts.keys()), y=list(pcts.values()),
                    labels={"x": "Rating", "y": "Percentage"},
                    title=f"Total ratings: {s.get('total_ratings', 'N/A'):,}")
        st.plotly_chart(fig, use_container_width=True)
