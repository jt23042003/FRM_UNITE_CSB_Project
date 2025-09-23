#!/usr/bin/env python3
"""
Script to fix the templates table structure and ensure it has the correct columns.
"""

import psycopg2
from config import DB_CONNECTION_PARAMS
import json

def fix_templates_table():
    """Fix the templates table structure"""
    
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # First, let's see what tables exist
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'templates'
                """)
                
                if cur.fetchone():
                    print("Templates table exists, checking structure...")
                    
                    # Check what columns exist
                    cur.execute("""
                        SELECT column_name, data_type FROM information_schema.columns 
                        WHERE table_name = 'templates'
                    """)
                    
                    existing_columns = {row[0]: row[1] for row in cur.fetchall()}
                    print(f"Existing columns: {existing_columns}")
                    
                    # Add missing columns if they don't exist
                    if 'questions' not in existing_columns:
                        print("Adding questions column...")
                        cur.execute("ALTER TABLE templates ADD COLUMN questions JSONB")
                    
                    if 'is_active' not in existing_columns:
                        print("Adding is_active column...")
                        cur.execute("ALTER TABLE templates ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
                    
                    if 'created_at' not in existing_columns:
                        print("Adding created_at column...")
                        cur.execute("ALTER TABLE templates ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    
                    if 'updated_at' not in existing_columns:
                        print("Adding updated_at column...")
                        cur.execute("ALTER TABLE templates ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    
                    # Check if there are any existing records
                    cur.execute("SELECT COUNT(*) FROM templates")
                    count = cur.fetchone()[0]
                    print(f"Found {count} existing template records")
                    
                    if count > 0:
                        # Check if existing records have the questions column populated
                        cur.execute("SELECT id, name FROM templates WHERE questions IS NULL LIMIT 1")
                        null_questions = cur.fetchone()
                        
                        if null_questions:
                            print(f"Found template {null_questions[0]} with null questions, updating...")
                            
                            # Update existing templates with sample questions
                            sample_questions = [
                                {
                                    "id": "sample_question",
                                    "type": "radio",
                                    "question": "Sample question for existing template?",
                                    "required": True,
                                    "options": ["Yes", "No"],
                                    "help_text": "This is a placeholder question for existing templates"
                                }
                            ]
                            
                            cur.execute("""
                                UPDATE templates 
                                SET questions = %s, is_active = TRUE
                                WHERE questions IS NULL
                            """, (json.dumps(sample_questions),))
                            
                            print("Updated existing templates with sample questions")
                    
                else:
                    print("Templates table doesn't exist, creating it...")
                    cur.execute("""
                        CREATE TABLE templates (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            questions JSONB NOT NULL,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    print("Created templates table")
                
                conn.commit()
                print("✅ Templates table structure fixed successfully!")
                
                # Now let's verify the structure
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'templates'
                    ORDER BY ordinal_position
                """)
                
                columns = cur.fetchall()
                print("\nFinal table structure:")
                for col in columns:
                    print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
                
    except Exception as e:
        print(f"Error fixing templates table: {e}")
        raise

if __name__ == "__main__":
    fix_templates_table()
