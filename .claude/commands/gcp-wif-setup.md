---
description: Set up GCP Workload Identity Federation for GitHub Actions OIDC auth. Eliminates the need for service account JSON keys.
argument-hint: [github-repo e.g. owner/repo]
---

Set up GCP Workload Identity Federation so GitHub Actions can authenticate to GCP via OIDC (no service account keys required).

## What this does
- Creates a GCP service account for GitHub Actions
- Grants it BigQuery and GCS permissions
- Creates a Workload Identity Pool + OIDC provider bound to the GitHub repo
- Creates any required GCS buckets
- Prints the exact secret values to add to GitHub

## Steps

### 1. Gather inputs

Read `profiles.yml` to get the GCP project ID. If $ARGUMENTS is provided use it as the GitHub repo (owner/repo format), otherwise read the git remote: `git remote get-url origin` and parse the owner/repo.

### 2. Run setup commands

Use the gcloud binary. Find it first:
```bash
find /c/Users -name "gcloud" -not -path "*/lib/*" 2>/dev/null | head -1
```

Run these in order:

```bash
GCLOUD="<path-to-gcloud>"
PROJECT_ID="<from-profiles.yml>"
REPO="<owner/repo>"
SA_NAME="dbt-github-actions"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Auth check
"$GCLOUD" auth list

# Service account
"$GCLOUD" iam service-accounts create $SA_NAME \
  --project=$PROJECT_ID \
  --display-name="dbt GitHub Actions"

# IAM bindings
"$GCLOUD" projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" --role="roles/bigquery.dataEditor"

"$GCLOUD" projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" --role="roles/bigquery.jobUser"

"$GCLOUD" projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" --role="roles/storage.objectAdmin"

# Workload Identity Pool
"$GCLOUD" iam workload-identity-pools create "github-pool" \
  --project=$PROJECT_ID --location="global" \
  --display-name="GitHub Actions Pool"

# OIDC provider
"$GCLOUD" iam workload-identity-pools providers create-oidc "github-provider" \
  --project=$PROJECT_ID --location="global" \
  --workload-identity-pool="github-pool" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='$REPO'"

# Bind SA to pool
POOL_ID=$("$GCLOUD" iam workload-identity-pools describe github-pool \
  --project=$PROJECT_ID --location=global --format="value(name)")

"$GCLOUD" iam service-accounts add-iam-policy-binding $SA_EMAIL \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/$POOL_ID/attribute.repository/$REPO"
```

### 3. Enable required APIs

```bash
"$GCLOUD" services enable iamcredentials.googleapis.com --project=$PROJECT_ID
```

### 4. Create GCS bucket for dbt manifests

Use the Python BigQuery client if gsutil/bq aren't available:
```python
from google.cloud import storage
client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(f"dbt-manifests-{PROJECT_ID}")
bucket.location = "US"
client.create_bucket(bucket)
```

### 5. Print secret values

```bash
PROVIDER=$("$GCLOUD" iam workload-identity-pools providers describe github-provider \
  --project=$PROJECT_ID --location=global \
  --workload-identity-pool=github-pool --format="value(name)")

echo "GCP_PROJECT_ID:                  $PROJECT_ID"
echo "GCP_SA_EMAIL:                    $SA_EMAIL"
echo "GCP_WORKLOAD_IDENTITY_PROVIDER:  $PROVIDER"
echo "GCS_BUCKET:                      dbt-manifests-$PROJECT_ID"
```

### 6. Tell the user

Present the 4 secret values in a table and instruct the user to add them at:
**github.com/{REPO} → Settings → Secrets and variables → Actions → New repository secret**

## Important notes
- If `gcloud` isn't on PATH, find it under `~/AppData/Local/Google/Cloud SDK/`
- If `bq` fails with "python3.14 not found", use the Python `google-cloud-bigquery` client instead
- The IAM Service Account Credentials API must be enabled (`iamcredentials.googleapis.com`) — enable it if the workflow fails with a 403 on token impersonation
- All BigQuery datasets must be in the same region as the data sources (use `US` for `bigquery-public-data`)
