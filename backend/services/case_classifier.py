import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Dict, Any, Optional

# Import database connection utilities
from db.connection import get_db_connection, get_db_cursor
from psycopg2.extras import RealDictCursor

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CaseClassifier:
    """
    Service class to classify cases based on account number and
    fetch relevant customer details for case_details_1 entry.
    """
    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor
        logging.info("CaseClassifier service initialized.")

    async def _execute_db_query(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Helper to execute a single SELECT query in the thread pool.
        Returns the first row as a dictionary, or None if no row found.
        """
        try:
            # Run the synchronous DB operation in the thread pool
            result = await asyncio.to_thread(self._sync_db_query_one, query, params)
            return result
        except Exception as e:
            logging.error(f"Database query failed: {e}", exc_info=True)
            return None

    def _sync_db_query_one(self, query: str, params: tuple) -> Optional[Dict[str, Any]]:
        """Synchronous part: executes a query and fetches one row."""
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute(query, params)
                return cur.fetchone()

    async def _execute_db_insert(self, query: str, params: tuple = ()) -> Optional[int]:
        """
        Helper to execute an INSERT query in the thread pool.
        Returns the ID of the newly inserted row, or None on failure.
        """
        try:
            # Run the synchronous DB operation in the thread pool
            new_id = await asyncio.to_thread(self._sync_db_insert_one, query, params)
            return new_id
        except Exception as e:
            logging.error(f"Database insert failed: {e}", exc_info=True)
            return None

    def _sync_db_insert_one(self, query: str, params: tuple) -> Optional[int]:
        """Synchronous part: executes an INSERT query and fetches the ID."""
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute(query, params)
                # Assuming 'caseid' is returned by RETURNING clause in insert query
                new_id = cur.fetchone()['caseid']
                conn.commit() # Commit the transaction
                return new_id


    async def classify_and_create_case(self, to_account: str, card_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Classifies the case based on to_account and creates an entry in case_details_1.
        Returns the created case details or None if no match.
        """
        logging.info(f"Classifying case for to_account: {to_account}")

        customer_details = {
            "cust_id": None,
            "mobile": None,
            "email": None,
            "pan": None,
            "aadhar": None,
        }
        case_type = None
        match_flag = None

        # --- Scenario 1: ECB (Existing Customer with Transaction with Beneficiary) ---
        logging.debug(f"Checking for ECB: to_account='{to_account}' in txn.bene_acct_num")
        # Check if to_account exists as bene_acct_num in txn table
        txn_query = "SELECT bene_acct_num FROM txn WHERE bene_acct_num = %s LIMIT 1;"
        matching_txn = await self._execute_db_query(txn_query, (to_account,))

        if matching_txn:
            logging.info(f"Match found in txn table for to_account: {to_account}")
            # Find cust_id via account_customer table
            acc_cust_query = "SELECT cust_id, acc_num FROM account_customer WHERE acc_num = %s LIMIT 1;"
            account_customer_entry = await self._execute_db_query(acc_cust_query, (to_account,))

            if account_customer_entry:
                cust_id = account_customer_entry['cust_id']
                logging.info(f"Account {to_account} linked to cust_id: {cust_id} in account_customer.")
                
                # Get customer details
                customer_query = """
                    SELECT cust_id, phone, email, pan, nat_id 
                    FROM customer 
                    WHERE cust_id = %s LIMIT 1;
                """
                customer = await self._execute_db_query(customer_query, (cust_id,))

                if customer:
                    logging.info(f"Customer details found for cust_id: {cust_id}")
                    case_type = "ECB"
                    match_flag = "TXN_MATCH"
                    customer_details["cust_id"] = customer['cust_id']
                    customer_details["mobile"] = customer['phone']
                    customer_details["email"] = customer['email']
                    customer_details["pan"] = customer['pan']
                    customer_details["aadhar"] = customer['nat_id']
                else:
                    logging.warning(f"No customer found for cust_id: {cust_id} (ECB path).")
            else:
                logging.warning(f"No account_customer entry for acc_num: {to_account} (ECB path).")
        else:
            logging.info(f"No match found in txn table for to_account: {to_account}")

        # --- Scenario 2: ECBNT (Existing customer with beneficiary but no transaction data) ---
        # Only proceed if it was NOT an ECB case
        if not case_type:
            logging.debug(f"Checking for ECBNT: to_account='{to_account}' in acc_bene.bene_acct_num")
            # Check if to_account exists as bene_acct_num in acc_bene table
            acc_bene_query = "SELECT bene_acct_num FROM acc_bene WHERE bene_acct_num = %s LIMIT 1;"
            matching_bene = await self._execute_db_query(acc_bene_query, (to_account,))

            if matching_bene:
                logging.info(f"Match found in acc_bene table for to_account: {to_account}")
                # Find cust_id via account_customer table
                acc_cust_query = "SELECT cust_id, acc_num FROM account_customer WHERE acc_num = %s LIMIT 1;"
                account_customer_entry = await self._execute_db_query(acc_cust_query, (to_account,))

                if account_customer_entry:
                    cust_id = account_customer_entry['cust_id']
                    logging.info(f"Account {to_account} linked to cust_id: {cust_id} in account_customer.")
                    
                    # Get customer details
                    customer_query = """
                        SELECT cust_id, phone, email, pan, nat_id 
                        FROM customer 
                        WHERE cust_id = %s LIMIT 1;
                    """
                    customer = await self._execute_db_query(customer_query, (cust_id,))

                    if customer:
                        logging.info(f"Customer details found for cust_id: {cust_id}")
                        case_type = "ECBNT"
                        match_flag = "BENE_MATCH"
                        customer_details["cust_id"] = customer['cust_id']
                        customer_details["mobile"] = customer['phone']
                        customer_details["email"] = customer['email']
                        customer_details["pan"] = customer['pan']
                        customer_details["aadhar"] = customer['nat_id']
                    else:
                        logging.warning(f"No customer found for cust_id: {cust_id} (ECBNT path).")
                else:
                    logging.warning(f"No account_customer entry for acc_num: {to_account} (ECBNT path).")
            else:
                logging.info(f"No match found in acc_bene table for to_account: {to_account}")

        # --- Create CaseDetails1 Entry if a type was determined ---
        if case_type:
            insert_query = """
                INSERT INTO case_details_1 (
                    casetype, mobile, email, pan, card, cust_id, acc_no, aadhar, match_flag, creation_timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING caseid;
            """
            insert_params = (
                case_type,
                customer_details["mobile"],
                customer_details["email"],
                customer_details["pan"],
                card_number, # Use the card_number passed to the method
                customer_details["cust_id"],
                to_account,
                customer_details["aadhar"],
                match_flag
            )
            
            new_case_id = await self._execute_db_insert(insert_query, insert_params)

            if new_case_id:
                logging.info(f"Case {new_case_id} of type {case_type} created for account {to_account}.")
                return {
                    "case_id": new_case_id,
                    "case_type": case_type,
                    "account_number": to_account,
                    "cust_id": customer_details["cust_id"],
                    "match_flag": match_flag
                }
            else:
                logging.error(f"Failed to retrieve caseid after insertion for account {to_account}.")
                return None
        else:
            logging.info(f"No matching scenario found for to_account: {to_account}. Case not created.")
            return None # No case created
