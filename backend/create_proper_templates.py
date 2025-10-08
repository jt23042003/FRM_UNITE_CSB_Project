#!/usr/bin/env python3
"""
Script to create proper templates with the correct question structure.
"""

import psycopg2
from config import DB_CONNECTION_PARAMS
import json

def create_proper_templates():
    """Create proper templates with correct question structure"""
    
    # Proper templates with different question types
    proper_templates = [
        {
            "name": "Customer Visit Verification",
            "description": "Template for verifying customer visit details and financial platform support",
            "questions": [
                {
                    "id": "visit_verification",
                    "type": "radio",
                    "question": "Did you visit the customer's house?",
                    "required": True,
                    "options": ["Yes", "No"],
                    "help_text": "Please confirm if you physically visited the customer's residence"
                },
                {
                    "id": "visit_date",
                    "type": "date",
                    "question": "When did you visit?",
                    "required": True,
                    "help_text": "Select the date of your visit"
                },
                {
                    "id": "customer_present",
                    "type": "radio",
                    "question": "Was the customer present during the visit?",
                    "required": True,
                    "options": ["Yes", "No", "Partially"],
                    "help_text": "Indicate if the customer was available during your visit"
                },
                {
                    "id": "financial_platform",
                    "type": "radio",
                    "question": "Does the customer support this financial platform?",
                    "required": True,
                    "options": ["Yes", "No", "Unsure"],
                    "help_text": "Customer's stance on the financial platform"
                },
                {
                    "id": "platform_details",
                    "type": "textarea",
                    "question": "Please provide details about the financial platform discussion",
                    "required": False,
                    "help_text": "Describe what was discussed regarding the financial platform",
                    "max_length": 500
                },
                {
                    "id": "customer_concerns",
                    "type": "textarea",
                    "question": "What concerns did the customer express?",
                    "required": False,
                    "help_text": "List any concerns or objections raised by the customer",
                    "max_length": 300
                },
                {
                    "id": "next_steps",
                    "type": "textarea",
                    "question": "What are the next steps?",
                    "required": True,
                    "help_text": "Outline the planned next actions",
                    "max_length": 200
                },
                {
                    "id": "supporting_documents",
                    "type": "file_upload",
                    "question": "Upload any supporting documents",
                    "required": False,
                    "help_text": "Upload photos, receipts, or other relevant documents",
                    "allowed_types": ["image/*", "application/pdf"],
                    "max_size_mb": 10
                }
            ]
        },
        {
            "name": "Financial Assessment",
            "description": "Template for assessing customer's financial situation and needs",
            "questions": [
                {
                    "id": "income_verification",
                    "type": "radio",
                    "question": "Have you verified the customer's income?",
                    "required": True,
                    "options": ["Yes", "No"],
                    "help_text": "Confirm if income verification was completed"
                },
                {
                    "id": "income_amount",
                    "type": "number",
                    "question": "What is the customer's monthly income?",
                    "required": False,
                    "help_text": "Enter the monthly income amount in INR",
                    "min_value": 0,
                    "max_value": 1000000
                },
                {
                    "id": "bank_accounts",
                    "type": "radio",
                    "question": "Does the customer have multiple bank accounts?",
                    "required": True,
                    "options": ["Yes", "No"],
                    "help_text": "Check if customer has accounts with multiple banks"
                },
                {
                    "id": "account_details",
                    "type": "textarea",
                    "question": "Provide details about the bank accounts",
                    "required": False,
                    "help_text": "List the banks and account types",
                    "max_length": 400
                },
                {
                    "id": "risk_assessment",
                    "type": "radio",
                    "question": "What is the risk level for this customer?",
                    "required": True,
                    "options": ["Low", "Medium", "High"],
                    "help_text": "Assess the overall risk level based on your findings"
                },
                {
                    "id": "risk_reasons",
                    "type": "textarea",
                    "question": "Explain the risk assessment",
                    "required": True,
                    "help_text": "Provide reasoning for the risk level assigned",
                    "max_length": 300
                }
            ]
        },
        {
            "name": "Document Verification",
            "description": "Template for verifying customer documents and identity",
            "questions": [
                {
                    "id": "pan_verified",
                    "type": "radio",
                    "question": "Is the PAN card verified?",
                    "required": True,
                    "options": ["Yes", "No", "Pending"],
                    "help_text": "Confirm PAN card verification status"
                },
                {
                    "id": "aadhaar_verified",
                    "type": "radio",
                    "question": "Is the Aadhaar card verified?",
                    "required": True,
                    "options": ["Yes", "No", "Pending"],
                    "help_text": "Confirm Aadhaar card verification status"
                },
                {
                    "id": "address_verified",
                    "type": "radio",
                    "question": "Is the address verified?",
                    "required": True,
                    "options": ["Yes", "No", "Pending"],
                    "help_text": "Confirm address verification status"
                },
                {
                    "id": "verification_method",
                    "type": "radio",
                    "question": "How was the verification done?",
                    "required": True,
                    "options": ["Physical verification", "Video call", "Document review", "Other"],
                    "help_text": "Select the verification method used"
                },
                {
                    "id": "verification_notes",
                    "type": "textarea",
                    "question": "Additional verification notes",
                    "required": False,
                    "help_text": "Any additional notes about the verification process",
                    "max_length": 400
                },
                {
                    "id": "verification_documents",
                    "type": "file_upload",
                    "question": "Upload verification documents",
                    "required": False,
                    "help_text": "Upload photos or scans of verified documents",
                    "allowed_types": ["image/*", "application/pdf"],
                    "max_size_mb": 15
                }
            ]
        }
    ]
    
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Clear existing templates
                cur.execute("DELETE FROM templates")
                print("Cleared existing templates")
                
                # Insert proper templates
                for template in proper_templates:
                    cur.execute("""
                        INSERT INTO templates (name, description, questions, is_active)
                        VALUES (%s, %s, %s, TRUE)
                        RETURNING id
                    """, (template["name"], template["description"], json.dumps(template["questions"])))
                    
                    template_id = cur.fetchone()[0]
                    print(f"Created template: {template['name']} (ID: {template_id})")
                    
                    # Print first question as verification
                    first_question = template["questions"][0]
                    print(f"  Sample question: {first_question['question']} (Type: {first_question['type']})")
                
                conn.commit()
                print(f"\n✅ Successfully created {len(proper_templates)} proper templates!")
                
                # Verify the templates were created correctly
                cur.execute("SELECT id, name, questions FROM templates ORDER BY id")
                templates = cur.fetchall()
                
                print(f"\nVerification - Found {len(templates)} templates:")
                for t in templates:
                    questions = t[2]
                    if questions and isinstance(questions, list):
                        print(f"  ID {t[0]}: {t[1]} - {len(questions)} questions")
                    else:
                        print(f"  ID {t[0]}: {t[1]} - INVALID QUESTIONS FORMAT")
                
    except Exception as e:
        print(f"Error creating proper templates: {e}")
        raise

if __name__ == "__main__":
    create_proper_templates()
