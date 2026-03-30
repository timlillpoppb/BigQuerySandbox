#!/usr/bin/env python3
"""Validate dbt metadata logging tables in BigQuery."""

from __future__ import annotations

import argparse
import json
from google.cloud import bigquery


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--metadata-dataset", default="prod_dataset_ops")
    args = parser.parse_args()

    client = bigquery.Client(project=args.project_id)
    dataset = args.metadata_dataset

    existence_sql = f"""
    SELECT table_name
    FROM `{args.project_id}.{dataset}.INFORMATION_SCHEMA.TABLES`
    WHERE table_name IN ('dbt_run_summary', 'dbt_run_job_metadata')
    ORDER BY table_name
    """
    tables = [row.table_name for row in client.query(existence_sql).result()]
    if tables != ['dbt_run_job_metadata', 'dbt_run_summary']:
        raise SystemExit(f"Missing expected metadata tables. Found: {tables}")

    accuracy_sql = f"""
    WITH latest AS (
      SELECT invocation_id
      FROM `{args.project_id}.{dataset}.dbt_run_summary`
      ORDER BY inserted_at DESC
      LIMIT 1
    ),
    step_agg AS (
      SELECT
        invocation_id,
        SUM(bytes_consumed_bytes) AS step_bytes
      FROM `{args.project_id}.{dataset}.dbt_run_job_metadata`
      WHERE invocation_id = (SELECT invocation_id FROM latest)
      GROUP BY invocation_id
    )
    SELECT
      r.invocation_id,
      r.total_steps,
      r.total_bytes_consumed_bytes,
      s.step_bytes,
      ABS(r.total_bytes_consumed_bytes - s.step_bytes) AS bytes_diff,
      ABS(r.total_bytes_consumed_mb - (r.total_bytes_consumed_bytes / POW(1024, 2))) < 1e-9 AS mb_ok,
      ABS(r.total_bytes_consumed_gb - (r.total_bytes_consumed_bytes / POW(1024, 3))) < 1e-9 AS gb_ok,
      ABS(r.total_bytes_consumed_tb - (r.total_bytes_consumed_bytes / POW(1024, 4))) < 1e-9 AS tb_ok
    FROM `{args.project_id}.{dataset}.dbt_run_summary` r
    JOIN step_agg s USING (invocation_id)
    WHERE r.invocation_id = (SELECT invocation_id FROM latest)
    """

    rows = list(client.query(accuracy_sql).result())
    if not rows:
        raise SystemExit("No metadata rows found to validate.")

    row = rows[0]
    payload = dict(row.items())
    if payload["bytes_diff"] != 0 or not payload["mb_ok"] or not payload["gb_ok"] or not payload["tb_ok"]:
        raise SystemExit(json.dumps(payload, default=str))

    print(json.dumps({"status": "ok", **payload}, default=str))


if __name__ == "__main__":
    main()
