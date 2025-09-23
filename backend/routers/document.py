# routers/document.py
import os
import uuid
import shutil
import asyncio
import traceback
import json

from fastapi import APIRouter, HTTPException, Request, File, UploadFile, Form, Depends, status
from fastapi.responses import FileResponse
from typing import Annotated, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

# FIX: Import CaseEntryMatcher to fetch integer case_id
from db.matcher import insert_uploaded_document, get_uploaded_documents, get_document_by_id, CaseEntryMatcher, CaseNotFoundError, log_case_action
from config import UPLOAD_DIR, ERROR_LOG_DIR

router = APIRouter()

# Imports for authentication dependencies
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
            raise HTTPException(status_code=401, detail="Could not validate credentials: Username missing in token.")
        return username
    except JWTError as e:
        print(f"ERROR: JWT Decoding/Validation failed: {e}", flush=True)
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: Invalid token ({e}).")
    except Exception as e:
        print(f"UNEXPECTED ERROR in get_current_username (i4c_match): {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

# NEW: Dependency for CaseEntryMatcher (needed here)
def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)

@router.post("/api/case/{ack_no}/upload-documents")
@router.post("/api/case/{ack_no}/upload-document")
async def upload_multiple_documents_api(
    ack_no: str, # Original string ACK No from path
    request: Request,
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)], # FIX: Inject CaseEntryMatcher
    logged_in_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]: # Return type for clarity
    """
    Handles uploading documents to the new case_documents table, linking by case_main.case_id.
    """
    # FIX: Fetch the integer case_id from case_main using the ack_no
    try:
        case_main_record = await matcher.fetch_single_case_details_from_case_main_by_ack_no(ack_no)
        if not case_main_record or not case_main_record.get('case_id'):
            raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in the new case_main system. Cannot upload documents.")
        integer_case_id = case_main_record.get('case_id')
    except CaseNotFoundError as e: # Catch specific CaseNotFoundError from matcher method
        raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in the new case_main system. Error: {e}")
    except Exception as e:
        print(f"ERROR: Failed to fetch case_id for ACK No {ack_no} during upload: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error fetching case details for upload: {e}")

    form_data = await request.form()
    uploaded_docs = []
    
    print(f"DEBUG: Received upload request for ACK: {ack_no} (CaseID: {integer_case_id})", flush=True)
    print(f"DEBUG: Total form data items received: {len(form_data.items())}", flush=True)
    print(f"DEBUG: Form data keys received: {list(form_data.keys())}", flush=True)

    try:
        for field_name, value in form_data.items():
            print(f"DEBUG: Processing field '{field_name}'. Value Type: {type(value)}", flush=True)
            
            if isinstance(value, UploadFile): 
                print(f"DEBUG:   - Detected as an actual UploadFile. Filename: '{value.filename}', Content-Type: '{value.content_type}'", flush=True)
                
                file_extension = os.path.splitext(value.filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                saved_filepath = os.path.join(UPLOAD_DIR, unique_filename)
                
                doc_comment = form_data.get(f"{field_name}_comment", '') 

                def _sync_write_file(content_bytes: bytes):
                    with open(saved_filepath, "wb") as buffer:
                        buffer.write(content_bytes)

                file_content = await value.read()
                await asyncio.get_running_loop().run_in_executor(executor, _sync_write_file, file_content)
                print(f"DEBUG: File '{value.filename}' saved to disk at {saved_filepath}", flush=True)

                # FIX: Pass the integer case_id to insert_uploaded_document
                new_doc = await insert_uploaded_document(
                    executor,
                    case_id=integer_case_id, # Pass the integer case_id
                    document_type=field_name,
                    original_filename=value.filename,
                    saved_filepath=saved_filepath,
                    file_mime_type=value.content_type,
                    comment=doc_comment,
                    uploaded_by=logged_in_username
                )

                if new_doc and new_doc.get('id'):
                    uploaded_docs.append(new_doc)
                    print(f"DEBUG: ✅ DB record inserted for {value.filename} (ID: {new_doc.get('id')}). Returned data: {new_doc}", flush=True)
                    # Log document upload in case_logs
                    try:
                        log_case_action(integer_case_id, logged_in_username, "upload_document", f"{value.filename} ({value.content_type})")
                    except Exception as _log_err:
                        print(f"Warning: Failed to log document upload for case {integer_case_id}: {_log_err}")
                else:
                    print(f"DEBUG: ⚠️ DB record insert for {value.filename} returned None or empty. This indicates a problem with the DB insert returning data.", flush=True)
                    pass

            else:
                print(f"DEBUG:   - Identified as non-file item. Value for '{field_name}': '{value}' (Type: {type(value)})", flush=True)

        if uploaded_docs:
            print(f"DEBUG: Successfully processed {len(uploaded_docs)} document(s).", flush=True)
            return {"success": True, "message": f"{len(uploaded_docs)} file(s) processed and inserted successfully", "documents": uploaded_docs}
        else:
            print(f"DEBUG: No documents were added to uploaded_docs list. This indicates no files were correctly identified OR DB insert failed.", flush=True)
            return {"success": False, "message": "No files were successfully processed or inserted.", "documents": []}

    except HTTPException:
        raise
    except Exception as overall_error:
        print(f"ERROR: Overall file upload process failed: {overall_error}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Overall file upload failed. Error: {overall_error}")


@router.get("/api/case/{ack_no}/documents")
async def get_documents_api( # This endpoint is for old system, still uses ack_no string
    ack_no: str,
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)] # FIX: Inject CaseEntryMatcher
) -> Dict[str, Any]: # Return type for clarity
    """
    Retrieves documents for a case from the new case_documents table, linking by case_main.case_id.
    """
    # FIX: Get the integer case_id from case_main using ack_no first
    try:
        case_main_record = await matcher.fetch_single_case_details_from_case_main_by_ack_no(ack_no)
        if not case_main_record or not case_main_record.get('case_id'):
            raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in new system to retrieve documents.")
        
        integer_case_id = case_main_record.get('case_id')
        
        documents = await get_uploaded_documents(executor, integer_case_id)
        print(f"Fetched {len(documents)} documents from DB for ACK {ack_no} (CaseID: {integer_case_id}).", flush=True)
        return {"success": True, "documents": documents}
    except CaseNotFoundError as e: # Catch specific CaseNotFoundError from matcher method
        raise HTTPException(status_code=404, detail=f"Case ACK No '{ack_no}' not found in new system. Error: {e}")
    except Exception as e:
        print(f"Failed to fetch documents: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch documents.")


