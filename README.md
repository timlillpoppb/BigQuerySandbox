# dbt Medallion Architecture — TheLook Subscription Analytics

A production-grade, FAANG-level dbt project modeling the BigQuery public dataset
`bigquery-public-data.thelook_ecommerce` as a subscription/recurring revenue analytics platform.

**Data source:** Google BigQuery Public Data — TheLook E-Commerce
**Platform:** BigQuery (us-east5) | dbt Core 1.8 | GitHub Actions CI/CD
**AI Assistant:** Claude (Anthropic) — default for all code review and generation

---

## Architecture Overview

```
bigquery-public-data.thelook_ecommerce
          │
          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  BRONZE  (raw ingestion, partitioned, clustered)            │
    │  brz_users  brz_orders  brz_order_items  brz_events        │
    │  brz_products  brz_inventory_items  brz_distribution_centers│
    └─────────────────────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  SNAPSHOTS  (SCD Type 2)                                    │
    │  snap_users    snap_products                                │
    └─────────────────────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  SILVER  (cleaned, enriched, normalized — views)            │
    │  slv_users  slv_orders  slv_order_items  slv_products      │
    │  slv_events  slv_inventory_items                           │
    └─────────────────────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  GOLD — Dimensions                                          │
    │  dim_users  dim_products  dim_date  dim_distribution_centers│
    │                                                             │
    │  GOLD — Facts                                               │
    │  fct_orders  fct_order_items  fct_user_sessions            │
    │                                                             │
    │  GOLD — Reports (Subscription KPIs)                        │
    │  rpt_mrr               Monthly Recurring Revenue           │
    │  rpt_churn             Churn rate, NRR, revenue churn      │
    │  rpt_cohort_retention  Retention matrix (pivotable)        │
    │  rpt_customer_ltv      LTV, AOV, RFM, payback period      │
    │  rpt_cac_and_payback   CAC proxy, LTV:CAC ratio           │
    │  rpt_subscription_health  Executive KPI dashboard table    │
    │  rpt_product_analytics    Product revenue & margin         │
    │  rpt_revenue_by_segment   Contribution margin view         │
    └─────────────────────────────────────────────────────────────┘
```

---

## Subscription Modeling Logic

This project treats e-commerce repeat purchases as a proxy for subscription behavior:

| Concept | Definition |
|---|---|
| **Subscriber** | User with ≥2 completed orders (`min_orders_for_subscriber` var) |
| **Active** | Last order within 90 days (`churn_inactivity_days` var) |
| **Churned** | No order in 90+ days |
| **Billing period** | Calendar month of order (date truncated to month) |
| **MRR** | Sum of completed order revenue in a calendar month |
| **NRR** | (Retained MRR + Expansion MRR) / Prior month MRR |

---

## Quickstart

### Prerequisites

- Python 3.11
- GCP project with BigQuery access
- `gcloud` CLI authenticated

### Setup

```bash
# 1. Clone and enter project
git clone <repo-url> && cd dbt

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install dbt packages
dbt deps

# 5. Validate connection
dbt debug

# Windows convenience: use run_dbt.ps1 if make is unavailable
#   .\run_dbt.ps1 build  OR  .\run_dbt.ps1 run --select bronze

# Optional: make `make` and `dbt` available globally in PowerShell
# 1) Add GNU make installation path (winget / choco) to user PATH
#    setx PATH "%PATH%;C:\Program Files (x86)\GnuWin32\bin"
# 2) Add project virtualenv scripts to user PATH
#    setx PATH "%PATH%;C:\Users\uktim\OneDrive\Documents\Code\dbt\.venv\Scripts"

# 6. Load seeds
dbt seed

# 6. Load seeds
dbt seed

# 7. Run snapshots (first time)
dbt snapshot

# 8. Full build
dbt build
```

### Environment Targets

| Target | Schema prefix | Use |
|---|---|---|
| `dev` | `dev_dataset_bronze/silver/gold` | Local development |
| `staging` | `staging_dataset_bronze/silver/gold` | Pre-prod validation |
| `prod` | `bronze` / `silver` / `gold` | Production (CI/CD only) |

```bash
dbt build --target dev      # Development
dbt build --target prod     # Production (runs in GitHub Actions)
```

---

## Key Commands

```bash
# Build by layer
make build-bronze
make build-silver
make build-gold

# Build specific report
dbt build --select rpt_subscription_health

# Slim CI (feature branch)
dbt build --select state:modified+ --defer --state ./prod_manifest

# Source freshness
dbt source freshness

# Snapshots
dbt snapshot --target prod

# Docs
make docs-serve
```

See [DBT_CHEAT_SHEET.md](DBT_CHEAT_SHEET.md) for the full command reference.

---

## CI/CD Pipeline

| Event | Job | Scope |
|---|---|---|
| Push to `feature/**` | CI (slim build) | `state:modified+` vs prod manifest |
| PR to `master` | CI (slim build) | `state:modified+` vs prod manifest |
| Push to `master` | CD (full prod deploy) | All models, requires `production` env approval |

**Required GitHub Secrets:**

| Secret | Description |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | WIF provider resource name |
| `GCP_SA_EMAIL` | Service account email (BigQuery Data Editor + Job User) |
| `GCP_PROJECT_ID` | `project-2ac71b10-d4cb-403a-b2c` |
| `GCS_BUCKET` | GCS bucket for prod manifest storage |

---

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for naming conventions, best practices, and PR checklist.
See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed layer descriptions and design decisions.
See [AGENTS.md](AGENTS.md) for AI agent workflows (Claude-powered).
