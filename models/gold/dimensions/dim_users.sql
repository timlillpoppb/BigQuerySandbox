{{
    config(
        materialized = 'table',
        tags = ['gold', 'dimension', 'users'],
        cluster_by = ['country', 'acquisition_channel', 'customer_segment']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- dim_users: Subscriber dimension with current profile + subscription metrics.
-- Joins to snap_users for SCD2-aware history; the latest snapshot record
-- represents the current state. Segment classification drives BI dashboards.
-- ─────────────────────────────────────────────────────────────────────────────

with latest_snapshot as (
    -- Pull current-state user record from SCD2 snapshot
    select * from {{ ref('snap_users') }}
    where dbt_valid_to is null
),

order_stats as (
    -- Lifetime order metrics per user
    select
        user_id,
        count(order_id)                                             as total_orders,
        sum(case when is_completed then 1 else 0 end)              as completed_orders,
        min(created_at)                                             as first_order_at,
        max(created_at)                                             as last_order_at,
        min(order_month)                                            as first_order_month,
        max(order_month)                                            as last_order_month,
        date_diff(current_date(), date(max(created_at)), day)      as days_since_last_order
    from {{ ref('slv_orders') }}
    group by 1
),

revenue_stats as (
    -- Lifetime revenue per user (completed items only)
    select
        user_id,
        sum(sale_price)                                             as lifetime_revenue,
        avg(sale_price)                                             as avg_order_item_price,
        sum(gross_margin)                                           as lifetime_gross_margin
    from {{ ref('slv_order_items') }}
    where status = 'complete'
    group by 1
),

final as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['u.user_id']) }}       as user_sk,

        -- Natural key
        u.user_id,

        -- Profile (current state from snapshot)
        u.email,
        u.first_name,
        u.last_name,
        u.city,
        u.state,
        u.country,
        u.acquisition_channel,
        u.age_band,
        u.cohort_month,
        u.created_at                                                as registered_at,

        -- Order activity
        coalesce(o.total_orders, 0)                                 as total_orders,
        coalesce(o.completed_orders, 0)                             as completed_orders,
        o.first_order_at,
        o.last_order_at,
        o.first_order_month,
        o.last_order_month,
        coalesce(o.days_since_last_order, 9999)                    as days_since_last_order,

        -- Revenue
        coalesce(r.lifetime_revenue, 0)                             as lifetime_revenue,
        coalesce(r.lifetime_gross_margin, 0)                       as lifetime_gross_margin,
        coalesce(r.avg_order_item_price, 0)                        as avg_order_item_price,

        -- Subscription classification
        case
            when coalesce(o.total_orders, 0) >= {{ var('min_orders_for_subscriber') }}
            then true else false
        end                                                         as is_subscriber,

        case
            when coalesce(o.days_since_last_order, 9999) <= {{ var('churn_inactivity_days') }}
            then 'active'
            when coalesce(o.total_orders, 0) = 0
            then 'never_ordered'
            else 'churned'
        end                                                         as subscriber_status,

        -- Customer value segment
        case
            when coalesce(r.lifetime_revenue, 0) >= 500 then 'high_value'
            when coalesce(r.lifetime_revenue, 0) >= 150 then 'standard'
            else 'low_value'
        end                                                         as customer_segment,

        -- SCD2 metadata
        u.dbt_scd_id,
        u.dbt_updated_at,
        u.dbt_valid_from,
        u.dbt_valid_to

    from latest_snapshot u
    left join order_stats o    using (user_id)
    left join revenue_stats r  using (user_id)
)

select * from final
