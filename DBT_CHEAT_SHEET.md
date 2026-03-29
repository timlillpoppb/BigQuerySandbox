# dbt Command Cheat Sheet

This cheat sheet provides all essential dbt commands for the Medallion Architecture project. All commands use the project's Python 3.11 virtual environment.

## Quick Start
```bash
# Activate environment (if not using VS Code)
.\.venv\Scripts\Activate.ps1

# Check dbt version
.\.venv\Scripts\python.exe -m dbt.cli.main --version

# Install dependencies
.\.venv\Scripts\python.exe -m dbt.cli.main deps
```

## Make Commands (Recommended)

For convenience, this project includes comprehensive make commands. Use these instead of direct dbt commands:

### Quick Commands
```bash
make build          # Build all (run + test)
make test           # Run all tests
make run            # Run all models
make docs           # Generate docs
make help           # Show all commands
```

### Layer-Specific Commands
```bash
make run-bronze     # Run bronze layer
make run-silver     # Run silver layer
make run-gold       # Run gold layer
make run-staging    # Run staging models
make run-facts      # Run fact tables
make run-dims       # Run dimensions

make build-bronze   # Build bronze layer
make build-silver   # Build silver layer
make build-gold     # Build gold layer

make test-bronze    # Test bronze layer
make test-silver    # Test silver layer
make test-gold      # Test gold layer
```

### Full Refresh & State-Based
```bash
make run-full               # Run all with full refresh
make build-full             # Build all with full refresh
make state-modified         # Run modified models
make state-modified-plus    # Run modified + downstream
make state-build-modified   # Build modified + downstream
```

### Custom Selection
```bash
make run-select SELECT="my_model"     # Run specific model
make test-select SELECT="my_model"    # Test specific model
make build-select SELECT="my_model"   # Build specific model
```

### Environment Targets
```bash
make run-target-dev       # Run in dev
make run-target-staging   # Run in staging
make run-target-prod      # Run in prod
make test-target-dev      # Test in dev
make test-target-staging  # Test in staging
make test-target-prod     # Test in prod
make build-target-dev     # Build in dev
make build-target-staging # Build in staging
make build-target-prod    # Build in prod
```

### Other Operations
```bash
make compile           # Dry run
make snapshot          # Update snapshots
make seed              # Load seeds
make source-freshness  # Check freshness
make debug             # Debug config
make parse             # Validate project
make list              # List models
make docs-serve        # Serve docs
make clean             # Clean target
```

## BigQuery auth (no service-account key file)

Your org policy blocks `iam.disableServiceAccountKeyCreation`; use OAuth/ADC or OIDC.

- `profiles.yml` should use:
  - `method: oauth`
  - no `keyfile`

- GitHub secrets:
  - `GCP_PROJECT_ID`
  - `GCP_WORKLOAD_IDENTITY_PROVIDER`
  - `GCP_SA_EMAIL`

- Workflow steps (from `.github/workflows/dbt.yml`):
  - `google-github-actions/auth@v1`
  - `google-github-actions/setup-gcloud@v1`
  - `dbt deps`, `dbt build --target dev`, `dbt test --target dev`

## Direct dbt Commands

If you prefer direct dbt commands or need advanced options:

## Core Commands

### Model Execution
```bash
# Run all models
.\.venv\Scripts\python.exe -m dbt.cli.main run

# Run specific model
.\.venv\Scripts\python.exe -m dbt.cli.main run --select my_model

# Run models in bronze layer
.\.venv\Scripts\python.exe -m dbt.cli.main run --select bronze

# Run with full refresh (rebuilds all)
.\.venv\Scripts\python.exe -m dbt.cli.main run --full-refresh

# Dry run (compile only, no execution)
.\.venv\Scripts\python.exe -m dbt.cli.main compile
```

### Testing
```bash
# Run all tests
.\.venv\Scripts\python.exe -m dbt.cli.main test

# Test specific model
.\.venv\Scripts\python.exe -m dbt.cli.main test --select my_model

# Test bronze layer
.\.venv\Scripts\python.exe -m dbt.cli.main test --select bronze

# Run data tests only (not unit tests)
.\.venv\Scripts\python.exe -m dbt.cli.main test --data

# Run schema tests only
.\.venv\Scripts\python.exe -m dbt.cli.main test --schema
```

### Build (Run + Test)
```bash
# Build all (run models + tests)
.\.venv\Scripts\python.exe -m dbt.cli.main build

# Build specific models
.\.venv\Scripts\python.exe -m dbt.cli.main build --select my_model

# Build with full refresh
.\.venv\Scripts\python.exe -m dbt.cli.main build --full-refresh
```

## Model Selection

### By Layer
```bash
# Bronze (raw) layer
.\.venv\Scripts\python.exe -m dbt.cli.main run --select bronze

# Silver (business) layer
.\.venv\Scripts\python.exe -m dbt.cli.main run --select silver

# Gold (presentation) layer
.\.venv\Scripts\python.exe -m dbt.cli.main run --select gold

# Staging models
.\.venv\Scripts\python.exe -m dbt.cli.main run --select stg_*
```

### By Type
```bash
# Facts
.\.venv\Scripts\python.exe -m dbt.cli.main run --select fact_*

# Dimensions
.\.venv\Scripts\python.exe -m dbt.cli.main run --select dim_*

# Snapshots
.\.venv\Scripts\python.exe -m dbt.cli.main snapshot
```

### Advanced Selection
```bash
# Models that depend on a specific model
.\.venv\Scripts\python.exe -m dbt.cli.main run --select +my_model

# Models that my_model depends on
.\.venv\Scripts\python.exe -m dbt.cli.main run --select my_model+

# Exclude models
.\.venv\Scripts\python.exe -m dbt.cli.main run --select bronze --exclude brz_pubsub

# By tag
.\.venv\Scripts\python.exe -m dbt.cli.main run --select tag:important
```

