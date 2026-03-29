# AI Instructions — TheLook Subscription Analytics dbt Project

## Overview

This workspace implements a FAANG-level Medallion Architecture in dbt Core, sourced from
`bigquery-public-data.thelook_ecommerce` and modeled as a subscription analytics platform.

**Primary AI:** Claude (Anthropic) — set as default via `chat.agent.default: claude` in VS Code settings.

---

## Architecture Principles

- **Strict layer separation:** Bronze → Silver → Gold (no cross-layer skipping)
- **Source references:** `{{ source() }}` in bronze only; `{{ ref() }}` everywhere else
- **Naming:** `brz_`, `slv_`, `dim_`, `fct_`, `rpt_`, `snap_`, `seed_`, `assert_`
- **Audit columns:** All bronze models include `_loaded_at`, `_dbt_run_id`, `_source_model`
- **Schema routing:** `generate_schema_name` macro handles dev/prod isolation automatically

---

## Subscription Analytics Context

The project treats e-commerce repeat purchases as subscription behavior:
- Subscriber = user with ≥2 orders (`{{ var('min_orders_for_subscriber') }}`)
- Active = last order within 90 days (`{{ var('churn_inactivity_days') }}`)
- Billing period = calendar month (`{{ subscription_period() }}` macro)
- MRR = sum of completed order revenue in a calendar month

Core KPI models: `rpt_mrr`, `rpt_churn`, `rpt_cohort_retention`, `rpt_customer_ltv`,
`rpt_cac_and_payback`, `rpt_subscription_health`, `rpt_revenue_by_segment`

---

## Key Standards

- Use `{{ clean_string() }}`, `{{ safe_divide() }}`, `{{ subscription_period() }}` macros consistently
- BigQuery incremental models use `insert_overwrite` on bronze, `merge` on gold facts
- All large tables must have `partition_by` and `cluster_by` in config
- Model contracts enforced on: `brz_users`, `brz_products`, `dim_users`, `fct_orders`
- Tests: minimum `unique` + `not_null` on PKs; `dbt_expectations` range checks on metrics

---

## Agent Roles (see AGENTS.md)

- **DbtValidator** — SQL syntax, BigQuery patterns, macro usage
- **ArchitectureReviewer** — Layer separation, materialization strategy
- **SubscriptionAnalyticsReviewer** — KPI business logic correctness
- **DataQualityGuardian** — Test coverage completeness

---

## Before Committing

```bash
dbt parse          # Validates project structure
dbt build          # Runs all models + tests
dbt source freshness  # Checks data recency
```

See DEVELOPMENT.md for the full PR checklist.
