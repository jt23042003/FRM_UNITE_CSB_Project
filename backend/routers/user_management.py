# routers/user_management.py
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional, Union, Dict, Any, Annotated
import asyncio
import traceback

from fastapi import APIRouter, HTTPException, Depends, Request, Query # Re-added Query as it's used
from concurrent.futures import ThreadPoolExecutor

from db.matcher import CaseEntryMatcher, CaseNotFoundError
from models.base_models import UserResponse,DepartmentNameResponse, DepartmentResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from keycloak.keycloak_openid import KeycloakOpenID

router = APIRouter()

# --- Shared Dependencies ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_keycloak_openid_dependency(request: Request) -> KeycloakOpenID:
    return request.app.state.keycloak_openid

async def get_current_username(
    token: Annotated[str, Depends(oauth2_scheme)],
    keycloak_openid_instance: Annotated[KeycloakOpenID, Depends(get_keycloak_openid_dependency)]
) -> str:
    """Authenticates user via JWT and returns username."""
    try:
        decoded_token = keycloak_openid_instance.decode_token(token)
        username: str = decoded_token.get("preferred_username") or decoded_token.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials: Username missing in token.")
        return username
    except JWTError as e:
        print(f"ERROR: JWT Decoding/Validation failed (user_management): {e}", flush=True)
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: Invalid token ({e}).")
    except Exception as e:
        print(f"UNEXPECTED ERROR in get_current_username (user_management): {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)

# MODIFIED API ENDPOINT: Get All Backend Users
@router.get("/api/users", response_model=List[UserResponse], tags=["User Management"])
async def get_users(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    # Query parameter now expects 'department_name' (e.g., "Finance")
    department_name: Optional[str] = Query(
        None,
        description="The exact name of the department as it appears in the database (e.g., 'Finance', 'Risk', 'Compliance')."
    )
) -> List[UserResponse]:
    """
    Retrieves a list of users, optionally filtered by department name.

    **Query Parameter:**
    - `department_name` (string, optional): The exact name of the department
      you want to get users for, as returned by the `/api/departments` endpoint.
      Example: `http://34.47.219.225:9000/api/users?department_name=Finance`
    """
    try:
        # Pass the department_name directly to the matcher method
        users = await matcher.fetch_backend_users(department_name=department_name)
        return users
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


# NEW API ENDPOINT: GET /api/departments (Modified to use DepartmentNameResponse)
@router.get("/api/departments", response_model=List[DepartmentNameResponse], tags=["User Management"])
async def get_departments(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
) -> List[DepartmentNameResponse]:
    """
    Retrieves a list of all unique department names from the user table.
    """
    try:
        departments = await matcher.fetch_departments_data()
        return departments
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve departments: {e}")
