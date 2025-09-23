# routers/case_updates.py
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any, Annotated
import traceback
import os
from fastapi import APIRouter, HTTPException, Query, Depends, Request, Body,Path # Body is likely needed for update_data
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from keycloak.keycloak_openid import KeycloakOpenID
from concurrent.futures import ThreadPoolExecutor
from fastapi.responses import FileResponse

from db.matcher import CaseEntryMatcher, CaseNotFoundError, log_case_action # CaseEntryMatcher is where update_case_main_data resides
from models.base_models import CaseMainUpdateData, CaseActionLogResponse # Ensure this Pydantic model is imported

router = APIRouter()

# --- Shared Dependencies (Reusing authentication & executor setup) ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_keycloak_openid_dependency(request: Request) -> KeycloakOpenID:
    return request.app.state.keycloak_openid

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
        print(f"ERROR: JWT Decoding/Validation failed: {e}", flush=True)
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: Invalid token ({e}).")
    except Exception as e:
        print(f"UNEXPECTED ERROR in get_current_username (case_updates): {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)

# --- API Endpoint for Updating CaseMain Data ---
@router.post("/api/case-main/{case_id}/update")
async def update_case_main_api(
    # FIX: Move all Depends parameters to the beginning
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)], # Requires authentication
    case_id: int = Path(..., description="The unique integer ID of the case to update."), # Path parameter after Depends
    update_data: CaseMainUpdateData = Body(..., description="Data to update in the case_main table.") # Body parameter after Depends
) -> Dict[str, Any]:
    """
    Updates specific fields of a case in the case_main table.
    Expects JSON body conforming to CaseMainUpdateData model.
    """
    try:
        updated_case = await matcher.update_case_main_data(case_id, update_data.dict(exclude_unset=True))
        if not updated_case:
            raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found or no update occurred.")
        return {"success": True, "message": "Case updated successfully.", "updated_case": updated_case}
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found: {e}.")
    except Exception as e:
        print(f"Error updating case {case_id}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update case. Error: {e}")

# NEW API ENDPOINT: GET /api/case/{case_id}/action-log
@router.get("/api/case/{case_id}/action-log", response_model=CaseActionLogResponse, tags=["Case Details"])
async def get_case_action_log(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)], # Keep Depends parameter first
    case_id: int = Path(..., description="The unique integer ID of the case.")
) -> CaseActionLogResponse:
    """
    Retrieves the latest operational confirmation log for a specific case.
    """
    try:
        log_data = await matcher.fetch_operational_confirmation_log(case_id)

        if log_data is None:
            raise HTTPException(status_code=404, detail=f"No action log found for case_id {case_id}")

        return CaseActionLogResponse(success=True, data=log_data)

    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# NEW API ENDPOINT: POST /api/case/{case_id}/reopen
@router.post("/api/case/{case_id}/reopen")
async def reopen_case_api(
    request_data: Dict[str, Any],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)],
    case_id: int = Path(..., description="The unique integer ID of the case to reopen.")
) -> Dict[str, Any]:
    """
    Reopens a closed case and optionally assigns it to a risk officer. 
    Only super_user can perform this action.
    """
    try:
        # Check if user is super_user
        user_type = await matcher.fetch_user_type(logged_in_username)
        if user_type != 'super_user':
            raise HTTPException(
                status_code=403, 
                detail="Only super_user can reopen closed cases."
            )
        
        # Check if case exists and is closed
        case_data = await matcher.fetch_single_case_details_from_case_main_by_case_id(case_id)
        if not case_data:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found.")
        
        if case_data.get('status') != 'Closed':
            raise HTTPException(
                status_code=400, 
                detail=f"Case is not closed. Current status: {case_data.get('status')}"
            )
        
        # Get assigned risk officer from request (optional)
        assigned_risk_officer = request_data.get('assigned_risk_officer')
        
        # Get reopen comment from request (required)
        reopen_comment = request_data.get('reopen_comment')
        if not reopen_comment or not reopen_comment.strip():
            raise HTTPException(
                status_code=400,
                detail="Reopen comment is required."
            )
        
        # Update case status to "Open" (not "Reopened" to keep assignment functionality)
        update_data = {
            "status": "Open",
            "closing_date": None  # Clear closing date
        }
        
        # Update case_main table
        await matcher.update_case_main_data(case_id, update_data)
        
        # If a risk officer is specified, assign the case to them
        assignment_message = ""
        if assigned_risk_officer:
            # Verify the assigned user is a risk officer
            assigned_user_type = await matcher.fetch_user_type(assigned_risk_officer)
            if assigned_user_type != 'risk_officer':
                raise HTTPException(
                    status_code=400,
                    detail=f"User {assigned_risk_officer} is not a risk officer."
                )
            
            # Create assignment
            import psycopg2
            from config import DB_CONNECTION_PARAMS
            
            with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
                with conn.cursor() as cur:
                    # Deactivate any existing assignments
                    cur.execute("""
                        UPDATE assignment 
                        SET is_active = FALSE 
                        WHERE case_id = %s AND is_active = TRUE
                    """, (case_id,))
                    
                    # Create new assignment as 'auto' type so it appears in risk officer's main case list
                    cur.execute("""
                        INSERT INTO assignment (case_id, assigned_to, assigned_by, comment, is_active, assignment_type)
                        VALUES (%s, %s, %s, %s, TRUE, 'auto')
                    """, (case_id, assigned_risk_officer, logged_in_username, f"Assigned during case reopen by {logged_in_username}"))
                    
                    conn.commit()
            
            assignment_message = f" and assigned to {assigned_risk_officer}"
        
        # Log the reopen action with the actual comment
        log_details = f"Case reopened by super_user {logged_in_username}{assignment_message}. Reason: {reopen_comment.strip()}"
        log_case_action(
            case_id=case_id,
            user_name=logged_in_username,
            action="reopen_case",
            details=log_details
        )
        
        return {
            "success": True,
            "message": f"Case {case_id} has been reopened successfully{assignment_message}.",
            "case_id": case_id,
            "new_status": "Open",
            "assigned_to": assigned_risk_officer if assigned_risk_officer else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to reopen case {case_id}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to reopen case. Error: {e}")

# NEW API ENDPOINT: GET /api/risk-officers
@router.get("/api/risk-officers")
async def get_risk_officers(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Get list of all risk officers for assignment dropdown.
    Only super_user can access this endpoint.
    """
    try:
        # Check if user is super_user
        user_type = await matcher.fetch_user_type(logged_in_username)
        if user_type != 'super_user':
            raise HTTPException(
                status_code=403, 
                detail="Only super_user can access risk officers list."
            )
        
        # Get risk officers from database
        import psycopg2
        from config import DB_CONNECTION_PARAMS
        
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_name, dept 
                    FROM user_table 
                    WHERE user_type = 'risk_officer' 
                    ORDER BY user_name
                """)
                risk_officers = [
                    {"username": row[0], "department": row[1]} 
                    for row in cur.fetchall()
                ]
        
        return {
            "success": True,
            "risk_officers": risk_officers
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to get risk officers: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get risk officers. Error: {e}")

UPLOAD_DIR = "/home/ubuntu/fraud_uploads"  # Use your actual upload directory

@router.get("/api/case-document/download/{filename}")
async def download_case_document(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)
