# routers/combined_data.py
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

@router.get("/api/ecbnt-matching-bene/{case_id}")
async def get_ecbnt_matching_bene(
    case_id: int
) -> Dict[str, Any]:
    """
    For a given case_id, finds all bene_acc_num in acc_bene where cust_acct_num matches acc_num from case_main,
    and returns those bene_acc_num that also match source_bene_accno in case_main for that case.
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor
    try:
        # Connect to DB (reuse config if available)
        from config import DB_CONNECTION_PARAMS
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1. Get acc_num and source_bene_accno for the given case_id
                cur.execute("SELECT acc_num, source_bene_accno FROM case_main WHERE case_id = %s", (case_id,))
                row = cur.fetchone()
                if not row:
                    return {"beneficiaries": []}
                acc_num = row["acc_num"]
                source_bene_accno = row["source_bene_accno"]
                if not acc_num:
                    return {"beneficiaries": []}
                # 2. Find all bene_acct_num in acc_bene where cust_acct_num = acc_num
                cur.execute("SELECT bene_acct_num FROM acc_bene WHERE cust_acct_num = %s", (acc_num,))
                bene_rows = cur.fetchall()
                beneficiaries = []
                for r in bene_rows:
                    bene_acct = r["bene_acct_num"]
                    is_match = (bene_acct == source_bene_accno)
                    beneficiaries.append({"bene_acct_num": bene_acct, "is_match": is_match})
                return {"beneficiaries": beneficiaries}
    except Exception as e:
        print(f"Error in /api/ecbnt-matching-bene/{case_id}: {e}", flush=True)
        return {"beneficiaries": []}
