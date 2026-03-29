{{
    config(
        materialized = 'table',
        tags = ['bronze', 'raw', 'distribution_centers']
    )
}}

select
    id                                          as distribution_center_id,
    name                                        as distribution_center_name,
    latitude,
    longitude,

    -- Audit columns
    {{ add_metadata_columns() }}

from {{ source('thelook_ecommerce', 'distribution_centers') }}
