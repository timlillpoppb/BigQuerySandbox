{{
    config(
        materialized = 'table',
        tags = ['bronze', 'raw', 'users'],
        cluster_by = ['country', 'traffic_source']
    )
}}

select
    id                                          as user_id,
    first_name,
    last_name,
    email,
    age,
    gender,
    state,
    street_address,
    postal_code,
    city,
    country,
    latitude,
    longitude,
    traffic_source,
    cast(created_at as timestamp)               as created_at,

    -- Audit columns
    {{ add_metadata_columns() }}

from {{ source('thelook_ecommerce', 'users') }}
