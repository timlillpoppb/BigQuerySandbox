---
description: Query the gold layer BI report tables in BigQuery and run ad-hoc analyses. Accepts a plain-English question about the data and translates it into a BigQuery SQL query, runs it, and returns the result.
argument-hint: "<plain-English question about the data>"
---

Answer the following business question by querying the gold layer report tables in BigQuery:

**Question:** ${ARGUMENTS}

## Available report tables

All tables live in `project-2ac71b10-d4cb-403a-b2c.dev_dataset_gold` (swap `dev` → `prod` for production data).

| Table | Description | Key columns |
|---|---|---|
| `rpt_mrr` | Monthly Recurring Revenue — one row per user × month | `revenue_month`, `user_id`, `customer_segment`, `cohort_month`, `monthly_revenue`, `mrr_movement_type` (new/expansion/contraction/retained/churned), `new_mrr`, `expansion_mrr`, `contraction_mrr`, `churned_mrr`, `retained_mrr`, `mrr_delta` |
| `rpt_churn` | Monthly churn metrics by segment | `cohort_month` (= revenue month), `customer_segment`, `active_subscribers`, `new_subscribers`, `churned_subscribers`, `total_mrr`, `churn_rate`, `net_new_subscribers` |
| `rpt_cohort_retention` | Cohort retention matrix | `cohort_month`, `customer_segment`, `period_number` (months since first order), `cohort_size`, `active_users`, `retention_rate` |
| `rpt_customer_ltv` | Customer lifetime value | `user_id`, `customer_segment`, `cohort_month`, `first_order_month`, `last_order_month`, `total_orders`, `total_revenue`, `total_gross_margin`, `avg_order_value`, `predicted_ltv`, `avg_days_between_orders` |
| `rpt_revenue_by_segment` | Revenue decomposed by segment, channel, category | `billing_month`, `customer_segment`, `acquisition_channel`, `age_band`, `country`, `category`, `department`, `total_revenue`, `total_gross_margin`, `order_count`, `subscriber_count` |
| `rpt_subscription_health` | Executive KPI dashboard — one row per month | `revenue_month`, `total_mrr`, `arr`, `new_mrr`, `expansion_mrr`, `contraction_mrr`, `churned_mrr`, `net_new_mrr`, `active_subscribers`, `new_subscribers`, `churned_subscribers`, `churn_rate`, `nrr`, `arpu`, `cac_proxy`, `payback_months` |
| `rpt_cac_and_payback` | Customer acquisition cost and payback by channel/segment | `cohort_month`, `acquisition_channel`, `customer_segment`, `new_customers`, `total_revenue_3m`, `total_revenue_6m`, `total_revenue_12m`, `cac_proxy`, `payback_months` |
| `rpt_product_analytics` | Product/category performance and funnel metrics | `event_month`, `category`, `department`, `page_views`, `add_to_carts`, `purchases`, `conversion_rate`, `total_revenue`, `avg_sale_price` |

Supporting dimension/fact tables you may need to join:

| Table | Key columns |
|---|---|
| `dim_users` | `user_id`, `user_sk`, `email`, `acquisition_channel`, `age_band`, `country`, `customer_segment`, `cohort_month`, `lifetime_revenue`, `completed_orders` |
| `dim_products` | `product_id`, `product_sk`, `product_name`, `category`, `department`, `brand`, `retail_price` |
| `dim_date` | `date_day`, `year`, `month_of_year`, `quarter_of_year`, `day_of_week_name`, `is_weekend` |
| `fct_orders` | `order_id`, `user_id`, `order_date`, `billing_month`, `order_revenue`, `order_gross_margin`, `customer_segment`, `status`, `is_completed`, `is_subscriber` |
| `fct_order_items` | `order_item_id`, `order_id`, `product_id`, `sale_price`, `gross_margin`, `status`, `category`, `department` |

## Steps

### 1. Write the SQL

Write a BigQuery SQL query that answers the question. Use the table reference format:
```
`project-2ac71b10-d4cb-403a-b2c.dev_dataset_gold.<table_name>`
```

Tips:
- For time-series questions, order by the date column and limit recent months if the dataset is large
- For "top N" questions, use `ORDER BY ... DESC LIMIT N`
- For percentage calculations, cast numerator to FLOAT64 first: `SAFE_DIVIDE(CAST(numerator AS FLOAT64), denominator)`
- `rpt_mrr` and `rpt_churn` have `revenue_month` / `cohort_month` as DATE fields (first day of month)
- All monetary values are in USD

### 2. Run the query

```bash
"C:\Users\uktim\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\bq.cmd" query \
  --use_legacy_sql=false \
  --project_id=project-2ac71b10-d4cb-403a-b2c \
  --format=pretty \
  '<SQL_QUERY>'
```

For multi-line queries, write them to a temp file first:
```bash
cat > /tmp/bq_query.sql << 'EOF'
<SQL_QUERY>
EOF
"C:\Users\uktim\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\bq.cmd" query \
  --use_legacy_sql=false \
  --project_id=project-2ac71b10-d4cb-403a-b2c \
  --format=pretty < /tmp/bq_query.sql
```

### 3. Interpret and present results

After running the query, summarize the key findings in plain English. Include:
- Direct answer to the question
- Notable patterns, outliers, or trends
- Any caveats about data quality or coverage

## Common question patterns

**MRR / revenue trend:**
```sql
SELECT revenue_month, SUM(total_mrr) AS mrr, SUM(new_mrr) AS new_mrr, SUM(churned_mrr) AS churned_mrr
FROM `...dev_dataset_gold.rpt_churn`
GROUP BY 1 ORDER BY 1 DESC LIMIT 12
```

**Churn rate by segment:**
```sql
SELECT cohort_month, customer_segment, ROUND(churn_rate * 100, 2) AS churn_pct
FROM `...dev_dataset_gold.rpt_churn`
WHERE cohort_month >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
ORDER BY 1 DESC, 2
```

**Cohort retention at month 3:**
```sql
SELECT cohort_month, customer_segment, ROUND(retention_rate * 100, 1) AS retention_pct
FROM `...dev_dataset_gold.rpt_cohort_retention`
WHERE period_number = 3
ORDER BY 1 DESC
```

**Top revenue categories:**
```sql
SELECT category, SUM(total_revenue) AS revenue, SUM(order_count) AS orders
FROM `...dev_dataset_gold.rpt_revenue_by_segment`
GROUP BY 1 ORDER BY 2 DESC LIMIT 10
```

**Executive health snapshot (latest month):**
```sql
SELECT * FROM `...dev_dataset_gold.rpt_subscription_health`
ORDER BY revenue_month DESC LIMIT 1
```
