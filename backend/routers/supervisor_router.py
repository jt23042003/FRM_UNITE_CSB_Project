#!/usr/bin/env python3
"""
Supervisor Router - NEW endpoints for supervisor template review
This is completely separate from existing functionality to avoid breaking anything
"""

import psycopg2
from typing import Annotated, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Body, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from keycloak.keycloak_openid import KeycloakOpenID
from config import DB_CONNECTION_PARAMS
import traceback

router = APIRouter()

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
            raise HTTPException(status_code=401, detail="Could not validate credentials: Username missing in token.")
        
        return username
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: Invalid token ({e}).")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

@router.get("/api/user/department")
async def get_user_department(
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Get the current user's department information
    """
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Get user type and department
                cur.execute("SELECT user_type, dept FROM user_table WHERE user_name = %s", (current_username,))
                user_row = cur.fetchone()
                
                if not user_row:
                    raise HTTPException(status_code=404, detail="User not found")
                
                user_type = user_row[0]
                user_department = user_row[1]
                
                return {
                    "success": True,
                    "username": current_username,
                    "user_type": user_type,
                    "department": user_department
                }
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get user department: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve user department")

@router.get("/api/supervisor/template-responses/{case_id}")
async def get_supervisor_template_responses(
    case_id: int,
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    NEW endpoint for supervisors to get template responses for their department
    This is completely separate from existing functionality
    """
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Get user type and department
                cur.execute("SELECT user_type, dept FROM user_table WHERE user_name = %s", (current_username,))
                user_row = cur.fetchone()
                
                if not user_row:
                    raise HTTPException(status_code=404, detail="User not found")
                
                user_type = user_row[0]
                user_department = user_row[1]
                
                # Only supervisors can access this endpoint
                if user_type != 'supervisor':
                    raise HTTPException(status_code=403, detail="Only supervisors can access this endpoint")
                
                # If supervisor has no department, show all pending responses
                if not user_department:
                    query = """
                        SELECT tr.id, tr.template_id, tr.assigned_to, tr.responses, tr.status, 
                               tr.department, tr.approved_by, tr.approved_at, tr.rejection_reason,
                               tr.created_at, tr.updated_at,
                               t.name as template_name, t.description as template_description
                        FROM template_responses tr
                        JOIN templates t ON tr.template_id = t.id
                        WHERE tr.case_id = %s AND tr.status = 'pending_approval'
                        ORDER BY tr.created_at DESC
                    """
                    params = (case_id,)
                else:
                    # Show all responses from supervisor's department
                    query = """
                        SELECT tr.id, tr.template_id, tr.assigned_to, tr.responses, tr.status, 
                               tr.department, tr.approved_by, tr.approved_at, tr.rejection_reason,
                               tr.created_at, tr.updated_at,
                               t.name as template_name, t.description as template_description
                        FROM template_responses tr
                        JOIN templates t ON tr.template_id = t.id
                        WHERE tr.case_id = %s AND tr.department = %s
                        ORDER BY tr.created_at DESC
                    """
                    params = (case_id, user_department)
                
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
                    "responses": responses,
                    "supervisor_department": user_department
                }
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in supervisor template responses: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve template responses")

@router.put("/api/supervisor/template-responses/{response_id}/approve")
async def supervisor_approve_template_response(
    response_id: int,
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    NEW endpoint for supervisors to approve template responses
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
                
                # Update template response status
                if supervisor_dept:
                    # Only approve responses from supervisor's department
                    cur.execute("""
                        UPDATE template_responses 
                        SET status = 'approved', approved_by = %s, approved_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND status = 'pending_approval' AND department = %s
                        RETURNING id
                    """, (current_username, response_id, supervisor_dept))
                else:
                    # If no department, approve any pending response
                    cur.execute("""
                        UPDATE template_responses 
                        SET status = 'approved', approved_by = %s, approved_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND status = 'pending_approval'
                        RETURNING id
                    """, (current_username, response_id))
                
                updated_row = cur.fetchone()
                if not updated_row:
                    raise HTTPException(status_code=404, detail="Template response not found or cannot be approved")
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": "Template response approved successfully",
                    "response_id": response_id,
                    "approved_by": current_username
                }
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in supervisor approve: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to approve template response")

@router.put("/api/supervisor/template-responses/{response_id}/reject")
async def supervisor_reject_template_response(
    response_id: int,
    rejection_data: Annotated[Dict[str, Any], Body()],
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    NEW endpoint for supervisors to reject template responses
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
                
                # Update template response status
                if supervisor_dept:
                    # Only reject responses from supervisor's department
                    cur.execute("""
                        UPDATE template_responses 
                        SET status = 'rejected', approved_by = %s, approved_at = CURRENT_TIMESTAMP, rejection_reason = %s
                        WHERE id = %s AND status = 'pending_approval' AND department = %s
                        RETURNING id
                    """, (current_username, rejection_reason, response_id, supervisor_dept))
                else:
                    # If no department, reject any pending response
                    cur.execute("""
                        UPDATE template_responses 
                        SET status = 'rejected', approved_by = %s, approved_at = CURRENT_TIMESTAMP, rejection_reason = %s
                        WHERE id = %s AND status = 'pending_approval'
                        RETURNING id
                    """, (current_username, rejection_reason, response_id))
                
                updated_row = cur.fetchone()
                if not updated_row:
                    raise HTTPException(status_code=404, detail="Template response not found or cannot be rejected")
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": "Template response rejected successfully",
                    "response_id": response_id,
                    "rejected_by": current_username,
                    "rejection_reason": rejection_reason
                }
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in supervisor reject: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to reject template response")
