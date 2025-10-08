# routers/case_entry.py
from fastapi import APIRouter, HTTPException, Depends, Request, Form, File, UploadFile, status # Added status for HTTP status codes
from typing import Annotated, Optional, Dict, List, Union, Any
from datetime import date, datetime
from fastapi.exceptions import RequestValidationError # Import RequestValidationError
# pydantic.ValidationError not needed if RequestValidationError catches it
import psycopg2 # For specific database error handling
import traceback
import json
import os
import asyncio
from concurrent.futures import as_completed
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from keycloak.keycloak_openid import KeycloakOpenID

from models.base_models import CaseEntryData # Import the Pydantic model
from db.connection import get_db_connection, get_db_cursor
from db.matcher import CaseEntryMatcher # Import the matcher class
from services.error_handler import ErrorHelper # Import ErrorHelper
from config import ERROR_LOG_DIR

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get Keycloak instance
def get_keycloak_openid_dependency(request: Request) -> KeycloakOpenID:
    return request.app.state.keycloak_openid

# Dependency to get current username from JWT token (optional)
async def get_current_username_optional(
    request: Request
) -> str:
    try:
        # Try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return "System"  # Default fallback
        
        token = auth_header.split(" ")[1]
        keycloak_openid_instance = request.app.state.keycloak_openid
        
        decoded_token = keycloak_openid_instance.decode_token(token)
        username: str = decoded_token.get("preferred_username") or decoded_token.get("sub")
        if username is None:
            return "System"  # Default fallback
        return username
    except Exception as e:
        print(f"Authentication failed, using System as fallback: {e}", flush=True)
        return "System"  # Default fallback

# Dependency to get the CaseEntryMatcher instance
def get_case_entry_matcher(request: Request) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=request.app.state.executor)

# Dependency for ErrorHelper
def get_error_helper_dependency(request: Request) -> ErrorHelper:
    return ErrorHelper(executor=request.app.state.executor)

async def process_single_case_entry(form_data_dict, matcher, error_helper, created_by_user="System"):
    try:
        case_data_instance = CaseEntryData(**form_data_dict)
        result = await matcher.match_data(case_data_instance, created_by_user=created_by_user)
        
        # Check if no match was found
        if result.get("no_match"):
            return {
                "result": result, 
                "error": {
                    "type": "no_match", 
                    "detail": result.get("no_match_message", "No Victim or Beneficiary account match found")
                }
            }
        
        # Always return a dict with result and error keys
        return {"result": result, "error": None}
    except RequestValidationError as e:
        return {"result": None, "error": {"type": "validation", "detail": e.errors()}}
    except ValueError as e:
        return {"result": None, "error": {"type": "value", "detail": str(e)}}
    except psycopg2.Error as e:
        return {"result": None, "error": {"type": "db", "detail": str(e)}}
    except Exception as e:
        return {"result": None, "error": {"type": "unknown", "detail": str(e)}}

