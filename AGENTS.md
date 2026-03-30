# AI Agents — TheLook Subscription Analytics

This project uses a panel of six specialist agents. Before making any non-trivial
change, Claude must identify which agents are relevant and simulate a review round
with each before finalising the approach.

---

## Consultation Protocol

For every change, identify the relevant agents from the matrix below, surface their
concerns/questions, resolve conflicts, and only then proceed with implementation.

| Change type | Consult |
|---|---|
| New or modified dbt model (SQL) | Data Engineering, Data Architecture |
| New fact / dimension / report table | Data Architecture, Data Analyst |
| MRR, churn, LTV, cohort, RFM logic | Data Analyst, QA/Governance |
| New or modified Streamlit page / chart | BI Analyst |
| Dashboard KPI definition change | BI Analyst, Data Analyst |
| New source integration or layer change | Data Architecture, Data Engineering |
| Test coverage / contracts / schema | QA/Governance, Data Engineering |
| Any change that touches multiple layers | All agents |
| Prioritisation, scope, or design trade-offs | Project Manager |
| CI/CD, infra, or environment changes | Data Engineering, Project Manager |

### How to run a review round

For each relevant agent, explicitly state:
1. What the agent's concern is for this change
2. Any objections or risks it raises
3. How those are resolved before proceeding

---

## Agent Definitions

### DataEngineer

**Role:** Implementation quality and platform health.

**Use when:** Adding/modifying model SQL, changing materializations, writing macros,
touching CI/CD, managing the venv or dependencies.

**What it checks:**
- CTEs named clearly; source → intermediate → final order
- `is_incremental()` guard present on incremental models
- Partition/cluster keys appropriate for table size
- No `SELECT *` in gold layer — explicit column lists required
- `{{ ref() }}` used for all model-to-model references
- `{{ source() }}` used only in bronze layer
- Macros used consistently (`clean_string`, `safe_divide`, `subscription_period`)
- Audit columns (`_loaded_at`, `_dbt_run_id`, `_source_model`) present in bronze
- black formatting applied to all Python files

---

### DataArchitect

**Role:** Structural integrity and medallion layer compliance.

**Use when:** Major structural changes (new layers, new fact/dim tables), changing
materialisation strategy across a layer, adding sources, editing `dbt_project.yml`
or `generate_schema_name`.

**What it checks:**
- Bronze references only `{{ source() }}`
- Silver references only bronze (no gold references)
- Gold references only silver or other gold (no bronze)
- Report models reference only facts and dimensions (no silver)
- Contracts enforced on stable interfaces
- Schema routing consistent across dev/staging/prod targets
- No circular dependencies

---

### DataAnalyst

**Role:** Business logic and KPI correctness.

**Use when:** Modifying MRR, churn, LTV, cohort retention, RFM, CAC, or any
subscription KPI model. Adding new business metrics.

**What it checks:**
- MRR movement types are mutually exclusive and exhaustive
- Churn definition consistent with `churn_inactivity_days` var
- Cohort month derived from `first_order_month` (not registration date)
- LTV calculations use only `is_completed = true` orders
- NRR formula: `(retained_mrr + expansion_mrr) / prior_total_mrr`
- RFM scores bounded 1–5
- CAC proxy uses `avg_order_value` as the denominator baseline
- Metric definitions are consistent across all report models

---

### BIAnalyst

**Role:** Dashboard usability, chart correctness, and storytelling.

**Use when:** Adding or modifying any Streamlit page, changing chart types, updating
KPI tiles, adding filters or selectors, or changing how data is presented to end users.

**What it checks:**
- Chart type is appropriate for the data shape (time series vs. bar vs. scatter etc.)
- KPI tile values match the underlying SQL (no off-by-one periods, no silent nulls)
- Filters are consistent across pages (same date range defaults, same segment options)
- Color encoding is consistent and accessible
- Page loads in < 3 seconds under normal data volumes
- No raw column names exposed to end users — all labels are human-readable
- Empty states handled gracefully (no blank charts when data is missing)
- Streamlit page order and naming reflect the analytical narrative

---

### QAGovernance

**Role:** Test coverage, data contracts, and trust.

**Use when:** Adding new models, changing column types, updating contracts, after
any data incident or failed assertion, before any prod deploy.

**What it checks:**
- Every model in `_schema.yml` has at minimum `not_null` on the primary key
- Incremental models have the same tests as their full-refresh counterpart
- `rpt_mrr.monthly_revenue` has a `>= 0` assertion
- Churn rate assertions bounded 0–1
- No future order dates in fact tables
- All custom SQL tests have explicit `severity: error` or `severity: warn`
- Public-data quality warnings are documented and intentionally downgraded
- New columns added to contracts before models are deployed to prod

---

### ProjectManager

**Role:** Scope, prioritisation, and delivery risk.

**Use when:** Planning a multi-step change, evaluating trade-offs between approaches,
assessing impact on CI/CD or downstream consumers, or when a change could affect
the shared/prod environment.

**What it checks:**
- Is the change in scope for the current task?
- Does it introduce tech debt that should be tracked?
- Are there downstream dependencies that need coordinating?
- Is a phased rollout safer than a big-bang change?
- Does the change need to be behind a feature branch before merging to master?
- Are GitHub secrets, infra, or manual steps required that the user must action?

---

## Invocation Examples

```
DataEngineer: Review this incremental model — is the is_incremental() guard correct?
DataArchitect: I'm adding rpt_arpu to the gold layer — does the layer placement comply?
DataAnalyst: Validate the churn classification logic in rpt_churn.sql
BIAnalyst: Review the new Cohort Retention page — are the chart choices appropriate?
QAGovernance: Check test coverage for rpt_cac_and_payback before prod deploy
ProjectManager: I'm planning to refactor all silver models — what's the rollout risk?
```
