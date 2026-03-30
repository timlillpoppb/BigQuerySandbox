"""Cohort Retention — triangle heatmap + retention curves."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from bq import run_query, table

st.set_page_config(page_title="Cohort Retention", layout="wide")
st.title("🔺 Cohort Retention")
st.caption("Classic cohort triangle heatmap — powered by `rpt_cohort_retention`")

# ── Data ─────────────────────────────────────────────────────────────────────
df = run_query(f"""
    SELECT
        FORMAT_DATE('%Y-%m', cohort_month) AS cohort,
        period_number,
        AVG(retention_rate)                AS retention_rate,
        SUM(cohort_size)                   AS cohort_size,
        SUM(active_users)                  AS active_users,
        customer_segment
    FROM {table('rpt_cohort_retention')}
    GROUP BY cohort, period_number, customer_segment
    ORDER BY cohort, period_number
""")

# ── Filters ───────────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    segments = ["All"] + sorted(df.customer_segment.dropna().unique().tolist())
    seg = st.selectbox("Customer segment", segments)
with col_f2:
    max_period = st.slider(
        "Max period (months)", min_value=3, max_value=24, value=12, step=1
    )

df_seg = df if seg == "All" else df[df.customer_segment == seg]

df_agg = df_seg.groupby(["cohort", "period_number"], as_index=False).agg(
    retention_rate=("retention_rate", "mean"),
    cohort_size=("cohort_size", "sum"),
    active_users=("active_users", "sum"),
)
df_agg = df_agg[df_agg.period_number <= max_period]

# ── Retention Heatmap ─────────────────────────────────────────────────────────
pivot = df_agg.pivot(
    index="cohort", columns="period_number", values="retention_rate"
).sort_index(
    ascending=False
)  # newest cohort on top

st.subheader("Retention Heatmap — % of cohort still active")
st.markdown("""
> Each cell = % of that cohort's users still active N months later.
> Healthy benchmarks: Month-3 ≥ 30%, Month-12 ≥ 15%.
""")

heatmap_z = (pivot.values * 100).round(1)
fig_hm = go.Figure(
    go.Heatmap(
        z=heatmap_z,
        x=[f"M+{c}" for c in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[
            [0.00, "#1a0a00"],
            [0.15, "#7f2f00"],
            [0.30, "#bf6000"],
            [0.50, "#e6a800"],
            [0.70, "#86d400"],
            [1.00, "#00c853"],
        ],
        text=heatmap_z,
        texttemplate="%{text}%",
        textfont=dict(size=10),
        hoverongaps=False,
        colorbar=dict(title="Retention %", ticksuffix="%"),
        zmin=0,
        zmax=100,
    )
)
fig_hm.update_layout(
    template="plotly_dark",
    height=max(400, len(pivot) * 22 + 80),
    margin=dict(t=20, b=20, l=80),
    xaxis=dict(side="top"),
)
st.plotly_chart(fig_hm, use_container_width=True)

st.divider()
col1, col2 = st.columns(2)

# ── Retention Curves ──────────────────────────────────────────────────────────
with col1:
    st.subheader("Retention Curves — Recent 12 Cohorts")
    recent_cohorts = sorted(df_agg.cohort.unique())[-12:]
    df_curves = df_agg[df_agg.cohort.isin(recent_cohorts)].copy()
    df_curves["retention_pct"] = (df_curves.retention_rate * 100).round(1)
    fig_curves = px.line(
        df_curves,
        x="period_number",
        y="retention_pct",
        color="cohort",
        template="plotly_dark",
        color_discrete_sequence=px.colors.sequential.Plasma_r,
        labels={
            "period_number": "Months Since Acquisition",
            "retention_pct": "Retention %",
        },
    )
    fig_curves.update_layout(
        height=380,
        margin=dict(t=10, b=10),
        yaxis=dict(ticksuffix="%", range=[0, 100]),
        legend=dict(orientation="h", y=1.1, font=dict(size=9)),
    )
    st.plotly_chart(fig_curves, use_container_width=True)

# ── Cohort Sizes ──────────────────────────────────────────────────────────────
with col2:
    st.subheader("Cohort Sizes at Acquisition")
    df_m0 = df_agg[df_agg.period_number == 0][["cohort", "cohort_size"]].sort_values(
        "cohort"
    )
    fig_sizes = go.Figure(
        go.Bar(
            x=df_m0.cohort,
            y=df_m0.cohort_size,
            marker_color="#4F8BF9",
            name="Cohort Size",
            text=df_m0.cohort_size.map("{:,}".format),
            textposition="outside",
        )
    )
    fig_sizes.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(t=10, b=10),
        xaxis=dict(tickangle=45),
        yaxis=dict(title="Users"),
    )
    st.plotly_chart(fig_sizes, use_container_width=True)
