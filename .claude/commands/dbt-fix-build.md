---
description: Run dbt build, parse all errors and warnings, then fix them iteratively until the build is clean.
argument-hint: [--target dev|staging|prod]
---

Run `dbt build` and fix all errors iteratively until the build passes. Focus on errors first (they block downstream models), then address warnings if they are actionable.

## Steps

### 1. Run the build

```bash
./.venv/Scripts/dbt.exe build --threads 8 --target ${ARGUMENTS:-dev} 2>&1
```

If the build succeeds with 0 errors, done. Otherwise continue.

### 2. Parse errors from run_results.json

```python
import json
with open('target/run_results.json') as f:
    data = json.load(f)

for r in data['results']:
    if r.get('status') in ('error', 'fail'):
        print(r['unique_id'])
        print(' ', (r.get('message') or '')[:600])
        print()
```

### 3. Fix by error type

#### Contract mismatch (`This model has an enforced contract that failed`)
The model selects columns not listed in `_schema.yml`. Read the model SQL to find all output columns, then add the missing ones to the contract in `_schema.yml` with the correct `data_type`.

Common BigQuery types: `string`, `int64`, `float64`, `bool`, `timestamp`, `date`

#### Dataset not found (`Dataset ... was not found in location US`)
Run `/bigquery-datasets-create` to create missing datasets in the correct region.

#### Analytic function in aggregate (`Analytic functions cannot be arguments to aggregate functions`)
BigQuery doesn't allow window functions inside aggregate functions. Fix by splitting into two CTEs:
```sql
-- WRONG:
avg(lag(col) over (partition by x order by col)) as metric

-- RIGHT:
raw_values as (
    select x, lag(col) over (partition by x order by col) as prev_val from ...
),
aggregated as (
    select x, avg(prev_val) as metric from raw_values where prev_val is not null group by 1
)
```

#### Unrecognized column name (`Unrecognized name: X; Did you mean Y?`)
The column was renamed somewhere in the lineage. Grep for the column name across all models to find where it was renamed, then update the reference.

#### `NOT NULL` constraint violation on public data
Public datasets (like `bigquery-public-data`) have data quality issues we can't fix. Downgrade those tests to `warn`:
```yaml
- not_null:
    config:
      severity: warn
- unique:
    config:
      severity: warn
```

#### Source test failures on public data (duplicate emails, null user_ids, unexpected statuses)
Same fix — downgrade to `warn` in `_sources.yml`. These are inherent to the public dataset.

### 4. Re-run after each fix

After fixing a batch of errors, re-run:
```bash
./.venv/Scripts/dbt.exe build --threads 8 --target dev 2>&1 | grep -E "(FAIL|ERROR|Done\.)"
```

Repeat until: `Done. PASS=N WARN=W ERROR=0`

### 5. Run specific failing model

To iterate faster on a single model:
```bash
./.venv/Scripts/dbt.exe run --select <model_name> --target dev
```

## Notes
- Warnings on public data quality tests are expected and acceptable
- Contract errors must be fixed — enforced contracts block model execution entirely
- If a downstream model fails because its upstream is stale/wrong, rebuild with `dbt run --select upstream+ --target dev`
