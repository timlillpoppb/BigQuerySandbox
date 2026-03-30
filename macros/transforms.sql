-- ─────────────────────────────────────────────────────────────────────────────
-- transforms.sql — Reusable transformation macros
-- ─────────────────────────────────────────────────────────────────────────────

-- Deduplicates a CTE/table by a set of key columns, keeping the latest row.
{% macro dedupe_by_key(table, key_columns, order_col='created_at') %}
    select *
    from {{ table }}
    qualify row_number() over (
        partition by {{ key_columns | join(', ') }}
        order by {{ order_col }} desc
    ) = 1
{% endmacro %}

-- Trims, lowercases, and returns NULL for empty strings.
{% macro clean_string(column) %}
    nullif(trim(lower({{ column }})), '')
{% endmacro %}

-- NULL-safe division. Parentheses are required around both arguments to
-- prevent operator-precedence bugs when callers pass expressions like
-- 'a - b' as the numerator (without parens, SQL parses: a - b/denominator).
{% macro safe_divide(numerator, denominator) %}
    case
        when ({{ denominator }}) = 0 or ({{ denominator }}) is null then null
        else ({{ numerator }}) / ({{ denominator }})
    end
{% endmacro %}

-- Truncates a date column to the start of its month (billing period proxy).
{% macro subscription_period(date_col) %}
    date_trunc(cast({{ date_col }} as date), month)
{% endmacro %}
