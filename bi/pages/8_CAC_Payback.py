"""CAC & Payback — LTV:CAC, payback period, channel quality."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from bq import run_query, table, fmt_currency

st.set_page_config(page_title="CAC & Payback", layout="wide")
st.title("🎯 CAC & Payback")
st.caption("""
LTV:CAC ratio and payback period by acquisition channel — powered by `rpt_cac_and_payback`

> **Note:** CAC is proxied by first-order value (actual ad spend not available in this dataset).
> LTV:CAC > 3× and payback < 12 months are typical SaaS benchmarks.
""")

# ── Data ─────────────────────────────────────────────────────────────────────
df = run_query(f"""
    SELECT *
    FROM {table('rpt_cac_and_payback')}
    ORDER BY cohort_month, acquisition_channel
""")
df["cohort_month"] = df["cohort_month"].astype(str)

# Channel-level aggregates
df_agg = df.groupby("acquisition_channel", as_index=False).agg(
    new_subscribers=("new_subscribers", "sum"),
    avg_payback=("estimated_payback_months", "mean"),
    avg_ltv_cac=("ltv_to_first_order_ratio", "mean"),
    avg_predicted_ltv=("avg_predicted_12m_ltv", "mean"),
    avg_rfm=("rfm_composite_score", "mean"),
)
df_agg["avg_payback"] = df_agg.avg_payback.round(1)
df_agg["avg_ltv_cac"] = df_agg.avg_ltv_cac.round(2)
df_agg["avg_predicted_ltv"] = df_agg.avg_predicted_ltv.round(2)
df_agg["avg_rfm"] = df_agg.avg_rfm.round(2)

overall_ltv_cac = round(df["ltv_to_first_order_ratio"].mean(), 2)
overall_payback = round(df["estimated_payback_months"].mean(), 1)
overall_predicted = df["avg_predicted_12m_ltv"].mean()

# ── KPI Tiles ─────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric(
    "Avg LTV:CAC Ratio",
    f"{overall_ltv_cac:.2f}×",
    help="Predicted 12m LTV / First Order Value. >3× is healthy.",
)
c2.metric(
    "Avg Payback Period",
    f"{overall_payback:.1f} months",
    help="First Order Value / Avg Monthly Revenue. <12 months is healthy.",
)
c3.metric("Avg Predicted 12m LTV", fmt_currency(overall_predicted))

st.divider()

# ── LTV:CAC Bubble Chart ──────────────────────────────────────────────────────
st.subheader("LTV:CAC vs Payback Period — by Channel & Cohort")
st.markdown("""
> Each bubble = one channel × cohort combination. **Ideal quadrant: top-left** (high LTV:CAC, fast payback).
> Size = new subscribers acquired.
""")
df_bub = df.copy()
df_bub["ltv_to_first_order_ratio"] = df_bub.ltv_to_first_order_ratio.round(2)
df_bub["estimated_payback_months"] = df_bub.estimated_payback_months.round(1)

fig_bub = px.scatter(
    df_bub,
    x="estimated_payback_months",
    y="ltv_to_first_order_ratio",
    size="new_subscribers",
    color="acquisition_channel",
    hover_name="cohort_month",
    hover_data={
        "new_subscribers": True,
        "avg_predicted_12m_ltv": ":,.2f",
        "rfm_composite_score": ":.2f",
    },
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Bold,
    size_max=40,
    labels={
        "estimated_payback_months": "Estimated Payback (months)",
        "ltv_to_first_order_ratio": "LTV:CAC Ratio",
        "acquisition_channel": "Channel",
    },
)
fig_bub.add_vline(
    x=12,
    line_color="yellow",
    line_dash="dash",
    annotation_text="12mo payback",
    annotation_position="top",
)
fig_bub.add_hline(
    y=3,
    line_color="yellow",
    line_dash="dash",
    annotation_text="3× LTV:CAC",
    annotation_position="right",
)
fig_bub.update_layout(
    height=480,
    margin=dict(t=20, b=20),
    legend=dict(orientation="h", y=1.05),
)
st.plotly_chart(fig_bub, use_container_width=True)

st.divider()
col1, col2 = st.columns(2)

# ── Payback by Channel ────────────────────────────────────────────────────────
with col1:
    st.subheader("Avg Payback Period by Channel")
    df_agg_s = df_agg.sort_values("avg_payback", ascending=True)
    bar_colors = [
        "#4CAF50" if v <= 6 else "#FF9800" if v <= 12 else "#F44336"
        for v in df_agg_s.avg_payback
    ]
    fig_pb = go.Figure(
        go.Bar(
            y=df_agg_s.acquisition_channel,
            x=df_agg_s.avg_payback,
            orientation="h",
            marker_color=bar_colors,
            text=df_agg_s.avg_payback.map("{:.1f} mo".format),
            textposition="outside",
        )
    )
    fig_pb.add_vline(
        x=12,
        line_color="yellow",
        line_dash="dash",
        annotation_text="12mo benchmark",
        annotation_position="top",
    )
    fig_pb.update_layout(
        template="plotly_dark",
        height=360,
        margin=dict(t=10, b=10, r=80),
        xaxis=dict(title="Months"),
    )
    st.plotly_chart(fig_pb, use_container_width=True)

# ── Predicted LTV Trend by Channel ────────────────────────────────────────────
with col2:
    st.subheader("Predicted 12m LTV Trend by Cohort")
    df_trend = df.groupby(["cohort_month", "acquisition_channel"], as_index=False).agg(
        avg_predicted_12m_ltv=("avg_predicted_12m_ltv", "mean")
    )
    df_trend["avg_predicted_12m_ltv"] = df_trend.avg_predicted_12m_ltv.round(2)
    fig_trend = px.line(
        df_trend,
        x="cohort_month",
        y="avg_predicted_12m_ltv",
        color="acquisition_channel",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Bold,
        markers=True,
        labels={
            "avg_predicted_12m_ltv": "Avg Predicted 12m LTV ($)",
            "cohort_month": "Cohort Month",
            "acquisition_channel": "Channel",
        },
    )
    fig_trend.update_layout(
        height=360,
        margin=dict(t=10, b=10),
        xaxis=dict(tickangle=45),
        yaxis=dict(tickprefix="$"),
        legend=dict(orientation="h", y=1.1, font=dict(size=9)),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# ── RFM Composite Heatmap ─────────────────────────────────────────────────────
st.subheader("RFM Composite Score Heatmap — Channel × Cohort")
st.markdown("""
> Weighted composite: **Recency × 0.30 + Frequency × 0.35 + Monetary × 0.35** (scale 1–5).
> Higher = better customer quality from that channel in that cohort.
""")
pivot = df.pivot_table(
    index="acquisition_channel",
    columns="cohort_month",
    values="rfm_composite_score",
    aggfunc="mean",
)
pivot_rounded = pivot.round(2)
fig_hm = go.Figure(
    go.Heatmap(
        z=pivot_rounded.values,
        x=pivot_rounded.columns.tolist(),
        y=pivot_rounded.index.tolist(),
        colorscale="RdYlGn",
        text=pivot_rounded.values,
        texttemplate="%{text}",
        textfont=dict(size=9),
        zmin=1,
        zmax=5,
        colorbar=dict(title="RFM Score"),
    )
)
fig_hm.update_layout(
    template="plotly_dark",
    height=max(280, len(pivot) * 45 + 80),
    margin=dict(t=10, b=10, l=120),
    xaxis=dict(tickangle=45),
)
st.plotly_chart(fig_hm, use_container_width=True)
