"""Customer LTV & RFM — lifetime value, predicted LTV, RFM scoring."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from bq import run_query, table, fmt_currency

st.set_page_config(page_title="Customer LTV & RFM", layout="wide")
st.title("💰 Customer LTV & RFM")
st.caption(
    "Lifetime value distribution, predicted LTV, and RFM segmentation — powered by `rpt_customer_ltv`"
)

# ── Data ─────────────────────────────────────────────────────────────────────
df = run_query(f"""
    SELECT
        user_id,
        customer_segment,
        acquisition_channel,
        is_subscriber,
        subscriber_status,
        observed_ltv,
        predicted_12m_ltv,
        avg_order_value,
        orders_per_month,
        rfm_recency_score,
        rfm_frequency_score,
        rfm_monetary_score,
        tenure_months,
        days_since_last_order,
        cohort_month,
        first_order_month,
        last_order_month
    FROM {table('rpt_customer_ltv')}
    WHERE completed_orders > 0
""")
df["cohort_month"] = df["cohort_month"].astype(str)

# ── KPI Tiles ─────────────────────────────────────────────────────────────────
st.subheader("Population Summary")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Customers with Orders", f"{len(df):,}")
c2.metric("Avg Observed LTV", fmt_currency(df.observed_ltv.mean()))
c3.metric("Median Observed LTV", fmt_currency(df.observed_ltv.median()))
c4.metric("Avg Predicted 12m LTV", fmt_currency(df.predicted_12m_ltv.mean()))
c5.metric("Avg Tenure", f"{df.tenure_months.mean():.1f} mo")

st.divider()
col1, col2 = st.columns(2)

# ── LTV Distribution Histogram ─────────────────────────────────────────────────
with col1:
    st.subheader("Observed LTV Distribution")
    ltv_cap = df.observed_ltv.quantile(0.99)
    df_hist = df[df.observed_ltv <= ltv_cap]
    fig_hist = px.histogram(
        df_hist,
        x="observed_ltv",
        nbins=60,
        color="customer_segment",
        template="plotly_dark",
        color_discrete_sequence=["#4F8BF9", "#F9844A", "#4CAF50"],
        barmode="overlay",
        opacity=0.7,
        labels={
            "observed_ltv": "Observed LTV ($)",
            "customer_segment": "Segment",
        },
    )
    fig_hist.update_layout(
        height=380,
        margin=dict(t=10, b=10),
        xaxis=dict(tickprefix="$"),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# ── Observed vs Predicted Scatter ─────────────────────────────────────────────
with col2:
    st.subheader("Observed LTV vs Predicted 12m LTV")
    st.caption(
        "Points above the diagonal are over-predicted; below are under-predicted."
    )
    df_scatter = df[(df.observed_ltv > 0) & (df.predicted_12m_ltv > 0)].sample(
        min(5_000, len(df)), random_state=42
    )
    cap = df_scatter[["observed_ltv", "predicted_12m_ltv"]].quantile(0.99).max()
    fig_sc = px.scatter(
        df_scatter,
        x="observed_ltv",
        y="predicted_12m_ltv",
        color="customer_segment",
        opacity=0.4,
        template="plotly_dark",
        color_discrete_sequence=["#4F8BF9", "#F9844A", "#4CAF50"],
        range_x=[0, cap],
        range_y=[0, cap],
        labels={
            "observed_ltv": "Observed LTV ($)",
            "predicted_12m_ltv": "Predicted 12m LTV ($)",
        },
    )
    fig_sc.add_shape(  # identity line
        type="line",
        x0=0,
        y0=0,
        x1=cap,
        y1=cap,
        line=dict(color="white", dash="dot", width=1),
    )
    fig_sc.update_layout(
        height=380,
        margin=dict(t=10, b=10),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig_sc, use_container_width=True)

st.divider()

# ── RFM Bubble Chart ──────────────────────────────────────────────────────────
st.subheader("RFM Segmentation Bubble Chart")
st.markdown("""
> **x** = Recency (5 = most recent) · **y** = Frequency (5 = most frequent) ·
> **size** = customer count · **facet** = Monetary score ·
> Top-right, large bubbles = best customers.
""")
df_rfm = df.groupby(
    [
        "rfm_recency_score",
        "rfm_frequency_score",
        "rfm_monetary_score",
        "customer_segment",
    ],
    as_index=False,
).agg(
    count=("user_id", "count"),
    avg_ltv=("observed_ltv", "mean"),
)
df_rfm["avg_ltv"] = df_rfm.avg_ltv.round(2)

fig_rfm = px.scatter(
    df_rfm,
    x="rfm_recency_score",
    y="rfm_frequency_score",
    size="count",
    color="customer_segment",
    facet_col="rfm_monetary_score",
    facet_col_spacing=0.05,
    hover_data={"rfm_monetary_score": True, "avg_ltv": True, "count": True},
    template="plotly_dark",
    color_discrete_sequence=["#4F8BF9", "#F9844A", "#4CAF50"],
    size_max=60,
    labels={
        "rfm_recency_score": "Recency Score (1–5)",
        "rfm_frequency_score": "Frequency Score (1–5)",
        "customer_segment": "Segment",
    },
)
fig_rfm.update_layout(
    height=420,
    margin=dict(t=40, b=10),
    legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig_rfm, use_container_width=True)

st.divider()
col3, col4 = st.columns(2)

# ── Avg Predicted LTV by Channel ──────────────────────────────────────────────
with col3:
    st.subheader("Avg Predicted 12m LTV by Channel")
    df_ch = df.groupby(["acquisition_channel", "customer_segment"], as_index=False).agg(
        avg_predicted=("predicted_12m_ltv", "mean")
    )
    df_ch["avg_predicted"] = df_ch.avg_predicted.round(2)
    fig_ch = px.bar(
        df_ch.sort_values("avg_predicted", ascending=True),
        x="avg_predicted",
        y="acquisition_channel",
        color="customer_segment",
        barmode="group",
        orientation="h",
        template="plotly_dark",
        color_discrete_sequence=["#4F8BF9", "#F9844A", "#4CAF50"],
        labels={
            "avg_predicted": "Avg Predicted 12m LTV ($)",
            "acquisition_channel": "Channel",
        },
    )
    fig_ch.update_layout(
        height=380,
        margin=dict(t=10, b=10),
        xaxis=dict(tickprefix="$"),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig_ch, use_container_width=True)

# ── LTV by Cohort (Vintage Analysis) ──────────────────────────────────────────
with col4:
    st.subheader("Avg Observed LTV by Cohort (Vintage)")
    df_coh = (
        df.groupby("cohort_month", as_index=False)
        .agg(avg_ltv=("observed_ltv", "mean"))
        .sort_values("cohort_month")
    )
    df_coh["avg_ltv"] = df_coh.avg_ltv.round(2)
    fig_coh = go.Figure(
        go.Bar(
            x=df_coh.cohort_month,
            y=df_coh.avg_ltv,
            name="Avg LTV",
            marker_color="#4F8BF9",
            text=df_coh.avg_ltv.map(fmt_currency),
            textposition="outside",
        )
    )
    fig_coh.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(t=10, b=10),
        xaxis=dict(tickangle=45),
        yaxis=dict(tickprefix="$"),
    )
    st.plotly_chart(fig_coh, use_container_width=True)
