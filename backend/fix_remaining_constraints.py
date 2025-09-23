#!/usr/bin/env python3
"""
Script to fix the remaining foreign key constraint issue.
"""

import psycopg2
from config import DB_CONNECTION_PARAMS

def fix_remaining_constraints():
    """Fix the remaining foreign key constraint issue"""
    
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Check what foreign key constraints still exist
                cur.execute("""
                    SELECT tc.constraint_name, tc.table_name, kcu.column_name, 
                           ccu.table_name AS foreign_table_name,
                           ccu.column_name AS foreign_column_name 
                    FROM information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                      AND tc.table_name = 'assignment'
                      AND kcu.column_name = 'template_id'
                """)
                
                fks = cur.fetchall()
                print(f"Found template_id foreign key constraints: {fks}")
                
                # Drop any remaining template_id foreign key constraints
                for fk in fks:
                    constraint_name = fk[0]
                    print(f"Dropping constraint: {constraint_name}")
                    cur.execute(f"ALTER TABLE assignment DROP CONSTRAINT IF EXISTS {constraint_name}")
                    print(f"Dropped constraint: {constraint_name}")
                
                # Verify the constraint is gone
                cur.execute("""
                    SELECT tc.constraint_name, tc.table_name, kcu.column_name
                    FROM information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                      AND tc.table_name = 'assignment'
                      AND kcu.column_name = 'template_id'
                """)
                
                remaining_fks = cur.fetchall()
                if not remaining_fks:
                    print("✅ All template_id foreign key constraints removed successfully!")
                else:
                    print(f"⚠️  Still found constraints: {remaining_fks}")
                
                conn.commit()
                
    except Exception as e:
        print(f"Error fixing remaining constraints: {e}")
        raise

if __name__ == "__main__":
    fix_remaining_constraints()
