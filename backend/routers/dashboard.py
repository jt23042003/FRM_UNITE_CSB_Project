# routers/dashboard.py
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any, Annotated
from fastapi import APIRouter, HTTPException, Query, Depends, Request
import traceback

from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from keycloak import KeycloakOpenID

from db.matcher import CaseEntryMatcher # Make sure this is imported

router = APIRouter()

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
            print("ERROR: Token decoded but username (preferred_username/sub) not found in claims.", flush=True)
            raise HTTPException(status_code=401, detail="Could not validate credentials: Username missing in token.")
        
        return username
    except JWTError as e:
        print(f"ERROR: JWT Decoding/Validation failed: {e}", flush=True)
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: Invalid token ({e}).")
    except Exception as e:
        print(f"UNEXPECTED ERROR in get_current_username: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

def get_case_matcher_instance(request: Request) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=request.app.state.executor)

@router.get("/api/case-list")
async def get_case_list(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)],
    skip: int = Query(0),
    limit: int = Query(25)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetches a paginated list of cases for the dashboard display, filtered by logged-in user's role and assignment.
    """
    # The user_type is fetched internally by fetch_dashboard_cases,
    # so we don't need to pass it as a separate parameter here.
    user_type = None # This line and its calculation can be kept for local debugging if needed, but won't be passed.
    if logged_in_username:
        user_type = await matcher.fetch_user_type(logged_in_username)
        if user_type is None:
            print(f"WARNING: User '{logged_in_username}' not found in user_table. No role-based filtering applied.", flush=True)

    try:
        cases_data = await matcher.fetch_dashboard_cases(
            skip=skip,
            limit=limit,
            search_ack_no=None, # This is a placeholder for actual search/status filters from frontend
            status_filter=None, # Pass search/status filters if frontend sends them
            current_logged_in_username=logged_in_username # This is the only user-related parameter needed here
            # REMOVED: current_logged_in_user_type=user_type - This parameter is not expected by fetch_dashboard_cases
        )

        if not cases_data:
            print("INFO: No cases found in the database for the dashboard.")
            return {"cases": []}
        
        return {"cases": cases_data}

    except HTTPException:
        raise
    except Exception as e:
        print(f"UNEXPECTED ERROR in /api/case-list: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve case list due to an internal server error.")


#@router.get("/api/all-cases")
#async def list_cases(
#    status: Annotated[Optional[str], Query()] = None,
#    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
#) -> Dict[str, List[Dict[str, Any]]]:
#    """
#    Fetches all cases, optionally filtered by status.
#    """
#    try:
#        cases = await matcher.fetch_all_cases_filtered(status=status)
#        return {"cases": cases}
#    except psycopg2.Error as db_error:
#        print(f"DATABASE ERROR in /api/all-cases: {db_error}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Database error while retrieving all cases.")
#    except Exception as e:
#        print(f"UNEXPECTED ERROR in /api/all-cases: {e}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Failed to retrieve all cases due to an internal server error.")


#@router.get("/api/dashboard-cases")
#async def get_dashboard_cases(
#    user_id: Annotated[str, Query(...)],
#    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
#) -> Dict[str, List[Dict[str, Any]]]:
#    """
#    Fetches dashboard-specific cases for a user.
#    """
#    try:
#        cases = await matcher.fetch_user_dashboard_cases(user_id=user_id)
#        return {"cases": cases}
#    except psycopg2.Error as db_error:
#        print(f"DATABASE ERROR in /api/dashboard-cases: {db_error}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Database error while retrieving dashboard cases.")
#    except Exception as e:
#        print(f"UNEXPECTED ERROR in /api/dashboard-cases: {e}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard cases due to an internal server error.")


#@router.get("/api/dropdown/status-list")
#async def get_status_list(
#    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
#) -> Dict[str, List[str]]:
#    """
#    Fetches a list of distinct statuses for dropdowns.
#    """
#    try:
#        statuses = await matcher.fetch_distinct_statuses()
#        return {"statuses": statuses}
#    except psycopg2.Error as db_error:
#        print(f"DATABASE ERROR in /api/dropdown/status-list: {db_error}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Database error while retrieving status list.")
#    except Exception as e:
#        print(f"UNEXPECTED ERROR in /api/dropdown/status-list: {e}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Failed to retrieve status list due to an internal server error.")


#@router.get("/api/dropdown/assigned-to-list")
#async def get_assigned_users(
#    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
#) -> Dict[str, List[str]]:
#    """
#    Fetches a list of distinct assigned users for dropdowns.
#    """
#    try:
#        users = await matcher.fetch_distinct_assigned_users()
#        return {"users": users}
#    except psycopg2.Error as db_error:
#        print(f"DATABASE ERROR in /api/dropdown/assigned-to-list: {db_error}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Database error while retrieving assigned users list.")
#    except Exception as e:
#        print(f"UNEXPECTED ERROR in /api/dropdown/assigned-to-list: {e}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Failed to retrieve assigned users list due to an internal server error.")

