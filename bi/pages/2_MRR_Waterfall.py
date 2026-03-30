"""MRR Waterfall — decompose net new MRR by movement type."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from bq import run_query, table, fmt_currency

st.set_page_config(page_title="MRR Waterfall", layout="wide")
st.title("💧 MRR Waterfall")
st.caption("New / Expansion / Retained / Contraction / Churned — powered by `rpt_mrr`")

# ── Data ─────────────────────────────────────────────────────────────────────
# Movement breakdown excluding retained (used for waterfall and pie)
df_monthly = run_query(f"""
    SELECT
        revenue_month,
        SUM(new_mrr)         AS new_mrr,
        SUM(expansion_mrr)   AS expansion_mrr,
        SUM(retained_mrr)    AS retained_mrr,
        SUM(contraction_mrr) AS contraction_mrr,
        SUM(churned_mrr)     AS churned_mrr,
        SUM(new_mrr) + SUM(expansion_mrr)
            + SUM(contraction_mrr) + SUM(churned_mrr)
                             AS net_new_mrr,
        SUM(monthly_revenue) AS total_mrr
    FROM {table('rpt_mrr')}
    WHERE mrr_movement_type != 'retained'
    GROUP BY 1
    ORDER BY 1
""")
df_monthly["revenue_month"] = df_monthly["revenue_month"].astype(str)

# Full breakdown including retained (used for stacked area)
df_full = run_query(f"""
    SELECT
        revenue_month,
        SUM(new_mrr)         AS new_mrr,
        SUM(expansion_mrr)   AS expansion_mrr,
        SUM(retained_mrr)    AS retained_mrr,
        SUM(contraction_mrr) AS contraction_mrr,
        SUM(churned_mrr)     AS churned_mrr,
        SUM(monthly_revenue) AS total_mrr
    FROM {table('rpt_mrr')}
    GROUP BY 1
    ORDER BY 1
""")
df_full["revenue_month"] = df_full["revenue_month"].astype(str)

# ── Month selector ────────────────────────────────────────────────────────────
months = df_monthly["revenue_month"].tolist()
selected_month = st.selectbox(
    "Select month for waterfall", months, index=len(months) - 1
)
row = df_monthly[df_monthly.revenue_month == selected_month].iloc[0]
row_full = df_full[df_full.revenue_month == selected_month].iloc[0]

# ── Single-month Waterfall ────────────────────────────────────────────────────
st.subheader(f"MRR Waterfall — {selected_month}")

labels = ["Beginning MRR", "New", "Expansion", "Contraction", "Churned", "Net New MRR"]
values = [
    row.total_mrr - row.net_new_mrr,
    row.new_mrr,
    row.expansion_mrr,
    row.contraction_mrr,
    row.churned_mrr,
    row.net_new_mrr,
]
measure = ["absolute", "relative", "relative", "relative", "relative", "total"]
text_vals = [fmt_currency(v) for v in values]

fig_wf = go.Figure(
    go.Waterfall(
        orientation="v",
        measure=measure,
        x=labels,
        y=values,
        text=text_vals,
        textposition="outside",
        connector=dict(line=dict(color="#666", width=1, dash="dot")),
        increasing=dict(marker_color="#4CAF50"),
        decreasing=dict(marker_color="#F44336"),
        totals=dict(marker_color="#4F8BF9"),
    )
)
fig_wf.update_layout(
    template="plotly_dark",
    height=420,
    margin=dict(t=20, b=20),
    yaxis=dict(tickprefix="$", tickformat=".2s"),
)
st.plotly_chart(fig_wf, use_container_width=True)

st.divider()
col1, col2 = st.columns(2)

# ── Stacked Area — all components ─────────────────────────────────────────────
with col1:
    st.subheader("MRR Components Over Time (Stacked)")
    pos_components = [
        ("New MRR", "new_mrr", "#4CAF50"),
        ("Expansion MRR", "expansion_mrr", "#8BC34A"),
        ("Retained MRR", "retained_mrr", "#4F8BF9"),
    ]
    neg_components = [
        ("Contraction MRR", "contraction_mrr", "#FF9800"),
        ("Churned MRR", "churned_mrr", "#F44336"),
    ]
    fig_area = go.Figure()
    for label, col, color in pos_components:
        fig_area.add_trace(
            go.Scatter(
                x=df_full.revenue_month,
                y=df_full[col],
                name=label,
                stackgroup="pos",
                line=dict(color=color, width=0),
                fillcolor=color,
            )
        )
    for label, col, color in neg_components:
        fig_area.add_trace(
            go.Scatter(
                x=df_full.revenue_month,
                y=df_full[col],
                name=label,
                stackgroup="neg",
                line=dict(color=color, width=0),
                fillcolor=color,
            )
        )
    fig_area.update_layout(
        template="plotly_dark",
        height=360,
        margin=dict(t=10, b=10),
        yaxis=dict(tickprefix="$", tickformat=".2s"),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig_area, use_container_width=True)

# ── Pie — latest month movement mix ──────────────────────────────────────────
with col2:
    st.subheader(f"Movement Mix — {selected_month}")
    pie_labels = ["New", "Expansion", "Retained", "Contraction", "Churned"]
    pie_vals = [
        abs(row.new_mrr),
        abs(row.expansion_mrr),
        abs(row_full.retained_mrr),
        abs(row.contraction_mrr),
        abs(row.churned_mrr),
    ]
    pie_colors = ["#4CAF50", "#8BC34A", "#4F8BF9", "#FF9800", "#F44336"]
    fig_pie = go.Figure(
        go.Pie(
            labels=pie_labels,
            values=pie_vals,
            marker=dict(colors=pie_colors),
            textinfo="label+percent",
            hole=0.4,
        )
    )
    fig_pie.update_layout(
        template="plotly_dark",
        height=360,
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Net New MRR Trend ─────────────────────────────────────────────────────────
st.subheader("Net New MRR Trend")
colors_net = ["#4CAF50" if v >= 0 else "#F44336" for v in df_monthly.net_new_mrr]
fig_net = go.Figure(
    go.Bar(
        x=df_monthly.revenue_month,
        y=df_monthly.net_new_mrr,
        marker_color=colors_net,
        name="Net New MRR",
    )
)
fig_net.add_hline(y=0, line_color="white", line_width=0.5)
fig_net.update_layout(
    template="plotly_dark",
    height=300,
    margin=dict(t=10, b=10),
    yaxis=dict(tickprefix="$", tickformat=".2s"),
)
st.plotly_chart(fig_net, use_container_width=True)
