# routers/ecb_cases.py
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any, Annotated
import traceback

from fastapi import APIRouter, HTTPException, Depends, Request
from concurrent.futures import ThreadPoolExecutor

from db.matcher import CaseEntryMatcher
from models.base_models import ECBCaseData # Import the new model

# Imports for authentication dependencies (if needed)
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
#from keycloak import KeycloakOpenID
from keycloak.keycloak_openid import KeycloakOpenID

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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials: Username missing in token.")
        return username
    except JWTError as e:
        print(f"ERROR: JWT Decoding/Validation failed: {e}", flush=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not validate credentials: Invalid token ({e}).")
    except Exception as e:
        print(f"UNEXPECTED ERROR in get_current_username (ecb_cases): {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during authentication.")

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)


# NEW API ENDPOINT: Create ECBT/ECBNT Case
@router.post("/api/create-ecb-case")
async def create_ecb_case_api(
    ecb_data: ECBCaseData, # Pydantic model for ECBT/ECBNT case data
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)] # Requires authentication
) -> Dict[str, Any]:
    """
    Creates an ECBT or ECBNT case (Stage 2 Internal Cases) based on beneficiary and transaction details.
    Sets is_operational=False.
    """
    try:
        result = await matcher.create_ecb_case(ecb_data)
        return {"success": True, "message": result.get("message"), "case_details": result}
    except Exception as e:
        print(f"Error creating ECB/ECBNT case: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create ECB/ECBNT case. Error: {e}")
