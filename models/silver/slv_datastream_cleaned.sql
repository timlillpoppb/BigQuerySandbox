{{ config(materialized='view') }}

with deduped as (
    {{ dedupe_by_key(ref('brz_datastream'), ['id']) }}
),

cleaned as (
    select
        id,
        name,
        amount,
        created_at,
        updated_at,
        created_by,
        updated_by
    from deduped
    where amount > 0
)

select * from cleaned