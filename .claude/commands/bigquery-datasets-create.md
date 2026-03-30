---
description: Create all BigQuery datasets required by the dbt project in the correct region, based on profiles.yml targets.
argument-hint: [region, defaults to US]
---

Create all BigQuery datasets needed by the dbt project. Reads `profiles.yml` and `dbt_project.yml` to determine the project ID, dataset names, and environments.

## Steps

### 1. Read config

Read `profiles.yml` to get:
- GCP project ID
- All dataset names across all targets (dev, staging, prod)

Read `dbt_project.yml` to check if `generate_schema_name` macro routes models to layer-specific datasets (e.g. `dev_dataset_bronze`, `dev_dataset_silver`, etc.).

### 2. Determine region

Use $ARGUMENTS if provided, otherwise default to `US`.

**Important:** `bigquery-public-data` datasets only exist in `US` or `EU` multi-regions. If the project sources from `bigquery-public-data`, the region MUST be `US` or `EU` — single regions like `us-east5` will fail with permission errors.

### 3. Check for existing datasets and their regions

```python
from google.cloud import bigquery
from google.auth import default

creds, _ = default()
client = bigquery.Client(project=PROJECT_ID, credentials=creds)

for ds in client.list_datasets():
    full = client.get_dataset(ds.dataset_id)
    print(ds.dataset_id, full.location)
```

If any datasets exist in the wrong region, delete and recreate them (they will be empty at this stage).

### 4. Create datasets

```python
datasets_to_create = [
    'dev_dataset_bronze', 'dev_dataset_silver', 'dev_dataset_gold', 'dev_dataset_seeds',
    'staging_dataset_bronze', 'staging_dataset_silver', 'staging_dataset_gold', 'staging_dataset_seeds',
    'prod_dataset_bronze', 'prod_dataset_silver', 'prod_dataset_gold', 'prod_dataset_seeds',
]

for ds_id in datasets_to_create:
    # Check if exists and in right region first
    try:
        existing = client.get_dataset(ds_id)
        if existing.location != REGION:
            print(f"Recreating {ds_id} (was {existing.location})")
            client.delete_dataset(ds_id, delete_contents=True, not_found_ok=True)
            raise Exception("recreate")
        else:
            print(f"OK: {ds_id} already in {REGION}")
            continue
    except Exception:
        pass

    dataset = bigquery.Dataset(f"{PROJECT_ID}.{ds_id}")
    dataset.location = REGION
    client.create_dataset(dataset, exists_ok=True)
    print(f"Created: {ds_id}")
```

Use `.venv/Scripts/python.exe` (or the active venv python) to run this.

## Common issues

- **"Not found: Dataset ... was not found in location US"** — dataset exists in a different region. Delete and recreate.
- **`bq` CLI fails** — install bq or use the Python `google-cloud-bigquery` client instead (it's already installed in the dbt venv).
- **Permission denied** — ensure ADC is set up: `gcloud auth application-default login` and `gcloud auth application-default set-quota-project PROJECT_ID`
