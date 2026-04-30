"""
Generate publication-quality matplotlib figures for the thesis chapters.

Reads from Supabase (read-only) and writes PNGs to ``thesis/figures/``. Run
locally before compiling the LaTeX document.

Figures produced:
    1. price_tier_distribution.png  - violin/strip plot of prices per category x tier
    2. lqs_distribution.png         - horizontal bar of LQS for the 30 watchlist ASINs
    3. bsr_trend.png                - line plot of BSR over the collection window
                                      for the top-5 BMS ASINs
    4. sentiment_distribution.png   - stacked bar of pos/neu/neg ratios per category
    5. alerts_breakdown.png         - grouped bar of alerts by type x severity
    6. entrant_exit_by_category.png - paired bar (entrants vs exits) per category

Usage:
    python scripts/thesis_figures.py
"""
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

import matplotlib.pyplot as plt
import numpy as np

from lib.db import supabase


CATEGORIES = ["gaming_keyboard", "true_wireless_earbuds", "portable_charger"]
PRETTY = {
    "gaming_keyboard": "Gaming Keyboards",
    "true_wireless_earbuds": "True Wireless Earbuds",
    "portable_charger": "Portable Chargers",
}
SHORT = {
    "gaming_keyboard": "Gaming KB",
    "true_wireless_earbuds": "TWS",
    "portable_charger": "Charger",
}
CAT_COLOR = {
    "gaming_keyboard": "#1f77b4",
    "true_wireless_earbuds": "#ff7f0e",
    "portable_charger": "#2ca02c",
}
TIER_COLOR = {"entry": "#9ecae1", "mid": "#3182bd", "premium": "#08519c"}
SENTIMENT_COLOR = {"positive": "#2ca02c", "neutral": "#bdbdbd", "negative": "#d62728"}

FIG_DIR = Path("thesis/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)


def _set_thesis_style() -> None:
    plt.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 200,
        "font.family": "serif",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "legend.fontsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    })


def _latest_date(table: str) -> str | None:
    res = (
        supabase.table(table)
        .select("snapshot_date")
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0]["snapshot_date"] if res.data else None


def _fetch_all(table: str, columns: str, **eq_filters) -> list[dict]:
    rows: list[dict] = []
    page_size = 1000
    start = 0
    while True:
        q = supabase.table(table).select(columns)
        for k, v in eq_filters.items():
            q = q.eq(k, v)
        res = q.range(start, start + page_size - 1).execute()
        chunk = res.data or []
        rows.extend(chunk)
        if len(chunk) < page_size:
            break
        start += page_size
    return rows


def _asin_to_category() -> dict[str, str]:
    rows = _fetch_all("asins", "asin,category")
    return {r["asin"]: r.get("category") for r in rows}


# ─────────────────────────────────────────────────────────────────────
# Figure 1 — Price tier distribution
# ─────────────────────────────────────────────────────────────────────
def fig_price_tier_distribution() -> None:
    snap_date = _latest_date("price_tier_daily")
    rows = (
        supabase.table("price_tier_daily")
        .select("browse_node,price,cluster_name")
        .eq("snapshot_date", snap_date)
        .execute()
    ).data
    if not rows:
        print("[fig] no price_tier_daily data, skipping")
        return

    fig, axes = plt.subplots(1, 3, figsize=(11, 4), sharey=False)
    for ax, cat in zip(axes, CATEGORIES):
        data = defaultdict(list)
        for r in rows:
            if r["browse_node"] != cat:
                continue
            data[r["cluster_name"]].append(float(r["price"]))
        tiers = ["entry", "mid", "premium"]
        positions = list(range(1, len(tiers) + 1))
        box_data = [data.get(t, []) for t in tiers]

        bp = ax.boxplot(
            box_data,
            positions=positions,
            widths=0.55,
            patch_artist=True,
            showfliers=False,
            medianprops=dict(color="black", linewidth=1.4),
        )
        for patch, tier in zip(bp["boxes"], tiers):
            patch.set_facecolor(TIER_COLOR[tier])
            patch.set_edgecolor("#222")
            patch.set_alpha(0.85)

        for i, tier in enumerate(tiers, start=1):
            xs = np.random.normal(loc=i, scale=0.05, size=len(data.get(tier, [])))
            ax.scatter(
                xs,
                data.get(tier, []),
                s=10,
                color="black",
                alpha=0.45,
                zorder=5,
            )

        ax.set_xticks(positions)
        ax.set_xticklabels([t.capitalize() for t in tiers])
        ax.set_title(PRETTY[cat])
        ax.set_ylabel("Price (USD)" if ax is axes[0] else "")

    fig.suptitle(f"K-Means price tier distribution by category (snapshot {snap_date})",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    out = FIG_DIR / "price_tier_distribution.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] {out}")


# ─────────────────────────────────────────────────────────────────────
# Figure 2 — LQS distribution
# ─────────────────────────────────────────────────────────────────────
def fig_lqs_distribution() -> None:
    snap_date = _latest_date("listing_quality_score_daily")
    rows = (
        supabase.table("listing_quality_score_daily")
        .select("asin,lqs_total")
        .eq("snapshot_date", snap_date)
        .execute()
    ).data
    asin_cat = _asin_to_category()

    items = [
        (r["asin"], asin_cat.get(r["asin"]) or "unknown", float(r["lqs_total"]))
        for r in rows
        if r.get("lqs_total") is not None
    ]
    items.sort(key=lambda x: x[2])

    if not items:
        print("[fig] no LQS data, skipping")
        return

    fig, ax = plt.subplots(figsize=(8, 9))
    asins = [i[0] for i in items]
    scores = [i[2] for i in items]
    colors = [CAT_COLOR.get(i[1], "#888888") for i in items]

    ax.barh(asins, scores, color=colors, edgecolor="#222", linewidth=0.5)
    ax.set_xlim(70, 100)
    ax.set_xlabel("Listing Quality Score")
    ax.set_title(f"LQS distribution across 30 watchlist ASINs (snapshot {snap_date})")

    for cat, color in CAT_COLOR.items():
        ax.bar([0], [0], color=color, label=PRETTY[cat])
    ax.legend(loc="lower right", frameon=True)

    overall_mean = float(np.mean(scores))
    ax.axvline(overall_mean, color="#444", linestyle=":", linewidth=1, alpha=0.7)
    ax.text(overall_mean + 0.4, 0.4, f"mean = {overall_mean:.1f}",
            fontsize=8, color="#333")

    fig.tight_layout()
    out = FIG_DIR / "lqs_distribution.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] {out}")


