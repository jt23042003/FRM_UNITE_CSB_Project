import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter, HTTPException
from db.connection import get_db_connection, get_db_cursor
from typing import List, Dict, Any

router = APIRouter()

@router.get("/api/match-suspect-customer", response_model=List[Dict[str, Any]])
def match_suspect_customer():
    """
    Matches records between suspect_entries and customer tables on pan, aadhar/nat_id, name, and mobile.
    Returns a list of matched pairs with all details from both tables.
    """
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                # Build SQL for matching on all 4 fields
                sql = '''
                SELECT s.*, c.*
                FROM suspect_entries s
                JOIN customer c
                  ON (
                    s.pan IS NOT NULL AND c.pan IS NOT NULL AND s.pan = c.pan
                  )
                  AND (
                    s.aadhar IS NOT NULL AND c.nat_id IS NOT NULL AND s.aadhar = c.nat_id
                  )
                  AND (
                    s.name IS NOT NULL AND (
                        TRIM(LOWER(s.name)) = TRIM(LOWER(
                            COALESCE(c.fname, '') || ' ' ||
                            COALESCE(c.mname, '') || ' ' ||
                            COALESCE(c.lname, '')
                        ))
                    )
                  )
                  AND (
                    s.mobile IS NOT NULL AND c.mobile IS NOT NULL AND s.mobile = c.mobile
                  )
                '''
                cur.execute(sql)
                results = cur.fetchall()
                # Return as list of dicts, each with suspect_ and customer_ prefixes
                matched = []
                for row in results:
                    suspect = {k: v for k, v in row.items() if k in [
                        'id', 'name', 'mobile', 'bank_account_number', 'pan', 'aadhar', 'gst_no', 'layer', 'upi_id', 'email_id', 'flagged_on', 'source', 'ifsc', 'source_flag']}
                    customer = {k: v for k, v in row.items() if k in [
                        'id', 'cust_id', 'fname', 'lname', 'mname', 'gender', 'phone', 'mobile', 'email', 'nat_id', 'pan', 'citizen', 'marital_stat', 'occupation', 'seg', 'risk_prof', 'kyc_status', 'cust_type', 'rm_id', 'pref_lang', 'country', 'dob', 'rel_value', 'cust_creation_date']}
                    matched.append({'suspect': suspect, 'customer': customer})
                return matched
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching suspect and customer records: {e}") 