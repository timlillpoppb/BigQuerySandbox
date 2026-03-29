{{
    config(
        materialized = 'view',
        tags = ['silver', 'cleaned', 'order_items']
    )
}}

with items as (
    select * from {{ ref('brz_order_items') }}
),

products as (
    select * from {{ ref('brz_products') }}
),

inventory as (
    select * from {{ ref('brz_inventory_items') }}
),

enriched as (
    select
        i.order_item_id,
        i.order_id,
        i.user_id,
        i.product_id,
        i.inventory_item_id,
        lower(trim(i.status))                                       as status,
        i.sale_price,
        i.created_at,
        i.shipped_at,
        i.delivered_at,
        i.returned_at,
        i.created_date,

        -- Product attributes denormalized for BI convenience
        p.product_name,
        p.category,
        p.brand,
        p.department,
        p.retail_price,

        -- Margin calculation using inventory cost
        coalesce(inv.cost, p.cost)                                  as unit_cost,
        i.sale_price - coalesce(inv.cost, p.cost)                  as gross_margin,
        {{ safe_divide('i.sale_price - coalesce(inv.cost, p.cost)',
                       'i.sale_price') }}                           as gross_margin_pct,

        -- Return flag
        case when i.returned_at is not null then true
             else false end                                         as is_returned,

        i._loaded_at,
        i._dbt_run_id,
        i._source_model

    from items i
    left join products p
        on i.product_id = p.product_id
    left join inventory inv
        on i.inventory_item_id = inv.inventory_item_id
)

select * from enriched