# ─────────────────────────────────────────────────────────────────────
# Figure 3 — BSR trend for top-5 BMS movers
# ─────────────────────────────────────────────────────────────────────
def fig_bsr_trend() -> None:
    snap_date = _latest_date("brand_momentum_daily")
    top_rows = (
        supabase.table("brand_momentum_daily")
        .select("asin,bms_score")
        .eq("snapshot_date", snap_date)
        .order("bms_score", desc=True)
        .limit(5)
        .execute()
    ).data
    top_asins = [r["asin"] for r in top_rows]
    if not top_asins:
        print("[fig] no BMS data, skipping")
        return

    asin_cat = _asin_to_category()
    fig, ax = plt.subplots(figsize=(10, 5))

    palette = plt.cm.tab10(np.linspace(0, 1, len(top_asins)))

    for color, asin in zip(palette, top_asins):
        snaps = (
            supabase.table("daily_snapshots")
            .select("snapshot_date,bsr")
            .eq("asin", asin)
            .order("snapshot_date", desc=False)
            .execute()
        ).data
        xs = [s["snapshot_date"] for s in snaps if s.get("bsr") is not None]
        ys = [int(s["bsr"]) for s in snaps if s.get("bsr") is not None]
        if not xs:
            continue
        cat_short = SHORT.get(asin_cat.get(asin), "?")
        ax.plot(xs, ys, marker="o", linewidth=1.5, markersize=4,
                color=color, label=f"{asin} ({cat_short})")

    ax.invert_yaxis()
    ax.set_ylabel("Best Seller Rank (lower is better)")
    ax.set_xlabel("Date")
    ax.set_title("BSR trajectory — top 5 BMS movers")
    ax.tick_params(axis="x", rotation=30)
    ax.legend(loc="best", frameon=True, fontsize=8)
    fig.tight_layout()
    out = FIG_DIR / "bsr_trend.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] {out}")


