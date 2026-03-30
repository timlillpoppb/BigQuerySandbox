"""Churn Analysis — subscriber & revenue churn by segment."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from bq import run_query, table, fmt_pct, fmt_currency

st.set_page_config(page_title="Churn Analysis", layout="wide")
st.title("📉 Churn Analysis")
st.caption("Monthly churn decomposed by segment — powered by `rpt_churn`")

# ── Data ─────────────────────────────────────────────────────────────────────
df = run_query(f"""
    SELECT *
    FROM {table('rpt_churn')}
    ORDER BY cohort_month, customer_segment
""")
df["cohort_month"] = df["cohort_month"].astype(str)

# Aggregate across segments; recalculate rates from totals.
# Use float("nan") not None — None converts series to object dtype and breaks .round().
df_total = df.groupby("cohort_month", as_index=False).agg(
    active_subscribers=("active_subscribers", "sum"),
    new_subscribers=("new_subscribers", "sum"),
    churned_subscribers=("churned_subscribers", "sum"),
    prior_active_subscribers=("prior_active_subscribers", "sum"),
    total_mrr=("total_mrr", "sum"),
    new_mrr=("new_mrr", "sum"),
    churned_mrr=("churned_mrr", "sum"),
    retained_mrr=("retained_mrr", "sum"),
    expansion_mrr=("expansion_mrr", "sum"),
    contraction_mrr=("contraction_mrr", "sum"),
)
df_total["subscriber_churn_rate"] = (
    df_total.churned_subscribers
    / df_total.prior_active_subscribers.replace(0, float("nan"))
)
df_total["revenue_churn_rate"] = (
    df_total.churned_mrr.abs() / df_total.total_mrr.replace(0, float("nan"))
)
df_total["net_revenue_retention_rate"] = (
    df_total.retained_mrr + df_total.expansion_mrr
) / df_total.total_mrr.replace(0, float("nan"))

latest = df_total.iloc[-1]

# ── KPI Tiles ─────────────────────────────────────────────────────────────────
st.subheader("Latest Month Snapshot")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Subscriber Churn Rate", fmt_pct(latest.subscriber_churn_rate))
c2.metric("Revenue Churn Rate", fmt_pct(latest.revenue_churn_rate))
c3.metric("NRR", fmt_pct(latest.net_revenue_retention_rate))
c4.metric(
    "Net Subscriber Change",
    f"{int(latest.new_subscribers - latest.churned_subscribers):+,}",
)

st.divider()
col1, col2 = st.columns(2)

# ── Churn Rate Dual-axis ──────────────────────────────────────────────────────
with col1:
    st.subheader("Subscriber & Revenue Churn Rate")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_total.cohort_month,
            y=(df_total.subscriber_churn_rate * 100).round(2),
            name="Subscriber Churn %",
            line=dict(color="#F44336", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_total.cohort_month,
            y=(df_total.revenue_churn_rate * 100).round(2),
            name="Revenue Churn %",
            line=dict(color="#FF9800", width=2, dash="dot"),
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=320,
        margin=dict(t=10, b=10),
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── NRR ───────────────────────────────────────────────────────────────────────
with col2:
    st.subheader("Net Revenue Retention (NRR)")
    fig2 = go.Figure()
    fig2.add_trace(
        go.Scatter(
            x=df_total.cohort_month,
            y=(df_total.net_revenue_retention_rate * 100).round(2),
            name="NRR %",
            line=dict(color="#4F8BF9", width=2),
            fill="tozeroy",
            fillcolor="rgba(79,139,249,0.15)",
        )
    )
    fig2.add_hline(
        y=100,
        line_color="#4CAF50",
        line_dash="dash",
        annotation_text="100% = perfect retention",
        annotation_position="bottom right",
    )
    fig2.update_layout(
        template="plotly_dark",
        height=320,
        margin=dict(t=10, b=10),
        yaxis=dict(ticksuffix="%"),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Subscriber Waterfall ──────────────────────────────────────────────────────
st.subheader("Subscriber Growth — New vs Churned")
net_change = df_total.new_subscribers - df_total.churned_subscribers
fig3 = go.Figure()
fig3.add_trace(
    go.Bar(
        x=df_total.cohort_month,
        y=df_total.new_subscribers,
        name="New Subscribers",
        marker_color="#4CAF50",
    )
)
fig3.add_trace(
    go.Bar(
        x=df_total.cohort_month,
        y=-df_total.churned_subscribers,
        name="Churned Subscribers",
        marker_color="#F44336",
    )
)
fig3.add_trace(
    go.Scatter(
        x=df_total.cohort_month,
        y=net_change,
        name="Net Change",
        mode="lines+markers",
        line=dict(color="white", width=2),
    )
)
fig3.update_layout(
    barmode="relative",
    template="plotly_dark",
    height=350,
    margin=dict(t=10, b=10),
    legend=dict(orientation="h", y=1.05),
)
st.plotly_chart(fig3, use_container_width=True)

# ── Churn by Segment ──────────────────────────────────────────────────────────
st.subheader("Churn Rate by Customer Segment — Latest 6 Months")
months_recent = sorted(df["cohort_month"].unique())[-6:]
df_seg = df[df.cohort_month.isin(months_recent)].copy()
df_seg["churn_pct"] = (df_seg.subscriber_churn_rate * 100).round(2)
fig4 = px.bar(
    df_seg,
    x="cohort_month",
    y="churn_pct",
    color="customer_segment",
    barmode="group",
    template="plotly_dark",
    color_discrete_sequence=["#4F8BF9", "#F9844A", "#4CAF50"],
    labels={
        "churn_pct": "Subscriber Churn %",
        "cohort_month": "Month",
        "customer_segment": "Segment",
    },
)
fig4.update_layout(
    height=350,
    margin=dict(t=10, b=10),
    yaxis=dict(ticksuffix="%"),
    legend=dict(orientation="h", y=1.05),
)
st.plotly_chart(fig4, use_container_width=True)

# ── MRR Summary ───────────────────────────────────────────────────────────────
st.subheader("MRR Summary — Latest 6 Months")
df_mrr = df_total.tail(6)[
    [
        "cohort_month",
        "total_mrr",
        "new_mrr",
        "churned_mrr",
        "retained_mrr",
        "expansion_mrr",
    ]
].copy()
df_mrr_disp = df_mrr.copy()
for col in ["total_mrr", "new_mrr", "churned_mrr", "retained_mrr", "expansion_mrr"]:
    df_mrr_disp[col] = df_mrr_disp[col].map(fmt_currency)
df_mrr_disp.columns = [
    "Month",
    "Total MRR",
    "New MRR",
    "Churned MRR",
    "Retained MRR",
    "Expansion MRR",
]
st.dataframe(df_mrr_disp, use_container_width=True, hide_index=True)
