# db/matcher.py
from asyncio.log import logger
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date
from typing import Dict, Any,AsyncGenerator, List, Optional, Union, Annotated
import json, time
import requests
import asyncio
import asyncpg
from concurrent.futures import ThreadPoolExecutor # Ensure this is imported for type hints
import traceback
# REMOVED: from main import executor # FIX: THIS LINE MUST BE REMOVED TO BREAK CIRCULAR IMPORT

# Import models and connection utilities
from .connection import get_db_connection, get_db_cursor
from models.base_models import CaseEntryData, I4CData, TransactionData, BeneficiaryData, PotentialSuspectAccountData
from config import DB_CONNECTION_PARAMS, ERROR_LOG_DIR
import os # FIX: Added import for os
import uuid
import re

from fastapi import UploadFile # FIX: Added import for UploadFile

# Custom exception
class CaseNotFoundError(Exception):
    pass

# --- Standalone Asynchronous Database Helper Functions ---
# FIX: All these functions now explicitly accept 'executor' as their first argument.

async def _execute_sync_op_standalone(executor: ThreadPoolExecutor, func, *args, **kwargs):
    return await asyncio.get_running_loop().run_in_executor(executor, func, *args, **kwargs)

async def fetch_transactions_from_db(executor: ThreadPoolExecutor, ack_no: str, from_date: date, to_date: date, type: str):
    def _sync_fetch():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute("SELECT account_number, to_account FROM case_entry_form WHERE ack_no = %s", (ack_no,))
                account_data = cur.fetchone()
                if not account_data:
                    raise CaseNotFoundError(f"Case with ACK No '{ack_no}' not found")

                account_to_query = None
                account_column = None
                if type == "victim":
                    account_to_query = account_data.get('account_number')
                    account_column = "acct_num"
                elif type == "beneficiary":
                    account_to_query = account_data.get('to_account')
                    account_column = "bene_acct_num"
                else:
                    raise ValueError("Type must be 'victim' or 'beneficiary'")

                if not account_to_query:
                    return []

                query = f"SELECT txn_date, descr, txn_ref, amount, txn_type FROM txn WHERE {account_column} = %s AND txn_date BETWEEN %s AND %s ORDER BY txn_date DESC"
                cur.execute(query, (account_to_query, from_date, to_date))
                db_rows = cur.fetchall()

                transactions = []
                for row in db_rows:
                    transactions.append({
                        'date': row['txn_date'].strftime('%d/%m/%Y'),
                        'narration': row['descr'],
                        'refNo': row['txn_ref'],
                        'valueDate': row['txn_date'].strftime('%d/%m/%Y'),
                        'withdrawal': row['amount'] if row['txn_type'] == 'Debit' else None,
                        'deposit': row['amount'] if row['txn_type'] == 'Credit' else None,
                        'closingBalance': None
                    })
                return transactions
    return await _execute_sync_op_standalone(executor, _sync_fetch)

# MODIFIED: insert_uploaded_document - Remove executor param, inline sync logic
async def insert_uploaded_document(executor: ThreadPoolExecutor, ack_no: str, document_type: str, original_filename: str, saved_filepath: str, file_mime_type: str, comment: Optional[str] = None): # Added comment
    def _sync_insert():
        with get_db_connection() as conn: # Use standard connection
            with get_db_cursor(conn) as cur: # Use standard cursor
                print("DEBUG: Inserting document into fraud_notice_uploads table", comment)
                logger.debug(f"Inserting document into fraud_notice_uploads table for ACK: {ack_no}, Type: {document_type}, Filename: {original_filename}, Path: {saved_filepath}, MIME Type: {file_mime_type}, Comment: {comment}")
                cur.execute(
    """
    INSERT INTO fraud_notice_uploads
        (ack_no, document_type, original_filename, saved_filepath, file_mime_type, comment)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id, original_filename, document_type;
    """,
    (ack_no, document_type, original_filename, saved_filepath, file_mime_type, comment)
)
                new_doc = cur.fetchone()
                conn.commit()
                return new_doc
    return await _execute_sync_op_standalone(executor, _sync_insert)

async def get_uploaded_documents(executor: ThreadPoolExecutor, ack_no: str):
    def _sync_get_docs():
        with get_db_connection() as conn: # Use standard connection
            with get_db_cursor(conn) as cur: # Use standard cursor
                cur.execute(
                    "SELECT id, document_type, original_filename, saved_filepath FROM fraud_notice_uploads WHERE ack_no = %s ORDER BY uploaded_at DESC",
                    (ack_no,)
                )
                docs = cur.fetchall()
                return docs
    return await _execute_sync_op_standalone(executor, _sync_get_docs)

# NEW: Helper for get_document_by_id (if needed for download_document_api)
async def get_document_by_id(executor: ThreadPoolExecutor, document_id: int) -> Optional[Dict[str, Any]]:
    def _sync_get_document():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute("SELECT saved_filepath, original_filename FROM fraud_notice_uploads WHERE id = %s", (document_id,))
                return cur.fetchone()
    return await _execute_sync_op_standalone(executor, _sync_get_document)

async def save_or_update_decision(executor: ThreadPoolExecutor, ack_no: str, data: Dict[str, Any]):
    def _sync_save_decision():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                # --- Part 1: Update case_decisions table (this part remains) ---
                db_data = {
                    "risk_score": data.get('riskScore'),
                    "triggering_rules": data.get('triggeringRules'),
                    "comments": data.get('comments'),
                    "decision_action": data.get('decisionAction'),
                    "assigned_employee": data.get('assignedEmployee'),
                    "audit_trail": data.get('auditTrail'),
                    "system_recommendation": data.get('systemRecommendation'),
                    "system_explanation": data.get('systemExplanation')
                }
                db_data = {k: v if v != '' else None for k, v in db_data.items() if v is not None}

                columns = ", ".join(db_data.keys())
                placeholders = ", ".join(["%s"] * len(db_data))
                update_set = ", ".join([f"{col} = EXCLUDED.{col}" for col in db_data.keys()])

                insert_columns = ", ".join(["ack_no"] + [col for col in db_data.keys() if col != "ack_no"])
                insert_placeholders = ", ".join(["%s"] * (1 + len([_ for _ in db_data.keys() if _ != "ack_no"])))
                db_values = [ack_no] + [db_data[k] for k in db_data.keys() if k != "ack_no"] # Ensure correct order

                cur.execute(
                    f"""
                    INSERT INTO case_decisions ({insert_columns})
                    VALUES ({insert_placeholders})
                    ON CONFLICT (ack_no) DO UPDATE SET
                        {update_set},
                        last_updated_at = NOW()
                    RETURNING *;
                    """,
                    tuple(db_values)
                )
                updated_decision_record = cur.fetchone()
                conn.commit()
                print(f"✅ Decision record for {ack_no} saved/updated in case_decisions.", flush=True)

                # --- Part 2: Update status in case_master based on decisionAction ---
                decision_action = data.get('decisionAction')
                if decision_action:
                    new_status_for_case_master = None
                    if decision_action == 'Close Case':
                        new_status_for_case_master = 'Closed'
                    elif decision_action == 'Mark as False Positive': # Example of another final status
                         new_status_for_case_master = 'False Positive'
                    # Add more decisionAction -> status mappings as needed

                    if new_status_for_case_master:
                        update_master_query = "UPDATE case_master SET status = %s"
                        master_params = [new_status_for_case_master]
                        if new_status_for_case_master in ['Closed', 'False Positive']: # If it's a final status
                            update_master_query += ", closed_on = NOW()"
                        update_master_query += " WHERE ack_no = %s"
                        master_params.append(ack_no)
                        
                        cur.execute(update_master_query, tuple(master_params))
                        rows_affected = cur.rowcount
                        conn.commit() # Commit this specific update
                        print(f"✅ Case master status for {ack_no} updated to '{new_status_for_case_master}'. Rows affected: {rows_affected}", flush=True)

                return updated_decision_record
    return await _execute_sync_op_standalone(executor, _sync_save_decision)


async def get_decision(executor: ThreadPoolExecutor, ack_no: str) -> Optional[Dict[str, Any]]:
    def _sync_get_decision():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute("SELECT * FROM case_decisions WHERE ack_no = %s", (ack_no,))
                decision_record_db = cur.fetchone()
                
                if not decision_record_db:
                    return None
                
                # Convert DB snake_case keys to frontend camelCase keys
                mapped_decision = {
                    "ackNo": decision_record_db.get('ack_no'),
                    "riskScore": decision_record_db.get('risk_score'),
                    "triggeringRules": decision_record_db.get('triggering_rules'),
                    "comments": decision_record_db.get('comments'),
                    "decisionAction": decision_record_db.get('decision_action'),
                    "assignedEmployee": decision_record_db.get('assigned_employee'),
                    "auditTrail": decision_record_db.get('audit_trail'),
                    "systemRecommendation": decision_record_db.get('system_recommendation'),
                    "systemExplanation": decision_record_db.get('system_explanation'),
                    "lastUpdatedAt": decision_record_db.get('last_updated_at').isoformat() if decision_record_db.get('last_updated_at') else None,
                }
                return mapped_decision
    return await _execute_sync_op_standalone(executor, _sync_get_decision)


