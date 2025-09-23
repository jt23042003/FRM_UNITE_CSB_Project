# routers/transaction.py
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date
from typing import Optional, Any, Dict, List, Annotated
import asyncio
import traceback

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from db.matcher import CaseEntryMatcher, CaseNotFoundError # CaseNotFoundError is used
from concurrent.futures import ThreadPoolExecutor # Needed for get_executor_dependency

router = APIRouter()

# Dependency to get the CaseEntryMatcher instance
def get_case_matcher_instance(request: Request) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=request.app.state.executor)

# Dependency to get the ThreadPoolExecutor instance (from main.py's app.state)
def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor


@router.get("/api/case/{ack_no}/transactions")
async def get_transactions_api_route(
    ack_no: str, # Required path parameter
    type: Annotated[str, Query(description="Type of user: 'victim' or 'beneficiary'")], # Required Query parameter

    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)], # Has default
    from_date: Annotated[date, Query(alias="from", description="Start date for transactions (YYYY-MM-DD)")], # Has default
    to_date: Annotated[date, Query(description="End date for transactions (YYYY-MM-DD)")] = date.today() # Has default
    #matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)] # Has default
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieves transaction details for a given case.
    """
    # Get integer case_id from case_main using ack_no first
    try:
        case_main_record = await matcher.fetch_single_case_details_from_case_main_by_ack_no(ack_no)
        if not case_main_record or not case_main_record.get('case_id'):
            raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in new system.")
        # integer_case_id = case_main_record.get('case_id') # Not directly used here, but obtained for context
        source_ack_no_for_old_tables = case_main_record.get('source_ack_no') # To query old case_entry_form/txn

    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in new system. Error: {e}")
    except Exception as e:
        print(f"ERROR: Failed to fetch case_id for ACK No {ack_no} during transactions fetch: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error fetching case details: {e}")

    print(f"ack_no: {ack_no} (Source ACK No: {source_ack_no_for_old_tables})", flush=True)
    print(f"\n--- DEBUG get_transactions_api_route START ---", flush=True)
    print(f"DEBUG: Endpoint called with ack_no: {ack_no}, from: {from_date}, to: {to_date}, type: {type}", flush=True)

    # Pass the source_ack_no (string) to fetch_transactions as it queries old case_entry_form/txn table
    transaction_list = await matcher.fetch_transactions(source_ack_no_for_old_tables, from_date, to_date, type)

    print(f"DEBUG: get_transactions_api_route: Collected {len(transaction_list)} transactions.", flush=True)
    print(f"--- DEBUG get_transactions_api_route END ---", flush=True)

    return {"transactions": transaction_list}


@router.get("/api/case/{ack_no}/customer-details")
async def get_customer_details(
    ack_no: str,
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
) -> Dict[str, Any]:
    """
    Retrieves detailed customer information related to a case.
    """
    # FIX: Get integer case_id from case_main using ack_no (or directly use ack_no in matcher method if it accepts it)
    try:
        # fetch_case_customer_details accepts Union[int, str] so pass ack_no directly
        customer_data = await matcher.fetch_case_customer_details(ack_no)
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in new system. Error: {e}")
    except Exception as e:
        print(f"ERROR: Failed to fetch case_id for ACK No {ack_no} during customer details fetch: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error fetching case details: {e}")
    
    if not customer_data:
        raise HTTPException(status_code=404, detail="Acknowledgement No. not found or no customer details associated.")

    return customer_data


@router.get("/api/case/{ack_no}/risk-profile")
async def get_risk_entity_profile(
    ack_no: str,
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Retrieves victim and beneficiary risk profiles for a given case.
    """
    # FIX: Pass ack_no directly to fetch_case_risk_profile (it accepts Union[int, str])
    try:
        risk_profiles = await matcher.fetch_case_risk_profile(ack_no)
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in new system. Error: {e}")
    except Exception as e:
        print(f"ERROR: Failed to fetch case_id for ACK No {ack_no} during risk profile fetch: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error fetching case details: {e}")

    if not risk_profiles or (not risk_profiles.get("victim") and not risk_profiles.get("beneficiary")):
         raise HTTPException(status_code=404, detail="Risk profiles not found for this Acknowledgement No.")

    return risk_profiles
