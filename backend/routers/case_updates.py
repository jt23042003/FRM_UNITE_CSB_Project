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

from db.matcher import CaseEntryMatcher, CaseNotFoundError # CaseEntryMatcher is where update_case_main_data resides
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
        decoded_token = keycloak_openid_instance.decode_token() # Removed 'token' as it's already in the signature
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

UPLOAD_DIR = "/home/ubuntu/fraud_uploads"  # Use your actual upload directory

@router.get("/api/case-document/download/{filename}")
async def download_case_document(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)