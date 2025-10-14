# routers/email_ingest.py
import os
import json
import base64
import time
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Request, Query, Depends
from concurrent.futures import ThreadPoolExecutor
from starlette.responses import PlainTextResponse, JSONResponse

from services.email_parser import EmailParser
from db.matcher import CaseEntryMatcher
from models.base_models import CaseEntryData, ECBCaseData
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

# Health and reachability checks
@router.get("/email/health")
async def email_health():
    # Expand with checks to Google/Graph if desired
    return {"ok": True, "service": "email_ingest", "ts": datetime.now(timezone.utc).isoformat()}

@router.get("/webhooks/google")
async def gmail_webhook_get_probe():
    # Helpful for Pub/Sub endpoint validation during setup
    return PlainTextResponse("OK")

# In-memory state; replace with DB in production
STATE = {
    "google": {},
    "microsoft": {"_last_token": {"token": None}}
}

# Dev tokens from .env (no client id/secret needed)
DEV_GOOGLE_TOKEN = os.getenv("DEV_GOOGLE_ACCESS_TOKEN") or None
DEV_GOOGLE_EMAIL = os.getenv("DEV_GOOGLE_EMAIL") or None
DEV_MS_TOKEN = os.getenv("DEV_MS_ACCESS_TOKEN") or None

if DEV_GOOGLE_TOKEN and DEV_GOOGLE_EMAIL:
    STATE["google"][DEV_GOOGLE_EMAIL] = {"token": DEV_GOOGLE_TOKEN, "last_history_id": None}

if DEV_MS_TOKEN:
    STATE["microsoft"]["_last_token"]["token"] = DEV_MS_TOKEN

async def _on_result(provider: str, message_id: str, result: Dict[str, Any]):
    # Persist, enqueue, or broadcast as needed
    print(f"[EmailParsed] provider={provider} id={message_id} fields={list(result.get('fields', {}).keys())}")

PARSER = EmailParser(on_result_cb=_on_result)

def _require(d: Dict[str, Any], key: str) -> Any:
    v = d.get(key)
    if v is None:
        raise HTTPException(400, f"Missing field: {key}")
    return v

def _token_for_google(payload_token: Optional[str]) -> str:
    return payload_token or DEV_GOOGLE_TOKEN or STATE["google"].get(DEV_GOOGLE_EMAIL, {}).get("token") or ""

def _token_for_ms(payload_token: Optional[str]) -> str:
    return payload_token or DEV_MS_TOKEN or STATE["microsoft"]["_last_token"].get("token") or ""

def _b64url_decode(s: str) -> bytes:
    # Safer base64url decoding with correct padding handling
    pad = (-len(s)) % 4
    if pad:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)

# --------------------
# Gmail: register/watch (optional in dev)
# --------------------

@router.post("/email/google/register")
async def register_google_email(payload: Dict[str, Any] = Body(...)):
    email = _require(payload, "email")
    token = payload.get("access_token") or DEV_GOOGLE_TOKEN
    if not token:
        raise HTTPException(400, "Provide access_token or set DEV_GOOGLE_ACCESS_TOKEN in .env")
    STATE["google"][email] = {
        "token": token,
        "last_history_id": STATE["google"].get(email, {}).get("last_history_id")
    }
    return {"ok": True, "email": email}

@router.post("/email/google/watch")
async def google_watch(payload: Dict[str, Any] = Body(...)):
    email = payload.get("email") or DEV_GOOGLE_EMAIL
    if not email:
        raise HTTPException(400, "Provide email or set DEV_GOOGLE_EMAIL in .env")
    topic = _require(payload, "topic")  # "projects/<project>/topics/<topic>"
    labels = payload.get("labels") or ["INBOX"]
    entry = STATE["google"].get(email)
    if not entry or not entry.get("token"):
        token = DEV_GOOGLE_TOKEN
        if not token:
            raise HTTPException(400, "No token found. Register or set DEV_GOOGLE_ACCESS_TOKEN.")
        STATE["google"][email] = {"token": token, "last_history_id": None}
        entry = STATE["google"][email]
    token = entry["token"]
    body_json = {"topicName": topic, "labelIds": labels, "labelFilterBehavior": "INCLUDE"}
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/watch",
            headers={"Authorization": f"Bearer {token}"},
            json=body_json, timeout=30
        )
        r.raise_for_status()
        data = r.json()
    STATE["google"][email]["last_history_id"] = data.get("historyId")
    return {"ok": True, "email": email, "historyId": data.get("historyId"), "expiration": data.get("expiration")}

