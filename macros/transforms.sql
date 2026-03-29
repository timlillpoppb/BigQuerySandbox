-- Example transformation macros
{% macro dedupe_by_key(table, key_columns) %}
    select *
    from {{ table }}
    qualify row_number() over (partition by {{ key_columns | join(', ') }} order by updated_at desc) = 1
{% endmacro %}

{% macro clean_column(column) %}
    trim(lower({{ column }}))
{% endmacro %}