# ─────────────────────────────────────────────────────────────────────
# Figure 4 — Sentiment distribution per category (stacked)
# ─────────────────────────────────────────────────────────────────────
def fig_sentiment_distribution() -> None:
    snap_date = _latest_date("review_sentiment_daily")
    rows = (
        supabase.table("review_sentiment_daily")
        .select("asin,positive_ratio,negative_ratio")
        .eq("snapshot_date", snap_date)
        .execute()
    ).data
    asin_cat = _asin_to_category()

    by_cat: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
    for r in rows:
        cat = asin_cat.get(r["asin"])
        if not cat or r.get("positive_ratio") is None or r.get("negative_ratio") is None:
            continue
        pos = float(r["positive_ratio"])
        neg = float(r["negative_ratio"])
        neu = max(0.0, 1.0 - pos - neg)
        by_cat[cat].append((pos, neu, neg))

    if not any(by_cat.values()):
        print("[fig] no sentiment data, skipping")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5))
    cats_with_data = [c for c in CATEGORIES if by_cat.get(c)]
    labels = [PRETTY[c] for c in cats_with_data]
    pos_avg = [float(np.mean([t[0] for t in by_cat[c]])) for c in cats_with_data]
    neu_avg = [float(np.mean([t[1] for t in by_cat[c]])) for c in cats_with_data]
    neg_avg = [float(np.mean([t[2] for t in by_cat[c]])) for c in cats_with_data]

    x = np.arange(len(labels))
    ax.bar(x, pos_avg, color=SENTIMENT_COLOR["positive"], label="Positive",
           edgecolor="white", linewidth=0.5)
    ax.bar(x, neu_avg, bottom=pos_avg, color=SENTIMENT_COLOR["neutral"],
           label="Neutral", edgecolor="white", linewidth=0.5)
    ax.bar(x, neg_avg, bottom=np.array(pos_avg) + np.array(neu_avg),
           color=SENTIMENT_COLOR["negative"], label="Negative",
           edgecolor="white", linewidth=0.5)

    for i, (p, nu, ng) in enumerate(zip(pos_avg, neu_avg, neg_avg)):
        ax.text(i, p / 2, f"{p:.0%}", ha="center", va="center",
                color="white", fontsize=9, fontweight="bold")
        if nu > 0.04:
            ax.text(i, p + nu / 2, f"{nu:.0%}", ha="center", va="center",
                    color="black", fontsize=8)
        if ng > 0.04:
            ax.text(i, p + nu + ng / 2, f"{ng:.0%}", ha="center", va="center",
                    color="white", fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Share of reviews")
    ax.set_ylim(0, 1.05)
    ax.set_title(f"RoBERTa sentiment distribution by category (snapshot {snap_date})")
    ax.legend(loc="upper right", frameon=True)
    ax.yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1.0))
    fig.tight_layout()
    out = FIG_DIR / "sentiment_distribution.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] {out}")


# ─────────────────────────────────────────────────────────────────────
# Figure 5 — Alerts breakdown by type and severity
# ─────────────────────────────────────────────────────────────────────
def fig_alerts_breakdown() -> None:
    rows = _fetch_all("alerts", "alert_type,severity")
    if not rows:
        print("[fig] no alerts data, skipping")
        return

    counts = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if r.get("alert_type") and r.get("severity"):
            counts[r["alert_type"]][r["severity"]] += 1

    types = sorted(counts.keys(), key=lambda t: -sum(counts[t].values()))
    severities = ["high", "medium", "low"]
    sev_color = {"high": "#d62728", "medium": "#ff9f0e", "low": "#9ecae1"}

    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(types))
    width = 0.25

    for i, sev in enumerate(severities):
        vals = [counts[t].get(sev, 0) for t in types]
        offset = (i - 1) * width
        bars = ax.bar(x + offset, vals, width, color=sev_color[sev],
                      label=sev.capitalize(), edgecolor="#222", linewidth=0.4)
        for bar, v in zip(bars, vals):
            if v > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                        str(v), ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(types)
    ax.set_ylabel("Alert count")
    ax.set_title("Alert engine output by type and severity (full window)")
    ax.legend(loc="upper right", frameon=True, title="Severity")
    fig.tight_layout()
    out = FIG_DIR / "alerts_breakdown.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] {out}")


# ─────────────────────────────────────────────────────────────────────
# Figure 6 — Entrant / exit events by category
# ─────────────────────────────────────────────────────────────────────
def fig_entrant_exit() -> None:
    rows = _fetch_all("entrant_exit_events", "browse_node,event_type")
    if not rows:
        print("[fig] no entrant_exit_events data, skipping")
        return

    counts = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if r.get("browse_node") and r.get("event_type"):
            counts[r["browse_node"]][r["event_type"]] += 1

    cats = [c for c in CATEGORIES if c in counts]
    labels = [PRETTY[c] for c in cats]
    entrants = [counts[c].get("entrant", 0) for c in cats]
    exits = [counts[c].get("exit", 0) for c in cats]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 4.5))
    b1 = ax.bar(x - width / 2, entrants, width, color="#2ca02c", label="Entrants",
                edgecolor="#222", linewidth=0.4)
    b2 = ax.bar(x + width / 2, exits, width, color="#d62728", label="Exits",
                edgecolor="#222", linewidth=0.4)

    for bars, vals in [(b1, entrants), (b2, exits)]:
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                    str(v), ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Event count")
    ax.set_title("Entrant / exit events by category (full window)")
    ax.legend(loc="upper right", frameon=True)
    fig.tight_layout()
    out = FIG_DIR / "entrant_exit_by_category.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] {out}")


def main() -> None:
    _set_thesis_style()
    print(f"[Figures] Writing PNGs to {FIG_DIR}/")
    fig_price_tier_distribution()
    fig_lqs_distribution()
    fig_bsr_trend()
    fig_sentiment_distribution()
    fig_alerts_breakdown()
    fig_entrant_exit()
    print(f"[Figures] Done as of {date.today().isoformat()}")


if __name__ == "__main__":
    main()
