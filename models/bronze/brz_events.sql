{{
    config(
        materialized = 'incremental',
        incremental_strategy = 'insert_overwrite',
        partition_by = {
            'field': 'event_date',
            'data_type': 'date',
            'granularity': 'day'
        },
        cluster_by = ['user_id', 'event_type', 'session_id'],
        tags = ['bronze', 'raw', 'events']
    )
}}

select
    id                                          as event_id,
    user_id,
    sequence_number,
    session_id,
    event_type,
    ip_address,
    city,
    state,
    postal_code,
    browser,
    traffic_source,
    uri,
    cast(created_at as timestamp)               as created_at,
    date(created_at)                            as event_date,

    -- Audit columns
    {{ add_metadata_columns() }}

from {{ source('thelook_ecommerce', 'events') }}

{% if is_incremental() %}
    where date(created_at) >= date_sub(current_date(), interval 3 day)
{% endif %}
