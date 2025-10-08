# routers/i4c_match.py
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional, Union, Dict, Any, Annotated
import asyncio
import traceback

from fastapi import APIRouter, HTTPException, Depends, Request, Form # Form might not be needed if only match_i4c
from concurrent.futures import ThreadPoolExecutor

# Relative imports
from models.base_models import I4CData # Import I4CData model for match_i4c
# No longer importing NewCustomerRequest or BeneficiaryData in this file
# because screen_new_customers and verify_beneficiary are moved.
from db.matcher import DatabaseMatcher, CaseNotFoundError # CaseNotFoundError is used

router = APIRouter()

# Dependency to get the ThreadPoolExecutor instance
def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

# Dependency to get the DatabaseMatcher instance
def get_database_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> DatabaseMatcher:
    return DatabaseMatcher(executor=executor)


# Endpoint for matching I4C data (if this is still active/desired here)
# This uses DatabaseMatcher, as its match_data typically operates on I4CData.
@router.post("/api/match-i4c-data")
async def match_i4c(
    i4c_data: I4CData,
    matcher: Annotated[DatabaseMatcher, Depends(get_database_matcher_instance)]
) -> Dict[str, Any]:
    """
    Receives I4C data and performs matching based on predefined criteria.
    """
    try:
        # Assuming matcher.match_data is correctly defined in DatabaseMatcher
        result = await matcher.match_data(i4c_data)
        return {"message": result}
    except Exception as e:
        print(f"Error in /api/match-i4c-data: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to match I4C data: {e}")



