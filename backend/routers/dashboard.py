# routers/dashboard.py
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any, Annotated
from fastapi import APIRouter, HTTPException, Query, Depends, Request
import traceback

from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
#from keycloak import KeycloakOpenID
from keycloak.keycloak_openid import KeycloakOpenID

from db.matcher import CaseEntryMatcher # Make sure this is imported
from config import (
    DELAY_THRESHOLD_DAYS, 
    RISK_OFFICER_DELAY_THRESHOLD_DAYS
    # Removed hardcoded department-specific thresholds for scalability
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_keycloak_openid_dependency(request: Request) -> KeycloakOpenID:
    return request.app.state.keycloak_openid

async def get_current_username(
    token: Annotated[str, Depends(oauth2_scheme)],
    keycloak_openid_instance: Annotated[KeycloakOpenID, Depends(get_keycloak_openid_dependency)]
) -> str:
    try:
        decoded_token = keycloak_openid_instance.decode_token(token)
        username: str = decoded_token.get("preferred_username") or decoded_token.get("sub")
          
        if username is None:
            print("ERROR: Token decoded but username (preferred_username/sub) not found in claims.", flush=True)
            raise HTTPException(status_code=401, detail="Could not validate credentials: Username missing in token.")
        
        return username
    except JWTError as e:
        print(f"ERROR: JWT Decoding/Validation failed: {e}", flush=True)
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: Invalid token ({e}).")
    except Exception as e:
        print(f"UNEXPECTED ERROR in get_current_username: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

def get_case_matcher_instance(request: Request) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=request.app.state.executor)

@router.get("/api/case-list")
async def get_case_list(
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    logged_in_username: Annotated[str, Depends(get_current_username)],
    skip: int = Query(0),
    limit: int = Query(25)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetches a paginated list of cases for the dashboard display, filtered by logged-in user's role and assignment.
    """
    # The user_type is fetched internally by fetch_dashboard_cases,
    # so we don't need to pass it as a separate parameter here.
    user_type = None # This line and its calculation can be kept for local debugging if needed, but won't be passed.
    if logged_in_username:
        user_type = await matcher.fetch_user_type(logged_in_username)
        if user_type is None:
            print(f"WARNING: User '{logged_in_username}' not found in user_table. No role-based filtering applied.", flush=True)

    try:
        cases_data = await matcher.fetch_dashboard_cases(
            skip=skip,
            limit=limit,
            search_ack_no=None, # This is a placeholder for actual search/status filters from frontend
            status_filter=None, # Pass search/status filters if frontend sends them
            current_logged_in_username=logged_in_username # This is the only user-related parameter needed here
            # REMOVED: current_logged_in_user_type=user_type - This parameter is not expected by fetch_dashboard_cases
        )

        if not cases_data:
            print("INFO: No cases found in the database for the dashboard.")
            return {"cases": []}
        
        return {"cases": cases_data}

    except HTTPException:
        raise
    except Exception as e:
        print(f"UNEXPECTED ERROR in /api/case-list: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve case list due to an internal server error.")


#@router.get("/api/all-cases")
#async def list_cases(
#    status: Annotated[Optional[str], Query()] = None,
#    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
#) -> Dict[str, List[Dict[str, Any]]]:
#    """
#    Fetches all cases, optionally filtered by status.
#    """
#    try:
#        cases = await matcher.fetch_all_cases_filtered(status=status)
#        return {"cases": cases}
#    except psycopg2.Error as db_error:
#        print(f"DATABASE ERROR in /api/all-cases: {db_error}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Database error while retrieving all cases.")
#    except Exception as e:
#        print(f"UNEXPECTED ERROR in /api/all-cases: {e}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Failed to retrieve all cases due to an internal server error.")


#@router.get("/api/dashboard-cases")
#async def get_dashboard_cases(
#    user_id: Annotated[str, Query(...)],
#    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
#) -> Dict[str, List[Dict[str, Any]]]:
#    """
#    Fetches dashboard-specific cases for a user.
#    """
#    try:
#        cases = await matcher.fetch_user_dashboard_cases(user_id=user_id)
#        return {"cases": cases}
#    except psycopg2.Error as db_error:
#        print(f"DATABASE ERROR in /api/dashboard-cases: {db_error}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Database error while retrieving dashboard cases.")
#    except Exception as e:
#        print(f"UNEXPECTED ERROR in /api/dashboard-cases: {e}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard cases due to an internal server error.")


#@router.get("/api/dropdown/status-list")
#async def get_status_list(
#    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
#) -> Dict[str, List[str]]:
#    """
#    Fetches a list of distinct statuses for dropdowns.
#    """
#    try:
#        statuses = await matcher.fetch_distinct_statuses()
#        return {"statuses": statuses}
#    except psycopg2.Error as db_error:
#        print(f"DATABASE ERROR in /api/dropdown/status-list: {db_error}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Database error while retrieving status list.")
#    except Exception as e:
#        print(f"UNEXPECTED ERROR in /api/dropdown/status-list: {e}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Failed to retrieve status list due to an internal server error.")


#@router.get("/api/dropdown/assigned-to-list")
#async def get_assigned_users(
#    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
#) -> Dict[str, List[str]]:
#    """
#    Fetches a list of distinct assigned users for dropdowns.
#    """
#    try:
#        users = await matcher.fetch_distinct_assigned_users()
#        return {"users": users}
#    except psycopg2.Error as db_error:
#        print(f"DATABASE ERROR in /api/dropdown/assigned-to-list: {db_error}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Database error while retrieving assigned users list.")
#    except Exception as e:
#        print(f"UNEXPECTED ERROR in /api/dropdown/assigned-to-list: {e}")
#        traceback.print_exc()
#        raise HTTPException(status_code=500, detail="Failed to retrieve assigned users list due to an internal server error.")


from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any, List, Optional, Annotated
from datetime import datetime, timedelta, date
import psycopg2
import traceback
from psycopg2.extras import RealDictCursor
from config import DB_CONNECTION_PARAMS
from keycloak.keycloak_openid import KeycloakOpenID
from concurrent.futures import ThreadPoolExecutor
from db.matcher import CaseEntryMatcher
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
import asyncio
import hashlib
import json

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Simple in-memory cache for dashboard queries
dashboard_cache = {}
cache_ttl = 300  # 5 minutes cache TTL

def get_cache_key(endpoint: str, params: Dict = None) -> str:
    """Generate cache key from endpoint and parameters"""
    cache_data = {"endpoint": endpoint}
    if params:
        cache_data.update(params)
    return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

def get_cached_data(cache_key: str) -> Optional[Dict]:
    """Get data from cache if not expired"""
    if cache_key in dashboard_cache:
        cached_item = dashboard_cache[cache_key]
        if datetime.now().timestamp() - cached_item["timestamp"] < cache_ttl:
            return cached_item["data"]
        else:
            # Remove expired cache
            del dashboard_cache[cache_key]
    return None

def set_cache_data(cache_key: str, data: Dict) -> None:
    """Set data in cache with timestamp"""
    dashboard_cache[cache_key] = {
        "data": data,
        "timestamp": datetime.now().timestamp()
    }

# --- Shared Dependencies (Same as other routers) ---
def get_keycloak_openid_dependency(request: Request) -> KeycloakOpenID:
    return request.app.state.keycloak_openid

async def get_current_username(
    token: Annotated[str, Depends(oauth2_scheme)],
    keycloak_openid_instance: Annotated[KeycloakOpenID, Depends(get_keycloak_openid_dependency)]
) -> str:
    try:
        decoded_token = keycloak_openid_instance.decode_token(token)
        username: str = decoded_token.get("preferred_username") or decoded_token.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials: Username missing in token.")
        return username
    except JWTError as e:
        print(f"ERROR: JWT Decoding/Validation failed: {e}", flush=True)
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: Invalid token ({e}).")
    except Exception as e:
        print(f"UNEXPECTED ERROR in get_current_username (dashboard): {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")

def get_executor_dependency(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor

def get_case_matcher_instance(executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]) -> CaseEntryMatcher:
    return CaseEntryMatcher(executor=executor)

@router.get("/api/dashboard/analytics")
async def get_dashboard_analytics(
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> Dict[str, Any]:
    """Get comprehensive dashboard analytics"""
    
    # Check cache first
    cache_key = get_cache_key("dashboard_analytics")
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                
                # Get total cases count and max case_id for verification
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        MAX(case_id) as max_case_id,
                        MIN(case_id) as min_case_id
                    FROM case_main
                """)
                case_stats = cur.fetchone()
                total_cases = case_stats['total']
                max_case_id = case_stats['max_case_id']
                min_case_id = case_stats['min_case_id']
                
                # Get cases by status (including NULL status)
                cur.execute("""
                    SELECT 
                        COALESCE(status, 'Unknown') as status, 
                        COUNT(*) as count 
                    FROM case_main 
                    GROUP BY status
                """)
                status_counts = {row['status']: row['count'] for row in cur.fetchall()}
                
                # Get cases by type
                cur.execute("""
                    SELECT case_type, COUNT(*) as count 
                    FROM case_main 
                    GROUP BY case_type
                """)
                type_counts = {row['case_type']: row['count'] for row in cur.fetchall()}
                
                # Get cases by operational status (including NULL)
                cur.execute("""
                    SELECT 
                        is_operational, 
                        COUNT(*) as count 
                    FROM case_main 
                    GROUP BY is_operational
                """)
                # PostgreSQL returns booleans as Python True/False/None
                operational_counts = {}
                for row in cur.fetchall():
                    key = str(row['is_operational']) if row['is_operational'] is not None else 'None'
                    operational_counts[key] = row['count']
                
                # Get recent activity (last 30 days)
                thirty_days_ago = datetime.now() - timedelta(days=30)
                cur.execute("""
                    SELECT 
                        DATE(creation_date) as date,
                        COUNT(*) as count
                    FROM case_main 
                    WHERE creation_date >= %s
                    GROUP BY DATE(creation_date)
                    ORDER BY date DESC
                """, (thirty_days_ago,))
                daily_activity = [{'date': row['date'].isoformat(), 'count': row['count']} for row in cur.fetchall()]
                
                # Calculate average resolution time
                cur.execute("""
                    SELECT 
                        AVG(EXTRACT(EPOCH FROM (closing_date - creation_date))/86400) as avg_resolution_days
                    FROM case_main 
                    WHERE status = 'Closed' AND closing_date IS NOT NULL
                """)
                avg_resolution_result = cur.fetchone()
                avg_resolution_days = float(avg_resolution_result['avg_resolution_days']) if avg_resolution_result['avg_resolution_days'] else 0
                
                # Aggregate Funds Saved from latest action per case
                try:
                    cur.execute(
                        """
                        WITH latest AS (
                            SELECT DISTINCT ON (case_id) case_id, action_data
                            FROM case_action_details
                            ORDER BY case_id, updated_at DESC
                        )
                        SELECT COALESCE(SUM((NULLIF(action_data->>'fundsSaved',''))::numeric), 0) AS total
                        FROM latest
                        WHERE (action_data->>'fundsSaved') IS NOT NULL AND (action_data->>'fundsSaved') <> ''
                        """
                    )
                    funds_saved_row = cur.fetchone()
                    funds_saved_total = float(funds_saved_row['total']) if funds_saved_row and funds_saved_row['total'] is not None else 0.0
                except Exception:
                    funds_saved_total = 0.0
                
                # Verify status counts sum matches total (for debugging)
                status_sum = sum(status_counts.values())
                
                result = {
                    "success": True,
                    "data": {
                        "overview": {
                            "total_cases": total_cases,
                            "max_case_id": max_case_id,  # For verification/debugging
                            "min_case_id": min_case_id,  # For verification/debugging
                            "new_cases": status_counts.get('New', 0),
                            "assigned_cases": status_counts.get('Assigned', 0),
                            "closed_cases": status_counts.get('Closed', 0),
                            "operational_cases": operational_counts.get('True', 0),
                            "non_operational_cases": operational_counts.get('False', 0),
                            "average_resolution_days": round(avg_resolution_days, 1),
                            "funds_saved_total": round(funds_saved_total, 2),
                            "_debug": {  # Internal debugging info (can be removed later)
                                "status_sum": status_sum,
                                "status_sum_matches_total": status_sum == total_cases
                            }
                        },
                        "case_types": type_counts,
                        "status_distribution": status_counts,
                        "operational_distribution": operational_counts,
                        "daily_activity": daily_activity,
                        "funds_saved": {
                            "aggregated": round(funds_saved_total, 2)
                        }
                    }
                }
                
                # Cache the result
                set_cache_data(cache_key, result)
                return result
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard analytics: {str(e)}")

@router.get("/api/dashboard/performance")
async def get_performance_metrics(
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> Dict[str, Any]:
    """Get performance metrics and KPIs"""
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                
                # Calculate average case resolution time using closing_date
                cur.execute("""
                    SELECT 
                        AVG(EXTRACT(EPOCH FROM (closing_date - creation_date))/86400) as avg_resolution_days
                    FROM case_main 
                    WHERE status = 'Closed' AND closing_date IS NOT NULL
                """)
                avg_resolution_result = cur.fetchone()
                avg_resolution_days = float(avg_resolution_result['avg_resolution_days']) if avg_resolution_result['avg_resolution_days'] else 0
                
                # Get cases closed this month
                first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM case_main 
                    WHERE status = 'Closed' AND creation_date >= %s
                """, (first_day_month,))
                monthly_closed = cur.fetchone()['count']
                
                # Get cases created this month
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM case_main 
                    WHERE creation_date >= %s
                """, (first_day_month,))
                monthly_created = cur.fetchone()['count']
                
                # Calculate closure rate
                closure_rate = (monthly_closed / monthly_created * 100) if monthly_created > 0 else 0
                
                # Get top performing users
                cur.execute("""
                    SELECT 
                        assigned_to,
                        COUNT(*) as cases_handled,
                        COUNT(CASE WHEN status = 'Closed' THEN 1 END) as cases_closed
                    FROM case_main 
                    WHERE assigned_to IS NOT NULL
                    GROUP BY assigned_to
                    ORDER BY cases_closed DESC
                    LIMIT 5
                """)
                top_performers = [
                    {
                        'user': row['assigned_to'],
                        'cases_handled': row['cases_handled'],
                        'cases_closed': row['cases_closed'],
                        'success_rate': (row['cases_closed'] / row['cases_handled'] * 100) if row['cases_handled'] > 0 else 0
                    }
                    for row in cur.fetchall()
                ]
                
                return {
                    "success": True,
                    "data": {
                        "avg_resolution_days": round(avg_resolution_days, 1),
                        "monthly_closed": monthly_closed,
                        "monthly_created": monthly_created,
                        "closure_rate": round(closure_rate, 1),
                        "top_performers": top_performers
                    }
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance metrics: {str(e)}")

@router.get("/api/dashboard/recent-activity")
async def get_recent_activity(
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)],
    limit: int = Query(10, description="Number of recent activities to return")
) -> Dict[str, Any]:
    """Get recent case activities"""
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                
                # Get recent cases with details
                cur.execute("""
                    SELECT 
                        case_id,
                        case_type,
                        status,
                        assigned_to,
                        creation_date,
                        disputed_amount,
                        location,
                        is_operational
                    FROM case_main 
                    ORDER BY creation_date DESC
                    LIMIT %s
                """, (limit,))
                
                recent_cases = []
                for row in cur.fetchall():
                    recent_cases.append({
                        'case_id': row['case_id'],
                        'case_type': row['case_type'],
                        'status': row['status'],
                        'assigned_to': row['assigned_to'],
                        'creation_date': row['creation_date'].isoformat() if row['creation_date'] else None,
                        'disputed_amount': float(row['disputed_amount']) if row['disputed_amount'] else None,
                        'location': row['location'],
                        'is_operational': row['is_operational']
                    })
                
                return {
                    "success": True,
                    "data": {
                        "recent_cases": recent_cases
                    }
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent activity: {str(e)}")


@router.get("/api/dashboard/user-analytics")
async def get_user_analytics(
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> Dict[str, Any]:
    """Get analytics scoped to the logged-in user (assigned_to = current user)."""
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Overview metrics for user
                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM case_main cm
                    INNER JOIN assignment a ON cm.case_id = a.case_id
                    WHERE a.assigned_to = %s
                    """,
                    (current_username,)
                )
                total_cases = cur.fetchone()["total"]

                cur.execute(
                    """
                    SELECT COUNT(*) AS open_count
                    FROM case_main cm
                    INNER JOIN assignment a ON cm.case_id = a.case_id
                    WHERE a.assigned_to = %s AND cm.status <> 'Closed'
                    """,
                    (current_username,)
                )
                open_cases = cur.fetchone()["open_count"]

                cur.execute(
                    """
                    SELECT COUNT(*) AS closed_count
                    FROM case_main cm
                    INNER JOIN assignment a ON cm.case_id = a.case_id
                    WHERE a.assigned_to = %s AND cm.status = 'Closed'
                    """,
                    (current_username,)
                )
                closed_cases = cur.fetchone()["closed_count"]

                # This month's created cases (assigned to user)
                cur.execute(
                    """
                    SELECT COUNT(*) AS monthly_created
                    FROM case_main cm
                    INNER JOIN assignment a ON cm.case_id = a.case_id
                    WHERE a.assigned_to = %s
                      AND DATE_TRUNC('month', cm.creation_date) = DATE_TRUNC('month', CURRENT_DATE)
                    """,
                    (current_username,)
                )
                monthly_created = cur.fetchone()["monthly_created"]

                # Status distribution for user
                cur.execute(
                    """
                    SELECT cm.status, COUNT(*) AS count
                    FROM case_main cm
                    INNER JOIN assignment a ON cm.case_id = a.case_id
                    WHERE a.assigned_to = %s
                    GROUP BY cm.status
                    """,
                    (current_username,)
                )
                status_distribution = {row["status"]: row["count"] for row in cur.fetchall()}

                # Daily activity (last 30 days) for user
                cur.execute(
                    """
                    SELECT DATE(cm.creation_date) AS date, COUNT(*) AS count
                    FROM case_main cm
                    INNER JOIN assignment a ON cm.case_id = a.case_id
                    WHERE a.assigned_to = %s
                      AND cm.creation_date >= (CURRENT_DATE - INTERVAL '30 days')
                    GROUP BY DATE(cm.creation_date)
                    ORDER BY DATE(cm.creation_date) DESC
                    """,
                    (current_username,)
                )
                daily_activity = [
                    {"date": row["date"].isoformat(), "count": row["count"]} for row in cur.fetchall()
                ]

                # Average resolution time for user's closed cases
                cur.execute(
                    """
                    SELECT AVG(EXTRACT(EPOCH FROM (cm.closing_date - cm.creation_date))/86400) AS avg_days
                    FROM case_main cm
                    INNER JOIN assignment a ON cm.case_id = a.case_id
                    WHERE a.assigned_to = %s AND cm.status = 'Closed' AND cm.closing_date IS NOT NULL
                    """,
                    (current_username,)
                )
                avg_days_row = cur.fetchone()
                avg_resolution_days = float(avg_days_row["avg_days"]) if avg_days_row and avg_days_row["avg_days"] else 0.0

                # Funds saved by latest action for cases assigned to user
                try:
                    cur.execute(
                        """
                        WITH latest AS (
                            SELECT DISTINCT ON (cad.case_id) cad.case_id, cad.action_data
                            FROM case_action_details cad
                            ORDER BY cad.case_id, cad.updated_at DESC
                        )
                        SELECT COALESCE(SUM((NULLIF(latest.action_data->>'fundsSaved',''))::numeric), 0) AS total
                        FROM latest
                        INNER JOIN case_main cm ON cm.case_id = latest.case_id
                        INNER JOIN assignment a ON a.case_id = cm.case_id AND a.assigned_to = %s
                        """,
                        (current_username,)
                    )
                    funds_saved_row = cur.fetchone()
                    funds_saved_total = float(funds_saved_row["total"]) if funds_saved_row and funds_saved_row["total"] is not None else 0.0
                except Exception:
                    funds_saved_total = 0.0

                # Recent cases for this user
                cur.execute(
                    """
                    SELECT 
                        cm.case_id,
                        cm.case_type,
                        cm.status,
                        cm.creation_date,
                        cm.short_dn,
                        cm.long_dn
                    FROM case_main cm
                    INNER JOIN assignment a ON cm.case_id = a.case_id
                    WHERE a.assigned_to = %s
                    ORDER BY cm.creation_date DESC
                    LIMIT 10
                    """,
                    (current_username,)
                )
                recent_cases = [
                    {
                        "case_id": row["case_id"],
                        "case_type": row["case_type"],
                        "status": row["status"],
                        "creation_date": row["creation_date"].isoformat() if row["creation_date"] else None,
                        "short_dn": row["short_dn"],
                        "long_dn": row["long_dn"],
                    }
                    for row in cur.fetchall()
                ]

                return {
                    "success": True,
                    "data": {
                        "overview": {
                            "total_cases": total_cases,
                            "open_cases": open_cases,
                            "closed_cases": closed_cases,
                            "monthly_created": monthly_created,
                            "average_resolution_days": round(avg_resolution_days, 1),
                            "funds_saved_total": round(funds_saved_total, 2),
                        },
                        "status_distribution": status_distribution,
                        "daily_activity": daily_activity,
                        "recent_cases": recent_cases,
                    },
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user analytics: {str(e)}")


@router.get("/api/user/activity-cases")
async def get_user_activity_cases(
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
) -> Dict[str, Any]:
    """Return cases the current user has touched and basic info for each.

    Definition of touched:
    - Any case with a log row where user_name = current user (assign, send_back, upload_document, close, etc.)
    - For users of type 'others': also include cases where logs contain details mentioning the current user on actions 'assign' or 'revoke_assignment'
    """
    try:
        # Determine user type
        try:
            user_type = await matcher.fetch_user_type(current_username)
        except Exception:
            user_type = None

        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # For super_user: show ALL cases, not just touched ones
                if user_type == 'super_user':
                    # Get all cases from case_main
                    cur.execute(
                        """
                        SELECT cm.case_id, cm.source_ack_no, cm.case_type, cm.status, 
                               cm.creation_date, cm.creation_time
                        FROM case_main cm
                        ORDER BY cm.creation_date DESC, cm.creation_time DESC
                        """
                    )
                    all_cases = cur.fetchall() or []
                    
                    # Build result for super_user
                    result = []
                    for case in all_cases:
                        result.append({
                            "case_id": case["case_id"],
                            "source_ack_no": case.get("source_ack_no"),
                            "case_type": case.get("case_type"),
                            "status": case.get("status"),
                            "last_touched_at": case.get("creation_date").isoformat() if case.get("creation_date") else None
                        })
                    
                    return {"cases": result, "user_type": user_type}
                
                # For other users: show only cases they've touched
                # 1) Cases where the user directly appears in logs
                cur.execute(
                    """
                    SELECT DISTINCT cl.case_id
                    FROM case_logs cl
                    WHERE cl.user_name = %s
                    """,
                    (current_username,)
                )
                direct_rows = cur.fetchall() or []
                case_ids = set([r["case_id"] for r in direct_rows])

                # 2) For 'others' users: include cases where they were assigned/revoked (detected via details)
                if user_type == 'others':
                    cur.execute(
                        """
                        SELECT DISTINCT cl.case_id
                        FROM case_logs cl
                        WHERE cl.action IN ('assign','revoke_assignment')
                          AND cl.details ILIKE %s
                        """,
                        (f"%{current_username}%",)
                    )
                    mention_rows = cur.fetchall() or []
                    case_ids.update([r["case_id"] for r in mention_rows])

                if not case_ids:
                    return {"cases": []}

                # Fetch basic case info and last touched timestamp by this user (or mention if others)
                case_ids_list = list(case_ids)
                cur.execute(
                    """
                    SELECT cm.case_id, cm.source_ack_no, cm.case_type, cm.status
                    FROM case_main cm
                    WHERE cm.case_id = ANY(%s)
                    """,
                    (case_ids_list,)
                )
                case_info_map = {row["case_id"]: row for row in (cur.fetchall() or [])}

                # Compute last touched timestamp for the user
                last_touch_map: Dict[int, Optional[datetime]] = {}
                # a) direct logs
                cur.execute(
                    """
                    SELECT cl.case_id, MAX(cl.created_at) AS last_ts
                    FROM case_logs cl
                    WHERE cl.user_name = %s AND cl.case_id = ANY(%s)
                    GROUP BY cl.case_id
                    """,
                    (current_username, case_ids_list)
                )
                for row in (cur.fetchall() or []):
                    last_touch_map[row["case_id"]] = row["last_ts"]

                # b) mentions (others only)
                if user_type == 'others':
                    cur.execute(
                        """
                        SELECT cl.case_id, MAX(cl.created_at) AS last_ts
                        FROM case_logs cl
                        WHERE cl.action IN ('assign','revoke_assignment')
                          AND cl.details ILIKE %s
                          AND cl.case_id = ANY(%s)
                        GROUP BY cl.case_id
                        """,
                        (f"%{current_username}%", case_ids_list)
                    )
                    for row in (cur.fetchall() or []):
                        cid = row["case_id"]
                        ts = row["last_ts"]
                        prev = last_touch_map.get(cid)
                        if prev is None or (ts and ts > prev):
                            last_touch_map[cid] = ts

                # Build response
                result = []
                for cid in case_ids_list:
                    info = case_info_map.get(cid)
                    if not info:
                        continue
                    result.append({
                        "case_id": cid,
                        "source_ack_no": info.get("source_ack_no"),
                        "case_type": info.get("case_type"),
                        "status": info.get("status"),
                        "last_touched_at": last_touch_map.get(cid).isoformat() if last_touch_map.get(cid) else None
                    })

                # Sort by last_touched_at desc, then case_id desc
                result.sort(key=lambda x: (x["last_touched_at"] or '', x["case_id"]), reverse=True)
                return {"cases": result, "user_type": user_type}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch user activity cases: {str(e)}")


@router.get("/api/supervisor/pending-approvals")
async def get_supervisor_pending_approvals(
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """Return cases that have pending_approval items OR are sent back to supervisor in the supervisor's department."""
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Determine supervisor's department
                cur.execute("SELECT dept, user_type FROM user_table WHERE user_name = %s", (current_username,))
                row = cur.fetchone()
                if not row or row.get('user_type') != 'supervisor':
                    return {"cases": []}
                dept = row.get('dept')

                # Cases with pending action approvals in this department
                cur.execute(
                    """
                    SELECT DISTINCT cad.case_id
                    FROM case_action_details cad
                    WHERE cad.status = 'pending_approval' AND cad.department = %s
                    """,
                    (dept,)
                )
                action_case_ids = {r['case_id'] for r in (cur.fetchall() or [])}

                # Cases with pending document approvals in this department
                cur.execute(
                    """
                    SELECT DISTINCT cd.case_id
                    FROM case_documents cd
                    WHERE cd.approval_status = 'pending_approval' AND cd.department = %s
                    """,
                    (dept,)
                )
                doc_case_ids = {r['case_id'] for r in (cur.fetchall() or [])}

                # Cases sent back to supervisor in this department (from case_logs)
                # BUT exclude cases that have been approved OR rejected (have 'approve_changes' or 'reject_changes' log after 'send_back_to_supervisor')
                cur.execute(
                    """
                    SELECT DISTINCT cl.case_id
                    FROM case_logs cl
                    WHERE cl.action = 'send_back_to_supervisor' 
                    AND cl.details LIKE %s
                    AND cl.case_id NOT IN (
                        SELECT DISTINCT cl2.case_id 
                        FROM case_logs cl2 
                        WHERE cl2.action IN ('approve_changes', 'reject_changes')
                        AND cl2.details LIKE %s
                        AND cl2.created_at > cl.created_at
                    )
                    """,
                    (f'%Dept: {dept}%', f'%Dept: {dept}%')
                )
                sent_back_case_ids = {r['case_id'] for r in (cur.fetchall() or [])}

                # Combine all case IDs
                case_ids = list(action_case_ids.union(doc_case_ids).union(sent_back_case_ids))
                if not case_ids:
                    return {"cases": []}

                # Fetch case summaries
                cur.execute(
                    """
                    SELECT cm.case_id, cm.source_ack_no, cm.case_type, cm.status, cm.creation_date
                    FROM case_main cm
                    WHERE cm.case_id = ANY(%s)
                    ORDER BY cm.creation_date DESC
                    """,
                    (case_ids,)
                )
                cases = cur.fetchall() or []
                return {"cases": cases, "department": dept}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending approvals: {str(e)}")

@router.get("/api/dashboard/advanced-analytics")
async def get_advanced_analytics(
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> Dict[str, Any]:
    """Get advanced analytics including department performance, workload distribution, and case aging"""
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                
                # Department Performance Analysis
                cur.execute("""
                    SELECT 
                        ut.dept,
                        COUNT(DISTINCT cm.case_id) as total_cases,
                        COUNT(CASE WHEN cm.status = 'Closed' THEN 1 END) as closed_cases,
                        COUNT(CASE WHEN cm.status = 'New' THEN 1 END) as new_cases,
                        COUNT(CASE WHEN cm.status = 'Assigned' THEN 1 END) as assigned_cases,
                        CAST(
                            COUNT(CASE WHEN cm.status = 'Closed' THEN 1 END)::numeric / 
                            NULLIF(COUNT(DISTINCT cm.case_id), 0) * 100 AS DECIMAL(10,2)
                        ) as closure_rate,
                        CAST(
                            AVG(CASE 
                                WHEN cm.status = 'Closed' AND cm.closing_date IS NOT NULL 
                                THEN EXTRACT(EPOCH FROM (cm.closing_date - cm.creation_date))/86400 
                            END) AS DECIMAL(10,1)
                        ) as avg_resolution_days
                    FROM case_main cm
                    LEFT JOIN assignment a ON cm.case_id = a.case_id
                    LEFT JOIN user_table ut ON a.assigned_to = ut.user_name
                    WHERE ut.dept IS NOT NULL
                    GROUP BY ut.dept
                    ORDER BY total_cases DESC
                """)
                department_performance = [dict(row) for row in cur.fetchall()]
                
                # User Workload Distribution
                cur.execute("""
                    SELECT 
                        a.assigned_to,
                        ut.dept,
                        COUNT(cm.case_id) as total_cases,
                        COUNT(CASE WHEN cm.status = 'Closed' THEN 1 END) as closed_cases,
                        COUNT(CASE WHEN cm.status IN ('New', 'Assigned') THEN 1 END) as active_cases,
                        CAST(
                            COUNT(CASE WHEN cm.status = 'Closed' THEN 1 END)::numeric / 
                            NULLIF(COUNT(cm.case_id), 0) * 100 AS DECIMAL(10,2)
                        ) as success_rate,
                        CAST(
                            AVG(CASE 
                                WHEN cm.status = 'Closed' AND cm.closing_date IS NOT NULL 
                                THEN EXTRACT(EPOCH FROM (cm.closing_date - cm.creation_date))/86400 
                            END) AS DECIMAL(10,1)
                        ) as avg_resolution_days
                    FROM assignment a
                    LEFT JOIN case_main cm ON a.case_id = cm.case_id
                    LEFT JOIN user_table ut ON a.assigned_to = ut.user_name
                    WHERE a.assigned_to IS NOT NULL
                    GROUP BY a.assigned_to, ut.dept
                    HAVING COUNT(cm.case_id) > 0
                    ORDER BY active_cases DESC, success_rate DESC
                """)
                workload_distribution = [dict(row) for row in cur.fetchall()]
                
                # Case Aging Analysis
                cur.execute("""
                    WITH age_buckets AS (
                        SELECT 
                            CASE 
                                WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 <= 1 THEN '0-1 days'
                                WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 <= 3 THEN '1-3 days'
                                WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 <= 7 THEN '3-7 days'
                                WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 <= 14 THEN '7-14 days'
                                WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 <= 30 THEN '14-30 days'
                                ELSE '30+ days'
                            END as age_bucket,
                            CASE 
                                WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 <= 1 THEN 1
                                WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 <= 3 THEN 2
                                WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 <= 7 THEN 3
                                WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 <= 14 THEN 4
                                WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 <= 30 THEN 5
                                ELSE 6
                            END as sort_order,
                            cm.status
                        FROM case_main cm
                        WHERE cm.status != 'Closed'
                    )
                    SELECT 
                        age_bucket,
                        COUNT(*) as case_count,
                        COUNT(CASE WHEN status = 'Closed' THEN 1 END) as closed_count,
                        CAST(
                            COUNT(CASE WHEN status = 'Closed' THEN 1 END)::numeric / 
                            NULLIF(COUNT(*), 0) * 100 AS DECIMAL(10,2)
                        ) as closure_rate
                    FROM age_buckets
                    GROUP BY age_bucket, sort_order
                    ORDER BY sort_order
                """)
                case_aging = [dict(row) for row in cur.fetchall()]
                
                # Case Type Performance Analysis
                cur.execute("""
                    SELECT 
                        cm.case_type,
                        COUNT(*) as total_cases,
                        COUNT(CASE WHEN cm.status = 'Closed' THEN 1 END) as closed_cases,
                        CAST(
                            COUNT(CASE WHEN cm.status = 'Closed' THEN 1 END)::numeric / 
                            NULLIF(COUNT(*), 0) * 100 AS DECIMAL(10,2)
                        ) as closure_rate,
                        CAST(
                            AVG(CASE 
                                WHEN cm.status = 'Closed' AND cm.closing_date IS NOT NULL 
                                THEN EXTRACT(EPOCH FROM (cm.closing_date - cm.creation_date))/86400 
                            END) AS DECIMAL(10,1)
                        ) as avg_resolution_days,
                        CAST(
                            AVG(CASE 
                                WHEN cm.disputed_amount IS NOT NULL 
                                THEN cm.disputed_amount 
                            END) AS DECIMAL(15,2)
                        ) as avg_disputed_amount
                    FROM case_main cm
                    GROUP BY cm.case_type
                    ORDER BY total_cases DESC
                """)
                case_type_performance = [dict(row) for row in cur.fetchall()]
                
                # Monthly Trends (last 12 months)
                cur.execute("""
                    SELECT 
                        DATE_TRUNC('month', cm.creation_date) as month,
                        COUNT(*) as cases_created,
                        COUNT(CASE WHEN cm.status = 'Closed' THEN 1 END) as cases_closed,
                        CAST(
                            COUNT(CASE WHEN cm.status = 'Closed' THEN 1 END)::numeric / 
                            NULLIF(COUNT(*), 0) * 100 AS DECIMAL(10,2)
                        ) as closure_rate
                    FROM case_main cm
                    WHERE cm.creation_date >= CURRENT_DATE - INTERVAL '12 months'
                    GROUP BY DATE_TRUNC('month', cm.creation_date)
                    ORDER BY month DESC
                """)
                monthly_trends = [dict(row) for row in cur.fetchall()]
                
                # Top Performing Users (last 30 days)
                cur.execute("""
                    SELECT 
                        a.assigned_to,
                        ut.dept,
                        COUNT(cm.case_id) as cases_handled,
                        COUNT(CASE WHEN cm.status = 'Closed' THEN 1 END) as cases_closed,
                        CAST(
                            COUNT(CASE WHEN cm.status = 'Closed' THEN 1 END)::numeric / 
                            NULLIF(COUNT(cm.case_id), 0) * 100 AS DECIMAL(10,2)
                        ) as success_rate,
                        CAST(
                            AVG(CASE 
                                WHEN cm.status = 'Closed' AND cm.closing_date IS NOT NULL 
                                THEN EXTRACT(EPOCH FROM (cm.closing_date - cm.creation_date))/86400 
                            END) AS DECIMAL(10,1)
                        ) as avg_resolution_days
                    FROM assignment a
                    LEFT JOIN case_main cm ON a.case_id = cm.case_id
                    LEFT JOIN user_table ut ON a.assigned_to = ut.user_name
                    WHERE a.assigned_to IS NOT NULL 
                    AND cm.creation_date >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY a.assigned_to, ut.dept
                    HAVING COUNT(cm.case_id) > 0
                    ORDER BY cases_closed DESC, success_rate DESC
                    LIMIT 10
                """)
                top_performers = [dict(row) for row in cur.fetchall()]
                
                return {
                    "success": True,
                    "data": {
                        "department_performance": department_performance,
                        "workload_distribution": workload_distribution,
                        "case_aging": case_aging,
                        "case_type_performance": case_type_performance,
                        "monthly_trends": monthly_trends,
                        "top_performers": top_performers
                    }
                }
                
    except Exception as e:
        print(f"ERROR: Failed to fetch advanced analytics: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch advanced analytics: {str(e)}")

@router.get("/api/dashboard/real-time-metrics")
async def get_real_time_metrics(
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> Dict[str, Any]:
    """Get real-time metrics for live dashboard updates"""
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                
                # Cases created in last 24 hours
                cur.execute("""
                    SELECT COUNT(*) as cases_last_24h
                    FROM case_main 
                    WHERE creation_date >= CURRENT_DATE - INTERVAL '24 hours'
                """)
                cases_last_24h = cur.fetchone()['cases_last_24h']
                
                # Cases closed in last 24 hours
                cur.execute("""
                    SELECT COUNT(*) as cases_closed_last_24h
                    FROM case_main 
                    WHERE closing_date >= CURRENT_DATE - INTERVAL '24 hours'
                """)
                cases_closed_last_24h = cur.fetchone()['cases_closed_last_24h']
                
                # Active cases (not closed)
                cur.execute("""
                    SELECT COUNT(*) as active_cases
                    FROM case_main 
                    WHERE status != 'Closed'
                """)
                active_cases = cur.fetchone()['active_cases']
                
                # Cases assigned in last hour
                cur.execute("""
                    SELECT COUNT(*) as cases_assigned_last_hour
                    FROM case_logs 
                    WHERE action = 'assign' 
                    AND created_at >= NOW() - INTERVAL '1 hour'
                """)
                cases_assigned_last_hour = cur.fetchone()['cases_assigned_last_hour']
                
                # Recent activity (last 10 actions)
                cur.execute("""
                    SELECT 
                        cl.action,
                        cl.user_name,
                        cl.created_at,
                        cm.case_id,
                        cm.case_type,
                        cm.status
                    FROM case_logs cl
                    LEFT JOIN case_main cm ON cl.case_id = cm.case_id
                    ORDER BY cl.created_at DESC
                    LIMIT 10
                """)
                recent_activity = [dict(row) for row in cur.fetchall()]
                
                # Current workload by user
                cur.execute("""
                    SELECT 
                        a.assigned_to,
                        COUNT(cm.case_id) as active_cases,
                        COUNT(CASE WHEN cm.status = 'New' THEN 1 END) as new_cases,
                        COUNT(CASE WHEN cm.status = 'Assigned' THEN 1 END) as assigned_cases
                    FROM assignment a
                    LEFT JOIN case_main cm ON a.case_id = cm.case_id
                    WHERE a.assigned_to IS NOT NULL 
                    AND cm.status != 'Closed'
                    GROUP BY a.assigned_to
                    ORDER BY active_cases DESC
                """)
                current_workload = [dict(row) for row in cur.fetchall()]
                
                return {
                    "success": True,
                    "data": {
                        "cases_last_24h": cases_last_24h,
                        "cases_closed_last_24h": cases_closed_last_24h,
                        "active_cases": active_cases,
                        "cases_assigned_last_hour": cases_assigned_last_hour,
                        "recent_activity": recent_activity,
                        "current_workload": current_workload,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
    except Exception as e:
        print(f"ERROR: Failed to fetch real-time metrics: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch real-time metrics: {str(e)}")

@router.get("/api/dashboard/predictive-analytics")
async def get_predictive_analytics(
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> Dict[str, Any]:
    """Get predictive analytics for case resolution forecasting"""
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                
                # Predict resolution time based on case type and age
                cur.execute("""
                    SELECT 
                        cm.case_type,
                        AVG(EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400) as avg_current_age_days,
                        CASE 
                            WHEN cm.case_type = 'VM' THEN 3
                            WHEN cm.case_type = 'BM' THEN 5
                            WHEN cm.case_type = 'PMA' THEN 7
                            WHEN cm.case_type = 'PSA' THEN 4
                            WHEN cm.case_type = 'NAB' THEN 6
                            WHEN cm.case_type = 'ECBT' THEN 8
                            WHEN cm.case_type = 'ECBNT' THEN 10
                            ELSE 5
                        END as predicted_resolution_days,
                        COUNT(*) as case_count
                    FROM case_main cm
                    WHERE cm.status != 'Closed'
                    GROUP BY cm.case_type
                    ORDER BY case_count DESC
                """)
                resolution_predictions = [dict(row) for row in cur.fetchall()]
                
                # Workload forecast for next 30 days
                cur.execute("""
                    SELECT 
                        DATE(cm.creation_date) as date,
                        COUNT(*) as cases_created,
                        AVG(COUNT(*)) OVER (ORDER BY DATE(cm.creation_date) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as moving_avg
                    FROM case_main cm
                    WHERE cm.creation_date >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(cm.creation_date)
                    ORDER BY date DESC
                    LIMIT 30
                """)
                workload_trend = [dict(row) for row in cur.fetchall()]
                
                # Predict cases at risk of SLA breach
                cur.execute("""
                    SELECT 
                        cm.case_id,
                        cm.case_type,
                        cm.creation_date,
                        EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 as age_days,
                        a.assigned_to,
                        CASE 
                            WHEN cm.case_type = 'VM' AND EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 > 2 THEN 'High'
                            WHEN cm.case_type = 'BM' AND EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 > 4 THEN 'High'
                            WHEN cm.case_type = 'PMA' AND EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 > 6 THEN 'High'
                            WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 > 5 THEN 'Medium'
                            ELSE 'Low'
                        END as risk_level
                    FROM case_main cm
                    LEFT JOIN assignment a ON cm.case_id = a.case_id
                    WHERE cm.status != 'Closed'
                    AND EXTRACT(EPOCH FROM (CURRENT_DATE - cm.creation_date))/86400 > 1
                    ORDER BY age_days DESC
                    LIMIT 20
                """)
                sla_risk_cases = [dict(row) for row in cur.fetchall()]
                
                # Department capacity analysis
                cur.execute("""
                    SELECT 
                        ut.dept,
                        COUNT(CASE WHEN cm.status != 'Closed' THEN 1 END) as active_cases,
                        COUNT(DISTINCT a.assigned_to) as active_users,
                        CAST(
                            COUNT(CASE WHEN cm.status != 'Closed' THEN 1 END)::numeric / 
                            NULLIF(COUNT(DISTINCT a.assigned_to), 0) AS DECIMAL(10,1)
                        ) as cases_per_user,
                        CASE 
                            WHEN COUNT(CASE WHEN cm.status != 'Closed' THEN 1 END)::numeric / NULLIF(COUNT(DISTINCT a.assigned_to), 0) > 10 THEN 'Overloaded'
                            WHEN COUNT(CASE WHEN cm.status != 'Closed' THEN 1 END)::numeric / NULLIF(COUNT(DISTINCT a.assigned_to), 0) > 5 THEN 'High Load'
                            WHEN COUNT(CASE WHEN cm.status != 'Closed' THEN 1 END)::numeric / NULLIF(COUNT(DISTINCT a.assigned_to), 0) > 2 THEN 'Normal'
                            ELSE 'Low Load'
                        END as capacity_status
                    FROM case_main cm
                    LEFT JOIN assignment a ON cm.case_id = a.case_id
                    LEFT JOIN user_table ut ON a.assigned_to = ut.user_name
                    WHERE ut.dept IS NOT NULL
                    GROUP BY ut.dept
                    ORDER BY cases_per_user DESC
                """)
                capacity_analysis = [dict(row) for row in cur.fetchall()]
                
                # Generate forecast for next 7 days based on historical data
                if workload_trend:
                    recent_avg = sum(float(row['moving_avg'] or 0) for row in workload_trend[:7]) / min(7, len(workload_trend))
                    forecast = []
                    for i in range(7):
                        forecast_date = datetime.now() + timedelta(days=i+1)
                        # Add some randomness based on day of week
                        weekday_multiplier = 1.2 if forecast_date.weekday() < 5 else 0.6  # Higher on weekdays
                        predicted_cases = int(recent_avg * weekday_multiplier)
                        forecast.append({
                            'date': forecast_date.date().isoformat(),
                            'predicted_cases': predicted_cases,
                            'confidence': 85 if i < 3 else 70  # Higher confidence for near-term
                        })
                else:
                    forecast = []
                
                return {
                    "success": True,
                    "data": {
                        "resolution_predictions": resolution_predictions,
                        "workload_trend": workload_trend,
                        "sla_risk_cases": sla_risk_cases,
                        "capacity_analysis": capacity_analysis,
                        "forecast": forecast,
                        "generated_at": datetime.now().isoformat()
                    }
                }
                
    except Exception as e:
        print(f"ERROR: Failed to fetch predictive analytics: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch predictive analytics: {str(e)}")

@router.get("/api/dashboard/network-data")
async def get_network_data(
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)]
) -> Dict[str, Any]:
    """Get network visualization data for entity relationships and fraud patterns"""
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                
                # Get cases with key entity information
                cur.execute("""
                    SELECT 
                        cm.case_id,
                        cm.case_type,
                        cm.status,
                        cm.disputed_amount,
                        cm.creation_date,
                        cm.acc_num,
                        cm.source_bene_accno,
                        cm.cust_id,
                        cm.short_dn,
                        cm.long_dn,
                        cm.location,
                        cm.source_ack_no,
                        a.assigned_to,
                        ut.dept
                    FROM case_main cm
                    LEFT JOIN assignment a ON cm.case_id = a.case_id
                    LEFT JOIN user_table ut ON a.assigned_to = ut.user_name
                    WHERE cm.creation_date >= CURRENT_DATE - INTERVAL '90 days'
                    ORDER BY cm.creation_date DESC
                    LIMIT 500
                """)
                cases = [dict(row) for row in cur.fetchall()]
                
                # Build nodes and edges for network visualization
                nodes = {}
                edges = []
                node_connections = {}
                
                # Process each case to extract entities and relationships
                for case in cases:
                    case_id = case['case_id']
                    case_node_id = f"case_{case_id}"
                    
                    # Add case node
                    nodes[case_node_id] = {
                        'id': case_node_id,
                        'type': 'case',
                        'label': f"Case {case_id}",
                        'case_type': case['case_type'],
                        'status': case['status'],
                        'amount': float(case['disputed_amount']) if case['disputed_amount'] else 0,
                        'creation_date': case['creation_date'].isoformat() if case['creation_date'] else None,
                        'location': case['location'],
                        'assigned_to': case['assigned_to'],
                        'dept': case['dept']
                    }
                    
                    # Process victim account (acc_num)
                    if case['acc_num']:
                        victim_account_id = f"account_{case['acc_num']}"
                        if victim_account_id not in nodes:
                            nodes[victim_account_id] = {
                                'id': victim_account_id,
                                'type': 'account',
                                'label': case['acc_num'],
                                'entity_type': 'victim_account',
                                'cases': []
                            }
                        nodes[victim_account_id]['cases'].append(case_id)
                        edges.append({
                            'source': case_node_id,
                            'target': victim_account_id,
                            'type': 'victim_account',
                            'strength': 1
                        })
                        
                        if victim_account_id not in node_connections:
                            node_connections[victim_account_id] = 0
                        node_connections[victim_account_id] += 1
                    
                    # Process beneficiary account (source_bene_accno)
                    if case['source_bene_accno']:
                        beneficiary_account_id = f"account_{case['source_bene_accno']}"
                        if beneficiary_account_id not in nodes:
                            nodes[beneficiary_account_id] = {
                                'id': beneficiary_account_id,
                                'type': 'account',
                                'label': case['source_bene_accno'],
                                'entity_type': 'beneficiary_account',
                                'cases': []
                            }
                        nodes[beneficiary_account_id]['cases'].append(case_id)
                        edges.append({
                            'source': case_node_id,
                            'target': beneficiary_account_id,
                            'type': 'beneficiary_account',
                            'strength': 1
                        })
                        
                        if beneficiary_account_id not in node_connections:
                            node_connections[beneficiary_account_id] = 0
                        node_connections[beneficiary_account_id] += 1
                    
                    # Process customer ID
                    if case['cust_id']:
                        customer_id = f"customer_{case['cust_id']}"
                        if customer_id not in nodes:
                            nodes[customer_id] = {
                                'id': customer_id,
                                'type': 'customer',
                                'label': case['cust_id'],
                                'entity_type': 'customer',
                                'cases': []
                            }
                        nodes[customer_id]['cases'].append(case_id)
                        edges.append({
                            'source': case_node_id,
                            'target': customer_id,
                            'type': 'customer',
                            'strength': 1
                        })
                        
                        if customer_id not in node_connections:
                            node_connections[customer_id] = 0
                        node_connections[customer_id] += 1
                    
                    # Process source acknowledgment number
                    if case['source_ack_no']:
                        ack_id = f"ack_{case['source_ack_no']}"
                        if ack_id not in nodes:
                            nodes[ack_id] = {
                                'id': ack_id,
                                'type': 'ack_no',
                                'label': case['source_ack_no'],
                                'entity_type': 'source_ack',
                                'cases': []
                            }
                        nodes[ack_id]['cases'].append(case_id)
                        edges.append({
                            'source': case_node_id,
                            'target': ack_id,
                            'type': 'source_ack',
                            'strength': 1
                        })
                        
                        if ack_id not in node_connections:
                            node_connections[ack_id] = 0
                        node_connections[ack_id] += 1
                
                # Add risk scores and connection counts to nodes
                for node_id, node in nodes.items():
                    connection_count = node_connections.get(node_id, 0)
                    node['connections'] = connection_count
                    
                    # Assign risk level based on connections
                    if connection_count >= 5:
                        node['risk_level'] = 'high'
                    elif connection_count >= 3:
                        node['risk_level'] = 'medium'
                    else:
                        node['risk_level'] = 'low'
                
                # Get fraud pattern statistics
                cur.execute("""
                    SELECT 
                        case_type,
                        COUNT(*) as count,
                        AVG(disputed_amount) as avg_amount,
                        COUNT(CASE WHEN status = 'Closed' THEN 1 END) as closed_count
                    FROM case_main
                    WHERE creation_date >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY case_type
                    ORDER BY count DESC
                """)
                fraud_patterns = [dict(row) for row in cur.fetchall()]
                
                # Get repeated entity statistics
                cur.execute("""
                    WITH entity_counts AS (
                        SELECT 
                            acc_num as entity,
                            'victim_account' as entity_type,
                            COUNT(*) as case_count
                        FROM case_main 
                        WHERE acc_num IS NOT NULL 
                        AND creation_date >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY acc_num
                        
                        UNION ALL
                        
                        SELECT 
                            source_bene_accno as entity,
                            'beneficiary_account' as entity_type,
                            COUNT(*) as case_count
                        FROM case_main 
                        WHERE source_bene_accno IS NOT NULL 
                        AND creation_date >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY source_bene_accno
                        
                        UNION ALL
                        
                        SELECT 
                            cust_id as entity,
                            'customer' as entity_type,
                            COUNT(*) as case_count
                        FROM case_main 
                        WHERE cust_id IS NOT NULL 
                        AND creation_date >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY cust_id
                        
                        UNION ALL
                        
                        SELECT 
                            location as entity,
                            'location' as entity_type,
                            COUNT(*) as case_count
                        FROM case_main 
                        WHERE location IS NOT NULL 
                        AND creation_date >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY location
                    )
                    SELECT entity, entity_type, case_count
                    FROM entity_counts
                    WHERE case_count > 1
                    ORDER BY case_count DESC
                    LIMIT 20
                """)
                repeated_entities = [dict(row) for row in cur.fetchall()]
                
                return {
                    "success": True,
                    "data": {
                        "nodes": list(nodes.values()),
                        "edges": edges,
                        "fraud_patterns": fraud_patterns,
                        "repeated_entities": repeated_entities,
                        "stats": {
                            "total_nodes": len(nodes),
                            "total_edges": len(edges),
                            "high_risk_nodes": len([n for n in nodes.values() if n.get('risk_level') == 'high']),
                            "medium_risk_nodes": len([n for n in nodes.values() if n.get('risk_level') == 'medium'])
                        },
                        "generated_at": datetime.now().isoformat()
                    }
                }
                
    except Exception as e:
        print(f"ERROR: Failed to fetch network data: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch network data: {str(e)}")

@router.get("/api/dashboard/fraud-patterns")
async def get_fraud_patterns(
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)],
    executor: Annotated[ThreadPoolExecutor, Depends(get_executor_dependency)],
    time_range: str = Query("24h", description="Time range: 24h, 7d, or 30d")
) -> Dict[str, Any]:
    """Get real fraud patterns from database analytics"""
    try:
        # Convert time range to days
        days_map = {"24h": 1, "7d": 7, "30d": 30}
        days = days_map.get(time_range, 1)
        
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                
                # Critical Alert 1: Account numbers appearing in multiple transactions with different beneficiaries
                cur.execute("""
                    WITH suspicious_accounts AS (
                        SELECT 
                            t.acct_num,
                            COUNT(DISTINCT t.bene_acct_num) as unique_beneficiaries,
                            COUNT(*) as total_transactions,
                            SUM(t.amount) as total_amount,
                            MIN(t.txn_date) as first_seen,
                            array_agg(DISTINCT c.mobile) as mobile_numbers
                        FROM txn t
                        LEFT JOIN account_customer ac ON t.acct_num = ac.acc_num
                        LEFT JOIN customer c ON ac.cust_id = c.cust_id
                        WHERE t.txn_date >= CURRENT_DATE - INTERVAL '%s days'
                        AND t.txn_type = 'Debit'
                        GROUP BY t.acct_num
                        HAVING COUNT(DISTINCT t.bene_acct_num) >= 5
                        ORDER BY unique_beneficiaries DESC, total_amount DESC
                        LIMIT 5
                    )
                    SELECT * FROM suspicious_accounts
                """, (days,))
                suspicious_accounts = [dict(row) for row in cur.fetchall()]
                
                # Critical Alert 2: Beneficiary accounts receiving from multiple different source accounts
                cur.execute("""
                    WITH suspicious_beneficiaries AS (
                        SELECT 
                            t.bene_acct_num,
                            t.bene_name,
                            COUNT(DISTINCT t.acct_num) as unique_sources,
                            COUNT(*) as total_transactions,
                            SUM(t.amount) as total_amount,
                            MIN(t.txn_date) as first_seen,
                            array_agg(DISTINCT t.acct_num) as source_accounts
                        FROM txn t
                        WHERE t.txn_date >= CURRENT_DATE - INTERVAL '%s days'
                        AND t.txn_type = 'Debit'
                        AND t.bene_acct_num IS NOT NULL
                        GROUP BY t.bene_acct_num, t.bene_name
                        HAVING COUNT(DISTINCT t.acct_num) >= 8
                        ORDER BY unique_sources DESC, total_amount DESC
                        LIMIT 5
                    )
                    SELECT * FROM suspicious_beneficiaries
                """, (days,))
                suspicious_beneficiaries = [dict(row) for row in cur.fetchall()]
                
                # Critical Alert 3: Mobile numbers associated with high-value rapid transactions
                cur.execute("""
                    WITH mobile_velocity AS (
                        SELECT 
                            c.mobile,
                            COUNT(*) as transaction_count,
                            SUM(t.amount) as total_amount,
                            AVG(t.amount) as avg_amount,
                            COUNT(DISTINCT t.bene_acct_num) as unique_beneficiaries,
                            MIN(t.txn_date) as first_seen,
                            MAX(t.txn_date) as last_seen
                        FROM txn t
                        JOIN account_customer ac ON t.acct_num = ac.acc_num
                        JOIN customer c ON ac.cust_id = c.cust_id
                        WHERE t.txn_date >= CURRENT_DATE - INTERVAL '%s days'
                        AND t.txn_type = 'Debit'
                        AND c.mobile IS NOT NULL
                        AND t.amount > 50000
                        GROUP BY c.mobile
                        HAVING COUNT(*) >= 10
                        ORDER BY transaction_count DESC, total_amount DESC
                        LIMIT 5
                    )
                    SELECT * FROM mobile_velocity
                """, (days,))
                mobile_patterns = [dict(row) for row in cur.fetchall()]
                
                # Geographic clustering - locations with unusual transaction patterns
                cur.execute("""
                    WITH location_analysis AS (
                        SELECT 
                            c.country,
                            COUNT(*) as transaction_count,
                            COUNT(DISTINCT t.acct_num) as unique_accounts,
                            COUNT(DISTINCT t.bene_acct_num) as unique_beneficiaries,
                            SUM(t.amount) as total_amount,
                            AVG(t.amount) as avg_amount
                        FROM txn t
                        JOIN account_customer ac ON t.acct_num = ac.acc_num
                        JOIN customer c ON ac.cust_id = c.cust_id
                        WHERE t.txn_date >= CURRENT_DATE - INTERVAL '%s days'
                        AND t.txn_type = 'Debit'
                        AND c.country IS NOT NULL
                        GROUP BY c.country
                        HAVING COUNT(*) >= 50
                        ORDER BY transaction_count DESC
                        LIMIT 10
                    )
                    SELECT * FROM location_analysis
                """, (days,))
                geographic_patterns = [dict(row) for row in cur.fetchall()]
                
                # Real-time stats
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT t.acct_num) as active_accounts,
                        COUNT(DISTINCT t.bene_acct_num) as unique_beneficiaries,
                        COUNT(*) as total_transactions,
                        SUM(t.amount) as total_amount,
                        COUNT(CASE WHEN t.amount > 100000 THEN 1 END) as high_value_txns
                    FROM txn t
                    WHERE t.txn_date >= CURRENT_DATE - INTERVAL '%s days'
                    AND t.txn_type = 'Debit'
                """, (days,))
                real_time_stats = dict(cur.fetchone())
                
                # Repeated case patterns from actual case data
                cur.execute("""
                    WITH pattern_analysis AS (
                        SELECT 
                            cm.acc_num as entity_value,
                            'victim_account' as entity_type,
                            'Account Reuse' as pattern_type,
                            COUNT(*) as case_count,
                            SUM(cm.disputed_amount) as total_amount,
                            MIN(cm.creation_date) as first_seen,
                            MAX(cm.creation_date) as last_seen,
                            array_agg(DISTINCT cm.location) as locations,
                            array_agg(DISTINCT cm.case_id) as case_ids
                        FROM case_main cm
                        WHERE cm.creation_date >= CURRENT_DATE - INTERVAL '%s days'
                        AND cm.acc_num IS NOT NULL
                        GROUP BY cm.acc_num
                        HAVING COUNT(*) > 1
                        
                        UNION ALL
                        
                        SELECT 
                            cm.source_bene_accno as entity_value,
                            'beneficiary_account' as entity_type,
                            'Beneficiary Clustering' as pattern_type,
                            COUNT(*) as case_count,
                            SUM(cm.disputed_amount) as total_amount,
                            MIN(cm.creation_date) as first_seen,
                            MAX(cm.creation_date) as last_seen,
                            array_agg(DISTINCT cm.location) as locations,
                            array_agg(DISTINCT cm.case_id) as case_ids
                        FROM case_main cm
                        WHERE cm.creation_date >= CURRENT_DATE - INTERVAL '%s days'
                        AND cm.source_bene_accno IS NOT NULL
                        GROUP BY cm.source_bene_accno
                        HAVING COUNT(*) > 1
                    )
                    SELECT * FROM pattern_analysis
                    ORDER BY case_count DESC, total_amount DESC
                    LIMIT 10
                """, (days, days))
                repeated_cases = [dict(row) for row in cur.fetchall()]
                
                # Build critical alerts from the analysis
                critical_alerts = []
                
                # Process suspicious accounts
                for acc in suspicious_accounts:
                    critical_alerts.append({
                        'id': f"acc_{acc['acct_num']}",
                        'title': f"Suspicious Account Activity",
                        'description': f"Account {acc['acct_num']} sent money to {acc['unique_beneficiaries']} different beneficiaries",
                        'case_count': acc['total_transactions'],
                        'total_amount': float(acc['total_amount']) if acc['total_amount'] else 0,
                        'first_seen': acc['first_seen'],
                        'risk_score': min(95, 70 + acc['unique_beneficiaries'] * 3),
                        'entity_type': 'account',
                        'entity_value': acc['acct_num']
                    })
                
                # Process suspicious beneficiaries
                for bene in suspicious_beneficiaries:
                    critical_alerts.append({
                        'id': f"bene_{bene['bene_acct_num']}",
                        'title': f"Beneficiary Account Clustering",
                        'description': f"Beneficiary {bene['bene_name']} received money from {bene['unique_sources']} different accounts",
                        'case_count': bene['total_transactions'],
                        'total_amount': float(bene['total_amount']) if bene['total_amount'] else 0,
                        'first_seen': bene['first_seen'],
                        'risk_score': min(98, 75 + bene['unique_sources'] * 2),
                        'entity_type': 'beneficiary_account',
                        'entity_value': bene['bene_acct_num']
                    })
                
                # Process mobile patterns
                for mobile in mobile_patterns:
                    critical_alerts.append({
                        'id': f"mobile_{mobile['mobile']}",
                        'title': f"High-Velocity Mobile Pattern",
                        'description': f"Mobile {mobile['mobile']} associated with {mobile['transaction_count']} high-value transactions",
                        'case_count': mobile['transaction_count'],
                        'total_amount': float(mobile['total_amount']) if mobile['total_amount'] else 0,
                        'first_seen': mobile['first_seen'],
                        'risk_score': min(92, 60 + mobile['transaction_count'] * 2),
                        'entity_type': 'mobile',
                        'entity_value': mobile['mobile']
                    })
                
                # Sort alerts by risk score
                critical_alerts.sort(key=lambda x: x['risk_score'], reverse=True)
                
                return {
                    "success": True,
                    "data": {
                        "critical_alerts": critical_alerts[:5],  # Top 5 alerts
                        "stats": {
                            "suspicious_entities": len(suspicious_accounts) + len(suspicious_beneficiaries),
                            "new_suspicious": len([a for a in critical_alerts if a['risk_score'] > 90]),
                            "repeated_patterns": len(repeated_cases),
                            "pattern_growth": 15,  # Could calculate actual growth
                            "fraud_networks": len(suspicious_beneficiaries),
                            "network_size": sum(b['unique_sources'] for b in suspicious_beneficiaries) // max(len(suspicious_beneficiaries), 1),
                            "high_velocity": real_time_stats['high_value_txns'],
                            "velocity_increase": 25
                        },
                        "repeated_cases": [
                            {
                                'pattern_id': f"p_{i}",
                                'pattern_type': case['pattern_type'],
                                'entity_type': case['entity_type'],
                                'entity_value': case['entity_value'],
                                'case_count': case['case_count'],
                                'time_span': f"{(case['last_seen'] - case['first_seen']).days} days" if case['last_seen'] and case['first_seen'] else "N/A",
                                'total_amount': float(case['total_amount']) if case['total_amount'] else 0,
                                'risk_level': 'high' if case['case_count'] >= 5 else 'medium' if case['case_count'] >= 3 else 'low',
                                'locations': [loc for loc in case['locations'] if loc] if case['locations'] else [],
                                'case_ids': case['case_ids']
                            }
                            for i, case in enumerate(repeated_cases)
                        ],
                        "velocity_data": {
                            "peak_hour": "14:00-15:00",
                            "avg_per_hour": real_time_stats['total_transactions'] // (24 * days),
                            "trend": "Increasing" if real_time_stats['high_value_txns'] > 10 else "Stable",
                            "hourly_data": []  # Could add hourly breakdown
                        },
                        "geographic_patterns": [
                            {
                                'location': geo['country'],
                                'case_count': geo['transaction_count'],
                                'total_amount': float(geo['total_amount']) if geo['total_amount'] else 0,
                                'risk_level': 'high' if geo['transaction_count'] > 100 else 'medium' if geo['transaction_count'] > 50 else 'low',
                                'trend': 'Increasing'  # Could calculate actual trend
                            }
                            for geo in geographic_patterns
                        ],
                        "generated_at": datetime.now().isoformat()
                    }
                }
                
    except Exception as e:
        print(f"ERROR: Failed to fetch fraud patterns: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch fraud patterns: {str(e)}")

@router.get("/api/super-user/all-case-logs")
async def get_all_case_logs_for_super_user(
    current_username: Annotated[str, Depends(get_current_username)],
    matcher: Annotated[CaseEntryMatcher, Depends(get_case_matcher_instance)]
) -> Dict[str, Any]:
    """
    Get logs for all cases in the system. Only accessible by super_user.
    This is useful for the UserActivity page to show comprehensive case activity.
    """
    try:
        # Check if user is super_user
        user_type = await matcher.fetch_user_type(current_username)
        if user_type != 'super_user':
            raise HTTPException(
                status_code=403, 
                detail="Only super_user can access all case logs."
            )
        
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get all case logs with case information
                cur.execute(
                    """
                    SELECT 
                        cl.id,
                        cl.case_id,
                        cl.user_name,
                        cl.action,
                        cl.details,
                        cl.created_at,
                        cm.source_ack_no,
                        cm.case_type,
                        cm.status
                    FROM case_logs cl
                    LEFT JOIN case_main cm ON cl.case_id = cm.case_id
                    ORDER BY cl.created_at DESC
                    LIMIT 1000
                    """
                )
                
                logs = []
                for row in cur.fetchall():
                    logs.append({
                        "id": row["id"],
                        "case_id": row["case_id"],
                        "user_name": row["user_name"],
                        "action": row["action"],
                        "details": row["details"],
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                        "source_ack_no": row["source_ack_no"],
                        "case_type": row["case_type"],
                        "status": row["status"]
                    })
                
                return {
                    "success": True,
                    "logs": logs,
                    "total_count": len(logs)
                }
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to fetch all case logs: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch all case logs. Error: {e}")


@router.get("/api/super-user/delayed-cases")
async def get_risk_officer_delayed_cases(
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """Return cases assigned to risk officers that haven't been acted upon for X days. Only accessible by super_user."""
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if user is super_user
                cur.execute("SELECT user_type FROM user_table WHERE user_name = %s", (current_username,))
                user_row = cur.fetchone()
                if not user_row or user_row.get('user_type') != 'super_user':
                    raise HTTPException(status_code=403, detail="Only super users can access risk officer delayed cases.")
                
                # Get delayed cases assigned to risk officers (no action for X days)
                # Use subquery to get the most recent active assignment to avoid duplicates
                cur.execute(
                    """
                    SELECT 
                        cm.case_id,
                        cm.source_ack_no,
                        cm.case_type,
                        cm.status,
                        cm.creation_date,
                        latest_assignment.assigned_to as current_assigned_to,
                        latest_assignment.assigned_by as assigned_by,
                        latest_assignment.assign_date,
                        latest_assignment.assign_time,
                        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - COALESCE(latest_assignment.assign_date, cm.creation_date))) / 86400 AS days_old,
                        cl.last_action_date
                    FROM case_main cm
                    LEFT JOIN (
                        SELECT DISTINCT ON (case_id)
                            case_id,
                            assigned_to,
                            assigned_by,
                            assign_date,
                            assign_time
                        FROM assignment 
                        WHERE is_active = TRUE
                        ORDER BY case_id, assign_date DESC
                    ) latest_assignment ON cm.case_id = latest_assignment.case_id
                    LEFT JOIN (
                        SELECT 
                            case_id,
                            MAX(created_at) as last_action_date
                        FROM case_logs 
                        GROUP BY case_id
                    ) cl ON cm.case_id = cl.case_id
                    WHERE latest_assignment.assigned_to IN (
                        SELECT user_name FROM user_table WHERE user_type = 'risk_officer'
                    )
                    AND LOWER(cm.status) != 'closed'
                    AND EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - COALESCE(latest_assignment.assign_date, cm.creation_date))) / 86400 >= %s
                    AND (
                        cl.last_action_date IS NULL 
                        OR cl.last_action_date < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    )
                    ORDER BY COALESCE(latest_assignment.assign_date, cm.creation_date) ASC
                    """,
                    (RISK_OFFICER_DELAY_THRESHOLD_DAYS, RISK_OFFICER_DELAY_THRESHOLD_DAYS)
                )
                
                delayed_cases = cur.fetchall() or []
                
                # Convert to list of dictionaries and format the data
                result = []
                for case in delayed_cases:
                    result.append({
                        "case_id": case['case_id'],
                        "source_ack_no": case['source_ack_no'],
                        "case_type": case['case_type'],
                        "status": case['status'],
                        "creation_date": case['creation_date'].isoformat() if case['creation_date'] else None,
                        "days_old": round(float(case['days_old'])),
                        "current_assigned_to": case['current_assigned_to'],
                        "assigned_by": case['assigned_by'],
                        "assign_date": case['assign_date'].isoformat() if case['assign_date'] else None,
                        "assign_time": case['assign_time'].isoformat() if case['assign_time'] else None,
                        "last_action_date": case['last_action_date'].isoformat() if case['last_action_date'] else None
                    })
                
                return {
                    "delayed_cases": result,
                    "threshold_days": RISK_OFFICER_DELAY_THRESHOLD_DAYS,
                    "total_count": len(result),
                    "case_type": "risk_officer"
                }
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to fetch risk officer delayed cases: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch risk officer delayed cases. Error: {e}")


@router.get("/api/supervisor/delayed-cases")
async def get_department_delayed_cases(
    current_username: Annotated[str, Depends(get_current_username)]
) -> Dict[str, Any]:
    """Return cases assigned to the supervisor's department that haven't been acted upon for X days. Only accessible by supervisors."""
    try:
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if user is supervisor and get their department
                cur.execute("SELECT user_type, dept FROM user_table WHERE user_name = %s", (current_username,))
                user_row = cur.fetchone()
                if not user_row or user_row.get('user_type') != 'supervisor':
                    raise HTTPException(status_code=403, detail="Only supervisors can access department delayed cases.")
                
                supervisor_dept = user_row.get('dept')
                if not supervisor_dept:
                    raise HTTPException(status_code=400, detail="Supervisor department not found.")
                
                # Use generic threshold for all departments (no hardcoded department names)
                # All departments use the same default threshold, making it scalable for any new departments
                threshold_days = 3  # Default threshold for all departments
                
                # Get delayed cases assigned to this department (no action for X days)
                # Use subquery to get the most recent active assignment to avoid duplicates
                cur.execute(
                    """
                    SELECT 
                        cm.case_id,
                        cm.source_ack_no,
                        cm.case_type,
                        cm.status,
                        cm.creation_date,
                        latest_assignment.assigned_to as current_assigned_to,
                        latest_assignment.assigned_by as assigned_by,
                        latest_assignment.assign_date,
                        latest_assignment.assign_time,
                        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - COALESCE(latest_assignment.assign_date, cm.creation_date))) / 86400 AS days_old,
                        cl.last_action_date,
                        ut.dept as assigned_dept
                    FROM case_main cm
                    LEFT JOIN (
                        SELECT DISTINCT ON (case_id)
                            case_id,
                            assigned_to,
                            assigned_by,
                            assign_date,
                            assign_time
                        FROM assignment 
                        WHERE is_active = TRUE
                        ORDER BY case_id, assign_date DESC
                    ) latest_assignment ON cm.case_id = latest_assignment.case_id
                    LEFT JOIN user_table ut ON latest_assignment.assigned_to = ut.user_name
                    LEFT JOIN (
                        SELECT 
                            case_id,
                            MAX(created_at) as last_action_date
                        FROM case_logs 
                        GROUP BY case_id
                    ) cl ON cm.case_id = cl.case_id
                    WHERE ut.dept = %s
                    AND LOWER(cm.status) != 'closed'
                    AND EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - COALESCE(latest_assignment.assign_date, cm.creation_date))) / 86400 >= %s
                    AND (
                        cl.last_action_date IS NULL 
                        OR cl.last_action_date < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    )
                    ORDER BY COALESCE(latest_assignment.assign_date, cm.creation_date) ASC
                    """,
                    (supervisor_dept, threshold_days, threshold_days)
                )
                
                delayed_cases = cur.fetchall() or []
                
                # Convert to list of dictionaries and format the data
                result = []
                for case in delayed_cases:
                    result.append({
                        "case_id": case['case_id'],
                        "source_ack_no": case['source_ack_no'],
                        "case_type": case['case_type'],
                        "status": case['status'],
                        "creation_date": case['creation_date'].isoformat() if case['creation_date'] else None,
                        "days_old": round(float(case['days_old'])),
                        "current_assigned_to": case['current_assigned_to'],
                        "assigned_by": case['assigned_by'],
                        "assign_date": case['assign_date'].isoformat() if case['assign_date'] else None,
                        "assign_time": case['assign_time'].isoformat() if case['assign_time'] else None,
                        "last_action_date": case['last_action_date'].isoformat() if case['last_action_date'] else None,
                        "assigned_dept": case['assigned_dept']
                    })
                
                return {
                    "delayed_cases": result,
                    "threshold_days": threshold_days,
                    "total_count": len(result),
                    "case_type": "department",
                    "department": supervisor_dept
                }
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to fetch department delayed cases: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch department delayed cases. Error: {e}")


