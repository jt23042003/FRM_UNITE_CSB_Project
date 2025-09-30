# routers/new_case_list.py
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any, Annotated
import traceback

from fastapi import APIRouter, HTTPException, Query, Depends, Request, Body
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
#from keycloak import KeycloakOpenID
from keycloak.keycloak_openid import KeycloakOpenID

from concurrent.futures import ThreadPoolExecutor

from db.matcher import CaseEntryMatcher, log_case_action # CaseEntryMatcher is where fetch_new_cases_list resides
from fastapi import UploadFile
from models.base_models import CaseActionDataSaveRequest, CaseActionDataResponse
import os
import json
# --- File Upload Configuration ---
UPLOAD_DIR = "./fraud_uploads"  # Local development path
from config import DB_CONNECTION_PARAMS

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
        print(f"UNEXPECTED ERROR in get_current_username (new_case_list): {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)

# --- API Endpoint for New Case List with Server-side Pagination, Search, and Sorting ---
@router.get("/api/new-case-list")
async def get_new_case_list(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)],
    page: int = Query(1, description="Page number (1-based)"),
    page_size: int = Query(15, description="Number of cases per page"),
    search: Optional[str] = Query(None, description="Search across all fields"),
    sort_column: Optional[str] = Query(None, description="Column to sort by"),
    sort_direction: Optional[str] = Query("asc", description="Sort direction: asc or desc")
) -> Dict[str, Any]:
    """
    Fetches a paginated list of cases from the new case management system,
    with server-side search, sorting, and pagination.
    """
    user_type = None
    if logged_in_username:
        user_type = await matcher.fetch_user_type(logged_in_username)
        if user_type is None:
            print(f"WARNING: User '{logged_in_username}' not found in user_table. No role-based filtering applied.", flush=True)

    try:
        # Calculate skip from page and page_size
        skip = (page - 1) * page_size
        
        # Call the updated matcher method with new parameters
        result = await matcher.fetch_new_cases_list_paginated(
            skip=skip,
            limit=page_size,
            search=search,
            sort_column=sort_column,
            sort_direction=sort_direction,
            current_logged_in_username=logged_in_username,
            current_logged_in_user_type=user_type
        )

        return {
            "cases": result.get("cases", []),
            "total_count": result.get("total_count", 0),
            "total_pages": result.get("total_pages", 0),
            "current_page": page,
            "page_size": page_size,
            "logged_in_user_type": user_type,
            "logged_in_username": logged_in_username
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"UNEXPECTED ERROR in /api/new-case-list: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve new case list due to an internal server error.")

# NEW API ENDPOINT: Get all case IDs for bulk operations
@router.get("/api/new-case-list/all-case-ids")
async def get_all_case_ids(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)],
    search: Optional[str] = Query(None, description="Search across all fields")
) -> Dict[str, Any]:
    """
    Get all case IDs that match the search criteria for bulk operations.
    This is used for "select all across pages" functionality.
    """
    user_type = None
    if logged_in_username:
        user_type = await matcher.fetch_user_type(logged_in_username)
        if user_type is None:
            print(f"WARNING: User '{logged_in_username}' not found in user_table. No role-based filtering applied.", flush=True)

    try:
        result = await matcher.fetch_all_case_ids_for_bulk(
            search=search,
            current_logged_in_username=logged_in_username,
            current_logged_in_user_type=user_type
        )

        return {
            "case_ids": result.get("case_ids", []),
            "total_count": result.get("total_count", 0),
            "logged_in_user_type": user_type,
            "logged_in_username": logged_in_username
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"UNEXPECTED ERROR in /api/new-case-list/all-case-ids: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve case IDs for bulk operations.")

