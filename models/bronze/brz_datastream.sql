{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key='id',
    incremental_predicates=["updated_at > (select max(updated_at) from {{ this }})"]
) }}

with source as (
    select * from {{ ref('stg_datastream') }}
),

transformed as (
    select
        *,
        {{ add_metadata_columns() }}
    from source
    {% if is_incremental() %}
    where updated_at > (select max(updated_at) from {{ this }})
    {% endif %}
)

select * from transformed