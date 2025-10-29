"""
Audit Logger Service for Banks v2 API
Stores failed/invalid requests for audit purposes
"""

import psycopg2
import psycopg2.extras
from typing import Dict, Any, Optional
from config import DB_CONNECTION_PARAMS


def store_failed_request(
    ack_no: str,
    raw_body: dict,
    failure_reason: str,
    failure_type: str,
    error_details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Store failed request in audit table
    
    Args:
        ack_no: Acknowledgement number
        raw_body: Raw request body as dict
        failure_reason: Reason for failure
        failure_type: Type of failure (validation_error, vm_match_failed, etc.)
        error_details: Additional error details as dict
    """
    try:
        conn = psycopg2.connect(
            host=DB_CONNECTION_PARAMS["host"],
            port=DB_CONNECTION_PARAMS["port"],
            dbname=DB_CONNECTION_PARAMS["database"],
            user=DB_CONNECTION_PARAMS["user"],
            password=DB_CONNECTION_PARAMS["password"]
        )
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO banks_v2_failed_requests 
            (acknowledgement_no, raw_request_body, failure_reason, failure_type, error_details)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            ack_no or "Unknown",
            psycopg2.extras.Json(raw_body),
            failure_reason,
            failure_type,
            psycopg2.extras.Json(error_details) if error_details else None
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[AUDIT] Stored failed request: ack={ack_no}, type={failure_type}, reason={failure_reason}", flush=True)
    except Exception as e:
        print(f"[AUDIT] Failed to store failed request: {e}", flush=True)
        # Don't fail the API response if audit storage fails


def extract_ack_from_request(body_bytes: bytes) -> tuple[str, dict]:
    """
    Extract acknowledgement number from request body
    
    Args:
        body_bytes: Raw request body bytes
        
    Returns:
        Tuple of (ack_no, raw_body)
    """
    ack_no = "Unknown"
    raw_body = {}
    
    try:
        if body_bytes:
            import json
            raw_body = json.loads(body_bytes.decode('utf-8'))
            ack_no = raw_body.get("acknowledgement_no", "Unknown")
            print(f"[AUDIT] Extracted ACK from body: {ack_no}", flush=True)
    except Exception as e:
        print(f"[AUDIT] Could not parse request body: {e}", flush=True)
    
    return ack_no, raw_body


def get_all_failed_requests() -> list:
    """Get all failed requests from audit table"""
    try:
        conn = psycopg2.connect(
            host=DB_CONNECTION_PARAMS["host"],
            port=DB_CONNECTION_PARAMS["port"],
            dbname=DB_CONNECTION_PARAMS["database"],
            user=DB_CONNECTION_PARAMS["user"],
            password=DB_CONNECTION_PARAMS["password"]
        )
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                id, acknowledgement_no, failure_type, failure_reason,
                error_details, created_at
            FROM banks_v2_failed_requests 
            ORDER BY created_at DESC
        """)
        
        records = cur.fetchall()
        cur.close()
        conn.close()
        
        return records
    except Exception as e:
        print(f"[AUDIT] Failed to get failed requests: {e}", flush=True)
        return []


def get_failed_requests_by_ack(ack_no: str) -> list:
    """Get failed requests by acknowledgement number"""
    try:
        conn = psycopg2.connect(
            host=DB_CONNECTION_PARAMS["host"],
            port=DB_CONNECTION_PARAMS["port"],
            dbname=DB_CONNECTION_PARAMS["database"],
            user=DB_CONNECTION_PARAMS["user"],
            password=DB_CONNECTION_PARAMS["password"]
        )
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                id, acknowledgement_no, failure_type, failure_reason,
                error_details, raw_request_body, created_at
            FROM banks_v2_failed_requests 
            WHERE acknowledgement_no = %s
            ORDER BY created_at DESC
        """, (ack_no,))
        
        records = cur.fetchall()
        cur.close()
        conn.close()
        
        return records
    except Exception as e:
        print(f"[AUDIT] Failed to get failed requests by ACK: {e}", flush=True)
        return []


def mark_request_resolved(record_id: int, resolved_by: str, notes: str = None) -> bool:
    """Mark a failed request as resolved"""
    try:
        conn = psycopg2.connect(
            host=DB_CONNECTION_PARAMS["host"],
            port=DB_CONNECTION_PARAMS["port"],
            dbname=DB_CONNECTION_PARAMS["database"],
            user=DB_CONNECTION_PARAMS["user"],
            password=DB_CONNECTION_PARAMS["password"]
        )
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE banks_v2_failed_requests
            SET resolved = true,
                resolved_at = NOW(),
                resolved_by = %s,
                notes = %s
            WHERE id = %s
        """, (resolved_by, notes, record_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[AUDIT] Marked request {record_id} as resolved", flush=True)
        return True
    except Exception as e:
        print(f"[AUDIT] Failed to mark request as resolved: {e}", flush=True)
        return False

