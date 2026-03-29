{{
    config(
        materialized = 'table',
        tags = ['gold', 'report', 'subscription', 'revenue']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- rpt_revenue_by_segment: Revenue decomposition by customer segment, channel,
-- and product category. Used for contribution margin and segment P&L views.
-- ─────────────────────────────────────────────────────────────────────────────

with orders as (
    select
        billing_month,
        user_id,
        order_id,
        order_revenue,
        order_gross_margin,
        customer_segment,
        cohort_month,
        is_subscriber
    from {{ ref('fct_orders') }}
    where is_completed = true
),

users as (
    select user_id, acquisition_channel, age_band, country
    from {{ ref('dim_users') }}
),

items as (
    select
        order_id,
        category,
        department,
        sum(sale_price)     as category_revenue,
        sum(gross_margin)   as category_margin
    from {{ ref('fct_order_items') }}
    where status = 'complete'
    group by 1, 2, 3
)

select
    o.billing_month,
    o.customer_segment,
    u.acquisition_channel,
    u.age_band,
    u.country,
    i.category,
    i.department,

    -- Subscriber vs non-subscriber split
    countif(o.is_subscriber)                                        as subscriber_orders,
    countif(not o.is_subscriber)                                    as non_subscriber_orders,
    count(distinct o.user_id)                                       as unique_buyers,
    count(distinct o.order_id)                                      as total_orders,

    -- Revenue
    sum(o.order_revenue)                                            as total_revenue,
    sum(o.order_gross_margin)                                       as total_gross_margin,
    {{ safe_divide('sum(o.order_gross_margin)', 'sum(o.order_revenue)') }} as gross_margin_pct,

    -- Subscriber revenue share
    {{ safe_divide(
        'sum(case when o.is_subscriber then o.order_revenue else 0 end)',
        'sum(o.order_revenue)'
    ) }}                                                            as subscriber_revenue_share

from orders o
left join users u  using (user_id)
left join items i  using (order_id)
group by 1, 2, 3, 4, 5, 6, 7