@router.post("/api/process-bulk-file")
async def process_bulk_file(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_entry_matcher)],
    error_helper: Annotated[ErrorHelper, Depends(get_error_helper_dependency)],
    request: Request,
    file: UploadFile = File(...)
):
    content = await file.read()
    try:
        records = json.loads(content)
        if not isinstance(records, list):
            raise ValueError("Uploaded file must contain a JSON array of records.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {e}")

    # Get username from request (with fallback to System)
    current_username = await get_current_username_optional(request)
    
    # NEW: Check if this is a reverification flags file
    is_reverification_flags_file = await _is_reverification_flags_file(records)
    
    if is_reverification_flags_file:
        # Process as reverification flags and trigger mobile matching
        return await _process_reverification_flags_file(records, matcher, current_username)
    
    # Original case entry processing
    success_count = 0
    failed_count = 0
    errors = []
    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append({
                "index": idx,
                "error": "Record is not a JSON object.",
                "record": record
            })
            failed_count += 1
            continue
        result = await process_single_case_entry(record, matcher, error_helper, current_username)
        if result["error"] is not None:
            errors.append({
                "index": idx,
                "error": result["error"],
                "record": record
            })
            failed_count += 1
        else:
            success_count += 1

    # Build error summaries with fields for download
    def extract_error_fields(err):
        # Pydantic validation errors
        if isinstance(err, dict) and err.get('type') == 'validation' and isinstance(err.get('detail'), list):
            try:
                field_names = set()
                for v in err['detail']:
                    if isinstance(v, dict):
                        loc = v.get('loc')
                        if isinstance(loc, list) and len(loc) > 1 and isinstance(loc[1], str):
                            field_names.add(loc[1])
                return list(field_names)
            except Exception:
                return []
        # Database duplicate key errors
        if isinstance(err, dict) and err.get('type') == 'db' and isinstance(err.get('detail'), str):
            msg = err['detail']
            if 'duplicate key value violates unique constraint' in msg:
                if 'case_main_source_ack_no_key' in msg:
                    return ['source_ack_no', 'ackNo']
                return ['ackNo']
        return []

    error_summaries = []
    if failed_count > 0:
        for e in errors:
            record = e.get('record', {})
            ack_no_val = record.get('ackNo') if isinstance(record, dict) else None
            err = e.get('error')
            err_type = (err.get('type') if isinstance(err, dict) else 'unknown')
            err_detail = (err.get('detail') if isinstance(err, dict) else str(err))
            fields = extract_error_fields(err)

            # Normalize validation details to a readable string
            if err_type == 'validation' and isinstance(err_detail, list):
                try:
                    msg = '; '.join([
                        f"{(v.get('loc', [None, None])[1] if isinstance(v.get('loc'), list) and len(v.get('loc')) > 1 else '')}: {v.get('msg', '')}"
                        for v in err_detail if isinstance(v, dict)
                    ])
                except Exception:
                    msg = json.dumps(err_detail)
            else:
                msg = err_detail if isinstance(err_detail, str) else json.dumps(err_detail)

            error_summaries.append({
                "index": e.get('index'),
                "ackNo": ack_no_val,
                "error_type": err_type,
                "error_message": msg,
                "fields": fields,
                "record": record
            })

    # Write error file if failures exist
    error_file_name = None
    if error_summaries:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        error_file_name = f"errors_{timestamp}.json"
        file_path = os.path.join(ERROR_LOG_DIR, error_file_name)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({
                    "summary": {
                        "total": len(records),
                        "success": success_count,
                        "failed": failed_count
                    },
                    "errors": error_summaries
                }, f, ensure_ascii=False, indent=2)
        except Exception as _e:
            print(f"Failed to write error log file: {_e}", flush=True)
            error_file_name = None

    response = {
        "message": f"Processed {len(records)} records.",
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": errors
    }
    if error_file_name:
        response["error_file_path"] = error_file_name
    return response

