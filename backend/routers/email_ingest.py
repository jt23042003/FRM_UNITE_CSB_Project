# routers/email_ingest.py
import os
import json
import base64
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Request, Query
from starlette.responses import PlainTextResponse

from services.email_parser import EmailParser
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

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
                # This endpoint intentionally returns processed=0 so the caller can re-issue a watch if desired
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
