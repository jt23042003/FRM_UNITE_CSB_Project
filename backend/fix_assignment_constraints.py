#!/usr/bin/env python3
"""
Script to fix foreign key constraints in the assignment table.
"""

import psycopg2
from config import DB_CONNECTION_PARAMS

def fix_assignment_constraints():
    """Fix foreign key constraints in assignment table"""
    
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Check what foreign key constraints exist
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
                """)
                
                fks = cur.fetchall()
                print(f"Found foreign key constraints in assignment table: {fks}")
                
                # Check if template_id column exists and has constraints
                if any('template_id' in fk[2] for fk in fks):
                    print("Found template_id foreign key constraint, dropping it...")
                    
                    # Find the constraint name
                    template_fk = next((fk for fk in fks if 'template_id' in fk[2]), None)
                    if template_fk:
                        constraint_name = template_fk[0]
                        print(f"Dropping constraint: {constraint_name}")
                        
                        # Drop the foreign key constraint
                        cur.execute(f"ALTER TABLE assignment DROP CONSTRAINT {constraint_name}")
                        print("Dropped template_id foreign key constraint")
                
                # Check if there are any assignments with template_id references
                cur.execute("SELECT COUNT(*) FROM assignment WHERE template_id IS NOT NULL")
                template_assignments = cur.fetchone()[0]
                print(f"Found {template_assignments} assignments with template_id references")
                
                if template_assignments > 0:
                    # Clear template_id references
                    cur.execute("UPDATE assignment SET template_id = NULL WHERE template_id IS NOT NULL")
                    print("Cleared template_id references from assignments")
                
                # Now we can safely update templates
                print("✅ Assignment table constraints fixed successfully!")
                
                conn.commit()
                
    except Exception as e:
        print(f"Error fixing assignment constraints: {e}")
        raise

if __name__ == "__main__":
    fix_assignment_constraints()
