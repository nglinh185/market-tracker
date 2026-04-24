"""
Amazon Market Tracker Dashboard — Home page.
Run: streamlit run dashboard/app.py
"""
import streamlit as st
from datetime import date
from utils.db import query, latest_snapshot_date

st.set_page_config(
    page_title="Amazon Market Tracker",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Amazon Market Tracker")
st.caption("E-Commerce Intelligence Platform — Thesis Dashboard")

latest = latest_snapshot_date()
st.info(f"**Latest data:** {latest}")

# Summary metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    n_asins = query("SELECT COUNT(DISTINCT asin) as c FROM asins")[0]["c"]
    st.metric("Tracked ASINs", n_asins)

with col2:
    n_categories = 3
    st.metric("Categories", n_categories)

with col3:
    n_reviews = query("SELECT COUNT(*) as c FROM reviews_raw")[0]["c"]
    st.metric("Reviews Collected", f"{n_reviews:,}")

with col4:
    n_alerts = query(
        "SELECT COUNT(*) as c FROM alerts WHERE snapshot_date = %s",
        (latest,),
    )[0]["c"]
    st.metric("Active Alerts Today", n_alerts)

st.divider()

st.markdown("""
## 📖 Dashboard Pages

- **1. Market Overview** — Top 50 rankings, entrant/exit tracking, BSR trends
- **2. Price Intelligence** — K-Means price tiers, discount tracker, price trends
- **3. Brand Competition** — Brand Momentum Score (BMS), market share
- **4. Listing Quality** — LQS radar, image/content change events
- **5. Sentiment & Reviews** — RoBERTa sentiment, aspect analysis, AI summaries
- **6. Alerts Center** — Price drop, stockout, entrant alerts

## 🧠 ML Components

- **K-Means Clustering** (scikit-learn) — Price tiering: entry/mid/premium
- **RoBERTa** (HuggingFace) — Review sentiment analysis
- **Perceptual Hashing** (imagehash) — Product image change detection
- **Prophet** — Short-term price forecasting
""")

st.divider()
st.caption("Built with Streamlit + Plotly • Data: Apify → Supabase")