# NEW METHOD: Assign case to an employee in case_master
    async def assign_case_to_employee(self, ack_no: str, assigned_to_employee_name: str) -> bool:
        def _sync_assign_case():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("SELECT ack_no FROM case_master WHERE ack_no = %s", (ack_no,))
                    if not cur.fetchone():
                        return False # Case not found

                    update_query = """
                        UPDATE case_master
                        SET
                            assigned_to = %s,
                            status = %s -- Set status to 'Assigned'
                        WHERE ack_no = %s
                    """
                    cur.execute(update_query, (assigned_to_employee_name, 'Assigned', ack_no))
                    rows_affected = cur.rowcount
                    conn.commit()
                    print(f"✅ Case {ack_no} master updated: assigned_to='{assigned_to_employee_name}', status='Assigned'. Rows affected: {rows_affected}", flush=True)

                    if rows_affected > 0:
                        # FIX: Also update assigned_employee in case_decisions table
                        # Use save_or_update_decision to handle the ON CONFLICT logic
                        # Need to pass this updated decision data to save_or_update_decision helper.
                        # It expects a dict with camelCase keys like assignedEmployee.

                        # Create a payload for save_or_update_decision
                        decision_update_payload = {
                            "assignedEmployee": assigned_to_employee_name,
                            "decisionAction": "Assigned", # Explicitly set action if assignment implies it
                            "comments": f"Case assigned to {assigned_to_employee_name}." # Add a comment
                        }
                        
                        # Use the original _sync_save_decision logic (or call the async wrapper if possible)
                        # Since save_or_update_decision is an async method of CaseEntryMatcher,
                        # we can't directly call it from inside this _sync_assign_case.
                        # We will make this method return the necessary data, and the router will call save_or_update_decision.
                        print(f"DEBUG: Returning update success for router to trigger case_decisions update.", flush=True)
                        return True # Indicate successful update to case_master
                    return False # Indicate update to case_master failed
        try:
            return await self._execute_sync_db_op(_sync_assign_case)
        except Exception as e:
            print(f"❌ Error in assign_case_to_employee for ACK {ack_no}: {e}", flush=True)
            raise # Re-raise for router to handle

# In your database helper file (e.g., db/matcher.py)

async def get_document_by_id(executor, doc_id: int):
    """Fetches a single document's details from the database by its primary key."""
    # This function should contain your database logic to run a query
    # For example:
    # query = "SELECT saved_filepath, original_filename FROM fraud_notice_uploads WHERE id = %s"
    # result = await run_query_in_executor(executor, query, (doc_id,))
    # return result
    
    # For now, let's assume you have a function that can execute this query.
    # The implementation depends on your specific database connection setup.
    # This is a placeholder for that logic.
    print(f"Placeholder: Fetching document with ID {doc_id} from DB.")
    # In a real scenario, this would query the DB and return a dictionary like:
    # {'saved_filepath': '/path/to/file.pdf', 'original_filename': 'original_name.pdf'}
    pass # You will need to implement the actual DB query here.
# --- Matcher Classes (Methods adapted to be async and use executor for DB calls) ---

