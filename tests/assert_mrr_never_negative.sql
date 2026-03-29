{{ config(severity = 'error', tags = ['data_quality', 'mrr']) }}

-- MRR for active subscribers should never be negative.
-- Churned rows have negative mrr_delta which is expected; exclude them.
select
    revenue_month,
    user_id,
    monthly_revenue
from {{ ref('rpt_mrr') }}
where mrr_movement_type != 'churned'
  and monthly_revenue < 0
