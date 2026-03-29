# Development Guidelines

## Naming Conventions

| Prefix | Layer | Example |
|---|---|---|
| `brz_` | Bronze (raw ingestion) | `brz_orders` |
| `slv_` | Silver (cleaned/enriched) | `slv_orders` |
| `dim_` | Gold — Dimension | `dim_users` |
| `fct_` | Gold — Fact | `fct_orders` |
| `rpt_` | Gold — Report | `rpt_mrr` |
| `snap_` | Snapshot (SCD2) | `snap_users` |
| `seed_` | Seed file | `seed_churn_thresholds` |
| `assert_` | Custom SQL test | `assert_mrr_never_negative` |

**Column conventions:**
- All columns: `snake_case`
- Surrogate keys: `<entity>_sk` (e.g. `user_sk`)
- Natural keys: `<entity>_id` (e.g. `user_id`)
- Audit columns: `_loaded_at`, `_dbt_run_id`, `_source_model`
- Boolean flags: `is_<condition>` (e.g. `is_subscriber`, `is_completed`)
- Date columns: `<event>_at` (timestamp), `<event>_date` (date), `<event>_month` (date truncated to month)

---

## Materialization Strategy

| Layer | Strategy | Reason |
|---|---|---|
| Bronze (high-volume) | `incremental (insert_overwrite)` | Cost-efficient BigQuery day-partition rewrite |
| Bronze (lookup) | `table` | Small, rarely changes |
| Silver | `view` | No aggregation — compute deferred to gold |
| Gold dimensions | `table` | Stable, needs clustering for BI query performance |
| Gold facts | `incremental (merge)` | Surrogate keys require merge for updates |
| Gold reports | `table` | Full recompute; BI tools read directly |
| Snapshots | `snapshot (check)` | SCD Type 2 via check strategy |

**When to use full-refresh (`--full-refresh`):**
- After changing partition keys or cluster keys
- After adding new columns to an incremental model
- When source data has been backfilled significantly

---

## Model Contracts

Apply contracts (`contract.enforced: true`) to models that form stable interfaces:
- All bronze models that have dbt_expectations tests
- `dim_users` and `fct_orders` (consumed by reports and BI tools)

When a contract is enforced, column names and data types **must** match the `_schema.yml`
definition exactly. dbt will error at compile time — not at runtime — if they diverge.

---

## Subscription Analytics Patterns

### Defining a "subscriber"
```sql
-- In dim_users and reports, use the project variable:
where total_orders >= {{ var('min_orders_for_subscriber') }}
```

### Billing period (MRR month)
```sql
-- Use the subscription_period macro consistently:
{{ subscription_period('created_at') }}  as billing_month
```

### Churn classification
```sql
case
    when days_since_last_order <= {{ var('churn_inactivity_days') }} then 'active'
    when total_orders = 0 then 'never_ordered'
    else 'churned'
end as subscriber_status
```

---

## Adding a New Report Model

1. Create `models/gold/reports/rpt_<name>.sql`
2. Add materialization config with `tags: ['gold', 'report', 'subscription']`
3. Add model documentation to `models/gold/_schema.yml`
4. Add exposure reference to `models/gold/_exposures.yml` if BI-facing
5. Write any required custom SQL tests in `tests/`

---

## PR Checklist

- [ ] `dbt parse` passes without errors
- [ ] `dbt build --select <model>+` passes all tests
- [ ] New columns documented in `_schema.yml`
- [ ] Contracts updated if model interface changed
- [ ] No hardcoded project IDs or dataset names (use `target.project` or sources)
- [ ] Incremental models include `{% if is_incremental() %}` filter
- [ ] BigQuery partition + cluster keys set on large tables
- [ ] `dbt source freshness` checked if sources changed
- [ ] Claude review completed via AGENTS.md workflow

---

## Running Locally

```bash
# First time
dbt deps && dbt seed && dbt snapshot && dbt build

# Day-to-day (incremental)
dbt build --target dev

# Test only
dbt test --target dev

# Specific model + downstream
dbt build --select fct_orders+ --target dev

# Full refresh (after schema changes)
dbt build --full-refresh --select brz_orders --target dev
```
