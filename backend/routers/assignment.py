# routers/assignment.py
import psycopg2
from typing import Annotated, Dict, Any, Optional
import traceback
import time
from fastapi import APIRouter, HTTPException, Depends, Request, Body
from concurrent.futures import ThreadPoolExecutor

from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
#from keycloak import KeycloakOpenID
from keycloak.keycloak_openid import KeycloakOpenID

from db.matcher import CaseEntryMatcher, save_or_update_decision, log_case_action # Also need save_or_update_decision here
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
        print(f"UNEXPECTED ERROR in get_current_username: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)

@router.post("/api/case/{ack_no}/assign")
async def assign_case_api(
    ack_no: str,
    assigned_to_employee: Annotated[str, Body(..., embed=True, description="Username of the employee to assign the case to")],
    assigner_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)],
    comment: Annotated[Optional[str], Body(..., embed=True, description="Comment for the assignment")] = None,
    template_id: Annotated[Optional[int], Body(..., embed=True, description="Optional template ID for template-based assignment")] = None
) -> Dict[str, Any]:
    """
    Assign a case to an employee with optional comment and template
    """
    import psycopg2
    from config import DB_CONNECTION_PARAMS
    import time
    
    try:
        # Get case_id from ack_no
        case_id = await matcher.get_case_id_from_ack_no(ack_no) if hasattr(matcher, 'get_case_id_from_ack_no') else None
        if not case_id:
            raise HTTPException(status_code=404, detail=f"Case with ack_no {ack_no} not found.")
        
        # Update assignment table - allow multiple assignments per case
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Ensure columns exist
                try:
                    cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
                    cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS assignment_type VARCHAR(50) DEFAULT 'manual'")
                    cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS comment TEXT")
                    cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS template_id INTEGER")
                except Exception:
                    pass
                
                # Insert assignment with template if provided
                cur.execute(
                    """
                    INSERT INTO assignment (case_id, assigned_to, assigned_by, comment, is_active, assignment_type, template_id)
                    VALUES (%s, %s, %s, %s, TRUE, %s, %s)
                    """,
                    (case_id, assigned_to_employee, assigner_username, comment, 'template' if template_id else 'manual', template_id)
                )
            conn.commit()
        
        # Fetch template name once if template_id exists
        template_name = None
        if template_id:
            try:
                with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT name FROM templates WHERE id = %s", (template_id,))
                        template_row = cur.fetchone()
                        if template_row:
                            template_name = template_row[0]
            except Exception as e:
                print(f"Error fetching template name: {e}", flush=True)
        
        # Log the assignment action with comment and template info
        log_details = f"Assigned to {assigned_to_employee}"
        if comment:
            log_details += f" - Comment: {comment}"
        if template_id:
            if template_name:
                log_details += f" - Template: {template_name}"
            else:
                log_details += f" - Template ID: {template_id}"  # Fallback if template not found
        log_case_action(case_id, assigner_username, "assign", log_details)
        
        # Update decision table
        decision_update_payload = {
            "assignedEmployee": assigned_to_employee,
            "decisionAction": "Assigned",
            "comments": comment or f"Case assigned by {assigner_username}.",
            "auditTrail": f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} - Assigned by {assigner_username} to {assigned_to_employee}"
        }
        if template_id:
            decision_update_payload["templateId"] = template_id
            if template_name:
                decision_update_payload["auditTrail"] += f" with template '{template_name}'"
            else:
                decision_update_payload["auditTrail"] += f" with template {template_id}"
        
        updated_decision_record = await save_or_update_decision(executor, case_id, decision_update_payload)
        
        return {
            "success": True,
            "message": f"Case {ack_no} assigned to {assigned_to_employee} successfully.",
            "case_id": case_id,
            "assigned_to": assigned_to_employee,
            "assigned_by": assigner_username,
            "comment": comment,
            "template_id": template_id
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error in assign_case_api for case {ack_no}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to assign case. Error: {e}")

@router.post("/api/case/{ack_no}/send-back")
async def send_back_case_api(
    ack_no: str,
    comment: Annotated[str, Body(..., embed=True, description="Comment from 'others' user")],
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    reason_id: Annotated[Optional[int], Body(embed=True, description="Optional send back analysis reason id")] = None,
) -> Dict[str, Any]:
    """
    Handles 'send back' from 'others' user: reassigns to previous risk_officer and logs the comment.
    """
    import psycopg2
    from config import DB_CONNECTION_PARAMS
    try:
        # Get case_id from ack_no
        case_id = await matcher.get_case_id_from_ack_no(ack_no) if hasattr(matcher, 'get_case_id_from_ack_no') else None
        if not case_id:
            raise HTTPException(status_code=404, detail=f"Case with ack_no {ack_no} not found.")
        # Find who originally assigned to this user (risk officer)
        previous_risk_officer = None
        user_department = None
        supervisor_username = None
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Identify assigning risk officer
                cur.execute("SELECT assigned_by FROM assignment WHERE case_id = %s AND assigned_to = %s ORDER BY assign_date DESC, assign_time DESC LIMIT 1", (case_id, current_username))
                row = cur.fetchone()
                if row and row[0]:
                    previous_risk_officer = row[0]
                if not previous_risk_officer:
                    raise HTTPException(status_code=400, detail="No previous risk_officer found for this case.")

                # Determine current user's department
                cur.execute("SELECT dept FROM user_table WHERE user_name = %s", (current_username,))
                dept_row = cur.fetchone()
                user_department = dept_row[0] if dept_row and dept_row[0] else None
                if not user_department:
                    raise HTTPException(status_code=400, detail="Department not set for current user.")

                # Find supervisor for this department
                cur.execute("SELECT user_name FROM user_table WHERE user_type = 'supervisor' AND dept = %s ORDER BY user_id LIMIT 1", (user_department,))
                sup_row = cur.fetchone()
                supervisor_username = sup_row[0] if sup_row else None
                if not supervisor_username:
                    raise HTTPException(status_code=400, detail=f"No supervisor found for department {user_department}.")

                # Ensure new columns exist for approvals (idempotent)
                try:
                    cur.execute("ALTER TABLE case_documents ADD COLUMN IF NOT EXISTS approval_status TEXT")
                    cur.execute("ALTER TABLE case_documents ADD COLUMN IF NOT EXISTS department TEXT")
                except Exception:
                    pass
                try:
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS status TEXT")
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS department TEXT")
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS approved_by TEXT")
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP")
                except Exception:
                    pass

                # Mark current user's drafts as pending_approval for this department
                cur.execute(
                    """
                    UPDATE case_action_details
                    SET status = 'pending_approval', department = %s, updated_at = NOW()
                    WHERE case_id = %s AND created_by = %s AND (status IS NULL OR status IN ('draft','open'))
                    """,
                    (user_department, case_id, current_username)
                )
                cur.execute(
                    """
                    UPDATE case_documents
                    SET approval_status = 'pending_approval', department = %s
                    WHERE case_id = %s AND uploaded_by = %s AND (approval_status IS NULL OR approval_status = 'draft')
                    """,
                    (user_department, case_id, current_username)
                )

                # Mark template responses as pending approval
                try:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS template_responses (
                            id SERIAL PRIMARY KEY,
                            case_id INTEGER NOT NULL REFERENCES case_main(case_id) ON DELETE CASCADE,
                            template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
                            assigned_to VARCHAR(50) NOT NULL,
                            responses JSONB NOT NULL,
                            status VARCHAR(50) DEFAULT 'pending_approval',
                            department VARCHAR(100),
                            approved_by VARCHAR(50),
                            approved_at TIMESTAMP,
                            rejection_reason TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    cur.execute(
                        """
                        UPDATE template_responses
                        SET status = 'pending_approval', department = %s
                        WHERE case_id = %s AND assigned_to = %s AND (status IS NULL OR status = 'draft')
                        """,
                        (user_department, case_id, current_username)
                    )
                except Exception:
                    pass

                # If a reason_id was provided, attach the reason text into the assignment comment & logs
                reason_text = None
                if reason_id is not None:
                    try:
                        cur.execute("SELECT reason FROM send_back_analysis WHERE id = %s", (reason_id,))
                        r = cur.fetchone()
                        if r and r[0]:
                            reason_text = r[0]
                    except Exception:
                        reason_text = None

                # Ensure is_active column exists
                try:
                    cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
                except Exception:
                    pass

                # Reassign this specific assignment row to supervisor for approval (keep active)
                appended_comment = ' | Pending approval by supervisor'
                if reason_text:
                    appended_comment += f" | Reason: {reason_text}"
                cur.execute(
                    """
                    UPDATE assignment
                    SET assigned_to = %s, comment = COALESCE(comment,'') || %s, is_active = TRUE
                    WHERE case_id = %s AND assigned_to = %s
                    """,
                    (supervisor_username, appended_comment, case_id, current_username)
                )
            conn.commit()

        # Log the send back action and routing to supervisor (include reason text if available)
        details_str = f"Dept: {user_department}, Supervisor: {supervisor_username}. Comment: {comment}"
        if reason_id is not None:
            try:
                # Prefer logging the reason text; fall back to id if not resolvable
                if 'reason_text' in locals() and reason_text:
                    details_str += f" | Reason: {reason_text}"
                else:
                    details_str += f" | ReasonId: {reason_id}"
            except Exception:
                details_str += f" | ReasonId: {reason_id}"
        log_case_action(case_id, current_username, "send_back_to_supervisor", details_str)
        return {"success": True, "message": f"Case {ack_no} sent to {supervisor_username} (supervisor) for approval."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error in send_back_case_api for case {ack_no}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to send back case. Error: {e}")


@router.post("/api/case/{ack_no}/approve-dept")
async def approve_department_changes_api(
    ack_no: str,
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    approval_comment: Annotated[str, Body(..., embed=True, description="Approval comment from supervisor")]
) -> Dict[str, Any]:
    """
    Supervisor approves pending changes for their department; case routes back to the risk officer who assigned it.
    """
    import psycopg2
    try:
        # Validate approval comment
        if not approval_comment or not approval_comment.strip():
            raise HTTPException(
                status_code=400,
                detail="Approval comment is required."
            )
        
        case_id = await matcher.get_case_id_from_ack_no(ack_no)
        if not case_id:
            raise HTTPException(status_code=404, detail=f"Case with ack_no {ack_no} not found.")

        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Determine supervisor's department
                cur.execute("SELECT dept FROM user_table WHERE user_name = %s", (current_username,))
                dept_row = cur.fetchone()
                supervisor_dept = dept_row[0] if dept_row and dept_row[0] else None
                if not supervisor_dept:
                    raise HTTPException(status_code=400, detail="Supervisor department not set.")

                # Approve pending action details and documents for this department
                # Ensure columns
                try:
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS status TEXT")
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS department TEXT")
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS approved_by TEXT")
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP")
                except Exception:
                    pass
                try:
                    cur.execute("ALTER TABLE case_documents ADD COLUMN IF NOT EXISTS approval_status TEXT")
                    cur.execute("ALTER TABLE case_documents ADD COLUMN IF NOT EXISTS department TEXT")
                except Exception:
                    pass

                cur.execute(
                    """
                    UPDATE case_action_details
                    SET status = 'approved', approved_by = %s, approved_at = NOW()
                    WHERE case_id = %s AND department = %s AND status = 'pending_approval'
                    """,
                    (current_username, case_id, supervisor_dept)
                )
                cur.execute(
                    """
                    UPDATE case_documents
                    SET approval_status = 'approved'
                    WHERE case_id = %s AND department = %s AND approval_status = 'pending_approval'
                    """,
                    (case_id, supervisor_dept)
                )

                # Approve pending template responses for this department
                try:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS template_responses (
                            id SERIAL PRIMARY KEY,
                            case_id INTEGER NOT NULL REFERENCES case_main(case_id) ON DELETE CASCADE,
                            template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
                            assigned_to VARCHAR(50) NOT NULL,
                            responses JSONB NOT NULL,
                            status VARCHAR(50) DEFAULT 'pending_approval',
                            department VARCHAR(100),
                            approved_by VARCHAR(50),
                            approved_at TIMESTAMP,
                            rejection_reason TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    cur.execute(
                        """
                        UPDATE template_responses
                        SET status = 'approved', approved_by = %s, approved_at = NOW()
                        WHERE case_id = %s AND department = %s AND status = 'pending_approval'
                        """,
                        (current_username, case_id, supervisor_dept)
                    )
                except Exception:
                    pass

                # Route assignment back to the original risk officer (assigned_by of this approval thread)
                previous_risk_officer = None
                cur.execute(
                    """
                    SELECT assigned_by FROM assignment
                    WHERE case_id = %s AND assigned_to = %s
                    ORDER BY assign_date DESC, assign_time DESC LIMIT 1
                    """,
                    (case_id, current_username)
                )
                row = cur.fetchone()
                if row and row[0]:
                    previous_risk_officer = row[0]
                if previous_risk_officer:
                    cur.execute(
                        """
                        UPDATE assignment
                        SET assigned_to = %s, comment = COALESCE(comment,'') || %s
                        WHERE case_id = %s AND assigned_to = %s
                        """,
                        (previous_risk_officer, ' | Approved by supervisor and routed back', case_id, current_username)
                    )
                    # Mark the routed-back row inactive
                    try:
                        cur.execute(
                            """
                            UPDATE assignment SET is_active = FALSE
                            WHERE case_id = %s AND assigned_to = %s
                            """,
                            (case_id, previous_risk_officer)
                        )
                    except Exception:
                        pass
            conn.commit()

        log_case_action(case_id, current_username, "approve_changes", f"Dept: {supervisor_dept}. Comment: {approval_comment.strip()}")
        return {"success": True, "message": f"Approved pending changes for {supervisor_dept} and routed back to risk officer."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error in approve_department_changes_api for case {ack_no}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to approve changes. Error: {e}")


@router.post("/api/case/{ack_no}/reject-dept")
async def reject_department_changes_api(
    ack_no: str,
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    rejection_reason: Annotated[str, Body(..., embed=True, description="Reason for rejection")],
) -> Dict[str, Any]:
    """
    Supervisor rejects pending changes for their department; changes are hidden and case routes back to the risk officer.
    """
    import psycopg2
    try:
        # Validate rejection reason
        if not rejection_reason or not rejection_reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required."
            )
        
        case_id = await matcher.get_case_id_from_ack_no(ack_no)
        if not case_id:
            raise HTTPException(status_code=404, detail=f"Case with ack_no {ack_no} not found.")

        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Determine supervisor's department
                cur.execute("SELECT dept FROM user_table WHERE user_name = %s", (current_username,))
                dept_row = cur.fetchone()
                supervisor_dept = dept_row[0] if dept_row and dept_row[0] else None
                if not supervisor_dept:
                    raise HTTPException(status_code=400, detail="Supervisor department not set.")

                # Ensure columns
                try:
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS status TEXT")
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS department TEXT")
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS approved_by TEXT")
                    cur.execute("ALTER TABLE case_action_details ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP")
                except Exception:
                    pass
                try:
                    cur.execute("ALTER TABLE case_documents ADD COLUMN IF NOT EXISTS approval_status TEXT")
                    cur.execute("ALTER TABLE case_documents ADD COLUMN IF NOT EXISTS department TEXT")
                except Exception:
                    pass

                # Mark as rejected
                cur.execute(
                    """
                    UPDATE case_action_details
                    SET status = 'rejected', approved_by = %s, approved_at = NOW()
                    WHERE case_id = %s AND department = %s AND status = 'pending_approval'
                    """,
                    (current_username, case_id, supervisor_dept)
                )
                cur.execute(
                    """
                    UPDATE case_documents
                    SET approval_status = 'rejected'
                    WHERE case_id = %s AND department = %s AND approval_status = 'pending_approval'
                    """,
                    (case_id, supervisor_dept)
                )

                # Reject pending template responses for this department
                try:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS template_responses (
                            id SERIAL PRIMARY KEY,
                            case_id INTEGER NOT NULL REFERENCES case_main(case_id) ON DELETE CASCADE,
                            template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
                            assigned_to VARCHAR(50) NOT NULL,
                            responses JSONB NOT NULL,
                            status VARCHAR(50) DEFAULT 'pending_approval',
                            department VARCHAR(100),
                            approved_by VARCHAR(50),
                            approved_at TIMESTAMP,
                            rejection_reason TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    cur.execute(
                        """
                        UPDATE template_responses
                        SET status = 'rejected', approved_by = %s, approved_at = NOW(), rejection_reason = %s
                        WHERE case_id = %s AND department = %s AND status = 'pending_approval'
                        """,
                        (current_username, rejection_reason or 'Rejected by supervisor', case_id, supervisor_dept)
                    )
                except Exception:
                    pass

                # Route back to the department user (the one who initially sent back)
                dept_employee_username = None
                try:
                    cur.execute(
                        """
                        SELECT created_by FROM case_action_details
                        WHERE case_id = %s AND department = %s
                        ORDER BY updated_at DESC
                        LIMIT 1
                        """,
                        (case_id, supervisor_dept)
                    )
                    created_by_row = cur.fetchone()
                    if created_by_row and created_by_row[0]:
                        dept_employee_username = created_by_row[0]
                except Exception:
                    dept_employee_username = None

                if not dept_employee_username:
                    # Fallback: find most recent assignment in this case to a user in the same department (excluding supervisor)
                    try:
                        cur.execute(
                            """
                            SELECT a.assigned_to
                            FROM assignment a
                            JOIN user_table u ON u.user_name = a.assigned_to
                            WHERE a.case_id = %s AND u.dept = %s AND a.assigned_to <> %s
                            ORDER BY a.assign_date DESC, a.assign_time DESC
                            LIMIT 1
                            """,
                            (case_id, supervisor_dept, current_username)
                        )
                        row2 = cur.fetchone()
                        if row2 and row2[0]:
                            dept_employee_username = row2[0]
                    except Exception:
                        dept_employee_username = None

                if dept_employee_username:
                    cur.execute(
                        """
                        UPDATE assignment
                        SET assigned_to = %s, comment = COALESCE(comment,'') || %s, is_active = TRUE
                        WHERE case_id = %s AND assigned_to = %s
                        """,
                        (dept_employee_username, ' | Rejected by supervisor. Please revise and Send Back.', case_id, current_username)
                    )
            conn.commit()

        log_case_action(case_id, current_username, "reject_changes", f"Dept: {supervisor_dept}. Reason: {rejection_reason or 'N/A'}")
        return {"success": True, "message": f"Rejected pending changes for {supervisor_dept} and routed back to the department user for revision."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error in reject_department_changes_api for case {ack_no}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to reject changes. Error: {e}")

@router.post("/api/case/{ack_no}/revoke-assignment")
async def revoke_assignment_api(
    ack_no: str,
    assigned_to_employee: Annotated[str, Body(..., embed=True, description="Username of the employee to revoke assignment from")],
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
) -> Dict[str, Any]:
    """
    Revoke assignment from a specific employee
    """
    import psycopg2
    from config import DB_CONNECTION_PARAMS
    
    try:
        # Get case_id from ack_no
        case_id = await matcher.get_case_id_from_ack_no(ack_no) if hasattr(matcher, 'get_case_id_from_ack_no') else None
        if not case_id:
            raise HTTPException(status_code=404, detail=f"Case with ack_no {ack_no} not found.")
        
        # Check if the current user is the one who assigned the case
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT assigned_by FROM assignment WHERE case_id = %s AND assigned_to = %s",
                    (case_id, assigned_to_employee)
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail=f"No assignment found for case {ack_no} to {assigned_to_employee}")
                
                if row[0] != current_username:
                    raise HTTPException(status_code=403, detail="You can only revoke assignments you made")
                
                # Delete the specific assignment
                cur.execute(
                    "DELETE FROM assignment WHERE case_id = %s AND assigned_to = %s",
                    (case_id, assigned_to_employee)
                )
            conn.commit()
        
        # Log the revoke action
        log_case_action(case_id, current_username, "revoke_assignment", f"Revoked assignment from {assigned_to_employee}")
        
        return {
            "success": True,
            "message": f"Assignment revoked from {assigned_to_employee} successfully.",
            "case_id": case_id,
            "revoked_from": assigned_to_employee,
            "revoked_by": current_username
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error in revoke_assignment_api for case {ack_no}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to revoke assignment. Error: {e}")

@router.get("/api/case/{case_id}/logs")
async def get_case_logs(
    case_id: int,
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
):
    """
    Get case logs. Access control:
    - Super_user can access logs for any case
    - Risk officers can access logs for cases they've been assigned to, have interacted with, or unassigned cases
    - Other users can access logs for cases they've been assigned to or have interacted with
    """
    import psycopg2
    from config import DB_CONNECTION_PARAMS
    
    try:
        # Check if user is super_user
        user_type = await matcher.fetch_user_type(current_username)
        
        # If not super_user, check if they have access to this case
        if user_type != 'super_user':
            with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
                with conn.cursor() as cur:
                    # Check multiple access conditions
                    has_access = False
                    access_reason = ""
                    
                    # 1. Check if user has been assigned to this case
                    cur.execute(
                        """
                        SELECT COUNT(*) FROM assignment 
                        WHERE case_id = %s AND assigned_to = %s AND COALESCE(is_active, TRUE) = TRUE
                        """,
                        (case_id, current_username)
                    )
                    is_assigned = cur.fetchone()[0] > 0
                    
                    # 2. Check if user has interacted with this case (created logs)
                    cur.execute(
                        """
                        SELECT COUNT(*) FROM case_logs 
                        WHERE case_id = %s AND user_name = %s
                        """,
                        (case_id, current_username)
                    )
                    has_interacted = cur.fetchone()[0] > 0
                    
                    # 3. For risk officers, also allow access to unassigned cases
                    can_access_unassigned = False
                    if user_type == 'risk_officer':
                        cur.execute(
                            """
                            SELECT COUNT(*) FROM assignment 
                            WHERE case_id = %s AND COALESCE(is_active, TRUE) = TRUE
                            """,
                            (case_id,)
                        )
                        no_active_assignments = cur.fetchone()[0] == 0
                        can_access_unassigned = no_active_assignments
                    
                    # Determine access
                    if is_assigned:
                        has_access = True
                        access_reason = "assigned to case"
                    elif has_interacted:
                        has_access = True
                        access_reason = "previously interacted with case"
                    elif can_access_unassigned:
                        has_access = True
                        access_reason = "unassigned case accessible to risk officers"
                    
                    if not has_access:
                        raise HTTPException(
                            status_code=403, 
                            detail="Access denied. You can only view logs for cases you've been assigned to, have interacted with, or unassigned cases (if you're a risk officer)."
                        )
                    
                    print(f"DEBUG: User {current_username} accessing case {case_id} logs - {access_reason}", flush=True)
        
        # Fetch case logs
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_name, action, details, created_at
                    FROM case_logs
                    WHERE case_id = %s
                    ORDER BY created_at ASC
                    """,
                    (case_id,)
                )
                logs = [
                    {
                        "id": row[0],
                        "user_name": row[1],
                        "action": row[2],
                        "details": row[3],
                        "created_at": row[4].isoformat() if row[4] else None
                    }
                    for row in cur.fetchall()
                ]
        return {"logs": logs}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching logs for case {case_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch case logs.")

@router.get("/api/case/{case_id}/assignments")
async def get_case_assignments(
    case_id: int,
    current_username: Annotated[str, Depends(get_current_username)]
):
    """
    Get all assignments for a specific case, excluding assignments where the current user is the assigned_to
    (which happens when cases are sent back to the original risk officer)
    """
    import psycopg2
    from config import DB_CONNECTION_PARAMS
    
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Ensure template_id column exists
                try:
                    cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS template_id INTEGER REFERENCES templates(id) ON DELETE SET NULL")
                except Exception:
                    pass
                
                cur.execute(
                    """
                    SELECT 
                        assigned_to,
                        assigned_by,
                        assign_date,
                        assign_time,
                        comment,
                        template_id
                    FROM assignment 
                    WHERE case_id = %s AND assigned_to != %s
                    ORDER BY assign_date DESC, assign_time DESC
                    """,
                    (case_id, current_username)
                )
                rows = cur.fetchall()
                
                assignments = []
                for row in rows:
                    assignment = {
                        "assigned_to": row[0],
                        "assigned_by": row[1],
                        "assign_date": row[2],
                        "assign_time": row[3],
                        "comment": row[4] if len(row) > 4 else None,
                        "template_id": row[5] if len(row) > 5 else None,
                        "sent_back": False  # This would need to be determined by checking case_logs
                    }
                    assignments.append(assignment)
                
                # Check which assignments have been sent back and if they're still pending
                for assignment in assignments:
                    # Check if user has sent back to supervisor
                    cur.execute(
                        """
                        SELECT COUNT(*) FROM case_logs 
                        WHERE case_id = %s AND user_name = %s AND action = 'send_back_to_supervisor'
                        """,
                        (case_id, assignment["assigned_to"])
                    )
                    sent_back_count = cur.fetchone()[0]
                    
                    if sent_back_count > 0:
                        # Check if there's a subsequent approve_changes or reject_changes action
                        # that would indicate the case is no longer pending
                        cur.execute(
                            """
                            SELECT COUNT(*) FROM case_logs 
                            WHERE case_id = %s 
                            AND action IN ('approve_changes', 'reject_changes')
                            AND created_at > (
                                SELECT MAX(created_at) FROM case_logs 
                                WHERE case_id = %s AND user_name = %s AND action = 'send_back_to_supervisor'
                            )
                            """,
                            (case_id, case_id, assignment["assigned_to"])
                        )
                        resolved_count = cur.fetchone()[0]
                        # Case is sent back but still pending if no subsequent approval/rejection
                        assignment["sent_back"] = resolved_count == 0
                    else:
                        assignment["sent_back"] = False
                
                return {"assignments": assignments}
    except Exception as e:
        print(f"[DEBUG] Error in get_case_assignments for case {case_id}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get case assignments. Error: {e}")

@router.get("/api/case/{case_id}/my-assignment")
async def get_my_case_assignment(
    case_id: int,
    current_username: Annotated[str, Depends(get_current_username)]
):
    """
    Get the current user's assignment for a specific case, including template information
    """
    import psycopg2
    from config import DB_CONNECTION_PARAMS
    
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                # Ensure template_id column exists
                try:
                    cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS template_id INTEGER")
                except Exception:
                    pass
                
                cur.execute(
                    """
                    SELECT 
                        assigned_to,
                        assigned_by,
                        assign_date,
                        assign_time,
                        comment,
                        template_id
                    FROM assignment 
                    WHERE case_id = %s AND assigned_to = %s
                    ORDER BY assign_date DESC, assign_time DESC
                    LIMIT 1
                    """,
                    (case_id, current_username)
                )
                row = cur.fetchone()
                
                if not row:
                    return {"assignment": None}
                
                assignment = {
                    "assigned_to": row[0],
                    "assigned_by": row[1],
                    "assign_date": row[2],
                    "assign_time": row[3],
                    "comment": row[4] if len(row) > 4 else None,
                    "template_id": row[5] if len(row) > 5 else None
                }
                
                return {"assignment": assignment}
    except Exception as e:
        print(f"[DEBUG] Error in get_my_case_assignment for case {case_id}: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get my case assignment. Error: {e}")

@router.post("/api/case/bulk-close")
async def bulk_close_cases_api(
    case_ids: Annotated[list[int], Body(..., embed=True, description="List of case IDs to close")],
    closure_data: Annotated[dict, Body(..., embed=True, description="Closure data including reason and confirmation details")],
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> Dict[str, Any]:
    """
    Bulk close multiple cases with closure data
    """
    try:
        if not case_ids or len(case_ids) == 0:
            raise HTTPException(status_code=400, detail="No case IDs provided")
        
        closed_cases = []
        failed_cases = []
        
        for case_id in case_ids:
            try:
                # Check if case exists and get current status
                with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
                    with conn.cursor() as cur:
                        # First check if case exists and get current status
                        cur.execute(
                            """
                            SELECT status FROM case_main 
                            WHERE case_id = %s
                            """,
                            (case_id,)
                        )
                        
                        result = cur.fetchone()
                        if not result:
                            failed_cases.append({"case_id": case_id, "error": "Case not found"})
                            continue
                        
                        current_status = result[0]
                        
                        # Check if case is already closed
                        if current_status == 'Closed':
                            failed_cases.append({"case_id": case_id, "error": "Case is already closed"})
                            continue
                        
                        # Note: VM cases can be closed but not assigned, so no restriction here
                        
                        # Note: We don't update status here anymore - let save_or_update_decision handle it
                        # The status will be updated when we call save_or_update_decision with "decisionAction": "Closed"
                        
                        # Insert closure decision
                        decision_update_payload = {
                            "closureLOV": closure_data.get("closureLOV", ""),
                            "closureRemarks": closure_data.get("closureRemarks", ""),
                            "confirmedMule": closure_data.get("confirmedMule", "No"),
                            "fundsSaved": closure_data.get("fundsSaved"),
                            "digitalBlocked": closure_data.get("digitalBlocked", "No"),
                            "accountBlocked": closure_data.get("accountBlocked", "No"),
                            "decisionAction": "Closed",
                            "comments": f"Case closed by {current_username}",
                            "auditTrail": f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} - Closed by {current_username}"
                        }
                        
                        await save_or_update_decision(executor, case_id, decision_update_payload)
                        
                        # Log the closure action
                        log_details = f"Case closed - Reason: {closure_data.get('closureLOV', 'N/A')}"
                        if closure_data.get('closureRemarks'):
                            log_details += f" - Remarks: {closure_data.get('closureRemarks')}"
                        log_case_action(case_id, current_username, "close", log_details)
                        
                        closed_cases.append(case_id)
                        
                    conn.commit()
                    
            except Exception as e:
                print(f"[DEBUG] Error closing case {case_id}: {e}", flush=True)
                failed_cases.append({"case_id": case_id, "error": str(e)})
        
        return {
            "message": f"Bulk close operation completed",
            "closed_cases": closed_cases,
            "failed_cases": failed_cases,
            "total_processed": len(case_ids),
            "successful_closes": len(closed_cases),
            "failed_closes": len(failed_cases),
            "closed_by": current_username,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        }
        
    except Exception as e:
        print(f"[DEBUG] Error in bulk_close_cases_api: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to bulk close cases. Error: {e}")

@router.post("/api/case/bulk-assign")
async def bulk_assign_cases_api(
    assignments: Annotated[list[dict], Body(..., embed=True, description="List of assignments with case_id, assigned_to, and comment")],
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> Dict[str, Any]:
    """
    Bulk assign multiple cases to users
    """
    try:
        if not assignments or len(assignments) == 0:
            raise HTTPException(status_code=400, detail="No assignments provided")
        
        successful_assignments = []
        failed_assignments = []
        
        for assignment in assignments:
            try:
                case_id = assignment.get("case_id")
                assigned_to = assignment.get("assigned_to")
                comment = assignment.get("comment", "")
                
                if not case_id or not assigned_to:
                    failed_assignments.append({
                        "case_id": case_id,
                        "assigned_to": assigned_to,
                        "error": "Missing case_id or assigned_to"
                    })
                    continue
                
                # Get case details and check status
                case_details = await matcher.fetch_single_case_details_from_case_main_by_case_id(case_id)
                if not case_details or not case_details.get("source_ack_no"):
                    failed_assignments.append({
                        "case_id": case_id,
                        "assigned_to": assigned_to,
                        "error": "Case not found or missing ACK number"
                    })
                    continue
                
                # Check if case is already closed
                if case_details.get("status") == "Closed":
                    failed_assignments.append({
                        "case_id": case_id,
                        "assigned_to": assigned_to,
                        "error": "Cannot assign a closed case"
                    })
                    continue
                

                
                ack_no = case_details["source_ack_no"]
                
                # Create assignment record
                with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO assignment (case_id, assigned_to, assigned_by, comment)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (case_id, assigned_to, current_username, comment)
                        )
                    conn.commit()
                
                # Log the assignment action
                log_details = f"Assigned to {assigned_to}"
                if comment:
                    log_details += f" - Comment: {comment}"
                log_case_action(case_id, current_username, "assign", log_details)
                
                # Update decision table
                decision_update_payload = {
                    "assignedEmployee": assigned_to,
                    "decisionAction": "Assigned",
                    "comments": comment or f"Case assigned by {current_username}.",
                    "auditTrail": f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} - Assigned by {current_username} to {assigned_to}"
                }
                await save_or_update_decision(executor, case_id, decision_update_payload)
                
                successful_assignments.append({
                    "case_id": case_id,
                    "ack_no": ack_no,
                    "assigned_to": assigned_to,
                    "comment": comment
                })
                
            except Exception as e:
                print(f"[DEBUG] Error assigning case {assignment.get('case_id')}: {e}", flush=True)
                failed_assignments.append({
                    "case_id": assignment.get("case_id"),
                    "assigned_to": assignment.get("assigned_to"),
                    "error": str(e)
                })
        
        return {
            "message": f"Bulk assignment operation completed",
            "successful_assignments": successful_assignments,
            "failed_assignments": failed_assignments,
            "total_processed": len(assignments),
            "successful_assigns": len(successful_assignments),
            "failed_assigns": len(failed_assignments),
            "assigned_by": current_username,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        }
        
    except Exception as e:
        print(f"[DEBUG] Error in bulk_assign_cases_api: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to bulk assign cases. Error: {e}")
