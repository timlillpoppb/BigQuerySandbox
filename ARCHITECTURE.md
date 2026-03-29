# Medallion Architecture

## Layers

### Bronze (Raw)
- Append-only ingestion
- Minimal transformation
- Audit trail for all data
- Sources: Datastream (incremental merge), Pub/Sub (streaming)

### Silver (Business)
- Data cleaning and deduplication
- Business logic application
- Relationship establishment
- Late-arriving data handling

### Gold (Presentation)
- Fact and dimension tables
- Star schema for analytics
- SCD Type 2 for dimensions
- BI-ready data

## Data Flow

Raw Sources → Bronze → Staging → Silver → Gold

## Metadata

All tables include:
- created_at
- updated_at
- created_by
- updated_by

## dbt Run Metadata

Tracked in `metadata_dbt_runs` table for monitoring and auditing.