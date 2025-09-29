# services/email_parser.py
import re
import base64
import io
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import httpx
from PIL import Image
import numpy as np
import fitz  # PyMuPDF
import easyocr  # EasyOCR

# Initialize EasyOCR reader once (CPU)
EASYOCR_READER = easyocr.Reader(['en'], gpu=False)

# ----------------------------
# Constants and enumerations
# ----------------------------

INDIA_STATES = set([
    'Andaman And Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar',
    'Chandigarh', 'Chhattisgarh', 'Delhi', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh',
    'Jammu And Kashmir', 'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep',
    'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha',
    'Puducherry', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
    'The Dadra And Nagar Haveli And Daman And Diu', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
])

PAYMENT_MODES = [
    'UPI', 'Net Banking / Internet Banking', 'Credit Card', 'Debit Card',
    'Digital Wallets / Mobile Wallets', 'Cheque', 'IMPS', 'NEFT', 'RTGS', 'AEPS', 'POS Terminals'
]

ACTIONS = ['Freeze Account', 'Reverse Transaction', 'Block/Restrict Account Access', 'Investigation', 'others']

SUBCATEGORIES = [
    'Online Scams', 'Phishing', 'Unauthorized Transactions', 'Credit/Debit Card Fraud',
    'UPI/Wallet Frauds', 'SIM Swap Fraud', 'Vishing (Voice Phishing)', 'Smishing (SMS Phishing)',
    'Fake Banking Websites/Apps', 'Online Payment Gateway Frauds', 'KYC Update Frauds',
    'Loan App Frauds', 'Others'
]

# ---------------------------------
# Regex library for field extraction
# ---------------------------------

RE_DATE = re.compile(r'\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b')
RE_DATETIME = re.compile(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}[ T]\d{1,2}:\d{2}(?::\d{2})?(?:\s?(?:AM|PM))?\b', re.I)

# ACK is strictly "ACK" followed by digits
RE_ACK = re.compile(r'\bACK\d+\b', re.I)

RE_TXN_ID = re.compile(r'\b(?:TXN|UTR|RRN|REF)[-_]?\d{5,20}\b', re.I)

RE_ACCOUNT = re.compile(r'\b(?:A/C|AC|Account|Acct|Beneficiary Account|Victim Account)\s*(?:No\.?|Number)?[:\-]?\s*(\d{9,18})\b', re.I)
RE_CARD = re.compile(r'\b(?:Card|PAN)\s*(?:No\.?|Number)?[:\-]?\s*(\d{12,19})\b', re.I)

RE_IFSC = re.compile(r'\b[A-Z]{4}0[A-Z0-9]{6}\b')
RE_UPI = re.compile(r'\b[a-z0-9._-]{3,30}@[a-z0-9._-]{2,20}\b', re.I)

RE_RUPEE_AMOUNT = re.compile(r'(?:₹|INR|Rs\.?)\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)', re.I)
RE_AMOUNT_LABELLED = {
    "transactionAmount": re.compile(r'(?:transaction\s+amount|amount\s+debited|amount)\s*[:\-]?\s*(?:₹|INR|Rs\.?)?\s*([0-9,]+(?:\.[0-9]{1,2})?)', re.I),
    "disputedAmount": re.compile(r'(?:disputed\s+amount|chargeback\s+amount)\s*[:\-]?\s*(?:₹|INR|Rs\.?)?\s*([0-9,]+(?:\.[0-9]{1,2})?)', re.I),
    "toAmount": re.compile(r'(?:beneficiary|credit(?:ed)?|to)\s*(?:transaction\s+)?amount\s*[:\-]?\s*(?:₹|INR|Rs\.?)?\s*([0-9,]+(?:\.[0-9]{1,2})?)', re.I),
}

RE_LAYER = re.compile(r'\bLayer\s+(\d{1,2})\b', re.I)