@router.post("/api/process-bulk-file-optimized")
async def process_bulk_file_optimized(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_entry_matcher)],
    error_helper: Annotated[ErrorHelper, Depends(get_error_helper_dependency)],
    request: Request,
    file: UploadFile = File(...)
):
    """
    Optimized bulk file processing with parallel batch processing for better performance.
    Processes records in batches with concurrent execution to significantly reduce processing time.
    """
    content = await file.read()
    try:
        records = json.loads(content)
        if not isinstance(records, list):
            raise ValueError("Uploaded file must contain a JSON array of records.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {e}")

    # Get username from request (with fallback to System)
    current_username = await get_current_username_optional(request)
    
    # Check if this is a reverification flags file
    is_reverification_flags_file = await _is_reverification_flags_file(records)
    if is_reverification_flags_file:
        return await _process_reverification_flags_file(records, matcher, current_username)
    
    # OPTIMIZED: Process records in batches with parallel execution
    batch_size = 10  # Process 10 records at a time
    success_count = 0
    failed_count = 0
    errors = []
    
    print(f"🚀 Starting optimized bulk processing of {len(records)} records in batches of {batch_size}")
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        batch_start_idx = i
        
        # Process batch in parallel
        tasks = []
        for idx, record in enumerate(batch):
            if not isinstance(record, dict):
                errors.append({
                    "index": batch_start_idx + idx,
                    "error": "Record is not a JSON object.",
                    "record": record
                })
                failed_count += 1
                continue
            
            # Create async task for each record
            task = asyncio.create_task(
                process_single_case_entry_with_index(
                    record, matcher, error_helper, current_username, batch_start_idx + idx
                )
            )
            tasks.append(task)
        
        # Wait for batch to complete
        if tasks:
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    failed_count += 1
                    errors.append({
                        "index": len(errors),
                        "error": {"type": "exception", "detail": str(result)},
                        "record": {}
                    })
                elif result["error"] is not None:
                    failed_count += 1
                    errors.append(result)
                else:
                    success_count += 1
        
        # Progress logging
        processed = min(i + batch_size, len(records))
        print(f"📊 Processed {processed}/{len(records)} records. Success: {success_count}, Failed: {failed_count}")

    # Build error summaries with fields for download
    def extract_error_fields(err):
        # Pydantic validation errors
        if isinstance(err, dict) and err.get('type') == 'validation' and isinstance(err.get('detail'), list):
            try:
                field_names = set()
                for v in err['detail']:
                    if isinstance(v, dict):
                        loc = v.get('loc')
                        if isinstance(loc, list) and len(loc) > 1 and isinstance(loc[1], str):
                            field_names.add(loc[1])
                return list(field_names)
            except Exception:
                return []
        # Database duplicate key errors
        if isinstance(err, dict) and err.get('type') == 'db' and isinstance(err.get('detail'), str):
            msg = err['detail']
            if 'duplicate key value violates unique constraint' in msg:
                if 'case_main_source_ack_no_key' in msg:
                    return ['source_ack_no', 'ackNo']
                return ['ackNo']
        return []

    error_summaries = []
    if failed_count > 0:
        for e in errors:
            record = e.get('record', {})
            ack_no_val = record.get('ackNo') if isinstance(record, dict) else None
            err = e.get('error')
            err_type = (err.get('type') if isinstance(err, dict) else 'unknown')
            err_detail = (err.get('detail') if isinstance(err, dict) else str(err))
            fields = extract_error_fields(err)

            # Normalize validation details to a readable string
            if err_type == 'validation' and isinstance(err_detail, list):
                try:
                    msg = '; '.join([
                        f"{(v.get('loc', [None, None])[1] if isinstance(v.get('loc'), list) and len(v.get('loc')) > 1 else '')}: {v.get('msg', '')}"
                        for v in err_detail if isinstance(v, dict)
                    ])
                except Exception:
                    msg = json.dumps(err_detail)
            else:
                msg = err_detail if isinstance(err_detail, str) else json.dumps(err_detail)

            error_summaries.append({
                "index": e.get('index'),
                "ackNo": ack_no_val,
                "error_type": err_type,
                "error_message": msg,
                "fields": fields,
                "record": record
            })

    # Write error file if failures exist
    error_file_name = None
    if error_summaries:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        error_file_name = f"errors_{timestamp}.json"
        file_path = os.path.join(ERROR_LOG_DIR, error_file_name)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({
                    "summary": {
                        "total": len(records),
                        "success": success_count,
                        "failed": failed_count
                    },
                    "errors": error_summaries
                }, f, ensure_ascii=False, indent=2)
        except Exception as _e:
            print(f"Failed to write error log file: {_e}", flush=True)
            error_file_name = None

    response = {
        "message": f"Processed {len(records)} records.",
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": errors
    }
    if error_file_name:
        response["error_file_path"] = error_file_name
    return response

# Helper function with index tracking for optimized processing
async def process_single_case_entry_with_index(record, matcher, error_helper, username, index):
    """
    Helper function to process a single case entry with index tracking for parallel processing.
    """
    try:
        result = await process_single_case_entry(record, matcher, error_helper, username)
        if result["error"] is not None:
            return {
                "index": index,
                "error": result["error"],
                "record": record
            }
        return {"error": None}
    except Exception as e:
        return {
            "index": index,
            "error": {"type": "exception", "detail": str(e)},
            "record": record
        }

