{{
    config(
        materialized = 'table',
        tags = ['gold', 'dimension', 'date']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- dim_date: Standard date dimension spanning 2018–2030.
-- Generated via dbt_date package. Covers all thelook transaction history.
-- ─────────────────────────────────────────────────────────────────────────────

with date_spine as (
    {{
        dbt_date.get_date_dimension(
            var('date_spine_start'),
            var('date_spine_end')
        )
    }}
)

select
    date_day                            as date_id,
    date_day,
    day_of_week,
    day_of_week_name,
    day_of_week_name_short,
    day_of_month,
    day_of_year,
    week_of_year,
    month_of_year,
    month_name,
    month_name_short,
    quarter_of_year,
    year_number,
    date_trunc(date_day, month)         as month_start,
    date_trunc(date_day, quarter)       as quarter_start,
    date_trunc(date_day, year)          as year_start,
    case when day_of_week in (1, 7) then true else false end as is_weekend,
    case when day_of_week between 2 and 6 then true else false end as is_weekday

from date_spine
