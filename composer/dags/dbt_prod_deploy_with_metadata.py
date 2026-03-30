from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

DEFAULT_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "project-2ac71b10-d4cb-403a-b2c")
DEFAULT_LOCATION = os.environ.get("GCP_LOCATION", "US")
DEFAULT_METADATA_DATASET = os.environ.get("DBT_METADATA_DATASET", "prod_dataset_ops")
DBT_PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/home/airflow/gcs/repo/dbt")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", DBT_PROJECT_DIR)
DBT_PYTHON = os.environ.get("DBT_PYTHON", "/usr/local/bin/python")
DBT_BIN = os.environ.get("DBT_BIN", "/usr/local/bin/dbt")


def build_metadata_command() -> str:
    return (
        f"cd {DBT_PROJECT_DIR} && "
        f"{DBT_PYTHON} scripts/log_dbt_run_metadata.py "
        f"--project-id {DEFAULT_PROJECT_ID} "
        f"--location {DEFAULT_LOCATION} "
        f"--target-name prod "
        f"--target-dataset prod_dataset "
        f"--metadata-dataset {DEFAULT_METADATA_DATASET} "
        f"--run-results-path target/run_results.json "
        f"--run-started-at '{{{{ ti.xcom_pull(task_ids='prepare_context', key='run_started_at') }}}}' "
        f"--run-completed-at '{{{{ ti.xcom_pull(task_ids='prepare_context', key='run_completed_at') }}}}' "
        f"--dbt-exit-code '{{{{ ti.xcom_pull(task_ids='prepare_context', key='dbt_exit_code') }}}}' "
        f"--github-run-id composer-{{{{ run_id }}}} "
        f"--github-sha '{{{{ dag_run.conf.get('git_sha', '') if dag_run else '' }}}}' "
        f"--github-ref '{{{{ dag_run.conf.get('git_ref', 'composer') if dag_run else 'composer' }}}}'"
    )


with DAG(
    dag_id="dbt_prod_deploy_with_metadata",
    start_date=datetime(2026, 3, 30),
    schedule=None,
    catchup=False,
    tags=["dbt", "bigquery", "prod", "metadata"],
    default_args={"owner": "data-platform"},
    description="Run dbt prod build and persist run metadata to BigQuery",
) as dag:
    start = EmptyOperator(task_id="start")

    def prepare_context(**context):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        context["ti"].xcom_push(key="run_started_at", value=now)
        context["ti"].xcom_push(key="dbt_exit_code", value="1")

    prepare = PythonOperator(task_id="prepare_context", python_callable=prepare_context)

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"export DBT_PROFILES_DIR={DBT_PROFILES_DIR} && "
            f"{DBT_BIN} deps"
        ),
    )

    dbt_build = BashOperator(
        task_id="dbt_build_prod",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"export DBT_PROFILES_DIR={DBT_PROFILES_DIR} && "
            f"{DBT_BIN} build --target prod --threads 4"
        ),
    )

    def finalize_context(**context):
        completed = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ti = context["ti"]
        ti.xcom_push(key="run_completed_at", value=completed)
        build_state = context.get("dag_run")
        _ = build_state
        task_instance = context["dag_run"].get_task_instance("dbt_build_prod")
        ti.xcom_push(key="dbt_exit_code", value="0" if task_instance.state == "success" else "1")

    finalize = PythonOperator(
        task_id="finalize_context",
        python_callable=finalize_context,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    log_metadata = BashOperator(
        task_id="log_run_metadata",
        bash_command=build_metadata_command(),
        trigger_rule=TriggerRule.ALL_DONE,
    )

    validate_capture = BashOperator(
        task_id="validate_run_capture",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"{DBT_PYTHON} scripts/validate_dbt_run_metadata.py "
            f"--project-id {DEFAULT_PROJECT_ID} "
            f"--metadata-dataset {DEFAULT_METADATA_DATASET}"
        ),
        trigger_rule=TriggerRule.ALL_DONE,
    )

    finish = EmptyOperator(task_id="finish", trigger_rule=TriggerRule.ALL_DONE)

    start >> prepare >> dbt_deps >> dbt_build >> finalize >> log_metadata >> validate_capture >> finish
