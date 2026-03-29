{{
    config(
        materialized = 'incremental',
        incremental_strategy = 'merge',
        unique_key = 'order_sk',
        partition_by = {
            'field': 'order_date',
            'data_type': 'date',
            'granularity': 'day'
        },
        cluster_by = ['user_sk', 'billing_month'],
        on_schema_change = 'fail',
        tags = ['gold', 'fact', 'orders']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- fct_orders: Central fact table. One row per order.
-- Joins orders to user and date dimensions. Carries subscription flags
-- and revenue rolled up from line items.
-- ─────────────────────────────────────────────────────────────────────────────

with orders as (
    select * from {{ ref('slv_orders') }}
    {% if is_incremental() %}
        where created_date >= date_sub(current_date(), interval 3 day)
    {% endif %}
),

users as (
    select user_id, user_sk, customer_segment, is_subscriber, cohort_month
    from {{ ref('dim_users') }}
),

item_rollup as (
    select
        order_id,
        sum(sale_price)                                             as order_revenue,
        sum(gross_margin)                                           as order_gross_margin,
        count(order_item_id)                                        as num_items,
        count(case when is_returned then 1 end)                    as num_returned_items
    from {{ ref('slv_order_items') }}
    group by 1
)

select
    {{ dbt_utils.generate_surrogate_key(['o.order_id']) }}          as order_sk,
    o.order_id,
    o.user_id,
    u.user_sk,

    -- Status
    o.status,
    o.is_completed,
    o.is_refunded,

    -- Timestamps
    o.created_at,
    o.shipped_at,
    o.delivered_at,
    o.returned_at,
    o.created_date                                                  as order_date,
    o.order_month,

    -- Fulfillment
    o.num_of_item,
    o.hours_to_ship,
    o.hours_to_deliver,

    -- Revenue (from line items)
    coalesce(i.order_revenue, 0)                                    as order_revenue,
    coalesce(i.order_gross_margin, 0)                               as order_gross_margin,
    coalesce(i.num_items, 0)                                        as num_line_items,
    coalesce(i.num_returned_items, 0)                               as num_returned_items,

    -- Subscription context
    u.is_subscriber,
    u.customer_segment,
    u.cohort_month,

    -- Billing period
    {{ subscription_period('o.created_at') }}                       as billing_month

from orders o
left join users u       on o.user_id = u.user_id
left join item_rollup i on o.order_id = i.order_id
