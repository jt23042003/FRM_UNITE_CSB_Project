"""
Script to create the banks_v2_failed_requests table for audit logging.
This table stores all failed/invalid requests for audit purposes.

Usage: python backend/scripts/create_failed_requests_table.py
"""

import psycopg2
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONNECTION_PARAMS

def create_failed_requests_table():
    """Create the banks_v2_failed_requests table if it doesn't exist"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_CONNECTION_PARAMS["host"],
            port=DB_CONNECTION_PARAMS["port"],
            dbname=DB_CONNECTION_PARAMS["database"],
            user=DB_CONNECTION_PARAMS["user"],
            password=DB_CONNECTION_PARAMS["password"]
        )
        cur = conn.cursor()
        
        # Read and execute the SQL file
        sql_file_path = 'backend/scripts/create_failed_requests_table.sql'
        with open(sql_file_path, 'r') as f:
            sql = f.read()
        
        # Execute the SQL
        cur.execute(sql)
        conn.commit()
        
        print("✅ Successfully created banks_v2_failed_requests table")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to create banks_v2_failed_requests table: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_failed_requests_table()

