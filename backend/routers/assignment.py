# routers/assignment.py
import psycopg2
from typing import Annotated, Dict, Any
import traceback
import time
from fastapi import APIRouter, HTTPException, Depends, Request, Body
from concurrent.futures import ThreadPoolExecutor

from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
#from keycloak import KeycloakOpenID
from keycloak.keycloak_openid import KeycloakOpenID

from db.matcher import CaseEntryMatcher, save_or_update_decision # Also need save_or_update_decision here

router = APIRouter()

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

def get_keycloak_openid_dependency(request: Request) -> KeycloakOpenID:
    return request.app.state.keycloak_openid

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)

@router.post("/api/case/{ack_no}/assign")
async def assign_case_api(
    ack_no: str,
    assigned_to_employee: Annotated[str, Body(..., embed=True, description="Name of the employee to assign the case to")],
    assigner_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)] # Need executor for save_or_update_decision
) -> Dict[str, Any]:
    """
    Handles assigning or reassigning a case based on user roles (CRO, Risk Officer, Others).
    Updates case_master (assigned_to, assigned_by, status) and case_decisions.
    """
    try:
        # Get the user_type of the assigner
        assigner_user_type = await matcher.fetch_user_type(assigner_username) # Call the new method
        if assigner_user_type is None:
            raise HTTPException(status_code=403, detail=f"Assigner user '{assigner_username}' not found or has no defined role.")

        # Call the core logic in db/matcher.py to handle assignment rules
        success = await matcher.assign_case_to_employee(
            ack_no=ack_no,
            assigned_to_employee_name=assigned_to_employee,
            assigner_username=assigner_username,
            assigner_user_type=assigner_user_type
        )

        if success:
            # After updating case_master, also update case_decisions via save_or_update_decision
            decision_update_payload = {
                "assignedEmployee": assigned_to_employee,
                "decisionAction": "Assigned", # Default action if assigned
                "comments": f"Case assigned by {assigner_username}.",
                "auditTrail": f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} - Assigned by {assigner_username} to {assigned_to_employee}."
            }
            # save_or_update_decision needs to be awaited directly.
            updated_decision_record = await save_or_update_decision(executor, ack_no, decision_update_payload)
            
            return {"success": True, "message": f"Case {ack_no} assigned to {assigned_to_employee} successfully.", "decision_record": updated_decision_record}
        else:
            raise HTTPException(status_code=404, detail=f"Case {ack_no} not found or assignment failed.")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in assign_case_api for case {ack_no}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to assign case. Error: {e}")
