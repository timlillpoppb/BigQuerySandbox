{{ config(materialized='table') }}

select
    cast(null as string) as run_id,
    cast(null as timestamp) as start_time,
    cast(null as timestamp) as end_time,
    cast(null as string) as models_run,
    cast(null as string) as status
where false