class DatabaseMatcher:
    def __init__(self):
        pass


    # Helper to run synchronous DB operations in the thread pool for methods in this class
    def _execute_sync_db_op(self, func, *args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(executor, func, *args, **kwargs)

    async def insert_cyber_complaint(self, data: I4CData):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                await self._execute_sync_db_op(cur.execute, "SELECT ack_no FROM cyber_complaints WHERE ack_no = %s", (data.complaintref,)) 
                existing = await self._execute_sync_db_op(cur.fetchone)
                if existing: return None
                await self._execute_sync_db_op(cur.execute, """
                    INSERT INTO cyber_complaints (
                        ack_no, category, sub_category, complaint_date, incident_location, incident_url_id,
                        suspect_name, ip_address, suspect_id_type, suspect_id_no, suspect_bank_acct, suspect_upi_mobile,
                        comp_full_name, comp_mobile, comp_relation_name, comp_email, comp_address, comp_state, comp_district_ps, comp_relation_with_victim,
                        complaint_ps_name, complaint_ps_desig, complaint_ps_mobile, complaint_ps_email,
                        fraud_amount, txn_sno, txn_entity, txn_acct_wallet, txn_amount,
                        txn_ref_no, txn_date, txn_complaint_date, txn_remarks, reported_state, forwarded_to
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    data.complaintref, data.complaintType, data.subCategory, data.complaintDate or date.today(),
                    data.incidentLocation, data.incidentUrlId, data.beneficiaryInfo, data.beneficiaryIp,
                    data.suspectIdType, data.suspectIdNo, data.beneficiaryAccountNumber, data.beneficiaryMobile,
                    data.victimName, data.victimContact, data.victimRelativeName, data.victimEmail,
                    data.victimAddress, data.victimState, data.victimCity, data.victimRelativeName,
                    data.policeName, data.policeDesignation, data.policeMobile, data.policeEmail,
                    data.fraudAmount, data.txnSno, data.txnEntity, data.txnAcctWallet, data.txnAmount,
                    data.transactionId, data.txnDate, data.txnComplaintDate, data.txnRemarks,
                    data.reportedState, data.forwardedTo
                ))
                await self._execute_sync_db_op(conn.commit)
                return data.complaintref


    async def fetch_customer_data(self):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                await self._execute_sync_db_op(cur.execute, "SELECT cust_id, fname, mname, lname, mobile, email, pan, nat_id FROM customer")
                return await self._execute_sync_db_op(cur.fetchall)

    async def insert_case_master(self, ack_no, cust_id, match_type):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                today = date.today()
                await self._execute_sync_db_op(cur.execute, """
                    INSERT INTO case_master (ack_no, cust_id, match_type, status, created_on, closed_on, decision, remarks)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING case_id
                """, (ack_no, cust_id, match_type, 'New', today, None, '', ''))
                case_id_result = await self._execute_sync_db_op(cur.fetchone)
                await self._execute_sync_db_op(conn.commit)
                return case_id_result[0]

    async def insert_case_details(self, case_id, cust_id, complaint_date, mobile, email, pan, nat_id, card_num, acct_num, txn_ref_id):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                await self._execute_sync_db_op(cur.execute, """
                    INSERT INTO case_detail (case_id, cust_id, comp_date, mobile, email, pan, aadhar, card, acct, txn_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (case_id, cust_id, complaint_date, mobile, email, pan, nat_id, card_num or '', acct_num or '', txn_ref_id or ''))
                await self._execute_sync_db_op(conn.commit)

    async def insert_case_decisions(self, ack_no: str, classification_result: dict):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                classification = classification_result.get("classification"); reason = classification_result.get("reason")
                decision_action = classification; system_explanation = reason; comments = reason
                try:
                    await self._execute_sync_db_op(cur.execute, """
                        INSERT INTO public.case_decisions (
                            ack_no, risk_score, triggering_rules, comments, decision_action,
                            assigned_employee, audit_trail, system_recommendation, system_explanation
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ack_no, None, None, comments, decision_action, None, None, decision_action, system_explanation
                    ))
                    await self._execute_sync_db_op(conn.commit)
                except Exception as e:
                    await self._execute_sync_db_op(conn.rollback)
                    raise e

    async def match_data(self, data: I4CData):
        # All synchronous DB calls are wrapped in loop.run_in_executor.
        ack_no = await self.insert_cyber_complaint(data) # This is now async

        if ack_no is None:
            return f"⚠️ Duplicate ack_no '{data.complaintref}' already exists. Skipping insert."

        customers = await self.fetch_customer_data()
        victim_cust_id = None
        beneficiary_cust_id = None

        for cust in customers:
            cust_id, fname, mname, lname, mobile, email, pan, nat_id = cust
            full_name = f"{fname} {mname} {lname}".strip().lower()
            i4c_name_fields = [data.beneficiaryInfo.lower(), data.victimName.lower(), data.policeName.lower()]
            if full_name in i4c_name_fields:
                victim_cust_id = cust_id
                break

        if not victim_cust_id and data.beneficiaryAccountNumber:
             for cust in customers:
                cust_id, fname, mname, lname, mobile, email, pan, nat_id = cust
                if str(data.beneficiaryAccountNumber) == str(cust[9]): # Assuming acc_num is at index 9
                    beneficiary_cust_id = cust_id
                    break

        if victim_cust_id or beneficiary_cust_id:
            case_id = await self.insert_case_master(ack_no, victim_cust_id or beneficiary_cust_id, 'Mixed Match')
            await self.insert_case_details( 
                case_id, victim_cust_id or beneficiary_cust_id, data.complaintDate or date.today(),
                data.victimContact, data.victimEmail, None, None, 
                data.victimAccountNumber, data.victimAccountNumber, data.transactionId, 'Victim'
            )

            if beneficiary_cust_id:
                try:
                    api_acct_num = str(data.victimAccountNumber)
                    api_amount = float(data.fraudAmount)
                    api_txn_ref = data.complaintref
                    api_descr = f"Transaction for ACK {data.complaintref} from case entry system."

                    decision_api_url = "http://34.47.219.225:9000/api/classify-transaction"
                    headers = {"Content-Type": "application/json"}
                    payload = {"acct_num": api_acct_num, "amount": api_amount, "txn_ref": api_txn_ref, "descr": api_descr}

                    response = await self._execute_sync_db_op(requests.post, decision_api_url, headers=headers, data=json.dumps(payload)) # requests.post is sync
                    response.raise_for_status()
                    decision_data = await self._execute_sync_db_op(response.json)

                    classification_result = decision_data.get("classification_result")
                    if classification_result:
                        await self._execute_sync_db_op(self.insert_case_decisions, data.complaintref, classification_result)

                except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                    print(f"❌ Error calling decision API for beneficiary-matched case (RequestException): {e}")
                except Exception as e:
                    print(f"❌ An unexpected error occurred during decision API call or processing for beneficiary-matched case: {e}")

            return f"✅ Match found and inserted into case_master with ack_no {ack_no}. Decision processing attempted (for beneficiary match)."

        return f"ℹ️ Inserted complaint to cyber_complaints, but no customer match found (ack_no: {ack_no})."


# --- CaseEntryMatcher Class ---
class CaseEntryMatcher:
    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor

    async def _execute_sync_db_op(self, func, *args, **kwargs):
        return await asyncio.get_running_loop().run_in_executor(self.executor, func, *args, **kwargs)

    # NEW METHOD: Fetch list of cases from the new tables (for /api/new-case-list)
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
                            cm.source_ack_no,
                            cm.status,
                            cm.creation_date,
                            a.assigned_to,
                            a.assigned_by
                        FROM case_main AS cm
                        LEFT JOIN assignment AS a ON cm.case_id = a.case_id
                    """
                    params = []
                    where_clauses = []

                    if search_source_ack_no:
                        where_clauses.append("cm.source_ack_no ILIKE %s")
                        params.append(f"%{search_source_ack_no}%")

                    if status_filter:
                        where_clauses.append("cm.status = %s")
                        params.append(status_filter)

                    # Role-based filtering logic using user_type
                    if current_logged_in_username and current_logged_in_user_type:
                        if current_logged_in_user_type == 'CRO':
                            # CROs see ALL cases. No filter needed.
                            pass
                        elif current_logged_in_user_type == 'risk_officer':
                            # Risk Officers see ONLY cases assigned to them.
                            where_clauses.append("a.assigned_to = %s")
                            params.append(current_logged_in_username)
                        elif current_logged_in_user_type == 'others':
                            # 'Others' see ONLY cases assigned to them.
                            where_clauses.append("a.assigned_to = %s")
                            params.append(current_logged_in_username)
                        else: # User type not recognized/unhandled
                            where_clauses.append("FALSE") # Effectively returns no rows
                    else:
                        # Fallback if no user is authenticated or type is missing
                        # Default: show all cases if no user context for filtering.
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
                            acc_num, cust_id, creation_date, creation_time, is_operational, status
                        FROM case_main
                        WHERE case_id = %s
                    """, (case_id,))
                    case_main_data = cur.fetchone()
                    if not case_main_data:
                        raise CaseNotFoundError(f"Case with ID {case_id} not found in case_main.")
                    combined_case_data.update(case_main_data) # Add base case details

                    source_ack_no = case_main_data.get('source_ack_no')
                    main_cust_id = case_main_data.get('cust_id')
                    main_acc_num = case_main_data.get('acc_num')
                    source_bene_accno = case_main_data.get('source_bene_accno') # For transactions

                    # 2. Fetch I4C data from case_entry_form (linked by source_ack_no)
                    if source_ack_no:
                        cur.execute("""
                            SELECT
                                ack_no, sub_category, transaction_date, complaint_date, report_datetime,
                                state, district, policestation, payment_mode, account_number, card_number,
                                transaction_id, layers, transaction_amount, disputed_amount, action,
                                to_bank, to_account, ifsc, to_transaction_id, to_amount, action_taken_date,
                                lien_amount, evidence, evidence_name, additional_info, to_upi_id
                            FROM case_entry_form
                            WHERE ack_no = %s
                        """, (source_ack_no,))
                        i4c_data = cur.fetchone()
                        if i4c_data:
                            combined_case_data['i4c_data'] = i4c_data
                        else:
                            combined_case_data['i4c_data'] = None # Explicitly set None if no match

                    # 3. Fetch customer details (victim/primary)
                    customer_data = None
                    if main_cust_id:
                        cur.execute("""
                            SELECT cust_id, fname, mname, lname, mobile, email, pan, aadhar, dob, citizen, occupation, seg, cust_type, risk_prof, kyc_status
                            FROM customer WHERE cust_id = %s
                        """, (main_cust_id,))
                        customer_data = cur.fetchone()
                    combined_case_data['customer_details'] = customer_data

                    # 4. Fetch account details (primary account from case_main)
                    account_details = None
                    if main_acc_num:
                        cur.execute("""
                            SELECT acc_num, acc_name, acc_type, acc_status, open_date, branch_code, currency, balance, prod_code, min_bal, od_limit, credit_score, aqb, interest_rate, last_txn_date
                            FROM account WHERE acc_num = %s
                        """, (main_acc_num,))
                        account_details = cur.fetchone()
                    combined_case_data['account_details'] = account_details
                    
                    # 5. Fetch transaction details (based on acc_num and source_bene_accno)
                    transactions = []
                    # Get relevant account numbers for transaction fetching
                    tx_acc_nums_to_check = []
                    if main_acc_num: tx_acc_nums_to_check.append(main_acc_num)
                    if source_bene_accno and source_bene_accno != main_acc_num: tx_acc_nums_to_check.append(source_bene_accno)

                    if tx_acc_nums_to_check:
                        # Fetch all transactions for these accounts within a broad range or defined period for display
                        # You might want to pass from_date/to_date as parameters to the API
                        # For now, let's use a broad range for example
                        cur.execute("""
                            SELECT acc_num, txn_date, txn_time, txn_type, amount, descr, txn_ref, currency, bene_name, bene_acct_num, pay_method, channel
                            FROM txn
                            WHERE acc_num IN %s
                            ORDER BY txn_date DESC, txn_time DESC
                        """, (tuple(tx_acc_nums_to_check),))
                        transactions = cur.fetchall()
                    combined_case_data['transactions'] = transactions

                    # 6. Fetch decision history from the new 'decision' table
                    cur.execute("""
                        SELECT remarks, short_dn, long_dn, decision_type, decision_by, created_time
                        FROM decision
                        WHERE case_id = %s
                        ORDER BY created_time DESC
                    """, (case_id,))
                    decision_history = cur.fetchall()
                    combined_case_data['decision_history'] = decision_history

                    # 7. Fetch assignment history from the new 'assignment' table
                    cur.execute("""
                        SELECT assigned_to, assigned_by, assign_date, assign_time
                        FROM assignment
                        WHERE case_id = %s
                        ORDER BY assign_date DESC, assign_time DESC
                    """, (case_id,))
                    assignment_history = cur.fetchall()
                    combined_case_data['assignment_history'] = assignment_history

                    # 8. Fetch fraud notice uploads (using source_ack_no from case_main)
                    uploaded_documents = []
                    # Assuming case_id from case_main is the correct link
                    cur.execute("""
                        SELECT id, document_type, original_filename, file_location, uploaded_by, comment, uploaded_at, file_mime_type
                        FROM public.case_documents
                        WHERE case_id = %s
                        ORDER BY uploaded_at DESC
                    """, (str(case_id),)) # Convert case_id to str if case_documents.case_id is varchar
                    uploaded_documents = cur.fetchall()
                    combined_case_data['uploaded_documents'] = uploaded_documents
                    return combined_case_data

        try:
            return await self._execute_sync_db_op(_sync_fetch_combined_data)
        except CaseNotFoundError:
            raise # Re-raise CaseNotFoundError for the router to handle as 404
        except Exception as e:
            print(f"Error fetching combined case data for case_id {case_id}: {e}", flush=True)
            raise # Re-raise for router to handle as 500


    # NEW METHOD: Fetch detailed case info from new tables (for /api/new-case-details/{case_id})
    async def fetch_new_case_details(self, case_id: int) -> Optional[Dict[str, Any]]:
        def _sync_fetch_new_case_details():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    sql_query = """
                        SELECT
                            cm.*, -- Select all columns from case_main
                            a.assigned_to, a.assigned_by, a.assign_date, a.assign_time, -- From assignment
                            d.remarks AS decision_remarks, d.short_dn, d.long_dn, d.decision_type, d.decision_by, d.created_time AS decision_created_time -- From decision
                        FROM case_main AS cm
                        LEFT JOIN assignment AS a ON cm.case_id = a.case_id
                        LEFT JOIN decision AS d ON cm.case_id = d.case_id
                        WHERE cm.case_id = %s
                    """
                    cur.execute(sql_query, (case_id,))
                    result = cur.fetchone()
                    return result
        
        try:
            return await self._execute_sync_db_op(_sync_fetch_new_case_details)
        except Exception as e:
            print(f"Error fetching new case details for ID {case_id}: {e}", flush=True)
            raise

    async def insert_case_master(self, ack_no, cust_id, complaint_type, source, location, transaction_amount):
        # FIX: Use synchronous helper function with `with` and pass to executor
        def _sync_insert_master():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    today = date.today()
                    cur.execute("""
                        INSERT INTO case_master (ack_no, cust_id, complaint_type, source,
                        location, transaction_amount, status, created_on,
                        closed_on, decision, remarks)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING case_id
                    """, (
                        ack_no, cust_id, complaint_type, source,
                        location, transaction_amount, 'New', today,
                        None, None, None
                    ))
                    case_id_result = cur.fetchone()
                    conn.commit()
                    return case_id_result['case_id']
        return await self._execute_sync_db_op(_sync_insert_master)

    async def insert_case_details(self, case_id, cust_id, complaint_date, mobile, email, pan, nat_id, card_num, acct_num, txn_ref_id, match_flag):
        # FIX: Use synchronous helper function with `with` and pass to executor
        def _sync_insert_details():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("""
                        INSERT INTO case_detail (case_id, cust_id, comp_date, mobile, email, pan, aadhar, card, acct, txn_id, match_flag)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (case_id, cust_id, complaint_date, mobile or None, email or None, pan or None, nat_id or None,
                          card_num or None, acct_num or None, txn_ref_id or None, match_flag))
                    conn.commit()
        return await self._execute_sync_db_op(_sync_insert_details)

    async def insert_case_decisions(self, ack_no: str, classification_result: dict):
        # FIX: Use synchronous helper function with `with` and pass to executor
        def _sync_insert_decisions():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    classification = classification_result.get("classification")
                    reason = classification_result.get("reason")
                    decision_action = classification
                    system_explanation = reason
                    comments = reason
                    try:
                        cur.execute("""
                            INSERT INTO public.case_decisions (
                                ack_no, risk_score, triggering_rules, comments, decision_action,
                                assigned_employee, audit_trail, system_recommendation, system_explanation
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            ack_no, None, None, comments, decision_action,
                            None, None, decision_action, system_explanation
                        ))
                        conn.commit()
                        print(f"✅ Decision for ack_no {ack_no} inserted into case_decisions.", flush=True)
                    except Exception as e:
                        conn.rollback()
                        print(f"❌ Error inserting decision for ack_no {ack_no}: {e}", flush=True)
                        raise
        return await self._execute_sync_db_op(_sync_insert_decisions)

    # ... (validate_numeric_field remains unchanged as it's static/synchronous) ...

    async def fetch_transactions(self, ack_no: str, from_date: date, to_date: date, type: str):
        # FIX: Use synchronous helper function with `with` and pass to executor
        def _sync_fetch_transactions():
            transactions = []
            try:
                print(f"\n--- DEBUG fetch_transactions START ---", flush=True)
                print(f"DEBUG: Input - ack_no: {ack_no}, from_date: {from_date}, to_date: {to_date}, type: {type}", flush=True)

                with get_db_connection() as conn:
                    with get_db_cursor(conn) as cur:
                        account_col = 'account_number' if type == 'victim' else 'to_account'
                        print(f"DEBUG: Determining account_col: {account_col}", flush=True)

                        cur.execute(f"""
                            SELECT {account_col}
                            FROM case_entry_form
                            WHERE ack_no = %s
                        """, (ack_no,))
                        result = cur.fetchone()

                        print(f"DEBUG: Result from case_entry_form for {account_col}: {result}", flush=True)

                        if not result or not result.get(account_col):
                            print(f"DEBUG: No {type} account found in case_entry_form for ACK {ack_no}. Returning empty list.", flush=True)
                            print(f"--- DEBUG fetch_transactions END ---", flush=True)
                            return []

                        account_num = result.get(account_col)
                        print(f"DEBUG: Retrieved account_num for {type}: {account_num}", flush=True)

                        if not isinstance(account_num, (int, float, str)) or (isinstance(account_num, str) and not re.fullmatch(r'\d+', str(account_num).strip())):
                            print(f"DEBUG: Invalid account number retrieved from case_entry_form ('{account_num}') for {type}. Skipping txn fetch.", flush=True)
                            return []

                        sql_query = """
                            SELECT
                                txn_date,
                                descr,
                                txn_ref,
                                amount,
                                txn_type
                            FROM txn
                            WHERE acct_num = %s
                              AND txn_date BETWEEN %s AND %s
                            ORDER BY txn_date DESC, txn_time DESC;
                        """
                        query_params = (str(account_num), from_date, to_date)

                        print(f"DEBUG: Executing txn query for account: {account_num}, Dates: {from_date} to {to_date}", flush=True)
                        print(f"DEBUG: SQL Query: {sql_query}", flush=True)
                        print(f"DEBUG: Query Parameters: {query_params}", flush=True)

                        cur.execute(sql_query, query_params)
                        raw_transactions = cur.fetchall()

                        print(f"DEBUG: Fetched {len(raw_transactions)} raw transactions.", flush=True)

                        if len(raw_transactions) > 0:
                            print(f"DEBUG: Keys of first raw transaction: {raw_transactions[0].keys()}", flush=True)

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

                        print(f"DEBUG: Processed {len(processed_transactions)} transactions for {type} account {account_num}.", flush=True)
                        print(f"--- DEBUG fetch_transactions END ---", flush=True)
                        return processed_transactions

            except psycopg2.Error as db_error:
                print(f"DEBUG: Database error in self.fetch_transactions: {db_error}", flush=True)
                print(f"--- DEBUG fetch_transactions END ---", flush=True)
                raise
            except Exception as e:
                print(f"DEBUG: An unexpected error occurred in self.fetch_transactions: {e}", flush=True)
                print(f"--- DEBUG fetch_transactions END ---", flush=True)
                raise
        return await self._execute_sync_db_op(_sync_fetch_transactions)

    # FIX: Renamed method and updated SQL query for user_type
    async def fetch_user_type(self, user_name: str) -> Optional[str]:
        def _sync_fetch_user_type():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    print(f"DEBUG: Fetching user_type for user: '{user_name}'", flush=True) # NEW DEBUG
                    cur.execute(
                        """
                        SELECT user_type FROM user_table WHERE user_name = %s
                        """, (user_name,)
                    )
                    result = cur.fetchone()
                    user_type = result['user_type'] if result else None
                    print(f"DEBUG: User '{user_name}' has user_type: '{user_type}'", flush=True) # NEW DEBUG
                    return user_type
        return await self._execute_sync_db_op(_sync_fetch_user_type)

    async def fetch_dashboard_cases(self, skip: int = 0, limit: int = 25, 
                                    search_ack_no: Optional[str] = None, 
                                    status_filter: Optional[str] = None,
                                    current_logged_in_username: Optional[str] = None 
                                    ) -> List[Dict[str, Any]]:
        def _sync_fetch_dashboard_cases():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    sql_query = """
                        SELECT
                            ack_no,
                            complaint_type,
                            source,
                            complaint_type AS match_type,
                            location,
                            COALESCE(transaction_amount, 0) AS transaction_amount,
                            status,
                            assigned_to
                        FROM case_master
                    """
                    params = []
                    where_clauses = []

                    if search_ack_no:
                        where_clauses.append("ack_no ILIKE %s")
                        params.append(f"%{search_ack_no}%")

                    if status_filter:
                        where_clauses.append("status = %s")
                        params.append(status_filter)

                    print(f"DEBUG: Dashboard: current_logged_in_username: '{current_logged_in_username}'", flush=True) # NEW DEBUG

                    # Role-based filtering logic using user_type directly from DB
                    if current_logged_in_username:
                        user_type_from_db = None
                        # No need to call fetch_user_type here; it's handled in the router.
                        # The user_type is determined in the router's get_case_list and passed via the call itself
                        # Oh wait, fetch_dashboard_cases does NOT receive user_type as a param.
                        # It must fetch it itself as per my last code provided.
                        # The code below *is* correct for fetching it internally.

                        cur.execute("SELECT user_type FROM user_table WHERE user_name = %s", (current_logged_in_username,))
                        user_type_result = cur.fetchone()
                        if user_type_result:
                            user_type_from_db = user_type_result.get('user_type')
                        print(f"DEBUG: Dashboard: user_type_from_db for '{current_logged_in_username}': '{user_type_from_db}'", flush=True) # NEW DEBUG

                        if user_type_from_db == 'CRO':
                            pass
                        elif user_type_from_db == 'risk_officer':
                            where_clauses.append("assigned_to = %s")
                            params.append(current_logged_in_username)
                        elif user_type_from_db == 'others':
                            where_clauses.append("assigned_to = %s")
                            params.append(current_logged_in_username)
                        else: # User not found in user_table or unhandled type
                            print(f"WARNING: Dashboard: User '{current_logged_in_username}' has unhandled user_type '{user_type_from_db}' or not found. Restricting view.", flush=True) # NEW DEBUG
                            where_clauses.append("FALSE")
                    else:
                        # Fallback for unauthenticated or no username provided
                        print("DEBUG: Dashboard: No current_logged_in_username provided. Defaulting to show all cases (no assigned_to filter).", flush=True) # NEW DEBUG
                        pass # Show all by default if no user is provided

                    if where_clauses:
                        sql_query += " WHERE " + " AND ".join(where_clauses)

                    print(f"DEBUG: Final Dashboard SQL: {sql_query}", flush=True) # NEW DEBUG
                    print(f"DEBUG: Final Dashboard Params: {params}", flush=True) # NEW DEBUG

                    cur.execute(sql_query, tuple(params))
                    fetched_rows = cur.fetchall()
                    print(f"DEBUG: Fetched {len(fetched_rows)} rows for dashboard.", flush=True)
                    return fetched_rows
        return await self._execute_sync_db_op(_sync_fetch_dashboard_cases)


    # NEW METHOD: Fetch customer details for a case by ACK No
    async def fetch_case_customer_details(self, ack_no: str) -> Optional[Dict[str, Any]]:
        def _sync_fetch_case_customer_details():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("""
                        SELECT
                            cef.ack_no,
                            cef.sub_category,
                            cef.transaction_date,
                            cef.complaint_date,
                            cef.report_datetime,
                            cef.district,
                            cef.state,
                            cef.policestation,
                            cef.payment_mode,
                            cef.card_number,
                            cef.layers,
                            cef.disputed_amount,
                            cef.to_bank,
                            cef.ifsc,
                            cef.to_amount,
                            COALESCE(cef.lien_amount, 0.00) AS lien_amount,
                            cef.additional_info,
                            cef.account_number,
                            cef.transaction_id,
                            cef.transaction_amount,
                            cef.action,
                            cef.to_account,
                            cef.to_transaction_id,
                            cef.action_taken_date,
                            cef.evidence_name
                        FROM case_entry_form AS cef
                        WHERE cef.ack_no = %s
                    """, (ack_no,))
                    
                    row = cur.fetchone() # Fetch a single row as a dict
                    
                    if not row:
                        raise CaseNotFoundError(f"Acknowledgement No. {ack_no} not found in case_entry_form.")

                    # Map to the frontend's expected keys (using the exact strings)
                    return {
                        "Acknowledgement No.": row["ack_no"],
                        "Sub Category of Complaint": row["sub_category"],
                        "Transaction Date": row["transaction_date"],
                        "Complaint Date": row["complaint_date"],
                        "Date & Time of Reporting / Escalation": row["report_datetime"],
                        "District": row["district"],
                        "State": row["state"],
                        "Policestation": row["policestation"],
                        "Mode of Payment": row["payment_mode"],
                        "Card Number": row["card_number"],
                        "Layers": row["layers"],
                        "Disputed Amount": float(row["disputed_amount"]),
                        "Money transfer TO Bank": row["to_bank"], # This should be str, was float in old code
                        "IFSC Code (Non Mandatory)": row["ifsc"],
                        "Money transfer TO Amount": float(row["to_amount"]),
                        "Lien Amount (Non Mandatory)": float(row["lien_amount"]),
                        "Additional Information": row["additional_info"],
                        "Account Number": row["account_number"],
                        "Transaction Id / UTR Number": row["transaction_id"],
                        "Transaction Amount": float(row["transaction_amount"]),
                        "Action": row["action"],
                        "Money transfer TO Account": row["to_account"],
                        "Money transfer TO Transaction Id / UTR Number": row["to_transaction_id"],
                        "Action Taken Date": row["action_taken_date"],
                        "Evidence Provided (Non Mandatory)": row["evidence_name"]
                    }
        try:
            return await self._execute_sync_db_op(_sync_fetch_case_customer_details)
        except CaseNotFoundError:
            raise # Re-raise for router
        except Exception as e:
            print(f"Error in fetch_case_customer_details for ACK {ack_no}: {e}")
            raise # Let router handle generic exception

    async def match_and_populate_cases(self) -> List[Dict[str, Any]]:
        """
        Performs a join across 'account_customer', 'customer', and 'txn_table'
        to identify matching rows and populates the 'case_details_1' table.
        All DB interactions are wrapped using the class's ThreadPoolExecutor.
        """
        inserted_records = []

        # Define a synchronous function to fetch records, to be run in the executor
        def _sync_match_and_fetch():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    query = """
                    SELECT
                        ac.account_number AS acc_no,
                        c.cust_id,
                        c.mobile,
                        c.email,
                        c.pan,
                        c.card, -- Assuming 'card' column in 'customer' or similar
                        c.nat_id AS aadhar, -- Using nat_id from customer table as aadhar
                        'Automatic Match' AS casetype,
                        'Matched' AS match_flag
                    FROM
                        account_customer ac
                    JOIN
                        customer c ON ac.cust_id = c.cust_id
                    JOIN
                        txn_table tt ON ac.account_number = tt.account_num;
                    """
                    cur.execute(query) # Synchronous execute
                    return cur.fetchall() # Synchronous fetchall

        try:
            # Run the synchronous fetch operation in the class's thread pool
            records_to_insert = await self._execute_sync_db_op(_sync_match_and_fetch)

            if not records_to_insert:
                print("No matching records found for population in CaseEntryMatcher. Returning empty list.", flush=True)
                return []

            # Define a synchronous function to insert a batch of records
            def _sync_insert_batch(batch_records):
                with get_db_connection() as conn:
                    with get_db_cursor(conn) as cur:
                        insert_query = """
                        INSERT INTO case_details_1 (
                            casetype, mobile, email, pan, card, cust_id, acc_no, aadhar, match_flag
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s
                        );
                        """
                        values_to_insert = []
                        for record in batch_records:
                            # Create a Pydantic model instance to ensure data conforms to schema
                            case_data = CaseDetails1Entry(
                                casetype=record.get('casetype', 'Automatic Match'),
                                mobile=record.get('mobile'),
                                email=record.get('email'),
                                pan=record.get('pan'),
                                card=record.get('card'),
                                cust_id=record.get('cust_id'),
                                acc_no=record.get('acc_no'),
                                aadhar=record.get('aadhar'),
                                match_flag=record.get('match_flag', 'Matched')
                            )
                            values_to_insert.append((
                                case_data.casetype, case_data.mobile, case_data.email,
                                case_data.pan, case_data.card, case_data.cust_id,
                                case_data.acc_no, case_data.aadhar, case_data.match_flag
                            ))
                        
                        cur.executemany(insert_query, values_to_insert) # Synchronous executemany
                        conn.commit() # Synchronous commit
                        # Return the dictionary representation for successful response
                        return [CaseDetails1Entry(**record).dict() for record in batch_records]

            # Process in batches for efficient insertion
            BATCH_SIZE = 1000 # Adjust this size as needed
            for i in range(0, len(records_to_insert), BATCH_SIZE):
                batch = records_to_insert[i:i + BATCH_SIZE]
                inserted_batch = await self._execute_sync_db_op(_sync_insert_batch, batch)
                inserted_records.extend(inserted_batch)
                print(f"Inserted batch {i//BATCH_SIZE + 1} ({len(inserted_batch)} records). Total inserted: {len(inserted_records)}", flush=True)

            return inserted_records

        except Exception as e:
            print(f"Error during match and populate in CaseEntryMatcher: {e}", flush=True)
            traceback.print_exc()
            raise # Re-raise the exception to be caught by the FastAPI endpoint


    async def create_nab_case_if_flagged(self, beneficiary_data: BeneficiaryData) -> Optional[Dict[str, Any]]:
        def _sync_create_nab_case():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    matched = False
                    matched_fields = []
                    cyber_result_ack_no = None
                    suspect_result_id = None

                    # Check against cyber_complaints (this part is not the source of the error)
                    cur.execute("""
                        SELECT ack_no FROM cyber_complaints
                        WHERE suspect_bank_acct = %s OR suspect_upi_mobile = %s OR comp_email = %s
                    """, (beneficiary_data.beneficiaryAccountNumber, beneficiary_data.beneficiaryMobile, beneficiary_data.beneficiaryEmail))
                    cyber_result_row = cur.fetchone()
                    if cyber_result_row:
                        matched = True
                        matched_fields.append("cyber_complaints")
                        cyber_result_ack_no = cyber_result_row.get('ack_no')

                    # Check against suspect_entries (THIS IS THE SECTION WITH THE ERROR)
                    sql_suspect_query = """
                        SELECT id FROM suspect_entries
                        WHERE bank_account_number = %s OR mobile = %s OR email_id = %s OR pan = %s OR aadhar = %s OR upi_id = %s
                    """
                    params_for_suspect_query = (
                        beneficiary_data.beneficiaryAccountNumber,
                        beneficiary_data.beneficiaryMobile,
                        beneficiary_data.beneficiaryEmail,
                        beneficiary_data.beneficiaryPAN,       # This can be Optional[str]
                        beneficiary_data.beneficiaryAadhar,    # This can be Optional[str]
                        beneficiary_data.beneficiaryUPI
                    )
                    
                    # FIX: Add debug prints to check types and values
                    print(f"DEBUG: Suspects SQL Query: {sql_suspect_query}", flush=True)
                    print(f"DEBUG: Suspects Params Values: {params_for_suspect_query}", flush=True)
                    print(f"DEBUG: Suspects Param Types: {[type(p) for p in params_for_suspect_query]}", flush=True)
                    
                    cur.execute(sql_suspect_query, params_for_suspect_query)
                    suspect_result_row = cur.fetchone()
                    if suspect_result_row:
                        matched = True
                        matched_fields.append("suspect_entries")
                        suspect_result_id = suspect_result_row.get('id')
                    
                    # ... (rest of _sync_create_nab_case logic) ...
                    if matched:
                        print(f"⚠️ Flagged beneficiary '{beneficiary_data.beneficiaryName}'. Creating NAB case.", flush=True)
                        
                        case_type = "NAB" # Hardcoded as per requirement
                        cur.execute("SELECT case_type FROM case_type_master WHERE case_type = %s", (case_type,))
                        if not cur.fetchone():
                            print(f"ERROR: Case type '{case_type}' not found in case_type_master.", flush=True)
                            raise ValueError(f"Case type '{case_type}' is not defined in case_type_master table.")

                        new_ack_no = f"NAB_{uuid.uuid4().hex[:10].upper()}"
                        print(f"Generated new ACK No for NAB case: {new_ack_no}", flush=True)

                        # Insert into case_master
                        cur.execute("""
                            INSERT INTO case_master (ack_no, cust_id, status, created_on, complaint_type, source, location, transaction_amount, decision, remarks, assigned_to)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING case_id
                        """, (
                            new_ack_no,
                            beneficiary_data.customerId,
                            'New',
                            date.today(),
                            case_type,
                            'Automated',
                            'System',
                            0,
                            'Pending Review',
                            'Auto-generated due to beneficiary match.',
                            None
                        ))
                        case_id_result = cur.fetchone()
                        case_id = case_id_result['case_id']
                        print(f"Case Master entry created with case_id: {case_id} for ACK {new_ack_no}", flush=True)

                        # Populate case_detail table
                        cur.execute("""
                            INSERT INTO case_detail (case_id, cust_id, comp_date, mobile, email, pan, aadhar, acct, match_flag, txn_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            case_id,
                            beneficiary_data.customerId,
                            date.today(),
                            beneficiary_data.beneficiaryMobile,
                            beneficiary_data.beneficiaryEmail,
                            beneficiary_data.beneficiaryPAN or None, # Use None for Optional fields if empty
                            beneficiary_data.beneficiaryAadhar or None, # Use None for Optional fields if empty
                            beneficiary_data.beneficiaryAccountNumber,
                            'Beneficiary Match',
                            None # txn_id
                        ))
                        print(f"Case Detail entry created for case_id: {case_id}", flush=True)

                        # FIX: Insert into public.case_details_1 table - Aligned with its schema
                        cur.execute("""
                            INSERT INTO public.case_details_1 (
                                cust_id, casetype, mobile, email, pan, aadhar, acc_no, card, match_flag
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            beneficiary_data.customerId,          # maps to cust_id
                            case_type,                            # maps to casetype ('NAB')
                            beneficiary_data.beneficiaryMobile,   # maps to mobile
                            beneficiary_data.beneficiaryEmail,    # maps to email
                            beneficiary_data.beneficiaryPAN or None, # maps to pan (Optional)
                            beneficiary_data.beneficiaryAadhar or None, # maps to aadhar (Optional)
                            beneficiary_data.beneficiaryAccountNumber, # maps to acc_no
                            None,                                 # maps to card (no equivalent in BeneficiaryData)
                            "Beneficiary Match"                   # maps to match_flag
                        ))
                        conn.commit()
                        print(f"Case details_1 entry created for customer: {beneficiary_data.customerId}", flush=True)

                        return {
                            "ack_no": new_ack_no,
                            "case_id": case_id,
                            "message": "NAB case created successfully due to match."
                        }
                    else:
                        print(f"✅ Beneficiary '{beneficiary_data.beneficiaryName}' is clean. No case created.", flush=True)
                        return None
        try:
            return await self._execute_sync_db_op(_sync_create_nab_case)
        except ValueError as e:
            print(f"ERROR processing NAB case: {e}", flush=True)
            raise
        except Exception as e:
            print(f"UNEXPECTED ERROR processing NAB case: {e}", flush=True)
            raise

    # NEW METHOD: Create PSA (Potential Suspect Account) case if flagged
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
                        suspect_data.accountNumber, suspect_data.upiId, suspect_data.email,
                        suspect_data.mobile, suspect_data.aadhar, suspect_data.pan
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
                    
                    # Debug prints (keep for now, remove in production)
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
                        
                        # Verify "PSA" case type exists in case_type_master
                        case_type = "PSA"
                        cur.execute("SELECT case_type FROM case_type_master WHERE case_type = %s", (case_type,))
                        if not cur.fetchone():
                            print(f"ERROR: Case type '{case_type}' not found in case_type_master.", flush=True)
                            raise ValueError(f"Case type '{case_type}' is not defined in case_type_master table.")

                        # Create new ACK No for this auto-generated case
                        new_ack_no = f"PSA_{uuid.uuid4().hex[:10].upper()}"
                        print(f"Generated new ACK No for PSA case: {new_ack_no}", flush=True)

                        # Insert into case_master
                        cur.execute("""
                            INSERT INTO case_master (ack_no, cust_id, status, created_on, complaint_type, source, location, transaction_amount, decision, remarks, assigned_to)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING case_id
                        """, (
                            new_ack_no,
                            suspect_data.customerId,
                            'New',
                            date.today(),
                            case_type, # 'PSA'
                            'Automated',
                            'System',
                            suspect_data.transactionAmount or 0,
                            'Pending Review',
                            suspect_data.suspiciousActivityDescription or 'Auto-generated due to suspect match.',
                            None
                        ))
                        case_id_result = cur.fetchone()
                        case_id = case_id_result['case_id']
                        print(f"Case Master entry created with case_id: {case_id} for ACK {new_ack_no}", flush=True)

                        # Populate case_detail (linking to customer/account details)
                        cur.execute("""
                            INSERT INTO case_detail (case_id, cust_id, comp_date, mobile, email, pan, aadhar, acct, match_flag, txn_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            case_id,
                            suspect_data.customerId,
                            date.today(),
                            suspect_data.mobile or None,
                            suspect_data.email or None,
                            suspect_data.pan or None,
                            suspect_data.aadhar or None,
                            suspect_data.accountNumber or None,
                            'PSA Match',
                            None # txn_id
                        ))
                        print(f"Case Detail entry created for case_id: {case_id}", flush=True)

                        # Insert into case_details_1 table (for screening details)
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
                            None, # card (not in PotentialSuspectAccountData)
                            "PSA Match"
                        ))
                        conn.commit()
                        print(f"Case details_1 entry created for customer: {suspect_data.customerId}", flush=True)

                        return {
                            "ack_no": new_ack_no,
                            "case_id": case_id,
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


    # NEW METHOD: Verify Beneficiary Data (for /api/verify-beneficiary)
    async def verify_beneficiary_data(self, beneficiary_data: BeneficiaryData) -> Dict[str, Any]:
        def _sync_verify_beneficiary_data():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    matched = False
                    match_type = "none"
                    matched_fields = []
                    cyber_result_row = None
                    suspect_result_row = None

                    # Match against cyber_complaints
                    cur.execute("""
                        SELECT ack_no, ifsc, comp_mobile, aadhar, pan, comp_email, suspect_upi_mobile, suspect_bank_acct FROM cyber_complaints
                        WHERE suspect_bank_acct = %s OR suspect_upi_mobile = %s OR comp_email = %s
                        OR comp_mobile = %s OR aadhar = %s OR pan = %s
                    """, (
                        beneficiary_data.beneficiaryAccountNumber, beneficiary_data.beneficiaryUPI, beneficiary_data.beneficiaryEmail,
                        beneficiary_data.beneficiaryMobile, beneficiary_data.beneficiaryAadhar, beneficiary_data.beneficiaryPAN
                    ))
                    cyber_result_row = cur.fetchone()
                    if cyber_result_row:
                        matched = True
                        cyber_ifsc = cyber_result_row.get('ifsc')
                        if cyber_ifsc and cyber_ifsc == beneficiary_data.beneficiaryIFSC:
                            match_type = "full"
                        elif match_type != "full":
                            match_type = "partial"
                        matched_fields.append("cyber_complaints")

                    # Match against suspect_entries
                    cur.execute("""
                        SELECT id, ifsc, mobile, aadhar, pan, email_id, upi_id, bank_account_number FROM suspect_entries
                        WHERE bank_account_number = %s OR mobile = %s OR email_id = %s OR pan = %s OR aadhar = %s OR upi_id = %s
                    """, (
                        beneficiary_data.beneficiaryAccountNumber, beneficiary_data.beneficiaryMobile,
                        beneficiary_data.beneficiaryEmail, beneficiary_data.beneficiaryPAN,
                        beneficiary_data.beneficiaryAadhar, beneficiary_data.beneficiaryUPI
                    ))
                    suspect_result_row = cur.fetchone()
                    if suspect_result_row:
                        matched = True
                        suspect_ifsc = suspect_result_row.get('ifsc')
                        if suspect_ifsc and suspect_ifsc == beneficiary_data.beneficiaryIFSC:
                            match_type = "full"
                        elif match_type != "full":
                            match_type = "partial"
                        matched_fields.append("suspect_entries")

                    return {
                        "matched": matched,
                        "match_type": match_type,
                        "matched_fields": matched_fields,
                        "matched_ack_no": cyber_result_row.get('ack_no') if cyber_result_row else None, # Include details if needed
                        "matched_suspect_id": suspect_result_row.get('id') if suspect_result_row else None # Include details if needed
                    }
        try:
            return await self._execute_sync_db_op(_sync_verify_beneficiary_data)
        except Exception as e:
            print(f"Error in verify_beneficiary_data: {e}", flush=True)
            raise


    async def fetch_single_case_details(self, ack_no: str) -> Optional[Dict[str, Any]]:
        def _sync_fetch_single_case_details():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute("""
                        SELECT
                            cm.case_id,
                            cm.ack_no,
                            cm.cust_id,
                            cm.status,
                            cm.created_on,
                            cm.closed_on,
                            cm.decision,
                            cm.remarks,
                            cm.assigned_to,
                            cm.created_by,
                            cm.complaint_type,
                            cm.source,
                            cm.location,
                            cm.transaction_amount,
                            cd.comp_date,
                            cd.mobile,
                            cd.email,
                            cd.pan,
                            cd.aadhar,
                            cd.card,
                            cd.acct,
                            cd.txn_id,
                            cd.match_flag,
                            -- Columns from case_entry_form (cef)
                            cef.sub_category,
                            cef.report_datetime,
                            cef.state,
                            cef.district,
                            cef.policestation,
                            cef.payment_mode,
                            cef.account_number,
                            cef.card_number,
                            cef.transaction_id AS form_transaction_id,
                            cef.layers,
                            cef.transaction_amount AS form_transaction_amount,
                            cef.disputed_amount,
                            cef.action,
                            cef.to_bank,
                            cef.to_account,
                            cef.ifsc,
                            cef.to_transaction_id,
                            cef.to_amount,
                            cef.action_taken_date,
                            cef.lien_amount,
                            cef.evidence,
                            cef.evidence_name,
                            cef.additional_info,
                            cef.to_upi_id,
                            -- Columns from case_decisions (cdes)
                            cdes.risk_score,
                            cdes.triggering_rules,
                            cdes.comments AS decision_comments,
                            cdes.decision_action,
                            cdes.system_recommendation,
                            cdes.system_explanation
                        FROM case_master AS cm
                        LEFT JOIN case_detail AS cd ON cm.case_id = cd.case_id
                        -- FIX: Add LEFT JOIN for case_entry_form with alias 'cef'
                        LEFT JOIN case_entry_form AS cef ON cm.ack_no = cef.ack_no
                        LEFT JOIN case_decisions AS cdes ON cm.ack_no = cdes.ack_no
                        WHERE cm.ack_no = %s
                    """, (ack_no,))
                    
                    case_data = cur.fetchone()

                    if not case_data:
                        raise CaseNotFoundError(f"No case found with ACK No: {ack_no}")
                    
                    return case_data
        
        try:
            return await self._execute_sync_db_op(_sync_fetch_single_case_details)
        except CaseNotFoundError:
            raise 
        except Exception as e:
            print(f"Error fetching case details for {ack_no}: {e}")
            raise


    # NEW METHOD: Fetch risk profiles for victim and beneficiary by ACK No
    async def fetch_case_risk_profile(self, ack_no: str) -> Dict[str, Optional[Dict[str, Any]]]:
        def _sync_fetch_case_risk_profile():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # Step 1: Get case_id from case_master
                    cur.execute("SELECT case_id FROM case_master WHERE ack_no = %s", (ack_no,))
                    case_master_row = cur.fetchone()
                    if not case_master_row:
                        raise CaseNotFoundError(f"Acknowledgement number {ack_no} not found in case_master.")
                    case_id = case_master_row['case_id']

                    # Nested helper function to get entity profile (customer + account)
                    def get_entity_profile_sync(case_id: int, flag: str):
                        # Step 2: Get cust_id and acc_num for the given match_flag
                        cur.execute("""
                            SELECT cust_id, acct FROM case_detail
                            WHERE case_id = %s AND match_flag = %s
                        """, (case_id, flag))
                        result = cur.fetchone()
                        if not result:
                            return None

                        cust_id = result["cust_id"]
                        acc_num = result["acct"]

                        # Step 3: Get customer profile
                        cur.execute("""
                            SELECT
                                c.cust_id,
                                CONCAT_WS(' ', c.fname, c.mname, c.lname) AS full_name,
                                c.dob, c.nat_id, c.pan, c.citizen,
                                c.occupation, c.seg, c.cust_type,
                                c.risk_prof, c.kyc_status
                            FROM customer c
                            WHERE c.cust_id = %s
                        """, (cust_id,))
                        customer = cur.fetchone()

                        # Step 4: Get account profile
                        cur.execute("""
                            SELECT
                                a.acc_num AS account_number,
                                a.acc_type, a.acc_status,
                                a.open_date, a.balance,
                                a.last_txn_date, a.credit_score
                            FROM account a
                            WHERE a.acc_num = %s
                        """, (acc_num,))
                        account = cur.fetchone()

                        if not customer and not account:
                            return None

                        return {**(customer or {}), **(account or {})} # Combine both results

                    victim_profile = get_entity_profile_sync(case_id, 'victim')
                    beneficiary_profile = get_entity_profile_sync(case_id, 'beneficiary')

                    return {
                        "victim": victim_profile,
                        "beneficiary": beneficiary_profile
                    }
        try:
            return await self._execute_sync_db_op(_sync_fetch_case_risk_profile)
        except CaseNotFoundError: # Catch if CaseNotFoundError is raised from case_master lookup
            raise
        except Exception as e:
            print(f"Error in fetch_case_risk_profile for ACK {ack_no}: {e}")
            raise

    async def assign_case_to_employee(self, ack_no: str, assigned_to_employee_name: str, 
                                      assigner_username: str, assigner_user_type: str) -> bool:
        def _sync_assign_case():
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    # 1. Get current case details (current assignee, status)
                    cur.execute("SELECT assigned_to, assigned_by, status FROM case_master WHERE ack_no = %s FOR UPDATE", (ack_no,))
                    case_master_current_state = cur.fetchone()
                    if not case_master_current_state:
                        return False # Case not found

                    current_assignee = case_master_current_state.get('assigned_to')
                    current_status = case_master_current_state.get('status')
                    previous_assigner_of_record = case_master_current_state.get('assigned_by')

                    # 2. Get user_type of the intended assignee
                    cur.execute("SELECT user_type FROM user_table WHERE user_name = %s", (assigned_to_employee_name,))
                    assignee_user_type_row = cur.fetchone()
                    if not assignee_user_type_row:
                        raise HTTPException(status_code=400, detail=f"Assignee '{assigned_to_employee_name}' not found in user database.")
                    assignee_user_type = assignee_user_type_row.get('user_type')

                    # --- Implement Assignment Rules ---
                    can_assign = False
                    new_status_for_case_master = 'Assigned' # Default status when case is assigned to someone
                    assignment_comments = "" # Specific comment for decision_update_payload
                    
                    assign_by_update = assigner_username
                    reassign_from_update = current_assignee

                    if assigner_user_type == 'CRO':
                        if assignee_user_type == 'risk_officer':
                            can_assign = True
                            assignment_comments = f"Case initially assigned by CRO {assign_by_update}."
                        else:
                            raise HTTPException(status_code=400, detail=f"CRO can only assign cases to 'risk_officer' users.")
                        
                    elif assigner_user_type == 'risk_officer':
                        if assignee_user_type == 'others':
                            can_assign = True
                            new_status_for_case_master = 'Assigned' # Case is assigned to the 'others' user
                            assignment_comments = f"Case assigned by Risk Officer {assign_by_update} to team member."
                        elif assignee_user_type == 'risk_officer' and assigned_to_employee_name != assigner_username:
                            can_assign = True
                            new_status_for_case_master = 'Assigned' # Case is reassigned to another RO
                            assignment_comments = f"Case reassigned by Risk Officer {assign_by_update} to colleague."
                        else:
                            raise HTTPException(status_code=400, detail=f"Risk Officer can assign to 'others' or reassign to another 'risk_officer'.")
                        
                        # Restriction: Cannot send back to CRO
                        if assignee_user_type == 'CRO':
                            raise HTTPException(status_code=400, detail=f"Risk Officer cannot reassign case to a 'CRO' user.")

                    elif assigner_user_type == 'others':
                        if assigned_to_employee_name == previous_assigner_of_record and assignee_user_type == 'risk_officer':
                            can_assign = True
                            new_status_for_case_master = 'Assigned' # Case is assigned back to the RO
                            assignment_comments = f"Case sent back by {assign_by_update} (others) to Risk Officer {assigned_to_employee_name}."
                        else:
                            raise HTTPException(status_code=400, detail=f"User of type 'others' can only send case back to their assigned 'risk_officer'.")
                    
                    else:
                        raise HTTPException(status_code=403, detail="Unauthorized: Your user type cannot assign cases.")


                    if can_assign:
                        update_query = """
                            UPDATE case_master
                            SET
                                assigned_to = %s,
                                status = %s,              -- Use new_status_for_case_master
                                assigned_by = %s,         -- The user who just performed the assignment
                                reassigned_from = %s,     -- The user it was assigned from before this action
                                reassignment_count = COALESCE(reassignment_count, 0) + 1
                            WHERE ack_no = %s
                        """
                        cur.execute(update_query, (
                            assigned_to_employee_name,
                            new_status_for_case_master, # Use the determined status
                            assign_by_update,
                            reassign_from_update,
                            ack_no
                        ))
                        rows_affected = cur.rowcount
                        conn.commit()

                        if rows_affected > 0:
                            # Update assigned_employee in case_decisions with a detailed audit trail
                            decision_update_payload = {
                                "assignedEmployee": assigned_to_employee_name,
                                "decisionAction": new_status_for_case_master, # Status reflecting the assignment
                                "comments": assignment_comments, # Specific comment for this assignment type
                                "auditTrail": f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} GMT - Assigned by {assign_by_update} (Type: {assigner_user_type}) to {assigned_to_employee_name} (Type: {assignee_user_type}). Previous assignee: {reassign_from_update or 'None'}. (Status: {new_status_for_case_master})"
                            }
                            # This will be called by the router after this sync block returns True
                            return True
                        else:
                            print(f"DEBUG: Case master update failed (0 rows affected) for ACK {ack_no}.", flush=True)
                            return False
                    else:
                        return False # Should be caught by HTTPException raises above

        try:
            return await self._execute_sync_db_op(_sync_assign_case)
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Error in assign_case_to_employee for ACK {ack_no}: {e}", flush=True)
            raise

    async def match_data(self, data: CaseEntryData, evidence_file: Optional[UploadFile] = None):
        victim_cust_id = None
        beneficiary_cust_id = None
        case_id = None

        # ... (validate_numeric_field calls) ...

        # ---- Print incoming data values for debug clarity ----
        # ... (print statements) ...

        # ---- Check for victim match ----
        if data.accountNumber is not None:
            # FIX: Wrap DB operations in a synchronous helper function
            def _sync_check_victim():
                with get_db_connection() as conn:
                    with get_db_cursor(conn) as cur:
                        cur.execute("SELECT cust_id FROM account_customer WHERE acc_num = %s", (str(data.accountNumber),))
                        return cur.fetchone()
            try:
                victim_result = await self._execute_sync_db_op(_sync_check_victim)
                print("Victim result from DB:", victim_result, flush=True)
                if victim_result:
                    victim_cust_id = victim_result.get('cust_id')
            except Exception as e:
                print(f"Error checking victim match for {data.accountNumber}: {e}", flush=True)
        else:
            print("Skipping victim match check: accountNumber is None.", flush=True)

        # ---- Check for beneficiary match ----
        if data.toAccount is not None:
            # FIX: Wrap DB operations in a synchronous helper function
            def _sync_check_beneficiary():
                with get_db_connection() as conn:
                    with get_db_cursor(conn) as cur:
                        cur.execute("SELECT cust_id FROM account_customer WHERE acc_num = %s", (str(data.toAccount),))
                        return cur.fetchone()
            try:
                beneficiary_result = await self._execute_sync_db_op(_sync_check_beneficiary)
                print("Beneficiary result from DB:", beneficiary_result, flush=True)
                if beneficiary_result:
                    beneficiary_cust_id = beneficiary_result.get('cust_id')
            except Exception as e:
                print(f"Error checking beneficiary match for {data.toAccount}: {e}", flush=True)
        else:
            print("Skipping beneficiary match check: toAccount is None.", flush=True)

        print(f"DEBUG: At this point, victim_cust_id: {victim_cust_id}, beneficiary_cust_id: {beneficiary_cust_id}", flush=True)

        # ---- Always insert into case_entry_form FIRST ----
        print("Inserting into case_entry_form...", flush=True)
        # Prepare evidence path and name for DB insert
        saved_filepath_for_db = None
        original_filename_for_db = None

        if evidence_file:
            UPLOAD_DIR = "/home/ubuntu/fraud_uploads"
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            original_filename = evidence_file.filename if evidence_file.filename else "unknown_file"
            file_extension = os.path.splitext(original_filename)[1] if original_filename else ".bin"
            unique_filename = f"{data.ackNo}_{uuid.uuid4()}{file_extension}"
            saved_filepath_for_db = os.path.join(UPLOAD_DIR, unique_filename)
            original_filename_for_db = original_filename

            try:
                file_content = await evidence_file.read()
                # FIX: File writing is also a blocking I/O operation, should be in executor
                def _sync_write_file():
                    with open(saved_filepath_for_db, "wb") as buffer:
                        buffer.write(file_content)
                await self._execute_sync_db_op(_sync_write_file) # Run file write in executor
                print(f"✅ Evidence file saved to: {saved_filepath_for_db}", flush=True)
            except Exception as e:
                print(f"❌ Error saving evidence file for ack_no {data.ackNo}: {e}", flush=True)
                raise ValueError(f"Failed to save evidence file: {e}")



        # FIX: Wrap DB operations in a synchronous helper function for case_entry_form insert
        def _sync_insert_case_entry_form():
            with get_db_connection() as conn_form_insert:
                with get_db_cursor(conn_form_insert) as cur_form_insert:
                    try:
                        cur_form_insert.execute("""INSERT INTO case_entry_form (
                            ack_no, sub_category, transaction_date, complaint_date, report_datetime,
                            state, district, policestation, payment_mode,
                            account_number, card_number, transaction_id, layers,
                            transaction_amount, disputed_amount, action, to_bank, to_account,
                            ifsc, to_transaction_id, to_amount, action_taken_date, lien_amount,
                            evidence, evidence_name, additional_info, to_upi_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (
                                data.ackNo, data.subCategory, data.transactionDate, data.complaintDate, data.reportDateTime,
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
                                data.lienAmount,
                                saved_filepath_for_db, # Pass the saved file path
                                original_filename_for_db, # Pass the original filename
                                data.additionalInfo,
                                data.toUpiId
                            )
                        )
                        conn_form_insert.commit()
                        print("✅ Case_entry_form committed to the database.", flush=True)
                    except psycopg2.Error as e:
                        conn_form_insert.rollback()
                        print(f"❌ Error inserting into case_entry_form for ack_no {data.ackNo}: {e}", flush=True)
                        raise ValueError(f"Database error inserting into case_entry_form: {e}")
        await self._execute_sync_db_op(_sync_insert_case_entry_form)


        # ---- Insert into case_master if any match exists ----
        # ... (remaining logic for case_master, case_detail, decision API call) ...
        # These methods are now async, so they will be called with await self.method_name(...)
        # and they internally use _execute_sync_db_op.

        if victim_cust_id or beneficiary_cust_id:
            try:
                case_id = await self.insert_case_master( # This is correct, insert_case_master is async
                    ack_no=data.ackNo,
                    cust_id=victim_cust_id or beneficiary_cust_id,
                    complaint_type=data.subCategory,
                    source="Portal",
                    location=data.state,
                    transaction_amount=data.transactionAmount
                )
                print(f"case_master entry created with case_id: {case_id}", flush=True)
            except Exception as e:
                print(f"❌ Error inserting into case_master for ack_no {data.ackNo}: {e}", flush=True)
                raise

            # ---- Insert victim case_detail ----
            if victim_cust_id:
                print("Inserting victim details into case_detail...", flush=True)
                try:
                    await self.insert_case_details( # This is correct, insert_case_details is async
                        case_id=case_id,
                        cust_id=victim_cust_id,
                        complaint_date=data.complaintDate,
                        mobile=None, email=None, pan=None, nat_id=None,
                        card_num=data.cardNumber,
                        acct_num=data.accountNumber,
                        txn_ref_id=data.transactionId,
                        match_flag="victim"
                    )
                except Exception as e:
                    print(f"❌ Error inserting victim case_detail for ack_no {data.ackNo}: {e}", flush=True)
                    raise

            # ---- Insert beneficiary case_detail ----
            if beneficiary_cust_id:
                print("Inserting beneficiary details into case_detail...", flush=True)
                try:
                    await self.insert_case_details( # This is correct, insert_case_details is async
                        case_id=case_id,
                        cust_id=beneficiary_cust_id,
                        complaint_date=data.complaintDate,
                        mobile=None, email=None, pan=None, nat_id=None,
                        card_num=None,
                        acct_num=data.toAccount,
                        txn_ref_id=data.toTransactionId,
                        match_flag="beneficiary"
                    )
                except Exception as e:
                    print(f"❌ Error inserting beneficiary case_detail for ack_no {data.ackNo}: {e}", flush=True)
                    raise

            # ---- Call the decision API and process its response ONLY IF BENEFICIARY MATCH WAS FOUND ----
            if beneficiary_cust_id:
                api_acct_num = str(data.accountNumber) if data.accountNumber is not None else ''
                api_amount = float(data.transactionAmount) if data.transactionAmount is not None else 0.0
                api_txn_ref = str(data.transactionId) if data.transactionId is not None else ''
                api_descr = f"Transaction for ACK {data.ackNo} from case entry system."

                decision_api_url = "http://34.47.219.225:9000/api/classify-transaction"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "acct_num": api_acct_num,
                    "amount": api_amount,
                    "txn_ref": api_txn_ref,
                    "descr": api_descr
                }

                print(f"\n--- Calling decision API for beneficiary-matched case ---", flush=True)
                print(f"API URL: {decision_api_url}", flush=True)
                print(f"Payload: {json.dumps(payload, indent=2)}", flush=True)

                try:
                    response = await self._execute_sync_db_op(requests.post, decision_api_url, headers=headers, data=json.dumps(payload))
                    response.raise_for_status()
                    decision_data = await self._execute_sync_db_op(response.json)
                    print(f"Decision API raw response: {json.dumps(decision_data, indent=2)}", flush=True)

                    classification_result = decision_data.get("classification_result")
                    if classification_result:
                        print(f"DEBUG: Calling insert_case_decisions with ack_no: {data.ackNo}, result: {classification_result}", flush=True)
                        await self.insert_case_decisions(data.ackNo, classification_result)
                    else:
                        print("⚠️ No 'classification_result' found in decision API response for beneficiary-matched case.", flush=True)
                        print(f"Full API response was: {json.dumps(decision_data, indent=2)}", flush=True)

                except requests.exceptions.RequestException as e:
                    print(f"❌ Error calling decision API for beneficiary-matched case (RequestException): {e}", flush=True)
                    if hasattr(e, 'response') and e.response is not None:
                        print(f"API Response content (if available): {e.response.text}", flush=True)
                except json.JSONDecodeError as e:
                    print(f"❌ Error decoding JSON from decision API response for beneficiary-matched case (JSONDecodeError): {e}", flush=True)
                    if 'response' in locals() and response:
                        print(f"Raw response content: {response.text}", flush=True)
                except Exception as e:
                    print(f"❌ An unexpected error occurred during decision API call or processing for beneficiary-matched case: {e}", flush=True)
            else:
                print("ℹ️ No beneficiary match found. Skipping decision API call and case_decisions insertion.", flush=True)

        else:
            print("ℹ️ No victim or beneficiary match found. Skipping case_master, case_detail, and decision API call for case_decisions.", flush=True)

        # ---- Final return message ----
        print("\n--- Finalizing match_data processing ---", flush=True)
        if victim_cust_id or beneficiary_cust_id:
            return f"✅ Match found and inserted into case_master with ack_no {data.ackNo}. Decision processing attempted (for beneficiary match)."
        else:
            return f"ℹ️ No match found. Only case_entry_form entry inserted for ack_no {data.ackNo}."
