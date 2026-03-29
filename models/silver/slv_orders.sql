{{
    config(
        materialized = 'view',
        tags = ['silver', 'cleaned', 'orders']
    )
}}

with source as (
    select * from {{ ref('brz_orders') }}
),

normalized as (
    select
        order_id,
        user_id,
        num_of_item,
        created_at,
        shipped_at,
        delivered_at,
        returned_at,
        created_date,

        -- Normalize status to consistent lowercase values
        lower(trim(status))                                         as status,

        -- Derived flags for subscription logic
        case when lower(trim(status)) = 'complete'   then true
             else false end                                         as is_completed,
        case when lower(trim(status)) in ('returned', 'cancelled')
             then true else false end                               as is_refunded,

        -- Fulfillment cycle time in hours (for SLA tracking)
        timestamp_diff(shipped_at, created_at, hour)               as hours_to_ship,
        timestamp_diff(delivered_at, shipped_at, hour)             as hours_to_deliver,

        -- Billing period (month of order — used in MRR roll-up)
        {{ subscription_period('created_at') }}                    as order_month,

        _loaded_at,
        _dbt_run_id,
        _source_model

    from source
)

select * from normalized