NEAR_LABEL = {
    "ackNo": re.compile(r'(acknowledg?ement|ack\s*no\.?)\s*[:\-]?\s*(ACK\d+)', re.I),
    "transactionId": re.compile(r'(?:txn|utr|rrn|ref)\s*(?:id|no\.?|number)?\s*[:\-]?\s*([A-Z0-9\-_]{5,})', re.I),
    "toTransactionId": re.compile(r'(?:beneficiary|credit(?:ed)?)\s*(?:txn|utr|rrn|ref)\s*(?:id|no\.?|number)?\s*[:\-]?\s*([A-Z0-9\-_]{5,})', re.I),
    "accountNumber": re.compile(r'(?:victim|from|debit(?:ed)?)\s*(?:a/c|account)\s*(?:no\.?|number)?\s*[:\-]?\s*(\d{9,18})', re.I),
    "toAccount": re.compile(r'(?:beneficiary|to|credit(?:ed)?)\s*(?:a/c|account)\s*(?:no\.?|number)?\s*[:\-]?\s*(\d{9,18})', re.I),
    "ifsc": re.compile(r'(?:ifsc|branch\s*code)\s*[:\-]?\s*([A-Z]{4}0[A-Z0-9]{6})', re.I),
    "toUpiId": re.compile(r'(?:upi|vpa|beneficiary\s*upi)\s*(?:id)?\s*[:\-]?\s*([a-z0-9._-]{3,30}@[a-z0-9._-]{2,20})', re.I),
    "toBank": re.compile(r'(?:beneficiary|to)\s*(?:bank|bank\s*name)\s*[:\-]?\s*([A-Za-z\s\.\'&-]{3,100})', re.I),
    "transactionDate": re.compile(r'(?:transaction|txn)\s*(?:date|dt)\s*[:\-]?\s*([0-9\/\-\: TAMPamp]+)', re.I),
    "complaintDate": re.compile(r'(?:complaint)\s*(?:date)\s*[:\-]?\s*([0-9\/\-\: TAMPamp]+)', re.I),
    "reportDateTime": re.compile(r'(?:report(?:ing)?|reported)\s*(?:date|time|date\s*&\s*time)\s*[:\-]?\s*([0-9\/\-\: TAMPamp]+)', re.I),
    "actionTakenDate": re.compile(r'(?:action\s*taken\s*date)\s*[:\-]?\s*([0-9\/\-\: TAMPamp]+)', re.I),
}

# NEW IDs: PAN, Aadhaar, Indian phone
RE_PAN = re.compile(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b')
RE_AADHAAR = re.compile(r'\b([2-9][0-9]{3}[\s-]?[0-9]{4}[\s-]?[0-9]{4})\b')
RE_PHONE_IN = re.compile(r'\b(?:\+?91[\s-]?|0)?([6-9]\d{9})\b')

# NEW: Indian Passport (one uppercase letter + seven digits, e.g., A1234567)
RE_PASSPORT = re.compile(r'\b([A-Z][0-9]{7})\b')

# NEW: Voter ID (EPIC: three uppercase letters + seven digits, e.g., ABC1234567)
RE_VOTER = re.compile(r'\b([A-Z]{3}[0-9]{7})\b')

# NEW: Driving License (flexible): AA00[- ]?YYYY[- ]?NNNNNNN or AA00YYYYNNNNNNN
RE_DL = re.compile(
    r'\b('
    r'[A-Z]{2}\d{2}[- ]?\d{4}[- ]?\d{7}'        # HR06-1985-0034761 or HR06 1985 0034761
    r'|[A-Z]{2}\d{2}\s?\d{11}'                  # HR06 19850034761
    r'|[A-Z]{2}\d{13}'                          # HR0619850034761
    r')\b'
)

# --------------------------------
# Base64url helper
# --------------------------------

def b64url_decode(s: str) -> bytes:
    s = s or ""
    pad = (-len(s)) % 4
    if pad:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)

# --------------------------------
# OCR helpers (EasyOCR + PyMuPDF)
# --------------------------------

