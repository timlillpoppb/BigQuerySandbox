from google.cloud import bigquery
client = bigquery.Client(project='project-2ac71b10-d4cb-403a-b2c')
tables=['rpt_subscription_health','rpt_mrr','dim_users','fct_orders']
for t in tables:
    full=f'project-2ac71b10-d4cb-403a-b2c.dev_dataset.{t}'
    try:
        tbl=client.get_table(full)
        print('FOUND', full, 'rows', tbl.num_rows)
    except Exception as e:
        print('MISSING', full, e)
