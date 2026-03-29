{{
    config(
        materialized = 'table',
        tags = ['gold', 'report', 'subscription', 'ltv']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- rpt_customer_ltv: Customer Lifetime Value (CLV/LTV) analysis.
--
-- Computes observed LTV (historical spend) and predicted LTV using
-- average order value × purchase frequency × estimated lifespan.
-- One row per user with full KPI suite.
-- ─────────────────────────────────────────────────────────────────────────────

with users as (
    select
        user_id,
        user_sk,
        cohort_month,
        customer_segment,
        acquisition_channel,
        is_subscriber,
        subscriber_status,
        registered_at,
        total_orders,
        completed_orders,
        first_order_at,
        last_order_at,
        first_order_month,
        last_order_month,
        days_since_last_order,
        lifetime_revenue,
        lifetime_gross_margin,
        avg_order_item_price
    from {{ ref('dim_users') }}
),

monthly_revenue as (
    select
        user_id,
        count(distinct revenue_month)                               as active_months,
        avg(monthly_revenue)                                        as avg_monthly_revenue,
        max(monthly_revenue)                                        as peak_monthly_revenue,
        min(monthly_revenue)                                        as min_monthly_revenue
    from {{ ref('rpt_mrr') }}
    where mrr_movement_type != 'churned'
    group by 1
),

order_intervals as (
    -- Average days between consecutive orders per user
    select
        user_id,
        avg(
            date_diff(
                created_date,
                lag(created_date) over (partition by user_id order by created_date),
                day
            )
        )                                                           as avg_days_between_orders
    from {{ ref('fct_orders') }}
    where is_completed = true
    group by 1
)

select
    u.user_id,
    u.user_sk,
    u.cohort_month,
    u.customer_segment,
    u.acquisition_channel,
    u.is_subscriber,
    u.subscriber_status,
    u.registered_at,
    u.total_orders,
    u.completed_orders,
    u.first_order_at,
    u.last_order_at,
    u.days_since_last_order,

    -- ── Observed LTV metrics ──────────────────────────────────────────────────
    u.lifetime_revenue                                              as observed_ltv,
    u.lifetime_gross_margin                                        as observed_ltv_gross_margin,
    u.avg_order_item_price,

    -- Months from first order to last order (tenure)
    date_diff(
        coalesce(date(u.last_order_at), current_date()),
        date(u.first_order_at),
        month
    )                                                               as tenure_months,

    -- Average Order Value (AOV)
    {{ safe_divide('u.lifetime_revenue', 'u.completed_orders') }}  as avg_order_value,

    -- Purchase frequency (orders per active month)
    {{ safe_divide('u.completed_orders',
                   'greatest(date_diff(coalesce(date(u.last_order_at), current_date()), date(u.first_order_at), month), 1)') }}
                                                                    as orders_per_month,

    -- ── Predicted LTV metrics ─────────────────────────────────────────────────
    -- Simple LTV = AOV × frequency (monthly) × 12-month window
    {{ safe_divide('u.lifetime_revenue', 'u.completed_orders') }}
        * {{ safe_divide('u.completed_orders',
                         'greatest(date_diff(coalesce(date(u.last_order_at), current_date()), date(u.first_order_at), month), 1)') }}
        * 12                                                        as predicted_12m_ltv,

    -- ── Monthly revenue context ───────────────────────────────────────────────
    coalesce(mr.active_months, 0)                                   as active_revenue_months,
    coalesce(mr.avg_monthly_revenue, 0)                             as avg_monthly_revenue,
    coalesce(mr.peak_monthly_revenue, 0)                            as peak_monthly_revenue,

    -- ── Recency / Frequency / Monetary (RFM) scores ──────────────────────────
    -- Recency score (1=churned, 5=very recent)
    case
        when u.days_since_last_order <= 30  then 5
        when u.days_since_last_order <= 60  then 4
        when u.days_since_last_order <= 90  then 3
        when u.days_since_last_order <= 180 then 2
        else 1
    end                                                             as rfm_recency_score,

    -- Frequency score
    case
        when u.completed_orders >= 10 then 5
        when u.completed_orders >= 6  then 4
        when u.completed_orders >= 4  then 3
        when u.completed_orders >= 2  then 2
        else 1
    end                                                             as rfm_frequency_score,

    -- Monetary score
    case
        when u.lifetime_revenue >= 1000 then 5
        when u.lifetime_revenue >= 500  then 4
        when u.lifetime_revenue >= 250  then 3
        when u.lifetime_revenue >= 100  then 2
        else 1
    end                                                             as rfm_monetary_score,

    -- Avg days between orders
    coalesce(oi.avg_days_between_orders, 0)                        as avg_days_between_orders

from users u
left join monthly_revenue mr  using (user_id)
left join order_intervals oi  using (user_id)
