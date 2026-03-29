{{
    config(
        materialized = 'view',
        tags = ['silver', 'cleaned', 'events']
    )
}}

with source as (
    select * from {{ ref('brz_events') }}
),

traffic_map as (
    select * from {{ ref('seed_traffic_source_mapping') }}
),

enriched as (
    select
        e.event_id,
        e.user_id,
        e.session_id,
        e.sequence_number,
        {{ clean_string('e.event_type') }}                          as event_type,
        e.browser,
        e.traffic_source                                            as raw_traffic_source,
        coalesce(tm.normalized_channel, 'unknown')                  as acquisition_channel,
        e.ip_address,
        e.city,
        e.state,
        e.postal_code,
        e.uri,
        e.created_at,
        e.event_date,

        -- Session-level flags (first/last event in session)
        row_number() over (
            partition by e.session_id
            order by e.sequence_number asc
        )                                                           as session_event_rank,

        e._loaded_at,
        e._dbt_run_id,
        e._source_model

    from source e
    left join traffic_map tm
        on lower(e.traffic_source) = lower(tm.raw_traffic_source)
)

select * from enriched
