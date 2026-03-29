# Copilot Instructions for dbt Medallion Project

## Overview
This workspace implements a FAANG-level Medallion Architecture in dbt Core. Always follow the established patterns and standards.

## Key Guidelines
- Use the Medallion layers: Bronze (raw), Silver (cleaned), Gold (presentation)
- Include metadata columns in all models
- Write tests for all models using dbt-expectations
- Follow naming conventions: stg_, brz_, slv_, fct_, dim_
- Use incremental models where appropriate
- Document all models with descriptions

## When to Use Agents
- DbtValidator: For reviewing new models or changes
- ArchitectureReviewer: For major architectural decisions

## Best Practices
- Always run dbt build before committing
- Use state-based selection for efficient CI/CD
- Monitor data freshness and quality
- Follow the development checklist in DEVELOPMENT.md