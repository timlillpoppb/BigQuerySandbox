# BigQuerySandbox — TheLook Subscription Analytics (dbt)

A complete dbt medallion pipeline for subscription-style e-commerce analytics, built on BigQuery with GitHub Actions CI/CD.

---

## 🚀 Quick Project Summary

- Source dataset: `bigquery-public-data.thelook_ecommerce`
- Data warehouse: BigQuery (US multi-region)
- dbt model layers: Bronze -> Snapshots -> Silver -> Gold (facts/dimensions/reports)
- Key business metrics: MRR, churn, LTV, cohort retention, CAC, RFM
- CI/CD: GitHub Actions (`.github/workflows/dbt.yml`)
- PR automation: `make pr-and-merge` + `scripts/pr_and_merge.py`

---

## 🏗 Architecture Layers

1. **Bronze**: raw ingest views (`models/bronze/brz_*.sql`)
2. **Snapshots**: SCD2 history (`snapshots/snap_users.sql`, `snapshots/snap_products.sql`)
3. **Silver**: cleaned, normalized staging (`models/silver/slv_*.sql`)
4. **Gold**:
   - dimensions (`models/gold/dimensions/`)
   - facts (`models/gold/facts/`)
   - reports (`models/gold/reports/`)

---

## 📦 Core Reports and KPIs

- `rpt_mrr`: monthly recurring revenue
- `rpt_churn`: churn and NRR
- `rpt_cohort_retention`: cohort retention matrix
- `rpt_customer_ltv`: customer lifetime value, RFM, payback
- `rpt_cac_and_payback`: CAC proxy and payback analysis
- `rpt_revenue_by_segment`: segment-level revenue and contribution
- `rpt_product_analytics`: product revenue and demand insights
- `rpt_subscription_health`: executive-quality KPI snapshot

---

## 🛠 Key Files

- `dbt_project.yml` - model configuration and materialization
- `models/` - GOLD/SILVER/BRONZE SQL models and schema tests
- `macros/` - dbt macros for helpers / naming / validation
- `packages.yml` - dbt package dependencies (`dbt_utils`, `dbt_date`, etc.)
- `profiles.yml` - local connection settings (not committed in repo)
- `scripts/pr_and_merge.py` - GitHub API PR automation
- `Makefile` - common commands (build/test/deploy/pr-and-merge)
- `README.md` - this document
- `.github/workflows/dbt.yml` - CI/CD pipeline
- `.github/workflows/auto-pr-merge.yml` - PR automation (mostly disabled)

---

## ⚙️ Setup (Local Development)

### Requirements
- Python 3.11
- dbt-bigquery 1.8.3
- gcloud CLI authenticated with Workload Identity
- GitHub token in `.env` (`GITHUB_TOKEN=...`)

### Bootstrap

```bash
git clone <repo> && cd dbt
python -m venv .venv
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
dbt deps
```

### Quick commands

```bash
dbt debug
make build-bronze
make build-silver
make build-gold
make pr-and-merge   # merges feature to master via GitHub API
```

---

## 🧪 Testing

- `dbt test --select <model>`
- `dbt source freshness --target dev`
- `dbt snapshot --target dev`
- `dbt build --target dev --select state:modified+ --defer --state ./prod_manifest`

---

## 🔐 Security & Secrets

- `.env` is gitignored and should store secrets locally only.
- GitHub Actions uses repository secrets:
  - `GCP_WORKLOAD_IDENTITY_PROVIDER`
  - `GCP_SA_EMAIL`
  - `GCP_PROJECT_ID`
  - `GCS_BUCKET`
  - `GITHUB_TOKEN` (for automation tasks)
- Never commit `.env`, `profiles.yml`, or service account keys.

---

## 🧭 CI/CD Strategy

- `on: push` for feature branches runs `ci` job with quick validation
- `on: pull_request` to master also runs `ci` job
- `on: push` to master triggers `deploy` (prod dbt build)
- `api` workflows produce `state:modified+` behavior in CI when manifest exists

---

## 📘 Reference

- `ARCHITECTURE.md`: design principles and medallion choices
- `DEVELOPMENT.md`: conventions, branch/PR policy, testing
- `DBT_CHEAT_SHEET.md`: quick dbt command reference
- `AGENTS.md`: agent review protocol for changes
