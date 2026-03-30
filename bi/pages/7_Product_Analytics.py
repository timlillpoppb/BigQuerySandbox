"""Product Analytics — treemap, margin vs return bubble, top products."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit           as st
import plotly.graph_objects as go
import plotly.express       as px
from bq import run_query, table, fmt_currency, fmt_pct

st.set_page_config(page_title="Product Analytics", layout="wide")
st.title("🛍️ Product Analytics")
st.caption("Revenue rank, margin, return rate — powered by `rpt_product_analytics`")

# ── Data ─────────────────────────────────────────────────────────────────────
df = run_query(f"""
    SELECT *
    FROM {table('rpt_product_analytics')}
    WHERE total_units_sold > 0
    ORDER BY overall_revenue_rank
""")

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Products",    f"{len(df):,}")
c2.metric("Avg Gross Margin",  fmt_pct(df.avg_gross_margin_pct.mean()))
c3.metric("Avg Return Rate",   fmt_pct(df.return_rate.mean()))
c4.metric("Total Units Sold",  f"{int(df.total_units_sold.sum()):,}")

st.divider()

# ── Revenue Treemap ───────────────────────────────────────────────────────────
st.subheader("Revenue Treemap — Category → Department")
st.caption("Color = average gross margin % (green = high margin, red = low margin)")
df_tree = (
    df
    .groupby(["category", "department"], as_index=False)
    .agg(
        total_revenue = ("total_revenue",       "sum"),
        total_units   = ("total_units_sold",    "sum"),
        avg_margin    = ("avg_gross_margin_pct", "mean"),
    )
)
df_tree["avg_margin"] = df_tree.avg_margin.round(4)   # keep precision for color scale

fig_tree = px.treemap(
    df_tree,
    path                    = ["category", "department"],
    values                  = "total_revenue",
    color                   = "avg_margin",
    color_continuous_scale  = "RdYlGn",
    color_continuous_midpoint = df_tree.avg_margin.median(),
    template                = "plotly_dark",
    hover_data              = {"total_units": True, "avg_margin": ":.1%"},
    labels                  = {"total_revenue": "Revenue ($)", "avg_margin": "Avg Margin"},
)
fig_tree.update_coloraxes(colorbar_tickformat=".0%")
fig_tree.update_layout(
    height = 480,
    margin = dict(t=20, b=10),
)
st.plotly_chart(fig_tree, use_container_width=True)

st.divider()
col1, col2 = st.columns(2)

# ── Margin vs Return Rate Bubble ──────────────────────────────────────────────
with col1:
    st.subheader("Gross Margin % vs Return Rate")
    st.caption("Ideal: top-left (high margin, low returns). Size = total revenue.")
    df_cat = (
        df
        .groupby("category", as_index=False)
        .agg(
            avg_gross_margin_pct = ("avg_gross_margin_pct", "mean"),
            return_rate          = ("return_rate",           "mean"),
            total_revenue        = ("total_revenue",         "sum"),
            total_units          = ("total_units_sold",      "sum"),
        )
    )
    df_cat["margin_pct"] = (df_cat.avg_gross_margin_pct * 100).round(1)
    df_cat["return_pct"] = (df_cat.return_rate          * 100).round(1)
    fig_bub = px.scatter(
        df_cat,
        x            = "return_pct",
        y            = "margin_pct",
        size         = "total_revenue",
        color        = "category",
        hover_name   = "category",
        hover_data   = {"total_revenue": ":$,.0f", "total_units": ":,"},
        template     = "plotly_dark",
        size_max     = 60,
        labels       = {
            "return_pct": "Return Rate %",
            "margin_pct": "Gross Margin %",
        },
    )
    fig_bub.update_layout(
        height     = 420,
        margin     = dict(t=10, b=10),
        xaxis      = dict(ticksuffix="%"),
        yaxis      = dict(ticksuffix="%"),
        showlegend = True,
        legend     = dict(orientation="h", y=1.1, font=dict(size=9)),
    )
    st.plotly_chart(fig_bub, use_container_width=True)

# ── Top 20 Products ────────────────────────────────────────────────────────────
with col2:
    st.subheader("Top 20 Products by Revenue")
    top20 = df.head(20).copy()
    top20["margin_pct"] = (top20.avg_gross_margin_pct * 100).round(1)
    top20["return_pct"] = (top20.return_rate          * 100).round(1)
    fig_bar = px.bar(
        top20.sort_values("total_revenue"),
        x            = "total_revenue",
        y            = "product_name",
        color        = "category",
        orientation  = "h",
        template     = "plotly_dark",
        color_discrete_sequence = px.colors.qualitative.Set2,
        hover_data   = {"margin_pct": True, "return_pct": True, "total_units_sold": True},
        labels       = {"total_revenue": "Total Revenue ($)", "product_name": ""},
    )
    fig_bar.update_layout(
        height = 420,
        margin = dict(t=10, b=10, r=10),
        xaxis  = dict(tickprefix="$", tickformat=".2s"),
        legend = dict(orientation="h", y=1.1, font=dict(size=9)),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Product Performance Table ──────────────────────────────────────────────────
st.subheader("Product Performance Table")
with st.expander("Show full table (sortable)"):
    display_cols = [
        "product_name", "category", "department", "brand",
        "total_units_sold", "total_revenue", "avg_sale_price",
        "avg_gross_margin_pct", "return_rate",
        "revenue_rank_in_category", "overall_revenue_rank",
    ]
    df_disp = df[display_cols].copy()
    df_disp["total_revenue"]        = df_disp.total_revenue.map("${:,.2f}".format)
    df_disp["avg_sale_price"]       = df_disp.avg_sale_price.map("${:,.2f}".format)
    df_disp["avg_gross_margin_pct"] = (df_disp.avg_gross_margin_pct * 100).round(1).astype(str) + "%"
    df_disp["return_rate"]          = (df_disp.return_rate          * 100).round(1).astype(str) + "%"
    df_disp.columns = [
        "Product", "Category", "Department", "Brand",
        "Units Sold", "Revenue", "Avg Price",
        "Gross Margin %", "Return Rate",
        "Category Rank", "Overall Rank",
    ]
    st.dataframe(df_disp, use_container_width=True, hide_index=True)
