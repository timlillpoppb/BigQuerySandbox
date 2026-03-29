{{
    config(
        materialized = 'incremental',
        incremental_strategy = 'insert_overwrite',
        partition_by = {
            'field': 'created_date',
            'data_type': 'date',
            'granularity': 'day'
        },
        cluster_by = ['order_id', 'user_id', 'status'],
        tags = ['bronze', 'raw', 'order_items']
    )
}}

select
    id                                          as order_item_id,
    order_id,
    user_id,
    product_id,
    inventory_item_id,
    status,
    sale_price,
    cast(created_at as timestamp)               as created_at,
    cast(shipped_at as timestamp)               as shipped_at,
    cast(delivered_at as timestamp)             as delivered_at,
    cast(returned_at as timestamp)              as returned_at,
    date(created_at)                            as created_date,

    -- Audit columns
    {{ add_metadata_columns() }}

from {{ source('thelook_ecommerce', 'order_items') }}

{% if is_incremental() %}
    where date(created_at) >= date_sub(current_date(), interval 3 day)
{% endif %}
