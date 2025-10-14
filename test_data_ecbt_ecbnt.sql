-- =====================================================
-- TEST DATA SETUP FOR ECBT AND ECBNT CASES
-- =====================================================
-- This script sets up all required test data for testing
-- ECBT (with transactions) and ECBNT (without transactions) cases
-- =====================================================

-- Clean up any existing test data first (optional - comment out if you want to keep existing data)
-- DELETE FROM txn WHERE rrn IN ('1234567890123', '9876543210987', '5555666677889');
-- DELETE FROM acc_bene WHERE cust_acct_num IN ('1234567890', '5555666677778888');
-- DELETE FROM account_customer WHERE acc_num IN ('1234567890', '5555666677778888', '9999888877776666');
-- DELETE FROM account WHERE acc_num IN ('1234567890', '5555666677778888', '9999888877776666', '7000723456789999', '9000111122223333');
-- DELETE FROM customer WHERE cust_id IN ('TESTCUST001', 'TESTCUST002', 'TESTVICTIM001');

-- =====================================================
-- SCENARIO 1: ECBT (Existing Customer with Transactions)
-- =====================================================

-- 1. Insert Customer 1 (Potential Victim for ECBT)
INSERT INTO customer (
    cust_id, fname, mname, lname, mobile, email, pan, nat_id,
    dob, citizen, occupation, seg, cust_type, risk_prof, kyc_status,
    cust_creation_date, rel_value
) VALUES (
    'TESTCUST001',              -- Customer ID
    'Rajesh',                   -- First name
    'Kumar',                    -- Middle name
    'Sharma',                   -- Last name
    '9876543210',               -- Mobile
    'rajesh.sharma@email.com',  -- Email
    'ABCDE1234F',               -- PAN
    '123456789012',             -- Aadhaar
    '1985-06-15',               -- DOB
    'Indian',                   -- Citizen
    'Service',                  -- Occupation
    'Mass',                     -- Segment
    'Individual',               -- Customer type
    'Low',                      -- Risk profile
    'Verified',                 -- KYC status
    '2020-01-15',               -- Customer creation date
    500000.00                   -- Relationship value
) ON CONFLICT (cust_id) DO UPDATE SET
    fname = EXCLUDED.fname,
    mobile = EXCLUDED.mobile,
    email = EXCLUDED.email;

-- 2. Insert Customer 1's Account
INSERT INTO account (
    acc_num, acc_name, acc_type, acc_status, open_date, branch_code,
    currency, balance, prod_code, min_bal, od_limit, credit_score,
    aqb, interest_rate, last_txn_date
) VALUES (
    '1234567890',               -- Account number
    'Rajesh Kumar Sharma',      -- Account name
    'Savings',                  -- Account type
    'Active',                   -- Account status
    '2020-01-15',               -- Open date
    'BR001',                    -- Branch code
    'INR',                      -- Currency
    125000.00,                  -- Balance
    'SB001',                    -- Product code
    10000.00,                   -- Minimum balance
    0.00,                       -- OD limit
    750,                        -- Credit score
    45000.00,                   -- AQB
    4.00,                       -- Interest rate
    '2024-01-15'                -- Last transaction date
) ON CONFLICT (acc_num) DO UPDATE SET
    acc_name = EXCLUDED.acc_name,
    balance = EXCLUDED.balance,
    acc_status = EXCLUDED.acc_status;

-- 3. Link Customer 1 to Account
INSERT INTO account_customer (cust_id, acc_num)
VALUES ('TESTCUST001', '1234567890')
ON CONFLICT (cust_id, acc_num) DO NOTHING;

-- 4. Insert Fraudulent Beneficiary Account (for ECBT)
INSERT INTO account (
    acc_num, acc_name, acc_type, acc_status, open_date, branch_code,
    currency, balance, prod_code, min_bal, od_limit, credit_score,
    aqb, interest_rate, last_txn_date
) VALUES (
    '7000723456789999',         -- Fraudulent account number
    'Fraudster One',            -- Account name
    'Savings',                  -- Account type
    'Active',                   -- Account status
    '2023-06-10',               -- Open date
    'BR099',                    -- Branch code
    'INR',                      -- Currency
    250000.00,                  -- Balance
    'SB001',                    -- Product code
    10000.00,                   -- Minimum balance
    0.00,                       -- OD limit
    650,                        -- Credit score
    25000.00,                   -- AQB
    4.00,                       -- Interest rate
    '2024-01-15'                -- Last transaction date
) ON CONFLICT (acc_num) DO UPDATE SET
    acc_name = EXCLUDED.acc_name,
    balance = EXCLUDED.balance;

