-- Adds standard audit columns to any model.
-- Usage: SELECT col1, col2, {{ add_metadata_columns() }} FROM source
{% macro add_metadata_columns() %}
    current_timestamp()      as _loaded_at,
    '{{ invocation_id }}'    as _dbt_run_id,
    '{{ this.name }}'        as _source_model
{% endmacro %}
