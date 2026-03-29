{{
    config(
        materialized = 'table',
        tags = ['gold', 'report', 'subscription', 'cohort']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- rpt_cohort_retention: Classic cohort retention matrix.
--
-- Rows = cohort (month of first order).
-- Columns = months since first order (period_number 0, 1, 2, ...).
-- Value = % of cohort still active (made at least one purchase) in that month.
--
-- BI tools (Looker, Tableau) can pivot this directly into a retention heatmap.
-- ─────────────────────────────────────────────────────────────────────────────

with user_cohorts as (
    select
        user_id,
        cohort_month,
        customer_segment
    from {{ ref('dim_users') }}
    where cohort_month is not null
),

user_activity as (
    select distinct
        user_id,
        billing_month
    from {{ ref('fct_orders') }}
    where is_completed = true
),

cohort_activity as (
    select
        uc.user_id,
        uc.cohort_month,
        uc.customer_segment,
        ua.billing_month,
        date_diff(ua.billing_month, uc.cohort_month, month)        as period_number
    from user_cohorts uc
    inner join user_activity ua using (user_id)
    where ua.billing_month >= uc.cohort_month
),

cohort_sizes as (
    select
        cohort_month,
        customer_segment,
        count(distinct user_id)                                     as cohort_size
    from user_cohorts
    group by 1, 2
),

period_active as (
    select
        cohort_month,
        customer_segment,
        period_number,
        count(distinct user_id)                                     as active_users
    from cohort_activity
    group by 1, 2, 3
)

select
    pa.cohort_month,
    pa.customer_segment,
    cs.cohort_size,
    pa.period_number,
    pa.active_users,
    {{ safe_divide('pa.active_users', 'cs.cohort_size') }}          as retention_rate,

    -- Rolling labels for BI
    date_add(pa.cohort_month, interval pa.period_number month)      as activity_month

from period_active pa
inner join cohort_sizes cs
    on pa.cohort_month = cs.cohort_month
    and pa.customer_segment = cs.customer_segment
