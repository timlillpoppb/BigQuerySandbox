{{
    config(
        materialized = 'view',
        tags = ['silver', 'cleaned', 'inventory']
    )
}}

with source as (
    select * from {{ ref('brz_inventory_items') }}
)

select
    inventory_item_id,
    product_id,
    {{ clean_string('product_category') }}  as product_category,
    {{ clean_string('product_name') }}      as product_name,
    {{ clean_string('product_brand') }}     as product_brand,
    {{ clean_string('product_department') }} as product_department,
    product_sku,
    product_retail_price,
    product_distribution_center_id,
    cost,
    created_at,
    sold_at,
    created_date,

    -- Derived: was this item sold?
    case when sold_at is not null then true else false end   as is_sold,

    -- Days in inventory before sale
    date_diff(
        cast(coalesce(sold_at, current_timestamp()) as date),
        cast(created_at as date),
        day
    )                                                       as days_in_inventory,

    _loaded_at,
    _dbt_run_id,
    _source_model

from source
