{{
    config(
        materialized = 'table',
        partition_by = {
            'field': 'revenue_month',
            'data_type': 'date',
            'granularity': 'month'
        },
        tags = ['gold', 'report', 'subscription', 'mrr']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- rpt_mrr: Monthly Recurring Revenue
--
-- Treats completed orders in a calendar month as "subscription revenue".
-- Computes MRR, new MRR, churned MRR, expansion MRR, and net new MRR.
-- Each row = one user × one month.
-- ─────────────────────────────────────────────────────────────────────────────

with monthly_revenue as (
    select
        billing_month                                               as revenue_month,
        user_id,
        customer_segment,
        cohort_month,
        sum(order_revenue)                                          as monthly_revenue,
        count(order_id)                                             as orders_in_month
    from {{ ref('fct_orders') }}
    where is_completed = true
    group by 1, 2, 3, 4
),

with_prior as (
    select
        m.*,
        date_sub(m.revenue_month, interval 1 month)                as prior_month,
        lag(m.monthly_revenue) over (
            partition by m.user_id
            order by m.revenue_month
        )                                                           as prior_month_revenue
    from monthly_revenue m
),

classified as (
    select
        w.revenue_month,
        w.user_id,
        w.customer_segment,
        w.cohort_month,
        w.monthly_revenue,
        w.orders_in_month,
        w.prior_month_revenue,

        -- MRR movement classification
        case
            when w.prior_month_revenue is null      then 'new'
            when w.monthly_revenue > w.prior_month_revenue then 'expansion'
            when w.monthly_revenue < w.prior_month_revenue then 'contraction'
            else 'retained'
        end                                                         as mrr_movement_type,

        -- MRR deltas
        coalesce(w.monthly_revenue, 0)
            - coalesce(w.prior_month_revenue, 0)                   as mrr_delta

    from with_prior w
),

-- Identify churned users: present last month, absent this month
churned as (
    select
        date_add(prev.revenue_month, interval 1 month)              as revenue_month,
        prev.user_id,
        prev.customer_segment,
        prev.cohort_month,
        0                                                           as monthly_revenue,
        0                                                           as orders_in_month,
        prev.monthly_revenue                                        as prior_month_revenue,
        'churned'                                                   as mrr_movement_type,
        -prev.monthly_revenue                                       as mrr_delta
    from monthly_revenue prev
    where not exists (
        select 1 from monthly_revenue curr
        where curr.user_id = prev.user_id
          and curr.revenue_month = date_add(prev.revenue_month, interval 1 month)
    )
),

combined as (
    select * from classified
    union all
    select * from churned
)

select
    revenue_month,
    user_id,
    customer_segment,
    cohort_month,
    monthly_revenue,
    orders_in_month,
    prior_month_revenue,
    mrr_movement_type,
    mrr_delta,

    -- Convenience flags for aggregation
    case when mrr_movement_type = 'new'         then monthly_revenue else 0 end as new_mrr,
    case when mrr_movement_type = 'expansion'   then mrr_delta       else 0 end as expansion_mrr,
    case when mrr_movement_type = 'contraction' then mrr_delta       else 0 end as contraction_mrr,
    case when mrr_movement_type = 'churned'     then mrr_delta       else 0 end as churned_mrr,
    case when mrr_movement_type = 'retained'    then monthly_revenue else 0 end as retained_mrr

from combined
