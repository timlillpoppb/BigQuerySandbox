{{ config(materialized='table') }}

with fact_data as (
    select
        id,
        amount,
        created_at as transaction_date,
        'datastream' as source
    from {{ ref('slv_datastream_cleaned') }}
    union all
    select
        id,
        0 as amount,  -- assume events don't have amount
        created_at as transaction_date,
        'pubsub' as source
    from {{ ref('brz_pubsub') }}
)

select
    *,
    {{ add_metadata_columns() }}
from fact_data