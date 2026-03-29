{{
    config(
        materialized = 'table',
        tags = ['gold', 'report', 'subscription', 'kpi']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- rpt_subscription_health: Executive KPI dashboard table.
--
-- One row per calendar month with all top-level subscription health metrics:
-- MRR, ARR, subscriber counts, churn, NRR, CAC proxy, ARPU, payback period.
-- Designed as the single-source-of-truth for the C-suite dashboard.
-- ─────────────────────────────────────────────────────────────────────────────

with mrr_summary as (
    select
        revenue_month,
        sum(monthly_revenue)                                        as total_mrr,
        sum(new_mrr)                                                as new_mrr,
        sum(expansion_mrr)                                          as expansion_mrr,
        sum(contraction_mrr)                                        as contraction_mrr,
        sum(churned_mrr)                                            as churned_mrr,
        sum(retained_mrr)                                           as retained_mrr,
        countif(mrr_movement_type != 'churned')                    as active_subscribers,
        countif(mrr_movement_type = 'new')                         as new_subscribers,
        countif(mrr_movement_type = 'churned')                     as churned_subscribers
    from {{ ref('rpt_mrr') }}
    group by 1
),

with_prior as (
    select
        m.*,
        lag(m.total_mrr) over (order by m.revenue_month)           as prior_mrr,
        lag(m.active_subscribers) over (order by m.revenue_month)  as prior_active_subscribers
    from mrr_summary m
),

session_funnel as (
    select
        date_trunc(session_date, month)                             as activity_month,
        count(distinct session_id)                                  as total_sessions,
        count(distinct user_id)                                     as unique_visitors,
        countif(converted)                                          as converting_sessions,
        {{ safe_divide('countif(converted)', 'count(distinct session_id)') }} as session_conversion_rate
    from {{ ref('fct_user_sessions') }}
    group by 1
)

select
    m.revenue_month,

    -- ── MRR / ARR ─────────────────────────────────────────────────────────────
    m.total_mrr,
    m.total_mrr * 12                                               as arr,
    m.new_mrr,
    m.expansion_mrr,
    m.contraction_mrr,
    m.churned_mrr,
    m.retained_mrr,
    m.total_mrr - coalesce(m.prior_mrr, 0)                        as net_new_mrr,

    -- ── Subscriber Counts ─────────────────────────────────────────────────────
    m.active_subscribers,
    m.new_subscribers,
    m.churned_subscribers,
    m.active_subscribers - coalesce(m.prior_active_subscribers, 0) as net_subscriber_change,

    -- ── Churn & Retention Rates ───────────────────────────────────────────────
    {{ safe_divide('m.churned_subscribers', 'm.prior_active_subscribers') }} as subscriber_churn_rate,
    {{ safe_divide('abs(m.churned_mrr)', 'm.prior_mrr') }}         as revenue_churn_rate,
    {{ safe_divide('m.retained_mrr + m.expansion_mrr', 'm.prior_mrr') }} as net_revenue_retention_rate,

    -- ── ARPU (Average Revenue Per User) ──────────────────────────────────────
    {{ safe_divide('m.total_mrr', 'm.active_subscribers') }}       as arpu,

    -- ── Funnel Metrics ────────────────────────────────────────────────────────
    coalesce(f.total_sessions, 0)                                   as total_sessions,
    coalesce(f.unique_visitors, 0)                                  as unique_visitors,
    coalesce(f.converting_sessions, 0)                              as converting_sessions,
    coalesce(f.session_conversion_rate, 0)                          as session_conversion_rate,

    -- ── Growth Rates ─────────────────────────────────────────────────────────
    {{ safe_divide('m.total_mrr - m.prior_mrr', 'm.prior_mrr') }}  as mrr_growth_rate

from with_prior m
left join session_funnel f on m.revenue_month = f.activity_month
