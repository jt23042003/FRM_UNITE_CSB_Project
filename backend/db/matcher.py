# db/matcher.py
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime, time, timedelta # Added datetime, time for new table defaults
from typing import Dict, Any, List, Optional, Union, Annotated
import json
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
import random
import uuid
import re
import asyncpg
import os
from .connection import get_db_connection, get_db_cursor
# Ensure all necessary models are imported from base_models.py
from models.base_models import CaseEntryData, I4CData, TransactionData, BeneficiaryData, PotentialSuspectAccountData, CaseMainUpdateData, ECBCaseData, NewCustomerRequest
from config import DB_CONNECTION_PARAMS
# COMMENTED OUT: Complex assignment service import
# from services.case_assignment_service import CaseAssignmentService

from fastapi import UploadFile

# Add caching for performance optimization
import time as time_module

class CaseNotFoundError(Exception):
    pass

# Global cache for user types and frequently accessed data
USER_TYPE_CACHE = {}
CACHE_EXPIRY_SECONDS = 300  # 5 minutes

def is_cache_valid(timestamp):
    return (time_module.time() - timestamp) < CACHE_EXPIRY_SECONDS

# --- Standalone Asynchronous Database Helper Functions ---
async def _execute_sync_op_standalone(executor: ThreadPoolExecutor, func, *args, **kwargs):
    return await asyncio.get_running_loop().run_in_executor(executor, func, *args, **kwargs)

# FIX: Correct definition of _execute_sync_db_op
# It should NOT take 'executor' as an argument, it uses self.executor
async def _execute_sync_db_op(self, func, *args, **kwargs):
    return await asyncio.get_running_loop().run_in_executor(self.executor, func, *args, **kwargs)


async def fetch_transactions_from_db(executor: ThreadPoolExecutor, ack_no: str, from_date: date, to_date: date, type: str):
    def _sync_fetch():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                account_col = 'account_number' if type == 'victim' else 'to_account'
                cur.execute(f"""
                    SELECT {account_col}
                    FROM case_entry_form
                    WHERE ack_no = %s
                """, (ack_no,))
                result = cur.fetchone()

                if not result or not result.get(account_col):
                    return []

                account_num = result.get(account_col)
                if not isinstance(account_num, (int, float, str)) or (isinstance(account_num, str) and not re.fullmatch(r'\d+', str(account_num).strip())):
                    return []

                query = f"SELECT txn_date, descr, txn_ref, amount, txn_type FROM txn WHERE acct_num = %s AND txn_date BETWEEN %s AND %s ORDER BY txn_date DESC, txn_time DESC;"
                cur.execute(query, (account_num, from_date, to_date))
                raw_transactions = cur.fetchall()

                processed_transactions = []
                for txn in raw_transactions:
                    withdrawal = None
                    deposit = None
                    if txn.get('txn_type') == 'Debit':
                        withdrawal = txn.get('amount')
                    elif txn.get('txn_type') == 'Credit':
                        deposit = txn.get('amount')

                    processed_transactions.append({
                        'date': txn.get('txn_date'),
                        'narration': txn.get('descr'),
                        'refNo': txn.get('txn_ref'),
                        'valueDate': txn.get('txn_date'),
                        'withdrawal': withdrawal,
                        'deposit': deposit,
                        'closingBalance': None
                    })
                return processed_transactions
    return await _execute_sync_op_standalone(executor, _sync_fetch)

async def insert_uploaded_document(executor: ThreadPoolExecutor, case_id: int, document_type: str, original_filename: str, saved_filepath: str, file_mime_type: str, comment: Optional[str] = None, uploaded_by: Optional[str] = None):
    # FIX: Redefine _sync_insert to accept all necessary parameters
    def _sync_insert(case_id: int, document_type: str, original_filename: str, saved_filepath: str, file_mime_type: str, uploaded_by: Optional[str], comment: Optional[str]):
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO public.case_documents
                        (case_id, document_type, original_filename, file_location, file_mime_type, uploaded_by, comment)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, original_filename, document_type, file_location, uploaded_at, uploaded_by, comment, file_mime_type;
                    """,
                    (case_id, document_type, original_filename, saved_filepath, file_mime_type, uploaded_by, comment)
                )
                new_doc = cur.fetchone()
                conn.commit()
                return new_doc
    # FIX: Pass all arguments to _execute_sync_op_standalone
    return await _execute_sync_op_standalone(executor, _sync_insert, case_id, document_type, original_filename, saved_filepath, file_mime_type, uploaded_by, comment)

async def get_uploaded_documents(executor: ThreadPoolExecutor, case_id: int) -> List[Dict[str, Any]]:
    def _sync_get_docs():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT id, document_type, original_filename, file_location, uploaded_by, comment, uploaded_at, file_mime_type
                    FROM public.case_documents WHERE case_id = %s ORDER BY uploaded_at DESC
                    """,
                    (case_id,) # Use case_id in the query
                )
                docs = cur.fetchall()
                return docs
    return await _execute_sync_op_standalone(executor, _sync_get_docs)

async def get_document_by_id(executor: ThreadPoolExecutor, document_id: int) -> Optional[Dict[str, Any]]:
    def _sync_get_document():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute("SELECT file_location, original_filename, file_mime_type FROM public.case_documents WHERE id = %s", (document_id,))
                return cur.fetchone()
    return await _execute_sync_op_standalone(executor, _sync_get_document)

# Note: save_or_update_decision and get_decision now refer to case_history, not case_decisions
async def save_or_update_decision(executor: ThreadPoolExecutor, case_id: int, data: Dict[str, Any]):
    def _sync_save_decision():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                # FIX: Align with actual case_history schema (remarks, updated_by)
                db_data_for_insert_update = {
                    "remarks": data.get('comments'), # Map frontend 'comments' to DB 'remarks'
                    "updated_by": data.get('assignedEmployee'), # Map frontend 'assignedEmployee' to DB 'updated_by'
                    # REMOVED: "short_dn": data.get('riskScore'),
                    # REMOVED: "long_dn": data.get('systemExplanation'),
                    # REMOVED: "decision_type": data.get('decisionAction'),
                    # REMOVED: "assigned_employee": data.get('assignedEmployee'), (this was in old decision table)
                    # REMOVED: "audit_trail": data.get('auditTrail'), (this was in old decision table)
                    # REMOVED: "system_recommendation": data.get('systemRecommendation'),
                    # REMOVED: "system_explanation": data.get('systemExplanation')
                }

                filtered_db_data = {k: v if v != '' else None for k, v in db_data_for_insert_update.items()}
                
                db_columns_list = ["case_id"] # Always include case_id
                db_values_list = [case_id]

                for key, value in filtered_db_data.items():
                    db_columns_list.append(key)
                    db_values_list.append(value)

                update_set_parts = [f"{col} = EXCLUDED.{col}" for col in db_columns_list if col != "case_id"]
                update_set_parts.append("created_time = NOW()") # Update timestamp

                insert_cols_str = ", ".join(db_columns_list)
                insert_placeholders_str = ", ".join(["%s"] * len(db_columns_list))
                update_set_str = ", ".join(update_set_parts)

                # Since case_history is designed for audit trail (multiple entries per case_id),
                # we should just INSERT a new record instead of trying to update
                cur.execute(
                    f"""
                    INSERT INTO public.case_history ({insert_cols_str})
                    VALUES ({insert_placeholders_str})
                    RETURNING *;
                    """,
                    tuple(db_values_list)
                )
                
                updated_decision_record = cur.fetchone()
                
                # Update case_main table status and closing_date if decision action indicates case closure
                decision_action = data.get('decisionAction')
                if decision_action:
                    new_status = None
                    should_set_closing_date = False
                    
                    if decision_action in ['Close Case', 'Closed', 'Approve', 'Reject']:
                        new_status = 'Closed'
                        should_set_closing_date = True
                    elif decision_action == 'Mark as False Positive':
                        new_status = 'False Positive'
                        should_set_closing_date = True
                    elif decision_action == 'Assigned':
                        new_status = 'Assigned'
                    
                    if new_status:
                        update_query = "UPDATE public.case_main SET status = %s"
                        update_params = [new_status]
                        
                        if should_set_closing_date:
                            update_query += ", closing_date = CURRENT_DATE"
                        
                        update_query += " WHERE case_id = %s"
                        update_params.append(case_id)
                        
                        cur.execute(update_query, tuple(update_params))
                        print(f"✅ Case {case_id} status updated to '{new_status}' in case_main table.", flush=True)
                
                conn.commit()
                print(f"✅ Decision record for case_id {case_id} saved/updated in case_history.", flush=True)

                return updated_decision_record
    return await _execute_sync_op_standalone(executor, _sync_save_decision)


async def get_decision(executor: ThreadPoolExecutor, case_id: int) -> Optional[Dict[str, Any]]:
    def _sync_get_decision():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute("SELECT * FROM public.case_history WHERE case_id = %s", (case_id,))
                decision_record_db = cur.fetchone() # This will have snake_case keys from DB
                
                if not decision_record_db:
                    return None
                
                # FIX: Map actual case_history columns to frontend camelCase expectations
                mapped_decision = {
                    "caseId": decision_record_db.get('case_id'),
                    "riskScore": decision_record_db.get('remarks'), # Mapping riskScore from remarks (as it's general purpose)
                    "triggeringRules": None, # Not directly stored in case_history
                    "comments": decision_record_db.get('remarks'), # Map remarks to comments
                    "decisionAction": None, # Not directly stored in case_history
                    "assignedEmployee": decision_record_db.get('updated_by'), # Map updated_by to assignedEmployee
                    "auditTrail": None, # Not directly stored in case_history
                    "systemRecommendation": None, # Not directly stored in case_history
                    "systemExplanation": None, # Not directly stored in case_history
                    "lastUpdatedAt": decision_record_db.get('created_time').isoformat() if decision_record_db.get('created_time') else None,
                }
                return mapped_decision
    return await _execute_sync_op_standalone(executor, _sync_get_decision)



