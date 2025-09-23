#!/usr/bin/env python3
"""
Script to check and fix the template_responses table structure.
"""

import psycopg2
from config import DB_CONNECTION_PARAMS

def fix_template_responses_table():
    """Check and fix the template_responses table structure"""
    
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # First, let's see what columns currently exist
                cur.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'template_responses'
                    ORDER BY ordinal_position
                """)
                
                existing_columns = cur.fetchall()
                print("Current template_responses table structure:")
                for col in existing_columns:
                    print(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
                
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'template_responses'
                    )
                """)
                
                table_exists = cur.fetchone()[0]
                print(f"\nTable exists: {table_exists}")
                
                if not table_exists:
                    print("Creating template_responses table...")
                    cur.execute("""
                        CREATE TABLE template_responses (
                            id SERIAL PRIMARY KEY,
                            case_id INTEGER NOT NULL REFERENCES case_main(case_id) ON DELETE CASCADE,
                            template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
                            assigned_to VARCHAR(50) NOT NULL,
                            responses JSONB NOT NULL,
                            status VARCHAR(50) DEFAULT 'pending_approval',
                            department VARCHAR(100),
                            approved_by VARCHAR(50),
                            approved_at TIMESTAMP,
                            rejection_reason TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    print("✅ Table created successfully!")
                else:
                    # Check if we need to rename the primary key column
                    if 'response_id' in [col[0] for col in existing_columns] and 'id' not in [col[0] for col in existing_columns]:
                        print("Renaming response_id to id...")
                        try:
                            cur.execute("ALTER TABLE template_responses RENAME COLUMN response_id TO id")
                            print("✅ Renamed response_id to id")
                        except Exception as e:
                            print(f"⚠️  Could not rename column: {e}")
                    
                    # Add missing columns if they don't exist
                    required_columns = {
                        'template_id': 'INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE',
                        'assigned_to': 'VARCHAR(50) NOT NULL',
                        'responses': 'JSONB NOT NULL',
                        'status': 'VARCHAR(50) DEFAULT \'pending_approval\'',
                        'department': 'VARCHAR(100)',
                        'approved_by': 'VARCHAR(50)',
                        'approved_at': 'TIMESTAMP',
                        'rejection_reason': 'TEXT',
                        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                        'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                    }
                    
                    existing_column_names = [col[0] for col in existing_columns]
                    
                    for col_name, col_definition in required_columns.items():
                        if col_name not in existing_column_names:
                            print(f"Adding missing column: {col_name}")
                            try:
                                cur.execute(f"ALTER TABLE template_responses ADD COLUMN {col_name} {col_definition}")
                                print(f"✅ Added column: {col_name}")
                            except Exception as e:
                                print(f"⚠️  Could not add column {col_name}: {e}")
                        else:
                            print(f"✅ Column {col_name} already exists")
                    
                    # Remove old unused columns if they exist
                    old_columns_to_remove = ['field_id', 'response_value', 'response_date']
                    for old_col in old_columns_to_remove:
                        if old_col in existing_column_names:
                            print(f"Removing old column: {old_col}")
                            try:
                                cur.execute(f"ALTER TABLE template_responses DROP COLUMN {old_col}")
                                print(f"✅ Removed column: {old_col}")
                            except Exception as e:
                                print(f"⚠️  Could not remove column {old_col}: {e}")
                    
                    # Fix case_id to be NOT NULL
                    print("Making case_id NOT NULL...")
                    try:
                        cur.execute("ALTER TABLE template_responses ALTER COLUMN case_id SET NOT NULL")
                        print("✅ Made case_id NOT NULL")
                    except Exception as e:
                        print(f"⚠️  Could not make case_id NOT NULL: {e}")
                
                # Verify final structure
                cur.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'template_responses'
                    ORDER BY ordinal_position
                """)
                
                final_columns = cur.fetchall()
                print(f"\nFinal template_responses table structure:")
                for col in final_columns:
                    print(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
                
                conn.commit()
                
    except Exception as e:
        print(f"Error fixing template_responses table: {e}")
        raise

if __name__ == "__main__":
    fix_template_responses_table()
