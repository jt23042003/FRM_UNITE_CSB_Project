"""
Case Assignment Router - Simplified Version

API endpoints for managing case assignments with simplified logic.
All cases go to general risk officer queue.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from typing import Annotated, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
# COMMENTED OUT: Complex assignment service
# from services.case_assignment_service import CaseAssignmentService
from keycloak.keycloak_openid import KeycloakOpenID
from fastapi.security import OAuth2PasswordBearer
import traceback
from jose import JWTError
import psycopg2
from config import DB_CONNECTION_PARAMS

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
        print(f"UNEXPECTED ERROR in get_current_username (case_assignment): {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

# COMMENTED OUT: Complex assignment service dependency
# def get_assignment_service(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseAssignmentService:
#     return CaseAssignmentService(executor)

@router.get("/api/assignment/statistics")
async def get_assignment_statistics(
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Get current case assignment statistics - simplified version
    """
    try:
        # SIMPLIFIED: Direct database query instead of complex service
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Get risk officers
                cur.execute("""
                    SELECT user_name, dept 
                    FROM user_table 
                    WHERE user_type = 'risk_officer'
                    ORDER BY user_name
                """)
                risk_officers = [{"username": row[0], "dept": row[1]} for row in cur.fetchall()]
                
                # Get actual case counts
                cur.execute("""
                    SELECT assigned_to, COUNT(*) as case_count
                    FROM assignment 
                    WHERE is_active = TRUE
                    GROUP BY assigned_to
                """)
                actual_counts = {row[0]: row[1] for row in cur.fetchall()}
        
        stats = {
            'risk_officers': [officer['username'] for officer in risk_officers],
            'actual_counts': actual_counts,
            'assignment_method': 'simplified_general_queue',
            'note': 'All cases assigned to general risk officer queue'
        }
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        print(f"ERROR: Failed to get assignment statistics: {e}", flush=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve assignment statistics")

@router.post("/api/assignment/assign-case")
async def manually_assign_case(
    case_id: Annotated[int, Body(..., embed=True)],
    case_type: Annotated[str, Body(..., embed=True)],
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Manually trigger case assignment for a specific case - simplified version
    """
    try:
        # SIMPLIFIED: Direct assignment to general queue
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Get first available risk officer
                cur.execute("""
                    SELECT user_name 
                    FROM user_table 
                    WHERE user_type = 'risk_officer'
                    ORDER BY user_name
                    LIMIT 1
                """)
                result = cur.fetchone()
                
                if not result:
                    return {
                        "success": False,
                        "message": "No risk officers available for assignment"
                    }
                
                assigned_user = result[0]
                
                # Ensure assignment table columns exist
                cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
                cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS assignment_type VARCHAR(50) DEFAULT 'manual'")
                
                # Insert assignment record
                cur.execute("""
                    INSERT INTO assignment (case_id, assigned_to, assigned_by, comment, is_active, assignment_type)
                    VALUES (%s, %s, %s, %s, TRUE, 'manual')
                """, (case_id, assigned_user, current_username, f"Manually assigned {case_type} case to general queue"))
                
                conn.commit()
        
        return {
            "success": True,
            "message": f"Case {case_id} assigned to general queue: {assigned_user}",
            "assigned_to": assigned_user
        }
    except Exception as e:
        print(f"ERROR: Manual case assignment failed: {e}", flush=True)
        raise HTTPException(status_code=500, detail="Failed to assign case")

# COMMENTED OUT: Complex case type rules endpoints
# @router.get("/api/assignment/case-type-rules")
# async def get_case_type_rules(
#     assignment_service: Annotated[CaseAssignmentService, Depends(get_assignment_service)],
#     current_username: Annotated[str, Depends(get_current_username)]
# ) -> Dict[str, Any]:
#     """Get current case type assignment rules"""
#     # COMMENTED OUT: No longer using complex case type rules

# @router.post("/api/assignment/update-case-type-rules")
# async def update_case_type_rules(
#     rules: Annotated[Dict[str, str], Body(...)],
#     assignment_service: Annotated[CaseAssignmentService, Depends(get_assignment_service)],
#     current_username: Annotated[str, Depends(get_current_username)]
# ) -> Dict[str, Any]:
#     """Update case type assignment rules"""
#     # COMMENTED OUT: No longer using complex case type rules

@router.get("/api/assignment/risk-officers")
async def get_risk_officers(
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """
    Get list of all risk officers available for assignment - simplified version
    """
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_name, dept 
                    FROM user_table 
                    WHERE user_type = 'risk_officer'
                    ORDER BY user_name
                """)
                risk_officers = [{"username": row[0], "dept": row[1]} for row in cur.fetchall()]
        
        return {
            "success": True,
            "risk_officers": risk_officers
        }
    except Exception as e:
        print(f"ERROR: Failed to get risk officers: {e}", flush=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve risk officers")

# COMMENTED OUT: Round-robin reset endpoint (no longer needed)
# @router.post("/api/assignment/reset-round-robin")
# async def reset_round_robin_state(
#     assignment_service: Annotated[CaseAssignmentService, Depends(get_assignment_service)],
#     current_username: Annotated[str, Depends(get_current_username)]
# ) -> Dict[str, Any]:
#     """Reset the round-robin assignment state (admin function)"""
#     # COMMENTED OUT: No longer using round-robin logic
