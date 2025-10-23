from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, List
import uuid
import psycopg2
import psycopg2.extras
from datetime import datetime
import time

from models.banks_v2_models import CaseEntryV2
from db.matcher import CaseEntryMatcher, save_or_update_decision
from models.base_models import ECBCaseData
from config import DB_CONNECTION_PARAMS

router = APIRouter()


def build_ack_response(ack_no: str, success: bool, message: str) -> Dict[str, Any]:
    return {
        "meta": {
            "response_code": "00" if success else "11",
            "response_message": "Success" if success else message
        },
        "data": {
            "acknowledgement_no": ack_no,
            "job_id": f"BANKS-{uuid.uuid4()}"
        }
    }


def _get_db_conn():
    # Add sane timeouts to avoid request hangs under lock/contention
    return psycopg2.connect(
        host=DB_CONNECTION_PARAMS["host"],
        port=DB_CONNECTION_PARAMS["port"],
        dbname=DB_CONNECTION_PARAMS["database"],
        user=DB_CONNECTION_PARAMS["user"],
        password=DB_CONNECTION_PARAMS["password"],
        options='-c statement_timeout=10000 -c lock_timeout=5000'
    )


def _parse_date_yyyymmdd(s: str) -> str:
    # input YYYY-MM-DD -> output YYYY-MM-DD (already in correct format)
    # Just validate the date is valid
    dt = datetime.strptime(s, "%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


def _normalize_time(s: str | None) -> str | None:
    if not s:
        return None
    # Accept HH:MM or HH:MM:SS, store as HH:MM:SS
    if len(s) == 5:
        return f"{s}:00"
    return s


def _rrn_is_numeric_and_length(rrn: str) -> bool:
    return rrn.isdigit() and 10 <= len(rrn) <= 14


def _rrn_in_range(rrn: str) -> bool:
    try:
        n = int(rrn)
        return 1_000_000_000 <= n <= 99_999_999_999_999  # 10 to 14 digits inclusive
    except Exception:
        return False


def _txn_table_exists(cur) -> bool:
    cur.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'txn'
        """
    )
    return cur.fetchone() is not None


@router.post("/api/v2/banks/case-entry", tags=["Bank Ingest v2"])
async def banks_case_entry(payload: CaseEntryV2, request: Request) -> Dict[str, Any]:
    # Phase 1: Structural validation is already performed by Pydantic.
    ack_no = payload.acknowledgement_no
    job_id = f"BANKS-{uuid.uuid4()}"
    t0 = time.perf_counter()
    print(f"[v2] START banks_case_entry ack={ack_no} job={job_id}", flush=True)

    # Enforce incidents count (already in model, but double-safeguard)
    if not payload.incidents or len(payload.incidents) == 0:
        raise HTTPException(status_code=400, detail={
            "meta": {"response_code": "11", "response_message": "Structure validation failed"},
            "data": {"acknowledgement_no": ack_no, "job_id": job_id}
        })
    if len(payload.incidents) > 25:
        raise HTTPException(status_code=400, detail={
            "meta": {"response_code": "04", "response_message": "Invalid incidents count"},
            "data": {"acknowledgement_no": ack_no, "job_id": job_id}
        })

    # Phase 1: Persist envelope and incidents; produce per-incident validation results
    transactions: List[Dict[str, Any]] = []
    incident_validations: List[Dict[str, Any]] = []  # Store validation results per incident
    vm_case_id = None  # Will be created early if VM matches

    try:
        conn = _get_db_conn()
        conn.autocommit = False
        cur = conn.cursor()

        # Initialize matcher using app's executor for creating cases in public.case_main
        matcher = CaseEntryMatcher(executor=request.app.state.executor)

        # Upsert into case_main_v2 using a separate connection to avoid transaction conflicts
        t_upsert_0 = time.perf_counter()
        case_id = None
        
        # Use a separate connection for the upsert to avoid transaction conflicts
        upsert_conn = None
        try:
            upsert_conn = _get_db_conn()
            upsert_conn.autocommit = True  # Use autocommit for this operation
            upsert_cur = upsert_conn.cursor()
            
            # First try to get existing record
            upsert_cur.execute(
                "SELECT case_id FROM public.case_main_v2 WHERE acknowledgement_no = %s",
                (ack_no,)
            )
            row = upsert_cur.fetchone()
            if row:
                case_id = row[0]
                print(f"[v2] Found existing case_main_v2 case_id={case_id}", flush=True)
            else:
                # Insert new record
                upsert_cur.execute(
                    """
                    INSERT INTO public.case_main_v2 (
                        acknowledgement_no, sub_category, requestor, payer_bank, payer_bank_code,
                        mode_of_payment, payer_mobile_number, payer_account_number, state, district,
                        transaction_type, wallet
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (acknowledgement_no) DO NOTHING
                    RETURNING case_id
                    """,
                    (
                        ack_no,
                        payload.sub_category,
                        payload.instrument.requestor,
                        payload.instrument.payer_bank,
                        payload.instrument.payer_bank_code,
                        payload.instrument.mode_of_payment,
                        payload.instrument.payer_mobile_number,
                        payload.instrument.payer_account_number,
                        payload.instrument.state,
                        payload.instrument.district,
                        payload.instrument.transaction_type,
                        payload.instrument.wallet,
                    ),
                )
                result = upsert_cur.fetchone()
                if result:
                    case_id = result[0]
                    print(f"[v2] Inserted new case_main_v2 case_id={case_id}", flush=True)
                else:
                    # Conflict occurred, fetch the existing record
                    upsert_cur.execute(
                        "SELECT case_id FROM public.case_main_v2 WHERE acknowledgement_no = %s",
                        (ack_no,)
                    )
                    row = upsert_cur.fetchone()
                    case_id = row[0] if row else None
                    print(f"[v2] Conflict resolved, found case_id={case_id}", flush=True)
                    
        except Exception as e:
            print(f"[v2] Error in upsert: {e}", flush=True)
            raise
        finally:
            if upsert_conn:
                upsert_conn.close()
                
        if case_id is None:
            raise psycopg2.Error("Failed to upsert case_main_v2")
            
        print(f"[v2] Upsert case_main_v2 case_id={case_id} dt={(time.perf_counter()-t_upsert_0)*1000:.1f}ms", flush=True)

        # PRIORITY CHECK: VM Match - Check if payer_account_number matches any customer
        # This happens BEFORE any RRN validation
        print(f"[v2] Checking VM match for payer_account: {payload.instrument.payer_account_number}", flush=True)
        cur.execute(
            "SELECT cust_id FROM public.account_customer WHERE acc_num = %s LIMIT 1",
            (payload.instrument.payer_account_number,)
        )
        vm_row = cur.fetchone()
        
        if not vm_row:
            # NO VM MATCH - Return error immediately, don't proceed
            conn.rollback()
            conn.close()
            print(f"[v2] NO VM MATCH for payer_account: {payload.instrument.payer_account_number}", flush=True)
            return {
                "meta": {
                    "response_code": "20",
                    "response_message": "No matching customer account found"
                },
                "data": {
                    "acknowledgement_no": ack_no,
                    "job_id": job_id,
                    "error": f"Payer account number '{payload.instrument.payer_account_number}' does not match any customer in the system."
                }
            }
        
        # VM MATCH FOUND - Get customer ID and CREATE VM CASE IMMEDIATELY (before RRN validation)
        victim_cust_id = vm_row[0]
        print(f"[v2] VM MATCH FOUND! cust_id={victim_cust_id}", flush=True)
        
        # Commit what we have so far before creating case
        conn.commit()
        
        # Create VM case NOW
        vm_case_id = await matcher.insert_into_case_main(
            case_type="VM",
            source_ack_no=f"{ack_no}_VM",
            cust_id=victim_cust_id,
            acc_num=payload.instrument.payer_account_number,
            is_operational=True,
            status='New',
            decision_input='Pending Review',
            remarks_input=f"Automated VM case from bank ingest for {ack_no}",
            source_bene_accno=None,
            customer_full_name=None
        )
        await save_or_update_decision(request.app.state.executor, vm_case_id, {"comments": "Initial VM case created", "assignedEmployee": "jalaj"})
        with _get_db_conn() as c2:
            with c2.cursor() as k:
                k.execute("INSERT INTO public.case_details_1 (cust_id, casetype, acc_no, match_flag, creation_timestamp) VALUES (%s, %s, %s, %s, NOW())", (victim_cust_id, "VM", payload.instrument.payer_account_number, "VM Match"))
                c2.commit()
        
        print(f"[v2] VM CASE CREATED! case_id={vm_case_id}", flush=True)

        # Prepare to insert each incident and validate RRNs
        has_txn_table = _txn_table_exists(cur)
        t_inc_total = 0.0
        # Defer PSA/ECBT/ECBNT case creation until after all incidents processed
        deferred_actions: List[Dict[str, Any]] = []
        rrn_to_txn_idx: Dict[str, int] = {}
        for inc in payload.incidents:
            rrn = inc.rrn
            try:
                t_inc_0 = time.perf_counter()
                
                # Initialize validation result for this incident
                validation_result = {
                    "rrn": rrn,
                    "amount": str(inc.amount),
                    "transaction_date": inc.transaction_date,
                    "transaction_time": inc.transaction_time,
                    "disputed_amount": str(inc.disputed_amount),
                    "layer": inc.layer,
                    "validation_status": "pending",
                    "validation_message": "",
                    "matched_txn": None,
                    "error": None
                }
                
                # Check if RRN already exists in case_incidents table (for duplicate check)
                cur.execute("SELECT case_id FROM public.case_incidents WHERE rrn = %s", (rrn,))
                existing_rrn = cur.fetchone()
                
                if existing_rrn:
                    # RRN already exists - mark as duplicate but STILL STORE IT
                    validation_result["validation_status"] = "duplicate"
                    validation_result["validation_message"] = "Duplicate RRN - already exists in system"
                    validation_result["error"] = f"RRN '{rrn}' already exists"
                    incident_validations.append(validation_result)
                    
                    # Store in transactions response with error status
                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "status_code": "16",
                        "response_message": "Duplicate RRN"
                    })
                    t_inc_total += time.perf_counter()-t_inc_0
                    continue  # Skip to next incident
                
                # Insert incident (always store, even if validation fails later)
                cur.execute(
                    """
                    INSERT INTO public.case_incidents (
                        case_id, amount, rrn, transaction_date, transaction_time, disputed_amount, layer
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        case_id,
                        float(inc.amount),
                        rrn,
                        _parse_date_yyyymmdd(inc.transaction_date),
                        _normalize_time(inc.transaction_time),
                        float(inc.disputed_amount),
                        int(inc.layer),
                    ),
                )

                # Now perform RRN validation and txn table lookup
                if not _rrn_is_numeric_and_length(rrn):
                    validation_result["validation_status"] = "invalid_format"
                    validation_result["validation_message"] = "Invalid RRN format (must be 10-14 digits)"
                    validation_result["error"] = "Invalid RRN"
                    incident_validations.append(validation_result)
                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "status_code": "02",
                        "response_message": "Invalid RRN"
                    })
                    t_inc_total += time.perf_counter()-t_inc_0
                    continue

                if not _rrn_in_range(rrn):
                    validation_result["validation_status"] = "invalid_range"
                    validation_result["validation_message"] = "Invalid RRN range"
                    validation_result["error"] = "Invalid RRN range"
                    incident_validations.append(validation_result)
                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "status_code": "03",
                        "response_message": "Invalid RRN range"
                    })
                    t_inc_total += time.perf_counter()-t_inc_0
                    continue

                if not has_txn_table:
                    validation_result["validation_status"] = "pending"
                    validation_result["validation_message"] = "Transaction table not available"
                    incident_validations.append(validation_result)
                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "status_code": "31",
                        "response_message": "Pending"
                    })
                    t_inc_total += time.perf_counter()-t_inc_0
                    continue

                # Lookup RRN in txn table
                cur.execute(
                    "SELECT id, acct_num, bene_acct_num, amount, txn_date, txn_time, channel, descr FROM public.txn WHERE rrn = %s",
                    (rrn,)
                )
                rows = cur.fetchall()
                if len(rows) == 0:
                    validation_result["validation_status"] = "not_found"
                    validation_result["validation_message"] = "No transaction found in bank records"
                    validation_result["error"] = "Record not found"
                    incident_validations.append(validation_result)
                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "status_code": "01",
                        "response_message": "Record not found"
                    })
                    t_inc_total += time.perf_counter()-t_inc_0
                elif len(rows) > 1:
                    validation_result["validation_status"] = "multiple_found"
                    validation_result["validation_message"] = "Multiple transactions found for this RRN"
                    validation_result["error"] = "Multiple Records Found"
                    incident_validations.append(validation_result)
                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "status_code": "15",
                        "response_message": "Multiple Records Found"
                    })
                    t_inc_total += time.perf_counter()-t_inc_0
                else:
                    # SUCCESS - Found exactly 1 matching transaction
                    _id, acct_num, bene_acct_num, amount, txn_date, txn_time, channel, descr = rows[0]
                    
                    # Store matched transaction details in validation result
                    validation_result["validation_status"] = "matched"
                    validation_result["validation_message"] = "Transaction found and matched successfully"
                    validation_result["matched_txn"] = {
                        "txn_id": _id,
                        "acct_num": acct_num,
                        "bene_acct_num": bene_acct_num,
                        "amount": str(amount),
                        "txn_date": txn_date.strftime('%Y-%m-%d') if txn_date else None,
                        "txn_time": str(txn_time) if txn_time else None,
                        "channel": channel or "N/A",
                        "descr": descr or "N/A",
                        "rrn": rrn
                    }

                    # Resolve beneficiary cust_id for PSA
                    cur.execute("SELECT cust_id FROM public.account_customer WHERE acc_num = %s LIMIT 1", (bene_acct_num,))
                    row_b = cur.fetchone()
                    bene_cust_id = row_b[0] if row_b else None

                    # ECBT/ECBNT Logic (ECB Flow):
                    # Step 1: Check if bene_acct_num from txn matches bene_acct_num in acc_bene table
                    # FIX: Find ALL customers who have added this beneficiary (not just one)
                    
                    # Query acc_bene and join with account_customer to get ALL valid customers
                    cur.execute("""
                        SELECT ab.cust_acct_num, ab.bene_acct_num, ac.cust_id
                        FROM public.acc_bene ab
                        JOIN public.account_customer ac ON ab.cust_acct_num = ac.acc_num
                        WHERE ab.bene_acct_num = %s
                    """, (bene_acct_num,))
                    
                    acc_bene_rows = cur.fetchall()  # Get ALL customers with this beneficiary
                    
                    # Add validation result to array
                    incident_validations.append(validation_result)
                    
                    # Create ECB cases for ALL customers who have this beneficiary
                    if acc_bene_rows:
                        for acc_bene_row in acc_bene_rows:
                            ecb_cust_acct_num = acc_bene_row[0]  # cust_acct_num from acc_bene
                            ecb_bene_acct_num = acc_bene_row[1]  # bene_acct_num from acc_bene
                            ecb_cust_id = acc_bene_row[2]  # cust_id from account_customer
                            
                            # Step 2: Check if there's a transaction between this customer and beneficiary
                            cur.execute("""
                                SELECT 1 FROM public.txn 
                                WHERE acct_num = %s AND bene_acct_num = %s 
                                LIMIT 1
                            """, (ecb_cust_acct_num, ecb_bene_acct_num))
                            
                            txn_exists = bool(cur.fetchone())
                            
                            # Create action for this specific customer
                            action = {
                                "rrn": rrn,
                                "bene_cust_id": bene_cust_id,
                                "bene_acc": bene_acct_num,
                                "psa": bool(bene_cust_id),  # True if bene_acct_num matches account_customer.acc_num
                                "ecbt": txn_exists,  # True if transaction found between this customer and beneficiary
                                "ecbnt": not txn_exists,  # True if NO transaction found between this customer and beneficiary
                                "ecb_cust_id": ecb_cust_id,  # Customer ID for ECB cases
                                "ecb_cust_acct_num": ecb_cust_acct_num,  # Customer account number for ECB cases
                                "ecb_bene_acct_num": ecb_bene_acct_num  # Beneficiary account number for ECB cases
                            }
                            print(f"[v2] 📋 Created action for customer {ecb_cust_id} (account: {ecb_cust_acct_num}): PSA={action['psa']}, ECBT={action['ecbt']}, ECBNT={action['ecbnt']}", flush=True)
                            deferred_actions.append(action)
                    else:
                        # No ECB match, but still need PSA action
                        action = {
                            "rrn": rrn,
                            "bene_cust_id": bene_cust_id,
                            "bene_acc": bene_acct_num,
                            "psa": bool(bene_cust_id),  # True if bene_acct_num matches account_customer.acc_num
                            "ecbt": False,
                            "ecbnt": False,
                            "ecb_cust_id": None,
                            "ecb_cust_acct_num": None,
                            "ecb_bene_acct_num": None
                        }
                        deferred_actions.append(action)

                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "payee_account_number": bene_acct_num,
                        "amount": str(amount),
                        "transaction_datetime": f"{txn_date} {txn_time}",
                        "root_account_number": acct_num,
                        "root_rrn_transaction_id": rrn,
                        "status_code": "00",
                        "response_message": "SUCCESS"
                    })
                    rrn_to_txn_idx[rrn] = len(transactions) - 1
                    t_inc_total += time.perf_counter()-t_inc_0
            except psycopg2.errors.UniqueViolation:
                # Should not occur due to ON CONFLICT DO NOTHING, but keep fallback
                pass
            except psycopg2.Error as db_err:
                # Generic DB error for this incident (temporary: include reason for debugging)
                transactions.append({
                    "rrn_transaction_id": rrn,
                    "status_code": "32",
                    "response_message": "Failure",
                    "error": str(db_err)
                })

        # Store incident validation results in database for frontend retrieval
        # Create a simple JSON storage table if needed or link to VM case
        validation_conn = _get_db_conn()
        validation_cur = validation_conn.cursor()
        
        # Store validation results linked to the VM case
        for val_result in incident_validations:
            validation_cur.execute("""
                INSERT INTO public.incident_validation_results 
                (case_id, rrn, validation_status, validation_message, matched_txn_data, error_message, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (
                vm_case_id,
                val_result["rrn"],
                val_result["validation_status"],
                val_result["validation_message"],
                psycopg2.extras.Json(val_result["matched_txn"]) if val_result["matched_txn"] else None,
                val_result["error"]
            ))
        validation_conn.commit()
        validation_cur.close()
        validation_conn.close()
        
        conn.commit()
        print(f"[v2] Phase1 done (upsert+incidents+validation) dt={(time.perf_counter()-t0)*1000:.1f}ms inc_total={t_inc_total*1000:.1f}ms validations={len(incident_validations)}", flush=True)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[v2] ERROR Phase1: {e}", flush=True)
        # Internal error
        raise HTTPException(status_code=500, detail={
            "meta": {"response_code": "99", "response_message": "Internal error"},
            "data": {"acknowledgement_no": ack_no, "job_id": job_id, "error": str(e)}
        })
    finally:
        try:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
        except Exception:
            pass

    # Phase 2: Create PSA/ECBT/ECBNT cases (VM already created in Phase 1)
    try:
        matcher = CaseEntryMatcher(executor=request.app.state.executor)
        psa_case_id = None  # Track if we create a PSA case
        ecbt_case_ids = []  # Track all ECBT case IDs
        ecbnt_case_ids = []  # Track all ECBNT case IDs
        
        # Deduplicate actions to prevent duplicate source_ack_no errors
        unique_actions = {}
        for action in deferred_actions:
            # Create unique key for ECBT/ECBNT actions
            if action["ecb_cust_id"] and action["ecb_bene_acct_num"]:
                key = f"{action['ecb_cust_id']}_{action['ecb_bene_acct_num']}"
                if key not in unique_actions:
                    unique_actions[key] = action
                else:
                    # Merge flags if duplicate found
                    existing = unique_actions[key]
                    existing["ecbt"] = existing["ecbt"] or action["ecbt"]
                    existing["ecbnt"] = existing["ecbnt"] or action["ecbnt"]
                    existing["psa"] = existing["psa"] or action["psa"]
            else:
                # For PSA-only actions, use RRN as key
                key = f"psa_{action['rrn']}"
                if key not in unique_actions:
                    unique_actions[key] = action
        
        deduplicated_actions = list(unique_actions.values())
        print(f"[v2] 🚀 Phase 2: Processing {len(deduplicated_actions)} deduplicated actions (from {len(deferred_actions)} original) for PSA/ECBT/ECBNT case creation", flush=True)
        
        for action in deduplicated_actions:
            rrn = action["rrn"]
            idx = rrn_to_txn_idx.get(rrn)
            if idx is None:
                continue
            txn_entry = transactions[idx]

            # PSA - Created if RRN found AND bene_acct_num matches account_customer.acc_num
            if action["psa"] and not psa_case_id:  # Only create one PSA case
                psa_case_id = await matcher.insert_into_case_main(
                    case_type="PSA",
                    source_ack_no=f"{ack_no}_PSA",
                    cust_id=action["bene_cust_id"],
                    acc_num=action["bene_acc"],
                    is_operational=True,
                    status='New',
                    decision_input='Pending Review',
                    remarks_input=f"Automated PSA case from bank ingest for {ack_no}",
                    source_bene_accno=action["bene_acc"],
                    customer_full_name=None
                )
                await save_or_update_decision(request.app.state.executor, psa_case_id, {"comments": "Initial PSA case created", "assignedEmployee": "jalaj"})
                with _get_db_conn() as c2:
                    with c2.cursor() as k:
                        k.execute("INSERT INTO public.case_details_1 (cust_id, casetype, acc_no, match_flag, creation_timestamp) VALUES (%s, %s, %s, %s, NOW())", (action["bene_cust_id"], "PSA", action["bene_acc"], "PSA Match"))
                        c2.commit()
                        
                # Store validation results for PSA case too
                psa_validation_conn = _get_db_conn()
                psa_validation_cur = psa_validation_conn.cursor()
                for val_result in incident_validations:
                    if val_result["validation_status"] == "matched":  # Only matched incidents
                        psa_validation_cur.execute("""
                            INSERT INTO public.incident_validation_results 
                            (case_id, rrn, validation_status, validation_message, matched_txn_data, error_message, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        """, (
                            psa_case_id,
                            val_result["rrn"],
                            val_result["validation_status"],
                            val_result["validation_message"],
                            psycopg2.extras.Json(val_result["matched_txn"]) if val_result["matched_txn"] else None,
                            val_result["error"]
                        ))
                psa_validation_conn.commit()
                psa_validation_cur.close()
                psa_validation_conn.close()

            # ECBT - Existing Customer Beneficiary with Transaction (can be multiple per RRN)
            ecbt_case_id = None
            if action["ecbt"] and action["ecb_cust_id"]:
                print(f"[v2] 🔍 Creating ECBT case for customer {action['ecb_cust_id']} (account: {action['ecb_cust_acct_num']}) - HAS transaction with beneficiary {action['ecb_bene_acct_num']}", flush=True)
                ecb_payload = ECBCaseData(
                    sourceAckNo=f"{ack_no}_ECBT_{action['ecb_cust_id']}_{action['ecb_bene_acct_num']}",  # Unique ACK per customer-beneficiary pair
                    customerId=action["ecb_cust_id"],
                    customerAccountNumber=action["ecb_cust_acct_num"],
                    beneficiaryAccountNumber=action["ecb_bene_acct_num"],
                    hasTransaction=True,
                    remarks=f"Automated ECBT case from bank ingest. RRN {rrn}. Customer: {action['ecb_cust_id']}, Account: {action['ecb_cust_acct_num']}, Beneficiary: {action['ecb_bene_acct_num']}",
                    location=None,
                    disputedAmount=None
                )
                ecbt_result = await matcher.create_ecb_case(ecb_payload, created_by_user="System")
                ecbt_case_id = (ecbt_result or {}).get("case_id")
                if ecbt_case_id:
                    ecbt_case_ids.append(ecbt_case_id)
                    print(f"[v2] ✅ Created ECBT case {ecbt_case_id} for customer {action['ecb_cust_id']} (account: {action['ecb_cust_acct_num']})", flush=True)
                else:
                    print(f"[v2] ❌ Failed to create ECBT case for customer {action['ecb_cust_id']}", flush=True)

            # ECBNT - Existing Customer Beneficiary with No Transaction (can be multiple per RRN)
            ecbnt_case_id = None
            if action["ecbnt"] and action["ecb_cust_id"]:
                print(f"[v2] 🔍 Creating ECBNT case for customer {action['ecb_cust_id']} (account: {action['ecb_cust_acct_num']}) - NO transaction with beneficiary {action['ecb_bene_acct_num']}", flush=True)
                ecbn_payload = ECBCaseData(
                    sourceAckNo=f"{ack_no}_ECBNT_{action['ecb_cust_id']}_{action['ecb_bene_acct_num']}",  # Unique ACK per customer-beneficiary pair
                    customerId=action["ecb_cust_id"],
                    customerAccountNumber=action["ecb_cust_acct_num"],
                    beneficiaryAccountNumber=action["ecb_bene_acct_num"],
                    hasTransaction=False,
                    remarks=f"Automated ECBNT case from bank ingest. RRN {rrn}. Customer: {action['ecb_cust_id']}, Account: {action['ecb_cust_acct_num']}, Beneficiary: {action['ecb_bene_acct_num']}",
                    location=None,
                    disputedAmount=None
                )
                ecbnt_result = await matcher.create_ecb_case(ecbn_payload, created_by_user="System")
                ecbnt_case_id = (ecbnt_result or {}).get("case_id")
                if ecbnt_case_id:
                    ecbnt_case_ids.append(ecbnt_case_id)
                    print(f"[v2] ✅ Created ECBNT case {ecbnt_case_id} for customer {action['ecb_cust_id']} (account: {action['ecb_cust_acct_num']})", flush=True)
                else:
                    print(f"[v2] ❌ Failed to create ECBNT case for customer {action['ecb_cust_id']}", flush=True)

            # Collect ECB case IDs for this RRN
            if not hasattr(txn_entry, '_ecbt_cases'):
                txn_entry["ecbt_case_ids"] = []
                txn_entry["ecbnt_case_ids"] = []
            if ecbt_case_id:
                txn_entry["ecbt_case_ids"].append(ecbt_case_id)
            if ecbnt_case_id:
                txn_entry["ecbnt_case_ids"].append(ecbnt_case_id)
            
            # Keep backward compatibility with single case ID fields
            if not txn_entry.get("psa_case_id"):
                txn_entry["psa_case_id"] = psa_case_id
            if ecbt_case_id and not txn_entry.get("ecbt_case_id"):
                txn_entry["ecbt_case_id"] = ecbt_case_id  # First ECBT case for backward compatibility
            if ecbnt_case_id and not txn_entry.get("ecbnt_case_id"):
                txn_entry["ecbnt_case_id"] = ecbnt_case_id  # First ECBNT case for backward compatibility
    except Exception as e:
        print(f"[v2] Phase2 warning: {e}", flush=True)

    # Final combined response with ack and per-incident details
    print(f"[v2] END banks_case_entry ack={ack_no} job={job_id} total_dt={(time.perf_counter()-t0)*1000:.1f}ms", flush=True)
    print(f"[v2] 📊 Case Creation Summary: VM={vm_case_id}, PSA={psa_case_id}, ECBT={len(ecbt_case_ids)} cases, ECBNT={len(ecbnt_case_ids)} cases", flush=True)
    return {
        "meta": {"response_code": "00", "response_message": "Success"},
        "data": {
            "acknowledgement_no": ack_no,
            "job_id": job_id,
            "vm_case_id": vm_case_id,  # VM case created immediately
            "psa_case_id": psa_case_id if 'psa_case_id' in locals() else None,
            "ecbt_case_ids": ecbt_case_ids,  # All ECBT case IDs
            "ecbnt_case_ids": ecbnt_case_ids  # All ECBNT case IDs
        },
        "transactions": transactions
    }


@router.post("/api/v2/banks/case-entry/{ack_no}/respond", tags=["Bank Ingest v2"])
async def banks_case_entry_respond(ack_no: str, request: Request) -> Dict[str, Any]:
    """
    Respond to bank for a case entry. Marks VM case as closed and returns detailed transaction response.
    This endpoint is called when user reviews the VM case and clicks "Respond" button.
    Accepts manually selected transactions to replace unmatched RRNs.
    """
    try:
        # Parse request body for manually selected transactions
        body = await request.json() if request.headers.get('content-length') else {}
        manually_selected_txns = body.get('manually_selected_transactions', [])
        
        print(f"[v2] Respond endpoint - received {len(manually_selected_txns)} manually selected transactions", flush=True)
        
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get case_main_v2 data
        cur.execute("""
            SELECT case_id, acknowledgement_no
            FROM public.case_main_v2
            WHERE acknowledgement_no = %s
        """, (ack_no,))
        
        case_main_v2_data = cur.fetchone()
        if not case_main_v2_data:
            raise HTTPException(status_code=404, detail=f"Case {ack_no} not found")
        
        v2_case_id = case_main_v2_data['case_id']
        
        # Get VM case
        cur.execute("""
            SELECT case_id, status
            FROM public.case_main
            WHERE source_ack_no = %s
        """, (f"{ack_no}_VM",))
        
        vm_case = cur.fetchone()
        if not vm_case:
            raise HTTPException(status_code=404, detail=f"VM case not found for {ack_no}")
        
        vm_case_id = vm_case['case_id']
        
        # Mark VM case as Closed
        cur.execute("""
            UPDATE public.case_main
            SET status = 'Closed'
            WHERE case_id = %s
        """, (vm_case_id,))
        conn.commit()
        
        print(f"[v2] VM case {vm_case_id} marked as Closed", flush=True)
        
        # Get all validation results for this VM case
        cur.execute("""
            SELECT rrn, validation_status, validation_message, matched_txn_data, error_message
            FROM public.incident_validation_results
            WHERE case_id = %s
            ORDER BY created_at
        """, (vm_case_id,))
        
        validations = cur.fetchall()
        
        # Get incidents data
        cur.execute("""
            SELECT rrn, amount, disputed_amount, transaction_date, transaction_time
            FROM public.case_incidents
            WHERE case_id = %s
        """, (v2_case_id,))
        
        incidents = cur.fetchall()
        
        # Get PSA case if exists
        cur.execute("""
            SELECT case_id FROM public.case_main WHERE source_ack_no = %s
        """, (f"{ack_no}_PSA",))
        psa_row = cur.fetchone()
        psa_case_id = psa_row['case_id'] if psa_row else None
        
        # Get ECBT cases if exist
        cur.execute("""
            SELECT case_id FROM public.case_main WHERE source_ack_no LIKE %s
        """, (f"{ack_no}_ECBT%",))
        ecbt_rows = cur.fetchall()
        ecbt_case_ids = [row['case_id'] for row in ecbt_rows]
        
        # Get ECBNT cases if exist
        cur.execute("""
            SELECT case_id FROM public.case_main WHERE source_ack_no LIKE %s
        """, (f"{ack_no}_ECBNT%",))
        ecbnt_rows = cur.fetchall()
        ecbnt_case_ids = [row['case_id'] for row in ecbnt_rows]
        
        cur.close()
        conn.close()
        
        # Build detailed transaction response
        transactions = []
        
        # Track which manually selected transactions have been used
        manual_txns_used = []
        
        for val in validations:
            rrn = val['rrn']
            matched_txn = val['matched_txn_data']
            
            # Find corresponding incident
            incident = next((inc for inc in incidents if inc['rrn'] == rrn), None)
            
            # Determine status code based on validation
            if val['validation_status'] == 'matched':
                status_code = "00"
                response_message = "SUCCESS"
            elif val['validation_status'] == 'duplicate':
                status_code = "16"
                response_message = "Duplicate RRN"
            elif val['validation_status'] == 'invalid_format':
                status_code = "02"
                response_message = "Invalid RRN"
            elif val['validation_status'] == 'invalid_range':
                status_code = "03"
                response_message = "Invalid RRN range"
            elif val['validation_status'] == 'not_found':
                status_code = "01"
                response_message = "Record not found"
            elif val['validation_status'] == 'multiple_found':
                status_code = "15"
                response_message = "Multiple Records Found"
            else:
                status_code = "31"
                response_message = "Pending"
            
            txn_entry = {
                "rrn_transaction_id": rrn,
                "status_code": status_code,
                "response_message": response_message
            }
            
            # Add matched transaction details if available
            if matched_txn:
                txn_entry["payee_account_number"] = matched_txn.get("bene_acct_num")
                txn_entry["amount"] = matched_txn.get("amount")
                txn_entry["transaction_datetime"] = f"{matched_txn.get('txn_date')} {matched_txn.get('txn_time')}"
                txn_entry["root_account_number"] = matched_txn.get("acct_num")
                txn_entry["root_rrn_transaction_id"] = rrn
            else:
                txn_entry["payee_account_number"] = None
                txn_entry["amount"] = str(incident['amount']) if incident else None
                txn_entry["transaction_datetime"] = f"{incident['transaction_date']} {incident['transaction_time']}" if incident else None
                txn_entry["root_account_number"] = None
                txn_entry["root_rrn_transaction_id"] = rrn
            
            # Add case IDs
            txn_entry["psa_case_id"] = psa_case_id
            txn_entry["ecbt_case_id"] = ecbt_case_ids[0] if ecbt_case_ids else None
            txn_entry["ecbnt_case_id"] = ecbnt_case_ids[0] if ecbnt_case_ids else None
            
            transactions.append(txn_entry)
        
        # Add manually selected transactions to response (for unmatched RRNs)
        for manual_txn in manually_selected_txns:
            manual_entry = {
                "rrn_transaction_id": manual_txn.get("rrn"),
                "status_code": "00",
                "response_message": "SUCCESS - Manually Matched",
                "payee_account_number": manual_txn.get("bene_acct_num"),
                "amount": manual_txn.get("amount"),
                "transaction_datetime": f"{manual_txn.get('txn_date')} {manual_txn.get('txn_time')}",
                "root_account_number": manual_txn.get("acct_num"),
                "root_rrn_transaction_id": manual_txn.get("rrn"),
                "psa_case_id": None,
                "ecbt_case_id": None,
                "ecbnt_case_id": None,
                "manually_matched": True
            }
            transactions.append(manual_entry)
            manual_txns_used.append(manual_txn.get("rrn"))
        
        print(f"[v2] Response includes {len(manual_txns_used)} manually matched transactions", flush=True)
        
        # Return detailed response
        return {
            "meta": {"response_code": "00", "response_message": "Response sent successfully"},
            "data": {
                "acknowledgement_no": ack_no,
                "vm_case_id": vm_case_id,
                "psa_case_id": psa_case_id,
                "ecbt_case_ids": ecbt_case_ids,
                "ecbnt_case_ids": ecbnt_case_ids,
                "status": "responded"
            },
            "transactions": transactions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[v2] Error in respond endpoint for {ack_no}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/api/v2/banks/case-data/{ack_no}", tags=["Bank Ingest v2"])
async def get_banks_v2_case_data(ack_no: str) -> Dict[str, Any]:
    """
    Get case data from banks_v2 tables for display in frontend I4C section.
    This endpoint fetches data from case_main_v2, case_incidents, and related tables.
    """
    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get case_main_v2 data
        cur.execute("""
            SELECT 
                case_id, acknowledgement_no, sub_category, requestor, 
                payer_bank, payer_bank_code, mode_of_payment, 
                payer_mobile_number, payer_account_number, state, district, 
                transaction_type, wallet, created_at
            FROM public.case_main_v2 
            WHERE acknowledgement_no = %s
        """, (ack_no,))
        
        case_data = cur.fetchone()
        if not case_data:
            raise HTTPException(status_code=404, detail=f"Case {ack_no} not found in banks_v2 system")
        
        # Get incidents data
        cur.execute("""
            SELECT 
                incident_id, amount, rrn, transaction_date, transaction_time, 
                disputed_amount, layer
            FROM public.case_incidents 
            WHERE case_id = %s
            ORDER BY incident_id
        """, (case_data['case_id'],))
        
        incidents = cur.fetchall()
        
        # Get card details if any
        cur.execute("""
            SELECT first6digit, last4digit, cardlength
            FROM public.card_details_v2 
            WHERE case_id = %s
        """, (case_data['case_id'],))
        
        card_details = cur.fetchone()
        
        # Get UPI details if any
        cur.execute("""
            SELECT wallet
            FROM public.upi_details_v2 
            WHERE case_id = %s
        """, (case_data['case_id'],))
        
        upi_details = cur.fetchone()
        
        cur.close()
        conn.close()
        
        # Format response to match frontend expectations
        response_data = {
            "acknowledgement_no": case_data['acknowledgement_no'],
            "sub_category": case_data['sub_category'],
            "instrument": {
                "requestor": case_data['requestor'],
                "payer_bank": case_data['payer_bank'],
                "payer_bank_code": case_data['payer_bank_code'],
                "mode_of_payment": case_data['mode_of_payment'],
                "payer_mobile_number": case_data['payer_mobile_number'],
                "payer_account_number": case_data['payer_account_number'],
                "state": case_data['state'],
                "district": case_data['district'],
                "transaction_type": case_data['transaction_type'],
                "wallet": case_data['wallet']
            },
            "incidents": [
                {
                    "amount": str(incident['amount']),
                    "rrn": incident['rrn'],
                    "transaction_date": incident['transaction_date'].strftime('%d-%m-%Y') if incident['transaction_date'] else None,
                    "transaction_time": str(incident['transaction_time']) if incident['transaction_time'] else None,
                    "disputed_amount": str(incident['disputed_amount']),
                    "layer": incident['layer']
                }
                for incident in incidents
            ],
            "card_details": card_details if card_details else None,
            "upi_details": upi_details if upi_details else None,
            "created_at": case_data['created_at'].isoformat() if case_data['created_at'] else None
        }
        
        return {
            "success": True,
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[v2] Error fetching case data for {ack_no}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/api/v2/banks/transaction-details/{ack_no}", tags=["Bank Ingest v2"])
async def get_banks_v2_transaction_details(ack_no: str) -> Dict[str, Any]:
    """
    Get transaction details from banks_v2 tables for display in frontend transaction sections.
    This endpoint fetches incident data and formats it for transaction display.
    """
    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get case_main_v2 data to get case_id
        cur.execute("""
            SELECT case_id, acknowledgement_no, sub_category, mode_of_payment
            FROM public.case_main_v2 
            WHERE acknowledgement_no = %s
        """, (ack_no,))
        
        case_data = cur.fetchone()
        if not case_data:
            raise HTTPException(status_code=404, detail=f"Case {ack_no} not found in banks_v2 system")
        
        # Get incidents data formatted for transaction display
        cur.execute("""
            SELECT 
                incident_id, amount, rrn, transaction_date, transaction_time, 
                disputed_amount, layer
            FROM public.case_incidents 
            WHERE case_id = %s
            ORDER BY incident_id
        """, (case_data['case_id'],))
        
        incidents = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Format response to match frontend transaction expectations
        transaction_details = []
        for incident in incidents:
            transaction_details.append({
                "txn_date": incident['transaction_date'].strftime('%d-%m-%Y') if incident['transaction_date'] else None,
                "txn_time": str(incident['transaction_time']) if incident['transaction_time'] else None,
                "bene_acct_num": "N/A",  # Not available in banks_v2 data
                "amount": str(incident['amount']),
                "channel": case_data['mode_of_payment'] or "N/A",
                "txn_ref": incident['rrn'],
                "descr": f"Layer {incident['layer']} - Disputed: ₹{incident['disputed_amount']}",
                "is_bene_match": False,  # Not applicable for banks_v2 data
                "disputed_amount": str(incident['disputed_amount']),
                "layer": incident['layer']
            })
        
        return {
            "success": True,
            "data": {
                "acknowledgement_no": case_data['acknowledgement_no'],
                "sub_category": case_data['sub_category'],
                "mode_of_payment": case_data['mode_of_payment'],
                "transactions": transaction_details,
                "total_value_at_risk": sum(float(txn['amount']) for txn in transaction_details)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[v2] Error fetching transaction details for {ack_no}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/api/v2/banks/victim-transactions/{account_number}", tags=["Bank Ingest v2"])
async def get_victim_all_transactions(account_number: str) -> Dict[str, Any]:
    """
    Get ALL transactions by victim account number for manual review.
    This is shown when there are unmatched RRNs and user needs to manually verify.
    """
    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Fetch ALL transactions where victim is the payer
        cur.execute("""
            SELECT 
                id, txn_date, txn_time, acct_num, bene_acct_num,
                amount, channel, rrn, descr
            FROM public.txn
            WHERE acct_num = %s
            ORDER BY txn_date DESC, txn_time DESC
            LIMIT 100
        """, (account_number,))
        
        transactions = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Format transactions
        transaction_list = []
        for txn in transactions:
            transaction_list.append({
                "id": txn['id'],
                "txn_date": txn['txn_date'].strftime('%d-%m-%Y') if txn['txn_date'] else None,
                "txn_time": str(txn['txn_time']) if txn['txn_time'] else None,
                "acct_num": txn['acct_num'],
                "bene_acct_num": txn['bene_acct_num'],
                "amount": str(txn['amount']),
                "channel": txn['channel'] or "N/A",
                "rrn": txn['rrn'],
                "descr": txn['descr'] or "N/A"
            })
        
        return {
            "success": True,
            "data": {
                "account_number": account_number,
                "transactions": transaction_list,
                "total_count": len(transaction_list),
                "total_amount": sum(float(txn['amount']) for txn in transaction_list)
            }
        }
        
    except Exception as e:
        print(f"[v2] Error fetching victim transactions for {account_number}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/api/v2/banks/incident-validations/{case_id}", tags=["Bank Ingest v2"])
async def get_incident_validations(case_id: int) -> Dict[str, Any]:
    """
    Get incident validation results for a case (VM or PSA).
    Returns both the raw I4C incidents and the matched/validated bank transactions.
    """
    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get all validation results for this case
        cur.execute("""
            SELECT 
                id, case_id, rrn, validation_status, validation_message,
                matched_txn_data, error_message, created_at
            FROM public.incident_validation_results
            WHERE case_id = %s
            ORDER BY created_at
        """, (case_id,))
        
        validations = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Format response
        validation_results = []
        for val in validations:
            validation_results.append({
                "rrn": val['rrn'],
                "validation_status": val['validation_status'],
                "validation_message": val['validation_message'],
                "matched_txn": val['matched_txn_data'],  # JSON data
                "error": val['error_message'],
                "created_at": val['created_at'].isoformat() if val['created_at'] else None
            })
        
        return {
            "success": True,
            "data": {
                "case_id": case_id,
                "validations": validation_results,
                "total_incidents": len(validation_results),
                "matched_count": sum(1 for v in validation_results if v["validation_status"] == "matched"),
                "error_count": sum(1 for v in validation_results if v["validation_status"] not in ["matched", "pending"])
            }
        }
        
    except Exception as e:
        print(f"[v2] Error fetching incident validations for case {case_id}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/api/v2/banks/ecbt-transactions/{case_id}", tags=["Bank Ingest v2"])
async def get_ecbt_transactions(case_id: int) -> Dict[str, Any]:
    """
    Get ALL transactions from txn table for ECBT cases.
    This fetches actual bank transactions between the customer and the fraudulent beneficiary.
    """
    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # First, get the case details to find ecb_cust_acct_num and ecb_bene_acct_num
        # These are stored in the case_main table's source_ack_no and we need to look them up
        cur.execute("""
            SELECT source_ack_no, acc_num
            FROM public.case_main
            WHERE case_id = %s
        """, (case_id,))
        
        case_main_data = cur.fetchone()
        if not case_main_data:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        source_ack_no = case_main_data['source_ack_no']
        acc_num = case_main_data['acc_num']
        
        # For ECBT cases, we need to find the beneficiary account
        # Extract base ack_no and get the original incident data
        if source_ack_no and '_ECBT' in source_ack_no:
            base_ack_no = source_ack_no.replace('_ECBT', '')
            
            # Get the case_main_v2 and incidents to find the beneficiary account
            cur.execute("""
                SELECT ci.rrn
                FROM public.case_main_v2 cm2
                JOIN public.case_incidents ci ON cm2.case_id = ci.case_id
                WHERE cm2.acknowledgement_no = %s
                LIMIT 1
            """, (base_ack_no,))
            
            incident_row = cur.fetchone()
            if not incident_row:
                # No banks_v2 data, return empty
                return {
                    "success": True,
                    "data": {
                        "case_id": case_id,
                        "transactions": [],
                        "total_value_at_risk": 0
                    }
                }
            
            rrn = incident_row['rrn']
            
            # Get the beneficiary account from txn table using the RRN
            cur.execute("""
                SELECT bene_acct_num
                FROM public.txn
                WHERE rrn = %s
                LIMIT 1
            """, (rrn,))
            
            txn_row = cur.fetchone()
            if not txn_row:
                # RRN not found in txn table
                return {
                    "success": True,
                    "data": {
                        "case_id": case_id,
                        "transactions": [],
                        "total_value_at_risk": 0
                    }
                }
            
            bene_acct_num = txn_row['bene_acct_num']
            
            # Find the customer account from acc_bene table (the account that has this beneficiary saved)
            # This is the correct account for ECBT cases, not case_main.acc_num
            cur.execute("""
                SELECT cust_acct_num
                FROM public.acc_bene
                WHERE bene_acct_num = %s
                LIMIT 1
            """, (bene_acct_num,))
            
            acc_bene_row = cur.fetchone()
            if not acc_bene_row:
                # Beneficiary not in acc_bene table - shouldn't happen for ECBT cases
                print(f"[v2] ECBT case {case_id} - beneficiary {bene_acct_num} not found in acc_bene table", flush=True)
                return {
                    "success": True,
                    "data": {
                        "case_id": case_id,
                        "transactions": [],
                        "total_value_at_risk": 0
                    }
                }
            
            cust_acct_num = acc_bene_row['cust_acct_num']
            
            # Now fetch ALL transactions between cust_acct_num (customer) and bene_acct_num (beneficiary)
            cur.execute("""
                SELECT 
                    id, txn_date, txn_time, acct_num, bene_acct_num, 
                    amount, channel, rrn, descr, txn_type, currency, 
                    fee, exch_rate, bene_name, pay_ref, auth_code, pay_method
                FROM public.txn
                WHERE acct_num = %s AND bene_acct_num = %s
                ORDER BY txn_date DESC, txn_time DESC
            """, (cust_acct_num, bene_acct_num))
            
            transactions = cur.fetchall()
            
            print(f"[v2] ECBT case {case_id} - Found {len(transactions)} transactions between {cust_acct_num} and {bene_acct_num}", flush=True)
            
            cur.close()
            conn.close()
            
            # Format transactions for frontend - include ALL fields
            transaction_details = []
            for txn in transactions:
                transaction_details.append({
                    "txn_id": txn['id'],
                    "txn_date": txn['txn_date'].strftime('%d-%m-%Y') if txn['txn_date'] else None,
                    "txn_time": str(txn['txn_time']) if txn['txn_time'] else None,
                    "acct_num": txn['acct_num'],
                    "bene_acct_num": txn['bene_acct_num'],
                    "amount": str(txn['amount']),
                    "channel": txn['channel'] or "N/A",
                    "txn_ref": txn['rrn'],
                    "descr": txn['descr'] or "N/A",
                    "txn_type": txn['txn_type'] or "N/A",
                    "currency": txn['currency'] or "N/A",
                    "fee": str(txn['fee']) if txn['fee'] else "N/A",
                    "exch_rate": str(txn['exch_rate']) if txn['exch_rate'] else "N/A",
                    "bene_name": txn['bene_name'] or "N/A",
                    "pay_ref": txn['pay_ref'] or "N/A",
                    "auth_code": txn['auth_code'] or "N/A",
                    "pay_method": txn['pay_method'] or "N/A"
                })
            
            return {
                "success": True,
                "data": {
                    "case_id": case_id,
                    "customer_account": cust_acct_num,
                    "beneficiary_account": bene_acct_num,
                    "transactions": transaction_details,
                    "total_value_at_risk": sum(float(txn['amount']) for txn in transaction_details)
                }
            }
        else:
            # Not an ECBT case
            return {
                "success": False,
                "error": "This endpoint is only for ECBT cases"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[v2] Error fetching ECBT transactions for case {case_id}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