def ocr_image_bytes_easy(image_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    arr = np.array(img)
    lines = EASYOCR_READER.readtext(arr, detail=0, paragraph=True)
    return "\n".join(lines)

def ocr_pdf_bytes_easy(pdf_bytes: bytes, dpi: int = 200) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    out: List[str] = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        png_bytes = pix.tobytes("png")
        out.append(ocr_image_bytes_easy(png_bytes))
    return "\n".join(out)

def ocr_bytes(data: bytes, mime: str, filename: str = "") -> str:
    mime_l = (mime or "").lower()
    name_l = (filename or "").lower()
    if "pdf" in mime_l or name_l.endswith(".pdf"):
        return ocr_pdf_bytes_easy(data)
    try:
        return ocr_image_bytes_easy(data)
    except Exception:
        return ""

# --------------------------------
# Gmail/Graph fetch helpers
# --------------------------------

async def gmail_get_message(client: httpx.AsyncClient, token: str, msg_id: str) -> Dict[str, Any]:
    r = await client.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
        params={"format": "full"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

async def gmail_get_attachment(client: httpx.AsyncClient, token: str, msg_id: str, attach_id: str) -> bytes:
    r = await client.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/attachments/{attach_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    js = r.json()
    return b64url_decode(js.get("data", ""))

async def gmail_extract_full_text_and_attachments(
    client: httpx.AsyncClient,
    token: str,
    payload: Dict[str, Any],
    msg_id: str
) -> Tuple[str, List[Dict[str, Any]]]:
    headers = {h.get("name","").lower(): h.get("value","") for h in (payload.get("headers") or [])}
    subject = headers.get("subject", "")
    attachments: List[Dict[str, Any]] = []
    body_texts: List[str] = []

    async def walk_async(part: Dict[str, Any]):
        mime = part.get("mimeType") or ""
        body = part.get("body") or {}
        filename = part.get("filename") or ""

        # Large text parts via attachmentId
        if body.get("attachmentId"):
            if filename:
                attachments.append({
                    "filename": filename,
                    "mimeType": mime or "application/octet-stream",
                    "attachmentId": body["attachmentId"],
                })
            if mime.startswith("text/") and not body.get("data"):
                data = await gmail_get_attachment(client, token, msg_id, body["attachmentId"])
                try:
                    body_texts.append(data.decode("utf-8", errors="ignore"))
                except Exception:
                    pass

        # Inline text bodies
        if mime.startswith("text/") and body.get("data"):
            try:
                body_texts.append(b64url_decode(body["data"]).decode("utf-8", errors="ignore"))
            except Exception:
                pass

        for p in part.get("parts") or []:
            await walk_async(p)

    if payload:
        await walk_async(payload)
    return subject + "\n" + "\n".join(body_texts), attachments

async def graph_get_message(client: httpx.AsyncClient, token: str, msg_id: str) -> Dict[str, Any]:
    r = await client.get(
        f"https://graph.microsoft.com/v1.0/me/messages/{msg_id}",
        params={"$select": "id,subject,bodyPreview,body,hasAttachments"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    r.raise_for_status()
    return r.json()

async def graph_list_attachments(client: httpx.AsyncClient, token: str, msg_id: str) -> List[Dict[str, Any]]:
    r = await client.get(
        f"https://graph.microsoft.com/v1.0/me/messages/{msg_id}/attachments",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    r.raise_for_status()
    return r.json().get("value", []) or []

def graph_attachment_to_bytes(att: Dict[str, Any]) -> Optional[Tuple[bytes, str, str]]:
    if att.get("@odata.type") == "#microsoft.graph.fileAttachment":
        content_b64 = att.get("contentBytes")
        if content_b64:
            data = base64.b64decode(content_b64)
            return data, att.get("name") or "attachment", att.get("contentType") or "application/octet-stream"
    return None

# -----------------------------
# Field normalization utilities
# -----------------------------

def _norm_amount(s: str) -> Optional[float]:
    if not s:
        return None
    n = s.replace(",", "").strip()
    try:
        return float(n)
    except Exception:
        return None

def _parse_date_any(s: str) -> Optional[str]:
    s = s.strip()
    try:
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d",
                    "%d-%m-%y", "%d/%m/%y", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M"]:
            try:
                dt = datetime.strptime(s, fmt)
                return dt.date().isoformat()
            except Exception:
                continue
        m = RE_DATE.search(s)
        if m:
            return _parse_date_any(m.group(0))
    except Exception:
        pass
    return None

def _parse_datetime_any(s: str) -> Optional[str]:
    s = s.strip()
    try:
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M",
                    "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"]:
            try:
                dt = datetime.strptime(s, fmt)
                return dt.strftime("%Y-%m-%dT%H:%M")
            except Exception:
                continue
        m = RE_DATETIME.search(s) or RE_DATE.search(s)
        if m:
            return _parse_datetime_any(m.group(0))
    except Exception:
        pass
    return None

def _pick_payment_mode(text: str) -> Optional[str]:
    t = text.lower()
    if "upi" in t or "vpa" in t:
        return "UPI"
    if "netbank" in t or "internet banking" in t or "net banking" in t:
        return "Net Banking / Internet Banking"
    if "credit card" in t:
        return "Credit Card"
    if "debit card" in t:
        return "Debit Card"
    if "wallet" in t:
        return "Digital Wallets / Mobile Wallets"
    if "imps" in t:
        return "IMPS"
    if "neft" in t:
        return "NEFT"
    if "rtgs" in t:
        return "RTGS"
    if "aeps" in t:
        return "AEPS"
    if "pos" in t:
        return "POS Terminals"
    if "cheque" in t or "check" in t:
        return "Cheque"
    return None

def _pick_subcategory(text: str) -> Optional[str]:
    t = text.lower()
    if "phishing" in t:
        return "Phishing"
    if "vishing" in t:
        return "Vishing (Voice Phishing)"
    if "smishing" in t or "sms phishing" in t:
        return "Smishing (SMS Phishing)"
    if "kyc" in t:
        return "KYC Update Frauds"
    if "loan app" in t:
        return "Loan App Frauds"
    if "upi" in t or "wallet" in t:
        return "UPI/Wallet Frauds"
    if "card" in t or "debit card" in t or "credit card" in t:
        return "Credit/Debit Card Fraud"
    if "unauthorized" in t or "unauthorised" in t:
        return "Unauthorized Transactions"
    if "gateway" in t or "payment link" in t:
        return "Online Payment Gateway Frauds"
    if "fake" in t and ("app" in t or "website" in t):
        return "Fake Banking Websites/Apps"
    if "sim swap" in t:
        return "SIM Swap Fraud"
    if "scam" in t:
        return "Online Scams"
    return None

def _pick_action(text: str) -> Optional[str]:
    t = text.lower()
    if "freeze" in t:
        return "Freeze Account"
    if "reverse" in t:
        return "Reverse Transaction"
    if "block" in t or "restrict" in t:
        return "Block/Restrict Account Access"
    if "investigation" in t or "investigate" in t:
        return "Investigation"
    return None

def _find_state(text: str) -> Optional[str]:
    for s in INDIA_STATES:
        if s.lower() in text.lower():
            return s
    return None

def _norm_aadhaar(s: str) -> str:
    return re.sub(r'[\s-]+', '', s).strip()

def _norm_pan(s: str) -> str:
    return s.strip().upper()

def _norm_phone_in(s: str) -> str:
    digits = re.sub(r'\D', '', s)
    if len(digits) >= 10:
        return digits[-10:]
    return digits

def _norm_upper_nospace(s: str) -> str:
    return re.sub(r'[\s-]+', '', s).upper().strip()

# ---------------------------------
# The form field extraction function
# ---------------------------------
def extract_form_fields(text: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {
        # Step 1
        "ackNo": None, "customerName": None, "subCategory": None, "complaintDate": None,
        "reportDateTime": None, "state": None, "district": None, "policestation": None,
        # Step 2
        "paymentMode": None, "transactionDate": None, "transactionId": None, "accountNumber": None,
        "cardNumber": None, "layers": None, "transactionAmount": None, "disputedAmount": None,
        # Step 3
        "toBank": None, "toAccount": None, "ifsc": None, "toTransactionId": None, "toAmount": None, "toUpiId": None,
        # Step 4
        "action": None, "actionTakenDate": None,
        # Extra
        "panCard": None, "aadhaarNumber": None, "phoneNumber": None,
        # NEW IDs
        "passportNumber": None, "voterIdNumber": None, "drivingLicenseNumber": None,
    }
    evidence: Dict[str, Dict[str, Any]] = {}

    def setf(k: str, v: Any, m: Optional[str], c: float):
        if v is not None and (fields.get(k) in (None, "", 0)):
            fields[k] = v
            evidence[k] = {"match": m or str(v), "confidence": round(c, 2)}

    # Basic pre-clean to reduce weird whitespace
    t = (text or "").replace('\u00A0', ' ').replace('\u200B', '')

    # ackNo
    m = NEAR_LABEL["ackNo"].search(t) or RE_ACK.search(t)
    if m:
        val = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(0)
        setf("ackNo", val.strip(), m.group(0), 0.95)

    # transaction ids
    m = NEAR_LABEL["transactionId"].search(t) or RE_TXN_ID.search(t)
    if m:
        val = m.group(1) if m.lastindex else m.group(0)
        setf("transactionId", val.strip(), m.group(0), 0.9)

    m = NEAR_LABEL["toTransactionId"].search(t)
    if m:
        setf("toTransactionId", m.group(1).strip(), m.group(0), 0.85)

    # account numbers
    m = NEAR_LABEL["accountNumber"].search(t) or RE_ACCOUNT.search(t)
    if m:
        # Prefer labeled capture group; else raw match
        grp = m.group(1) if m.lastindex else m.group(0)
        if RE_ACCOUNT.fullmatch(grp) or RE_ACCOUNT.fullmatch(m.group(0)):
            setf("accountNumber", grp.strip(), m.group(0), 0.9)

    m = NEAR_LABEL["toAccount"].search(t)
    if m:
        acct = m.group(1).strip()
        if RE_ACCOUNT.fullmatch(acct):
            setf("toAccount", acct, m.group(0), 0.9)

    # card number
    m = RE_CARD.search(t)
    if m:
        setf("cardNumber", re.sub(r'\D', '', m.group(0)).strip(), m.group(0), 0.75)

    # IFSC and UPI
    m = NEAR_LABEL["ifsc"].search(t) or RE_IFSC.search(t)
    if m:
        code = m.group(1) if m.lastindex else m.group(0)
        setf("ifsc", code.strip().upper(), m.group(0), 0.95)

    m = NEAR_LABEL["toUpiId"].search(t) or RE_UPI.search(t)
    if m:
        vpa = m.group(1) if m.lastindex else m.group(0)
        # Heuristic: drop if domain looks like an email domain with dot
        if '@' in vpa and '.' not in vpa.split('@', 1)[1]:
            setf("toUpiId", vpa.strip(), m.group(0), 0.9)

    # amounts
    for k, rx in RE_AMOUNT_LABELLED.items():
        m = rx.search(t)
        if m:
            amt = _norm_amount(m.group(1))
            if amt is not None:
                setf(k, amt, m.group(0), 0.9)

    if fields["transactionAmount"] is None:
        m = RE_RUPEE_AMOUNT.search(t)
        if m:
            amt = _norm_amount(m.group(1))
            setf("transactionAmount", amt, m.group(0), 0.6)

    # dates
    for key, rx in [("transactionDate", NEAR_LABEL["transactionDate"]),
                    ("complaintDate", NEAR_LABEL["complaintDate"]),
                    ("actionTakenDate", NEAR_LABEL["actionTakenDate"])]:
        m = rx.search(t)
        if m:
            iso = _parse_date_any(m.group(1))
            if iso:
                setf(key, iso, m.group(0), 0.85)

    m = NEAR_LABEL["reportDateTime"].search(t)
    if m:
        dt = _parse_datetime_any(m.group(1))
        if dt:
            setf("reportDateTime", dt, m.group(0), 0.85)

    # layers
    m = RE_LAYER.search(t)
    if m:
        setf("layers", f"Layer {m.group(1)}", m.group(0), 0.8)

    # toBank
    m = NEAR_LABEL["toBank"].search(t)
    if m:
        bank = m.group(1).strip()
        setf("toBank", bank, m.group(0), 0.8)

    # enums
    mode = _pick_payment_mode(t)
    if mode:
        setf("paymentMode", mode, mode, 0.8)

    subc = _pick_subcategory(t)
    if subc:
        setf("subCategory", subc, subc, 0.6)

    act = _pick_action(t)
    if act:
        setf("action", act, act, 0.6)

    # state and police station
    st = _find_state(t)
    if st:
        setf("state", st, st, 0.6)

    ps = None
    for lab in ["police station", "ps", "thana", "outpost", "chowki"]:
        m = re.search(rf'{lab}\s*[:\-]?\s*([A-Za-z\s\.\'\-]{{3,100}})', t, re.I)
        if m:
            ps = m.group(1).strip()
            break
    if ps:
        setf("policestation", ps, ps, 0.6)

    # customer name
    m = re.search(r'(?:customer\s*name)\s*[:\-]?\s*([A-Za-z\s\.\'\-]{2,100})', t, re.I)
    if not m:
        m = re.search(r'\bDear\s+([A-Za-z\s\.\'\-]{2,100})\b', t)
    if m:
        setf("customerName", m.group(1).strip(), m.group(0), 0.6)

    # PAN
    m = RE_PAN.search(t)
    if m:
        val = _norm_upper_nospace(m.group(0))
        setf("panCard", val, m.group(0), 0.95)

    # Aadhaar
    m = RE_AADHAAR.search(t)
    if m:
        raw = m.group(0)
        val = _norm_aadhaar(raw)
        if re.fullmatch(r'[2-9]\d{11}', val):
            setf("aadhaarNumber", val, m.group(0), 0.95)
        else:
            setf("aadhaarNumber", val, m.group(0), 0.6)

    # Indian phone
    m = RE_PHONE_IN.search(t)
    if m:
        local10 = _norm_phone_in(m.group(0))
        if re.fullmatch(r'[6-9]\d{9}', local10):
            setf("phoneNumber", local10, m.group(0), 0.9)

    # NEW: Passport
    m = RE_PASSPORT.search(t)
    if m:
        val = _norm_upper_nospace(m.group(0))
        setf("passportNumber", val, m.group(0), 0.95)

    # NEW: Voter ID (EPIC)
    m = RE_VOTER.search(t)
    if m:
        val = _norm_upper_nospace(m.group(0))
        setf("voterIdNumber", val, m.group(0), 0.95)

    # NEW: Driving License
    m = RE_DL.search(t)
    if m:
        val = _norm_upper_nospace(m.group(0))
        setf("drivingLicenseNumber", val, m.group(0), 0.9)

    # Drop this block into services/email_parser.py inside extract_form_fields(), AFTER the existing single-value setters.
    # It adds arrays (e.g., phoneNumbers) and preserves primary fields (e.g., phoneNumber).

        # -----------------------------
        # Collect ALL matches with context windows (arrays)
        # -----------------------------
        def _unique(seq):
            seen = set()
            out = []
            for x in seq:
                k = x if isinstance(x, str) else x.get("value")
                if k not in seen:
                    seen.add(k)
                    out.append(x)
            return out

        # Build line index to create small context windows
        lines = (t or "").splitlines()
        idx_offsets = []
        off = 0
        for ln in lines:
            idx_offsets.append((off, off + len(ln)))
            off += len(ln) + 1  # include newline

        def _context_for_span(span: tuple, radius: int = 2) -> Dict[str, Any]:
            start, end = span
            line_idx = 0
            for i, (a, b) in enumerate(idx_offsets):
                if a <= start <= b:
                    line_idx = i
                    break
            left = max(0, line_idx - radius)
            right = min(len(lines), line_idx + radius + 1)
            ctx = "\n".join(lines[left:right])
            ctx_low = ctx.lower()
            role = "beneficiary" if ("beneficiary" in ctx_low or "to a/c" in ctx_low or "to account" in ctx_low) else (
                "victim" if ("victim" in ctx_low or "from a/c" in ctx_low or "from account" in ctx_low) else None)
            return {"lineIndex": line_idx, "role": role, "text": ctx}

        # PAN candidates
        pan_candidates = []
        for m in RE_PAN.finditer(t):
            val = _norm_upper_nospace(m.group(0))
            pan_candidates.append({"value": val, "evidence": m.group(0), "context": _context_for_span(m.span())})
        pan_candidates = _unique(pan_candidates)

        # Aadhaar candidates
        aadhaar_candidates = []
        for m in RE_AADHAAR.finditer(t):
            raw = m.group(0)
            val = _norm_aadhaar(raw)
            if re.fullmatch(r'[2-9]\d{11}', val):
                aadhaar_candidates.append({"value": val, "evidence": m.group(0), "context": _context_for_span(m.span())})
        aadhaar_candidates = _unique(aadhaar_candidates)

        # Phone candidates
        phone_candidates = []
        for m in RE_PHONE_IN.finditer(t):
            local10 = _norm_phone_in(m.group(0))
            if re.fullmatch(r'[6-9]\d{9}', local10):
                phone_candidates.append({"value": local10, "evidence": m.group(0), "context": _context_for_span(m.span())})
        phone_candidates = _unique(phone_candidates)

        # Passport candidates
        passport_candidates = []
        for m in RE_PASSPORT.finditer(t):
            val = _norm_upper_nospace(m.group(0))
            passport_candidates.append({"value": val, "evidence": m.group(0), "context": _context_for_span(m.span())})
        passport_candidates = _unique(passport_candidates)

        # Voter ID candidates
        voter_candidates = []
        for m in RE_VOTER.finditer(t):
            val = _norm_upper_nospace(m.group(0))
            voter_candidates.append({"value": val, "evidence": m.group(0), "context": _context_for_span(m.span())})
        voter_candidates = _unique(voter_candidates)

        # DL candidates
        dl_candidates = []
        for m in RE_DL.finditer(t):
            val = _norm_upper_nospace(m.group(0))
            dl_candidates.append({"value": val, "evidence": m.group(0), "context": _context_for_span(m.span())})
        dl_candidates = _unique(dl_candidates)

        # Attach arrays to fields (backward compatible: keep single fields too)
        fields["panCards"] = [c["value"] for c in pan_candidates]
        fields["aadhaarNumbers"] = [c["value"] for c in aadhaar_candidates]
        fields["phoneNumbers"] = [c["value"] for c in phone_candidates]
        fields["passportNumbers"] = [c["value"] for c in passport_candidates]
        fields["voterIdNumbers"] = [c["value"] for c in voter_candidates]
        fields["drivingLicenseNumbers"] = [c["value"] for c in dl_candidates]

        # Prefer candidate by role if a primary field is still empty
        def _prefer_role(cands, want):
            for c in cands:
                if c["context"]["role"] == want:
                    return c["value"]
            return cands[0]["value"] if cands else None

        if not fields.get("panCard") and pan_candidates:
            fields["panCard"] = _prefer_role(pan_candidates, "beneficiary")
            evidence["panCard"] = {"match": pan_candidates[0]["evidence"], "confidence": 0.9}
        if not fields.get("aadhaarNumber") and aadhaar_candidates:
            fields["aadhaarNumber"] = _prefer_role(aadhaar_candidates, "beneficiary")
            evidence["aadhaarNumber"] = {"match": aadhaar_candidates[0]["evidence"], "confidence": 0.9}
        if not fields.get("phoneNumber") and phone_candidates:
            fields["phoneNumber"] = _prefer_role(phone_candidates, "beneficiary")
            evidence["phoneNumber"] = {"match": phone_candidates[0]["evidence"], "confidence": 0.9}
        if not fields.get("passportNumber") and passport_candidates:
            fields["passportNumber"] = _prefer_role(passport_candidates, "beneficiary")
            evidence["passportNumber"] = {"match": passport_candidates[0]["evidence"], "confidence": 0.9}
        if not fields.get("voterIdNumber") and voter_candidates:
            fields["voterIdNumber"] = _prefer_role(voter_candidates, "beneficiary")
            evidence["voterIdNumber"] = {"match": voter_candidates[0]["evidence"], "confidence": 0.9}
        if not fields.get("drivingLicenseNumber") and dl_candidates:
            fields["drivingLicenseNumber"] = _prefer_role(dl_candidates, "beneficiary")
            evidence["drivingLicenseNumber"] = {"match": dl_candidates[0]["evidence"], "confidence": 0.9}

        # Store candidate evidence for UI/debug
        evidence["panCard_candidates"] = pan_candidates
        evidence["aadhaar_candidates"] = aadhaar_candidates
        evidence["phone_candidates"] = phone_candidates
        evidence["passport_candidates"] = passport_candidates
        evidence["voter_candidates"] = voter_candidates
        evidence["dl_candidates"] = dl_candidates

    
    return {"fields": fields, "evidence": evidence}

# --------------------------------------
# EmailParser: combine body + OCR, then map
# --------------------------------------

class EmailParser:
    def __init__(self, on_result_cb=None):
        self.on_result_cb = on_result_cb

    async def process_gmail_message(self, token: str, msg_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            msg = await gmail_get_message(client, token, msg_id)
            payload = msg.get("payload") or {}
            body_text, attachments = await gmail_extract_full_text_and_attachments(client, token, payload, msg["id"])

            ocr_texts = []
            for att in attachments:
                data = await gmail_get_attachment(client, token, msg["id"], att["attachmentId"])
                ocr_texts.append(ocr_bytes(data, att.get("mimeType") or "application/octet-stream", att.get("filename") or ""))

            combined = "\n\n".join([body_text] + ocr_texts)
            extracted = extract_form_fields(combined)
            result = {
                "id": msg.get("id"),
                "provider": "google",
                "fields": extracted["fields"],
                "evidence": extracted["evidence"],
            }
            if self.on_result_cb:
                await self.on_result_cb("google", msg.get("id"), result)
            return result

    async def process_graph_message(self, token: str, msg_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            msg = await graph_get_message(client, token, msg_id)
            subject = msg.get("subject") or ""
            body_preview = msg.get("bodyPreview") or ""
            body_html = (msg.get("body") or {}).get("content") or ""
            base_text = "\n".join([subject, body_preview, body_html])

            ocr_texts = []
            if msg.get("hasAttachments"):
                atts = await graph_list_attachments(client, token, msg["id"])
                for att in atts:
                    parsed = graph_attachment_to_bytes(att)
                    if parsed:
                        data, name, mime = parsed
                        ocr_texts.append(ocr_bytes(data, mime, name))

            combined = "\n\n".join([base_text] + ocr_texts)
            extracted = extract_form_fields(combined)
            result = {
                "id": msg.get("id"),
                "provider": "microsoft",
                "fields": extracted["fields"],
                "evidence": extracted["evidence"],
            }
            if self.on_result_cb:
                await self.on_result_cb("microsoft", msg.get("id"), result)
            return result
