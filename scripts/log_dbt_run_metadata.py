#!/usr/bin/env python3
"""Persist dbt production run metadata and BigQuery bytes consumption.

This script is designed for CI/CD usage and guarantees idempotent writes for a run
by deleting/reinserting rows for a given invocation_id.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from google.cloud import bigquery


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    value = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def pick_start_end_from_timing(timing: List[Dict[str, Any]]) -> Tuple[Optional[datetime], Optional[datetime]]:
    starts: List[datetime] = []
    ends: List[datetime] = []
    for item in timing or []:
        s = parse_iso(item.get("started_at"))
        e = parse_iso(item.get("completed_at"))
        if s:
            starts.append(s)
        if e:
            ends.append(e)
    return (min(starts) if starts else None, max(ends) if ends else None)


def safe_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def safe_int(v: Any) -> int:
    try:
        return int(v)
    except Exception:
        return 0


def mib(bytes_value: int) -> float:
    return bytes_value / (1024.0**2)


def gib(bytes_value: int) -> float:
    return bytes_value / (1024.0**3)


def tib(bytes_value: int) -> float:
    return bytes_value / (1024.0**4)


def ensure_dataset_and_tables(client: bigquery.Client, project_id: str, metadata_dataset: str) -> None:
    dataset_id = f"{project_id}.{metadata_dataset}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)

    steps_table = f"`{project_id}.{metadata_dataset}.dbt_run_job_metadata`"
    runs_table = f"`{project_id}.{metadata_dataset}.dbt_run_summary`"

    client.query(
        f"""
        CREATE TABLE IF NOT EXISTS {steps_table} (
            invocation_id STRING NOT NULL,
            target_name STRING,
            project_id STRING,
            run_started_at TIMESTAMP,
            run_completed_at TIMESTAMP,
            model_unique_id STRING,
            model_name STRING,
            resource_type STRING,
            materialization STRING,
            dbt_status STRING,
            job_id STRING,
            job_state STRING,
            job_result STRING,
            error_message STRING,
            bytes_consumed_bytes INT64,
            bytes_consumed_mb FLOAT64,
            bytes_consumed_gb FLOAT64,
            bytes_consumed_tb FLOAT64,
            node_started_at TIMESTAMP,
            node_completed_at TIMESTAMP,
            execution_time_seconds FLOAT64,
            github_run_id STRING,
            github_sha STRING,
            github_ref STRING,
            inserted_at TIMESTAMP
        )
        PARTITION BY DATE(inserted_at)
        CLUSTER BY invocation_id, dbt_status, model_name
        """
    ).result()

    client.query(
        f"""
        CREATE TABLE IF NOT EXISTS {runs_table} (
            invocation_id STRING NOT NULL,
            target_name STRING,
            project_id STRING,
            run_started_at TIMESTAMP,
            run_completed_at TIMESTAMP,
            run_status STRING,
            total_steps INT64,
            success_steps INT64,
            failed_steps INT64,
            total_bytes_consumed_bytes INT64,
            total_bytes_consumed_mb FLOAT64,
            total_bytes_consumed_gb FLOAT64,
            total_bytes_consumed_tb FLOAT64,
            github_run_id STRING,
            github_sha STRING,
            github_ref STRING,
            inserted_at TIMESTAMP
        )
        PARTITION BY DATE(inserted_at)
        CLUSTER BY invocation_id, run_status
        """
    ).result()


def load_run_results(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_job_bytes(
    client: bigquery.Client,
    location: str,
    project_id: str,
    job_ids: List[str],
) -> Dict[str, Dict[str, Any]]:
    if not job_ids:
        return {}

    sql = f"""
    SELECT
        job_id,
        state,
        IF(error_result IS NULL, 'success', error_result.reason) AS job_result,
        total_bytes_processed
    FROM `region-{location.lower()}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE project_id = @project_id
      AND job_id IN UNNEST(@job_ids)
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("project_id", "STRING", project_id),
            bigquery.ArrayQueryParameter("job_ids", "STRING", job_ids),
        ]
    )

    rows = client.query(sql, job_config=job_config).result()
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        out[row["job_id"]] = {
            "state": row["state"],
            "job_result": row["job_result"],
            "bytes": safe_int(row["total_bytes_processed"]),
        }
    return out


def build_step_rows(
    run_results: Dict[str, Any],
    invocation_id: str,
    target_name: str,
    project_id: str,
    run_started_at: datetime,
    run_completed_at: datetime,
    github_run_id: str,
    github_sha: str,
    github_ref: str,
    job_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    inserted_at = datetime.now(timezone.utc)

    for result in run_results.get("results", []):
        unique_id = result.get("unique_id", "")
        adapter = result.get("adapter_response", {}) or {}
        status = result.get("status", "unknown")
        execution_time = safe_float(result.get("execution_time", 0))
        timing = result.get("timing", [])
        node_started_at, node_completed_at = pick_start_end_from_timing(timing)

        resource_type = unique_id.split(".")[0] if "." in unique_id else "unknown"
        model_name = unique_id.split(".")[-1] if unique_id else "unknown"
        materialization = result.get("config", {}).get("materialized") if isinstance(result.get("config"), dict) else None

        job_id = adapter.get("job_id") or adapter.get("jobId") or ""
        error_message = result.get("message")

        bytes_processed = safe_int(adapter.get("bytes_processed") or adapter.get("bytesProcessed") or 0)
        job_state = adapter.get("state")
        job_result = "success" if status in {"success", "pass"} else status

        if job_id and job_id in job_lookup:
            bytes_processed = safe_int(job_lookup[job_id].get("bytes", bytes_processed))
            job_state = job_lookup[job_id].get("state", job_state)
            job_result = job_lookup[job_id].get("job_result", job_result)

        rows.append(
            {
                "invocation_id": invocation_id,
                "target_name": target_name,
                "project_id": project_id,
                "run_started_at": run_started_at,
                "run_completed_at": run_completed_at,
                "model_unique_id": unique_id,
                "model_name": model_name,
                "resource_type": resource_type,
                "materialization": materialization,
                "dbt_status": status,
                "job_id": job_id,
                "job_state": job_state,
                "job_result": job_result,
                "error_message": error_message,
                "bytes_consumed_bytes": bytes_processed,
                "bytes_consumed_mb": mib(bytes_processed),
                "bytes_consumed_gb": gib(bytes_processed),
                "bytes_consumed_tb": tib(bytes_processed),
                "node_started_at": node_started_at,
                "node_completed_at": node_completed_at,
                "execution_time_seconds": execution_time,
                "github_run_id": github_run_id,
                "github_sha": github_sha,
                "github_ref": github_ref,
                "inserted_at": inserted_at,
            }
        )

    return rows


def upsert_rows(
    client: bigquery.Client,
    project_id: str,
    metadata_dataset: str,
    invocation_id: str,
    step_rows: List[Dict[str, Any]],
    run_row: Dict[str, Any],
) -> None:
    steps_table = f"{project_id}.{metadata_dataset}.dbt_run_job_metadata"
    runs_table = f"{project_id}.{metadata_dataset}.dbt_run_summary"

    delete_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("invocation_id", "STRING", invocation_id)]
    )
    client.query(
        f"DELETE FROM `{steps_table}` WHERE invocation_id = @invocation_id", job_config=delete_config
    ).result()
    client.query(
        f"DELETE FROM `{runs_table}` WHERE invocation_id = @invocation_id", job_config=delete_config
    ).result()

    if step_rows:
        errors = client.insert_rows_json(steps_table, step_rows)
        if errors:
            raise RuntimeError(f"Failed inserting step rows: {errors}")

    errors = client.insert_rows_json(runs_table, [run_row])
    if errors:
        raise RuntimeError(f"Failed inserting run row: {errors}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--location", default="US")
    parser.add_argument("--target-name", default="prod")
    parser.add_argument("--target-dataset", default="prod_dataset")
    parser.add_argument("--metadata-dataset", default="prod_dataset_ops")
    parser.add_argument("--run-results-path", default="target/run_results.json")
    parser.add_argument("--run-started-at", default="")
    parser.add_argument("--run-completed-at", default="")
    parser.add_argument("--dbt-exit-code", default="0")
    parser.add_argument("--github-run-id", default="")
    parser.add_argument("--github-sha", default="")
    parser.add_argument("--github-ref", default="")
    args = parser.parse_args()

    client = bigquery.Client(project=args.project_id)
    ensure_dataset_and_tables(client, args.project_id, args.metadata_dataset)

    run_results = load_run_results(Path(args.run_results_path))

    invocation_id = (
        run_results.get("metadata", {}).get("invocation_id")
        or f"github-{args.github_run_id}-{args.github_sha[:8]}"
    )

    run_started_at = parse_iso(args.run_started_at)
    run_completed_at = parse_iso(args.run_completed_at)

    if not run_started_at or not run_completed_at:
        all_timing = []
        for r in run_results.get("results", []):
            all_timing.extend(r.get("timing", []))
        guessed_start, guessed_end = pick_start_end_from_timing(all_timing)
        run_started_at = run_started_at or guessed_start or datetime.now(timezone.utc)
        run_completed_at = run_completed_at or guessed_end or datetime.now(timezone.utc)

    all_job_ids: List[str] = []
    for result in run_results.get("results", []):
        adapter = result.get("adapter_response", {}) or {}
        job_id = adapter.get("job_id") or adapter.get("jobId")
        if job_id:
            all_job_ids.append(job_id)

    all_job_ids = sorted(set(all_job_ids))
    job_lookup = fetch_job_bytes(client, args.location, args.project_id, all_job_ids)

    step_rows = build_step_rows(
        run_results=run_results,
        invocation_id=invocation_id,
        target_name=args.target_name,
        project_id=args.project_id,
        run_started_at=run_started_at,
        run_completed_at=run_completed_at,
        github_run_id=args.github_run_id,
        github_sha=args.github_sha,
        github_ref=args.github_ref,
        job_lookup=job_lookup,
    )

    success_steps = sum(1 for r in step_rows if r["dbt_status"] in {"success", "pass"})
    failed_steps = sum(1 for r in step_rows if r["dbt_status"] not in {"success", "pass"})
    total_bytes = sum(safe_int(r["bytes_consumed_bytes"]) for r in step_rows)

    run_status = "success" if safe_int(args.dbt_exit_code) == 0 and failed_steps == 0 else "failure"

    run_row = {
        "invocation_id": invocation_id,
        "target_name": args.target_name,
        "project_id": args.project_id,
        "run_started_at": run_started_at,
        "run_completed_at": run_completed_at,
        "run_status": run_status,
        "total_steps": len(step_rows),
        "success_steps": success_steps,
        "failed_steps": failed_steps,
        "total_bytes_consumed_bytes": total_bytes,
        "total_bytes_consumed_mb": mib(total_bytes),
        "total_bytes_consumed_gb": gib(total_bytes),
        "total_bytes_consumed_tb": tib(total_bytes),
        "github_run_id": args.github_run_id,
        "github_sha": args.github_sha,
        "github_ref": args.github_ref,
        "inserted_at": datetime.now(timezone.utc),
    }

    upsert_rows(
        client=client,
        project_id=args.project_id,
        metadata_dataset=args.metadata_dataset,
        invocation_id=invocation_id,
        step_rows=step_rows,
        run_row=run_row,
    )

    print(
        json.dumps(
            {
                "status": "ok",
                "invocation_id": invocation_id,
                "step_count": len(step_rows),
                "total_bytes_consumed_bytes": total_bytes,
                "run_status": run_status,
            }
        )
    )


if __name__ == "__main__":
    main()
