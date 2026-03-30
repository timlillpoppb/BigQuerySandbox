"""Executive Health — MRR, ARR, ARPU, NRR, churn, growth."""

import sys
import pathlib
import math

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
from bq import run_query, table, fmt_currency, fmt_pct

st.set_page_config(page_title="Executive Health", layout="wide")
st.title("📈 Executive Health")
st.caption(
    "Single source of truth for C-suite metrics — powered by `rpt_subscription_health`"
)

# ── Data ─────────────────────────────────────────────────────────────────────
df = run_query(f"""
    SELECT *
    FROM {table('rpt_subscription_health')}
    ORDER BY revenue_month
""")

df["revenue_month"] = df["revenue_month"].astype(str)
latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) > 1 else latest


def delta_pct(cur, prv) -> str:
    if prv is None or cur is None:
        return ""
    if not math.isfinite(float(prv)) or not math.isfinite(float(cur)):
        return ""
    if prv != 0:
        return f"{((cur - prv) / abs(prv)) * 100:+.1f}%"
    return ""


# ── KPI Tiles ─────────────────────────────────────────────────────────────────
st.subheader("Key Performance Indicators — Latest Month")
c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric(
    "Total MRR",
    fmt_currency(latest.total_mrr),
    delta_pct(latest.total_mrr, prev.total_mrr),
)
c2.metric("ARR", fmt_currency(latest.arr))
c3.metric(
    "Active Subscribers",
    f"{int(latest.active_subscribers):,}",
    delta_pct(latest.active_subscribers, prev.active_subscribers),
)
c4.metric(
    "Subscriber Churn",
    fmt_pct(latest.subscriber_churn_rate),
    delta_pct(latest.subscriber_churn_rate, prev.subscriber_churn_rate),
    delta_color="inverse",
)
c5.metric(
    "Net Revenue Retention",
    fmt_pct(latest.net_revenue_retention_rate),
    delta_pct(latest.net_revenue_retention_rate, prev.net_revenue_retention_rate),
)
c6.metric("ARPU", fmt_currency(latest.arpu), delta_pct(latest.arpu, prev.arpu))

st.divider()

# ── MRR Trend + Growth Rate ───────────────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("MRR & ARR Trend")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.revenue_month,
            y=df.total_mrr,
            name="MRR",
            line=dict(color="#4F8BF9", width=2),
            fill="tozeroy",
            fillcolor="rgba(79,139,249,0.15)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.revenue_month,
            y=df.arr,
            name="ARR",
            line=dict(color="#F9844A", width=2, dash="dot"),
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=320,
        margin=dict(t=10, b=10),
        legend=dict(orientation="h", y=1.05),
        yaxis=dict(tickprefix="$", tickformat=".2s"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.subheader("MRR Growth Rate")
    colors_growth = [
        "#4CAF50" if v >= 0 else "#F44336" for v in df.mrr_growth_rate.fillna(0)
    ]
    fig2 = go.Figure(
        go.Bar(
            x=df.revenue_month,
            y=(df.mrr_growth_rate * 100).round(2),
            marker_color=colors_growth,
            name="MoM Growth %",
        )
    )
    fig2.add_hline(y=0, line_color="white", line_width=0.5)
    fig2.update_layout(
        template="plotly_dark",
        height=320,
        margin=dict(t=10, b=10),
        yaxis=dict(ticksuffix="%"),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── MRR Component Breakdown ───────────────────────────────────────────────────
st.subheader("MRR Component Breakdown (Stacked)")
components = {
    "New MRR": ("new_mrr", "#4CAF50"),
    "Expansion MRR": ("expansion_mrr", "#8BC34A"),
    "Retained MRR": ("retained_mrr", "#4F8BF9"),
    "Contraction MRR": ("contraction_mrr", "#FF9800"),
    "Churned MRR": ("churned_mrr", "#F44336"),
}
fig3 = go.Figure()
for label, (col, color) in components.items():
    fig3.add_trace(
        go.Bar(
            name=label,
            x=df.revenue_month,
            y=df[col],
            marker_color=color,
        )
    )
fig3.update_layout(
    barmode="relative",
    template="plotly_dark",
    height=350,
    margin=dict(t=10, b=10),
    yaxis=dict(tickprefix="$", tickformat=".2s"),
    legend=dict(orientation="h", y=1.05),
)
st.plotly_chart(fig3, use_container_width=True)

# ── NRR + Churn Rates ─────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Net Revenue Retention (NRR)")
    fig4 = go.Figure()
    fig4.add_trace(
        go.Scatter(
            x=df.revenue_month,
            y=df.net_revenue_retention_rate * 100,
            name="NRR %",
            line=dict(color="#4F8BF9", width=2),
            fill="tozeroy",
            fillcolor="rgba(79,139,249,0.15)",
        )
    )
    fig4.add_hline(
        y=100,
        line_color="#4CAF50",
        line_dash="dash",
        annotation_text="100% baseline",
        annotation_position="bottom right",
    )
    fig4.update_layout(
        template="plotly_dark",
        height=300,
        margin=dict(t=10, b=10),
        yaxis=dict(ticksuffix="%"),
    )
    st.plotly_chart(fig4, use_container_width=True)

with col4:
    st.subheader("Churn Rates")
    fig5 = go.Figure()
    fig5.add_trace(
        go.Scatter(
            x=df.revenue_month,
            y=df.subscriber_churn_rate * 100,
            name="Subscriber Churn %",
            line=dict(color="#F44336", width=2),
        )
    )
    fig5.add_trace(
        go.Scatter(
            x=df.revenue_month,
            y=df.revenue_churn_rate * 100,
            name="Revenue Churn %",
            line=dict(color="#FF9800", width=2, dash="dot"),
        )
    )
    fig5.update_layout(
        template="plotly_dark",
        height=300,
        margin=dict(t=10, b=10),
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig5, use_container_width=True)

# ── Session Funnel ────────────────────────────────────────────────────────────
st.subheader("Session Funnel — Monthly")
fig6 = go.Figure()
fig6.add_trace(
    go.Bar(
        x=df.revenue_month,
        y=df.total_sessions,
        name="Total Sessions",
        marker_color="#4F8BF9",
    )
)
fig6.add_trace(
    go.Bar(
        x=df.revenue_month,
        y=df.converting_sessions,
        name="Converting Sessions",
        marker_color="#4CAF50",
    )
)
fig6.add_trace(
    go.Scatter(
        x=df.revenue_month,
        y=df.session_conversion_rate * 100,
        name="Conversion %",
        yaxis="y2",
        line=dict(color="#F9844A", width=2),
    )
)
fig6.update_layout(
    barmode="overlay",
    template="plotly_dark",
    height=320,
    margin=dict(t=10, b=10),
    yaxis=dict(title="Sessions"),
    yaxis2=dict(
        title="Conversion %",
        overlaying="y",
        side="right",
        ticksuffix="%",
    ),
    legend=dict(orientation="h", y=1.05),
)
st.plotly_chart(fig6, use_container_width=True)