-- 5. Add Beneficiary Relationship (Customer 1 has added Fraudster as beneficiary)
INSERT INTO acc_bene (cust_acct_num, bene_acct_num)
VALUES ('1234567890', '7000723456789999')
ON CONFLICT (cust_acct_num, bene_acct_num) DO NOTHING;

-- 6. Insert Transactions from Customer 1 to Fraudulent Beneficiary (This makes it ECBT)
INSERT INTO txn (
    acct_num, bene_acct_num, amount, txn_date, txn_time, 
    rrn, channel, descr, txn_type, currency, bene_name, pay_method,
    fee, exch_rate, pay_ref, auth_code
) VALUES 
(
    '1234567890',                   -- Customer account (payer)
    '7000723456789999',             -- Fraudulent beneficiary account (payee)
    5000.00,                        -- Amount
    '2024-01-15',                   -- Transaction date
    '14:30:00',                     -- Transaction time
    '1234567890123',                -- RRN (USE THIS IN API PAYLOAD)
    'UPI',                          -- Channel
    'Payment for services',         -- Description
    'DEBIT',                        -- Transaction type
    'INR',                          -- Currency
    'Fraudster One',                -- Beneficiary name
    'UPI',                          -- Payment method
    0.00,                           -- Fee
    1.00,                           -- Exchange rate
    'UPI2024011514300001',          -- Payment reference
    'AUTH123456'                    -- Auth code
),
(
    '1234567890',                   -- Customer account (payer)
    '7000723456789999',             -- Fraudulent beneficiary account (payee)
    3500.00,                        -- Amount
    '2024-01-10',                   -- Transaction date
    '11:20:00',                     -- Transaction time
    '5555666677889',                -- RRN (Additional transaction)
    'IMPS',                         -- Channel
    'Online transfer',              -- Description
    'DEBIT',                        -- Transaction type
    'INR',                          -- Currency
    'Fraudster One',                -- Beneficiary name
    'IMPS',                         -- Payment method
    5.00,                           -- Fee
    1.00,                           -- Exchange rate
    'IMPS2024011011200002',         -- Payment reference
    'AUTH789012'                    -- Auth code
)
ON CONFLICT (rrn) DO NOTHING;

-- =====================================================
-- SCENARIO 2: ECBNT (Existing Customer WITHOUT Transactions)
-- =====================================================

-- 7. Insert Customer 2 (Potential Victim for ECBNT)
INSERT INTO customer (
    cust_id, fname, mname, lname, mobile, email, pan, nat_id,
    dob, citizen, occupation, seg, cust_type, risk_prof, kyc_status,
    cust_creation_date, rel_value
) VALUES (
    'TESTCUST002',              -- Customer ID
    'Priya',                    -- First name
    '',                         -- Middle name (empty)
    'Patel',                    -- Last name
    '8765432109',               -- Mobile
    'priya.patel@email.com',    -- Email
    'XYZAB5678C',               -- PAN
    '987654321098',             -- Aadhaar
    '1990-03-22',               -- DOB
    'Indian',                   -- Citizen
    'Business',                 -- Occupation
    'SME',                      -- Segment
    'Individual',               -- Customer type
    'Medium',                   -- Risk profile
    'Verified',                 -- KYC status
    '2019-05-20',               -- Customer creation date
    750000.00                   -- Relationship value
) ON CONFLICT (cust_id) DO UPDATE SET
    fname = EXCLUDED.fname,
    mobile = EXCLUDED.mobile,
    email = EXCLUDED.email;

-- 8. Insert Customer 2's Account
INSERT INTO account (
    acc_num, acc_name, acc_type, acc_status, open_date, branch_code,
    currency, balance, prod_code, min_bal, od_limit, credit_score,
    aqb, interest_rate, last_txn_date
) VALUES (
    '5555666677778888',         -- Account number
    'Priya Patel',              -- Account name
    'Current',                  -- Account type
    'Active',                   -- Account status
    '2019-05-20',               -- Open date
    'BR002',                    -- Branch code
    'INR',                      -- Currency
    285000.00,                  -- Balance
    'CA001',                    -- Product code
    25000.00,                   -- Minimum balance
    50000.00,                   -- OD limit
    780,                        -- Credit score
    85000.00,                   -- AQB
    3.50,                       -- Interest rate
    '2024-01-20'                -- Last transaction date
) ON CONFLICT (acc_num) DO UPDATE SET
    acc_name = EXCLUDED.acc_name,
    balance = EXCLUDED.balance,
    acc_status = EXCLUDED.acc_status;

