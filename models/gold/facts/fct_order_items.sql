{{
    config(
        materialized = 'incremental',
        incremental_strategy = 'merge',
        unique_key = 'order_item_sk',
        partition_by = {
            'field': 'order_date',
            'data_type': 'date',
            'granularity': 'day'
        },
        cluster_by = ['product_id', 'category'],
        tags = ['gold', 'fact', 'order_items']
    )
}}

with items as (
    select * from {{ ref('slv_order_items') }}
    {% if is_incremental() %}
        where created_date >= date_sub(current_date(), interval 3 day)
    {% endif %}
),

users as (
    select user_id, user_sk, customer_segment, cohort_month
    from {{ ref('dim_users') }}
),

products as (
    select product_id, product_sk, category, department
    from {{ ref('dim_products') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['i.order_item_id']) }}     as order_item_sk,
    i.order_item_id,
    i.order_id,
    i.user_id,
    u.user_sk,
    i.product_id,
    p.product_sk,

    -- Product attributes
    i.product_name,
    i.category,
    i.brand,
    i.department,

    -- Status
    i.status,
    i.is_returned,

    -- Revenue & margin
    i.sale_price,
    i.retail_price,
    i.unit_cost,
    i.gross_margin,
    i.gross_margin_pct,

    -- Timestamps
    i.created_at,
    i.created_date                                                  as order_date,

    -- Dimension context
    u.customer_segment,
    u.cohort_month

from items i
left join users u    on i.user_id    = u.user_id
left join products p on i.product_id = p.product_id
