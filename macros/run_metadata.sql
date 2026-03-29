-- Macro for logging dbt runs
{% macro log_dbt_run() %}
    {% if execute %}
        {% set run_id = invocation_id %}
        {% set start_time = run_started_at %}
        {% set end_time = run_completed_at %}
        {% set models = [] %}
        {% for node in graph.nodes.values() if node.resource_type == 'model' %}
            {% do models.append(node.name) %}
        {% endfor %}
        insert into {{ var('metadata_schema', 'metadata') }}.dbt_runs (
            run_id,
            start_time,
            end_time,
            models_run,
            status
        ) values (
            '{{ run_id }}',
            '{{ start_time }}',
            '{{ end_time }}',
            '{{ models | join(', ') }}',
            'success'
        );
    {% endif %}
{% endmacro %}