{{
    config(
        materialized = 'table',
        tags = ['gold', 'report', 'product']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- rpt_product_analytics: Product performance report.
-- One row per product with revenue, margin, return, and category rank metrics.
-- ─────────────────────────────────────────────────────────────────────────────

with items as (
    select * from {{ ref('fct_order_items') }}
    where status = 'complete'
),

product_metrics as (
    select
        product_id,
        product_name,
        category,
        brand,
        department,
        count(order_item_id)                                        as total_units_sold,
        count(distinct order_id)                                    as total_orders,
        count(distinct user_id)                                     as unique_buyers,
        sum(sale_price)                                             as total_revenue,
        avg(sale_price)                                             as avg_sale_price,
        sum(gross_margin)                                           as total_gross_margin,
        avg(gross_margin_pct)                                       as avg_gross_margin_pct,
        countif(is_returned)                                        as total_returns,
        {{ safe_divide('countif(is_returned)', 'count(order_item_id)') }} as return_rate,
        min(created_at)                                             as first_sold_at,
        max(created_at)                                             as last_sold_at
    from items
    group by 1, 2, 3, 4, 5
)

select
    product_id,
    product_name,
    category,
    brand,
    department,
    total_units_sold,
    total_orders,
    unique_buyers,
    total_revenue,
    avg_sale_price,
    total_gross_margin,
    avg_gross_margin_pct,
    total_returns,
    return_rate,
    first_sold_at,
    last_sold_at,

    -- Rank within category
    rank() over (partition by category order by total_revenue desc) as revenue_rank_in_category,
    rank() over (partition by category order by total_units_sold desc) as units_rank_in_category,

    -- Overall rank
    rank() over (order by total_revenue desc)                       as overall_revenue_rank

from product_metrics
