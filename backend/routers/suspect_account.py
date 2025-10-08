# routers/suspect_account.py
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date
from typing import Optional, Any, Dict, List, Annotated
import asyncio
import traceback

from fastapi import APIRouter, HTTPException, Depends, Request
from concurrent.futures import ThreadPoolExecutor

from db.matcher import CaseEntryMatcher, CaseNotFoundError
from models.base_models import PotentialSuspectAccountData # Ensure this model is imported

router = APIRouter()

# Dependency to get the ThreadPoolExecutor instance
def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

# Dependency to get the CaseEntryMatcher instance
def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)

@router.post("/api/potential-suspect-account")
async def potential_suspect_account_api(
    suspect_data: PotentialSuspectAccountData, # Expecting the new payload
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
) -> Dict[str, Any]:
    """
    Receives data for a customer/account, performs screening, and creates a PSA case if flagged.
    """
    try:
        result = await matcher.create_psa_case_if_flagged(suspect_data)

        if result:
            return {"success": True, "message": "Potential suspect account identified. Case created for review.", "case_details": result}
        else:
            return {"success": True, "message": "Account checked. No red flags found, no case created."}

    except Exception as e:
        print(f"Error processing potential suspect account: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process potential suspect account. Error: {e}")
