# ECBT and ECBNT Testing Guide - Banks V2 API

## Prerequisites

Before testing, ensure you have the following data in your database:

### 1. Check Existing Transaction Data
```sql
-- Find a transaction with RRN
SELECT rrn, acct_num, bene_acct_num, amount, txn_date, txn_time 
FROM txn 
WHERE rrn IS NOT NULL 
LIMIT 5;
```

### 2. Check Account-Beneficiary Relationships
```sql
-- Check acc_bene table
SELECT ab.cust_acct_num, ab.bene_acct_num, ac.cust_id
FROM acc_bene ab
JOIN account_customer ac ON ab.cust_acct_num = ac.acc_num
LIMIT 5;
```

### 3. Check Customer and Account Data
```sql
-- Get customer details
SELECT c.cust_id, c.fname, c.mobile, ac.acc_num
FROM customer c
JOIN account_customer ac ON c.cust_id = ac.cust_id
LIMIT 5;
```

---

## Test Scenario 1: ECBT Case (Existing Customer Beneficiary WITH Transactions)

### Setup Required:
1. Customer Account: `1234567890` (has cust_id, exists in account_customer)
2. Beneficiary Account: `7000723456789999` (fraudulent account)
3. In `acc_bene` table: Record showing customer `1234567890` has added beneficiary `7000723456789999`
4. In `txn` table: At least one transaction from `1234567890` to `7000723456789999`

### Setup SQL:
```sql
-- 1. Ensure customer exists (use your actual customer data)
-- Check: SELECT * FROM customer WHERE cust_id = 'CUST001';

-- 2. Ensure account_customer relationship exists
INSERT INTO account_customer (cust_id, acc_num) 
VALUES ('CUST001', '1234567890') 
ON CONFLICT DO NOTHING;

-- 3. Add beneficiary relationship in acc_bene
INSERT INTO acc_bene (cust_acct_num, bene_acct_num) 
VALUES ('1234567890', '7000723456789999') 
ON CONFLICT DO NOTHING;

-- 4. Insert a transaction between customer and beneficiary
INSERT INTO txn (
    acct_num, bene_acct_num, amount, txn_date, txn_time, 
    rrn, channel, descr, txn_type, currency
) VALUES (
    '1234567890',           -- Customer account (payer)
    '7000723456789999',     -- Beneficiary account (fraudster)
    5000.00,                -- Amount
    '2024-01-15',           -- Transaction date
    '14:30:00',             -- Transaction time
    '1234567890123',        -- RRN (use this in payload)
    'UPI',                  -- Channel
    'Payment to merchant',  -- Description
    'DEBIT',                -- Transaction type
    'INR'                   -- Currency
) ON CONFLICT DO NOTHING;
```

### API Payload for ECBT:
```json
{
  "acknowledgement_no": "ECBTTEST001",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "Police Station XYZ",
    "payer_bank": "State Bank of India",
    "payer_bank_code": 12345,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "9999888877776666",
    "state": "Maharashtra",
    "district": "Mumbai",
    "transaction_type": "UPI",
    "wallet": "GooglePay"
  },
  "incidents": [
    {
      "amount": "5000.00",
      "rrn": "1234567890123",
      "transaction_date": "2024-01-15",
      "transaction_time": "14:30:00",
      "disputed_amount": "5000.00",
      "layer": 0
    }
  ]
}
```

