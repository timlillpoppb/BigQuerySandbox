# AI Agents — TheLook Subscription Analytics

This project uses Claude (Anthropic) as the primary AI assistant for code review,
architecture decisions, and data quality validation.

---

## DbtValidator

**Purpose:** Validates dbt models for syntax correctness, best practices, and BigQuery performance patterns.

**Use when:**
- Adding or modifying any model SQL
- Changing materialization strategy
- Adding new tests or contracts

**What it checks:**
- CTEs named clearly and organized (source → intermediate → final)
- `is_incremental()` guard present on incremental models
- Partition/cluster keys appropriate for table size
- No `select *` in gold layer (explicit column list required)
- `{{ ref() }}` used for all model-to-model references
- `{{ source() }}` used only in bronze layer
- Macro usage consistent (`clean_string`, `safe_divide`, `subscription_period`)
- Audit columns (`_loaded_at`, `_dbt_run_id`, `_source_model`) present in bronze

---

## ArchitectureReviewer

**Purpose:** Reviews overall architecture decisions, data flow, layer separation, and compliance with medallion principles.

**Use when:**
- Major structural changes (new layers, new fact/dimension tables)
- Changing materialization strategy across a layer
- Adding new source integrations
- Changes to `dbt_project.yml` or `generate_schema_name` macro

**What it checks:**
- Bronze models reference only `{{ source() }}`
- Silver models reference only bronze models (no gold references)
- Gold models reference only silver or other gold models (no bronze references)
- Report models only reference facts and dimensions (no silver)
- Contracts enforced on stable interfaces
- Schema routing consistent with environment targets

---

## SubscriptionAnalyticsReviewer

**Purpose:** Validates subscription KPI logic for business correctness.

**Use when:**
- Modifying MRR, churn, LTV, or cohort retention models
- Changing subscription classification variables
- Adding new subscription KPI reports

**What it checks:**
- MRR movement types are mutually exclusive and exhaustive
- Churn definition consistent with `churn_inactivity_days` var
- Cohort month derived from `first_order_month` (not registration date)
- LTV calculations use only `is_completed = true` orders
- NRR formula: `(retained_mrr + expansion_mrr) / prior_total_mrr`
- RFM scores bounded 1–5
- CAC proxy uses `avg_order_value` as the denominator baseline

---

## DataQualityGuardian

**Purpose:** Reviews test coverage and data quality assertions across all layers.

**Use when:**
- Adding new models without corresponding tests
- Changing column data types (contract impact)
- After any data incident or failed assertion

**What it checks:**
- Every model in `_schema.yml` has at minimum `not_null` on PK
- Incremental models have the same tests as their base table
- `rpt_mrr.monthly_revenue` has `expect_column_values_to_be_between min_value: 0`
- Churn rate assertions bounded 0–1
- No future order dates
- All custom SQL tests have `{{ config(severity='error') }}` or `warn` set explicitly

---

## Invoking Agents

These agents are invoked via Claude Code (claude.ai/code or VS Code extension):

```
@claude Review this model with DbtValidator lens: [paste SQL]
@claude ArchitectureReviewer: I'm adding a new report layer model rpt_arpu — is the layer placement correct?
@claude SubscriptionAnalyticsReviewer: Validate the MRR movement classification in rpt_mrr.sql
@claude DataQualityGuardian: Review test coverage for the new rpt_cac_and_payback model
```

Claude is set as the default AI assistant for this project (VS Code: `chat.agent.default: claude`).
