{{ config(severity = 'error', tags = ['data_quality', 'churn']) }}

-- Churn rate must be a valid proportion (0–1).
-- Null is acceptable when prior_active_subscribers = 0 (first month).
select
    cohort_month,
    customer_segment,
    subscriber_churn_rate
from {{ ref('rpt_churn') }}
where subscriber_churn_rate is not null
  and (subscriber_churn_rate < 0 or subscriber_churn_rate > 1)
