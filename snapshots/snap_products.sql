{% snapshot snap_products %}

{{
    config(
        target_schema = 'snapshots',
        unique_key = 'product_id',
        strategy = 'check',
        check_cols = ['product_name', 'category', 'brand', 'retail_price', 'cost'],
        tags = ['snapshot', 'scd2', 'products'],
        invalidate_hard_deletes = true
    )
}}

-- SCD Type 2 snapshot of product catalog.
-- Captures price and category changes so historical orders reflect the product
-- attributes at time of purchase.
select
    product_id,
    product_name,
    category,
    brand,
    department,
    sku,
    cost,
    retail_price,
    standard_margin,
    standard_margin_pct,
    distribution_center_id,
    distribution_center_name

from {{ ref('slv_products') }}

{% endsnapshot %}
