"""Page 3: Brand Competition — BMS scores + market share."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db import fetch, latest_snapshot_date, get_asins_with_metadata

st.set_page_config(page_title="Brand Competition", page_icon="🏆", layout="wide")

st.title("🏆 Brand Competition")
st.caption("Brand Momentum Score (BMS) = 0.5·BSR velocity + 0.3·review velocity + 0.2·sentiment")

latest = latest_snapshot_date()
asins_meta = get_asins_with_metadata()

CATEGORIES = {"gaming_keyboard": "🎮 Gaming Keyboards",
              "true_wireless_earbuds": "🎧 True Wireless Earbuds",
              "portable_charger": "🔋 Portable Chargers"}
cat = st.selectbox("Category", options=list(CATEGORIES.keys()),
                   format_func=lambda x: CATEGORIES[x])

# --- Brand Market Share ---
st.subheader("📊 Brand Market Share in Top 50")
rankings = fetch("category_rankings",
                filters={"snapshot_date": latest, "browse_node": cat})
if rankings:
    df_r = pd.DataFrame(rankings)
    df_r["brand"] = df_r["brand"].fillna("Unknown")
    brand_counts = df_r.groupby("brand").size().reset_index(name="count")
    brand_counts = brand_counts.sort_values("count", ascending=True).tail(15)
    fig = px.bar(brand_counts, x="count", y="brand", orientation="h",
                color="count", color_continuous_scale="Blues",
                title=f"Brand presence in Top 50 ({len(df_r)} products)")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- BMS Score Table ---
st.subheader("🚀 Brand Momentum Score (Watchlist)")
bms = fetch("brand_momentum_daily", filters={"snapshot_date": latest})
if bms:
    df_bms = pd.DataFrame(bms)
    df_bms["product"] = df_bms["asin"].map(lambda a: asins_meta.get(a, {}).get("product_name", a)[:40])
    df_bms["brand"] = df_bms["asin"].map(lambda a: asins_meta.get(a, {}).get("brand", ""))
    df_bms["category"] = df_bms["asin"].map(lambda a: asins_meta.get(a, {}).get("category", ""))
    df_bms = df_bms[df_bms["category"] == cat]
    df_bms = df_bms.sort_values("bms_score", ascending=False)

    # Bullet-style bar chart
    fig = px.bar(df_bms, x="bms_score", y="product", orientation="h",
                color="bms_score", color_continuous_scale="RdYlGn",
                range_color=[0, 1],
                hover_data=["bsr_velocity", "review_velocity", "sentiment_score"],
                title="BMS Score (0-1) — higher = better momentum")
    fig.add_vline(x=0.5, line_dash="dash", line_color="gray",
                 annotation_text="Neutral (0.5)")
    st.plotly_chart(fig, use_container_width=True)

    # Top mover
    top = df_bms.iloc[0] if not df_bms.empty else None
    if top is not None:
        st.success(f"🏅 **Top mover:** {top['product']} — BMS {top['bms_score']:.3f}")

st.divider()

# --- BSR Velocity Waterfall ---
st.subheader("📈 BSR Velocity (24h change)")
if bms:
    df_v = pd.DataFrame(bms)
    df_v["product"] = df_v["asin"].map(lambda a: asins_meta.get(a, {}).get("product_name", a)[:30])
    df_v["category"] = df_v["asin"].map(lambda a: asins_meta.get(a, {}).get("category", ""))
    df_v = df_v[(df_v["category"] == cat) & df_v["bsr_velocity"].notna()]
    df_v = df_v.sort_values("bsr_velocity", ascending=False)

    colors = ["#22c55e" if v > 0 else "#ef4444" for v in df_v["bsr_velocity"]]
    fig = go.Figure(go.Bar(x=df_v["bsr_velocity"], y=df_v["product"],
                          orientation="h", marker_color=colors))
    fig.update_layout(title="BSR velocity (% improvement vs yesterday)",
                     xaxis_title="Velocity (+ = improved rank)",
                     yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)
