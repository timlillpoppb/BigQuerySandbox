{{
    config(
        materialized = 'incremental',
        incremental_strategy = 'insert_overwrite',
        partition_by = {
            'field': 'created_date',
            'data_type': 'date',
            'granularity': 'day'
        },
        cluster_by = ['product_id', 'product_category'],
        tags = ['bronze', 'raw', 'inventory']
    )
}}

select
    id                                          as inventory_item_id,
    product_id,
    product_category,
    product_name,
    product_brand,
    product_retail_price,
    product_department,
    product_sku,
    product_distribution_center_id,
    cost,
    cast(created_at as timestamp)               as created_at,
    cast(sold_at as timestamp)                  as sold_at,
    date(created_at)                            as created_date,

    -- Audit columns
    {{ add_metadata_columns() }}

from {{ source('thelook_ecommerce', 'inventory_items') }}

{% if is_incremental() %}
    where date(created_at) >= date_sub(current_date(), interval 3 day)
{% endif %}
