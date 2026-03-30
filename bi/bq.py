"""Shared BigQuery client and query helpers."""
import streamlit as st
import pandas    as pd
from google.cloud import bigquery

PROJECT = "project-2ac71b10-d4cb-403a-b2c"
DATASET = "dev_dataset_gold"


@st.cache_resource
def get_client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT)


@st.cache_data(ttl=300, show_spinner="Querying BigQuery...")
def run_query(sql: str) -> pd.DataFrame:
    client = get_client()
    return client.query(sql).to_dataframe()


def table(name: str) -> str:
    return f"`{PROJECT}.{DATASET}.{name}`"


def fmt_currency(v: float) -> str:
    if v >= 1_000_000:
        return f"${v / 1_000_000:.2f}M"
    if v >= 1_000:
        return f"${v / 1_000:.1f}K"
    return f"${v:.2f}"


def fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"
