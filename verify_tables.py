#!/usr/bin/env python
"""Check if rpt_subscription_health table exists in dev_dataset_gold."""

from google.cloud import bigquery

client = bigquery.Client(project='project-2ac71b10-d4cb-403a-b2c')

print("Checking tables in dev_dataset_gold...")
try:
    dataset = client.get_dataset('dev_dataset_gold')
    print(f"✅ Dataset dev_dataset_gold exists")
    
    tables = list(client.list_tables(dataset))
    print(f"\nFound {len(tables)} tables:")
    for table in tables:
        print(f"  - {table.table_id}")
    
    # Check specific table
    if any(t.table_id == 'rpt_subscription_health' for t in tables):
        print("\n✅ rpt_subscription_health EXISTS")
        full_path = 'project-2ac71b10-d4cb-403a-b2c.dev_dataset_gold.rpt_subscription_health'
        tbl = client.get_table(full_path)
        print(f"   Rows: {tbl.num_rows}")
        print(f"   Schema: {len(tbl.schema)} columns")
    else:
        print("\n❌ rpt_subscription_health NOT FOUND in dataset")
        print("\nAvailable report tables:")
        for table in tables:
            if table.table_id.startswith('rpt_'):
                print(f"  - {table.table_id}")

except Exception as e:
    print(f"❌ Error: {e}")