# Pub/Sub push: process history and RETURN JSON with extracted details
@router.post("/webhooks/google")
async def gmail_webhook(req: Request):
    envelope = await req.json()
    msg = envelope.get("message") or {}
    data_b64 = msg.get("data")
    if not data_b64:
        return {"ok": True, "processed": 0, "results": []}
    try:
        notif = json.loads(_b64url_decode(data_b64).decode("utf-8"))
    except Exception:
        traceback.print_exc()
        return {"ok": False, "error": "Invalid Pub/Sub message data"}
    email = notif.get("emailAddress") or DEV_GOOGLE_EMAIL
    hist_id = notif.get("historyId")
    if not email or not hist_id:
        return {"ok": True, "processed": 0, "results": []}

    entry = STATE["google"].get(email)
    if not entry:
        return {"ok": True, "processed": 0, "results": []}
    token = entry["token"]
    start = entry.get("last_history_id") or str(hist_id)

    results: List[Dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        page_token = None
        while True:
            params = {"startHistoryId": start}
            if page_token:
                params["pageToken"] = page_token
            r = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/history",
                headers={"Authorization": f"Bearer {token}"},
                params=params, timeout=30
            )
            if r.status_code == 404:
                # Old/invalid anchor; create a fresh users.watch to obtain a new start point per Gmail docs
                break
            r.raise_for_status()
            data = r.json()
            for h in data.get("history", []) or []:
                for added in h.get("messagesAdded", []) or []:
                    msg_id = added["message"]["id"]
                    try:
                        res = await PARSER.process_gmail_message(token, msg_id)
                        results.append(res)
                    except Exception:
                        traceback.print_exc()
            page_token = data.get("nextPageToken")
            if not page_token:
                break
    STATE["google"][email]["last_history_id"] = str(hist_id)
    # If you switch to background processing, return 202 and minimal JSON:
    # return JSONResponse({"ok": True}, status_code=202)
    return {"ok": True, "processed": len(results), "results": results}

# -------------------------
# Microsoft: subscribe/hook (optional in dev)
# -------------------------

@router.post("/email/microsoft/register")
async def register_ms(payload: Dict[str, Any] = Body(...)):
    access_token = payload.get("access_token") or DEV_MS_TOKEN
    if not access_token:
        raise HTTPException(400, "Provide access_token or set DEV_MS_ACCESS_TOKEN in .env")
    STATE["microsoft"]["_last_token"]["token"] = access_token
    return {"ok": True}

