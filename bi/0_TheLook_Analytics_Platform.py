"""
TheLook Analytics — PhD-Level BI Dashboard
Built with Streamlit + Plotly against BigQuery gold layer.
"""

import streamlit as st

st.set_page_config(
    page_title="TheLook Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 TheLook Analytics Platform")
st.markdown("""
### Subscription & Ecommerce Intelligence Dashboard

This dashboard suite covers the full analytical stack for TheLook ecommerce,
powered by the dbt gold layer in BigQuery.

| Dashboard | Description |
|---|---|
| **Executive Health** | MRR, ARR, ARPU, NRR — the C-suite view |
| **MRR Waterfall** | New / expansion / contraction / churn decomposition |
| **Cohort Retention** | Classic triangle heatmap + retention curves |
| **Churn Analysis** | Subscriber & revenue churn by segment |
| **Customer LTV & RFM** | Lifetime value, predicted LTV, RFM scoring |
| **Revenue by Segment** | P&L decomposed by channel, category, country |
| **Product Analytics** | Category treemap, margin vs return, top products |
| **CAC & Payback** | LTV:CAC ratio, payback period by channel |

Navigate using the sidebar. All data is queried live from BigQuery `dev_dataset_gold`.
""")

st.info("💡 Select a dashboard from the sidebar to get started.", icon="👈")