@router.post("/api/case/submit")
async def submit_case(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)],
    payload: dict = Body(...)
):
    """
    Submits a case by updating its status to 'Closed'.
    """
    case_id = payload.get("case_id")
    if not case_id:
        raise HTTPException(status_code=400, detail="case_id is required.")

    try:
        update_data = {"status": "Closed"}
        updated_case = await matcher.update_case_main_data(case_id, update_data)
        if not updated_case:
            raise HTTPException(status_code=404, detail="Case not found or not updated.")

        # Add case closure log entry
        import psycopg2
        from config import DB_CONNECTION_PARAMS

        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO case_logs (case_id, user_name, action, details, created_at)
                    VALUES (%s, %s, %s, %s, (NOW() AT TIME ZONE 'Asia/Kolkata'))
                    """,
                    (case_id, logged_in_username, "case_closed", f"Case closed by {logged_in_username}")
                )
                conn.commit()

        return {"success": True, "message": f"Case {case_id} submitted and closed."}
    except Exception as e:
        print(f"Error in submit_case: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit case.")

# NEW API ENDPOINT: Mobile Matching Cases
@router.post("/api/mobile-matching/create-cases")
async def create_mobile_matching_cases(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)]
):
    """
    Creates MM (Mobile Matching) cases by matching mobile numbers
    between customer and reverification_flags tables.
    Automatically triggered when matches are found.
    """
    try:
        result = await matcher.create_mobile_matching_cases()
        return result
    except Exception as e:
        print(f"Error in create_mobile_matching_cases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create mobile matching cases: {e}")

# NEW API ENDPOINT: Get Mobile Matching Cases
@router.get("/api/mobile-matching/cases")
async def get_mobile_matching_cases(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)],
    skip: int = Query(0),
    limit: int = Query(25)
):
    """
    Get all MM (Mobile Matching) cases with pagination.
    """
    try:
        cases_data = await matcher.fetch_new_cases_list(
            skip=skip,
            limit=limit,
            search_source_ack_no=None,
            status_filter=None,
            current_logged_in_username=logged_in_username,
            current_logged_in_user_type=None  # Will be fetched internally if needed
        )

        # Filter only MM cases
        mm_cases = [case for case in cases_data if case.get('case_type') == 'MM']

        return {
            "cases": mm_cases,
            "total_count": len(mm_cases)
        }
    except Exception as e:
        print(f"Error in get_mobile_matching_cases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch mobile matching cases: {e}")



@router.get("/api/download/{document_id}")
async def download_document(
    document_id: int,
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
):
    """Download a document by ID"""
    from fastapi.responses import FileResponse
    import os
    
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT file_location, original_filename FROM case_documents WHERE id = %s",
                    (document_id,)
                )
                doc = cur.fetchone()
                if not doc:
                    raise HTTPException(status_code=404, detail="Document not found")
                
                file_path = doc['file_location']
                if not os.path.exists(file_path):
                    raise HTTPException(status_code=404, detail="File not found")
                
                return FileResponse(
                    path=file_path,
                    filename=doc['original_filename'],
                    media_type='application/octet-stream'
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.post("/api/case-action/save")
async def save_case_action(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)],
    case_id: int = Body(...),
    case_type: str = Body(...),
    action_data: str = Body(...),  # JSON string from frontend
    files: Optional[List[UploadFile]] = None
):
    """
    Saves case action data and uploaded files. Updates case status to 'Open'.
    """
    # Parse action_data JSON
    try:
        action_data_dict = json.loads(action_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid action_data JSON: {e}")

    # Determine user's department and type for approval routing (optimized with single query)
    user_department = None
    user_type = None
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Single query to get both dept and user_type
                cur.execute("SELECT dept, user_type FROM user_table WHERE user_name = %s", (logged_in_username,))
                user_row = cur.fetchone()
                if user_row:
                    user_department = user_row.get('dept')
                    user_type = user_row.get('user_type')
    except Exception:
        user_department = None

    # Build map of file displayName -> comment from action_data for enriching file metadata
    file_comment_map = {}
    try:
        uploads = action_data_dict.get('dataUploads', []) if isinstance(action_data_dict, dict) else []
        for block in uploads:
            block_comment = block.get('comment') if isinstance(block, dict) else None
            files_in_block = block.get('files', []) if isinstance(block, dict) else []
            for f in files_in_block:
                display_name = None
                if isinstance(f, dict):
                    display_name = f.get('displayName') or f.get('name')
                if display_name:
                    file_comment_map[str(display_name)] = block_comment
    except Exception:
        file_comment_map = {}

    # --- Save files (if any) ---
    file_metadata = []
    if files:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        for upload in files:
            filename = f"{case_id}_{upload.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, "wb") as f:
                f.write(await upload.read())
            # Note: Assuming approval columns already exist (remove ALTER TABLE for performance)
            # Insert into case_documents
            try:
                with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        # Derive comment from action_data 'dataUploads' per displayName
                        derived_comment = file_comment_map.get(str(upload.filename))
                        cur.execute(
                            """
                            INSERT INTO case_documents (case_id, document_type, original_filename, file_location, file_mime_type, uploaded_by, comment, approval_status, department)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id, original_filename, file_location, file_mime_type, uploaded_at, approval_status
                            """,
                            (case_id, "BeneficiaryActionUpload", upload.filename, file_path, upload.content_type, logged_in_username, derived_comment, ('approved' if user_type in ('risk_officer','CRO') else 'draft'), user_department)
                        )
                        doc_row = cur.fetchone()
                        file_metadata.append(doc_row)
                    conn.commit()
                # Log document upload in case_logs
                try:
                    log_case_action(case_id, logged_in_username, "upload_document", f"{upload.filename} ({upload.content_type})")
                except Exception as _log_err:
                    print(f"Warning: Failed to log document upload for case {case_id}: {_log_err}")
            except Exception as e:
                print(f"Error saving file metadata for {filename}: {e}")
    # Add file metadata to action_data
    action_data_dict['uploaded_files'] = file_metadata

    # Persist fundsSaved into a dedicated table for aggregation (optional but efficient)
    try:
        funds_saved_val = action_data_dict.get('fundsSaved')
        if funds_saved_val is not None and str(funds_saved_val) != '':
            with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS case_funds_saved (
                            id SERIAL PRIMARY KEY,
                            case_id INTEGER NOT NULL,
                            funds_saved NUMERIC(18,2) NOT NULL,
                            saved_by TEXT,
                            saved_at TIMESTAMP DEFAULT NOW()
                        )
                        """
                    )
                    cur.execute(
                        """
                        INSERT INTO case_funds_saved (case_id, funds_saved, saved_by)
                        VALUES (%s, %s, %s)
                        """,
                        (case_id, funds_saved_val, logged_in_username)
                    )
                conn.commit()
    except Exception as e:
        print(f"Warning: Could not persist fundsSaved snapshot: {e}")

    # --- Insert into case_action_details ---
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Note: Assuming approval columns already exist (removed ALTER TABLE for performance)
                cur.execute(
                    """
                    INSERT INTO case_action_details (case_id, case_type, action_data, created_by, status, department)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, case_id, case_type, action_data, created_by, created_at, updated_at, status, department
                    """,
                    (case_id, case_type, json.dumps(action_data_dict, default=str), logged_in_username, ('approved' if user_type in ('risk_officer','CRO') else 'draft'), user_department)
                )
                saved_row = cur.fetchone()
            conn.commit()
    except Exception as e:
        print(f"Error saving case action data: {e}")
        raise HTTPException(status_code=500, detail="Failed to save case action data.")

    # --- Update case_main status to 'Open' if not already ---
    try:
        await matcher.update_case_main_data(case_id, {"status": "Open"})
    except Exception as e:
        print(f"Warning: Could not update case_main status to Open: {e}")

    return saved_row

