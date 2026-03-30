{{
    config(
        materialized = 'table',
        partition_by = {
            'field': 'cohort_month',
            'data_type': 'date',
            'granularity': 'month'
        },
        tags = ['gold', 'report', 'subscription', 'churn']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- rpt_churn: Monthly churn metrics by customer segment.
--
-- Churn definition: subscriber who had revenue last month but none this month.
-- Reports monthly churn rate, subscriber counts, and net subscriber change.
-- ─────────────────────────────────────────────────────────────────────────────

with mrr as (
    select * from {{ ref('rpt_mrr') }}
),

monthly_subscribers as (
    select
        revenue_month,
        customer_segment,
        countif(mrr_movement_type != 'churned')                     as active_subscribers,
        countif(mrr_movement_type = 'new')                          as new_subscribers,
        countif(mrr_movement_type = 'churned')                      as churned_subscribers,
        sum(monthly_revenue)                                        as total_mrr,
        sum(new_mrr)                                                as new_mrr,
        sum(churned_mrr)                                            as churned_mrr,
        sum(retained_mrr)                                           as retained_mrr,
        sum(expansion_mrr)                                          as expansion_mrr,
        sum(contraction_mrr)                                        as contraction_mrr
    from mrr
    group by 1, 2
),

with_prior as (
    select
        m.*,
        lag(m.active_subscribers) over (
            partition by m.customer_segment
            order by m.revenue_month
        )                                                           as prior_active_subscribers,
        lag(m.total_mrr) over (
            partition by m.customer_segment
            order by m.revenue_month
        )                                                           as prior_total_mrr
    from monthly_subscribers m
)

select
    revenue_month                                                   as cohort_month,
    customer_segment,
    active_subscribers,
    new_subscribers,
    churned_subscribers,
    prior_active_subscribers,
    total_mrr,
    new_mrr,
    churned_mrr,
    retained_mrr,
    expansion_mrr,
    contraction_mrr,

    -- Churn rate = churned / prior active
    {{ safe_divide('churned_subscribers', 'prior_active_subscribers') }}        as subscriber_churn_rate,

    -- Revenue churn rate
    {{ safe_divide('abs(churned_mrr)', 'prior_total_mrr') }}                    as revenue_churn_rate,

    -- Net revenue retention rate = (retained + expansion) / prior MRR
    {{ safe_divide('retained_mrr + expansion_mrr', 'prior_total_mrr') }}        as net_revenue_retention_rate,

    -- Net subscriber growth
    new_subscribers - churned_subscribers                                       as net_subscriber_change

from with_prior