-- 9. Link Customer 2 to Account
INSERT INTO account_customer (cust_id, acc_num)
VALUES ('TESTCUST002', '5555666677778888')
ON CONFLICT (cust_id, acc_num) DO NOTHING;

-- 10. Insert Another Fraudulent Beneficiary Account (for ECBNT)
INSERT INTO account (
    acc_num, acc_name, acc_type, acc_status, open_date, branch_code,
    currency, balance, prod_code, min_bal, od_limit, credit_score,
    aqb, interest_rate, last_txn_date
) VALUES (
    '9000111122223333',         -- Fraudulent account number
    'Fraudster Two',            -- Account name
    'Savings',                  -- Account type
    'Active',                   -- Account status
    '2023-08-25',               -- Open date
    'BR099',                    -- Branch code
    'INR',                      -- Currency
    150000.00,                  -- Balance
    'SB001',                    -- Product code
    10000.00,                   -- Minimum balance
    0.00,                       -- OD limit
    600,                        -- Credit score
    30000.00,                   -- AQB
    4.00,                       -- Interest rate
    '2024-01-20'                -- Last transaction date
) ON CONFLICT (acc_num) DO UPDATE SET
    acc_name = EXCLUDED.acc_name,
    balance = EXCLUDED.balance;

-- 11. Add Beneficiary Relationship (Customer 2 has added Fraudster Two as beneficiary)
-- BUT NO TRANSACTIONS - This makes it ECBNT
INSERT INTO acc_bene (cust_acct_num, bene_acct_num)
VALUES ('5555666677778888', '9000111122223333')
ON CONFLICT (cust_acct_num, bene_acct_num) DO NOTHING;

-- IMPORTANT: NO transactions between 5555666677778888 and 9000111122223333
-- This is what makes it an ECBNT case

-- =====================================================
-- VICTIM DATA (For the I4C complaint side)
-- =====================================================

-- 12. Insert Victim Customer (who filed the complaint)
INSERT INTO customer (
    cust_id, fname, mname, lname, mobile, email, pan, nat_id,
    dob, citizen, occupation, seg, cust_type, risk_prof, kyc_status,
    cust_creation_date, rel_value
) VALUES (
    'TESTVICTIM001',            -- Customer ID
    'Amit',                     -- First name
    'Singh',                    -- Middle name
    'Verma',                    -- Last name
    '9123456789',               -- Mobile
    'amit.verma@email.com',     -- Email
    'PQRST9876D',               -- PAN
    '456789123456',             -- Aadhaar
    '1988-11-08',               -- DOB
    'Indian',                   -- Citizen
    'Private Sector',           -- Occupation
    'Mass',                     -- Segment
    'Individual',               -- Customer type
    'Low',                      -- Risk profile
    'Verified',                 -- KYC status
    '2018-03-10',               -- Customer creation date
    350000.00                   -- Relationship value
) ON CONFLICT (cust_id) DO UPDATE SET
    fname = EXCLUDED.fname,
    mobile = EXCLUDED.mobile,
    email = EXCLUDED.email;

-- 13. Insert Victim's Account (from complaint)
INSERT INTO account (
    acc_num, acc_name, acc_type, acc_status, open_date, branch_code,
    currency, balance, prod_code, min_bal, od_limit, credit_score,
    aqb, interest_rate, last_txn_date
) VALUES (
    '9999888877776666',         -- Victim account number (used in complaint)
    'Amit Singh Verma',         -- Account name
    'Savings',                  -- Account type
    'Active',                   -- Account status
    '2018-03-10',               -- Open date
    'BR005',                    -- Branch code
    'INR',                      -- Currency
    95000.00,                   -- Balance (reduced due to fraud)
    'SB001',                    -- Product code
    10000.00,                   -- Minimum balance
    0.00,                       -- OD limit
    720,                        -- Credit score
    35000.00,                   -- AQB
    4.00,                       -- Interest rate
    '2024-01-20'                -- Last transaction date
) ON CONFLICT (acc_num) DO UPDATE SET
    acc_name = EXCLUDED.acc_name,
    balance = EXCLUDED.balance;