@router.post("/api/case-entry")
async def new_case_entry_api(
    ackNo: Annotated[str, Form()],
    customerName: Annotated[str, Form()], 
    subCategory: Annotated[str, Form()],
    transactionDate: Annotated[date, Form()],
    complaintDate: Annotated[date, Form()],
    reportDateTime: Annotated[str, Form()],
    state: Annotated[str, Form()],
    district: Annotated[str, Form()],
    policestation: Annotated[str, Form()],
    paymentMode: Annotated[str, Form()],
    accountNumber: Annotated[Optional[Union[int, str]], Form()],
    cardNumber: Annotated[Optional[Union[int, str]], Form()],
    transactionId: Annotated[Union[int, str], Form()],
    layers: Annotated[str, Form()],
    transactionAmount: Annotated[float, Form()],
    disputedAmount: Annotated[float, Form()],
    action: Annotated[Optional[str], Form()],
    toBank: Annotated[str, Form()], 
    toAccount: Annotated[Optional[Union[int, str]], Form()],
    ifsc: Annotated[Optional[str], Form()],
    toTransactionId: Annotated[str, Form()], 
    toUpiId: Annotated[Optional[str], Form()],
    toAmount: Annotated[float, Form()], 
    actionTakenDate: Annotated[date, Form()], 
    #lienAmount: Annotated[Optional[float], Form()],
    #additionalInfo: Annotated[Optional[str], Form()],
    #evidence_file: Annotated[Optional[UploadFile], File()],
    
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_entry_matcher)],
    error_helper: Annotated[ErrorHelper, Depends(get_error_helper_dependency)],
    request: Request
):
    """
    Handles the submission of a new case entry, providing robust server-side validation
    and structured error responses from error_master.
    """
    form_data_dict = {
        "ackNo": ackNo, "customerName": customerName, "subCategory": subCategory, "transactionDate": transactionDate,
        "complaintDate": complaintDate, "reportDateTime": reportDateTime, "state": state, "district": district,
        "policestation": policestation, "paymentMode": paymentMode, "accountNumber": accountNumber,
        "cardNumber": cardNumber, "transactionId": transactionId, "layers": layers, "transactionAmount": transactionAmount,
        "disputedAmount": disputedAmount, "action": action, "toBank": toBank, "toAccount": toAccount,
        "ifsc": ifsc, "toTransactionId": toTransactionId, "toUpiId": toUpiId, "toAmount": toAmount,
        "actionTakenDate": actionTakenDate
    }

    try:
        case_data_instance = CaseEntryData(**form_data_dict)
        
        # Get username from request (with fallback to System)
        current_username = await get_current_username_optional(request)
        
        result = await matcher.match_data(case_data_instance, created_by_user=current_username)
        return {"result": result}

    except RequestValidationError as e: # Catches Pydantic's built-in validation errors
        print(f"❌ Frontend Validation Error (Pydantic): {e.errors()}", flush=True)
        return await error_helper.get_error_response(
            error_code='3001', # Use the 'Validation Error' code from error_master
            http_status_code=status.HTTP_400_BAD_REQUEST,
            detail_override="One or more fields failed validation.",
            validation_errors=e.errors() # Include Pydantic's detailed errors
        )
    except ValueError as e: # Catches custom ValueErrors from matcher methods (e.g., validate_numeric_field)
        print(f"❌ Backend Logic Validation Error: {e}", flush=True)
        return await error_helper.get_error_response(
            error_code='3001', # Use the 'Validation Error' code
            http_status_code=status.HTTP_400_BAD_REQUEST,
            detail_override=f"Details: {str(e)}"
        )
    except psycopg2.Error as e: # Catches database specific errors (e.g., UndefinedColumn, UniqueViolation)
        print(f"❌ Database Error in new_case_entry_api: {e}", flush=True)
        import traceback
        traceback.print_exc()
        
        if isinstance(e, psycopg2.errors.UniqueViolation):
            return await error_helper.get_error_response(
                error_code='3101', # Assuming '3101' is for UniqueViolation/ACK Exists
                http_status_code=status.HTTP_409_CONFLICT, # 409 Conflict for duplicate resource
                detail_override=f"The Acknowledgement Number you provided might already exist. Details: {str(e)}"
            )
        else:
            return await error_helper.get_error_response(
                error_code='2001', # Generic Database Error
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail_override=f"A database error occurred. Details: {str(e)}"
            )
    except Exception as e: # Catch any other unexpected server errors
        print(f"UNEXPECTED ERROR in new_case_entry_api: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return await error_helper.get_error_response(
            error_code='5000', # Generic Unexpected Server Error
            http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail_override=f"An unexpected server error occurred. Details: {str(e)}"
        )


