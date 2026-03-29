{{
    config(
        materialized = 'view',
        tags = ['silver', 'cleaned', 'users']
    )
}}

with source as (
    select * from {{ ref('brz_users') }}
),

traffic_map as (
    select * from {{ ref('seed_traffic_source_mapping') }}
),

cleaned as (
    select
        user_id,
        {{ clean_string('first_name') }}            as first_name,
        {{ clean_string('last_name') }}             as last_name,
        {{ clean_string('email') }}                 as email,
        age,
        {{ clean_string('gender') }}                as gender,
        {{ clean_string('state') }}                 as state,
        {{ clean_string('city') }}                  as city,
        {{ clean_string('country') }}               as country,
        postal_code,
        latitude,
        longitude,
        traffic_source                              as raw_traffic_source,
        created_at,
        _loaded_at,
        _dbt_run_id,
        _source_model
    from source
),

enriched as (
    select
        c.*,
        coalesce(tm.normalized_channel, 'unknown')  as acquisition_channel,
        coalesce(tm.is_paid, false)                 as is_paid_acquisition,

        -- Derived age band for segmentation
        case
            when c.age < 25  then 'gen_z'
            when c.age < 40  then 'millennial'
            when c.age < 55  then 'gen_x'
            else                  'boomer_plus'
        end                                         as age_band,

        -- Cohort month: subscriber's first month
        {{ subscription_period('c.created_at') }}   as cohort_month

    from cleaned c
    left join traffic_map tm
        on lower(c.raw_traffic_source) = lower(tm.raw_traffic_source)
)

select * from enriched
