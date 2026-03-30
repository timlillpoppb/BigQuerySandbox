# Phase 2 Plan - Cloud Composer (Airflow) Orchestration

## Objective
Migrate production dbt orchestration from GitHub Actions-only to Cloud Composer while preserving the same metadata logging contract and cost telemetry.

## Current Phase 1 Baseline
- Production dbt runs execute in GitHub Actions.
- `scripts/log_dbt_run_metadata.py` writes run-level and step-level telemetry to BigQuery:
  - `prod_dataset_ops.dbt_run_summary`
  - `prod_dataset_ops.dbt_run_job_metadata`
- Bytes are reconciled from `INFORMATION_SCHEMA.JOBS_BY_PROJECT` for billing accuracy.

## Why Phase 2
Use Composer when orchestration requirements exceed GitHub Actions simplicity:
- Scheduled runs independent of git merges
- Complex dependencies and retries
- Backfills over date ranges
- Centralized SLA/alerting

## Target Architecture
1. Cloud Composer DAG triggers dbt build for prod.
2. DAG task persists metadata via `log_dbt_run_metadata.py` (same schema as Phase 1).
3. DAG task performs reconciliation checks and alerts on gaps.
4. Optional handoff: GitHub Actions triggers Composer DAG for deploy events.

## DAG Design
### DAG: `dbt_prod_deploy_with_metadata`
- Task 1: `prepare_context`
  - Capture run start timestamp and deployment metadata (commit SHA, actor, branch, trigger type).
- Task 2: `dbt_deps`
  - Install dependencies / run `dbt deps`.
- Task 3: `dbt_build_prod`
  - Run `dbt build --target prod` with retries for transient BigQuery failures.
- Task 4: `log_run_metadata`
  - Always-run task (`trigger_rule='all_done'`) calling `log_dbt_run_metadata.py`.
- Task 5: `validate_run_capture`
  - Query `prod_dataset_ops.dbt_run_summary` and `dbt_run_job_metadata` to assert row presence and totals.
- Task 6: `notify`
  - Send status to Slack/Email (success/failure and bytes summary).

## Data Contract (No Change)
### `prod_dataset_ops.dbt_run_summary`
- One row per `invocation_id`
- Includes start/end timestamps, status, step counts, and total bytes in B/MB/GB/TB

### `prod_dataset_ops.dbt_run_job_metadata`
- One row per executed dbt node/job
- Includes `job_id`, `job_result`, bytes in B/MB/GB/TB, and node timing

## Reliability Guarantees
- `log_run_metadata` runs even when dbt fails.
- Idempotency by `invocation_id` (delete/insert pattern) prevents duplicates.
- Reconciliation task detects missing or partial captures.
- Bytes sourced from BigQuery JOBS metadata for cost accuracy.

## Security
- Composer uses Workload Identity (no key files).
- No credentials in DAG code.
- BigQuery access scoped to datasets required for dbt and metadata logging.

## Rollout Plan
1. Deploy Composer environment with minimal DAG skeleton.
2. Run in shadow mode (Composer logs only; GitHub Actions remains deploy source).
3. Validate 100% run capture for at least 5 production runs.
4. Switch production trigger to Composer and keep GitHub Actions as fallback.
5. Retire duplicate orchestration once stable.

## Acceptance Criteria
- Every production dbt run is represented in `dbt_run_summary`.
- Every dbt executed step with a BigQuery job appears in `dbt_run_job_metadata`.
- Total bytes in summary equals sum of step bytes.
- Failed runs are still logged with accurate status and timing.
