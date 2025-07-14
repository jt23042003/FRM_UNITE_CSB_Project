# routers/beneficiary_onboarding.py
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date
from typing import Optional, Any, Dict, List, Annotated
import asyncio
import traceback

from fastapi import APIRouter, HTTPException, Depends, Request
from concurrent.futures import ThreadPoolExecutor

# FIX: Import CaseEntryMatcher instead of DatabaseMatcher
from db.matcher import CaseEntryMatcher, CaseNotFoundError
from models.base_models import BeneficiaryData

router = APIRouter()

# Dependency to get the ThreadPoolExecutor instance
def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

# FIX: Dependency to get the CaseEntryMatcher instance
def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)


@router.post("/api/beneficiary-onboard-check")
async def beneficiary_onboard_check(
    beneficiary_data: BeneficiaryData,
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)] # FIX: Use CaseEntryMatcher
) -> Dict[str, Any]:
    """
    Receives new beneficiary data, performs matching, and creates an internal review case if flagged.
    """
    try:
        # Call the method on the CaseEntryMatcher instance
        result = await matcher.create_nab_case_if_flagged(beneficiary_data)

        if result:
            return {"success": True, "message": "Beneficiary checked. Case created for review.", "case_details": result}
        else:
            return {"success": True, "message": "Beneficiary checked. No red flags found, no case created."}

    except Exception as e:
        print(f"Error processing beneficiary onboard check: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process beneficiary. Error: {e}")


# NEW API ENDPOINT: Verify Beneficiary (POST /api/verify-beneficiary)
@router.post("/api/verify-beneficiary")
async def verify_beneficiary_api(
    beneficiary_data: BeneficiaryData, # Expecting the BeneficiaryData payload
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
) -> Dict[str, Any]:
    """
    Verifies a beneficiary against existing flagged data sources (cyber_complaints, suspect_entries).
    Returns match status without creating a case automatically.
    """
    try:
        match_status = await matcher.verify_beneficiary_data(beneficiary_data) # Call new matcher method

        return {
            "success": True,
            "message": "Beneficiary verification processed.",
            "match_status": match_status # This will contain matched, match_type, matched_fields
        }
    except Exception as e:
        print(f"Error verifying beneficiary: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to verify beneficiary. Error: {e}")
