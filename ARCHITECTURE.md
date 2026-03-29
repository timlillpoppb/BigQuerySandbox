# Architecture: TheLook Subscription Analytics — Medallion Architecture

## Overview

This project ingests from `bigquery-public-data.thelook_ecommerce` and models it as a
subscription/recurring revenue analytics platform. The architecture follows a strict
Bronze → Silver → Gold medallion pattern with SCD2 snapshots between Silver and Gold.

> **Note:** This architecture was originally scaffolded by Grok and rebuilt to production
> grade with full subscription analytics, incremental strategies, model contracts, and a
> two-stage GitHub Actions CI/CD pipeline.

---

## Layer Descriptions

### Bronze — Raw Ingestion

**Purpose:** One-to-one copy of source data with audit columns added. No business logic.
**Materialization:** `table` for static lookups; `incremental (insert_overwrite)` for high-volume event tables.
**Schema:** `bronze` (prod) / `dev_dataset_bronze` (dev)

| Model | Source Table | Strategy | Partition | Cluster |
|---|---|---|---|---|
| `brz_users` | users | table | — | country, traffic_source |
| `brz_orders` | orders | incremental | created_date (day) | user_id, status |
| `brz_order_items` | order_items | incremental | created_date (day) | order_id, user_id |
| `brz_events` | events | incremental | event_date (day) | user_id, event_type |
| `brz_products` | products | table | — | category, department, brand |
| `brz_inventory_items` | inventory_items | incremental | created_date (day) | product_id |
| `brz_distribution_centers` | distribution_centers | table | — | — |

**Incremental strategy:** `insert_overwrite` on day-partitions. Rewrites the last 3 days
to capture late-arriving records without scanning the full table.

**Audit columns on all bronze models:**

| Column | Value |
|---|---|
| `_loaded_at` | `current_timestamp()` — when dbt loaded this row |
| `_dbt_run_id` | `invocation_id` — links row to a specific dbt run |
| `_source_model` | Model name — for lineage debugging |

---

### Snapshots — SCD Type 2

**Purpose:** Capture slowly-changing attributes on users and products so historical orders
reflect the profile state at time of purchase.
**Strategy:** `check` on specific columns (avoids timestamp dependency on source data).
**Schema:** `snapshots`

| Snapshot | Tracks Changes To |
|---|---|
| `snap_users` | email, name, location, traffic_source |
| `snap_products` | product_name, category, brand, retail_price, cost |

---

### Silver — Cleaned & Enriched

**Purpose:** Apply cleaning, normalization, type casting, and denormalization. No aggregation.
**Materialization:** `view` — compute deferred to gold queries. Promotes to `incremental` if volume becomes a bottleneck.
**Schema:** `silver` (prod) / `dev_dataset_silver` (dev)

| Model | Key Transformations |
|---|---|
| `slv_users` | clean_string, cohort_month derivation, acquisition_channel join, age_band |
| `slv_orders` | status normalization, is_completed/is_refunded flags, order_month, fulfillment SLA |
| `slv_order_items` | product enrichment join, gross_margin, gross_margin_pct, is_returned |
| `slv_products` | clean_string, standard_margin, distribution center join |
| `slv_events` | clean_string, acquisition_channel join, session_event_rank |
| `slv_inventory_items` | is_sold flag, days_in_inventory |

---

### Gold — Dimensions

**Purpose:** Conformed dimension tables for star schema. SCD2-aware via snapshot joins.
**Materialization:** `table`
**Schema:** `gold` (prod)

| Dimension | Key Attributes |
|---|---|
| `dim_users` | Subscriber status, customer segment, lifetime metrics, RFM context, SCD2 from snap_users |
| `dim_products` | Sales performance, return rate, margin, SCD2 from snap_products |
| `dim_date` | Full date spine 2018–2030 via dbt_date package |
| `dim_distribution_centers` | Warehouse master with surrogate key |

**Subscriber classification** (in `dim_users`):

| Status | Condition |
|---|---|
| `active` | Last order ≤ 90 days ago + ≥2 orders |
| `churned` | Last order > 90 days ago + ≥2 orders |
| `never_ordered` | No completed orders |

---

### Gold — Facts

**Purpose:** Grain-level event facts joining to dimensions.
**Materialization:** `incremental (merge)` — surrogate keys require merge for updates.
**Schema:** `gold` (prod)

| Fact | Grain | Key Metrics |
|---|---|---|
| `fct_orders` | One row per order | order_revenue, order_gross_margin, billing_month, subscriber flags |
| `fct_order_items` | One row per line item | sale_price, gross_margin, category, is_returned |
| `fct_user_sessions` | One row per session | session_duration, funnel stages, conversion |

---

### Gold — Reports (Subscription KPIs)

**Purpose:** Pre-aggregated BI-facing tables. Full recompute on each run.
**Materialization:** `table`
**Schema:** `gold` (prod)

| Report | Description | Key Metrics |
|---|---|---|
| `rpt_mrr` | MRR at user × month level | new_mrr, expansion_mrr, churned_mrr, retained_mrr |
| `rpt_churn` | Monthly churn by segment | subscriber_churn_rate, revenue_churn_rate, NRR |
| `rpt_cohort_retention` | Retention matrix (pivot-ready) | retention_rate by cohort × period |
| `rpt_customer_ltv` | Full LTV/RFM analysis per user | observed_ltv, predicted_12m_ltv, AOV, RFM scores |
| `rpt_cac_and_payback` | CAC proxy & payback | ltv_to_first_order_ratio, estimated_payback_months, RFM composite |
| `rpt_subscription_health` | Executive KPI table (monthly) | MRR, ARR, ARPU, churn rates, NRR, funnel conversion |
| `rpt_product_analytics` | Product performance | revenue_rank, margin, return_rate |
| `rpt_revenue_by_segment` | Contribution margin view | revenue by segment × channel × category |

---

## Schema Routing

The `generate_schema_name` macro ensures dev runs never overwrite production:

| Target | Schema example |
|---|---|
| `prod` | `bronze`, `silver`, `gold` |
| `dev` | `dev_dataset_bronze`, `dev_dataset_silver`, `dev_dataset_gold` |
| `staging` | `staging_dataset_bronze`, etc. |

---

## Model Contracts

`brz_users`, `brz_products`, `dim_users`, and `fct_orders` have dbt model contracts
enforced (`contract.enforced: true`). This guarantees column names and data types match
exactly what downstream models expect, surfacing schema drift at compile time.

---

## Data Quality

Three layers of testing:

1. **Source tests** (`_sources.yml`) — uniqueness, not_null, accepted_values, freshness
2. **Schema tests** (`_schema.yml` per layer) — dbt_expectations range checks, referential integrity
3. **Custom SQL tests** (`tests/`) — business logic assertions:
   - `assert_mrr_never_negative` — active subscriber MRR must be ≥ 0
   - `assert_churn_rate_between_0_and_1` — churn rate must be a valid proportion
   - `assert_no_future_order_dates` — no orders timestamped in the future

---

## CI/CD Pipeline

```
feature/  ──push──► CI Job
                     ├── dbt parse
                     ├── source freshness
                     └── dbt build --select state:modified+ --defer (slim build)

PR to master ──► CI Job (same as above)

master    ──push──► CD Job (requires production environment approval)
                     ├── dbt seed
                     ├── dbt snapshot
                     ├── dbt build --target prod (full)
                     ├── upload manifest.json → GCS (for next slim CI)
                     └── dbt docs generate
```
