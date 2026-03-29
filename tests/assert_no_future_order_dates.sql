{{ config(severity = 'warn', tags = ['data_quality', 'orders']) }}

-- Orders should not have a created_at timestamp in the future.
-- This catches bad data from the source system or timezone mishandling.
select
    order_id,
    user_id,
    created_at,
    order_date
from {{ ref('fct_orders') }}
where order_date > current_date()