@router.get("/api/download-document/{document_id}")
async def download_document_api(
    document_id: int,
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> FileResponse: # Return type
    """Handles downloading a single uploaded document."""
    
    doc_record = await get_document_by_id(executor, document_id)

    if not doc_record:
        raise HTTPException(status_code=404, detail="Document not found in database.")

    file_path = doc_record.get('file_location') # Use file_location from new schema
    original_filename = doc_record.get('original_filename')
    file_mime_type = doc_record.get('file_mime_type') # Get mime type from DB

    if not os.path.realpath(file_path).startswith(os.path.realpath(UPLOAD_DIR)):
        raise HTTPException(status_code=403, detail="Access denied.")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server.")
    
    return FileResponse(path=file_path, filename=original_filename, media_type=file_mime_type)

@router.get("/api/download-error-log/{filename}")
async def download_error_log(filename: str) -> FileResponse: # Return type
    file_path = os.path.join(ERROR_LOG_DIR, filename)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Error log file not found.")
    if not os.path.realpath(file_path).startswith(os.path.realpath(ERROR_LOG_DIR)):
        raise HTTPException(status_code=400, detail="Invalid file path or access denied.")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/json"
    )

#router
@router.post("/api/operational-confirm")
async def operational_confirm_api(
    case_id: Annotated[int, Form()], 
    checked_documents: Annotated[str, Form()], # Frontend sends JSON.stringified list of names
    proof_of_upload_ref: Annotated[str, Form()],
    confirmation_action_status: Annotated[str, Form()], # Renamed 'status'
    screenshot: Annotated[Optional[UploadFile], File()],

    logged_in_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> Dict[str, Any]:
    """
    Records operational confirmations for documents manually sent to I4C.
    Inserts a single row into public.operational_confirmation with JSONB document statuses,
    and updates case_main status if 'submitted'.
    """
    try:
        # Parse document_statuses_json string into a Python list of dicts
        try:
            parsed_document_statuses = json.loads(checked_documents)
            if not isinstance(parsed_document_statuses, list):
                raise ValueError("checked_documents must be a JSON string of a list.")
        except json.JSONDecodeError:
            raise ValueError("checked_documents is not a valid JSON string.")
        
        # Determine case_ack_no from case_id
        case_main_record = await matcher.fetch_single_case_details_from_case_main_by_case_id(case_id)
        if not case_main_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID '{case_id}' not found in case_main.")
        case_ack_no = case_main_record.get('source_ack_no')

        # Handle screenshot file upload (optional)
        screenshot_file_name = None
        screenshot_file_location = None
        if screenshot:
            UPLOAD_DIR = "./fraud_uploads" 
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            file_extension = os.path.splitext(screenshot.filename)[1]
            unique_filename = f"CONFIRM_SS_{case_id}_{proof_of_upload_ref}_{uuid.uuid4().hex[:4]}{file_extension}" 
            screenshot_file_location = os.path.join(UPLOAD_DIR, unique_filename)
            screenshot_file_name = screenshot.filename 

            def _sync_save_screenshot(content_bytes: bytes):
                with open(screenshot_file_location, "wb") as buffer:
                    buffer.write(content_bytes)
            
            await asyncio.get_running_loop().run_in_executor(executor, _sync_save_screenshot, await screenshot.read())
            print(f"DEBUG: Screenshot '{screenshot_file_name}' saved to disk at {screenshot_file_location}", flush=True)
            
            await insert_uploaded_document( 
                executor=executor,
                case_id=case_id,
                document_type="Screenshot_Confirmation",
                original_filename=screenshot_file_name,
                saved_filepath=screenshot_file_location,
                file_mime_type=screenshot.content_type,
                comment=f"Screenshot for operational confirmation. Ref: {proof_of_upload_ref}.",
                uploaded_by=logged_in_username
            )
            print(f"DEBUG: Screenshot recorded in case_documents for case_id {case_id}.", flush=True)


        # FIX: Define confirmation_boolean_overall here
        confirmation_boolean_overall = (confirmation_action_status.lower() == 'submitted') # Determine if overall action is 'submitted'


        # Call the new summary insertion method
        print(f"DEBUG: operational_confirm_api - About to call insert_operational_confirmation_summary for case {case_id}, {case_ack_no}", flush=True)

        final_confirmation_record = await matcher.insert_operational_confirmation_summary(
            executor=executor,
            case_id=case_id,
            case_ack_no=case_ack_no,
            document_statuses_json=parsed_document_statuses, # This is the List[Dict[str,bool]]
            proof_of_upload_ref=proof_of_upload_ref,
            screenshot_file_location=screenshot_file_location,
            confirmation_boolean_overall=confirmation_boolean_overall, # Pass the defined variable
            created_by_user=logged_in_username
        )

        print(f"DEBUG: operational_confirm_api - insert_operational_confirmation_summary call returned: {final_confirmation_record}", flush=True)
        
        return {"success": True, "message": "Operational confirmation recorded successfully.", "record": final_confirmation_record}
    except ValueError as e: 
        print(f"ERROR: Caught ValueError in operational_confirm_api: {e}", flush=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Validation Error: {str(e)}")
    except HTTPException: 
        raise
    except Exception as e:
        print(f"ERROR: Caught UNEXPECTED Exception in operational_confirm_api: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to record confirmation. Error: {e}")

@router.get("/api/case/{case_id}/operational-confirmation")
async def get_operational_confirmation_api(
    case_id: int,
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> Dict[str, Any]:
    """
    Retrieves the latest operational confirmation data for a specific case.
    """
    try:
        confirmation_data = await matcher.fetch_operational_confirmation_log(case_id)
        
        if confirmation_data is None:
            raise HTTPException(status_code=404, detail=f"No operational confirmation found for case_id {case_id}")
        
        return {"success": True, "data": confirmation_data}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching operational confirmation for case_id {case_id}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch operational confirmation. Error: {e}")