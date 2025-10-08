"""
Template Router

API endpoints for managing templates and template responses.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from typing import Annotated, Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from keycloak.keycloak_openid import KeycloakOpenID
from fastapi.security import OAuth2PasswordBearer
import traceback
from jose import JWTError
import psycopg2
from config import DB_CONNECTION_PARAMS
import json

router = APIRouter()

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

def get_keycloak_openid_dependency(request: Request) -> KeycloakOpenID:
    return request.app.state.keycloak_openid

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_username(
    token: Annotated[str, Depends(oauth2_scheme)],
    keycloak_openid_instance: Annotated[KeycloakOpenID, Depends(get_keycloak_openid_dependency)]
) -> str:
    try:
        decoded_token = keycloak_openid_instance.decode_token(token)
        username: str = decoded_token.get("preferred_username") or decoded_token.get("sub")
        
        if username is None:
            print("ERROR: Token decoded but username (preferred_username/sub) not found in claims.", flush=True)
            raise HTTPException(status_code=401, detail="Could not validate credentials: Username missing in token.")
        
        return username
    except JWTError as e:
        print(f"ERROR: JWT Decoding/Validation failed: {e}", flush=True)
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: Invalid token ({e}).")
    except Exception as e:
        print(f"UNEXPECTED ERROR in get_current_username (template): {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

@router.get("/api/templates")
async def get_all_templates(
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Get all active templates
    """
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Ensure templates table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS templates (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        questions JSONB NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cur.execute("SELECT id, name, description, questions FROM templates WHERE is_active = TRUE")
                rows = cur.fetchall()
                
                templates = []
                for row in rows:
                    templates.append({
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "questions": row[3]
                    })
                
                return {
                    "success": True,
                    "templates": templates
                }
    except Exception as e:
        print(f"ERROR: Failed to get templates: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve templates")

@router.get("/api/templates/{template_id}")
async def get_template_by_id(
    template_id: int,
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Get a specific template by ID
    """
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, description, questions FROM templates WHERE id = %s AND is_active = TRUE", (template_id,))
                row = cur.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Template not found")
                
                return {
                    "success": True,
                    "template": {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "questions": row[3]
                    }
                }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to get template {template_id}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve template")

@router.post("/api/templates")
async def create_template(
    template_data: Annotated[Dict[str, Any], Body(...)],
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Create a new template
    """
    try:
        name = template_data.get("name")
        description = template_data.get("description")
        questions = template_data.get("questions")
        
        if not name or not questions:
            raise HTTPException(status_code=400, detail="Name and questions are required")
        
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Ensure templates table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS templates (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        questions JSONB NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cur.execute("""
                    INSERT INTO templates (name, description, questions)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (name, description, questions))
                
                template_id = cur.fetchone()[0]
                conn.commit()
                
                return {
                    "success": True,
                    "message": "Template created successfully",
                    "template_id": template_id
                }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to create template: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to create template")

@router.post("/api/template-responses")
async def create_template_response(
    response_data: Annotated[Dict[str, Any], Body(...)],
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Create a template response for a case
    """
    try:
        case_id = response_data.get("case_id")
        template_id = response_data.get("template_id")
        responses = response_data.get("responses")
        department = response_data.get("department")
        
        if not case_id or not template_id or not responses:
            raise HTTPException(status_code=400, detail="Case ID, template ID, and responses are required")
        
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Ensure template_responses table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS template_responses (
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
                
                cur.execute("""
                    INSERT INTO template_responses (case_id, template_id, assigned_to, responses, department)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (case_id, template_id, current_username, json.dumps(responses), department))
                
                response_id = cur.fetchone()[0]
                conn.commit()
                
                return {
                    "success": True,
                    "message": "Template response created successfully",
                    "response_id": response_id
                }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to create template response: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to create template response")

@router.get("/api/case/{case_id}/template-responses")
async def get_case_template_responses(
    case_id: int,
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Get template responses for a specific case based on user role and department
    """
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Get user type and department
                cur.execute("SELECT user_type, dept FROM user_table WHERE user_name = %s", (current_username,))
                user_row = cur.fetchone()
                user_type = user_row[0] if user_row else None
                user_department = user_row[1] if user_row else None
                
                # Debug logging
                print(f"DEBUG: User {current_username} - Type: {user_type}, Department: {user_department}", flush=True)
                
                # Ensure template_responses table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS template_responses (
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
                
                # Build query based on user role
                if user_type == 'supervisor':
                    # Supervisor sees LATEST template response for each template in their department
                    query = """
                        WITH latest_responses AS (
                            SELECT tr.*, t.name as template_name, t.description as template_description,
                                   ROW_NUMBER() OVER (PARTITION BY tr.template_id ORDER BY tr.created_at DESC) as rn
                            FROM template_responses tr
                            JOIN templates t ON tr.template_id = t.id
                            WHERE tr.case_id = %s AND tr.department = %s
                        )
                        SELECT id, template_id, assigned_to, responses, status, 
                               department, approved_by, approved_at, rejection_reason,
                               created_at, updated_at, template_name, template_description
                        FROM latest_responses
                        WHERE rn = 1
                        ORDER BY created_at DESC
                    """
                    params = (case_id, user_department)
                elif user_type in ('risk_officer', 'CRO'):
                    # Risk officers only see latest approved template responses from other departments
                    query = """
                        WITH latest_responses AS (
                            SELECT tr.*, t.name as template_name, t.description as template_description,
                                   ROW_NUMBER() OVER (PARTITION BY tr.template_id ORDER BY tr.created_at DESC) as rn
                            FROM template_responses tr
                            JOIN templates t ON tr.template_id = t.id
                            WHERE tr.case_id = %s AND tr.status = 'approved'
                        )
                        SELECT id, template_id, assigned_to, responses, status, 
                               department, approved_by, approved_at, rejection_reason,
                               created_at, updated_at, template_name, template_description
                        FROM latest_responses
                        WHERE rn = 1
                        ORDER BY created_at DESC
                    """
                    params = (case_id,)
                else:
                    # Others see their latest responses and latest approved responses
                    query = """
                        WITH latest_responses AS (
                            SELECT tr.*, t.name as template_name, t.description as template_description,
                                   ROW_NUMBER() OVER (PARTITION BY tr.template_id ORDER BY tr.created_at DESC) as rn
                            FROM template_responses tr
                            JOIN templates t ON tr.template_id = t.id
                            WHERE tr.case_id = %s AND (
                                tr.assigned_to = %s
                                OR tr.status = 'approved'
                            )
                        )
                        SELECT id, template_id, assigned_to, responses, status, 
                               department, approved_by, approved_at, rejection_reason,
                               created_at, updated_at, template_name, template_description
                        FROM latest_responses
                        WHERE rn = 1
                        ORDER BY created_at DESC
                    """
                    params = (case_id, current_username)
                
                cur.execute(query, params)
                
                rows = cur.fetchall()
                responses = []
                
                for row in rows:
                    responses.append({
                        "id": row[0],
                        "template_id": row[1],
                        "assigned_to": row[2],
                        "responses": row[3],
                        "status": row[4],
                        "department": row[5],
                        "approved_by": row[6],
                        "approved_at": row[7].isoformat() if row[7] else None,
                        "rejection_reason": row[8],
                        "created_at": row[9].isoformat() if row[9] else None,
                        "updated_at": row[10].isoformat() if row[10] else None,
                        "template_name": row[11],
                        "template_description": row[12]
                    })
                
                return {
                    "success": True,
                    "responses": responses
                }
    except Exception as e:
        print(f"ERROR: Failed to get template responses for case {case_id}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve template responses")

@router.put("/api/template-responses/{response_id}/approve")
async def approve_template_response(
    response_id: int,
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Approve a template response (supervisor only)
    """
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Check if user is supervisor
                cur.execute("SELECT user_type, dept FROM user_table WHERE user_name = %s", (current_username,))
                user_row = cur.fetchone()
                if not user_row or user_row[0] != 'supervisor':
                    raise HTTPException(status_code=403, detail="Only supervisors can approve template responses")
                
                supervisor_dept = user_row[1]
                if not supervisor_dept:
                    raise HTTPException(status_code=400, detail="Supervisor department not set")
                
                # Update template response status - only for supervisor's own department
                cur.execute("""
                    UPDATE template_responses 
                    SET status = 'approved', approved_by = %s, approved_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND status = 'pending_approval' AND department = %s
                    RETURNING id
                """, (current_username, response_id, supervisor_dept))
                
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Template response not found or already processed")
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": "Template response approved successfully"
                }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to approve template response {response_id}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to approve template response")

@router.put("/api/template-responses/{response_id}/reject")
async def reject_template_response(
    response_id: int,
    rejection_data: Annotated[Dict[str, Any], Body(...)],
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Reject a template response (supervisor only)
    """
    try:
        rejection_reason = rejection_data.get("rejection_reason", "")
        
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Check if user is supervisor
                cur.execute("SELECT user_type, dept FROM user_table WHERE user_name = %s", (current_username,))
                user_row = cur.fetchone()
                if not user_row or user_row[0] != 'supervisor':
                    raise HTTPException(status_code=403, detail="Only supervisors can reject template responses")
                
                supervisor_dept = user_row[1]
                if not supervisor_dept:
                    raise HTTPException(status_code=400, detail="Supervisor department not set")
                
                # Update template response status - only for supervisor's own department
                cur.execute("""
                    UPDATE template_responses 
                    SET status = 'rejected', approved_by = %s, approved_at = CURRENT_TIMESTAMP, rejection_reason = %s
                    WHERE id = %s AND status = 'pending_approval' AND department = %s
                    RETURNING id
                """, (current_username, rejection_reason, response_id, supervisor_dept))
                
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Template response not found or already processed")
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": "Template response rejected successfully"
                }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to reject template response {response_id}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to reject template response")
