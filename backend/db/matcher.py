# db/matcher.py
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime, time # Added datetime, time for new table defaults
from typing import Dict, Any, List, Optional, Union, Annotated
import json
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
import random
import uuid
import re
import asyncpg

from .connection import get_db_connection, get_db_cursor
# Ensure all necessary models are imported from base_models.py
from models.base_models import CaseEntryData, I4CData, TransactionData, BeneficiaryData, PotentialSuspectAccountData, CaseMainUpdateData, ECBCaseData
from config import DB_CONNECTION_PARAMS, ERROR_LOG_DIR # Ensure ERROR_LOG_DIR is defined in config.py

from fastapi import UploadFile

class CaseNotFoundError(Exception):
    pass

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

                cur.execute(
                    f"""
                    INSERT INTO public.case_history ({insert_cols_str})
                    VALUES ({insert_placeholders_str})
                    ON CONFLICT (case_id) DO UPDATE SET
                        {update_set_str}
                    RETURNING *;
                    """,
                    tuple(db_values_list)
                )
                
                updated_decision_record = cur.fetchone()
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

    # FIX: Correct definition of _execute_sync_db_op
    # It should NOT take 'executor' as an argument, it uses self.executor
    async def _execute_sync_db_op(self, func, *args, **kwargs):
        return await asyncio.get_running_loop().run_in_executor(self.executor, func, *args, **kwargs)

    # UPDATED METHOD: insert_into_case_main
    # UPDATED METHOD: insert_into_case_main (new system's primary case table)
    # This helper is called by match_data, create_nab_case_if_flagged, create_psa_case_if_flagged
    async def insert_into_case_main(self, case_type: str, source_ack_no: str, cust_id: Optional[str] = None,
                                    acc_num: Optional[str] = None, source_bene_accno: Optional[str] = None,
                                    is_operational: bool = False, status: str = 'New',
                                    decision_input: Optional[str] = None, # Renamed to avoid confusion with column
                                    remarks_input: Optional[str] = None, # Renamed to avoid confusion with column
                                    customer_full_name: Optional[str] = None # Accepts customer_full_name
                                    ) -> int:
        def _sync_insert():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    actual_short_dn = customer_full_name or "N/A" # Derived from customer_full_name
                    actual_long_dn = remarks_input or ""           # Derived from remarks_input
                    actual_decision_type = decision_input or "N/A"  # Derived from decision_input

                    try:
                        cur.execute("""
                            INSERT INTO public.case_main (
                                case_type, source_ack_no, cust_id, acc_num, source_bene_accno,
                                is_operational, status, creation_date, creation_time,
                                short_dn, long_dn, decision_type
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, CURRENT_TIME, %s, %s, %s)
                            RETURNING case_id;
                        """, (
                            case_type, source_ack_no, cust_id, acc_num, source_bene_accno,
                            is_operational, status,
                            actual_short_dn, actual_long_dn, actual_decision_type # Pass values for the correct columns
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
            return await self._execute_sync_db_op(_sync_insert)
        except ValueError:
            raise
        except Exception as e:
            print(f"UNEXPECTED ERROR in insert_into_case_main wrapper for '{source_ack_no}': {e}", flush=True)
            raise


    # UPDATED METHOD: match_data (for POST /api/case-entry) - Implements new VM/BM/No-Match flow
    async def match_data(self, data: CaseEntryData, evidence_file: Optional[UploadFile] = None):
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
                    customer_full_name=data.customerName
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
                    customer_full_name=data.customerName
                )
                new_case_main_ids.append(new_bm_case_main_id)
                print(f"✅ BM Case Main entry created with case_id: {new_bm_case_main_id} for ACK {bm_ack_no}", flush=True)
                await save_or_update_decision(self.executor, new_bm_case_main_id, {"remarks": bm_remarks, "short_dn": "BM Case", "long_dn": bm_remarks, "decision_type": "Created", "updated_by": "System"})
                print(f"✅ Initial history record for BM case_id {new_bm_case_main_id} inserted into case_history.", flush=True)

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
                            decision='Pending Review',
                            remarks=suspect_data.suspiciousActivityDescription or 'Automated case for potential suspect account.',
                            customer_full_name=suspect_data.customerName
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
                            customer_full_name=beneficiary_data.customerName
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
    async def create_ecb_case(self, ecb_data: ECBCaseData) -> Dict[str, Any]:
        def _sync_create_ecb_case():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    case_type = 'ECBT' if ecb_data.hasTransaction else 'ECBNT'
                    is_operational_value = False # As per requirement for Stage 2 internal cases

                    # Generate new ACK No
                    new_ack_no = f"{case_type}_{uuid.uuid4().hex[:10].upper()}"
                    
                    # Insert into case_main
                    new_case_main_id = self.insert_into_case_main(
                        case_type=case_type,
                        source_ack_no=new_ack_no,
                        cust_id=ecb_data.customerId,
                        acc_num=ecb_data.beneficiaryAccountNumber, # Primary account is beneficiary's
                        is_operational=is_operational_value,
                        status='New', # Initial status for internal cases
                        decision_input='Pending Review',
                        remarks_input=ecb_data.remarks or f"Automated case for {case_type} - Beneficiary Account: {ecb_data.beneficiaryAccountNumber}.",
                        source_bene_accno=ecb_data.beneficiaryAccountNumber # Link beneficiary account
                    )

                    # Insert initial audit/decision into case_history
                    initial_history_data = {
                        "remarks": ecb_data.remarks or f"{case_type} case generated.",
                        "short_dn": case_type,
                        "long_dn": f"Automated case created for {case_type} type.",
                        "decision_type": "Automated Trigger",
                        "updated_by": "System"
                    }
                    save_or_update_decision(self.executor, new_case_main_id, initial_history_data)
                    
                    # Optional: Insert into case_details_1 if specific matching details are desired for ECBT/ECBNT
                    # This implies matching logic would also be here, or data comes pre-matched.
                    # For now, only case_main and history are primary targets.

                    return {
                        "ack_no": new_ack_no,
                        "case_id": new_case_main_id,
                        "message": f"{case_type} case created successfully."
                    }
            try:
                return self._execute_sync_db_op(_sync_create_ecb_case)
            except Exception as e:
                print(f"Error creating {case_type} case: {e}", flush=True)
                raise


    async def fetch_user_type(self, user_name: str) -> Optional[str]:
        def _sync_fetch_user_type():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("SELECT user_type FROM user_table WHERE user_name = %s", (user_name,))
                    result = cur.fetchone()
                    return result['user_type'] if result else None
        return await self._execute_sync_db_op(_sync_fetch_user_type)

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

                    # Role-based filtering logic using user_type from user_table
                    if current_logged_in_username:
                        user_type_from_db = None
                        cur.execute("SELECT user_type FROM user_table WHERE user_name = %s", (current_logged_in_username,))
                        user_type_result = cur.fetchone()
                        if user_type_result:
                            user_type_from_db = user_type_result.get('user_type')

                        if user_type_from_db == 'CRO':
                            pass # CROs see ALL cases.
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
        def _sync_fetch_new_cases_list():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    sql_query = """
                        SELECT
                            cm.case_id,
                            cm.case_type,
                            cm.source_ack_no,      -- Original ACK No (from old system)
                            cm.source_bene_accno,  -- Original Beneficiary Account No.
                            cm.acc_num,            -- Primary Account Number involved
                            cm.cust_id,            -- Primary Customer ID involved
                            cm.creation_date,
                            cm.creation_time,
                            cm.is_operational,
                            cm.status,
                            cm.short_dn,           -- Short Decision/Description Name
                            cm.long_dn,            -- Long Decision/Description Name
                            cm.decision_type,      -- Type of Decision
                            a.assigned_to,         -- From assignment table
                            a.assigned_by          -- From assignment table
                        FROM public.case_main AS cm
                        LEFT JOIN public.assignment AS a ON cm.case_id = a.case_id
                    """
                    params = []
                    where_clauses = []

                    if search_source_ack_no:
                        where_clauses.append("cm.source_ack_no ILIKE %s")
                        params.append(f"%{search_source_ack_no}%")

                    if status_filter:
                        where_clauses.append("cm.status = %s")
                        params.append(status_filter)

                    if current_logged_in_username and current_logged_in_user_type:
                        if current_logged_in_user_type == 'CRO':
                            pass
                        elif current_logged_in_user_type == 'risk_officer':
                            where_clauses.append("a.assigned_to = %s")
                            params.append(current_logged_in_username)
                        elif current_logged_in_user_type == 'others':
                            where_clauses.append("a.assigned_to = %s")
                            params.append(current_logged_in_username)
                        else:
                            where_clauses.append("FALSE")
                    else:
                        pass

                    if where_clauses:
                        sql_query += " WHERE " + " AND ".join(where_clauses)

                    sql_query += " ORDER BY cm.creation_date DESC, cm.creation_time DESC"
                    sql_query += f" LIMIT %s OFFSET %s"
                    params.append(limit)
                    params.append(skip)

                    cur.execute(sql_query, tuple(params))
                    return cur.fetchall()
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

                    source_ack_no = case_main_data.get('source_ack_no')
                    main_cust_id = case_main_data.get('cust_id')
                    main_acc_num = case_main_data.get('acc_num')
                    source_bene_accno = case_main_data.get('source_bene_accno')

                    # 2. Fetch I4C data from case_entry_form (linked by source_ack_no)
                    if source_ack_no:
                        cur.execute("""
                            SELECT
                                ack_no, customer_name, sub_category, transaction_date, complaint_date, report_datetime,
                                state, district, policestation, payment_mode, account_number, card_number,
                                transaction_id, layers, transaction_amount, disputed_amount, action,
                                to_bank, to_account, ifsc, to_transaction_id, to_amount, action_taken_date,
                                additional_info, to_upi_id
                            FROM case_entry_form
                            WHERE ack_no = %s
                        """, (source_ack_no,))
                        i4c_data = cur.fetchone()
                        if i4c_data:
                            combined_case_data['i4c_data'] = i4c_data
                        else:
                            combined_case_data['i4c_data'] = None

                    # 3. Fetch customer details (victim/primary)
                    customer_data = None
                    if main_cust_id:
                        cur.execute("""
                            SELECT cust_id, fname, mname, lname, mobile, email, pan, nat_id, dob, citizen, occupation, seg, cust_type, risk_prof, kyc_status
                            FROM customer WHERE cust_id = %s
                        """, (main_cust_id,))
                        customer_data = cur.fetchone()
                    combined_case_data['customer_details'] = customer_data

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
                            c.kyc_status
                        FROM public.case_main AS cm
                        LEFT JOIN public.customer AS c ON cm.cust_id = c.cust_id
                        WHERE cm.source_ack_no = %s
                    """, (ack_no,))
                    
                    case_data = cur.fetchone() 
                    
                    if not case_data:
                        raise CaseNotFoundError(f"Case with ACK No '{ack_no}' not found in case_main.")
                    
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
        # FIX: Redefine _sync_insert_summary to accept the transformed data
        def sync_insert_summary(self, executor: ThreadPoolExecutor,case_id: int, case_ack_no: str, document_statuses_json: str, screenshot_file_location: Optional[str], confirmation_boolean_overall: bool, created_by_user: str, proof_of_upload_ref: str):
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    new_record = None
                    try: 
                        print(f"DEBUG: _sync_insert_summary - Attempting INSERT for case_id {case_id}, ref_no: {proof_of_upload_ref}", flush=True) 
                        print(f"DEBUG: _sync_insert_summary - JSONB data to insert: {document_statuses_json}", flush=True)

                        cur.execute(
                            """
                            INSERT INTO public.operational_confirmation (case_id, case_ack_no, ref_no, document_statuses_json, screenshot_file_location, confirmation_boolean, created_by, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                            RETURNING id;
                            """,
                            (case_id, case_ack_no, proof_of_upload_ref, document_statuses_json, screenshot_file_location, confirmation_boolean_overall, created_by_user)
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
                        raise ValueError(f"Unexpected error recording operational confirmation: {e}")
                    
                    # --- Case Closure Logic ---
                    if confirmation_boolean_overall: 
                        print(f"DEBUG: Setting case {case_ack_no} (ID: {case_id}) to 'Closed' and is_operational=TRUE based on overall confirmation.", flush=True)
                        try: 
                            cur.execute(
                                """
                                UPDATE public.case_main
                                SET status = %s, is_operational = %s
                                WHERE case_id = %s;
                                """,
                                ('Closed', True, case_id)
                            )
                            rows_affected = cur.rowcount
                            conn.commit() 
                            if rows_affected > 0:
                                print(f"✅ Case {case_ack_no} in case_main updated to 'Closed' and is_operational=TRUE. Rows affected: {rows_affected}", flush=True)
                            else:
                                print(f"⚠️ Case {case_ack_no} in case_main not found for status update after confirmation.", flush=True)
                        except Exception as e:
                            conn.rollback() 
                            print(f"❌ ERROR updating case_main status for case_id {case_id}: {e}", flush=True)
                            raise ValueError(f"DB Error updating case status: {e}")
                    
                    return new_record 
            
            # Prepare the data for _sync_insert_summary here, OUTSIDE the inner sync function.
            # FIX: Transform List[str] (document names) into List[Dict[str, bool]] (name and status)
            #transformed_document_statuses = []
            #for doc_name in document_statuses_json: # document_statuses_json is currently List[str]
            #    transformed_document_statuses.append({
            #        "name": doc_name,
            #        "status": True # Assuming documents received here are always 'ticked'
            #    })


            try:
                jsonb_data_string_for_insert = json.dumps(document_statuses_json)
                return self._execute_sync_db_op(insert_operational_confirmation_summary, 
                                                  case_id, case_ack_no, jsonb_data_string_for_insert, screenshot_file_location, 
                                                  confirmation_boolean_overall, created_by_user, proof_of_upload_ref) # Pass actual remarks param here
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


# --- DatabaseMatcher Class (Currently not used for new table logic, can be removed if desired) ---
class DatabaseMatcher:
    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor

    async def _execute_sync_db_op(self, func, *args, **kwargs):
        return await asyncio.get_running_loop().run_in_executor(self.executor, func, *args, **kwargs)
