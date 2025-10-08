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


def _parse_date_ddmmyyyy(s: str) -> str:
    # input DD-MM-YYYY -> output YYYY-MM-DD
    dt = datetime.strptime(s, "%d-%m-%Y")
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

    # Phase 2: Persist envelope and incidents; produce per-incident validation results
    transactions: List[Dict[str, Any]] = []

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

        # Prepare to insert each incident
        has_txn_table = _txn_table_exists(cur)
        t_inc_total = 0.0
        # Defer case creation until after commit to avoid nested lock waits
        deferred_actions: List[Dict[str, Any]] = []
        rrn_to_txn_idx: Dict[str, int] = {}
        for inc in payload.incidents:
            rrn = inc.rrn
            try:
                t_inc_0 = time.perf_counter()
                # Idempotent insert; proceed even if rrn already present
                cur.execute(
                    """
                    INSERT INTO public.case_incidents (
                        case_id, amount, rrn, transaction_date, transaction_time, disputed_amount, layer
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (rrn) DO NOTHING
                    """,
                    (
                        case_id,
                        float(inc.amount),
                        rrn,
                        _parse_date_ddmmyyyy(inc.transaction_date),
                        _normalize_time(inc.transaction_time),
                        float(inc.disputed_amount),
                        int(inc.layer),
                    ),
                )

                # After persistence (or skip on duplicate), perform RRN validation/lookup for response mapping
                if not _rrn_is_numeric_and_length(rrn):
                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "status_code": "02",
                        "response_message": "Invalid RRN"
                    })
                    t_inc_total += time.perf_counter()-t_inc_0
                    continue

                if not _rrn_in_range(rrn):
                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "status_code": "03",
                        "response_message": "Invalid RRN range"
                    })
                    t_inc_total += time.perf_counter()-t_inc_0
                    continue

                if not has_txn_table:
                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "status_code": "31",
                        "response_message": "Pending"
                    })
                    t_inc_total += time.perf_counter()-t_inc_0
                    continue

                # Lookup in txn
                cur.execute(
                    "SELECT id, acct_num, bene_acct_num, amount, txn_date, txn_time FROM public.txn WHERE rrn = %s",
                    (rrn,)
                )
                rows = cur.fetchall()
                if len(rows) == 0:
                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "status_code": "01",
                        "response_message": "Record not found"
                    })
                    t_inc_total += time.perf_counter()-t_inc_0
                elif len(rows) > 1:
                    transactions.append({
                        "rrn_transaction_id": rrn,
                        "status_code": "15",
                        "response_message": "Multiple Records Found"
                    })
                    t_inc_total += time.perf_counter()-t_inc_0
                else:
                    _id, acct_num, bene_acct_num, amount, txn_date, txn_time = rows[0]

                    # VM: match payer_account_number to account_customer.acc_num
                    vm_match = False
                    cur.execute(
                        "SELECT cust_id FROM public.account_customer WHERE acc_num = %s LIMIT 1",
                        (payload.instrument.payer_account_number,)
                    )
                    row_v = cur.fetchone()
                    victim_cust_id = row_v[0] if row_v else None
                    if victim_cust_id:
                        vm_match = True

                    # Resolve beneficiary cust_id
                    cur.execute("SELECT cust_id FROM public.account_customer WHERE acc_num = %s LIMIT 1", (bene_acct_num,))
                    row_b = cur.fetchone()
                    bene_cust_id = row_b[0] if row_b else None

                    # Check ECBNT condition via acc_bene
                    cur.execute("SELECT 1 FROM public.acc_bene WHERE bene_acct_num = %s LIMIT 1", (bene_acct_num,))
                    has_bene_link = bool(cur.fetchone())

                    # Defer actions post-commit
                    action = {
                        "rrn": rrn,
                        "victim_cust_id": victim_cust_id,
                        "bene_cust_id": bene_cust_id,
                        "victim_acc": payload.instrument.payer_account_number,
                        "bene_acc": bene_acct_num,
                        "vm": vm_match,
                        "psa": bool(bene_cust_id),
                        "ecbt": bool(bene_acct_num),
                        "ecbnt": has_bene_link
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
                        "response_message": "SUCCESS",
                        "vm_match": vm_match
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

        conn.commit()
        print(f"[v2] Phase1 done (upsert+incidents+lookup) dt={(time.perf_counter()-t0)*1000:.1f}ms inc_total={t_inc_total*1000:.1f}ms", flush=True)
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

    # Phase 2: Create cases outside of transaction to avoid lock waits
    try:
        matcher = CaseEntryMatcher(executor=request.app.state.executor)
        for action in deferred_actions:
            rrn = action["rrn"]
            idx = rrn_to_txn_idx.get(rrn)
            if idx is None:
                continue
            txn_entry = transactions[idx]

            # PSA
            psa_case_id = None
            if action["psa"]:
                psa_case_id = await matcher.insert_into_case_main(
                    case_type="PSA",
                    source_ack_no=f"{ack_no}_PSA",
                    cust_id=action["bene_cust_id"],
                    acc_num=action["bene_acc"],
                    is_operational=True,
                    status='New',
                    decision_input='Pending Review',
                    remarks_input=f"Automated PSA case from bank ingest. RRN {rrn}",
                    source_bene_accno=action["bene_acc"],
                    customer_full_name=None
                )
                await save_or_update_decision(request.app.state.executor, psa_case_id, {"comments": "Initial PSA case created", "assignedEmployee": "System"})
                # case_details_1
                with _get_db_conn() as c2:
                    with c2.cursor() as k:
                        k.execute("INSERT INTO public.case_details_1 (cust_id, casetype, acc_no, match_flag, creation_timestamp) VALUES (%s, %s, %s, %s, NOW())", (action["bene_cust_id"], "PSA", action["bene_acc"], "PSA Match"))
                        c2.commit()

            # VM
            vm_case_id = None
            if action["vm"]:
                vm_case_id = await matcher.insert_into_case_main(
                    case_type="VM",
                    source_ack_no=f"{ack_no}_VM",
                    cust_id=action["victim_cust_id"],
                    acc_num=action["victim_acc"],
                    is_operational=True,
                    status='New',
                    decision_input='Pending Review',
                    remarks_input=f"Automated VM case from bank ingest. RRN {rrn}",
                    source_bene_accno=action["bene_acc"],
                    customer_full_name=None
                )
                await save_or_update_decision(request.app.state.executor, vm_case_id, {"comments": "Initial VM case created", "assignedEmployee": "System"})
                with _get_db_conn() as c2:
                    with c2.cursor() as k:
                        k.execute("INSERT INTO public.case_details_1 (cust_id, casetype, acc_no, match_flag, creation_timestamp) VALUES (%s, %s, %s, %s, NOW())", (action["victim_cust_id"], "VM", action["victim_acc"], "VM Match"))
                        c2.commit()

            # ECBT
            ecbt_case_id = None
            if action["ecbt"]:
                ecb_payload = ECBCaseData(
                    sourceAckNo=f"{ack_no}_ECBT",
                    customerId=action["bene_cust_id"],
                    beneficiaryAccountNumber=action["bene_acc"],
                    hasTransaction=True,
                    remarks=f"Automated ECBT case from bank ingest. RRN {rrn}",
                    location=None,
                    disputedAmount=None
                )
                ecbt_result = await matcher.create_ecb_case(ecb_payload, created_by_user="System")
                ecbt_case_id = (ecbt_result or {}).get("case_id")

            # ECBNT
            ecbnt_case_id = None
            if action["ecbnt"]:
                ecbn_payload = ECBCaseData(
                    sourceAckNo=f"{ack_no}_ECBNT",
                    customerId=action["bene_cust_id"],
                    beneficiaryAccountNumber=action["bene_acc"],
                    hasTransaction=False,
                    remarks=f"Automated ECBNT case from bank ingest. RRN {rrn}",
                    location=None,
                    disputedAmount=None
                )
                ecbnt_result = await matcher.create_ecb_case(ecbn_payload, created_by_user="System")
                ecbnt_case_id = (ecbnt_result or {}).get("case_id")

            # attach IDs back to response entry
            txn_entry["vm_case_id"] = vm_case_id
            txn_entry["psa_case_id"] = psa_case_id
            txn_entry["ecbt_case_id"] = ecbt_case_id
            txn_entry["ecbnt_case_id"] = ecbnt_case_id
    except Exception as e:
        print(f"[v2] Phase2 warning: {e}", flush=True)

    # Final combined response with ack and per-incident details
    print(f"[v2] END banks_case_entry ack={ack_no} job={job_id} total_dt={(time.perf_counter()-t0)*1000:.1f}ms", flush=True)
    return {
        "meta": {"response_code": "00", "response_message": "Success"},
        "data": {"acknowledgement_no": ack_no, "job_id": job_id},
        "transactions": transactions
    }


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


