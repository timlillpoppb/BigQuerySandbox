{% snapshot snap_users %}

{{
    config(
        target_schema = 'snapshots',
        unique_key = 'user_id',
        strategy = 'check',
        check_cols = ['email', 'first_name', 'last_name', 'state', 'city', 'country', 'raw_traffic_source'],
        tags = ['snapshot', 'scd2', 'users'],
        invalidate_hard_deletes = true
    )
}}

-- SCD Type 2 snapshot of user profile data.
-- Captures changes to email, name, location, and acquisition channel.
-- dim_users joins to this to build slowly-changing dimension records.
select
    user_id,
    email,
    first_name,
    last_name,
    state,
    city,
    country,
    raw_traffic_source,
    acquisition_channel,
    cohort_month,
    age_band,
    created_at

from {{ ref('slv_users') }}

{% endsnapshot %}
