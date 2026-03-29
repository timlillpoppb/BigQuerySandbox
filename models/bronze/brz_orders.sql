{{
    config(
        materialized = 'incremental',
        incremental_strategy = 'insert_overwrite',
        partition_by = {
            'field': 'created_date',
            'data_type': 'date',
            'granularity': 'day'
        },
        cluster_by = ['user_id', 'status'],
        tags = ['bronze', 'raw', 'orders']
    )
}}

select
    order_id,
    user_id,
    status,
    gender,
    num_of_item,
    cast(created_at as timestamp)               as created_at,
    cast(shipped_at as timestamp)               as shipped_at,
    cast(delivered_at as timestamp)             as delivered_at,
    cast(returned_at as timestamp)              as returned_at,
    date(created_at)                            as created_date,

    -- Audit columns
    {{ add_metadata_columns() }}

from {{ source('thelook_ecommerce', 'orders') }}

{% if is_incremental() %}
    -- Reprocess the last 3 days to capture late-arriving updates
    where date(created_at) >= date_sub(current_date(), interval 3 day)
{% endif %}
