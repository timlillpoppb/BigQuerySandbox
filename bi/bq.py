"""Shared BigQuery client and query helpers."""

import os

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT = "project-2ac71b10-d4cb-403a-b2c"

# Dataset resolution order:
#   1. Streamlit secrets  [bigquery] dataset
#   2. BQ_DATASET env var (useful for Cloud Run overrides)
#   3. Default: prod_dataset_gold
DATASET = st.secrets.get("bigquery", {}).get("dataset") or os.environ.get(
    "BQ_DATASET", "prod_dataset_gold"
)


@st.cache_resource
def get_client() -> bigquery.Client:
    """Return a BigQuery client.

    In Streamlit Cloud: credentials come from the [gcp_service_account] secret.
    Locally: falls back to Application Default Credentials (gcloud auth).
    """
    if "gcp_service_account" in st.secrets:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/bigquery.readonly"],
        )
        return bigquery.Client(project=PROJECT, credentials=creds)
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
