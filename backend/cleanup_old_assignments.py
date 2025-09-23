#!/usr/bin/env python3
"""
Script to clean up old assignment records that reference non-existent template IDs.
"""

import psycopg2
from config import DB_CONNECTION_PARAMS

def cleanup_old_assignments():
    """Clean up old assignment records"""
    
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Check if template_id column exists
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'assignment' AND column_name = 'template_id'
                """)
                
                if not cur.fetchone():
                    print("template_id column doesn't exist in assignment table")
                    return
                
                # Check for assignments with non-existent template IDs
                cur.execute("""
                    SELECT a.id, a.case_id, a.template_id, a.assigned_to
                    FROM assignment a
                    WHERE a.template_id IS NOT NULL 
                      AND a.template_id NOT IN (SELECT id FROM templates)
                """)
                
                invalid_assignments = cur.fetchall()
                print(f"Found {len(invalid_assignments)} assignments with invalid template IDs:")
                
                for assignment in invalid_assignments:
                    print(f"  Assignment ID: {assignment[0]}, Case: {assignment[1]}, Template: {assignment[2]}, Assigned to: {assignment[3]}")
                
                if invalid_assignments:
                    # Clear the invalid template_id references
                    cur.execute("""
                        UPDATE assignment 
                        SET template_id = NULL 
                        WHERE template_id IS NOT NULL 
                          AND template_id NOT IN (SELECT id FROM templates)
                    """)
                    
                    updated_count = cur.rowcount
                    print(f"Cleared template_id from {updated_count} invalid assignments")
                    
                    # Verify cleanup
                    cur.execute("""
                        SELECT COUNT(*) FROM assignment 
                        WHERE template_id IS NOT NULL 
                          AND template_id NOT IN (SELECT id FROM templates)
                    """)
                    
                    remaining_invalid = cur.fetchone()[0]
                    if remaining_invalid == 0:
                        print("✅ All invalid template_id references cleaned up!")
                    else:
                        print(f"⚠️  Still found {remaining_invalid} invalid references")
                else:
                    print("✅ No invalid template_id references found")
                
                conn.commit()
                
    except Exception as e:
        print(f"Error cleaning up old assignments: {e}")
        raise

if __name__ == "__main__":
    cleanup_old_assignments()
