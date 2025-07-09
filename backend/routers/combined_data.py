# routers/combined_data.py
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any, Annotated
import traceback

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from keycloak import KeycloakOpenID
from concurrent.futures import ThreadPoolExecutor

from db.matcher import CaseEntryMatcher, CaseNotFoundError # CaseEntryMatcher is where fetch_combined_case_data resides

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
        print(f"UNEXPECTED ERROR in get_current_username (combined_data): {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)

# --- API Endpoint for Combined Case Data ---
@router.get("/api/combined-case-data/{case_id}")
async def get_combined_case_data(
    case_id: int,
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)] # Authentication for this endpoint
) -> Dict[str, Any]:
    """
    Fetches comprehensive combined data for a single case from across various new and old tables.
    """
    try:
        combined_data = await matcher.fetch_combined_case_data(case_id)

        if not combined_data:
            raise HTTPException(status_code=404, detail=f"Combined case data for ID '{case_id}' not found.")
        
        return combined_data
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"UNEXPECTED ERROR in /api/combined-case-data/{case_id}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve combined case data.")