@router.get("/api/case-action/latest")
async def get_latest_case_action(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)],
    case_id: int = Query(...)
):
    """
    Fetch the latest saved action data and uploaded files for a case.
    """
    from psycopg2.extras import RealDictCursor
    import psycopg2
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Determine user type
                user_type = None
                cur.execute("SELECT user_type FROM user_table WHERE user_name = %s", (logged_in_username,))
                ut = cur.fetchone()
                if ut:
                    user_type = ut.get('user_type')

                # Latest action by visibility rules (treat NULL as approved for backward compatibility)
                merged_action_data = None
                merged_from_departments = []
                if user_type in ('risk_officer', 'CRO'):
                    # Risk officers should see their own base (NULL) changes and approved changes from other departments
                    # This ensures they can see the latest approved state
                    cur.execute(
                        """
                        SELECT DISTINCT ON (COALESCE(department,'__base__'))
                               COALESCE(department,'__base__') AS dept_key,
                               action_data,
                               updated_at
                        FROM case_action_details
                        WHERE case_id = %s AND (status IS NULL OR status = 'approved')
                        ORDER BY COALESCE(department,'__base__'), updated_at DESC
                        """,
                        (case_id,)
                    )
                    dept_rows = cur.fetchall() or []
                    rows_sorted = sorted(dept_rows, key=lambda r: r.get('updated_at') or 0)
                    
                    merged = {}
                    combined_uploads = []
                    seen_block_signatures = set()
                    seen_file_names = set()
                    depts = []
                    
                    for r in rows_sorted:
                        data_obj = r.get('action_data') or {}
                        if isinstance(data_obj, dict):
                            # Merge primitive/object keys (last writer wins)
                            for k, v in data_obj.items():
                                if k == 'dataUploads' and isinstance(v, list):
                                    # Accumulate uploads from all departments
                                    for item in v:
                                        if not isinstance(item, dict):
                                            continue
                                        files = item.get('files') if isinstance(item.get('files'), list) else []
                                        # Build filenames list
                                        fnames = []
                                        for f in files:
                                            if isinstance(f, dict):
                                                name = f.get('displayName') or f.get('newName') or f.get('name')
                                                if isinstance(name, str):
                                                    fnames.append(name.strip().lower())
                                        # Deduplicate by block signature: comment + sorted filenames
                                        signature = (str(item.get('comment') or '').strip(), tuple(sorted(fnames)))
                                        if signature in seen_block_signatures:
                                            continue
                                        seen_block_signatures.add(signature)
                                        # Also skip adding files already seen across blocks (prevent triplicates)
                                        if fnames and any(n in seen_file_names for n in fnames):
                                            # If all files already seen, skip this block
                                            if all(n in seen_file_names for n in fnames):
                                                continue
                                        for n in fnames:
                                            seen_file_names.add(n)
                                        combined_uploads.append(item)
                                else:
                                    merged[k] = v
                        dk = r.get('dept_key')
                        if dk and dk not in depts:
                            depts.append(dk)
                    
                    if combined_uploads:
                        merged['dataUploads'] = combined_uploads
                    merged_action_data = merged
                    merged_from_departments = depts
                    
                    # Select the latest action row for meta/status
                    cur.execute(
                        """
                        SELECT * FROM case_action_details
                        WHERE case_id = %s AND (status IS NULL OR status = 'approved')
                        ORDER BY updated_at DESC
                        LIMIT 1
                        """,
                        (case_id,)
                    )
                elif user_type == 'supervisor':
                    # Supervisor sees pending_approval for their department or approved
                    cur.execute("SELECT dept FROM user_table WHERE user_name = %s", (logged_in_username,))
                    dept_row = cur.fetchone()
                    supervisor_dept = dept_row.get('dept') if dept_row else None
                    cur.execute(
                        """
                        SELECT * FROM case_action_details
                        WHERE case_id = %s AND (
                            (status = 'pending_approval' AND department = %s)
                            OR status IS NULL OR status = 'approved'
                        )
                        ORDER BY status = 'pending_approval' DESC, updated_at DESC
                        LIMIT 1
                        """,
                        (case_id, supervisor_dept)
                    )
                else:
                    # For 'others' (department users): always merge base (NULL) and approved items from all departments
                    # Hide pending and rejected items in the merged view
                    cur.execute(
                        """
                        SELECT DISTINCT ON (COALESCE(department,'__base__'))
                               COALESCE(department,'__base__') AS dept_key,
                               action_data,
                               updated_at
                        FROM case_action_details
                        WHERE case_id = %s AND (status IS NULL OR status = 'approved')
                        ORDER BY COALESCE(department,'__base__'), updated_at DESC
                        """,
                        (case_id,)
                    )
                    dept_rows = cur.fetchall() or []
                    rows_sorted = sorted(dept_rows, key=lambda r: r.get('updated_at') or 0)
                    merged = {}
                    combined_uploads = []
                    seen_block_signatures = set()
                    seen_file_names = set()
                    depts = []
                    for r in rows_sorted:
                        data_obj = r.get('action_data') or {}
                        if isinstance(data_obj, dict):
                            # Merge primitive/object keys (last writer wins)
                            for k, v in data_obj.items():
                                if k == 'dataUploads' and isinstance(v, list):
                                    # Accumulate uploads from all departments (base + approved)
                                    for item in v:
                                        if not isinstance(item, dict):
                                            continue
                                        files = item.get('files') if isinstance(item.get('files'), list) else []
                                        # Build filenames list
                                        fnames = []
                                        for f in files:
                                            if isinstance(f, dict):
                                                name = f.get('displayName') or f.get('newName') or f.get('name')
                                                if isinstance(name, str):
                                                    fnames.append(name.strip().lower())
                                        # Deduplicate by block signature: comment + sorted filenames
                                        signature = (str(item.get('comment') or '').strip(), tuple(sorted(fnames)))
                                        if signature in seen_block_signatures:
                                            continue
                                        seen_block_signatures.add(signature)
                                        # Also skip adding files already seen across blocks (prevent triplicates)
                                        if fnames and any(n in seen_file_names for n in fnames):
                                            if all(n in seen_file_names for n in fnames):
                                                continue
                                        for n in fnames:
                                            seen_file_names.add(n)
                                        combined_uploads.append(item)
                                else:
                                    merged[k] = v
                        dk = r.get('dept_key')
                        if dk and dk not in depts:
                            depts.append(dk)
                    if combined_uploads:
                        merged['dataUploads'] = combined_uploads
                    merged_action_data = merged
                    merged_from_departments = depts
                    # still select a single latest row for meta/status
                    cur.execute(
                        """
                        SELECT * FROM case_action_details
                        WHERE case_id = %s AND (status IS NULL OR status = 'approved')
                        ORDER BY updated_at DESC
                        LIMIT 1
                        """,
                        (case_id,)
                    )
                action_row = cur.fetchone()
                # Note: Do NOT return early; still fetch files even if no visible action record

                # Fetch files with visibility rules
                if user_type in ('risk_officer', 'CRO'):
                    # Risk officer should always see base (NULL) and supervisor-approved documents; hide only pending/rejected
                    cur.execute(
                        """
                        SELECT id, original_filename, file_location, file_mime_type, uploaded_at, comment, approval_status, uploaded_by, department
                        FROM case_documents
                        WHERE case_id = %s AND (approval_status IS NULL OR approval_status = 'approved')
                        ORDER BY uploaded_at DESC
                        """,
                        (case_id,)
                    )
                elif user_type == 'supervisor':
                    cur.execute("SELECT dept FROM user_table WHERE user_name = %s", (logged_in_username,))
                    dept_row2 = cur.fetchone()
                    supervisor_dept2 = dept_row2.get('dept') if dept_row2 else None
                    cur.execute(
                        """
                        SELECT id, original_filename, file_location, file_mime_type, uploaded_at, comment, approval_status, uploaded_by, department
                        FROM case_documents
                        WHERE case_id = %s AND (
                            approval_status = 'approved'
                            OR approval_status IS NULL
                            OR (approval_status = 'pending_approval' AND department = %s)
                        )
                        ORDER BY uploaded_at DESC
                        """,
                        (case_id, supervisor_dept2)
                    )
                else:
                    # Others: show base (NULL) and approved documents across departments; exclude pending/rejected.
                    # Allow the current user to see their own drafts (NULL) while editing.
                    cur.execute(
                        """
                        SELECT id, original_filename, file_location, file_mime_type, uploaded_at, comment, approval_status, uploaded_by, department
                        FROM case_documents
                        WHERE case_id = %s AND (
                            approval_status IS NULL
                            OR approval_status = 'approved'
                            OR (uploaded_by = %s AND approval_status IS NULL)
                        )
                        ORDER BY uploaded_at DESC
                        """,
                        (case_id, logged_in_username)
                    )
                files = cur.fetchall()
    except Exception as e:
        print(f"Error fetching latest case action data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch case action data.")
    payload = {"action_data": action_row, "files": files}
    if merged_action_data is not None:
        payload["merged_action_data"] = merged_action_data
        payload["merged_from_departments"] = merged_from_departments
    return payload

@router.get("/api/assigned-cases")
async def get_assigned_cases(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)],
    skip: int = Query(0),
    limit: int = Query(25),
    search_source_ack_no: Optional[str] = Query(None, description="Search by Source Acknowledgement Number"),
    status_filter: Optional[str] = Query(None, description="Filter by case status")
) -> Dict[str, Any]:
    """
    Get cases that have been assigned by the current user (for review purposes)
    """
    try:
        cases_data = await matcher.fetch_assigned_cases(
            skip=skip,
            limit=limit,
            search_source_ack_no=search_source_ack_no,
            status_filter=status_filter,
            assigned_by_username=logged_in_username
        )
        
        return {
            "cases": cases_data,
            "total_count": len(cases_data)  # For now, return count of current page
        }
    except Exception as e:
        print(f"[DEBUG] Error in get_assigned_cases: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch assigned cases. Error: {e}")