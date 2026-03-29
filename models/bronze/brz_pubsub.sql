{{ config(materialized='table') }}

with source as (
    select * from {{ source('pubsub', 'events') }}
),

transformed as (
    select
        event_id as id,
        event_data,
        event_timestamp as created_at,
        event_timestamp as updated_at,
        {{ add_metadata_columns() }}
    from source
)

select * from transformed