import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional

# Global design system
ACCENT = "#2E8B57"        # Sea green — agriculture
WARNING = "#DC143C"       # Crimson — distress / below MSP
NEUTRAL = "#6B7280"       # Grey
TEMPLATE = "plotly_white"

CROP_COLORS = {
    "Wheat": "#F59E0B",
    "Rice": "#10B981",
    "Maize": "#F97316",
    "Sugarcane": "#8B5CF6",
    "Cotton": "#EC4899",
    "Mustard": "#06B6D4",
}
DEFAULT_PALETTE = list(CROP_COLORS.values()) + [
    "#6366F1", "#84CC16", "#EF4444", "#3B82F6", "#A78BFA"
]


def _apply_defaults(fig: go.Figure, caption: str = "") -> go.Figure:
    fig.update_layout(
        template=TEMPLATE,
        font=dict(family="Inter, sans-serif", size=13, color="#1F2937"),
        margin=dict(t=40, b=40, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def chart_daily_arrivals_trend(df: pd.DataFrame) -> go.Figure:
    """Line chart: total daily arrivals over time."""
    daily = df.groupby("date")["total_arrival_quintals"].sum().reset_index()
    fig = px.line(daily, x="date", y="total_arrival_quintals",
                  title="Daily Crop Arrivals",
                  labels={"total_arrival_quintals": "Arrivals (Qtl)", "date": "Date"},
                  color_discrete_sequence=[ACCENT])
    return _apply_defaults(fig, "Track whether inflows are stable or seasonal spikes are emerging.")


def chart_top_mandis(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: top 10 mandis by volume."""
    top = df.nlargest(10, "total_volume_quintals")
    fig = px.bar(top, x="total_volume_quintals", y="mandi_name", orientation="h",
                 title="Top 10 Mandis by Volume",
                 labels={"total_volume_quintals": "Volume (Qtl)", "mandi_name": "Mandi"},
                 color_discrete_sequence=[ACCENT])
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return _apply_defaults(fig)


def chart_price_vs_msp_timeline(df: pd.DataFrame) -> go.Figure:
    """Dual-line chart: modal price vs MSP with below-MSP region shaded red."""
    daily = df.groupby("date").agg(
        modal_price=("modal_price", "mean"),
        msp=("msp", "mean")
    ).reset_index().sort_values("date")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["modal_price"], mode="lines",
                             name="Avg Modal Price", line=dict(color=ACCENT, width=2)))
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["msp"], mode="lines",
                             name="Avg MSP", line=dict(color=WARNING, width=2, dash="dash")))

    # Shade below-MSP region
    fig.add_trace(go.Scatter(
        x=pd.concat([daily["date"], daily["date"][::-1]]),
        y=pd.concat([daily["msp"], daily["modal_price"][::-1]]),
        fill="toself", fillcolor="rgba(220,20,60,0.1)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip", name="Below MSP Region",
        showlegend=True
    ))
    fig.update_layout(title="Modal Price vs MSP Over Time",
                      xaxis_title="Date", yaxis_title="Price (₹/Qtl)")
    return _apply_defaults(fig)


def chart_msp_gap_by_district(df: pd.DataFrame) -> go.Figure:
    """Bar chart: average MSP gap % by district, ranked."""
    df = df.dropna(subset=["district", "msp_gap"])
    grp = df.groupby("district")["msp_gap"].mean().reset_index()
    grp = grp.sort_values("msp_gap")
    grp["color"] = grp["msp_gap"].apply(lambda x: WARNING if x < 0 else ACCENT)
    fig = px.bar(grp, x="msp_gap", y="district", orientation="h",
                 title="MSP Gap by District (₹/Qtl — negative = below MSP)",
                 labels={"msp_gap": "Avg MSP Gap (₹)", "district": "District"},
                 color="msp_gap",
                 color_continuous_scale=[[0, WARNING], [0.5, "#FBBF24"], [1, ACCENT]])
    fig.update_layout(coloraxis_showscale=False,
                      yaxis={"categoryorder": "total ascending"})
    return _apply_defaults(fig)


def chart_crop_stacked_area(df: pd.DataFrame) -> go.Figure:
    """Stacked area chart: crop-wise arrivals over time."""
    daily = df.groupby(["date", "crop"])["total_arrival_quintals"].sum().reset_index()
    fig = px.area(daily, x="date", y="total_arrival_quintals", color="crop",
                  title="Crop-wise Arrival Composition",
                  labels={"total_arrival_quintals": "Arrivals (Qtl)", "date": "Date"},
                  color_discrete_map=CROP_COLORS)
    return _apply_defaults(fig)


def chart_anomaly_band(df: pd.DataFrame) -> go.Figure:
    """Daily arrivals with rolling ±2σ anomaly band and glut markers."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    daily = df.groupby("date")["total_arrival_quintals"].sum().reset_index().sort_values("date")
    daily["rolling_mean"] = daily["total_arrival_quintals"].rolling(7, min_periods=1).mean()
    daily["rolling_std"] = daily["total_arrival_quintals"].rolling(7, min_periods=1).std().fillna(0)
    daily["upper"] = daily["rolling_mean"] + 2 * daily["rolling_std"]
    daily["lower"] = (daily["rolling_mean"] - 2 * daily["rolling_std"]).clip(lower=0)
    daily["is_anomaly"] = daily["total_arrival_quintals"] > daily["upper"]

    fig = go.Figure()
    # Band
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["upper"], mode="lines",
                             line=dict(width=0), showlegend=False, name="Upper Band"))
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["lower"], mode="lines",
                             fill="tonexty", fillcolor="rgba(46,139,87,0.15)",
                             line=dict(width=0), name="±2σ Band"))
    # Main line
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["total_arrival_quintals"], mode="lines",
                             name="Daily Arrivals", line=dict(color=ACCENT, width=2)))
    # Anomalies
    anomalies = daily[daily["is_anomaly"]]
    fig.add_trace(go.Scatter(x=anomalies["date"], y=anomalies["total_arrival_quintals"],
                             mode="markers", marker=dict(color=WARNING, size=10, symbol="x"),
                             name="Anomaly (>2σ)"))
    fig.update_layout(title="Arrival Anomaly Detection (Rolling 7-day ±2σ)",
                      xaxis_title="Date", yaxis_title="Arrivals (Qtl)")
    return _apply_defaults(fig)


