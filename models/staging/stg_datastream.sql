{{ config(materialized='view') }}

with source as (
    select * from {{ source('datastream', 'raw_table') }}
),

cleaned as (
    select
        id,
        {{ clean_column('name') }} as name,
        cast(amount as float64) as amount,
        cast(created_at as timestamp) as created_at,
        cast(updated_at as timestamp) as updated_at
    from source
    where id is not null
)

select * from cleaned