@router.post("/email/microsoft/subscribe")
async def ms_subscribe(payload: Dict[str, Any] = Body(...)):
    access_token = payload.get("access_token") or DEV_MS_TOKEN or STATE["microsoft"]["_last_token"].get("token")
    if not access_token:
        raise HTTPException(400, "Provide access_token or set DEV_MS_ACCESS_TOKEN in .env")
    notification_url = os.getenv("MS_WEBHOOK_URL") or _require(payload, "notificationUrl")
    minutes = int(payload.get("minutes") or 60)
    client_state = base64.urlsafe_b64encode(os.urandom(24)).decode("utf-8")

    body_json = {
        "changeType": "created",
        "notificationUrl": notification_url,
        "resource": "/me/mailFolders('inbox')/messages",
        "expirationDateTime": (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat(),
        "clientState": client_state
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://graph.microsoft.com/v1.0/subscriptions",
            headers={"Authorization": f"Bearer {access_token}"},
            json=body_json, timeout=30
        )
        r.raise_for_status()
        sub = r.json()
    sub_id = sub["id"]
    STATE["microsoft"][sub_id] = {
        "token": access_token,
        "clientState": client_state,
        "expires": sub.get("expirationDateTime")
    }
    return {"ok": True, "subscriptionId": sub_id, "expirationDateTime": sub.get("expirationDateTime")}

# Validation echo for Graph
@router.get("/webhooks/microsoft")
async def ms_validate(validationToken: Optional[str] = None):
    return PlainTextResponse(content=validationToken or "")

# Notifications POST: process immediately and RETURN JSON with details
@router.post("/webhooks/microsoft")
async def ms_notifications(payload: Dict[str, Any] = Body(...)):
    results: List[Dict[str, Any]] = []
    for n in (payload.get("value") or []):
        sub_id = n.get("subscriptionId")
        meta = STATE["microsoft"].get(sub_id)
        if not meta:
            continue
        if n.get("clientState") != meta.get("clientState"):
            continue
        if n.get("changeType") == "created":
            msg_id = (n.get("resourceData") or {}).get("id")
            if msg_id:
                try:
                    res = await PARSER.process_graph_message(meta["token"], msg_id)
                    results.append(res)
                except Exception:
                    traceback.print_exc()
    return {"ok": True, "processed": len(results), "results": results}

# ----------------------
# Dev helpers: list + preview using env tokens
# ----------------------

@router.get("/dev/google/messages")
async def dev_google_messages(q: str = Query("newer_than:7d"), max_results: int = Query(10, ge=1, le=100)):
    token = _token_for_google(None)
    if not token:
        raise HTTPException(400, "Set DEV_GOOGLE_ACCESS_TOKEN in .env or pass access_token")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            params={"q": q, "maxResults": max_results},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

@router.get("/dev/microsoft/messages")
async def dev_ms_messages(top: int = Query(10, ge=1, le=50)):
    token = _token_for_ms(None)
    if not token:
        raise HTTPException(400, "Set DEV_MS_ACCESS_TOKEN in .env or pass access_token")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://graph.microsoft.com/v1.0/me/messages",
            params={"$top": top, "$select": "id,subject,hasAttachments,receivedDateTime"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        r.raise_for_status()
        return r.json()

@router.post("/email/parse/preview")
async def preview_fields(payload: dict = Body(...)):
    provider = payload.get("provider")
    msg_id = payload.get("message_id")
    token = payload.get("access_token")
    if not provider or not msg_id:
        raise HTTPException(400, "provider and message_id are required")
    if provider == "google":
        token = _token_for_google(token)
        if not token:
            raise HTTPException(400, "No Google token available; set DEV_GOOGLE_ACCESS_TOKEN or pass access_token")
        result = await PARSER.process_gmail_message(token, msg_id)
    elif provider == "microsoft":
        token = _token_for_ms(token)
        if not token:
            raise HTTPException(400, "No Microsoft token available; set DEV_MS_ACCESS_TOKEN or pass access_token")
        result = await PARSER.process_graph_message(token, msg_id)
    else:
        raise HTTPException(400, "Unsupported provider")
    return {
        "id": result["id"],
        "provider": result["provider"],
        "fields": result["fields"],
        "evidence": result["evidence"],
    }

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    """Dependency to get ThreadPoolExecutor instance"""
    return request.app.state.executor

@router.get("/api/email/test")
async def test_email_endpoint():
    """Simple test endpoint to verify the router is working"""
    return {"status": "ok", "message": "Email router is working"}

@router.post("/api/email/test-parsing")
async def test_email_parsing(payload: dict = Body(...)):
    """Test email parsing without case creation"""
    try:
        provider = payload.get("provider")
        msg_id = payload.get("message_id")
        
        if not provider or not msg_id:
            raise HTTPException(400, "provider and message_id are required")
        
        # Just return success without actually parsing for now
        return {
            "status": "success",
            "provider": provider,
            "message_id": msg_id,
            "message": "Test parsing endpoint working"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/api/email/parse/create-cases")
async def parse_email_and_create_cases(
    payload: dict = Body(...),
    executor: ThreadPoolExecutor = Depends(get_executor_dependency)
):
    """
    Parse email content and automatically create fraud cases based on extracted data.
    This endpoint combines email parsing with automatic case creation workflow.
    """
    try:
        # Step 1: Parse the email (reuse existing logic)
        provider = payload.get("provider")
        msg_id = payload.get("message_id")
        token = payload.get("access_token")
        
        if not provider or not msg_id:
            raise HTTPException(400, "provider and message_id are required")
        
        if provider == "google":
            token = _token_for_google(token)
            if not token:
                raise HTTPException(400, "No Google token available; set DEV_GOOGLE_ACCESS_TOKEN or pass access_token")
            parsed_result = await PARSER.process_gmail_message(token, msg_id)
        elif provider == "microsoft":
            token = _token_for_ms(token)
            if not token:
                raise HTTPException(400, "No Microsoft token available; set DEV_MS_ACCESS_TOKEN or pass access_token")
            parsed_result = await PARSER.process_graph_message(token, msg_id)
        else:
            raise HTTPException(400, "Unsupported provider")
        
        # Step 2: Create cases based on parsed data
        case_matcher = CaseEntryMatcher(executor)
        case_creation_results = await _create_cases_from_parsed_data(case_matcher, parsed_result["fields"])
        
        return {
            "id": parsed_result["id"],
            "provider": parsed_result["provider"],
            "parsed_fields": parsed_result["fields"],
            "evidence": parsed_result["evidence"],
            "case_creation_results": case_creation_results
        }
    except Exception as e:
        print(f"❌ Error in parse_email_and_create_cases: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Internal server error: {str(e)}")

async def _create_cases_from_parsed_data(matcher: CaseEntryMatcher, fields: dict) -> dict:
    """
    Create fraud cases based on parsed email data.
    Logic: Assuming beneficiary account received, create BM case and check for ECBT/ECBNT.
    """
    results = {
        "bm_case": None,
        "ecb_cases": [],
        "errors": [],
        "summary": ""
    }
    
    try:
        # Extract key fields from parsed data
        bene_account = fields.get("toAccount")  # This is the beneficiary account from email
        victim_account = fields.get("accountNumber")  # This is the victim account from email
        ack_no = fields.get("ackNo", f"EMAIL_{int(time.time())}")
        
        # As per user requirement: "for now let's assume the account numbers he gets is a bene"
        # So we focus on the beneficiary account (toAccount) for case creation
        
        if not bene_account:
            results["errors"].append("No beneficiary account (toAccount) found in parsed email data")
            return results
        
        # Step 1: Check if beneficiary account exists in our customer database (BM case)
        bm_customer = await _find_customer_by_account(matcher, bene_account)
        
        if bm_customer:
            # Create BM case for the beneficiary account
            bm_case_data = _create_case_entry_data_from_fields(fields, bm_customer["cust_id"], "BM")
            bm_result = await matcher.match_data(bm_case_data, created_by_user="EmailSystem")
            results["bm_case"] = {
                "account_number": bene_account,
                "customer_id": bm_customer["cust_id"],
                "case_result": bm_result
            }
            
            # Step 2: Check for ECBT/ECBNT cases
            # Find all other customers who have added this beneficiary account
            ecb_results = await _create_ecb_cases_for_beneficiary(matcher, bene_account, ack_no, fields)
            results["ecb_cases"] = ecb_results
            
            results["summary"] = f"Created BM case for beneficiary account {bene_account}. Found {len(ecb_results)} ECB cases."
        else:
            results["summary"] = f"No customer match found for beneficiary account {bene_account}. No cases created."
            
    except Exception as e:
        results["errors"].append(f"Error creating cases: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return results

async def _find_customer_by_account(matcher: CaseEntryMatcher, account_number: str) -> Optional[dict]:
    """Find customer by account number"""
    from db.connection import get_db_connection, get_db_cursor
    
    def _sync_find_customer():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute("SELECT cust_id FROM account_customer WHERE acc_num = %s", (account_number,))
                return cur.fetchone()
    
    try:
        result = await matcher._execute_sync_db_op(_sync_find_customer)
        return result
    except Exception as e:
        print(f"Error finding customer by account {account_number}: {e}")
        return None

def _create_case_entry_data_from_fields(fields: dict, customer_id: str, case_type: str) -> CaseEntryData:
    """Convert parsed email fields to CaseEntryData for case creation"""
    import time
    from datetime import datetime, date
    
    # Handle date fields - convert to proper date objects
    def parse_date(date_str):
        if not date_str:
            return date.today()
        if isinstance(date_str, str):
            try:
                # Try different date formats
                for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except ValueError:
                        continue
            except:
                pass
        return date.today()
    
    # Handle reportDateTime - this is required for UPI payment mode
    report_datetime = fields.get("reportDateTime")
    if not report_datetime:
        # If not found, create one from complaint date + time or use current datetime
        complaint_date = fields.get("complaintDate")
        if complaint_date:
            report_datetime = f"{complaint_date} 10:00"  # Add default time
        else:
            report_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Ensure required numeric fields have default values
    transaction_amount = fields.get("transactionAmount") or 0.0
    disputed_amount = fields.get("disputedAmount") or transaction_amount
    to_amount = fields.get("toAmount") or transaction_amount
    
    return CaseEntryData(
        ackNo=fields.get("ackNo", f"EMAIL_{int(time.time())}"),
        customerName=fields.get("customerName", "Unknown Customer"),
        subCategory=fields.get("subCategory", "Others"),
        complaintDate=parse_date(fields.get("complaintDate")),
        reportDateTime=report_datetime,
        state=fields.get("state", "Unknown"),
        district=fields.get("district") or fields.get("state", "Unknown"),  # Use state as fallback for district
        policestation=fields.get("policestation", "Unknown"),
        paymentMode=fields.get("paymentMode", "UPI"),
        transactionDate=parse_date(fields.get("transactionDate")),
        transactionId=fields.get("transactionId", f"TXN{int(time.time())}"),
        accountNumber=fields.get("accountNumber"),  # Victim account
        cardNumber=fields.get("cardNumber"),
        layers=fields.get("layers", "Layer 1"),
        transactionAmount=float(transaction_amount),
        disputedAmount=float(disputed_amount),
        toBank=fields.get("toBank", "Unknown Bank"),
        toAccount=fields.get("toAccount"),  # Beneficiary account  
        ifsc=fields.get("ifsc"),
        toTransactionId=fields.get("toTransactionId"),
        toAmount=float(to_amount),
        toUpiId=fields.get("toUpiId"),
        action=fields.get("action"),
        actionTakenDate=parse_date(fields.get("actionTakenDate")),
        # Note: PAN, Aadhaar etc. are not part of CaseEntryData - they're handled separately
    )

async def _create_ecb_cases_for_beneficiary(matcher: CaseEntryMatcher, bene_account: str, ack_no: str, fields: dict) -> List[dict]:
    """
    Create ECBT/ECBNT cases by finding all customers who have added this beneficiary account
    and checking if they have transactions with this beneficiary
    """
    from db.connection import get_db_connection, get_db_cursor
    
    def _sync_find_customers_with_beneficiary():
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                # Find all customers who have added this account as a beneficiary
                cur.execute("""
                    SELECT DISTINCT ac.cust_id, ac.acc_num as customer_account, ab.bene_acct_num
                    FROM account_customer ac
                    JOIN acc_bene ab ON ac.acc_num = ab.cust_acct_num  
                    WHERE ab.bene_acct_num = %s
                """, (bene_account,))
                return cur.fetchall()
    
    try:
        customers_with_bene = await matcher._execute_sync_db_op(_sync_find_customers_with_beneficiary)
        ecb_results = []
        
        for customer in customers_with_bene:
            cust_id = customer["cust_id"]
            customer_account = customer["customer_account"]
            
            # Check if this customer has transactions with this beneficiary
            has_transactions = await matcher._check_customer_beneficiary_transactions(customer_account, bene_account)
            
            # Create ECBT or ECBNT case
            case_type = "ECBT" if has_transactions else "ECBNT"
            ecb_case_ack = f"{case_type}_{ack_no}_{cust_id}_{int(time.time())}"
            
            ecb_data = ECBCaseData(
                sourceAckNo=ecb_case_ack,
                customerId=cust_id,
                customerAccountNumber=customer_account,  # FIX: Add customer account number
                beneficiaryAccountNumber=bene_account,
                beneficiaryMobile=fields.get("phoneNumber"),
                beneficiaryEmail=fields.get("toUpiId"),  # Assuming UPI contains email-like format
                beneficiaryPAN=fields.get("panCard"),
                beneficiaryAadhar=fields.get("aadhaarNumber"), 
                hasTransaction=has_transactions,
                remarks=f"ECB case created from email parsing. Customer {cust_id} (Account: {customer_account}) has {'transactions' if has_transactions else 'no transactions'} with beneficiary {bene_account}",
                location=fields.get("state"),
                disputedAmount=fields.get("disputedAmount")
            )
            
            ecb_result = await matcher.create_ecb_case(ecb_data, created_by_user="EmailSystem")
            
            ecb_results.append({
                "customer_id": cust_id,
                "customer_account": customer_account,
                "beneficiary_account": bene_account,
                "case_type": case_type,
                "has_transactions": has_transactions,
                "case_result": ecb_result
            })
            
        return ecb_results
        
    except Exception as e:
        print(f"Error creating ECB cases for beneficiary {bene_account}: {e}")
        import traceback
        traceback.print_exc()
        return []
