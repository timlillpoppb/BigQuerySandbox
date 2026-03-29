-- ─────────────────────────────────────────────────────────────────────────────
-- generate_schema_name.sql — Environment-aware schema routing
--
-- prod  → schema name as-is  (e.g. bronze, silver, gold)
-- other → target.schema + "_" + custom_schema  (e.g. dev_dataset_bronze)
--
-- This prevents dev/staging runs from overwriting production schemas.
-- ─────────────────────────────────────────────────────────────────────────────
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- elif target.name == 'prod' -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ default_schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
