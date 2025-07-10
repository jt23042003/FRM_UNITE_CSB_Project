# routers/user_management.py
import psycopg2 # Though not directly used, useful for error handling if added
from psycopg2.extras import RealDictCursor # Useful if doing direct cur.fetchall
from typing import List, Optional, Union, Dict, Any, Annotated
import asyncio
import traceback

from fastapi import APIRouter, HTTPException, Depends, Request # Removed Query as not used
from concurrent.futures import ThreadPoolExecutor

# Import CaseEntryMatcher which contains the fetch_backend_users method
from db.matcher import CaseEntryMatcher 

# Imports for authentication dependencies (required for this API as it fetches internal users)
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
#from keycloak import KeycloakOpenID
from keycloak.keycloak_openid import KeycloakOpenID

router = APIRouter()

# --- Shared Dependencies (Reused from other routers for consistency) ---
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


# --- NEW API ENDPOINT: Get All Backend Users ---
@router.get("/api/users")
async def get_backend_users_api(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)] # This API should be authenticated
) -> List[Dict[str, str]]: # Return type matches dummy response
    """
    Fetches a list of all backend users (id and formatted name) from the user_table.
    Requires authentication.
    """
    try:
        users = await matcher.fetch_backend_users()
        return users
    except Exception as e:
        print(f"Error fetching backend users list: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user list. Error: {e}")