-- 14. Link Victim to Account
INSERT INTO account_customer (cust_id, acc_num)
VALUES ('TESTVICTIM001', '9999888877776666')
ON CONFLICT (cust_id, acc_num) DO NOTHING;

-- 15. Insert Fraudulent Transaction from Victim to Fraudster Two (for ECBNT scenario)
-- This transaction will be in the I4C complaint and create VM case
-- The RRN will be used in the ECBNT test payload
INSERT INTO txn (
    acct_num, bene_acct_num, amount, txn_date, txn_time, 
    rrn, channel, descr, txn_type, currency, bene_name, pay_method,
    fee, exch_rate, pay_ref, auth_code
) VALUES (
    '9999888877776666',             -- Victim account (payer)
    '9000111122223333',             -- Fraudulent beneficiary account (payee)
    3000.00,                        -- Amount
    '2024-01-20',                   -- Transaction date
    '10:15:00',                     -- Transaction time
    '9876543210987',                -- RRN (USE THIS IN ECBNT API PAYLOAD)
    'IMPS',                         -- Channel
    'Online transfer - fraudulent', -- Description
    'DEBIT',                        -- Transaction type
    'INR',                          -- Currency
    'Fraudster Two',                -- Beneficiary name
    'IMPS',                         -- Payment method
    5.00,                           -- Fee
    1.00,                           -- Exchange rate
    'IMPS2024012010150003',         -- Payment reference
    'AUTH345678'                    -- Auth code
) ON CONFLICT (rrn) DO NOTHING;

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify Customers
SELECT 'Customers' as table_name, cust_id, fname, lname, mobile 
FROM customer 
WHERE cust_id IN ('TESTCUST001', 'TESTCUST002', 'TESTVICTIM001');

-- Verify Accounts
SELECT 'Accounts' as table_name, acc_num, acc_name, acc_status, balance 
FROM account 
WHERE acc_num IN ('1234567890', '5555666677778888', '9999888877776666', '7000723456789999', '9000111122223333');

-- Verify Account-Customer Links
SELECT 'Account-Customer Links' as table_name, cust_id, acc_num 
FROM account_customer 
WHERE acc_num IN ('1234567890', '5555666677778888', '9999888877776666');

-- Verify Beneficiary Relationships
SELECT 'Beneficiary Relationships' as table_name, cust_acct_num, bene_acct_num 
FROM acc_bene 
WHERE cust_acct_num IN ('1234567890', '5555666677778888');

-- Verify Transactions
SELECT 'Transactions' as table_name, rrn, acct_num, bene_acct_num, amount, txn_date, channel 
FROM txn 
WHERE rrn IN ('1234567890123', '9876543210987', '5555666677889')
ORDER BY txn_date DESC;

-- Verify ECBT Setup (should return rows)
SELECT 'ECBT Check: Customer 1 has transactions with Fraudster 1' as check_name,
       COUNT(*) as transaction_count
FROM txn 
WHERE acct_num = '1234567890' AND bene_acct_num = '7000723456789999';

-- Verify ECBNT Setup (should return 0 rows)
SELECT 'ECBNT Check: Customer 2 has NO transactions with Fraudster 2' as check_name,
       COUNT(*) as transaction_count
FROM txn 
WHERE acct_num = '5555666677778888' AND bene_acct_num = '9000111122223333';

-- =====================================================
-- SUMMARY OF TEST DATA
-- =====================================================
/*
ECBT TEST (Scenario 1):
- Customer: TESTCUST001 (Rajesh Kumar Sharma)
- Customer Account: 1234567890
- Fraudulent Beneficiary: 7000723456789999
- Has Transactions: YES (2 transactions)
- RRN for API Payload: 1234567890123
- Expected Result: ECBT case created

ECBNT TEST (Scenario 2):
- Customer: TESTCUST002 (Priya Patel)
- Customer Account: 5555666677778888
- Fraudulent Beneficiary: 9000111122223333
- Has Transactions: NO (beneficiary saved but no transactions)
- Victim Account (complaint): 9999888877776666
- RRN for API Payload: 9876543210987
- Expected Result: ECBNT case created

After running this script, use the API payloads from ECBT_ECBNT_TEST_PAYLOADS.md
*/

