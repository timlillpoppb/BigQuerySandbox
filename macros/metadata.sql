-- Macro to add metadata columns to models
{% macro add_metadata_columns() %}
    , created_at as current_timestamp() as created_at
    , updated_at as current_timestamp() as updated_at
    , 'system' as created_by
    , 'system' as updated_by
{% endmacro %}