# --- CaseEntryMatcher Class (Core logic for both old and new systems) ---
class CaseEntryMatcher:
    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor
        # COMMENTED OUT: Complex assignment service
        # self.assignment_service = CaseAssignmentService(executor)

    # FIX: Correct definition of _execute_sync_db_op
    # It should NOT take 'executor' as an argument, it uses self.executor
    async def _execute_sync_db_op(self, func, *args, **kwargs):
        return await asyncio.get_running_loop().run_in_executor(self.executor, func, *args, **kwargs)

    def _sync_check_transactions_for_ecb_creation(self, vm_acc_num: str, bm_acc_num: str, to_date: date, from_date: date) -> bool:
        """
        Synchronous helper to check for transfers from VM to BM account in the txn table.
        This is for the case creation logic.
        """
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                # Check for transfers from VM account (acct_num) to BM account (bene_acct_num)
                cur.execute(
                    """
                    SELECT COUNT(*) FROM public.txn
                    WHERE acct_num = %s AND bene_acct_num = %s
                      AND txn_date BETWEEN %s AND %s;
                    """,
                    (vm_acc_num, bm_acc_num, from_date, to_date)
                )
                count = cur.fetchone()['count']
                return count > 0

    # UPDATED METHOD: insert_into_case_main
    # UPDATED METHOD: insert_into_case_main (new system's primary case table)
    # This helper is called by match_data, create_nab_case_if_flagged, create_psa_case_if_flagged
    async def insert_into_case_main(self, case_type: str, source_ack_no: str, cust_id: Optional[str] = None,
                                    acc_num: Optional[str] = None, source_bene_accno: Optional[str] = None,
                                    is_operational: bool = False, status: str = 'New',
                                    decision_input: Optional[str] = None,
                                    remarks_input: Optional[str] = None,
                                    customer_full_name: Optional[str] = None,
                                    location: Optional[str] = None,
                                    disputed_amount: Optional[float] = None,
                                    created_by: Optional[str] = None
                                    ) -> int:
        def _sync_insert():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    actual_short_dn = customer_full_name or "N/A"
                    actual_long_dn = remarks_input or ""
                    actual_decision_type = decision_input or "N/A"

                    try:
                        cur.execute("""
                            INSERT INTO public.case_main (
                                case_type, source_ack_no, cust_id, acc_num, source_bene_accno,
                                is_operational, status, creation_date, creation_time,
                                short_dn, long_dn, decision_type, location, disputed_amount, created_by
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, (NOW() AT TIME ZONE 'Asia/Kolkata')::date, (NOW() AT TIME ZONE 'Asia/Kolkata')::time, %s, %s, %s, %s, %s, %s)
                            RETURNING case_id;
                        """, (
                            case_type, source_ack_no, cust_id, acc_num, source_bene_accno,
                            is_operational, status,
                            actual_short_dn, actual_long_dn, actual_decision_type,
                            location, disputed_amount, created_by or "System"
                        ))
                        new_case_id = cur.fetchone()['case_id']
                        conn.commit()
                        return new_case_id
                    except psycopg2.Error as e:
                        conn.rollback()
                        print(f"ERROR: Database error inserting into case_main for source_ack_no '{source_ack_no}': {e}", flush=True)
                        raise ValueError(f"Database error inserting case into case_main: {e}")
                    except Exception as e:
                        conn.rollback()
                        print(f"UNEXPECTED ERROR: Failed to insert into case_main for source_ack_no '{source_ack_no}': {e}", flush=True)
                        raise ValueError(f"Unexpected error inserting case into case_main: {e}")

        try:
            case_id = await self._execute_sync_db_op(_sync_insert)
            
            # Log case creation
            if case_id:
                try:
                    creator_name = created_by or "System"
                    log_case_action(
                        case_id=case_id,
                        user_name=creator_name,
                        action="case_created",
                        details=f"Case created by {creator_name}. Type: {case_type}, ACK: {source_ack_no}"
                    )
                    print(f"✅ Case {case_id} ({source_ack_no}) creation logged by {creator_name}", flush=True)
                except Exception as log_error:
                    print(f"WARNING: Failed to log case creation for case {case_id}: {log_error}", flush=True)
                    # Don't fail case creation if logging fails
                
                # SIMPLIFIED: Auto-assign the case after creation to general queue
                try:
                    assigned_user = await self._simple_assign_case(case_id, case_type, source_ack_no)
                    if assigned_user:
                        print(f"✅ Case {case_id} ({source_ack_no}) automatically assigned to general queue: {assigned_user}", flush=True)
                    else:
                        print(f"⚠️ Case {case_id} ({source_ack_no}) created but auto-assignment failed", flush=True)
                except Exception as assignment_error:
                    print(f"ERROR: Auto-assignment failed for case {case_id}: {assignment_error}", flush=True)
                    # Don't fail case creation if assignment fails
            
            return case_id
        except ValueError:
            raise
        except Exception as e:
            print(f"UNEXPECTED ERROR in insert_into_case_main wrapper for '{source_ack_no}': {e}", flush=True)
            raise

    # NEW: Simplified assignment method
    async def _simple_assign_case(self, case_id: int, case_type: str, source_ack_no: str) -> Optional[str]:
        """
        Simplified case assignment - assigns all cases to general risk officer queue
        """
        def _sync_assign():
            try:
                # Get first available risk officer
                with get_db_connection() as conn:
                    with get_db_cursor(conn) as cur:
                        cur.execute("""
                            SELECT user_name 
                            FROM user_table 
                            WHERE user_type = 'risk_officer'
                            ORDER BY user_name
                            LIMIT 1
                        """)
                        result = cur.fetchone()
                        
                        if not result:
                            print(f"ERROR: No risk officers available for case assignment", flush=True)
                            return None
                        
                        assigned_user = result['user_name']
                        
                        # Ensure assignment table columns exist
                        cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
                        cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS assignment_type VARCHAR(50) DEFAULT 'manual'")
                        
                        # Insert assignment record
                        cur.execute("""
                            INSERT INTO assignment (case_id, assigned_to, assigned_by, comment, is_active, assignment_type)
                            VALUES (%s, %s, %s, %s, TRUE, 'auto')
                        """, (case_id, assigned_user, "System", f"Auto-assigned {case_type} case to general queue"))
                        
                        conn.commit()
                        print(f"✅ Case {case_id} successfully assigned to general queue: {assigned_user}", flush=True)
                        return assigned_user
                        
            except Exception as e:
                print(f"ERROR: Failed to assign case {case_id}: {e}", flush=True)
                return None
        
        return await self._execute_sync_db_op(_sync_assign)

    # UPDATED METHOD: match_data (for POST /api/case-entry) - Implements new VM/BM/No-Match flow
    async def match_data(self, data: CaseEntryData, evidence_file: Optional[UploadFile] = None, created_by_user: Optional[str] = "System"):
        victim_cust_id = None
        beneficiary_cust_id = None
        new_case_main_ids = [] # To store IDs of potentially multiple cases created

        # --- Backend Validation for Numeric Account Fields (from CaseEntryData) ---
        errors = []
        CaseEntryMatcher.validate_numeric_field("accountNumber", data.accountNumber, errors)
        CaseEntryMatcher.validate_numeric_field("cardNumber", data.cardNumber, errors)
        CaseEntryMatcher.validate_numeric_field("toAccount", data.toAccount, errors)
        CaseEntryMatcher.validate_numeric_field("transactionAmount", data.transactionAmount, errors)
        CaseEntryMatcher.validate_numeric_field("disputedAmount", data.disputedAmount, errors)
        CaseEntryMatcher.validate_numeric_field("toAmount", data.toAmount, errors)
        CaseEntryMatcher.validate_numeric_field("lienAmount", data.lienAmount, errors)

        if errors:
            error_message = f"Validation Error for ack_no {data.ackNo}: " + "; ".join(errors)
            print(f"❌ {error_message}", flush=True)
            raise ValueError(error_message)

        # ---- Debugging Incoming Data ----
        print("\n--- Starting match_data processing (New Flow) ---", flush=True)
        print("Received ackNo:", data.ackNo, flush=True)
        print("Received customerName:", data.customerName, flush=True)
        print("Received accountNumber (victim):", data.accountNumber, flush=True)
        print("Received toAccount (beneficiary):", data.toAccount, flush=True)
        print("Received transactionId:", data.transactionId, flush=True) # Alphanumeric now

        # ---- Check for victim match (ONLY against account_customer) ----
        has_victim_db_match = False
        if data.accountNumber is not None:
            def _sync_check_victim_account_customer():
                with get_db_connection() as conn:
                    with get_db_cursor(conn) as cur:
                        cur.execute("SELECT cust_id FROM account_customer WHERE acc_num = %s", (str(data.accountNumber),))
                        return cur.fetchone()
            try:
                victim_result = await self._execute_sync_db_op(_sync_check_victim_account_customer)
                if victim_result:
                    victim_cust_id = victim_result.get('cust_id')
                    has_victim_db_match = True
                print(f"Victim account match result from DB: {victim_result}", flush=True)
            except Exception as e:
                print(f"Error checking victim account match for {data.accountNumber}: {e}", flush=True)

        # ---- Check for beneficiary match (ONLY against account_customer) ----
        has_beneficiary_db_match = False
        if data.toAccount is not None:
            def _sync_check_beneficiary_account_customer():
                with get_db_connection() as conn:
                    with get_db_cursor(conn) as cur:
                        cur.execute("SELECT cust_id FROM account_customer WHERE acc_num = %s", (str(data.toAccount),))
                        return cur.fetchone()
            try:
                beneficiary_result = await self._execute_sync_db_op(_sync_check_beneficiary_account_customer)
                if beneficiary_result:
                    beneficiary_cust_id = beneficiary_result.get('cust_id')
                    has_beneficiary_db_match = True
                print(f"Beneficiary account match result from DB: {beneficiary_result}", flush=True)
            except Exception as e:
                print(f"Error checking beneficiary account match for {data.toAccount}: {e}", flush=True)

        print(f"DEBUG: At this point (match_data), has_victim_db_match: {has_victim_db_match}, has_beneficiary_db_match: {has_beneficiary_db_match}", flush=True)

        # --- Stage 1: Case Creation based on Initial Match (VM/BM ONLY) ---

        # If NEITHER victim NOR beneficiary account matches, DO NOT insert into case_main
        if not has_victim_db_match and not has_beneficiary_db_match:
            print("INFO: No Victim or Beneficiary account match found. Skipping case_main creation for this Data Entry.", flush=True)
            new_case_main_ids = [] # Ensure it's empty if no case_main entry
            # Still insert into case_entry_form below
        else:
            # If either or both match, create case(s)
            if has_victim_db_match:
                # Create Case 1: Victim Match (VM)
                vm_case_type = 'VM'
                vm_is_operational = True 
                vm_ack_no = f"{data.ackNo}_VM"
                vm_cust_id = victim_cust_id or data.customerId # Use discovered cust_id or provided
                vm_acc_num = data.accountNumber
                vm_remarks = f"VM case from Data Entry. Original ACK: {data.ackNo}. Customer: {data.customerName or 'N/A'}."
                
                new_vm_case_main_id = await self.insert_into_case_main(
                    case_type=vm_case_type, source_ack_no=vm_ack_no, cust_id=vm_cust_id, acc_num=vm_acc_num,
                    is_operational=vm_is_operational, status='New', decision_input='Pending Review', remarks_input=vm_remarks,
                    customer_full_name=data.customerName,
                    location=data.district,
                    disputed_amount=data.disputedAmount,
                    created_by=created_by_user
                )
                new_case_main_ids.append(new_vm_case_main_id)
                print(f"✅ VM Case Main entry created with case_id: {new_vm_case_main_id} for ACK {vm_ack_no}", flush=True)
                await save_or_update_decision(self.executor, new_vm_case_main_id, {"remarks": vm_remarks, "short_dn": "VM Case", "long_dn": vm_remarks, "decision_type": "Created", "updated_by": "System"})
                print(f"✅ Initial history record for VM case_id {new_vm_case_main_id} inserted into case_history.", flush=True)

            if has_beneficiary_db_match: # Check again if beneficiary also matches (for 2 cases)
                # Create Case 2: Beneficiary Match (BM)
                bm_case_type = 'BM'
                bm_is_operational = True 
                bm_ack_no = f"{data.ackNo}_BM"
                bm_cust_id = beneficiary_cust_id or data.customerId # Use discovered cust_id or provided
                bm_acc_num = data.toAccount
                bm_remarks = f"BM case from Data Entry. Original ACK: {data.ackNo}. Customer: {data.customerName or 'N/A'}."

                new_bm_case_main_id = await self.insert_into_case_main(
                    case_type=bm_case_type, source_ack_no=bm_ack_no, cust_id=bm_cust_id, acc_num=bm_acc_num,
                    is_operational=bm_is_operational, status='New', decision_input='Pending Review', remarks_input=bm_remarks,
                    customer_full_name=data.customerName,
                    location=data.district,
                    disputed_amount=data.disputedAmount,
                    created_by=created_by_user
                )
                new_case_main_ids.append(new_bm_case_main_id)
                print(f"✅ BM Case Main entry created with case_id: {new_bm_case_main_id} for ACK {bm_ack_no}", flush=True)
                await save_or_update_decision(self.executor, new_bm_case_main_id, {"remarks": bm_remarks, "short_dn": "BM Case", "long_dn": bm_remarks, "decision_type": "Created", "updated_by": "System"})
                print(f"✅ Initial history record for BM case_id {new_bm_case_main_id} inserted into case_history.", flush=True)

                # --- ECB Case Creation Logic (ECBT/ECBNT) ---
                # Trigger ECBT/ECBNT check for the beneficiary account
                try:
                    txn_lookup_to_date = data.transactionDate if data.transactionDate else date.today()
                    txn_lookup_from_date = txn_lookup_to_date - timedelta(days=90) # Look back 90 days
                    vm_acc_num = data.accountNumber  # From victim side
                    bm_beneficiary_acc_num = data.toAccount  # Beneficiary account
                    bm_beneficiary_cust_id = beneficiary_cust_id

                    print(f"DEBUG: Fetching transactions for ECBT/ECBNT check for beneficiary account: {bm_beneficiary_acc_num} from {txn_lookup_from_date} to {txn_lookup_to_date}", flush=True)

                    def _sync_check_transactions_for_ecb_creation():
                        with get_db_connection() as conn:
                            with get_db_cursor(conn) as cur:
                                cur.execute(
                                    """
                                    SELECT COUNT(*) FROM public.txn
                                    WHERE acct_num = %s AND bene_acct_num = %s
                                      AND txn_date BETWEEN %s AND %s;
                                    """,
                                    (vm_acc_num, bm_beneficiary_acc_num, txn_lookup_from_date, txn_lookup_to_date)
                                )
                                count = cur.fetchone()['count']
                                return count > 0
                    
                    has_transactions_for_ecb = False
                    if vm_acc_num:
                        has_transactions_for_ecb = await self._execute_sync_db_op(_sync_check_transactions_for_ecb_creation)
                    
                    ecb_case_type = 'ECBT' if has_transactions_for_ecb else 'ECBNT'
                    ecb_remarks = f"Automated {ecb_case_type} case from Data Entry BM flow. Beneficiary Acc: {bm_beneficiary_acc_num}."
                    ecb_data_for_creation = ECBCaseData(
                        sourceAckNo=f"{data.ackNo}_{ecb_case_type}",
                        customerId=bm_beneficiary_cust_id,
                        beneficiaryAccountNumber=bm_beneficiary_acc_num,
                        hasTransaction=has_transactions_for_ecb,
                        remarks=ecb_remarks,
                        location=data.district,  # Inherit from original data entry
                        disputedAmount=data.disputedAmount  # Inherit from original data entry
                    )
                    print(f"DEBUG: Calling create_ecb_case for beneficiary account: {bm_beneficiary_acc_num} as {ecb_case_type}", flush=True)
                    ecb_case_result = await self.create_ecb_case(ecb_data_for_creation, created_by_user=created_by_user)
                    if ecb_case_result:
                        new_ecb_case_id = ecb_case_result['case_id']
                        new_case_main_ids.append(new_ecb_case_id)
                        print(f"✅ Additional {ecb_case_type} case created with case_id: {ecb_case_result['case_id']} from BM flow.", flush=True)
                    else:
                        print(f"INFO: No {ecb_case_type} case created for beneficiary account: {bm_beneficiary_acc_num} during BM flow.", flush=True)
                except Exception as e:
                    print(f"ERROR: Failed to create ECBT/ECBNT case during BM flow for {bm_beneficiary_acc_num}: {e}", flush=True)

        # --- OLD TABLES INSERTIONS (case_entry_form is kept for slow migration) ---
        print("Inserting into old case_entry_form table (if still needed by other parts of old system)...", flush=True)
        saved_filepath_for_db = None
        original_filename_for_db = None

        if evidence_file:
            UPLOAD_DIR = "/home/ubuntu/fraud_uploads"
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            original_filename = evidence_file.filename if evidence_file.filename else "unknown_file"
            file_extension = os.path.splitext(original_filename)[1] if original_filename else ".bin"
            
            # Use the first new_case_main_id for file name prefix for new system documents
            # Or a generic UUID if no case_main entry was created (i.e., new_case_main_ids is empty)
            file_prefix_id = new_case_main_ids[0] if new_case_main_ids else uuid.uuid4().hex[:10].upper()
            unique_filename = f"{file_prefix_id}_{uuid.uuid4().hex[:10].upper()}{file_extension}" 
            saved_filepath_for_db = os.path.join(UPLOAD_DIR, unique_filename)
            original_filename_for_db = original_filename

            try:
                file_content = await evidence_file.read()
                def _sync_write_file():
                    with open(saved_filepath_for_db, "wb") as buffer:
                        buffer.write(file_content)
                await self._execute_sync_db_op(_sync_write_file, file_content)
                print(f"✅ Evidence file saved to: {saved_filepath_for_db}", flush=True)
            except Exception as e:
                print(f"❌ Error saving evidence file for ack_no {data.ackNo}: {e}", flush=True)
                raise ValueError(f"Failed to save evidence file: {e}")

        def _sync_insert_case_entry_form():
            with get_db_connection() as conn_form_insert:
                with get_db_cursor(conn_form_insert) as cur_form_insert:
                    try:
                        cur_form_insert.execute("""INSERT INTO case_entry_form (
                            ack_no, customer_name, sub_category, transaction_date, complaint_date, report_datetime,
                            state, district, policestation, payment_mode,
                            account_number, card_number, transaction_id, layers,
                            transaction_amount, disputed_amount, action, to_bank, to_account,
                            ifsc, to_transaction_id, to_amount, action_taken_date, lien_amount,
                            evidence, evidence_name, additional_info, to_upi_id, submitted_on
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (
                                data.ackNo, data.customerName, data.subCategory, data.transactionDate, data.complaintDate, data.reportDateTime,
                                data.state, data.district, data.policestation, data.paymentMode,
                                str(data.accountNumber) if data.accountNumber is not None else None,
                                str(data.cardNumber) if data.cardNumber is not None else None,
                                str(data.transactionId),
                                data.layers,
                                data.transactionAmount,
                                data.disputedAmount,
                                data.action,
                                str(data.toBank) if data.toBank is not None else None,
                                str(data.toAccount) if data.toAccount is not None else None,
                                data.ifsc,
                                str(data.toTransactionId),
                                data.toAmount,
                                data.actionTakenDate,
                                data.lienAmount or None,
                                saved_filepath_for_db,
                                original_filename_for_db,
                                data.additionalInfo,
                                data.toUpiId,
                                datetime.now()
                            )
                        )
                        conn_form_insert.commit()
                        print(f"✅ Case_entry_form committed to the database.", flush=True)
                    except psycopg2.Error as e:
                        conn_form_insert.rollback()
                        print(f"❌ Error inserting into case_entry_form for ack_no {data.ackNo}: {e}", flush=True)
                        raise ValueError(f"Database error inserting into case_entry_form: {e}")
        await self._execute_sync_db_op(_sync_insert_case_entry_form)

        # Call the new document insertion API (into case_documents)
        if evidence_file:
            # If any case_main entry was created, link doc to the first one. Otherwise, don't link (or link to a generic placeholder).
            if new_case_main_ids:
                await self.insert_uploaded_document(
                    self.executor,
                    new_case_main_ids[0], # Use the first new_case_main_id for the document
                    document_type=data.subCategory or "Data Entry Upload", # Use subCategory as doc type or generic
                    original_filename=original_filename_for_db,
                    saved_filepath=saved_filepath_for_db,
                    file_mime_type=evidence_file.content_type,
                    comment=f"Document uploaded for manual case {data.ackNo}.",
                    uploaded_by=data.customerName or "System"
                )
                print(f"✅ Document record for {data.ackNo} inserted into case_documents (Case ID: {new_case_main_ids[0]}).", flush=True)
            else:
                print(f"INFO: No case_main entry created for {data.ackNo}, skipping document link to new system.", flush=True)


        # Check if no matches were found
        if not has_victim_db_match and not has_beneficiary_db_match:
            return {
                "message": f"Case entry '{data.ackNo}' processed. New case_main ID(s): {new_case_main_ids}.",
                "no_match": True,
                "no_match_message": "No Victim or Beneficiary account match found"
            }
        else:
            return {"message": f"Case entry '{data.ackNo}' processed. New case_main ID(s): {new_case_main_ids}."}


    # FIX: Ensure this method is correctly defined as a @staticmethod inside CaseEntryMatcher
    @staticmethod
    def validate_numeric_field(field_name: str, field_value: Union[int, float, str, None], error_list: list):
        if field_value is not None and str(field_value).strip() != '':
            if isinstance(field_value, str):
                if not re.fullmatch(r'\d+', field_value.strip()):
                    error_list.append(f"'{field_name}' ('{field_value}') must contain only digits.")
            elif isinstance(field_value, (int, float)):
                if not str(int(field_value)).isdigit():
                    error_list.append(f"'{field_name}' ('{field_value}') must contain only digits.")

    # NEW METHOD: Fetch I4C Document Master List
    async def fetch_i4c_document_list(self) -> List[Dict[str, Any]]:
        def _sync_fetch_list():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("""
                        SELECT seq_id, file_name, file_description, sent_at FROM public.i4c_manual_file_list ORDER BY seq_id;
                    """)
                    return cur.fetchall()
        try:
            return await self._execute_sync_db_op(_sync_fetch_list)
        except Exception as e:
            print(f"Error fetching I4C document master list: {e}", flush=True)
            raise

    # UPDATED METHOD: screen_new_customers (for NAA case type and broader matching)
    async def screen_new_customers(self, payload: NewCustomerRequest) -> Dict[str, Any]:
        async def _sync_screen_customers():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    clean_count = 0
                    suspicious_count = 0

                    for customer in payload.customers: # Iterates through each new customer in the payload
                        matched = False
                        matched_fields = []
                        cyber_result_ack_no = None
                        suspect_result_id = None
                        case_main_beneficiary_case_id = None 

                        # 1. Matching Logic against cyber_complaints (for current customer's details)
                        cur.execute("""
                            SELECT ack_no FROM cyber_complaints
                            WHERE comp_mobile = %s OR aadhar = %s OR pan = %s OR comp_email = %s
                            OR suspect_bank_acct = %s OR suspect_upi_mobile = %s
                        """, (
                            customer.mobile, customer.aadhar, customer.pan, customer.email,
                            customer.customerId, # Assuming customerId might be bank account for new customers
                            customer.upiId # Assuming customer.upiId for new customers
                        ))
                        cyber_result_row = cur.fetchone()
                        if cyber_result_row:
                            matched = True
                            matched_fields.append("cyber_complaints")
                            cyber_result_ack_no = cyber_result_row.get('ack_no')

                        # 2. Matching Logic against suspect_entries (for current customer's details)
                        cur.execute("""
                            SELECT id FROM suspect_entries
                            WHERE mobile = %s OR aadhar = %s OR pan = %s OR email_id = %s
                            OR bank_account_number = %s OR upi_id = %s
                        """, (
                            customer.mobile, customer.aadhar, customer.pan, customer.email,
                            customer.customerId, # Assuming customerId might be bank account
                            customer.upiId # Assuming customer.upiId
                        ))
                        suspect_result_row = cur.fetchone()
                        if suspect_result_row:
                            matched = True
                            matched_fields.append("suspect_entries")
                            suspect_result_id = suspect_result_row.get('id')
                        
                        # NEW: 3. Matching Logic against case_main (beneficiary accounts from other cases)
                        # Check if this new customer's details match any beneficiary involved in existing 'BM'/'NAB'/'ECBT'/'ECBNT' cases
                        cur.execute("""
                            SELECT cm.case_id FROM public.case_main AS cm
                            WHERE cm.case_type IN ('BM', 'NAB', 'ECBT', 'ECBNT') AND (
                                cm.source_bene_accno = %s OR cm.cust_id = %s OR 
                                EXISTS (SELECT 1 FROM public.case_entry_form cef WHERE cef.ack_no = cm.source_ack_no AND (
                                    cef.to_account = %s OR cef.to_upi_id = %s
                                ))
                            ) LIMIT 1;
                        """, (
                            customer.customerId, # Potential beneficiary account number
                            customer.customerId, # Potential beneficiary customer ID
                            customer.customerId, # Potential to_account (from entry form)
                            customer.upiId # UPI ID match
                        ))

                        case_main_beneficiary_match = cur.fetchone()
                        if case_main_beneficiary_match:
                            matched = True
                            matched_fields.append("case_main_beneficiary")
                            case_main_beneficiary_case_id = case_main_beneficiary_match.get('case_id')

                        if matched:
                            suspicious_count += 1
                            # Case type for new screened customer is 'NAA' (Newly Added Account)
                            new_case_ack_no = f"NAA_{uuid.uuid4().hex[:10].upper()}"
                            
                            # Insert into case_main
                            new_case_main_id = await self.insert_into_case_main(
                                case_type='NAA', # Case type for newly added account screening
                                source_ack_no=new_case_ack_no,
                                cust_id=customer.customerId,
                                acc_num=customer.customerId, # Assuming customerId is the account number for new accounts
                                is_operational=False, # NAA is Stage 2, not operational
                                status='New',
                                decision_input='Pending Review',
                                remarks_input=f"New Account Screening Match for Customer: {customer.fullName}. Matched on: {', '.join(matched_fields)}.",
                                customer_full_name=customer.fullName,
                                location=None,  # NAA cases don't have location from data entry
                                disputed_amount=None,  # NAA cases don't have disputed amount from data entry
                                created_by="System"
                            )

                            # Insert initial case history
                            initial_history_data = {
                                "remarks": f"NAA case generated. Match on: {', '.join(matched_fields)}.",
                                "updated_by": "System"
                            }
                            await save_or_update_decision(self.executor, new_case_main_id, initial_history_data)

                            # Insert into case_details_1 (from new customer payload)
                            cur.execute("""
                                INSERT INTO public.case_details_1 (
                                    cust_id, casetype, mobile, email, pan, aadhar, acc_no, match_flag
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                customer.customerId,
                                'NAA',
                                customer.mobile,
                                customer.email,
                                customer.pan,
                                customer.aadhar,
                                customer.customerId, # acc_no for case_details_1
                                ", ".join(matched_fields)
                            ))
                            conn.commit() # Commit case_details_1 insertion
                            print(f"⚠️ [SUSPICIOUS] Customer ID: {customer.customerId}, Name: {customer.fullName}, Matched on: {', '.join(matched_fields)}. Created NAA case {new_case_ack_no}.")
                        else:
                            clean_count += 1
                            print(f"✅ [CLEAN] Customer ID: {customer.customerId}, Name: {customer.fullName}")

                    return {
                        "message": f"Screening completed. {clean_count} clean, {suspicious_count} suspicious.",
                        "clean_count": clean_count,
                        "suspicious_count": suspicious_count
                    }
        return await self._execute_sync_db_op(_sync_screen_customers)

    async def create_psa_case_if_flagged(self, suspect_data: PotentialSuspectAccountData) -> Optional[Dict[str, Any]]:
        def _sync_create_psa_case():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    matched = False
                    matched_fields = []
                    cyber_result_ack_no = None
                    suspect_result_id = None

                    # 1. Matching Logic against cyber_complaints
                    cur.execute("""
                        SELECT ack_no FROM cyber_complaints
                        WHERE suspect_bank_acct = %s OR suspect_upi_mobile = %s OR comp_email = %s
                        OR comp_mobile = %s OR aadhar = %s OR pan = %s
                    """, (
                        suspect_data.accountNumber or None, suspect_data.upiId or None, suspect_data.email or None,
                        suspect_data.mobile or None, suspect_data.aadhar or None, suspect_data.pan or None
                    ))
                    cyber_result_row = cur.fetchone()
                    if cyber_result_row:
                        matched = True
                        matched_fields.append("cyber_complaints")
                        cyber_result_ack_no = cyber_result_row.get('ack_no')

                    # 2. Matching Logic against suspect_entries
                    sql_suspect_query = """
                        SELECT id FROM suspect_entries
                        WHERE bank_account_number = %s OR mobile = %s OR email_id = %s OR pan = %s OR aadhar = %s OR upi_id = %s
                    """
                    params_for_suspect_query = (
                        suspect_data.accountNumber or None,
                        suspect_data.mobile or None,
                        suspect_data.email or None,
                        suspect_data.pan or None,
                        suspect_data.aadhar or None,
                        suspect_data.upiId or None
                    )
                    
                    print(f"DEBUG: Suspects SQL Query: {sql_suspect_query}", flush=True)
                    print(f"DEBUG: Suspects Params Values (FIXED): {params_for_suspect_query}", flush=True)
                    print(f"DEBUG: Suspects Param Types (FIXED): {[type(p) for p in params_for_suspect_query]}", flush=True)
                    
                    cur.execute(sql_suspect_query, params_for_suspect_query)
                    suspect_result_row = cur.fetchone()
                    if suspect_result_row:
                        matched = True
                        matched_fields.append("suspect_entries")
                        suspect_result_id = suspect_result_row.get('id')
                    
                    if matched:
                        print(f"⚠️ Flagged potential suspect account '{suspect_data.customerId}'. Creating PSA case.", flush=True)
                        
                        case_type = "PSA"
                        cur.execute("SELECT case_type FROM case_type_master WHERE case_type = %s", (case_type,))
                        if not cur.fetchone():
                            print(f"ERROR: Case type '{case_type}' not found in case_type_master.", flush=True)
                            raise ValueError(f"Case type '{case_type}' is not defined in case_type_master table.")

                        new_ack_no = f"PSA_{uuid.uuid4().hex[:10].upper()}"
                        print(f"Generated new ACK No for PSA case: {new_ack_no}", flush=True)

                        # FIX: Insert into case_main with is_operational=False
                        new_case_main_id = self.insert_into_case_main(
                            case_type=case_type,
                            source_ack_no=new_ack_no,
                            cust_id=suspect_data.customerId,
                            acc_num=suspect_data.accountNumber,
                            is_operational=False, # FIX: Set to False for Stage 2 cases
                            status='New',
                            decision_input='Pending Review',
                            remarks_input=suspect_data.suspiciousActivityDescription or 'Automated case for potential suspect account.',
                            customer_full_name=suspect_data.customerName,
                            location=None,  # PSA cases don't have location from data entry
                            disputed_amount=None,  # PSA cases don't have disputed amount from data entry
                            created_by="System"
                        )
                        print(f"✅ NEW Case Main entry created with case_id: {new_case_main_id} for ACK {new_ack_no}", flush=True)

                        # FIX: Insert initial audit/decision into case_history
                        initial_history_data = {
                            "remarks": suspect_data.suspiciousActivityDescription or f"PSA case generated due to match on {', '.join(matched_fields)}.",
                            "short_dn": "PSA Flagged",
                            "long_dn": "Automated case created for Potential Suspect Account screening match.",
                            "decision_type": "Automated Trigger",
                            "updated_by": "System"
                        }
                        save_or_update_decision(self.executor, new_case_main_id, initial_history_data)
                        print(f"✅ Initial history record for case_id {new_case_main_id} inserted into case_history.", flush=True)

                        # REMOVED: Old case_master insertion etc.
                        # REMOVED: Old case_detail insertion
                        # REMOVED: Old case_decisions insertion

                        # FIX: Insert into case_details_1 table (specific screening details)
                        cur.execute("""
                            INSERT INTO public.case_details_1 (
                                cust_id, casetype, mobile, email, pan, aadhar, acc_no, card, match_flag
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            suspect_data.customerId,
                            case_type,
                            suspect_data.mobile or None,
                            suspect_data.email or None,
                            suspect_data.pan or None,
                            suspect_data.aadhar or None,
                            suspect_data.accountNumber or None,
                            None, # card
                            "Potential Suspect Match"
                        ))
                        conn.commit()
                        print(f"✅ Case details_1 entry created for customer: {suspect_data.customerId}", flush=True)

                        return {
                            "ack_no": new_ack_no,
                            "case_id": new_case_main_id,
                            "message": "PSA case created successfully due to match."
                        }
                    else:
                        print(f"✅ Potential Suspect Account '{suspect_data.customerId}' is clean. No case created.", flush=True)
                        return None

        try:
            return await self._execute_sync_db_op(_sync_create_psa_case)
        except ValueError as e:
            print(f"ERROR processing PSA case: {e}", flush=True)
            raise
        except Exception as e:
            print(f"UNEXPECTED ERROR processing PSA case: {e}", flush=True)
            raise

    async def create_nab_case_if_flagged(self, beneficiary_data: BeneficiaryData) -> Optional[Dict[str, Any]]:
        def _sync_create_nab_case():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    matched = False
                    matched_fields = []
                    cyber_result_ack_no = None
                    suspect_result_id = None

                    # 1. Matching Logic against cyber_complaints
                    cur.execute("""
                        SELECT ack_no FROM cyber_complaints
                        WHERE suspect_bank_acct = %s OR suspect_upi_mobile = %s OR comp_email = %s
                        OR comp_mobile = %s OR aadhar = %s OR pan = %s
                    """, (
                        beneficiary_data.beneficiaryAccountNumber or None, beneficiary_data.beneficiaryUPI or None, beneficiary_data.beneficiaryEmail or None,
                        beneficiary_data.beneficiaryMobile or None, beneficiary_data.beneficiaryAadhar or None, beneficiary_data.beneficiaryPAN or None
                    ))
                    cyber_result_row = cur.fetchone()
                    if cyber_result_row:
                        matched = True
                        matched_fields.append("cyber_complaints")
                        cyber_result_ack_no = cyber_result_row.get('ack_no')

                    # 2. Matching Logic against suspect_entries
                    sql_suspect_query = """
                        SELECT id FROM suspect_entries
                        WHERE bank_account_number = %s OR mobile = %s OR email_id = %s OR pan = %s OR aadhar = %s OR upi_id = %s
                    """
                    params_for_suspect_query = (
                        beneficiary_data.beneficiaryAccountNumber or None,
                        beneficiary_data.beneficiaryMobile or None,
                        beneficiary_data.beneficiaryEmail or None,
                        beneficiary_data.beneficiaryPAN or None,
                        beneficiary_data.beneficiaryAadhar or None,
                        beneficiary_data.beneficiaryUPI or None
                    )
                    
                    print(f"DEBUG: Suspects SQL Query: {sql_suspect_query}", flush=True)
                    print(f"DEBUG: Suspects Params Values (FIXED): {params_for_suspect_query}", flush=True)
                    print(f"DEBUG: Suspects Param Types (FIXED): {[type(p) for p in params_for_suspect_query]}", flush=True)
                    
                    cur.execute(sql_suspect_query, params_for_suspect_query)
                    suspect_result_row = cur.fetchone()
                    if suspect_result_row:
                        matched = True
                        matched_fields.append("suspect_entries")
                        suspect_result_id = suspect_result_row.get('id')
                    
                    if matched:
                        print(f"⚠️ Flagged beneficiary '{beneficiary_data.beneficiaryName}'. Creating NAB case.", flush=True)
                        
                        case_type = "NAB" 
                        cur.execute("SELECT case_type FROM case_type_master WHERE case_type = %s", (case_type,))
                        if not cur.fetchone():
                            print(f"ERROR: Case type '{case_type}' not found in case_type_master.", flush=True)
                            raise ValueError(f"Case type '{case_type}' is not defined in case_type_master table.")

                        new_ack_no = f"NAB_{uuid.uuid4().hex[:10].upper()}"
                        print(f"Generated new ACK No for NAB case: {new_ack_no}", flush=True)

                        # FIX: Insert into case_main with is_operational=False
                        new_case_main_id = self.insert_into_case_main(
                            case_type=case_type,
                            source_ack_no=new_ack_no,
                            cust_id=beneficiary_data.customerId,
                            acc_num=beneficiary_data.beneficiaryAccountNumber,
                            source_bene_accno=beneficiary_data.beneficiaryAccountNumber,
                            is_operational=False, # FIX: Set to False for Stage 2 cases
                            status='New',
                            decision_input='Pending Review',
                            remarks_input='Automated case for new beneficiary match.',
                            customer_full_name=beneficiary_data.customerName,
                            location=None,  # NAB cases don't have location from data entry
                            disputed_amount=None,  # NAB cases don't have disputed amount from data entry
                            created_by="System"
                        )
                        print(f"✅ NEW Case Main entry created with case_id: {new_case_main_id} for ACK {new_ack_no}", flush=True)

                        # FIX: Insert initial audit/decision into case_history
                        initial_history_data = {
                            "remarks": f"NAB case generated due to match on {', '.join(matched_fields)}.",
                            "short_dn": "NAB Flagged",
                            "long_dn": "Automated case created for New Account Beneficiary screening match.",
                            "decision_type": "Automated Trigger",
                            "updated_by": "System"
                        }
                        save_or_update_decision(self.executor, new_case_main_id, initial_history_data)
                        print(f"✅ Initial history record for case_id {new_case_main_id} inserted into case_history.", flush=True)

                        # REMOVED: Old case_master insertion etc.
                        # REMOVED: Old case_detail insertion
                        # REMOVED: Old case_decisions insertion

                        # FIX: Insert into case_details_1 table (specific screening details)
                        cur.execute("""
                            INSERT INTO public.case_details_1 (
                                cust_id, casetype, mobile, email, pan, aadhar, acc_no, card, match_flag
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            beneficiary_data.customerId,
                            case_type, # 'NAB'
                            beneficiary_data.beneficiaryMobile or None,
                            beneficiary_data.beneficiaryEmail or None,
                            beneficiary_data.beneficiaryPAN or None,
                            beneficiary_data.beneficiaryAadhar or None,
                            beneficiary_data.beneficiaryAccountNumber or None,
                            None, # card
                            "Beneficiary Match"
                        ))
                        conn.commit()
                        print(f"✅ Case details_1 entry created for customer: {beneficiary_data.customerId}", flush=True)

                        return {
                            "ack_no": new_ack_no,
                            "case_id": new_case_main_id,
                            "message": "NAB case created successfully due to match."
                        }
                    else:
                        print(f"✅ Beneficiary '{beneficiary_data.beneficiaryName}' is clean. No case created.", flush=True)
                        return None

        try:
            return self._execute_sync_db_op(_sync_create_nab_case)
        except ValueError as e:
            print(f"ERROR processing NAB case: {e}", flush=True)
            raise
        except Exception as e:
            print(f"UNEXPECTED ERROR processing NAB case: {e}", flush=True)
            raise

    # NEW METHOD: Create ECBT/ECBNT case (Stage 2 Internal Cases)
    async def create_ecb_case(self, ecb_data: ECBCaseData, created_by_user: Optional[str] = "System") -> Optional[Dict[str, Any]]:
        case_type = 'ECBT' if ecb_data.hasTransaction else 'ECBNT'
        is_operational_value = False
        new_ack_no = f"{ecb_data.sourceAckNo}"

        new_case_main_id = await self.insert_into_case_main(
            case_type=case_type,
            source_ack_no=new_ack_no,
            cust_id=ecb_data.customerId,
            acc_num=ecb_data.beneficiaryAccountNumber,
            is_operational=is_operational_value,
            status='New',
            decision_input='Pending Review',
            remarks_input=ecb_data.remarks or f"Automated case for {case_type} - Beneficiary Account: {ecb_data.beneficiaryAccountNumber}.",
            source_bene_accno=ecb_data.beneficiaryAccountNumber,
            customer_full_name=None,
            location=ecb_data.location,  # Use location from ECBCaseData
            disputed_amount=ecb_data.disputedAmount,  # Use disputed amount from ECBCaseData
            created_by=created_by_user or "System"
        )

        if new_case_main_id is None:
            print(f"DEBUG: insert_into_case_main for {new_ack_no} returned None. {case_type} case not created.", flush=True)
            return None

        initial_history_data = {
            "remarks": ecb_data.remarks or f"{case_type} case generated.",
            "short_dn": case_type,
            "long_dn": f"Automated case created for {case_type} type.",
            "decision_type": "Automated Trigger",
            "updated_by": created_by_user or "System"
        }
        await save_or_update_decision(self.executor, new_case_main_id, initial_history_data)

        # Insert into case_details_1 for ECB case tracking
        async def _insert_ecb_case_details_1(cust_id, case_type, acc_no, created_by_user):
            def _sync_insert():
                with get_db_connection() as conn:
                    with get_db_cursor(conn) as cur:
                        cur.execute("""
                            INSERT INTO public.case_details_1 (
                                cust_id, casetype, acc_no, match_flag, creation_timestamp
                            )
                            VALUES (%s, %s, %s, %s, NOW())
                        """, (
                            cust_id,
                            case_type,
                            acc_no,
                            "ECB/ECBNT Match"
                        ))
                        conn.commit()
            await self._execute_sync_db_op(_sync_insert)

        await _insert_ecb_case_details_1(ecb_data.customerId, case_type, ecb_data.beneficiaryAccountNumber, created_by_user)

        return {
            "ack_no": new_ack_no,
            "case_id": new_case_main_id,
            "message": f"{case_type} case created successfully."
        }

    # NEW METHOD: Mobile Matching (MM) - Match customer and reverification_flags tables
    async def create_mobile_matching_cases(self) -> Dict[str, Any]:
        """
        Matches mobile numbers between customer and reverification_flags tables
        and creates MM cases for each match found.
        """
        def _sync_mobile_matching():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # Find matching mobile numbers between customer and reverification_flags
                    cur.execute("""
                        SELECT
                            c.cust_id,
                            c.fname,
                            c.lname,
                            c.mobile,
                            c.email,
                            c.pan,
                            rf.mobile_number,
                            rf.reason_flagged,
                            rf.flagged_date,
                            rf.sensitivity_index,
                            rf.distribution_details
                        FROM public.customer c
                        INNER JOIN public.reverification_flags rf ON c.mobile = rf.mobile_number
                        WHERE c.mobile IS NOT NULL
                        AND rf.mobile_number IS NOT NULL
                        AND LENGTH(TRIM(c.mobile)) > 0
                        AND LENGTH(TRIM(rf.mobile_number)) > 0
                    """)

                    matches = cur.fetchall()
                    return matches

        try:
            matches = await self._execute_sync_db_op(_sync_mobile_matching)

            if not matches:
                return {
                    "message": "No mobile number matches found between customer and reverification_flags tables.",
                    "matches_found": 0,
                    "cases_created": 0,
                    "matches": []
                }

            cases_created = []
            for match in matches:
                try:
                    # Create MM case (removed duplicate check - allow multiple MM cases per customer)
                    case_ack_no = f"MM_{match['cust_id']}_{uuid.uuid4().hex[:8].upper()}"

                    # Get customer full name
                    customer_full_name = f"{match.get('fname', '')} {match.get('lname', '')}".strip()
                    if not customer_full_name:
                        customer_full_name = match.get('cust_id', 'Unknown Customer')

                    new_case_main_id = await self.insert_into_case_main(
                        case_type='MM',
                        source_ack_no=case_ack_no,
                        cust_id=match['cust_id'],
                        acc_num=None,  # No specific account for MM cases
                        is_operational=False,  # Stage 2 case
                        status='New',
                        decision_input='Pending Review',
                        remarks_input=f"Mobile Matching Case: Customer {match['cust_id']} mobile {match['mobile']} matches reverification flag. Reason: {match.get('reason_flagged', 'N/A')}. Sensitivity: {match.get('sensitivity_index', 'N/A')}.",
                        customer_full_name=customer_full_name,
                        location=None,  # MM cases don't have location from data entry
                        disputed_amount=None,  # MM cases don't have disputed amount from data entry
                        created_by="System"
                    )

                    if new_case_main_id:
                        # Insert initial history
                        initial_history_data = {
                            "remarks": f"MM case created for mobile {match['mobile']} matching reverification flag.",
                            "short_dn": "Mobile Match",
                            "long_dn": f"Automated case created for mobile number matching. Customer: {customer_full_name}, Mobile: {match['mobile']}, Reason: {match.get('reason_flagged', 'N/A')}",
                            "decision_type": "Automated Trigger",
                            "updated_by": "System"
                        }
                        await save_or_update_decision(self.executor, new_case_main_id, initial_history_data)

                        # Insert into case_details_1 for MM case tracking
                        await self._insert_mm_case_details(
                            match['cust_id'],
                            match['mobile'],
                            match.get('reason_flagged'),
                            match.get('sensitivity_index'),
                            match.get('flagged_date')
                        )

                        cases_created.append({
                            "case_id": new_case_main_id,
                            "ack_no": case_ack_no,
                            "customer_id": match['cust_id'],
                            "mobile": match['mobile'],
                            "reason_flagged": match.get('reason_flagged'),
                            "sensitivity_index": match.get('sensitivity_index')
                        })

                        print(f"✅ MM case created: {case_ack_no} for customer {match['cust_id']} mobile {match['mobile']}")

                except Exception as e:
                    print(f"❌ Error creating MM case for customer {match['cust_id']}: {e}")
                    continue

            # Collect ECB cases created for summary
            total_ecb_cases = 0
            ecb_cases_summary = []
            
            for case in cases_created:
                # Get reverification data for this customer
                reverification_data = None
                for match in matches:
                    if match['cust_id'] == case['customer_id']:
                        reverification_data = {
                            'mobile_number': match['mobile'],
                            'reason_flagged': match.get('reason_flagged'),
                            'sensitivity_index': match.get('sensitivity_index'),
                            'tspname': match.get('tspname'),
                            'distribution_details': match.get('distribution_details'),
                            'flagged_date': match.get('flagged_date'),
                            'lsacode': match.get('lsacode')
                        }
                        break
                
                # Get ECB cases created for this customer with reverification data
                ecb_result = await self._create_ecb_cases_for_customer(case['customer_id'], f"Customer {case['customer_id']}", reverification_data)
                if ecb_result.get('ecb_cases_created', 0) > 0:
                    total_ecb_cases += ecb_result['ecb_cases_created']
                    ecb_cases_summary.extend(ecb_result.get('cases', []))

            return {
                "message": f"Mobile matching completed. Found {len(matches)} matches, created {len(cases_created)} MM cases and {total_ecb_cases} ECB cases.",
                "matches_found": len(matches),
                "mm_cases_created": len(cases_created),
                "ecb_cases_created": total_ecb_cases,
                "matches": matches,
                "mm_cases_details": cases_created,
                "ecb_cases_details": ecb_cases_summary
            }

        except Exception as e:
            print(f"❌ Error in mobile matching process: {e}")
            raise

    async def create_mobile_matching_cases_for_upload(self, upload_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Matches mobile numbers from the current upload only (not all stored flags)
        and creates MM cases for each match found.
        """
        # Extract mobile numbers from current upload
        upload_mobile_numbers = []
        for record in upload_records:
            if isinstance(record, dict) and record.get('mobile_number'):
                upload_mobile_numbers.append(record['mobile_number'])
        
        if not upload_mobile_numbers:
            return {
                "message": "No mobile numbers found in current upload.",
                "matches_found": 0,
                "mm_cases_created": 0,
                "ecb_cases_created": 0,
                "matches": [],
                "mm_cases_details": [],
                "ecb_cases_details": []
            }
        
        def _sync_mobile_matching_for_upload():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # Find matching mobile numbers between customer and ONLY the current upload
                    placeholders = ','.join(['%s'] * len(upload_mobile_numbers))
                    cur.execute(f"""
                        SELECT
                            c.cust_id,
                            c.fname,
                            c.lname,
                            c.mobile,
                            c.email,
                            c.pan,
                            rf.mobile_number,
                            rf.reason_flagged,
                            rf.flagged_date,
                            rf.sensitivity_index,
                            rf.distribution_details
                        FROM public.customer c
                        INNER JOIN public.reverification_flags rf ON c.mobile = rf.mobile_number
                        WHERE c.mobile IS NOT NULL
                        AND rf.mobile_number IS NOT NULL
                        AND LENGTH(TRIM(c.mobile)) > 0
                        AND LENGTH(TRIM(rf.mobile_number)) > 0
                        AND rf.mobile_number IN ({placeholders})
                    """, upload_mobile_numbers)

                    matches = cur.fetchall()
                    return matches

        try:
            matches = await self._execute_sync_db_op(_sync_mobile_matching_for_upload)

            if not matches:
                return {
                    "message": f"No mobile number matches found for the {len(upload_mobile_numbers)} mobile numbers in current upload.",
                    "matches_found": 0,
                    "mm_cases_created": 0,
                    "ecb_cases_created": 0,
                    "matches": [],
                    "mm_cases_details": [],
                    "ecb_cases_details": []
                }

            cases_created = []
            for match in matches:
                try:
                    # Create MM case (removed duplicate check - allow multiple MM cases per customer)
                    case_ack_no = f"MM_{match['cust_id']}_{uuid.uuid4().hex[:8].upper()}"

                    # Get customer full name
                    customer_full_name = f"{match.get('fname', '')} {match.get('lname', '')}".strip()
                    if not customer_full_name:
                        customer_full_name = match.get('cust_id', 'Unknown Customer')

                    new_case_main_id = await self.insert_into_case_main(
                        case_type='MM',
                        source_ack_no=case_ack_no,
                        cust_id=match['cust_id'],
                        acc_num=None,  # No specific account for MM cases
                        is_operational=False,  # Stage 2 case
                        status='New',
                        decision_input='Pending Review',
                        remarks_input=f"Mobile Matching Case: Customer {match['cust_id']} mobile {match['mobile']} matches reverification flag. Reason: {match.get('reason_flagged', 'N/A')}. Sensitivity: {match.get('sensitivity_index', 'N/A')}.",
                        customer_full_name=customer_full_name,
                        location=None,  # MM cases don't have location from data entry
                        disputed_amount=None,  # MM cases don't have disputed amount from data entry
                        created_by="System"
                    )

                    if new_case_main_id:
                        # Insert initial history
                        initial_history_data = {
                            "remarks": f"MM case created for mobile {match['mobile']} matching reverification flag.",
                            "short_dn": "Mobile Match",
                            "long_dn": f"Automated case created for mobile number matching. Customer: {customer_full_name}, Mobile: {match['mobile']}, Reason: {match.get('reason_flagged', 'N/A')}",
                            "decision_type": "Automated Trigger",
                            "updated_by": "System"
                        }
                        await save_or_update_decision(self.executor, new_case_main_id, initial_history_data)

                        # Insert into case_details_1 for MM case tracking
                        await self._insert_mm_case_details(
                            match['cust_id'],
                            match['mobile'],
                            match.get('reason_flagged'),
                            match.get('sensitivity_index'),
                            match.get('flagged_date')
                        )

                        cases_created.append({
                            "case_id": new_case_main_id,
                            "ack_no": case_ack_no,
                            "customer_id": match['cust_id'],
                            "mobile": match['mobile'],
                            "reason_flagged": match.get('reason_flagged'),
                            "sensitivity_index": match.get('sensitivity_index')
                        })

                        print(f"✅ MM case created: {case_ack_no} for customer {match['cust_id']} mobile {match['mobile']}")

                except Exception as e:
                    print(f"❌ Error creating MM case for customer {match['cust_id']}: {e}")
                    continue

            # Collect ECB cases created for summary
            total_ecb_cases = 0
            ecb_cases_summary = []
            
            for case in cases_created:
                # Get reverification data for this customer
                reverification_data = None
                for match in matches:
                    if match['cust_id'] == case['customer_id']:
                        reverification_data = {
                            'mobile_number': match['mobile'],
                            'reason_flagged': match.get('reason_flagged'),
                            'sensitivity_index': match.get('sensitivity_index'),
                            'tspname': match.get('tspname'),
                            'distribution_details': match.get('distribution_details'),
                            'flagged_date': match.get('flagged_date'),
                            'lsacode': match.get('lsacode')
                        }
                        break
                
                # Get ECB cases created for this customer with reverification data
                ecb_result = await self._create_ecb_cases_for_customer(case['customer_id'], f"Customer {case['customer_id']}", reverification_data)
                if ecb_result.get('ecb_cases_created', 0) > 0:
                    total_ecb_cases += ecb_result['ecb_cases_created']
                    ecb_cases_summary.extend(ecb_result.get('cases', []))

            return {
                "message": f"Mobile matching completed for current upload. Found {len(matches)} matches from {len(upload_mobile_numbers)} uploaded mobile numbers, created {len(cases_created)} MM cases and {total_ecb_cases} ECB cases.",
                "matches_found": len(matches),
                "mm_cases_created": len(cases_created),
                "ecb_cases_created": total_ecb_cases,
                "matches": matches,
                "mm_cases_details": cases_created,
                "ecb_cases_details": ecb_cases_summary
            }

        except Exception as e:
            print(f"❌ Error in mobile matching process for current upload: {e}")
            raise

    async def _check_existing_mm_case(self, cust_id: str) -> bool:
        """Check if an MM case already exists for this customer"""
        def _sync_check():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("""
                        SELECT case_id FROM public.case_main
                        WHERE cust_id = %s AND case_type = 'MM'
                        LIMIT 1
                    """, (cust_id,))
                    return cur.fetchone() is not None

        return await self._execute_sync_db_op(_sync_check)

    async def _insert_mm_case_details(self, cust_id: str, mobile: str, reason_flagged: str,
                                   sensitivity_index: str, flagged_date: date):
        """Insert MM case details into case_details_1 table"""
        def _sync_insert():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # Create match_flag string but ensure it fits within VARCHAR(20) limit
                    reason_short = (reason_flagged or 'N/A')[:8]  # Limit to 8 chars
                    sensitivity_short = (sensitivity_index or 'N/A')[:6]  # Limit to 6 chars
                    match_flag_text = f"MM-{reason_short}-{sensitivity_short}"

                    # Ensure total length doesn't exceed 20 characters
                    if len(match_flag_text) > 20:
                        match_flag_text = match_flag_text[:20]

                    cur.execute("""
                        INSERT INTO public.case_details_1 (
                            cust_id, casetype, mobile, email, pan, aadhar, acc_no,
                            card, match_flag, creation_timestamp
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        cust_id,
                        'MM',
                        mobile,
                        None,  # email
                        None,  # pan
                        None,  # aadhar
                        None,  # acc_no
                        None,  # card
                        match_flag_text
                    ))
                    conn.commit()

        await self._execute_sync_db_op(_sync_insert)

    async def _create_ecb_cases_for_customer(self, cust_id: str, customer_full_name: str, reverification_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        After MM case creation, check for ECBNT/ECBT cases by:
        1. Getting account numbers from account_customer table
        2. Finding matching beneficiary accounts in acc_bene table
        3. Checking for transactions between customer and beneficiary accounts
        4. Creating ECBNT (no transactions) or ECBT (with transactions) cases
        """
        try:
            # Step 1: Get customer account numbers
            customer_accounts = await self._get_customer_accounts(cust_id)
            if not customer_accounts:
                print(f"No accounts found for customer {cust_id}, skipping ECB case creation")
                return {"ecb_cases_created": 0, "message": "No customer accounts found"}

            ecb_cases_created = []
            
            for account in customer_accounts:
                cust_acct_num = account['acc_num']
                
                # Step 2: Find matching beneficiary accounts
                matching_beneficiaries = await self._find_matching_beneficiaries(cust_acct_num)
                
                for beneficiary in matching_beneficiaries:
                    bene_acct_num = beneficiary['bene_acct_num']
                    bene_name = beneficiary['bene_name']
                    
                    # Step 3: Check for transactions between customer and beneficiary
                    has_transactions = await self._check_customer_beneficiary_transactions(cust_acct_num, bene_acct_num)
                    
                    # Step 4: Create appropriate case type
                    if has_transactions:
                        case_type = 'ECBT'
                        base_description = f"Existing Customer with Transaction to Beneficiary: Customer {cust_id} (Account: {cust_acct_num}) has transactions with Beneficiary {bene_name} (Account: {bene_acct_num})"
                    else:
                        case_type = 'ECBNT'
                        base_description = f"Existing Customer with No Transaction to Beneficiary: Customer {cust_id} (Account: {cust_acct_num}) has beneficiary {bene_name} (Account: {bene_acct_num}) but no transactions"
                    
                    # Add reverification flags data if available
                    if reverification_data:
                        reverification_info = f" | Mobile Number Match: {reverification_data.get('mobile_number')} | Reason: {reverification_data.get('reason_flagged')} | Sensitivity: {reverification_data.get('sensitivity_index')} | TSP: {reverification_data.get('tspname')} | Details: {reverification_data.get('distribution_details')}"
                        case_description = base_description + reverification_info
                    else:
                        case_description = base_description
                    
                    # Create ECB case (removed duplicate check - allow multiple cases per customer/beneficiary)
                    case_ack_no = f"{case_type}_{cust_id}_{uuid.uuid4().hex[:8].upper()}"
                    
                    new_case_main_id = await self.insert_into_case_main(
                        case_type=case_type,
                        source_ack_no=case_ack_no,
                        cust_id=cust_id,
                        acc_num=cust_acct_num,
                        is_operational=False,  # Stage 2 case
                        status='New',
                        decision_input='Pending Review',
                        remarks_input=case_description,
                        customer_full_name=customer_full_name,
                        location=None,
                        disputed_amount=None,
                        created_by="System"
                    )
                    
                    if new_case_main_id:
                        # Insert initial history
                        initial_history_data = {
                            "remarks": f"{case_type} case created: Customer {cust_id} account {cust_acct_num} {'has' if has_transactions else 'no'} transactions with beneficiary {bene_name} account {bene_acct_num}",
                            "short_dn": case_type,
                            "long_dn": case_description,
                            "decision_type": "Automated Trigger",
                            "updated_by": "System"
                        }
                        await save_or_update_decision(self.executor, new_case_main_id, initial_history_data)
                        
                        # Insert into case_details_1 for ECB case tracking
                        await self._insert_ecb_case_details(
                            cust_id, cust_acct_num, bene_acct_num, bene_name, case_type, reverification_data
                        )
                        
                        ecb_cases_created.append({
                            "case_id": new_case_main_id,
                            "ack_no": case_ack_no,
                            "case_type": case_type,
                            "customer_id": cust_id,
                            "customer_account": cust_acct_num,
                            "beneficiary_account": bene_acct_num,
                            "beneficiary_name": bene_name,
                            "has_transactions": has_transactions
                        })
                        
                        print(f"✅ {case_type} case created: {case_ack_no} for customer {cust_id} account {cust_acct_num} and beneficiary {bene_acct_num}")
            
            return {
                "ecb_cases_created": len(ecb_cases_created),
                "cases": ecb_cases_created,
                "message": f"Created {len(ecb_cases_created)} ECB cases for customer {cust_id}"
            }
            
        except Exception as e:
            print(f"❌ Error creating ECB cases for customer {cust_id}: {e}")
            import traceback
            traceback.print_exc()
            return {"ecb_cases_created": 0, "error": str(e)}

    async def _get_customer_accounts(self, cust_id: str) -> List[Dict[str, Any]]:
        """Get all account numbers for a customer from account_customer table"""
        def _sync_get_accounts():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("""
                        SELECT acc_num, acc_name, rel_type, instructions
                        FROM public.account_customer
                        WHERE cust_id = %s
                    """, (cust_id,))
                    return cur.fetchall()
        
        accounts = await self._execute_sync_db_op(_sync_get_accounts)
        return [{"acc_num": acc['acc_num'], "acc_name": acc['acc_name'], "rel_type": acc['rel_type'], "instructions": acc['instructions']} for acc in accounts]

    async def _find_matching_beneficiaries(self, cust_acct_num: str) -> List[Dict[str, Any]]:
        """Find beneficiary accounts that match the customer account number"""
        def _sync_find_beneficiaries():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("""
                        SELECT bene_acct_num, bene_name, bene_bank_name, bene_status
                        FROM public.acc_bene
                        WHERE cust_acct_num = %s
                    """, (cust_acct_num,))
                    return cur.fetchall()
        
        beneficiaries = await self._execute_sync_db_op(_sync_find_beneficiaries)
        return [{"bene_acct_num": ben['bene_acct_num'], "bene_name": ben['bene_name'], "bene_bank_name": ben['bene_bank_name'], "bene_status": ben['bene_status']} for ben in beneficiaries]

    async def _check_customer_beneficiary_transactions(self, cust_acct_num: str, bene_acct_num: str) -> bool:
        """Check if there are any transactions between customer and beneficiary accounts"""
        def _sync_check_transactions():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("""
                        SELECT COUNT(*) as transaction_count
                        FROM public.txn
                        WHERE acct_num = %s AND bene_acct_num = %s
                        LIMIT 1
                    """, (cust_acct_num, bene_acct_num))
                    result = cur.fetchone()
                    return result['transaction_count'] > 0 if result else False
        
        return await self._execute_sync_db_op(_sync_check_transactions)

    async def _check_existing_ecb_case(self, cust_id: str, case_type: str, bene_acct_num: str) -> bool:
        """Check if an ECB case already exists for this customer and beneficiary combination"""
        def _sync_check():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("""
                        SELECT case_id FROM public.case_main
                        WHERE cust_id = %s AND case_type = %s
                        AND remarks LIKE %s
                        LIMIT 1
                    """, (cust_id, case_type, f"%{bene_acct_num}%"))
                    return cur.fetchone() is not None
        
        return await self._execute_sync_db_op(_sync_check)

    async def _insert_ecb_case_details(self, cust_id: str, cust_acct_num: str, bene_acct_num: str, 
                                     bene_name: str, case_type: str, reverification_data: Dict[str, Any] = None):
        """Insert ECB case details into case_details_1 table"""
        def _sync_insert():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # Create match_flag for ECB cases
                    if reverification_data:
                        # For MM-triggered ECB cases, include mobile number match info
                        mobile_short = reverification_data.get('mobile_number', '')[-4:]
                        match_flag_text = f"{case_type}-MM-{mobile_short}-{bene_acct_num[-4:]}"
                    else:
                        # For regular ECB cases
                        match_flag_text = f"{case_type}-{cust_acct_num[-4:]}-{bene_acct_num[-4:]}"
                    
                    cur.execute("""
                        INSERT INTO public.case_details_1 (
                            cust_id, casetype, mobile, email, pan, aadhar, acc_no,
                            card, match_flag, creation_timestamp
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        cust_id,
                        case_type,
                        None,  # mobile
                        None,  # email
                        None,  # pan
                        None,  # aadhar
                        cust_acct_num,  # acc_no
                        None,  # card
                        match_flag_text
                    ))
                    conn.commit()
        
        await self._execute_sync_db_op(_sync_insert)

    async def fetch_user_type(self, user_name: str) -> Optional[str]:
        """Cached version of fetch_user_type for better performance"""
        global USER_TYPE_CACHE
        
        cache_key = f"user_type_{user_name}"
        current_time = time_module.time()
        
        # Check cache first
        if cache_key in USER_TYPE_CACHE:
            cached_data = USER_TYPE_CACHE[cache_key]
            if is_cache_valid(cached_data['timestamp']):
                return cached_data['user_type']
        
        # Cache miss or expired, fetch from database
        def _sync_fetch_user_type():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("SELECT user_type FROM user_table WHERE user_name = %s", (user_name,))
                    result = cur.fetchone()
                    return result['user_type'] if result else None
        
        user_type = await self._execute_sync_db_op(_sync_fetch_user_type)
        
        # Cache the result
        USER_TYPE_CACHE[cache_key] = {
            'user_type': user_type,
            'timestamp': current_time
        }
        
        return user_type

    # FIX: Ensure this method is correctly defined inside CaseEntryMatcher
    async def update_case_main_data(self, case_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        def _sync_update_case_main_data():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # Check if case exists in case_main
                    cur.execute("SELECT case_id FROM public.case_main WHERE case_id = %s", (case_id,))
                    if not cur.fetchone():
                        raise CaseNotFoundError(f"Case with ID {case_id} not found in case_main for update.")

                    set_clauses = []
                    params = []
                    
                    db_column_map = {
                        "caseType": "case_type",
                        "sourceAckNo": "source_ack_no",
                        "sourceBeneAccno": "source_bene_accno",
                        "accNum": "acc_num",
                        "custId": "cust_id",
                        "isOperational": "is_operational",
                        "status": "status",
                        "decision_input": "decision",
                        "remarks_input": "remarks",
                        "assignedTo": "assigned_to",
                        "assignedBy": "assigned_by",
                        "reassignedFrom": "reassigned_from",
                        "reassignmentCount": "reassignment_count",
                        "shortDn": "short_dn",
                        "longDn": "long_dn",
                        "decisionType": "decision_type"
                    }

                    for fe_key, fe_value in update_data.items():
                        if fe_key in db_column_map:
                            db_col = db_column_map[fe_key]
                            set_clauses.append(f"{db_col} = %s")
                            # Explicitly convert boolean values
                            if db_col == "is_operational":
                                params.append(bool(fe_value))
                            elif db_col == "reassignment_count":
                                params.append(int(fe_value))
                            else:
                                params.append(fe_value)
                    
                    if not set_clauses:
                        raise ValueError("No valid fields provided for update.")

                    sql_query = f"""
                        UPDATE public.case_main
                        SET {", ".join(set_clauses)}
                        WHERE case_id = %s
                        RETURNING *;
                    """
                    params.append(case_id)

                    cur.execute(sql_query, tuple(params))
                    updated_record = cur.fetchone()
                    conn.commit()
                    return updated_record
        try:
            return await self._execute_sync_db_op(_sync_update_case_main_data)
        except CaseNotFoundError:
            raise
        except Exception as e:
            print(f"Error updating case_main for case_id {case_id}: {e}", flush=True)
            raise

    # UPDATED: fetch_dashboard_cases to query new case_main and assignment tables
    async def fetch_dashboard_cases(self, skip: int = 0, limit: int = 25, 
                                    search_ack_no: Optional[str] = None, # Note: this will now search source_ack_no
                                    status_filter: Optional[str] = None,
                                    current_logged_in_username: Optional[str] = None 
                                    ) -> List[Dict[str, Any]]:
        def _sync_fetch_dashboard_cases():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # FIX: Query new case_main and assignment tables
                    sql_query = """
                        SELECT
                            cm.source_ack_no AS ack_no, -- Alias source_ack_no to ack_no for frontend compatibility
                            cm.case_type AS complaint_type, -- Map case_type to complaint_type
                            cm.case_type AS match_type, -- Map case_type to match_type (Case Label)
                            cm.status,
                            cm.creation_time,
                            cm.creation_date AS created_on, -- Alias creation_date to created_on for frontend
                            a.assigned_to,
                            a.assigned_by
                        FROM public.case_main AS cm
                        LEFT JOIN public.assignment AS a ON cm.case_id = a.case_id
                    """
                    params = []
                    where_clauses = []

                    if search_ack_no:
                        # FIX: Search on source_ack_no in case_main
                        where_clauses.append("cm.source_ack_no ILIKE %s")
                        params.append(f"%{search_ack_no}%")

                    if status_filter:
                        # FIX: Filter on status in case_main
                        where_clauses.append("cm.status = %s")
                        params.append(status_filter)

                    # Role-based filtering logic using cached user_type
                    if current_logged_in_username:
                        user_type_from_db = None
                        # Use cached version for better performance
                        cache_key = f"user_type_{current_logged_in_username}"
                        if cache_key in USER_TYPE_CACHE and is_cache_valid(USER_TYPE_CACHE[cache_key]['timestamp']):
                            user_type_from_db = USER_TYPE_CACHE[cache_key]['user_type']
                        else:
                            # Fetch and cache
                            cur.execute("SELECT user_type FROM user_table WHERE user_name = %s", (current_logged_in_username,))
                            user_type_result = cur.fetchone()
                            if user_type_result:
                                user_type_from_db = user_type_result.get('user_type')
                                USER_TYPE_CACHE[cache_key] = {
                                    'user_type': user_type_from_db,
                                    'timestamp': time_module.time()
                                }

                        if user_type_from_db in ('CRO', 'super_user'):
                            pass # CROs and super_user see ALL cases.
                        elif user_type_from_db == 'risk_officer':
                            where_clauses.append("a.assigned_to = %s") # Filter by assigned_to in assignment table
                            params.append(current_logged_in_username)
                        elif user_type_from_db == 'others':
                            where_clauses.append("a.assigned_to = %s") # Filter by assigned_to in assignment table
                            params.append(current_logged_in_username)
                        else:
                            where_clauses.append("FALSE") # User not found or unhandled type, show nothing
                    else:
                        pass # Show all by default if no user is authenticated

                    if where_clauses:
                        sql_query += " WHERE " + " AND ".join(where_clauses)

                    sql_query += " ORDER BY cm.creation_date DESC, cm.creation_time DESC" # Order by new creation date/time
                    sql_query += f" LIMIT %s OFFSET %s"
                    params.append(limit)
                    params.append(skip)

                    cur.execute(sql_query, tuple(params))
                    return cur.fetchall()
        return await self._execute_sync_db_op(_sync_fetch_dashboard_cases)


    # This is a general method, now renamed to clearly indicate it fetches from NEW tables.
    async def fetch_new_cases_list(self, skip: int = 0, limit: int = 25,
                                   search_source_ack_no: Optional[str] = None,
                                   status_filter: Optional[str] = None,
                                   current_logged_in_username: Optional[str] = None,
                                   current_logged_in_user_type: Optional[str] = None
                                   ) -> List[Dict[str, Any]]:
        """
        Fetch cases for the new case list, with role-based filtering
        """
        def _sync_fetch_new_cases_list():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # Base query - simplified to avoid duplicates
                    base_query = """
                        SELECT DISTINCT
                            cm.case_id,
                            cm.case_type,
                            cm.source_ack_no,
                            cm.source_bene_accno,
                            cm.acc_num,
                            cm.cust_id,
                            cm.creation_date,
                            cm.creation_time,
                            cm.is_operational,
                            cm.status,
                            cm.short_dn,
                            cm.long_dn,
                            cm.decision_type,
                            cm.created_by,
                            cm.disputed_amount,
                            cm.location,
                            latest_assignment.assigned_to
                        FROM case_main cm
                        LEFT JOIN case_entry_form cef ON (
                            cef.ack_no = cm.source_ack_no 
                            OR cef.ack_no = SPLIT_PART(cm.source_ack_no, '_', 1)
                            OR cef.ack_no = SUBSTRING(cm.source_ack_no, 1, GREATEST(1, POSITION('_' IN cm.source_ack_no) - 1))
                        )
                        LEFT JOIN (
                            SELECT DISTINCT ON (case_id) 
                                case_id, 
                                assigned_to,
                                assign_date,
                                assign_time
                            FROM assignment 
                            WHERE COALESCE(is_active, TRUE) = TRUE
                            ORDER BY case_id, assign_date DESC, assign_time DESC
                        ) latest_assignment ON latest_assignment.case_id = cm.case_id
                    """
                    
                    where_clauses = []
                    params = []
                    
                    # Add search filter for source_ack_no
                    if search_source_ack_no:
                        where_clauses.append("cm.source_ack_no ILIKE %s")
                        params.append(f"%{search_source_ack_no}%")
                    
                    # Add status filter
                    if status_filter:
                        where_clauses.append("cm.status = %s")
                        params.append(status_filter)
                    
                    # Role-based filtering
                    if current_logged_in_username and current_logged_in_user_type:
                        if current_logged_in_user_type in ('CRO', 'super_user'):
                            pass  # CRO and super_user can see all cases
                        elif current_logged_in_user_type == 'risk_officer':
                            # Risk officer: show cases that are either:
                            # 1. Auto-assigned TO them (they can work on them)
                            # 2. Have no active assignments (unassigned cases)
                            # 3. Exclude cases they've manually assigned to others
                            try:
                                cur.execute("""
                                    SELECT 1 FROM information_schema.columns 
                                    WHERE table_schema = 'public' AND table_name = 'assignment' AND column_name = 'is_active'
                                """)
                                has_is_active = cur.fetchone() is not None
                            except Exception:
                                has_is_active = False

                            if has_is_active:
                                where_clauses.append("""
                                    (
                                        -- Cases auto-assigned TO this risk officer (any assignment type)
                                        latest_assignment.assigned_to = %s
                                        OR
                                        -- Cases with no active assignments (unassigned)
                                        latest_assignment.assigned_to IS NULL
                                    )
                                """)
                                params.append(current_logged_in_username)
                            else:
                                where_clauses.append("""
                                    (
                                        -- Cases auto-assigned TO this risk officer
                                        EXISTS (
                                            SELECT 1 FROM assignment a2 
                                            WHERE a2.case_id = cm.case_id 
                                            AND a2.assigned_to = %s
                                        )
                                        OR
                                        -- Cases with no assignments (unassigned)
                                        NOT EXISTS (
                                            SELECT 1 FROM assignment a3 
                                            WHERE a3.case_id = cm.case_id
                                        )
                                    )
                                    AND
                                    -- Exclude cases this risk officer has assigned to others
                                    NOT EXISTS (
                                        SELECT 1 FROM assignment a4
                                        WHERE a4.case_id = cm.case_id
                                        AND a4.assigned_by = %s
                                        AND a4.assigned_to != %s
                                    )
                                """)
                                params.extend([current_logged_in_username, current_logged_in_username, current_logged_in_username])
                        elif current_logged_in_user_type in ('others', 'supervisor'):
                            # Others can only see cases assigned to them - use a different query structure
                            base_query = """
                                SELECT DISTINCT
                                    cm.case_id,
                                    cm.case_type,
                                    cm.source_ack_no,
                                    cm.source_bene_accno,
                                    cm.acc_num,
                                    cm.cust_id,
                                    cm.creation_date,
                                    cm.creation_time,
                                    cm.is_operational,
                                    cm.status,
                                    cm.short_dn,
                                    cm.long_dn,
                                    cm.decision_type,
                                    cm.created_by,
                                    a.assigned_to,
                                    a.assigned_by,
                                    cm.disputed_amount,
                                    cm.location
                                FROM case_main cm
                                INNER JOIN assignment a ON cm.case_id = a.case_id AND a.assigned_to = %s
                                LEFT JOIN case_entry_form cef ON (
                                    cef.ack_no = cm.source_ack_no 
                                    OR cef.ack_no = SPLIT_PART(cm.source_ack_no, '_', 1)
                                    OR cef.ack_no = SUBSTRING(cm.source_ack_no, 1, GREATEST(1, POSITION('_' IN cm.source_ack_no) - 1))
                                )
                            """
                            params.insert(0, current_logged_in_username)
                        else:
                            where_clauses.append("FALSE")  # Unknown user type
                    else:
                        pass  # No user info, show all cases
                    
                    # Combine where clauses
                    if where_clauses:
                        base_query += " WHERE " + " AND ".join(where_clauses)
                    
                    # Add ordering and pagination
                    base_query += """
                        ORDER BY cm.creation_date DESC, cm.creation_time DESC
                        LIMIT %s OFFSET %s
                    """
                    params.extend([limit, skip])
                    
                    cur.execute(base_query, params)
                    rows = cur.fetchall()
                    
                    return [dict(row) for row in rows]
        
        return await self._execute_sync_db_op(_sync_fetch_new_cases_list)

    # NEW METHOD: Fetch detailed case info from new tables (for /api/new-case-details/{case_id})
    async def fetch_new_case_details(self, case_id: int) -> Optional[Dict[str, Any]]:
        def _sync_fetch_new_case_details():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    sql_query = """
                        SELECT
                            cm.*, -- Select all columns from case_main
                            a.assigned_to, a.assigned_by, a.assign_date, a.assign_time, -- From assignment
                            d.remarks AS decision_remarks, d.short_dn, d.long_dn, d.decision_type, d.decision_by, d.created_time AS decision_created_time -- From new decision table
                        FROM public.case_main AS cm
                        LEFT JOIN public.assignment AS a ON cm.case_id = a.case_id
                        LEFT JOIN public.case_history AS d ON cm.case_id = d.case_id -- Use case_history
                        WHERE cm.case_id = %s
                    """
                    cur.execute(sql_query, (case_id,))
                    result = cur.fetchone()
                    return result
        
        try:
            return await self._execute_sync_db_op(_sync_fetch_new_case_details)
        except CaseNotFoundError:
            raise
        except Exception as e:
            print(f"Error fetching new case details for ID {case_id}: {e}", flush=True)
            raise

    # OPTIMIZED METHOD: Fetch combined case data with fewer queries using JOINs
    async def fetch_combined_case_data_optimized(self, case_id: int) -> Optional[Dict[str, Any]]:
        """Optimized version using fewer database queries with JOINs"""
        def _sync_fetch_combined_data_optimized():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # Single query to get most data with JOINs
                    main_query = """
                        SELECT 
                            -- Case main data
                            cm.case_id, cm.case_type, cm.source_ack_no, cm.source_bene_accno,
                            cm.acc_num, cm.cust_id, cm.creation_date, cm.creation_time, 
                            cm.is_operational, cm.status, cm.short_dn, cm.long_dn, cm.decision_type,
                            
                            -- Customer data
                            c.fname, c.mname, c.lname, c.mobile, c.email, c.pan, c.nat_id, 
                            c.dob, c.citizen, c.occupation, c.seg, c.cust_type, c.risk_prof, 
                            c.kyc_status, c.cust_creation_date, c.rel_value,
                            
                            -- Account data
                            a.acc_name, a.acc_type, a.acc_status, a.open_date, a.branch_code,
                            a.currency, a.balance, a.prod_code, a.min_bal, a.od_limit, 
                            a.credit_score, a.aqb, a.interest_rate, a.last_txn_date
                            
                        FROM public.case_main cm
                        LEFT JOIN customer c ON cm.cust_id = c.cust_id
                        LEFT JOIN account a ON cm.acc_num = a.acc_num
                        WHERE cm.case_id = %s
                    """
                    
                    cur.execute(main_query, (case_id,))
                    main_result = cur.fetchone()
                    
                    if not main_result:
                        raise CaseNotFoundError(f"Case with ID {case_id} not found in case_main.")
                    
                    combined_case_data = dict(main_result)
                    
                    # Extract key values for additional queries
                    source_ack_no_from_case_main = main_result.get('source_ack_no')
                    main_acc_num = main_result.get('acc_num')
                    source_bene_accno = main_result.get('source_bene_accno')
                    
                    # Calculate MOB if customer creation date is available
                    if main_result.get('cust_creation_date'):
                        today = date.today()
                        creation_date = main_result.get('cust_creation_date')
                        delta = today - creation_date
                        combined_case_data['mob'] = round(delta.days / 30)
                    else:
                        combined_case_data['mob'] = None
                    
                    # Separate customer and account details for frontend compatibility
                    customer_fields = ['fname', 'mname', 'lname', 'mobile', 'email', 'pan', 'nat_id', 
                                     'dob', 'citizen', 'occupation', 'seg', 'cust_type', 'risk_prof', 
                                     'kyc_status', 'cust_creation_date', 'rel_value', 'mob']
                    
                    account_fields = ['acc_name', 'acc_type', 'acc_status', 'open_date', 'branch_code',
                                    'currency', 'balance', 'prod_code', 'min_bal', 'od_limit', 
                                    'credit_score', 'aqb', 'interest_rate', 'last_txn_date']
                    
                    combined_case_data['customer_details'] = {k: main_result.get(k) for k in customer_fields if k in main_result}
                    combined_case_data['account_details'] = {k: main_result.get(k) for k in account_fields if k in main_result}
                    
                    # Get I4C data (if needed)
                    if source_ack_no_from_case_main:
                        original_ack_no_for_i4c = source_ack_no_from_case_main
                        case_type_suffixes = ['_VM', '_BM', '_ECBT', '_ECBNT', '_NAB', '_PSA', '_PMA', '_PVA', '_NAA']
                        
                        for suffix in case_type_suffixes:
                            if source_ack_no_from_case_main.endswith(suffix):
                                original_ack_no_for_i4c = source_ack_no_from_case_main[:-len(suffix)]
                                break
                        
                        cur.execute("""
                            SELECT ack_no, customer_name, sub_category, transaction_date, complaint_date, 
                                   report_datetime, state, district, policestation, payment_mode, 
                                   account_number, card_number, transaction_id, layers, transaction_amount, 
                                   disputed_amount, action, to_bank, to_account, ifsc, to_transaction_id, 
                                   to_amount, action_taken_date, to_upi_id
                            FROM case_entry_form
                            WHERE ack_no = %s
                        """, (original_ack_no_for_i4c,))
                        
                        combined_case_data['i4c_data'] = cur.fetchone()
                    
                    # Get transactions, history, assignments, and documents in parallel-style queries
                    # Transactions
                    if main_acc_num or source_bene_accno:
                        tx_acc_nums = [acc for acc in [main_acc_num, source_bene_accno] if acc]
                        if tx_acc_nums:
                            cur.execute("""
                                SELECT acct_num, txn_date, txn_time, txn_type, amount, descr, 
                                       txn_ref, currency, bene_name, bene_acct_num, pay_method, channel
                                FROM txn
                                WHERE acct_num IN %s
                                ORDER BY txn_date DESC, txn_time DESC
                                LIMIT 100
                            """, (tuple(tx_acc_nums),))
                            transactions = cur.fetchall()
                            
                            # Add bene match indicator
                            for txn in transactions:
                                txn['is_bene_match'] = (txn.get('bene_acct_num') == source_bene_accno)
                            
                            combined_case_data['transactions'] = transactions
                        else:
                            combined_case_data['transactions'] = []
                    else:
                        combined_case_data['transactions'] = []
                    
                    # Case history
                    cur.execute("""
                        SELECT remarks, updated_by, created_time
                        FROM public.case_history
                        WHERE case_id = %s
                        ORDER BY created_time DESC
                    """, (case_id,))
                    combined_case_data['decision_history'] = cur.fetchall()
                    
                    # Assignment history
                    cur.execute("""
                        SELECT assigned_to, assigned_by, assign_date, assign_time
                        FROM public.assignment
                        WHERE case_id = %s
                        ORDER BY assign_date DESC, assign_time DESC
                    """, (case_id,))
                    combined_case_data['assignment_history'] = cur.fetchall()
                    
                    # Documents
                    cur.execute("""
                        SELECT id, document_type, original_filename, file_location, 
                               uploaded_by, comment, uploaded_at, file_mime_type
                        FROM public.case_documents
                        WHERE case_id = %s
                        ORDER BY uploaded_at DESC
                    """, (case_id,))
                    combined_case_data['uploaded_documents'] = cur.fetchall()
                    
                    # NEW: For MM, ECBNT, and ECBT cases, fetch reverification flags data
                    case_type = main_result.get('case_type')
                    mobile_number = main_result.get('mobile')
                    print(f"DEBUG: fetch_combined_case_data_optimized - Case Type: {case_type}, Mobile: {mobile_number}", flush=True)
                    
                    if case_type in ['MM', 'ECBNT', 'ECBT'] and mobile_number:
                        print(f"DEBUG: fetch_combined_case_data_optimized - Fetching reverification flags for mobile: {mobile_number} (type: {type(mobile_number)})", flush=True)
                        
                        # First, let's check what mobile numbers exist in reverification_flags table
                        cur.execute("SELECT mobile_number FROM public.reverification_flags LIMIT 10")
                        existing_mobiles = cur.fetchall()
                        print(f"DEBUG: fetch_combined_case_data_optimized - Existing mobile numbers in reverification_flags: {[row['mobile_number'] for row in existing_mobiles]}", flush=True)
                        
                        cur.execute("""
                            SELECT 
                                mobile_number,
                                reason_flagged,
                                flagged_date,
                                lsacode,
                                tspname,
                                sensitivity_index,
                                distribution_details
                            FROM public.reverification_flags
                            WHERE mobile_number = %s
                        """, (mobile_number,))
                        
                        reverification_data = cur.fetchone()
                        print(f"DEBUG: fetch_combined_case_data_optimized - Reverification data found: {reverification_data}", flush=True)
                        
                        if reverification_data:
                            combined_case_data['reverification_flags'] = reverification_data
                            print(f"DEBUG: fetch_combined_case_data_optimized - Added reverification flags to response", flush=True)
                        else:
                            combined_case_data['reverification_flags'] = {
                                'mobile_number': 'N/A',
                                'reason_flagged': 'N/A',
                                'flagged_date': 'N/A',
                                'lsacode': 'N/A',
                                'tspname': 'N/A',
                                'sensitivity_index': 'N/A',
                                'distribution_details': 'N/A'
                            }
                            print(f"DEBUG: fetch_combined_case_data_optimized - No reverification data found, set to N/A", flush=True)
                    else:
                        # For non-mobile matching cases, set reverification fields to N/A
                        combined_case_data['reverification_flags'] = {
                            'mobile_number': 'N/A',
                            'reason_flagged': 'N/A',
                            'flagged_date': 'N/A',
                            'lsacode': 'N/A',
                            'tspname': 'N/A',
                            'sensitivity_index': 'N/A',
                            'distribution_details': 'N/A'
                        }
                        print(f"DEBUG: fetch_combined_case_data_optimized - Not a mobile matching case, set to N/A", flush=True)
                    
                    return combined_case_data

        try:
            return await self._execute_sync_db_op(_sync_fetch_combined_data_optimized)
        except CaseNotFoundError:
            raise
        except Exception as e:
            print(f"Error fetching optimized combined case data for case_id {case_id}: {e}", flush=True)
            raise

    # NEW METHOD: Fetch combined case data from various tables
    async def fetch_combined_case_data(self, case_id: int) -> Optional[Dict[str, Any]]:
        def _sync_fetch_combined_data():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    combined_case_data = {}

                    # 1. Fetch base case details from case_main
                    cur.execute("""
                        SELECT
                            case_id, case_type, source_ack_no, source_bene_accno,
                            acc_num, cust_id, creation_date, creation_time, is_operational, status,
                            short_dn, long_dn, decision_type -- NEW: Add new columns from case_main
                        FROM public.case_main
                        WHERE case_id = %s
                    """, (case_id,))
                    case_main_data = cur.fetchone()
                    if not case_main_data:
                        raise CaseNotFoundError(f"Case with ID {case_id} not found in case_main.")
                    combined_case_data.update(case_main_data)

                    source_ack_no_from_case_main = case_main_data.get('source_ack_no')
                    main_cust_id = case_main_data.get('cust_id')
                    main_acc_num = case_main_data.get('acc_num')
                    source_bene_accno = case_main_data.get('source_bene_accno')

                    # 2. Fetch I4C data from case_entry_form (linked by source_ack_no)
                    original_ack_no_for_i4c = None
                    if source_ack_no_from_case_main:
                        # FIXED: Derive the original ACK No by stripping ALL case type suffixes
                        # Handle all possible case type suffixes: _VM, _BM, _ECBT, _ECBNT, _NAB, _PSA, _PMA, _PVA, etc.
                        case_type_suffixes = ['_VM', '_BM', '_ECBT', '_ECBNT', '_NAB', '_PSA', '_PMA', '_PVA', '_NAA']
                        original_ack_no_for_i4c = source_ack_no_from_case_main
                        
                        for suffix in case_type_suffixes:
                            if source_ack_no_from_case_main.endswith(suffix):
                                original_ack_no_for_i4c = source_ack_no_from_case_main[:-len(suffix)]
                                print(f"DEBUG: Combined Data - Found suffix '{suffix}', removing it", flush=True)
                                break

                        print(f"DEBUG: Combined Data - Derived original ACK for i4c_data: '{original_ack_no_for_i4c}' from source_ack_no: '{source_ack_no_from_case_main}'", flush=True)

                        cur.execute("""
                            SELECT
                                ack_no, customer_name, sub_category, transaction_date, complaint_date, report_datetime,
                                state, district, policestation, payment_mode, account_number, card_number,
                                transaction_id, layers, transaction_amount, disputed_amount, action,
                                to_bank, to_account, ifsc, to_transaction_id, to_amount, action_taken_date,
                                to_upi_id
                            FROM case_entry_form
                            WHERE ack_no = %s
                        """, (original_ack_no_for_i4c,))  # Use the derived original ACK No
                        i4c_data = cur.fetchone()
                        if i4c_data:
                            combined_case_data['i4c_data'] = i4c_data
                            print(f"DEBUG: Combined Data - Found i4c_data for original ACK: '{original_ack_no_for_i4c}'", flush=True)
                        else:
                            combined_case_data['i4c_data'] = None
                            print(f"DEBUG: Combined Data - No i4c_data found in case_entry_form for original ACK: '{original_ack_no_for_i4c}'", flush=True)
                            
                            # Additional debug: Check if any records exist with similar ACK patterns
                            cur.execute("""
                                SELECT ack_no FROM case_entry_form 
                                WHERE ack_no LIKE %s 
                                LIMIT 5
                            """, (f"%{original_ack_no_for_i4c.split('_')[0]}%",))
                            similar_acks = cur.fetchall()
                            print(f"DEBUG: Combined Data - Similar ACKs found: {[row['ack_no'] for row in similar_acks]}", flush=True)

                    # 3. Fetch customer details (victim/primary)
                    customer_data = None
                    if main_cust_id:
                        cur.execute("""
                            SELECT cust_id, fname, mname, lname, mobile, email, pan, nat_id, dob, citizen, occupation, seg, cust_type, risk_prof, kyc_status, cust_creation_date, rel_value
                            FROM customer WHERE cust_id = %s
                        """, (main_cust_id,))
                        customer_data = cur.fetchone()

                    # NEW: Calculate MOB if customer_data is available
                    if customer_data and customer_data.get('cust_creation_date'):
                        today = date.today()
                        creation_date = customer_data.get('cust_creation_date')
                        delta = today - creation_date
                        mob_value = round(delta.days / 30) # Calculate months
                        customer_data['mob'] = mob_value
                    else:
                        if customer_data: # If customer_data exists but date is missing, add mob as None
                            customer_data['mob'] = None
                        else: # If customer_data is None entirely, initialize it to add mob
                            customer_data = {'mob': None}

                    combined_case_data['customer_details'] = customer_data

                    # NEW: For MM, ECBNT, and ECBT cases, fetch reverification flags data
                    case_type = case_main_data.get('case_type')
                    mobile_number = customer_data.get('mobile') if customer_data else None
                    print(f"DEBUG: fetch_combined_case_data - Case Type: {case_type}, Mobile: {mobile_number}", flush=True)
                    
                    if case_type in ['MM', 'ECBNT', 'ECBT'] and customer_data and mobile_number:
                        print(f"DEBUG: fetch_combined_case_data - Fetching reverification flags for mobile: {mobile_number} (type: {type(mobile_number)})", flush=True)
                        
                        # First, let's check what mobile numbers exist in reverification_flags table
                        cur.execute("SELECT mobile_number FROM public.reverification_flags LIMIT 10")
                        existing_mobiles = cur.fetchall()
                        print(f"DEBUG: fetch_combined_case_data - Existing mobile numbers in reverification_flags: {[row['mobile_number'] for row in existing_mobiles]}", flush=True)
                        
                        cur.execute("""
                            SELECT 
                                mobile_number,
                                reason_flagged,
                                flagged_date,
                                lsacode,
                                tspname,
                                sensitivity_index,
                                distribution_details
                            FROM public.reverification_flags
                            WHERE mobile_number = %s
                        """, (mobile_number,))
                        
                        reverification_data = cur.fetchone()
                        print(f"DEBUG: fetch_combined_case_data - Reverification data found: {reverification_data}", flush=True)
                        
                        if reverification_data:
                            combined_case_data['reverification_flags'] = reverification_data
                            print(f"DEBUG: fetch_combined_case_data - Added reverification flags to response", flush=True)
                        else:
                            combined_case_data['reverification_flags'] = {
                                'mobile_number': 'N/A',
                                'reason_flagged': 'N/A',
                                'flagged_date': 'N/A',
                                'lsacode': 'N/A',
                                'tspname': 'N/A',
                                'sensitivity_index': 'N/A',
                                'distribution_details': 'N/A'
                            }
                            print(f"DEBUG: fetch_combined_case_data - No reverification data found, set to N/A", flush=True)
                    else:
                        # For non-MM cases, set reverification fields to N/A
                        combined_case_data['reverification_flags'] = {
                            'mobile_number': 'N/A',
                            'reason_flagged': 'N/A',
                            'flagged_date': 'N/A',
                            'lsacode': 'N/A',
                            'tspname': 'N/A',
                            'sensitivity_index': 'N/A',
                            'distribution_details': 'N/A'
                        }
                        print(f"DEBUG: fetch_combined_case_data - Not a mobile matching case, set to N/A", flush=True)

                    # 4. Fetch account details (primary account from case_main)
                    account_details = []
                    # FIX: Add debug prints here
                    print(f"DEBUG: Combined Data - Processing case_id {case_id}. acc_num from case_main: '{main_acc_num}'", flush=True) 
                    if main_acc_num:
                        try: # FIX: Add try-except around account query to catch specific errors
                            cur.execute("""
                                SELECT acc_num, acc_name, acc_type, acc_status, open_date, branch_code, currency, balance, prod_code, min_bal, od_limit, credit_score, aqb, interest_rate, last_txn_date
                                FROM public.account WHERE acc_num = %s
                            """, (main_acc_num,))
                            account_details = cur.fetchone()
                            print(f"DEBUG: Combined Data - Account query result for '{main_acc_num}': {account_details}", flush=True)
                        except Exception as e:
                            print(f"ERROR: Combined Data - Failed to query account table for '{main_acc_num}': {e}", flush=True)
                            # Do not re-raise, just log and account_details will remain None
                    else:
                        print(f"DEBUG: Combined Data - main_acc_num from case_main is NULL/empty for case_id {case_id}. Skipping account details fetch.", flush=True)

                    combined_case_data['account_details'] = account_details

                    # 5. Fetch transaction details (based on acc_num and source_bene_accno)
                    transactions = []
                    tx_acc_nums_to_check = []
                    if main_acc_num: tx_acc_nums_to_check.append(main_acc_num)
                    if source_bene_accno and source_bene_accno != main_acc_num: tx_acc_nums_to_check.append(source_bene_accno)

                    if tx_acc_nums_to_check:
                        cur.execute("""
                            SELECT acct_num, txn_date, txn_time, txn_type, amount, descr, txn_ref, currency, bene_name, bene_acct_num, pay_method, channel
                            FROM txn
                            WHERE acct_num IN %s
                            ORDER BY txn_date DESC, txn_time DESC
                        """, (tuple(tx_acc_nums_to_check),))
                        transactions = cur.fetchall()
                    # Add indicator for matching bene_acct_num
                    for txn in transactions:
                        txn['is_bene_match'] = (txn.get('bene_acct_num') == source_bene_accno)
                    combined_case_data['transactions'] = transactions

                    # 6. Fetch decision history from the new 'case_history' table
                    cur.execute("""
                        SELECT remarks, updated_by, created_time
                        FROM public.case_history -- Use case_history table
                        WHERE case_id = %s
                        ORDER BY created_time DESC
                    """, (case_id,))
                    decision_history = cur.fetchall()
                    combined_case_data['decision_history'] = decision_history

                    # 7. Fetch assignment history from the new 'assignment' table
                    cur.execute("""
                        SELECT assigned_to, assigned_by, assign_date, assign_time
                        FROM public.assignment
                        WHERE case_id = %s
                        ORDER BY assign_date DESC, assign_time DESC
                    """, (case_id,))
                    assignment_history = cur.fetchall()
                    combined_case_data['assignment_history'] = assignment_history

                    # 8. Fetch documents from the new 'case_documents' table (using integer case_id)
                    uploaded_documents = []
                    cur.execute("""
                        SELECT id, document_type, original_filename, file_location, uploaded_by, comment, uploaded_at, file_mime_type
                        FROM public.case_documents
                        WHERE case_id = %s
                        ORDER BY uploaded_at DESC
                    """, (case_id,)) # case_documents.case_id is now integer
                    uploaded_documents = cur.fetchall()
                    combined_case_data['uploaded_documents'] = uploaded_documents

                    return combined_case_data

        # Use optimized version for better performance
        try:
            return await self.fetch_combined_case_data_optimized(case_id)
        except Exception as e:
            print(f"Error in optimized fetch, falling back to original method: {e}", flush=True)
            # Fallback to original implementation if optimized version fails
            try:
                return await self._execute_sync_db_op(_sync_fetch_combined_data)
            except CaseNotFoundError:
                raise
            except Exception as e:
                print(f"Error fetching combined case data for case_id {case_id}: {e}", flush=True)
                raise

    # NEW METHOD: Fetch customer details for a case by ACK No (now uses CaseEntryMatcher)
    async def fetch_case_customer_details(self, ack_no: str) -> Optional[Dict[str, Any]]:
        def _sync_fetch_case_customer_details():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # First, get the case_main record by case_id (int) or source_ack_no (str)
                    case_main_query = """
                        SELECT case_id, source_ack_no, cust_id, acc_num
                        FROM public.case_main
                        WHERE case_id = %s OR source_ack_no = %s
                    """
                    cur.execute(case_main_query, (ack_no, ack_no))
                    cm_data = cur.fetchone()

                    if not cm_data:
                        raise CaseNotFoundError(f"Case {ack_no} not found in case_main.")

                    main_cust_id = cm_data.get('cust_id')
                    main_acc_num = cm_data.get('acc_num')

                    # Join case_main with customer table to get full customer details for the primary customer ID
                    cur.execute("""
                        SELECT
                            cm.case_id,             -- Include case_id
                            cm.case_type,
                            cm.source_ack_no,
                            cm.source_bene_accno,
                            cm.acc_num,
                            cm.cust_id,
                            cm.creation_date,
                            cm.creation_time,
                            cm.is_operational,
                            cm.status,
                            cm.short_dn,            -- New field
                            cm.long_dn,             -- New field
                            cm.decision_type,       -- New field
                            -- Customer details from the 'customer' table
                            c.gender,
                            c.mobile,
                            c.email,
                            c.pan,
                            c.nat_id,
                            c.dob,
                            c.citizen,
                            c.occupation,
                            c.seg,
                            c.cust_type AS customer_db_type, -- Alias to avoid conflict with cm.case_type
                            c.risk_prof,
                            c.kyc_status,
                            c.cust_creation_date,
                            c.rel_value
                        FROM public.case_main AS cm
                        LEFT JOIN public.customer AS c ON cm.cust_id = c.cust_id
                        WHERE cm.case_id = %s
                    """, (cm_data.get('case_id'),))
                    
                    case_data = cur.fetchone() 
                    
                    if not case_data:
                        raise CaseNotFoundError(f"Case data for case_id {cm_data.get('case_id')} not retrieved after join.")

                    # NEW: Calculate MOB (Months On Book)
                    if case_data.get('cust_creation_date'):
                        today = date.today()
                        creation_date = case_data.get('cust_creation_date')
                        delta = today - creation_date
                        mob_value = round(delta.days / 30) # Calculate months
                        case_data['mob'] = mob_value
                    else:
                        case_data['mob'] = None # Set to None if cust_creation_date is missing

                    # NEW: For MM, ECBNT, and ECBT cases, fetch reverification flags data
                    case_type = case_data.get('case_type')
                    mobile_number = case_data.get('mobile')
                    print(f"DEBUG: fetch_case_customer_details - Case Type: {case_type}, Mobile: {mobile_number}", flush=True)
                    
                    if case_type in ['MM', 'ECBNT', 'ECBT'] and mobile_number:
                        print(f"DEBUG: fetch_case_customer_details - Fetching reverification flags for mobile: {mobile_number} (type: {type(mobile_number)})", flush=True)
                        
                        # First, let's check what mobile numbers exist in reverification_flags table
                        cur.execute("SELECT mobile_number FROM public.reverification_flags LIMIT 10")
                        existing_mobiles = cur.fetchall()
                        print(f"DEBUG: fetch_case_customer_details - Existing mobile numbers in reverification_flags: {[row['mobile_number'] for row in existing_mobiles]}", flush=True)
                        
                        cur.execute("""
                            SELECT 
                                mobile_number,
                                reason_flagged,
                                flagged_date,
                                lsacode,
                                tspname,
                                sensitivity_index,
                                distribution_details
                            FROM public.reverification_flags
                            WHERE mobile_number = %s
                        """, (mobile_number,))
                        
                        reverification_data = cur.fetchone()
                        print(f"DEBUG: fetch_case_customer_details - Reverification data found: {reverification_data}", flush=True)
                        
                        if reverification_data:
                            # Add reverification flags data to case_data
                            case_data.update({
                                'flagged_mobile': reverification_data.get('mobile_number'),
                                'reason_flagged': reverification_data.get('reason_flagged'),
                                'flagged_date': reverification_data.get('flagged_date'),
                                'lsacode': reverification_data.get('lsacode'),
                                'tspname': reverification_data.get('tspname'),
                                'sensitivity_index': reverification_data.get('sensitivity_index'),
                                'distribution_details': reverification_data.get('distribution_details')
                            })
                            print(f"DEBUG: fetch_case_customer_details - Updated case_data with reverification flags", flush=True)
                        else:
                            # Set default values if no reverification data found
                            case_data.update({
                                'flagged_mobile': 'N/A',
                                'reason_flagged': 'N/A',
                                'flagged_date': 'N/A',
                                'lsacode': 'N/A',
                                'tspname': 'N/A',
                                'sensitivity_index': 'N/A',
                                'distribution_details': 'N/A'
                            })
                            print(f"DEBUG: fetch_case_customer_details - No reverification data found, set to N/A", flush=True)
                    else:
                        # For non-mobile matching cases, set reverification fields to N/A
                        case_data.update({
                            'flagged_mobile': 'N/A',
                            'reason_flagged': 'N/A',
                            'flagged_date': 'N/A',
                            'lsacode': 'N/A',
                            'tspname': 'N/A',
                            'sensitivity_index': 'N/A',
                            'distribution_details': 'N/A'
                        })
                        print(f"DEBUG: fetch_case_customer_details - Not a mobile matching case, set to N/A", flush=True)

                    return case_data # This will be a dictionary with combined data
        
        try:
            return await self._execute_sync_db_op(_sync_fetch_case_customer_details)
        except CaseNotFoundError:
            raise # Re-raise for router to handle as 404
        except Exception as e:
            print(f"Error fetching case customer details for ACK {ack_no}: {e}", flush=True)
            raise

    # NEW METHOD: Fetch single case details from case_main by integer case_id
    async def fetch_single_case_details_from_case_main_by_case_id(self, case_id: int) -> Optional[Dict[str, Any]]:
        def _sync_fetch():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("""
                        SELECT case_id, source_ack_no, case_type, status, is_operational, acc_num, cust_id, source_bene_accno
                        FROM public.case_main WHERE case_id = %s
                    """, (case_id,))
                    return cur.fetchone()
        try:
            return await self._execute_sync_db_op(_sync_fetch)
        except Exception as e:
            print(f"Error fetching case_main details by Case ID {case_id}: {e}", flush=True)
            raise

    # UPDATED: fetch_case_risk_profile to correctly handle case_id (int) OR ack_no (str)
    async def fetch_case_risk_profile(self, case_id_or_ack_no: Union[int, str]) -> Dict[str, Optional[Dict[str, Any]]]:
        def _sync_fetch_case_risk_profile():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # FIX: Build WHERE clause dynamically based on input type
                    case_main_select_query = """
                        SELECT case_id, source_ack_no, cust_id, acc_num, source_bene_accno
                        FROM public.case_main
                    """
                    query_params = []

                    if isinstance(case_id_or_ack_no, int):
                        case_main_select_query += " WHERE case_id = %s"
                        query_params.append(case_id_or_ack_no)
                    elif isinstance(case_id_or_ack_no, str):
                        case_main_select_query += " WHERE source_ack_no = %s"
                        query_params.append(case_id_or_ack_no)
                    else:
                        raise ValueError(f"Invalid type for case_id_or_ack_no: {type(case_id_or_ack_no)}. Expected int or str.")


                    cur.execute(case_main_select_query, tuple(query_params)) # Execute with the dynamic query/params
                    cm_data = cur.fetchone()

                    if not cm_data:
                        raise CaseNotFoundError(f"Case {case_id_or_ack_no} not found in case_main.")
                    
                    case_id = cm_data.get('case_id') # Ensure we get the integer case_id for subsequent lookups
                    primary_cust_id = cm_data.get('cust_id')
                    primary_acc_num = cm_data.get('acc_num')
                    beneficiary_acc_num = cm_data.get('source_bene_accno')

                    # Nested helper function to get entity profile (customer + account)
                    def get_entity_profile_sync(current_cur, cust_id: Optional[str], acc_num: Optional[str]):
                        customer = None
                        account = None

                        if cust_id:
                            current_cur.execute("""
                                SELECT
                                    c.cust_id, CONCAT_WS(' ', c.fname, c.mname, c.lname) AS full_name,
                                    c.dob, c.nat_id, c.pan, c.citizen, c.occupation, c.seg, c.cust_type,
                                    c.risk_prof, c.kyc_status, c.mobile, c.email
                                FROM public.customer c
                                WHERE c.cust_id = %s
                            """, (cust_id,))
                            customer = current_cur.fetchone()

                        if acc_num:
                            current_cur.execute("""
                                SELECT
                                    a.acc_num AS account_number, a.acc_name, a.acc_type, a.acc_status,
                                    a.open_date, a.balance, a.last_txn_date, a.credit_score
                                FROM public.account a
                                WHERE a.acc_num = %s
                            """, (acc_num,))
                            account = current_cur.fetchone()

                        if not customer and not account:
                            return None
                        
                        return {**(customer or {}), **(account or {})}

                    # Fetch victim profile using primary customer/account from case_main
                    victim_profile = get_entity_profile_sync(cur, primary_cust_id, primary_acc_num)
                    # Fetch beneficiary profile using beneficiary account from case_main (source_bene_accno)
                    beneficiary_profile = get_entity_profile_sync(cur, None, beneficiary_acc_num)

                    return {
                        "victim": victim_profile,
                        "beneficiary": beneficiary_profile
                    }
        try:
            return await self._execute_sync_db_op(_sync_fetch_case_risk_profile)
        except CaseNotFoundError:
            raise
        except Exception as e:
            print(f"Error in fetch_case_risk_profile for {case_id_or_ack_no}: {e}", flush=True)
            raise


    # UPDATED METHOD: Insert Operational Confirmation Summary (Fixing JSONB structure)
    async def insert_operational_confirmation_summary(self, executor: ThreadPoolExecutor, 
                                                    case_id: int, 
                                                    case_ack_no: str, 
                                                    document_statuses_json: List[str], # FIX: Renamed parameter to reflect it's List[str]
                                                    proof_of_upload_ref: str, 
                                                    confirmation_boolean_overall: bool, 
                                                    created_by_user: str,
                                                    screenshot_file_location: Optional[str] = None,
                                                    remarks: Optional[str] = None 
                                                    ) -> Dict[str, Any]:
        # FIX: Define the sync function correctly
        def _sync_insert_summary(case_id: int, case_ack_no: str, document_statuses_json: str, screenshot_file_location: Optional[str], confirmation_boolean_overall: bool, created_by_user: str, proof_of_upload_ref: str):
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    new_record = None
                    try: 
                        print(f"DEBUG: _sync_insert_summary - Attempting INSERT for case_id {case_id}, ref_no: {proof_of_upload_ref}", flush=True) 
                        print(f"DEBUG: _sync_insert_summary - JSONB data to insert: {document_statuses_json}", flush=True)

                        # First check if the table exists
                        cur.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name = 'operational_confirmation'
                            );
                        """)
                        table_exists_result = cur.fetchone()
                        # RealDictCursor returns a dict, so we need to access the first (and only) value
                        table_exists = list(table_exists_result.values())[0] if table_exists_result else False
                        print(f"DEBUG: operational_confirmation table exists: {table_exists}", flush=True)
                        
                        if not table_exists:
                            raise ValueError("operational_confirmation table does not exist")
                        
                        # Check table structure
                        cur.execute("""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'operational_confirmation'
                            ORDER BY ordinal_position;
                        """)
                        columns = cur.fetchall()
                        print(f"DEBUG: operational_confirmation table columns: {columns}", flush=True)
                        
                        if not columns:
                            print(f"DEBUG: No columns found for operational_confirmation table", flush=True)
                            raise ValueError("operational_confirmation table has no columns or doesn't exist")
                        
                        # Check if case_id exists in case_main
                        cur.execute("SELECT case_id FROM public.case_main WHERE case_id = %s", (case_id,))
                        case_exists_result = cur.fetchone()
                        case_exists = case_exists_result is not None
                        print(f"DEBUG: Case {case_id} exists in case_main: {case_exists}", flush=True)
                        
                        if not case_exists:
                            raise ValueError(f"Case {case_id} does not exist in case_main table")
                        
                        print(f"DEBUG: About to execute INSERT with params: case_id={case_id}, case_ack_no={case_ack_no}, ref_no={proof_of_upload_ref}, doc_json={document_statuses_json}, screenshot={screenshot_file_location}, confirmation={confirmation_boolean_overall}, created_by={created_by_user}", flush=True)
                        
                        # Convert the JSON string to proper JSONB format
                        import json
                        if isinstance(document_statuses_json, str):
                            # If it's already a string, parse it to ensure it's valid JSON
                            try:
                                json.loads(document_statuses_json)
                                jsonb_data = document_statuses_json
                            except json.JSONDecodeError:
                                raise ValueError(f"Invalid JSON string: {document_statuses_json}")
                        else:
                            # If it's a list, convert to JSON string
                            jsonb_data = json.dumps(document_statuses_json)
                        
                        print(f"DEBUG: Final JSONB data for insert: {jsonb_data}", flush=True)
                        
                        cur.execute(
                            """
                            INSERT INTO public.operational_confirmation (case_id, case_ack_no, ref_no, document_statuses_json, screenshot_file_location, confirmation_boolean, created_by, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                            RETURNING id;
                            """,
                            (case_id, case_ack_no, proof_of_upload_ref, jsonb_data, screenshot_file_location, confirmation_boolean_overall, created_by_user)
                        )
                        print(f"DEBUG: _sync_insert_summary - INSERT query executed. About to fetchone.", flush=True) 
                        
                        new_record = cur.fetchone() 
                        print(f"DEBUG: _sync_insert_summary - Fetched record: {new_record}", flush=True) 
                        
                        conn.commit() 
                        print(f"DEBUG: _sync_insert_summary - Transaction committed.", flush=True) 

                        print(f"✅ Operational confirmation summary recorded for case_id {case_id} (Ref: {proof_of_upload_ref}). Record ID: {new_record.get('id') if new_record else 'None'}", flush=True) 
                        
                    except psycopg2.Error as e:
                        conn.rollback() 
                        print(f"❌ DATABASE ERROR in _sync_insert_summary for case_id {case_id}: PGCODE: {e.pgcode} PGERROR: '{e.pgerror}'", flush=True) 
                        raise ValueError(f"DB Error recording operational confirmation: {e.pgerror}") 
                    except Exception as e:
                        conn.rollback() 
                        print(f"❌ UNEXPECTED ERROR in _sync_insert_summary for case_id {case_id}: {e}", flush=True)
                        print(f"❌ ERROR TYPE: {type(e)}", flush=True)
                        print(f"❌ ERROR ARGS: {e.args}", flush=True)
                        import traceback
                        print(f"❌ TRACEBACK: {traceback.format_exc()}", flush=True)
                        raise ValueError(f"Unexpected error recording operational confirmation: {e}")
                    
                    # --- Case Status Update Logic ---
                    # Update case status based on confirmation_boolean_overall
                    new_status = 'Closed' if confirmation_boolean_overall else 'Open'
                    print(f"DEBUG: Setting case {case_ack_no} (ID: {case_id}) to '{new_status}' based on confirmation_boolean_overall: {confirmation_boolean_overall}", flush=True)
                    try: 
                        # Update status and set closing_date if case is being closed
                        if confirmation_boolean_overall:
                            cur.execute(
                                """
                                UPDATE public.case_main
                                SET status = %s, is_operational = %s, closing_date = CURRENT_DATE
                                WHERE case_id = %s;
                                """,
                                (new_status, True, case_id)
                            )
                        else:
                            cur.execute(
                                """
                                UPDATE public.case_main
                                SET status = %s, is_operational = %s
                                WHERE case_id = %s;
                                """,
                                (new_status, True, case_id)
                            )
                        rows_affected = cur.rowcount
                        conn.commit() 
                        if rows_affected > 0:
                            print(f"✅ Case {case_ack_no} in case_main updated to '{new_status}' and is_operational=TRUE. Rows affected: {rows_affected}", flush=True)
                            if confirmation_boolean_overall:
                                print(f"✅ Case {case_ack_no} closing_date set to CURRENT_DATE", flush=True)
                        else:
                            print(f"⚠️ Case {case_ack_no} in case_main not found for status update after confirmation.", flush=True)
                    except Exception as e:
                        conn.rollback() 
                        print(f"❌ ERROR updating case_main status for case_id {case_id}: {e}", flush=True)
                        raise ValueError(f"DB Error updating case status: {e}")
                    
                    return new_record 
        
        # Prepare the data for _sync_insert_summary here, OUTSIDE the inner sync function.
        try:
            jsonb_data_string_for_insert = json.dumps(document_statuses_json)
            return await self._execute_sync_db_op(_sync_insert_summary, 
                                              case_id, case_ack_no, jsonb_data_string_for_insert, screenshot_file_location, 
                                              confirmation_boolean_overall, created_by_user, proof_of_upload_ref)
        except ValueError: 
            raise 
        except Exception as e:
            print(f"UNEXPECTED ERROR in insert_operational_confirmation_summary wrapper for case_id {case_id}: {e}", flush=True)
            raise 


    #def insert_operational_confirmation(self,  executor: ThreadPoolExecutor, case_id: int, case_ack_no: str, document_statuses_json: list[dict[str, bool]], screenshot_file_location: Optional[str], confirmation_boolean_overall: bool, created_by_user: str, proof_of_upload_ref: str):
    #    with get_db_connection() as conn:
    #        with get_db_cursor(conn) as cur:
    #           new_record = None
    #            try: 
    #                print(f"DEBUG: _sync_insert_summary - Attempting INSERT for case_id {case_id}, ref_no: {proof_of_upload_ref}", flush=True) 
    #                print(f"DEBUG: _sync_insert_summary - JSONB data to insert: {document_statuses_json}", flush=True)

    #                cur.execute(
    #                    """
    #                    INSERT INTO public.operational_confirmation (case_id, case_ack_no, ref_no, document_statuses_json, screenshot_file_location, confirmation_boolean, created_by, created_at)
    #                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
    #                    RETURNING id, case_id, case_ack_no, ref_no, document_statuses_json, screenshot_file_location, confirmation_boolean, created_by, created_at;
    #                    """,
    #                    (case_id, case_ack_no, proof_of_upload_ref, document_statuses_json, screenshot_file_location, confirmation_boolean_overall, created_by_user)
    #                )
    #                print(f"DEBUG: _sync_insert_summary - INSERT query executed. About to fetchone.", flush=True) 
    #                    
    #                new_record = cur.fetchone() 
    #                print(f"DEBUG: _sync_insert_summary - Fetched record: {new_record}", flush=True) 
    #                    
    #                conn.commit() 
    #                print(f"DEBUG: _sync_insert_summary - Transaction committed.", flush=True)

    #                print(f"✅ Operational confirmation summary recorded for case_id {case_id} (Ref: {proof_of_upload_ref}). Record ID: {new_record.get('id') if new_record else 'None'}", flush=True) 
                        
    #           except psycopg2.Error as e:
    #                conn.rollback() 
    #                print(f"❌ DATABASE ERROR in _sync_insert_summary for case_id {case_id}: PGCODE: {e.pgcode} PGERROR: '{e.pgerror}'", flush=True) 
    #                raise ValueError(f"DB Error recording operational confirmation: {e.pgerror}") 
    #            except Exception as e:
    #                conn.rollback() 
    #                print(f"❌ UNEXPECTED ERROR in _sync_insert_summary for case_id {case_id}: {e}", flush=True)
    #                raise ValueError(f"Unexpected error recording operational confirmation: {e}")
                    
    #            # --- Case Closure Logic ---
    #            if confirmation_boolean_overall: 
    #                print(f"DEBUG: Setting case {case_ack_no} (ID: {case_id}) to 'Closed' and is_operational=TRUE based on overall confirmation.", flush=True)
    #                try: 
    #                    cur.execute(
    #                        """
    #                        UPDATE public.case_main
    #                        SET status = %s, is_operational = %s
    #                        WHERE case_id = %s;
    #                        """,
    #                        ('Closed', True, case_id)
    #                    )
    #                    rows_affected = cur.rowcount
    #                    conn.commit() 
    #                    if rows_affected > 0:
    #                        print(f"✅ Case {case_ack_no} in case_main updated to 'Closed' and is_operational=TRUE. Rows affected: {rows_affected}", flush=True)
    #                    else:
    #                        print(f"⚠️ Case {case_ack_no} in case_main not found for status update after confirmation.", flush=True)
    #                except Exception as e:
    #                    conn.rollback() 
    #                    print(f"❌ ERROR updating case_main status for case_id {case_id}: {e}", flush=True)
    #                    raise ValueError(f"DB Error updating case status: {e}")
                    
    #            return new_record 
    #    try: 
    #        return self._execute_sync_db_op(_sync_insert_summary, 
    #                                            case_id, case_ack_no, json.dumps(document_statuses_json), screenshot_file_location, 
    #                                            confirmation_boolean_overall, created_by_user, proof_of_upload_ref) # Pass actual remarks param here
    #    except ValueError: 
    #        raise
    #    except Exception as e:
    #        print(f"UNEXPECTED ERROR in insert_operational_confirmation_summary wrapper for case_id {case_id}: {e}", flush=True)
    #        raise


    async def fetch_backend_users(self, department_name: Optional[str] = None) -> List[Dict[str, str]]:
            def _sync_fetch_users():
                with get_db_connection() as conn:
                    with get_db_cursor(conn) as cur:
                        sql_query = "SELECT user_id, user_name, dept FROM public.user_table" # Removed user_type if not needed for name formatting
                        params = []
                        where_clauses = []

                        # Always exclude supervisors from the assignment dropdown
                        where_clauses.append("user_type != %s")
                        params.append("supervisor")

                        if department_name:
                        # Directly use the provided department_name as it should match the DB 'dept' value
                            where_clauses.append("dept = %s")
                            params.append(department_name) # No mapping needed here

                        if where_clauses:
                            sql_query += " WHERE " + " AND ".join(where_clauses)
                    
                        sql_query += " ORDER BY user_name;"

                        cur.execute(sql_query, tuple(params))
                        raw_users = cur.fetchall()

                        formatted_users = []
                        for user_row in raw_users:
                            user_id = user_row.get('user_id')
                            user_id_str = str(user_id) if user_id is not None else "UNKNOWN_ID"
                        
                            user_name_display = user_row.get('user_name', 'Unknown User')
                        
                            formatted_users.append({
                                "id": user_id_str,
                                "name": user_name_display
                            })
                        return formatted_users
            try:
                return await self._execute_sync_db_op(_sync_fetch_users)
            except Exception as e:
                print(f"Error fetching backend users: {e}", flush=True)
                raise

    # MODIFIED: fetch_departments_data to use DB department names directly
    async def fetch_departments_data(self) -> List[Dict[str, str]]:
        def _sync_fetch_departments():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # Select distinct 'dept' values from user_table
                    cur.execute("SELECT DISTINCT dept FROM public.user_table WHERE dept IS NOT NULL ORDER BY dept;")
                    raw_departments = cur.fetchall()

                    departments = []
                    for row in raw_departments:
                        dept_name_raw = row.get('dept')
                        if dept_name_raw:
                            # Just use the raw department name from DB
                            departments.append({"name": dept_name_raw})
                    return departments
        try:
            return await self._execute_sync_db_op(_sync_fetch_departments)
        except Exception as e:
            print(f"Error fetching departments data from DB: {e}", flush=True)
            raise

    async def fetch_operational_confirmation_log(self, case_id: int) -> Optional[Dict[str, Any]]:
        def _sync_fetch_log():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # Fetch the latest operational confirmation for the given case_id
                    cur.execute("""
                        SELECT
                            id,
                            case_id,
                            case_ack_no,
                            file_name, -- Not used directly, but good to fetch if needed later
                            confirmation_boolean,
                            created_at,
                            created_by,
                            ref_no,
                            document_statuses_json,
                            screenshot_file_location
                        FROM public.operational_confirmation
                        WHERE case_id = %s
                        ORDER BY created_at DESC
                        LIMIT 1;
                    """, (case_id,))
                    raw_log = cur.fetchone()

                    if not raw_log:
                        return None

                    # Get user_type/dept for submitted_by formatting
                    submitted_by_user_name = raw_log.get('created_by')
                    submitted_by_display = submitted_by_user_name # Default
                    if submitted_by_user_name:
                        cur.execute("SELECT user_type, dept FROM public.user_table WHERE user_name = %s", (submitted_by_user_name,))
                        user_info = cur.fetchone()
                        if user_info:
                            user_type_db = user_info.get('user_type')
                            user_dept_db = user_info.get('dept')

                            if user_dept_db:
                                # Prioritize department if available
                                submitted_by_display = f"{submitted_by_user_name} - {user_dept_db.replace('_', ' ').title()}"
                            elif user_type_db:
                                # Fallback to user type
                                submitted_by_display = f"{submitted_by_user_name} - {user_type_db.replace('_', ' ').title()}"
                            # If neither, just use the raw username

                    # Extract filename from the full path and get document ID
                    screenshot_filename = None
                    screenshot_document_id = None
                    if raw_log.get('screenshot_file_location'):
                        screenshot_filename = os.path.basename(raw_log['screenshot_file_location'])
                        
                        # Get the document ID for the screenshot
                        cur.execute("""
                            SELECT id FROM public.case_documents 
                            WHERE case_id = %s AND file_location = %s
                            ORDER BY uploaded_at DESC LIMIT 1
                        """, (case_id, raw_log['screenshot_file_location']))
                        doc_result = cur.fetchone()
                        if doc_result:
                            screenshot_document_id = doc_result.get('id')

                    # Determine confirmation_action_status based on confirmation_boolean
                    confirmation_status = "submitted" if raw_log.get('confirmation_boolean') else "pending" # Adjust logic if more statuses exist

                    # Parse document_statuses_json. It's already a list of strings in your example row.
                    checked_documents = raw_log.get('document_statuses_json', [])
                    # The example response has "Account Statement", "KYC (Know Your Customer)", "65B Certificate"
                    # Your DB has "Account Details", "Branch Details", "Lien Details".
                    # We'll use your DB values. If you need a mapping, define it here.
                    # For example:
                    # mapped_documents = []
                    # for doc in checked_documents:
                    #     if doc == "Account Details": mapped_documents.append("Account Statement")
                    #     elif doc == "KYC": mapped_documents.append("KYC (Know Your Customer)")
                    #     # ...
                    # checked_documents = mapped_documents


                    formatted_log = {
                        "checked_documents": checked_documents, # Directly use as it's List[str]
                        "proof_of_upload_ref": raw_log.get('ref_no'),
                        "screenshot_filename": screenshot_filename,
                        "screenshot_document_id": screenshot_document_id, # Document ID for download
                        "confirmation_action_status": confirmation_status,
                        "submitted_by": submitted_by_display, # Formatted name
                        "submitted_at": raw_log.get('created_at') # datetime object, Pydantic will format to ISO 8601
                    }
                    return formatted_log
        try:
            return await self._execute_sync_db_op(_sync_fetch_log)
        except Exception as e:
            print(f"Error fetching operational confirmation log for case_id {case_id}: {e}", flush=True)
            raise
    # NEW METHOD: Insert I4C manual file confirmation into i4c_manual_file_list
    async def insert_i4c_manual_file_confirmation(self, executor: ThreadPoolExecutor, seq_id: int, file_name: str, file_description: Optional[str], sent_by_user: str) -> Dict[str, Any]:
        def _sync_insert_confirmation():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute(
                        """
                        INSERT INTO public.i4c_manual_file_list (seq_id, file_name, file_description, sent_by, sent_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        RETURNING id, seq_id, file_name, sent_at; -- Return relevant fields
                        """,
                        (seq_id, file_name, file_description, sent_by_user)
                    )
                    new_record = cur.fetchone()
                    conn.commit()
                    return new_record
            try:
                return self._execute_sync_db_op(_sync_insert_confirmation)
            except Exception as e:
                print(f"Error inserting I4C manual file confirmation: {e}", flush=True)
                raise

    async def get_case_id_from_ack_no(self, ack_no: str) -> Optional[int]:
        def _sync_get_case_id():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("SELECT case_id FROM case_main WHERE source_ack_no = %s", (ack_no,))
                    row = cur.fetchone()
                    return row['case_id'] if row else None
        return await self._execute_sync_db_op(_sync_get_case_id)

    async def fetch_assigned_cases(self, skip: int = 0, limit: int = 25,
                                   search_source_ack_no: Optional[str] = None,
                                   status_filter: Optional[str] = None,
                                   assigned_by_username: Optional[str] = None
                                   ) -> List[Dict[str, Any]]:
        """
        Fetch cases that have been assigned by a specific user (for review purposes)
        OPTIMIZED VERSION: Eliminates N+1 queries and expensive JOINs
        """
        def _sync_fetch_assigned_cases():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # OPTIMIZED: Single query with JOIN to get all assignment data at once
                    # Removed expensive LEFT JOIN with case_entry_form (not used in results)
                    base_query = """
                        SELECT 
                            cm.case_id,
                            cm.case_type,
                            cm.source_ack_no,
                            cm.source_bene_accno,
                            cm.acc_num,
                            cm.cust_id,
                            cm.creation_date,
                            cm.creation_time,
                            cm.is_operational,
                            cm.status,
                            cm.short_dn,
                            cm.long_dn,
                            cm.decision_type,
                            cm.created_by,
                            cm.disputed_amount,
                            cm.location,
                            -- Get all assigned users for this case in one go
                            STRING_AGG(DISTINCT a.assigned_to, ', ' ORDER BY a.assigned_to) as assigned_to,
                            MAX(a.assign_date) as assign_date,
                            MAX(a.assign_time) as assign_time
                        FROM case_main cm
                        INNER JOIN assignment a ON cm.case_id = a.case_id
                        WHERE COALESCE(a.assignment_type, 'manual') IN ('manual', 'template')
                        AND COALESCE(a.is_active, TRUE) = TRUE
                    """
                    
                    where_clauses = []
                    params = []
                    
                    # Add search filter for source_ack_no
                    if search_source_ack_no:
                        where_clauses.append("cm.source_ack_no ILIKE %s")
                        params.append(f"%{search_source_ack_no}%")
                    
                    # Add status filter
                    if status_filter:
                        where_clauses.append("cm.status = %s")
                        params.append(status_filter)
                    
                    # Role-based filtering - show cases assigned by the current user
                    if assigned_by_username:
                        where_clauses.append("a.assigned_by = %s")
                        params.append(assigned_by_username)
                        
                        # CRITICAL: Only show cases that haven't been routed back
                        where_clauses.append("a.assigned_to != %s")
                        params.append(assigned_by_username)
                    
                    # Combine where clauses
                    if where_clauses:
                        base_query += " AND " + " AND ".join(where_clauses)
                    
                    # Group by case fields and add ordering/pagination
                    base_query += """
                        GROUP BY cm.case_id, cm.case_type, cm.source_ack_no, cm.source_bene_accno,
                                cm.acc_num, cm.cust_id, cm.creation_date, cm.creation_time,
                                cm.is_operational, cm.status, cm.short_dn, cm.long_dn,
                                cm.decision_type, cm.created_by, cm.disputed_amount, cm.location
                        ORDER BY cm.creation_date DESC, cm.creation_time DESC
                        LIMIT %s OFFSET %s
                    """
                    params.extend([limit, skip])
                    
                    cur.execute(base_query, params)
                    rows = cur.fetchall()
                    
                    # Convert rows to list of dictionaries
                    cases = [dict(row) for row in rows]
                    
                    return cases
        
        return await self._execute_sync_db_op(_sync_fetch_assigned_cases)

    # BULK PROCESSING OPTIMIZATIONS
    async def bulk_process_account_lookups(self, records: List[Dict]) -> Dict[str, str]:
        """
        Bulk lookup all victim and beneficiary accounts in single queries.
        Returns mapping of account_number -> customer_id for performance optimization.
        """
        def _sync_bulk_account_lookup():
            account_numbers = set()
            for record in records:
                if record.get('accountNumber'):
                    account_numbers.add(str(record['accountNumber']))
                if record.get('toAccount'):
                    account_numbers.add(str(record['toAccount']))
            
            if not account_numbers:
                return {}
                
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # Single query to fetch all account lookups
                    placeholders = ','.join(['%s'] * len(account_numbers))
                    cur.execute(
                        f"SELECT acc_num, cust_id FROM account_customer WHERE acc_num IN ({placeholders})",
                        list(account_numbers)
                    )
                    results = cur.fetchall()
                    return {row['acc_num']: row['cust_id'] for row in results}
        
        return await self._execute_sync_db_op(_sync_bulk_account_lookup)
    
    async def bulk_insert_cases(self, case_data_list: List[Dict]) -> List[int]:
        """
        Bulk insert multiple cases in a single transaction for better performance.
        """
        def _sync_bulk_insert():
            if not case_data_list:
                return []
                
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    case_ids = []
                    try:
                        for case_data in case_data_list:
                            cur.execute("""
                                INSERT INTO public.case_main (
                                    case_type, source_ack_no, cust_id, acc_num, source_bene_accno,
                                    is_operational, status, creation_date, creation_time,
                                    short_dn, long_dn, decision_type, location, disputed_amount, created_by
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s, 
                                       (NOW() AT TIME ZONE 'Asia/Kolkata')::date, 
                                       (NOW() AT TIME ZONE 'Asia/Kolkata')::time, 
                                       %s, %s, %s, %s, %s, %s)
                                RETURNING case_id;
                            """, (
                                case_data['case_type'], case_data['source_ack_no'], 
                                case_data.get('cust_id'), case_data.get('acc_num'), 
                                case_data.get('source_bene_accno'), case_data.get('is_operational', True),
                                case_data.get('status', 'New'), case_data.get('short_dn', 'N/A'),
                                case_data.get('long_dn', ''), case_data.get('decision_type', 'N/A'),
                                case_data.get('location'), case_data.get('disputed_amount'),
                                case_data.get('created_by', 'System')
                            ))
                            case_id = cur.fetchone()['case_id']
                            case_ids.append(case_id)
                        
                        conn.commit()
                        print(f"✅ Bulk inserted {len(case_ids)} cases successfully")
                        return case_ids
                    except Exception as e:
                        conn.rollback()
                        print(f"❌ Bulk insert failed: {e}")
                        raise
        
        return await self._execute_sync_db_op(_sync_bulk_insert)
    
    async def bulk_check_transactions(self, vm_bm_pairs: List[Dict]) -> Dict[str, bool]:
        """
        Bulk check for transactions between victim and beneficiary accounts.
        Returns mapping of (vm_acc, bm_acc) -> has_transaction for ECB case creation.
        """
        def _sync_bulk_transaction_check():
            if not vm_bm_pairs:
                return {}
                
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    results = {}
                    for pair in vm_bm_pairs:
                        vm_acc = pair['vm_acc']
                        bm_acc = pair['bm_acc']
                        from_date = pair['from_date']
                        to_date = pair['to_date']
                        
                        cur.execute("""
                            SELECT COUNT(*) FROM public.txn
                            WHERE acct_num = %s AND bene_acct_num = %s
                              AND txn_date BETWEEN %s AND %s;
                        """, (vm_acc, bm_acc, from_date, to_date))
                        
                        count = cur.fetchone()['count']
                        results[f"{vm_acc}_{bm_acc}"] = count > 0
                    
                    return results
        
        return await self._execute_sync_db_op(_sync_bulk_transaction_check)


# --- DatabaseMatcher Class (Currently not used for new table logic, can be removed if desired) ---
class DatabaseMatcher:
    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor

    async def _execute_sync_db_op(self, func, *args, **kwargs):
        return await asyncio.get_running_loop().run_in_executor(self.executor, func, *args, **kwargs)

def log_case_action(case_id: int, user_name: str, action: str, details: str = None):
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO case_logs (case_id, user_name, action, details, created_at)
                    VALUES (%s, %s, %s, %s, (NOW() AT TIME ZONE 'Asia/Kolkata'))
                    """,
                    (case_id, user_name, action, details)
                )
            conn.commit()
    except Exception as e:
        print(f"Error logging case action: {e}")