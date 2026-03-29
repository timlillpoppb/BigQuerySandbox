{{ config(severity='error') }}

select id, count(*) as cnt
from {{ ref('brz_datastream') }}
group by id
having cnt > 1