### Expected Result:
- ✅ VM case created
- ✅ **ECBT case created** (because `1234567890` has transactions with `7000723456789999`)
- The ECBT case should show:
  - Potential Victim Account: `1234567890` (customer's account)
  - Beneficiary Account in transactions: `7000723456789999`

---

## Test Scenario 2: ECBNT Case (Existing Customer Beneficiary WITHOUT Transactions)

### Setup Required:
1. Customer Account: `5555666677778888` (has cust_id, exists in account_customer)
2. Beneficiary Account: `9000111122223333` (fraudulent account)
3. In `acc_bene` table: Record showing customer `5555666677778888` has added beneficiary `9000111122223333`
4. In `txn` table: NO transactions from `5555666677778888` to `9000111122223333`
5. In `txn` table: A different transaction with a different RRN (for the VM case)

### Setup SQL:
```sql
-- 1. Ensure customer exists
-- Check: SELECT * FROM customer WHERE cust_id = 'CUST002';

-- 2. Ensure account_customer relationship exists
INSERT INTO account_customer (cust_id, acc_num) 
VALUES ('CUST002', '5555666677778888') 
ON CONFLICT DO NOTHING;

-- 3. Add beneficiary relationship in acc_bene (but NO transactions)
INSERT INTO acc_bene (cust_acct_num, bene_acct_num) 
VALUES ('5555666677778888', '9000111122223333') 
ON CONFLICT DO NOTHING;

-- 4. Insert a transaction with DIFFERENT beneficiary (for VM case)
-- This transaction is from victim's complaint, NOT to the acc_bene beneficiary
INSERT INTO txn (
    acct_num, bene_acct_num, amount, txn_date, txn_time, 
    rrn, channel, descr, txn_type, currency
) VALUES (
    '9999888877776666',     -- Victim's account (from complaint)
    '9000111122223333',     -- Beneficiary account (fraudster)
    3000.00,                -- Amount
    '2024-01-20',           -- Transaction date
    '10:15:00',             -- Transaction time
    '9876543210987',        -- RRN (use this in payload)
    'IMPS',                 -- Channel
    'Online transfer',      -- Description
    'DEBIT',                -- Transaction type
    'INR'                   -- Currency
) ON CONFLICT DO NOTHING;

-- IMPORTANT: Ensure NO transactions exist between 5555666677778888 and 9000111122223333
-- Check: SELECT * FROM txn WHERE acct_num = '5555666677778888' AND bene_acct_num = '9000111122223333';
-- Should return 0 rows
```

### API Payload for ECBNT:
```json
{
  "acknowledgement_no": "ECBNTTEST001",
  "sub_category": "Internet Banking Related Fraud",
  "instrument": {
    "requestor": "Cyber Crime Cell",
    "payer_bank": "HDFC Bank",
    "payer_bank_code": 54321,
    "mode_of_payment": "IMPS",
    "payer_mobile_number": "8765432109",
    "payer_account_number": "9999888877776666",
    "state": "Karnataka",
    "district": "Bangalore",
    "transaction_type": "IMPS",
    "wallet": null
  },
  "incidents": [
    {
      "amount": "3000.00",
      "rrn": "9876543210987",
      "transaction_date": "2024-01-20",
      "transaction_time": "10:15:00",
      "disputed_amount": "3000.00",
      "layer": 0
    }
  ]
}
```

### Expected Result:
- ✅ VM case created
- ✅ **ECBNT case created** (because `5555666677778888` has beneficiary `9000111122223333` saved but NO transactions)
- The ECBNT case should show:
  - Potential Victim Account: `5555666677778888` (customer's account)
  - No transaction table (because it's ECBNT)

---

## Test Scenario 3: Both ECBT and ECBNT in Single Payload

You can also create a payload with multiple incidents where some trigger ECBT and others trigger ECBNT.

### API Payload (Combined):
```json
{
  "acknowledgement_no": "COMBINED001",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "Police HQ",
    "payer_bank": "ICICI Bank",
    "payer_bank_code": 11111,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9123456789",
    "payer_account_number": "1111222233334444",
    "state": "Delhi",
    "district": "New Delhi",
    "transaction_type": "UPI",
    "wallet": "PhonePe"
  },
  "incidents": [
    {
      "amount": "5000.00",
      "rrn": "1234567890123",
      "transaction_date": "2024-01-15",
      "transaction_time": "14:30:00",
      "disputed_amount": "5000.00",
      "layer": 0
    },
    {
      "amount": "3000.00",
      "rrn": "9876543210987",
      "transaction_date": "2024-01-20",
      "transaction_time": "10:15:00",
      "disputed_amount": "3000.00",
      "layer": 1
    }
  ]
}
```

---

## API Endpoint

**POST** `/api/v2/banks/case-entry`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <your_jwt_token>
```

---

## Testing Steps

1. **Setup Database** - Run the setup SQL for the scenario you want to test
2. **Get JWT Token** - Login and get authentication token
3. **Send API Request** - Use Postman or curl to send the payload
4. **Check Response** - Verify case IDs are returned
5. **Verify in Frontend** - Go to case list and open the ECBT/ECBNT cases
6. **Check Customer Account** - Verify the "Bank Account" field shows the CUSTOMER account, not beneficiary

---

## Verification Queries

### Check Created Cases:
```sql
-- Check all cases created
SELECT case_id, case_type, source_ack_no, cust_id, acc_num, source_bene_accno, status
FROM case_main
WHERE source_ack_no LIKE 'ECBTTEST%' OR source_ack_no LIKE 'ECBNTTEST%'
ORDER BY creation_date DESC;
```

### Verify ECBT Case Details:
```sql
-- For ECBT case - should show customer account in acc_num
SELECT 
    cm.case_id,
    cm.case_type,
    cm.acc_num as customer_account,
    cm.source_bene_accno as beneficiary_account,
    c.fname || ' ' || c.lname as customer_name,
    c.mobile
FROM case_main cm
LEFT JOIN customer c ON cm.cust_id = c.cust_id
WHERE cm.case_type = 'ECBT'
ORDER BY cm.creation_date DESC
LIMIT 5;
```

### Check Transactions Retrieved:
```sql
-- Verify transactions shown in ECBT case
SELECT acct_num, bene_acct_num, amount, txn_date, rrn, channel
FROM txn
WHERE acct_num = '1234567890' 
  AND bene_acct_num = '7000723456789999';
```

---

## Expected Behavior After Fix

### Before Fix:
- ❌ ECBT Potential Victim → Bank Account: `7000723456789999` (WRONG - shows beneficiary)

### After Fix:
- ✅ ECBT Potential Victim → Bank Account: `1234567890` (CORRECT - shows customer)
- ✅ ECBT Transaction Table → Customer Account: `1234567890`
- ✅ ECBT Transaction Table → Beneficiary Account: `7000723456789999`
- ✅ ECBNT Potential Victim → Bank Account: `5555666677778888` (CORRECT - shows customer)

---

## Troubleshooting

### No ECBT/ECBNT Cases Created?

1. **Check if RRN exists in txn table**
   ```sql
   SELECT * FROM txn WHERE rrn = 'YOUR_RRN';
   ```

2. **Check if beneficiary is in acc_bene**
   ```sql
   SELECT * FROM acc_bene WHERE bene_acct_num = 'BENE_ACCOUNT';
   ```

3. **Check if customer account is linked**
   ```sql
   SELECT * FROM account_customer WHERE acc_num = 'CUSTOMER_ACCOUNT';
   ```

4. **Check backend logs**
   ```bash
   tail -f backend/backend.log | grep -i "ecb"
   ```

### Cases Created But Wrong Account Shown?

- This was the original bug - should be fixed now
- Verify you're running the updated backend code
- Check `case_main.acc_num` in database - should show customer account

---

## Quick Test Command (curl)

```bash
# Replace with your actual JWT token
TOKEN="your_jwt_token_here"

curl -X POST "http://localhost:8000/api/v2/banks/case-entry" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "acknowledgement_no": "ECBTTEST001",
    "sub_category": "UPI Related Frauds",
    "instrument": {
      "requestor": "Police Station XYZ",
      "payer_bank": "State Bank of India",
      "payer_bank_code": 12345,
      "mode_of_payment": "UPI",
      "payer_mobile_number": "9876543210",
      "payer_account_number": "9999888877776666",
      "state": "Maharashtra",
      "district": "Mumbai",
      "transaction_type": "UPI",
      "wallet": "GooglePay"
    },
    "incidents": [{
      "amount": "5000.00",
      "rrn": "1234567890123",
      "transaction_date": "2024-01-15",
      "transaction_time": "14:30:00",
      "disputed_amount": "5000.00",
      "layer": 0
    }]
  }'
```

