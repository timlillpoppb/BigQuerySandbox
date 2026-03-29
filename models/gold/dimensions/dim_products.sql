{{
    config(
        materialized = 'table',
        tags = ['gold', 'dimension', 'products'],
        cluster_by = ['category', 'department']
    )
}}

with latest_snapshot as (
    select * from {{ ref('snap_products') }}
    where dbt_valid_to is null
),

sales_stats as (
    select
        product_id,
        count(distinct order_id)                                    as total_orders,
        count(order_item_id)                                        as total_units_sold,
        sum(sale_price)                                             as total_revenue,
        avg(sale_price)                                             as avg_sale_price,
        sum(gross_margin)                                           as total_gross_margin,
        avg(gross_margin_pct)                                       as avg_gross_margin_pct,
        count(case when is_returned then 1 end)                    as total_returns,
        {{ safe_divide(
            'count(case when is_returned then 1 end)',
            'count(order_item_id)'
        ) }}                                                        as return_rate
    from {{ ref('slv_order_items') }}
    group by 1
)

select
    {{ dbt_utils.generate_surrogate_key(['p.product_id']) }}        as product_sk,
    p.product_id,
    p.product_name,
    p.category,
    p.brand,
    p.department,
    p.sku,
    p.cost,
    p.retail_price,
    p.standard_margin,
    p.standard_margin_pct,
    p.distribution_center_id,
    p.distribution_center_name,

    -- Sales performance
    coalesce(s.total_orders, 0)                                     as total_orders,
    coalesce(s.total_units_sold, 0)                                 as total_units_sold,
    coalesce(s.total_revenue, 0)                                    as total_revenue,
    coalesce(s.avg_sale_price, 0)                                   as avg_sale_price,
    coalesce(s.total_gross_margin, 0)                               as total_gross_margin,
    coalesce(s.avg_gross_margin_pct, 0)                             as avg_gross_margin_pct,
    coalesce(s.total_returns, 0)                                    as total_returns,
    coalesce(s.return_rate, 0)                                      as return_rate,

    -- SCD2 metadata
    p.dbt_scd_id,
    p.dbt_updated_at,
    p.dbt_valid_from,
    p.dbt_valid_to

from latest_snapshot p
left join sales_stats s using (product_id)
