# routers/auth.py
import requests
from fastapi import APIRouter, HTTPException, Depends, status, Request # Import Request
from fastapi.responses import JSONResponse
#from keycloak import KeycloakOpenID
from config import KEYCLOAK_CONFIG
from models.base_models import LoginRequest

# Imports for CaseEntryMatcher and ThreadPoolExecutor (for matcher dependency)
from db.matcher import CaseEntryMatcher # Import CaseEntryMatcher
from concurrent.futures import ThreadPoolExecutor # For type hinting executor

from typing import Optional, Any, Dict, List, Annotated

router = APIRouter()

# Dependency to get the KeycloakOpenID instance (from main.py's app.state)
def get_keycloak_openid_instance(request: Request) -> KeycloakOpenID:
    return request.app.state.keycloak_openid

# Dependency to get the CaseEntryMatcher instance (from main.py's app.state)
def get_case_matcher_instance(request: Request) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=request.app.state.executor)

# Dependency to get the ThreadPoolExecutor (from main.py's app.state)
def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

# NEW: Explicit OPTIONS route for /api/login to handle CORS preflight
@router.options("/api/login")
async def options_login_api():
    """Handles CORS preflight requests for the /api/login endpoint."""
    return {"message": "OK"} # A simple 200 OK response

@router.post("/api/login")
async def login_for_access_token(
    form_data: LoginRequest,
    keycloak_openid_instance: Annotated[KeycloakOpenID, Depends(get_keycloak_openid_instance)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)], # FIX: Inject matcher
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)] # FIX: Inject executor
) -> Dict[str, str]: # Return type will expand to include user_type
    """
    Authenticates a user and returns JWT access token, refresh token, and user_type.
    """
    try:
        token_response = keycloak_openid_instance.token(
            username=form_data.username,
            password=form_data.password,
            grant_type='password'
        )

        if not token_response or "access_token" not in token_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = token_response["access_token"]
        refresh_token = token_response.get("refresh_token")
        
        # FIX: Decode token to get username (similar to get_current_username)
        # This is temporary to get username from token for user_type lookup.
        # In a real scenario, you might have a dedicated service for this.
        # This logic is complex because keycloak_openid_instance.decode_token needs a public key or client secret.
        # We'll use the secret from config for simplicity here.
        
        # You will need your KEYCLOAK_CONFIG imported here for jwt.decode
        from config import KEYCLOAK_CONFIG # Ensure this import is at the top

        try:
            # Decode the token (needs secret key or public key from config)
            # This is a bit redundant as keycloak_openid_instance.token already validates
            # but we need username from claims
            decoded_token = keycloak_openid_instance.decode_token(access_token)
            username_from_token: str = decoded_token.get("preferred_username") or decoded_token.get("sub")
            if not username_from_token:
                raise ValueError("Username claim missing in token.")

            # FIX: Fetch user_type from db/matcher.py
            user_type = await matcher.fetch_user_type(username_from_token) # Call fetch_user_type
            if user_type is None:
                # If user is in Keycloak but not in your user_table, decide behavior
                print(f"WARNING: User '{username_from_token}' logged in via Keycloak but not found in user_table. Defaulting to 'others' type.", flush=True)
                user_type = 'others' # Default role if not found in user_table

        except Exception as e:
            print(f"Error decoding token or fetching user_type during login: {e}", flush=True)
            user_type = 'others' # Default to a safe role on error
        
        # FIX: Include user_type in the response
        return JSONResponse(content={
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "user_type": user_type, # Include user_type
            "username": username_from_token # Also include username for frontend convenience
        })

    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        print(f"Keycloak connection error during login: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable."
        )
    except Exception as e:
        print(f"Unexpected error during login: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred during login."
        )