def chart_lag_correlation(df_lag: pd.DataFrame, best_lag: int) -> go.Figure:
    """Bar chart: lag-N correlation between rainfall and arrivals."""
    colors = [WARNING if i == best_lag else NEUTRAL for i in df_lag["lag"]]
    fig = px.bar(df_lag, x="lag", y="correlation",
                 title=f"Rainfall vs Arrival Correlation by Lag (Best: Lag-{best_lag})",
                 labels={"lag": "Lag (days)", "correlation": "Pearson r"})
    fig.update_traces(marker_color=colors)
    fig.add_hline(y=0, line_dash="dash", line_color=NEUTRAL)
    return _apply_defaults(fig)


def chart_rainfall_arrivals_dual(df: pd.DataFrame) -> go.Figure:
    """Dual-axis chart: rainfall (bars) and arrivals (line)."""
    daily = df.groupby("date").agg(
        arrivals=("total_arrival_quintals", "sum"),
        rain=("avg_rain_mm", "mean")
    ).reset_index().sort_values("date")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=daily["date"], y=daily["rain"], name="Rainfall (mm)",
                         marker_color="rgba(59,130,246,0.5)", yaxis="y2"))
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["arrivals"], mode="lines",
                             name="Arrivals (Qtl)", line=dict(color=ACCENT, width=2), yaxis="y"))
    fig.update_layout(
        title="Daily Rainfall vs Crop Arrivals",
        yaxis=dict(title="Arrivals (Qtl)", side="left"),
        yaxis2=dict(title="Rainfall (mm)", side="right", overlaying="y"),
        legend=dict(x=0.01, y=0.99)
    )
    return _apply_defaults(fig)


def chart_transit_by_warehouse(df: pd.DataFrame) -> go.Figure:
    """Bar chart: avg transit time and delay rate by warehouse."""
    grp = df.groupby("destination_warehouse").agg(
        avg_transit=("transit_hours", "mean"),
        trips=("trip_id", "count"),
        delayed=("is_delayed", "sum")
    ).reset_index()
    grp["delay_rate_pct"] = grp["delayed"] / grp["trips"] * 100

    fig = go.Figure()
    fig.add_trace(go.Bar(x=grp["destination_warehouse"], y=grp["avg_transit"],
                         name="Avg Transit (hrs)", marker_color=ACCENT))
    fig.add_trace(go.Scatter(x=grp["destination_warehouse"], y=grp["delay_rate_pct"],
                             mode="lines+markers", name="Delay Rate (%)",
                             yaxis="y2", line=dict(color=WARNING, width=2)))
    fig.update_layout(
        title="Transit Time & Delay Rate by Warehouse",
        yaxis=dict(title="Avg Transit Hours"),
        yaxis2=dict(title="Delay Rate (%)", overlaying="y", side="right")
    )
    return _apply_defaults(fig)


def chart_transit_distribution(df: pd.DataFrame) -> go.Figure:
    """Histogram: transit hour distribution."""
    fig = px.histogram(df, x="transit_hours", nbins=40, title="Transit Time Distribution",
                       labels={"transit_hours": "Transit Hours"},
                       color_discrete_sequence=[ACCENT])
    return _apply_defaults(fig)
