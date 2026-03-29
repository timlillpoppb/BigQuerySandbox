{{ config(materialized='table') }}

with dim_data as (
    select distinct
        id,
        name,
        created_at,
        updated_at
    from {{ ref('slv_datastream_cleaned') }}
)

select
    *,
    {{ add_metadata_columns() }}
from dim_data