# dbt Medallion Architecture Project

## Overview

This project implements a FAANG-level Medallion Architecture using dbt Core, featuring:

- **Bronze Layer**: Raw, append-only data ingestion
- **Silver Layer**: Cleaned and transformed business data
- **Gold Layer**: Analytics-ready facts and dimensions

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed data flow and layer descriptions.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Configure BigQuery credentials in `profiles.yml`
3. Run `dbt deps` to install packages
4. Run `dbt build` to build all models

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for coding standards and best practices.

## Deployment

Uses GitHub Actions for CI/CD with state-based incremental builds.