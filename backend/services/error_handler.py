# services/error_handler.py
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException, status
from typing import Dict, Any, Optional, List
import asyncio # Needed for asyncio.get_running_loop()
from concurrent.futures import ThreadPoolExecutor # Needed for type hinting executor

# Assuming DB_CONNECTION_PARAMS is accessible. Will import from config.
from config import DB_CONNECTION_PARAMS 

def _sync_get_error_details_from_db(error_code_str: str) -> Optional[Dict[str, Any]]:
    """Synchronously fetches error details from error_master table."""
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONNECTION_PARAMS)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT errorcode, errordesc, errormessage FROM public.error_master WHERE errorcode = %s", (error_code_str,))
        error_details = cur.fetchone()
        return error_details
    except Exception as e:
        print(f"ERROR: Failed to fetch error details for code '{error_code_str}' from DB: {e}", flush=True)
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()

class ErrorHelper: # This is the class injected into routers
    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor

    async def get_error_response(self, error_code: str, http_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, detail_override: Optional[str] = None, validation_errors: Optional[List[Dict]] = None) -> HTTPException:
        """
        Fetches application-defined error details and raises a structured HTTPException.
        """
        error_details = await asyncio.get_running_loop().run_in_executor(self.executor, _sync_get_error_details_from_db, error_code)

        message = detail_override
        description = "An unexpected error occurred on the server."

        if error_details:
            message = error_details.get('errormessage', message or 'An unhandled application error occurred.')
            description = error_details.get('errordesc', description)
        else:
            # Fallback if error code not found in DB
            error_code = "UNKNOWN_ERROR" # Use a generic code if lookup failed
            message = detail_override or "An unknown error occurred on the server. Please contact support."

        detail_response = {
            "error_code": error_code,
            "description": description,
            "message": message
        }
        if validation_errors:
            detail_response["validation_errors"] = validation_errors

        print(f"API ERROR: Code {error_code}, Status {http_status_code}, Message: {message}", flush=True)
        raise HTTPException(status_code=http_status_code, detail=detail_response)
