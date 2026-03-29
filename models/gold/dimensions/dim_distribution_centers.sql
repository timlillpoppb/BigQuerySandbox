{{
    config(
        materialized = 'table',
        tags = ['gold', 'dimension', 'distribution_centers']
    )
}}

select
    {{ dbt_utils.generate_surrogate_key(['distribution_center_id']) }} as distribution_center_sk,
    distribution_center_id,
    distribution_center_name,
    latitude,
    longitude,
    _loaded_at,
    _dbt_run_id

from {{ ref('brz_distribution_centers') }}
