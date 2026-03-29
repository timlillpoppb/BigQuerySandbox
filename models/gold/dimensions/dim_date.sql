{{
    config(
        materialized = 'table',
        tags = ['gold', 'dimension', 'date']
    )
}}

-- ─────────────────────────────────────────────────────────────────────────────
-- dim_date: Standard date dimension spanning 2018–2030.
-- Built via dbt_utils.date_spine — no external package dependency.
-- ─────────────────────────────────────────────────────────────────────────────

with date_spine as (
    {{
        dbt_utils.date_spine(
            datepart = "day",
            start_date = "cast('" ~ var('date_spine_start') ~ "' as date)",
            end_date   = "cast('" ~ var('date_spine_end')   ~ "' as date)"
        )
    }}
),

enriched as (
    select
        cast(date_day as date)                              as date_id,
        cast(date_day as date)                              as date_day,
        extract(dayofweek  from date_day)                   as day_of_week,
        format_date('%A',   date_day)                       as day_of_week_name,
        format_date('%a',   date_day)                       as day_of_week_name_short,
        extract(day        from date_day)                   as day_of_month,
        extract(dayofyear  from date_day)                   as day_of_year,
        extract(isoweek    from date_day)                   as week_of_year,
        extract(month      from date_day)                   as month_of_year,
        format_date('%B',   date_day)                       as month_name,
        format_date('%b',   date_day)                       as month_name_short,
        extract(quarter    from date_day)                   as quarter_of_year,
        extract(year       from date_day)                   as year_number,
        date_trunc(date_day, month)                         as month_start,
        date_trunc(date_day, quarter)                       as quarter_start,
        date_trunc(date_day, year)                          as year_start,
        case when extract(dayofweek from date_day) in (1, 7)
             then true else false end                        as is_weekend,
        case when extract(dayofweek from date_day) between 2 and 6
             then true else false end                        as is_weekday
    from date_spine
)

select * from enriched