## Environment & Profiles

### Target Environments
```bash
# Development (default)
.\.venv\Scripts\python.exe -m dbt.cli.main run --target dev

# Staging
.\.venv\Scripts\python.exe -m dbt.cli.main run --target staging

# Production
.\.venv\Scripts\python.exe -m dbt.cli.main run --target prod
```

### Profile Management
```bash
# List available profiles
.\.venv\Scripts\python.exe -m dbt.cli.main --profiles-dir . debug

# Validate profile configuration
.\.venv\Scripts\python.exe -m dbt.cli.main debug
```

## State-Based Commands (CI/CD)

### Compare with Git
```bash
# Run only modified models since last commit
.\.venv\Scripts\python.exe -m dbt.cli.main run --select state:modified

# Run modified + downstream
.\.venv\Scripts\python.exe -m dbt.cli.main run --select state:modified+

# Test modified models
.\.venv\Scripts\python.exe -m dbt.cli.main test --select state:modified
```

### Defer to Production
```bash
# Use production manifest for faster runs
.\.venv\Scripts\python.exe -m dbt.cli.main run --defer --state path/to/prod/manifest
```

## Documentation

```bash
# Generate docs
.\.venv\Scripts\python.exe -m dbt.cli.main docs generate

# Serve docs locally
.\.venv\Scripts\python.exe -m dbt.cli.main docs serve

# Generate docs with state
.\.venv\Scripts\python.exe -m dbt.cli.main docs generate --state path/to/state
```

## Debugging & Inspection

```bash
# Show model SQL
.\.venv\Scripts\python.exe -m dbt.cli.main compile --select my_model

# List all models
.\.venv\Scripts\python.exe -m dbt.cli.main list

# Show model dependencies
.\.venv\Scripts\python.exe -m dbt.cli.main list --select +my_model --output json

# Parse project
.\.venv\Scripts\python.exe -m dbt.cli.main parse

# Show project info
.\.venv\Scripts\python.exe -m dbt.cli.main --version
.\.venv\Scripts\python.exe -m dbt.cli.main --help
```

## Seeds & Sources

```bash
# Load seed data
.\.venv\Scripts\python.exe -m dbt.cli.main seed

# Load specific seed
.\.venv\Scripts\python.exe -m dbt.cli.main seed --select my_seed

# Check source freshness
.\.venv\Scripts\python.exe -m dbt.cli.main source freshness
```

## Snapshots

```bash
# Update all snapshots
.\.venv\Scripts\python.exe -m dbt.cli.main snapshot

# Update specific snapshot
.\.venv\Scripts\python.exe -m dbt.cli.main snapshot --select my_snapshot
```

## Package Management

```bash
# Install packages
.\.venv\Scripts\python.exe -m dbt.cli.main deps

# Update packages
.\.venv\Scripts\python.exe -m dbt.cli.main deps --upgrade

# Clean packages
.\.venv\Scripts\python.exe -m dbt.cli.main clean
```

## Performance & Optimization

```bash
# Run with threads
.\.venv\Scripts\python.exe -m dbt.cli.main run --threads 4

# Fail fast on first error
.\.venv\Scripts\python.exe -m dbt.cli.main run --fail-fast

# Continue on error
.\.venv\Scripts\python.exe -m dbt.cli.main run --continue-on-error
```

## Project-Specific Commands

### For This Medallion Project
```bash
# Build bronze layer
.\.venv\Scripts\python.exe -m dbt.cli.main build --select bronze

# Test silver layer
.\.venv\Scripts\python.exe -m dbt.cli.main test --select silver

# Run incremental models only
.\.venv\Scripts\python.exe -m dbt.cli.main run --select config.materialized:incremental

# Check source freshness
.\.venv\Scripts\python.exe -m dbt.cli.main source freshness
```

### Using Makefile (Alternative)
```bash
make build    # Build all
make test     # Run tests
make docs     # Generate docs
make deps     # Install packages
make clean    # Clean target
```

## Troubleshooting

```bash
# Debug connection
.\.venv\Scripts\python.exe -m dbt.cli.main debug

# Show logs
.\.venv\Scripts\python.exe -m dbt.cli.main run --log-level DEBUG

# Validate project
.\.venv\Scripts\python.exe -m dbt.cli.main parse

# Check for issues
.\.venv\Scripts\python.exe -m dbt.cli.main list --output json | jq '.errors'
```

## VS Code Integration

- Use Command Palette (Ctrl+Shift+P) → "Tasks: Run Task" → Select dbt commands
- Or use terminal with the commands above
- All tasks are configured to use the correct Python environment

## Common Workflows

### Development Cycle
```bash
# 1. Parse project
.\.venv\Scripts\python.exe -m dbt.cli.main parse

# 2. Run specific model
.\.venv\Scripts\python.exe -m dbt.cli.main run --select my_model

# 3. Test it
.\.venv\Scripts\python.exe -m dbt.cli.main test --select my_model

# 4. Generate docs
.\.venv\Scripts\python.exe -m dbt.cli.main docs generate
```

### CI/CD Pipeline
```bash
# Install deps
.\.venv\Scripts\python.exe -m dbt.cli.main deps

# Build modified models
.\.venv\Scripts\python.exe -m dbt.cli.main build --select state:modified+

# Generate docs
.\.venv\Scripts\python.exe -m dbt.cli.main docs generate
```

### Production Deployment
```bash
# Full build in production
.\.venv\Scripts\python.exe -m dbt.cli.main build --target prod

# Update snapshots
.\.venv\Scripts\python.exe -m dbt.cli.main snapshot --target prod
```