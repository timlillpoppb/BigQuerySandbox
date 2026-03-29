# dbt Medallion Architecture Project

## Overview

This project implements a FAANG-level Medallion Architecture using dbt Core, featuring:

- **Bronze Layer**: Raw, append-only data ingestion
- **Silver Layer**: Cleaned and transformed business data
- **Gold Layer**: Analytics-ready facts and dimensions

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed data flow and layer descriptions.

## Setup

1. Install Python 3.11 (dbt compatibility)
2. Clone the repository
3. Create virtual environment: `python -m venv .venv`
4. Activate: `.venv\Scripts\activate` (Windows)
5. Install dependencies: `make install` or `pip install -r requirements.txt`
6. Configure BigQuery credentials in `profiles.yml`
7. Run `make deps` or `dbt deps` to install packages
8. Run `make build` or `dbt build` to build all models

## Commands

### Basic Commands
- `make build` - Build all models (run + test)
- `make test` - Run all tests
- `make docs` - Generate docs
- `make clean` - Clean target
- `make help` - Show all available commands

### Layer-Specific Commands
- `make run-bronze` - Run bronze layer models
- `make run-silver` - Run silver layer models
- `make run-gold` - Run gold layer models
- `make run-staging` - Run staging models
- `make run-facts` - Run fact tables
- `make run-dims` - Run dimension tables

### Build by Layer
- `make build-bronze` - Build bronze layer
- `make build-silver` - Build silver layer
- `make build-gold` - Build gold layer

### Test by Layer
- `make test-bronze` - Test bronze layer
- `make test-silver` - Test silver layer
- `make test-gold` - Test gold layer
- `make test-data` - Run data tests only
- `make test-schema` - Run schema tests only

### Full Refresh Commands
- `make run-full` - Run all models with full refresh
- `make build-full` - Build all with full refresh

### State-Based Commands (CI/CD)
- `make state-modified` - Run modified models
- `make state-modified-plus` - Run modified + downstream
- `make state-build-modified` - Build modified + downstream

### Custom Selection
- `make run-select SELECT="my_model"` - Run specific model
- `make test-select SELECT="my_model"` - Test specific model
- `make build-select SELECT="my_model"` - Build specific model

### Environment Targets
- `make run-dev` - Run in dev environment
- `make run-staging` - Run in staging environment
- `make run-prod` - Run in prod environment

### Other dbt Operations
- `make compile` - Compile models (dry run)
- `make snapshot` - Update snapshots
- `make seed` - Load seed data
- `make source-freshness` - Check source freshness
- `make debug` - Debug configuration
- `make parse` - Parse and validate project
- `make list` - List all models
- `make docs-serve` - Serve docs locally

Or use VS Code tasks for dbt run/test/build

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for coding standards and best practices.

## Deployment

Uses GitHub Actions for CI/CD with state-based incremental builds.