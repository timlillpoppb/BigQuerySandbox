# CLAUDE.md — BigQuerySandbox dbt Project

## Project Overview

TheLook ecommerce subscription analytics platform. Full dbt medallion architecture
(bronze → silver → gold) built on BigQuery, sourced from `bigquery-public-data.thelook_ecommerce`.

## Local Environment

- Python venv: `.venv/` (Python 3.11)
- dbt binary: `.venv/Scripts/dbt.exe` (do NOT use `python -m dbt.cli.main`)
- Streamlit: `.venv/Scripts/streamlit.exe`
- BigQuery location: `US` multi-region (required for public dataset access)
- GCP project: `project-2ac71b10-d4cb-403a-b2c`

## Common Commands

```bash
# dbt
.venv/Scripts/dbt.exe build                        # full build
.venv/Scripts/dbt.exe build --select <model>       # single model
.venv/Scripts/dbt.exe test --select <model>        # run tests
.venv/Scripts/dbt.exe run --select state:modified  # slim CI

# Streamlit BI dashboard
.venv/Scripts/streamlit.exe run bi/0_TheLook_Analytics_Platform.py

# Python formatting
.venv/Scripts/python.exe -m black bi/
```

## Code Formatting

### Python
- Formatter: **black** (88-char line length)
- Always run `black` on any `.py` file after writing or editing it

### SQL / dbt models
- 4-space indentation
- SQL keywords UPPERCASE
- One column per line in SELECT lists
- Leading commas on multi-line selects
- Blank line between each CTE block
- Aliases: lowercase snake_case

### Jinja / dbt macros
- `{{ ref() }}` / `{{ source() }}` on the same line as FROM/JOIN
- Macro args: one per line if more than two

### General
- No trailing whitespace
- Newline at end of file
- No commented-out dead code

## Behavior

- Run all commands directly without asking permission
- Only pause for genuinely destructive/irreversible actions (e.g. deleting prod data, force-pushing master)

## Agent Consultation (Feedback Loop)

Before implementing any non-trivial change, consult the relevant agents defined in
`AGENTS.md`. Use the consultation matrix to identify which agents apply, surface
their concerns, resolve conflicts, then proceed.

**Agents:** DataEngineer · DataArchitect · DataAnalyst · BIAnalyst · QAGovernance · ProjectManager

Quick matrix:
- SQL model changes → DataEngineer + DataArchitect
- KPI / business logic → DataAnalyst + QAGovernance
- Dashboard / Streamlit → BIAnalyst
- Multi-layer or structural changes → all agents
- Scope / risk / trade-offs → ProjectManager

## Architecture

```
bronze (brz_*)  →  silver (slv_*)  →  gold dims/facts/reports
```

**Gold reports:** rpt_mrr, rpt_churn, rpt_cohort_retention, rpt_customer_ltv,
rpt_cac_and_payback, rpt_revenue_by_segment, rpt_subscription_health, rpt_product_analytics

**Snapshots:** snap_users, snap_products
**Seeds:** seed_churn_thresholds, seed_traffic_source_mapping

## CI/CD

- Workflow: `.github/workflows/dbt.yml`
- Feature branches: slim CI (`state:modified+`)
- Master merge: full prod deploy
- Auth: Workload Identity Federation (no service account keys)
- Prod manifest stored in: `gs://dbt-manifests-project-2ac71b10-d4cb-403a-b2c`

## Known Data Quality Warnings (expected, not actionable)

All downgraded to `severity: warn`:
- ~10k duplicate emails in thelook users
- ~1.1M null user_ids in events
- 5 unexpected order status values
- 2 null product names
