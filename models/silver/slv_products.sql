{{
    config(
        materialized = 'view',
        tags = ['silver', 'cleaned', 'products']
    )
}}

with source as (
    select * from {{ ref('brz_products') }}
),

centers as (
    select * from {{ ref('brz_distribution_centers') }}
),

enriched as (
    select
        p.product_id,
        {{ clean_string('p.product_name') }}    as product_name,
        {{ clean_string('p.category') }}        as category,
        {{ clean_string('p.brand') }}           as brand,
        {{ clean_string('p.department') }}      as department,
        p.sku,
        p.cost,
        p.retail_price,
        p.distribution_center_id,
        c.distribution_center_name,

        -- Margin metrics at product level
        p.retail_price - p.cost                                     as standard_margin,
        {{ safe_divide('p.retail_price - p.cost', 'p.retail_price') }} as standard_margin_pct,

        p._loaded_at,
        p._dbt_run_id,
        p._source_model

    from source p
    left join centers c using (distribution_center_id)
)

select * from enriched
