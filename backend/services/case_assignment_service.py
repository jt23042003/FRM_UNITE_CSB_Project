"""
Case Assignment Service - Simplified Version

This service handles automatic assignment of new cases to risk officers.
All cases are assigned to a general risk officer queue without complex rules.
"""

import psycopg2
from typing import Dict, List, Optional
from config import DB_CONNECTION_PARAMS
from concurrent.futures import ThreadPoolExecutor


class CaseAssignmentService:
    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor
    
    async def _execute_sync_db_op(self, sync_func):
        """Execute a synchronous database operation in the thread pool"""
        import asyncio
        return await asyncio.get_running_loop().run_in_executor(self.executor, sync_func)
    
    def _get_risk_officers(self) -> List[Dict[str, str]]:
        """Get all active risk officers from user_table"""
        with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_name, dept 
                    FROM user_table 
                    WHERE user_type = 'risk_officer'
                    ORDER BY user_name
                """)
                return [{"username": row[0], "dept": row[1]} for row in cur.fetchall()]
    
    # COMMENTED OUT: Complex case type assignment rules
    # def _get_case_type_assignment_rules(self) -> Dict[str, str]:
    #     """Get case type assignment rules from database or return default rules"""
    #     return {
    #         'ECBT': 'risk_user1',    # ECBT cases go to risk_user1
    #         'ECBNT': 'risk_user2',   # ECBNT cases go to risk_user2
    #         'NAB': 'risk_user3',     # NAB cases go to risk_user3
    #         'PSA': 'risk_user4',     # PSA cases go to risk_user4
    #         'VM': None,              # VM cases use round-robin
    #         'BM': None,              # BM cases use round-robin
    #         'NAA': None              # NAA cases use round-robin
    #     }
    
    # COMMENTED OUT: Assignment state tracking for round-robin
    # def _get_assignment_state(self) -> Dict[str, int]:
    #     """Get current assignment state from database"""
    #     with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
    #         with conn.cursor() as cur:
    #             # Create assignment_state table if it doesn't exist
    #             cur.execute("""
    #                 CREATE TABLE IF NOT EXISTS assignment_state (
    #                     id SERIAL PRIMARY KEY,
    #                     last_assigned_user VARCHAR(50),
    #                     assignment_counts JSONB DEFAULT '{}',
    #                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #                     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #                 )
    #             """)
    #             
    #             # Get current state
    #             cur.execute("SELECT last_assigned_user, assignment_counts FROM assignment_state ORDER BY id DESC LIMIT 1")
    #             result = cur.fetchone()
    #             
    #             if result:
    #                 return {
    #                     'last_assigned_user': result[0],
    #                     'assignment_counts': result[1] or {}
    #                 }
    #             else:
    #                 # Initialize with empty state
    #                 cur.execute("""
    #                     INSERT INTO assignment_state (last_assigned_user, assignment_counts) 
    #                     VALUES (NULL, '{}') 
    #                     RETURNING last_assigned_user, assignment_counts
    #                 """)
    #                 result = cur.fetchone()
    #                 conn.commit()
    #                 return {
    #                     'last_assigned_user': result[0],
    #                     'assignment_counts': result[1] or {}
    #                 }
    
    # COMMENTED OUT: Assignment state update for round-robin
    # def _update_assignment_state(self, last_assigned_user: str, assignment_counts: Dict[str, int]):
    #     """Update assignment state in database"""
    #     with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
    #         with conn.cursor() as cur:
    #             cur.execute("""
    #                 UPDATE assignment_state 
    #                 SET last_assigned_user = %s, 
    #                     assignment_counts = %s, 
    #                     updated_at = CURRENT_TIMESTAMP
    #                 WHERE id = (SELECT id FROM assignment_state ORDER BY id DESC LIMIT 1)
    #             """, (last_assigned_user, json.dumps(assignment_counts)))
    #             conn.commit()
    
    # COMMENTED OUT: Complex round-robin logic
    # def _get_next_round_robin_user(self, risk_officers: List[Dict[str, str]], 
    #                                current_state: Dict[str, int]) -> str:
    #     """Get next user in round-robin sequence"""
    #     if not risk_officers:
    #         raise ValueError("No risk officers available for assignment")
    #     
    #     last_assigned = current_state.get('last_assigned_user')
    #     assignment_counts = current_state.get('assignment_counts', {})
    #     
    #     # Initialize counts for all risk officers if not present
    #     for officer in risk_officers:
    #         username = officer['username']
    #         if username not in assignment_counts:
    #             assignment_counts[username] = 0
    #     
    #     # Find the user with minimum cases
    #     min_cases = min(assignment_counts.values())
    #     candidates = [user for user, count in assignment_counts.items() if count == min_cases]
    #     
    #     # If we have multiple candidates with same minimum count, use round-robin
    #     if len(candidates) > 1 and last_assigned in candidates:
    #         # Find next user after last_assigned in the candidates list
    #         try:
    #             current_index = candidates.index(last_assigned)
    #             next_index = (current_index + 1) % len(candidates)
    #             return candidates[next_index]
    #         except ValueError:
    #             # last_assigned not in candidates, just pick first
    #             return candidates[0]
    #     else:
    #         # Return first candidate with minimum cases
    #         return candidates[0]
    
    async def assign_case_to_user(self, case_id: int, case_type: str, 
                                  assigned_by: str = "System") -> Optional[str]:
        """
        Assign a case to the general risk officer queue.
        All cases go to the same queue without complex assignment rules.
        
        Args:
            case_id: The case ID to assign
            case_type: Type of case (ECBT, ECBNT, VM, BM, etc.) - kept for compatibility
            assigned_by: Who is making the assignment (default: System)
            
        Returns:
            Username of assigned user or None if assignment failed
        """
        def _sync_assign():
            try:
                # Get all risk officers
                risk_officers = self._get_risk_officers()
                
                if not risk_officers:
                    print(f"ERROR: No risk officers available for case assignment", flush=True)
                    return None
                
                # SIMPLIFIED: Just assign to the first available risk officer
                # All cases go to the general queue
                assigned_user = risk_officers[0]['username']
                print(f"SIMPLIFIED ASSIGNMENT: Case {case_id} ({case_type}) assigned to general queue: {assigned_user}", flush=True)
                
                # Verify assigned user exists
                user_exists = any(officer['username'] == assigned_user for officer in risk_officers)
                if not user_exists:
                    print(f"ERROR: Assigned user {assigned_user} not found in risk officers list", flush=True)
                    return None
                
                # Create assignment record
                with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
                    with conn.cursor() as cur:
                        # Ensure columns exist
                        cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
                        cur.execute("ALTER TABLE assignment ADD COLUMN IF NOT EXISTS assignment_type VARCHAR(50) DEFAULT 'manual'")
                        
                        # Insert assignment with type 'auto' for automatic assignments
                        cur.execute("""
                            INSERT INTO assignment (case_id, assigned_to, assigned_by, comment, is_active, assignment_type)
                            VALUES (%s, %s, %s, %s, TRUE, 'auto')
                        """, (case_id, assigned_user, assigned_by, f"Auto-assigned {case_type} case to general queue"))
                        
                        conn.commit()
                        print(f"✅ Case {case_id} successfully assigned to general queue: {assigned_user}", flush=True)
                        return assigned_user
                        
            except Exception as e:
                print(f"ERROR: Failed to assign case {case_id}: {e}", flush=True)
                return None
        
        return await self._execute_sync_db_op(_sync_assign)
    
    async def get_assignment_statistics(self) -> Dict[str, any]:
        """Get current assignment statistics - simplified version"""
        def _sync_get_stats():
            try:
                risk_officers = self._get_risk_officers()
                
                # Get actual case counts from database
                with psycopg2.connect(**DB_CONNECTION_PARAMS) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT assigned_to, COUNT(*) as case_count
                            FROM assignment 
                            WHERE is_active = TRUE
                            GROUP BY assigned_to
                        """)
                        actual_counts = {row[0]: row[1] for row in cur.fetchall()}
                
                stats = {
                    'risk_officers': [officer['username'] for officer in risk_officers],
                    'actual_counts': actual_counts,
                    'assignment_method': 'simplified_general_queue',
                    'note': 'All cases assigned to general risk officer queue'
                }
                
                return stats
                
            except Exception as e:
                print(f"ERROR: Failed to get assignment statistics: {e}", flush=True)
                return {}
        
        return await self._execute_sync_db_op(_sync_get_stats)
    
    # COMMENTED OUT: Complex case type rules update
    # async def update_case_type_rules(self, new_rules: Dict[str, str]) -> bool:
    #     """Update case type assignment rules (for future database storage)"""
    #     print(f"Case type rules update requested: {new_rules}", flush=True)
    #     print("Note: Case type rules are currently hardcoded. Update requires code deployment.", flush=True)
    #     return False
