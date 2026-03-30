"""Revenue by Segment — P&L decomposed by channel, category, country."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from bq import run_query, table, fmt_currency

st.set_page_config(page_title="Revenue by Segment", layout="wide")
st.title("💵 Revenue by Segment")
st.caption(
    "Revenue decomposed by segment, channel, category, country — powered by `rpt_revenue_by_segment`"
)

# ── Data ─────────────────────────────────────────────────────────────────────
df = run_query(f"""
    SELECT *
    FROM {table('rpt_revenue_by_segment')}
    ORDER BY billing_month
""")
df["billing_month"] = df["billing_month"].astype(str)

# ── Filters ───────────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns(2)
with col_f1:
    segments = ["All"] + sorted(df.customer_segment.dropna().unique().tolist())
    seg = st.selectbox("Customer Segment", segments)
with col_f2:
    categories = ["All"] + sorted(df.category.dropna().unique().tolist())
    cat = st.selectbox("Product Category", categories)

df_f = df.copy()
if seg != "All":
    df_f = df_f[df_f.customer_segment == seg]
if cat != "All":
    df_f = df_f[df_f.category == cat]

# ── Revenue by Segment Over Time ──────────────────────────────────────────────
st.subheader("Revenue by Customer Segment Over Time")
df_seg_time = df_f.groupby(["billing_month", "customer_segment"], as_index=False).agg(
    total_revenue=("total_revenue", "sum")
)
fig1 = px.area(
    df_seg_time,
    x="billing_month",
    y="total_revenue",
    color="customer_segment",
    template="plotly_dark",
    color_discrete_sequence=["#4F8BF9", "#F9844A", "#4CAF50"],
    labels={
        "total_revenue": "Revenue ($)",
        "billing_month": "Month",
        "customer_segment": "Segment",
    },
)
fig1.update_layout(
    height=320,
    margin=dict(t=10, b=10),
    yaxis=dict(tickprefix="$", tickformat=".2s"),
    legend=dict(orientation="h", y=1.05),
)
st.plotly_chart(fig1, use_container_width=True)

st.divider()
col1, col2 = st.columns(2)

# ── Gross Margin % by Category ────────────────────────────────────────────────
with col1:
    st.subheader("Gross Margin % by Category")
    df_cat = (
        df_f.groupby("category", as_index=False)
        .agg(
            total_revenue=("total_revenue", "sum"),
            total_gross_margin=("total_gross_margin", "sum"),
        )
        .assign(
            gm_pct=lambda x: (x.total_gross_margin / x.total_revenue * 100).round(1)
        )
        .sort_values("gm_pct", ascending=True)
    )
    df_cat["gm_pct"] = df_cat["gm_pct"].replace([float("inf"), float("-inf")], float("nan"))
    bar_colors = [
        "#4CAF50" if v > 40 else "#FF9800" if v > 25 else "#F44336"
        for v in df_cat.gm_pct
    ]
    fig2 = go.Figure(
        go.Bar(
            y=df_cat.category,
            x=df_cat.gm_pct,
            orientation="h",
            marker_color=bar_colors,
            text=df_cat.gm_pct.map(lambda v: "" if v != v else f"{v:.1f}%"),
            textposition="outside",
        )
    )
    fig2.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(t=10, b=10, r=60),
        xaxis=dict(ticksuffix="%", range=[0, 80]),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Revenue Treemap by Country ─────────────────────────────────────────────────
with col2:
    st.subheader("Revenue by Country")
    df_country = (
        df_f.groupby("country", as_index=False)
        .agg(total_revenue=("total_revenue", "sum"))
        .sort_values("total_revenue", ascending=False)
        .head(40)
    )
    fig3 = px.treemap(
        df_country,
        path=["country"],
        values="total_revenue",
        color="total_revenue",
        color_continuous_scale="Blues",
        template="plotly_dark",
        labels={"total_revenue": "Revenue ($)"},
    )
    fig3.update_layout(
        height=380,
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── Subscriber Revenue Share ───────────────────────────────────────────────────
st.subheader("Subscriber vs Non-Subscriber Orders — Monthly")
df_sub = df_f.groupby("billing_month", as_index=False).agg(
    subscriber_orders=("subscriber_orders", "sum"),
    non_subscriber_orders=("non_subscriber_orders", "sum"),
    subscriber_rev_share=("subscriber_revenue_share", "mean"),
)
df_sub["sub_share_pct"] = (df_sub.subscriber_rev_share * 100).round(1)
fig4 = go.Figure()
fig4.add_trace(
    go.Bar(
        x=df_sub.billing_month,
        y=df_sub.subscriber_orders,
        name="Subscriber Orders",
        marker_color="#4F8BF9",
    )
)
fig4.add_trace(
    go.Bar(
        x=df_sub.billing_month,
        y=df_sub.non_subscriber_orders,
        name="Non-Subscriber Orders",
        marker_color="#FF9800",
    )
)
fig4.add_trace(
    go.Scatter(
        x=df_sub.billing_month,
        y=df_sub.sub_share_pct,
        name="Subscriber Revenue Share %",
        yaxis="y2",
        line=dict(color="white", width=2),
    )
)
fig4.update_layout(
    barmode="stack",
    template="plotly_dark",
    height=320,
    margin=dict(t=10, b=10),
    yaxis=dict(title="Orders"),
    yaxis2=dict(
        title="Subscriber Share %",
        overlaying="y",
        side="right",
        ticksuffix="%",
        range=[0, 100],
    ),
    legend=dict(orientation="h", y=1.05),
)
st.plotly_chart(fig4, use_container_width=True)

# ── Channel Revenue Heatmap ────────────────────────────────────────────────────
st.subheader("Revenue Heatmap — Acquisition Channel × Month")
df_ch_hm = df_f.groupby(["billing_month", "acquisition_channel"], as_index=False).agg(
    total_revenue=("total_revenue", "sum")
)
pivot_ch = df_ch_hm.pivot(
    index="acquisition_channel", columns="billing_month", values="total_revenue"
).fillna(0)
fig5 = go.Figure(
    go.Heatmap(
        z=pivot_ch.values,
        x=pivot_ch.columns.tolist(),
        y=pivot_ch.index.tolist(),
        colorscale="Blues",
        colorbar=dict(title="Revenue ($)", tickformat="$.2s"),
        hoverongaps=False,
    )
)
fig5.update_layout(
    template="plotly_dark",
    height=300,
    margin=dict(t=10, b=10),
    xaxis=dict(tickangle=45),
)
st.plotly_chart(fig5, use_container_width=True)
