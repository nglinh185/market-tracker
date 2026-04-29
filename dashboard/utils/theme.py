"""
Shared theme + plotly defaults for dashboard pages.
Import: from utils.theme import PALETTE, apply_plotly_theme, sentiment_colors, tier_colors
"""
import plotly.io as pio
import plotly.graph_objects as go


# Brand palette (kept in sync with .streamlit/config.toml primaryColor)
PRIMARY = "#2563eb"      # blue-600
ACCENT = "#0ea5e9"       # sky-500
POSITIVE = "#22c55e"     # green-500
WARNING = "#f59e0b"      # amber-500
NEGATIVE = "#ef4444"     # red-500
NEUTRAL = "#94a3b8"      # slate-400
MUTED = "#cbd5e1"        # slate-300

# Categorical sequence for Plotly (≤8 distinct series; cycle gracefully)
PALETTE = [
    "#2563eb", "#22c55e", "#f59e0b", "#ef4444",
    "#8b5cf6", "#0ea5e9", "#ec4899", "#14b8a6",
]

# Domain-specific maps (used by px.scatter / px.bar `color_discrete_map=...`)
SENTIMENT_COLORS = {
    "positive": POSITIVE,
    "negative": NEGATIVE,
    "neutral":  NEUTRAL,
    "mixed":    WARNING,
}

TIER_COLORS = {
    "entry":   POSITIVE,
    "mid":     WARNING,
    "premium": NEGATIVE,
}

ALERT_SEVERITY_COLORS = {
    "high":   NEGATIVE,
    "medium": WARNING,
    "low":    POSITIVE,
}


def apply_plotly_theme() -> None:
    """Register a Plotly template named 'mt' and set as default. Idempotent."""
    if "mt" not in pio.templates:
        pio.templates["mt"] = go.layout.Template(
            layout=dict(
                colorway=PALETTE,
                font=dict(family="Inter, system-ui, sans-serif", size=13, color="#0f172a"),
                paper_bgcolor="white",
                plot_bgcolor="white",
                hovermode="x unified",
                hoverlabel=dict(bgcolor="white", font_size=12),
                margin=dict(t=50, l=10, r=10, b=10),
                xaxis=dict(gridcolor="#f1f5f9", zeroline=False),
                yaxis=dict(gridcolor="#f1f5f9", zeroline=False),
                legend=dict(bgcolor="rgba(255,255,255,0.6)", borderwidth=0),
            )
        )
    pio.templates.default = "mt"
