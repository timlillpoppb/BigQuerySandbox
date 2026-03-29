{{
    config(
        materialized = 'table',
        tags = ['bronze', 'raw', 'products'],
        cluster_by = ['category', 'department', 'brand']
    )
}}

select
    id                                          as product_id,
    name                                        as product_name,
    category,
    brand,
    department,
    sku,
    cost,
    retail_price,
    distribution_center_id,

    -- Audit columns
    {{ add_metadata_columns() }}

from {{ source('thelook_ecommerce', 'products') }}
