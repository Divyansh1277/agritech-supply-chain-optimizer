import sqlite3
import pandas as pd
import os

def load_csv_to_sqlite(db_path, csv_dir, schema_path):
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    
    # Initialize schema
    print(f"Initializing schema from {schema_path}...")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    
    # Tables to load
    tables = {
        'mandi_master': 'mandi_master.csv',
        'crop_master': 'crop_mapping.csv',
        'mandi_arrivals': 'mandi_arrivals.csv',
        'price_msp': 'price_and_msp.csv',
        'weather_daily': 'weather_sensors.csv',
        'transport_logistics': 'transport_logistics.csv'
    }
    
    for table_name, file_name in tables.items():
        file_path = os.path.join(csv_dir, file_name)
        if os.path.exists(file_path):
            print(f"Loading {file_name} into {table_name}...")
            df = pd.read_csv(file_path)
            # Use replace to avoid duplicate key errors if script is run multiple times
            df.to_sql(table_name, conn, if_exists='replace', index=False)
        else:
            print(f"Warning: {file_path} not found.")
            
    print("Executing analytics views...")
    views_path = os.path.join(os.path.dirname(schema_path), 'views.sql')
    if os.path.exists(views_path):
        with open(views_path, 'r') as f:
            views_sql = f.read()
        conn.executescript(views_sql)
    else:
        print(f"Views file {views_path} not found. Skipping.")
        
    conn.close()
    print("Database loading complete!")

if __name__ == "__main__":
    load_csv_to_sqlite(
        db_path="data/processed/agritech.db",
        csv_dir="data/processed",
        schema_path="sql/schema.sql"
    )