async def _is_reverification_flags_file(records: List[Dict[str, Any]]) -> bool:
    """
    Check if the uploaded JSON file contains reverification flags data
    by looking for the expected column names from reverification_flags table
    """
    if not records or len(records) == 0:
        return False
    
    # Expected columns from reverification_flags table
    expected_columns = {
        'mobile_number', 'reason_flagged', 'flagged_date', 
        'lsacode', 'tspname', 'sensitivity_index', 'distribution_details'
    }
    
    # Check first few records to see if they contain reverification flags columns
    sample_size = min(3, len(records))
    reverification_flags_count = 0
    
    for i in range(sample_size):
        record = records[i]
        if isinstance(record, dict):
            # Count how many expected columns are present in this record
            present_columns = set(record.keys()) & expected_columns
            if len(present_columns) >= 4:  # At least 4 out of 7 expected columns
                reverification_flags_count += 1
    
    # If majority of sample records look like reverification flags, treat as such
    return reverification_flags_count >= (sample_size // 2 + 1)


async def _process_reverification_flags_file(records: List[Dict[str, Any]], 
                                           matcher: CaseEntryMatcher, 
                                           current_username: str) -> Dict[str, Any]:
    """
    Process reverification flags JSON file by:
    1. Inserting records into reverification_flags table
    2. Triggering mobile matching API to create MM, ECBNT, ECBT cases
    """
    try:
        print(f"🔄 Processing reverification flags file with {len(records)} records...")
        
        # Step 1: Insert records into reverification_flags table
        inserted_count = await _insert_reverification_flags(records, matcher)
        
        if inserted_count == 0:
            return {
                "message": "No valid reverification flags records found to insert",
                "records_processed": 0,
                "records_inserted": 0,
                "mm_cases_created": 0,
                "ecb_cases_created": 0,
                "success": False
            }
        
        print(f"✅ Inserted {inserted_count} reverification flags records")
        
        # Step 2: Trigger mobile matching API for current upload only
        print("🔄 Triggering mobile matching API for current upload...")
        mm_result = await matcher.create_mobile_matching_cases_for_upload(records)
        
        return {
            "message": f"Reverification flags processed successfully. Inserted {inserted_count} records and created {mm_result.get('mm_cases_created', 0)} MM cases and {mm_result.get('ecb_cases_created', 0)} ECB cases.",
            "records_processed": len(records),
            "records_inserted": inserted_count,
            "mm_cases_created": mm_result.get('mm_cases_created', 0),
            "ecb_cases_created": mm_result.get('ecb_cases_created', 0),
            "mm_cases_details": mm_result.get('mm_cases_details', []),
            "ecb_cases_details": mm_result.get('ecb_cases_details', []),
            "success": True
        }
        
    except Exception as e:
        print(f"❌ Error processing reverification flags file: {e}")
        import traceback
        traceback.print_exc()
        return {
            "message": f"Error processing reverification flags file: {str(e)}",
            "records_processed": len(records),
            "records_inserted": 0,
            "mm_cases_created": 0,
            "ecb_cases_created": 0,
            "success": False,
            "error": str(e)
        }


async def _insert_reverification_flags(records: List[Dict[str, Any]], 
                                     matcher: CaseEntryMatcher) -> int:
    """
    Insert reverification flags records into the database
    """
    def _sync_insert_flags():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                inserted_count = 0
                
                for record in records:
                    if not isinstance(record, dict):
                        continue
                    
                    # Extract fields with defaults
                    mobile_number = record.get('mobile_number')
                    reason_flagged = record.get('reason_flagged')
                    flagged_date = record.get('flagged_date')
                    lsacode = record.get('lsacode')
                    tspname = record.get('tspname')
                    sensitivity_index = record.get('sensitivity_index')
                    distribution_details = record.get('distribution_details')
                    
                    # Skip if no mobile number
                    if not mobile_number:
                        continue
                    
                    try:
                        # Insert into reverification_flags table
                        cur.execute("""
                            INSERT INTO public.reverification_flags (
                                mobile_number, reason_flagged, flagged_date, 
                                lsacode, tspname, sensitivity_index, distribution_details
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (mobile_number) DO UPDATE SET
                                reason_flagged = EXCLUDED.reason_flagged,
                                flagged_date = EXCLUDED.flagged_date,
                                lsacode = EXCLUDED.lsacode,
                                tspname = EXCLUDED.tspname,
                                sensitivity_index = EXCLUDED.sensitivity_index,
                                distribution_details = EXCLUDED.distribution_details
                        """, (
                            mobile_number, reason_flagged, flagged_date,
                            lsacode, tspname, sensitivity_index, distribution_details
                        ))
                        inserted_count += 1
                        
                    except Exception as e:
                        print(f"❌ Error inserting reverification flag for mobile {mobile_number}: {e}")
                        continue
                
                conn.commit()
                return inserted_count
    
    return await matcher._execute_sync_db_op(_sync_insert_flags)
