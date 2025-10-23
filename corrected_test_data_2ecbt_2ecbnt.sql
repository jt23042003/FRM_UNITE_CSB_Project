-- =====================================
-- CORRECTED TEST DATA FOR 2 ECBT + 2 ECBNT + 1 VM
-- =====================================

-- Step 1: Add missing beneficiary relationships
-- We need customers to add the same beneficiary that appears in transactions

INSERT INTO acc_bene (
   id, cust_acct_num, bene_name, bene_acct_num, ifsc, bene_name_as_per_bank,
   bene_acct_type, bene_bank_name, bene_status_flag, bene_status,
   bene_limit_amount, bene_limit_unlimited_flag
)
VALUES
-- Customer 3 adds beneficiary 9990234567899999 (for ECBT)
(32019, '7710902234003', 'Ritika Sharma', '9990234567899999', 'SBI0006789', 'Anuj Khanna', 'Savings', 'State Bank of India', 1, 'Active', 85000.00, FALSE),

-- Customer 4 adds beneficiary 9990234567899999 (for ECBT)  
(32020, '7710902234004', 'Ritika Sharma', '9990234567899999', 'SBI0006789', 'Anuj Khanna', 'Savings', 'State Bank of India', 1, 'Active', 85000.00, FALSE),

-- Customer 1 adds beneficiary 9992234567899999 (for ECBNT)
(32021, '7710902234001', 'Ritika Sharma', '9992234567899999', 'SBI0006789', 'Anuj Khanna', 'Savings', 'State Bank of India', 1, 'Active', 85000.00, FALSE),

-- Customer 4 adds beneficiary 9992234567899999 (for ECBNT)
(32022, '7710902234004', 'Ritika Sharma', '9992234567899999', 'SBI0006789', 'Anuj Khanna', 'Savings', 'State Bank of India', 1, 'Active', 85000.00, FALSE)

ON CONFLICT (id) DO NOTHING;

-- Step 2: Add transactions for ECBT cases
-- We need transactions between customers and beneficiaries they've added

INSERT INTO txn (
   id, txn_ref, txn_date, txn_time, txn_type, amount, currency, acct_num,
   descr, fee, exch_rate, bene_name, bene_acct_num, pay_ref, auth_code,
   fraud_type, merch_name, mcc, channel, pay_method, rrn
) VALUES
-- Transaction for Customer 3 -> Beneficiary 9990234567899999 (ECBT)
(488616, 'TXN4004', '2025-10-18', '12:05:00', 'Debit', 8500.00, 'INR', '7710902234003',
'Online Transfer', 60.00, NULL, 'Anuj Khanna', '9990234567899999', 'PAY6004', 'AUTH6004',
'UPI Related Fraud', 'PhonePe', '6012', 'Mobile App', 'UPI', '9992000100'),

-- Transaction for Customer 4 -> Beneficiary 9990234567899999 (ECBT)
(488617, 'TXN4005', '2025-10-18', '12:10:00', 'Debit', 12000.00, 'INR', '7710902234004',
'Online Transfer', 80.00, NULL, 'Anuj Khanna', '9990234567899999', 'PAY6005', 'AUTH6005',
'UPI Related Fraud', 'GooglePay', '6012', 'Mobile App', 'UPI', '9992000101')

ON CONFLICT (id) DO NOTHING;

-- Step 3: Verify the setup
-- Check beneficiary relationships
SELECT 'BENEFICIARY RELATIONSHIPS' as check_name, 
       cust_acct_num, bene_acct_num, bene_name 
FROM acc_bene 
WHERE cust_acct_num LIKE '77109%' 
ORDER BY cust_acct_num, bene_acct_num;

-- Check transactions
SELECT 'TRANSACTIONS' as check_name, 
       rrn, acct_num, bene_acct_num, amount 
FROM txn 
WHERE rrn IN ('9992000088', '9992000100', '9992000101')
ORDER BY rrn;

-- Check which customers have transactions with which beneficiaries
SELECT 'ECBT CHECK' as check_name,
       t.acct_num as customer_account,
       t.bene_acct_num as beneficiary_account,
       COUNT(*) as transaction_count
FROM txn t
JOIN acc_bene ab ON t.acct_num = ab.cust_acct_num AND t.bene_acct_num = ab.bene_acct_num
WHERE t.rrn IN ('9992000088', '9992000100', '9992000101')
GROUP BY t.acct_num, t.bene_acct_num
ORDER BY t.acct_num;

-- Check which customers have NO transactions with beneficiaries they've added (ECBNT candidates)
SELECT 'ECBNT CHECK' as check_name,
       ab.cust_acct_num as customer_account,
       ab.bene_acct_num as beneficiary_account,
       COUNT(t.id) as transaction_count
FROM acc_bene ab
LEFT JOIN txn t ON ab.cust_acct_num = t.acct_num AND ab.bene_acct_num = t.bene_acct_num
WHERE ab.cust_acct_num LIKE '77109%'
GROUP BY ab.cust_acct_num, ab.bene_acct_num
HAVING COUNT(t.id) = 0
ORDER BY ab.cust_acct_num;
