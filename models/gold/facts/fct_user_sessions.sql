{{
    config(
        materialized = 'incremental',
        incremental_strategy = 'merge',
        unique_key = 'session_sk',
        partition_by = {
            'field': 'session_date',
            'data_type': 'date',
            'granularity': 'day'
        },
        cluster_by = ['user_id', 'acquisition_channel'],
        tags = ['gold', 'fact', 'sessions']
    )
}}

-- Aggregates clickstream events into session-level facts.
-- One row per session (not per event).

with events as (
    select * from {{ ref('slv_events') }}
    {% if is_incremental() %}
        where event_date >= date_sub(current_date(), interval 3 day)
    {% endif %}
),

session_agg as (
    select
        session_id,
        user_id,
        min(created_at)                                             as session_start,
        max(created_at)                                             as session_end,
        min(event_date)                                             as session_date,
        count(event_id)                                             as num_events,
        max(session_event_rank)                                     as max_event_rank,
        any_value(acquisition_channel)                              as acquisition_channel,
        any_value(browser)                                          as browser,
        any_value(city)                                             as city,
        any_value(state)                                            as state,

        -- Funnel flags
        countif(event_type = 'product')                            as product_views,
        countif(event_type = 'cart')                               as cart_adds,
        countif(event_type = 'purchase')                           as purchases,
        countif(event_type = 'cancel')                             as cancels

    from events
    group by session_id, user_id
),

users as (
    select user_id, user_sk, customer_segment, cohort_month, is_subscriber
    from {{ ref('dim_users') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['s.session_id', 's.user_id']) }} as session_sk,
    s.session_id,
    s.user_id,
    u.user_sk,
    s.session_start,
    s.session_end,
    s.session_date,
    timestamp_diff(s.session_end, s.session_start, second)         as session_duration_sec,
    s.num_events,
    s.acquisition_channel,
    s.browser,
    s.city,
    s.state,
    s.product_views,
    s.cart_adds,
    s.purchases,
    s.cancels,
    case when s.purchases > 0 then true else false end              as converted,
    u.customer_segment,
    u.is_subscriber,
    u.cohort_month

from session_agg s
left join users u using (user_id)
