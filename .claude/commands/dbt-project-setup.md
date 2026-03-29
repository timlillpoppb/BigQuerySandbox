---
description: Full local environment setup for this dbt project on a new machine — venv, deps, BigQuery auth, and first build.
---

Set up a fresh local development environment for this dbt project.

## Steps

### 1. Check Python version

This project requires Python 3.11. Check:
```bash
python --version
```

If not 3.11, install it from python.org or via winget: `winget install Python.Python.3.11`

### 2. Create virtual environment

```bash
python -m venv .venv311
```

### 3. Install dbt

```bash
./.venv311/Scripts/pip install dbt-bigquery==1.8.3
```

Verify:
```bash
./.venv311/Scripts/dbt.exe --version
```

### 4. Install dbt packages

```bash
./.venv311/Scripts/dbt.exe deps
```

### 5. Authenticate to GCP

```bash
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project project-2ac71b10-d4cb-403a-b2c
gcloud config set project project-2ac71b10-d4cb-403a-b2c
```

If `gcloud` is not on PATH, find it:
```bash
find ~/AppData/Local/Google -name "gcloud" 2>/dev/null | head -1
```

Then add `~/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin` to PATH.

### 6. Verify BigQuery connection

```bash
./.venv311/Scripts/dbt.exe debug --target dev
```

All checks should pass. If BigQuery connection fails, check:
- `profiles.yml` location set to `US` (not a single region like `us-east5`)
- OAuth credentials are fresh

### 7. Create BigQuery datasets

Run `/bigquery-datasets-create` to create all required datasets in the `US` region.

### 8. First build

```bash
./.venv311/Scripts/dbt.exe build --threads 8 --target dev
```

Expected result: `PASS=N WARN=11 ERROR=0` (11 warnings are expected public data quality issues).

If errors appear, run `/dbt-fix-build`.

### 9. Make commands (optional)

Install GNU make for Windows to use `make build`, `make test` etc:
```powershell
winget install GnuWin32.Make
```

Then add `C:\Program Files (x86)\GnuWin32\bin` to PATH (restart terminal after).

## Common issues

- **`dbt` not found** — activate the venv first: `.\.venv311\Scripts\Activate.ps1`
- **ExecutionPolicy error** — run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **Quota project warning** — run: `gcloud auth application-default set-quota-project <project-id>`
- **Dataset not found in location US** — datasets were created in wrong region; run `/bigquery-datasets-create`
