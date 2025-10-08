#routers/manual_file_confirm
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional, Union, Dict, Any, Annotated
import asyncio
import traceback
import json # Needed for json.loads()

from fastapi import APIRouter, HTTPException, Depends, Request, Form, Body, status # Add status for HTTP codes
from concurrent.futures import ThreadPoolExecutor

from models.base_models import I4CManualFileConfirmationData # Import the redefined model
from db.matcher import CaseEntryMatcher # CaseEntryMatcher for db methods

# Imports for authentication dependencies (reused)
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
        print(f"UNEXPECTED ERROR in get_current_username (i4c_confirmations): {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during authentication.")

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)


# NEW API ENDPOINT: Get I4C Document Master List
@router.get("/api/i4c-document-list")
async def get_i4c_document_list(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
) -> Dict[str, Any]:
    """
    Fetches the master list of document types that can be confirmed for I4C.
    """
    try:
        doc_list = await matcher.fetch_i4c_document_list()
        return {"success": True, "documents": doc_list}
    except Exception as e:
        print(f"Error fetching I4C document list: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch I4C document list. Error: {e}")
