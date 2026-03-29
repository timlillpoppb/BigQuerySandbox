{{
    config(
        materialized = 'table',
        tags = ['gold', 'report', 'subscription', 'cac']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- rpt_cac_and_payback: Customer Acquisition Cost proxy & payback period.
--
-- Since ad spend data is not available in thelook, we proxy CAC by:
--   - Counting new subscribers per acquisition channel per month
--   - Computing average first-order revenue as the "value recovered"
--   - Estimating payback period as months until cumulative LTV > avg first-month revenue
--
-- This model is designed to be extended when real CAC data is available.
-- ─────────────────────────────────────────────────────────────────────────────

with new_subscribers as (
    -- Users who placed their first order in this month
    select
        user_id,
        acquisition_channel,
        customer_segment,
        cohort_month,
        first_order_month,
        avg_order_value,
        predicted_12m_ltv,
        observed_ltv,
        avg_monthly_revenue,
        tenure_months,
        rfm_recency_score,
        rfm_frequency_score,
        rfm_monetary_score
    from {{ ref('rpt_customer_ltv') }}
    where first_order_month is not null
),

channel_monthly_cohort as (
    select
        first_order_month                                           as cohort_month,
        acquisition_channel,
        customer_segment,
        count(user_id)                                              as new_subscribers,
        avg(avg_order_value)                                        as avg_first_order_value,
        avg(predicted_12m_ltv)                                      as avg_predicted_12m_ltv,
        avg(observed_ltv)                                           as avg_observed_ltv,
        avg(avg_monthly_revenue)                                    as avg_monthly_revenue_per_user,
        avg(tenure_months)                                          as avg_tenure_months,
        avg(rfm_recency_score)                                      as avg_rfm_recency,
        avg(rfm_frequency_score)                                    as avg_rfm_frequency,
        avg(rfm_monetary_score)                                     as avg_rfm_monetary,

        -- LTV:CAC proxy (using first-order value as a CAC proxy baseline)
        -- Real CAC would be: marketing_spend / new_subscribers
        -- Here we show the ratio of 12m predicted LTV to first-order value
        {{ safe_divide('avg(predicted_12m_ltv)', 'avg(avg_order_value)') }} as ltv_to_first_order_ratio,

        -- Payback period proxy: months until avg monthly revenue covers avg first order
        {{ safe_divide('avg(avg_order_value)', 'avg(avg_monthly_revenue)') }} as estimated_payback_months

    from new_subscribers
    group by 1, 2, 3
)

select
    cohort_month,
    acquisition_channel,
    customer_segment,
    new_subscribers,
    avg_first_order_value,
    avg_predicted_12m_ltv,
    avg_observed_ltv,
    avg_monthly_revenue_per_user,
    avg_tenure_months,
    avg_rfm_recency,
    avg_rfm_frequency,
    avg_rfm_monetary,
    ltv_to_first_order_ratio,
    estimated_payback_months,

    -- Composite health score (weighted RFM)
    (avg_rfm_recency * 0.3)
        + (avg_rfm_frequency * 0.35)
        + (avg_rfm_monetary * 0.35)                                as rfm_composite_score

from channel_monthly_cohort
