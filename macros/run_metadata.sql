-- ─────────────────────────────────────────────────────────────────────────────
-- run_metadata.sql — Utility macros for dbt run introspection
-- ─────────────────────────────────────────────────────────────────────────────

-- Returns basic run context as a struct for use in models or logging.
{% macro get_run_metadata() %}
    struct(
        '{{ invocation_id }}'   as run_id,
        current_timestamp()     as run_started_at,
        '{{ target.name }}'     as target_env,
        '{{ target.project }}'  as gcp_project
    )
{% endmacro %}
