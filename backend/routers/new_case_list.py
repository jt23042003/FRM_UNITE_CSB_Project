# routers/new_case_list.py
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any, Annotated
import traceback

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
#from keycloak import KeycloakOpenID
from keycloak.keycloak_openid import KeycloakOpenID

from concurrent.futures import ThreadPoolExecutor

from db.matcher import CaseEntryMatcher # CaseEntryMatcher is where fetch_new_cases_list resides

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
        print(f"UNEXPECTED ERROR in get_current_username (new_case_list): {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)

# --- API Endpoint for New Case List ---
@router.get("/api/new-case-list")
async def get_new_case_list(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)],
    skip: int = Query(0),
    limit: int = Query(25),
    search_source_ack_no: Optional[str] = Query(None, description="Search by Source Acknowledgement Number"),
    status_filter: Optional[str] = Query(None, description="Filter by case status (e.g., 'New', 'Assigned', 'Closed')")
) -> Dict[str, Any]: # FIX: Changed return type to Dict[str, Any] as it's no longer just a List
    """
    Fetches a paginated list of cases from the new case management system,
    filtered by logged-in user's role and assignment.
    """
    user_type = None
    if logged_in_username:
        user_type = await matcher.fetch_user_type(logged_in_username)
        if user_type is None:
            print(f"WARNING: User '{logged_in_username}' not found in user_table. No role-based filtering applied.", flush=True)

    try:
        cases_data = await matcher.fetch_new_cases_list(
            skip=skip,
            limit=limit,
            search_source_ack_no=search_source_ack_no,
            status_filter=status_filter,
            current_logged_in_username=logged_in_username # This is the only user-related parameter needed here
        )

        if not cases_data:
            print("INFO: No cases found in the new case management system for the dashboard.")
            # FIX: Return user_type even if no cases
            return {"cases": [], "logged_in_user_type": user_type} 
        
        # FIX: Include user_type in the response
        return {"cases": cases_data, "logged_in_user_type": user_type}

    except HTTPException:
        raise
    except Exception as e:
        print(f"UNEXPECTED ERROR in /api/new-case-list: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve new case list due to an internal server error.")
