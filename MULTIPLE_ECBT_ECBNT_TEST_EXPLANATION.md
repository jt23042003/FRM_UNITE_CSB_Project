# MULTIPLE ECBT/ECBNT TEST SCENARIO

## Database Setup Summary

### Account Customer Data
- **1111111111111111** (Rajesh Kumar) - Primary victim account (payer_account_number)
- **2222222222222222** (Priya Sharma) - Customer with beneficiary 9999999999999999
- **3333333333333333** (Amit Patel) - Customer with beneficiary 9999999999999999  
- **4444444444444444** (Sneha Gupta) - Customer with beneficiary 8888888888888888
- **5555555555555555** (Vikram Singh) - Customer with beneficiary 8888888888888888
- **6666666666666666** (Anita Reddy) - Customer with beneficiary 7777777777777777
- **9999999999999999** (Fraud Beneficiary 1)
- **8888888888888888** (Fraud Beneficiary 2)  
- **7777777777777777** (Fraud Beneficiary 3)

### Beneficiary Relationships (acc_bene)
1. **1111111111111111** → **9999999999999999** ✅ (HAS transaction - ECBT)
2. **2222222222222222** → **9999999999999999** ❌ (NO transaction - ECBNT)
3. **3333333333333333** → **9999999999999999** ❌ (NO transaction - ECBNT)
4. **1111111111111111** → **8888888888888888** ✅ (HAS transaction - ECBT)
5. **4444444444444444** → **8888888888888888** ❌ (NO transaction - ECBNT)
6. **5555555555555555** → **8888888888888888** ❌ (NO transaction - ECBNT)
7. **1111111111111111** → **7777777777777777** ✅ (HAS transaction - ECBT)
8. **6666666666666666** → **7777777777777777** ❌ (NO transaction - ECBNT)

### Transactions (txn)
- **RRN 9000000006**: 1111111111111111 → 9999999999999999 (₹5,000)
- **RRN 9000000007**: 1111111111111111 → 8888888888888888 (₹7,500)  
- **RRN 9000000008**: 1111111111111111 → 7777777777777777 (₹3,000)

## Expected Case Creation Results

### 1. VM Case (Victim Match)
- **Case ID**: Will be created for account 1111111111111111
- **Reason**: payer_account_number matches customer account
- **Status**: New (will be closed when "Respond" is clicked)

### 2. PSA Case (Payee Suspect Account)
- **Case ID**: Will be created for account 1111111111111111
- **Reason**: payer_account_number has beneficiaries in acc_bene table
- **Status**: New

### 3. ECBT Cases (3 cases)
- **ECBT Case 1**: Customer 1111111111111111 + Beneficiary 9999999999999999
  - **Reason**: Transaction exists between them (RRN 9000000006)
- **ECBT Case 2**: Customer 1111111111111111 + Beneficiary 8888888888888888  
  - **Reason**: Transaction exists between them (RRN 9000000007)
- **ECBT Case 3**: Customer 1111111111111111 + Beneficiary 7777777777777777
  - **Reason**: Transaction exists between them (RRN 9000000008)

### 4. ECBNT Cases (5 cases)
- **ECBNT Case 1**: Customer 2222222222222222 + Beneficiary 9999999999999999
  - **Reason**: NO transaction exists between them
- **ECBNT Case 2**: Customer 3333333333333333 + Beneficiary 9999999999999999
  - **Reason**: NO transaction exists between them  
- **ECBNT Case 3**: Customer 4444444444444444 + Beneficiary 8888888888888888
  - **Reason**: NO transaction exists between them
- **ECBNT Case 4**: Customer 5555555555555555 + Beneficiary 8888888888888888
  - **Reason**: NO transaction exists between them
- **ECBNT Case 5**: Customer 6666666666666666 + Beneficiary 7777777777777777
  - **Reason**: NO transaction exists between them

## Total Expected Cases: 10
- **1 VM Case**
- **1 PSA Case** 
- **3 ECBT Cases**
- **5 ECBNT Cases**

## Test Payload
```json
{
  "acknowledgement_no": "MULTIECBT002",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "Test Bank",
    "payer_bank": "State Bank of India",
    "payer_bank_code": 1234,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "1111111111111111",
    "state": "Maharashtra",
    "district": "Mumbai"
  },
  "incidents": [
    {
      "amount": "5000.00",
      "rrn": "9000000006",
      "transaction_date": "2025-10-20",
      "transaction_time": "10:00:00",
      "disputed_amount": "5000.00",
      "layer": 0
    },
    {
      "amount": "7500.00",
      "rrn": "9000000007",
      "transaction_date": "2025-10-20",
      "transaction_time": "11:00:00",
      "disputed_amount": "7500.00",
      "layer": 0
    },
    {
      "amount": "3000.00",
      "rrn": "9000000008",
      "transaction_date": "2025-10-20",
      "transaction_time": "12:00:00",
      "disputed_amount": "3000.00",
      "layer": 0
    }
  ]
}
```

## How to Test

### Step 1: Send Initial Payload
```bash
curl -X POST "http://localhost:8000/api/v2/banks/case-entry" \
  -H "Content-Type: application/json" \
  -d @MULTIPLE_ECBT_ECBNT_TEST.json
```

**Expected Response:**
```json
{
  "meta": {
    "response_code": "00",
    "response_message": "Success"
  },
  "data": {
    "acknowledgement_no": "MULTIECBT001",
    "job_id": "BANKS-xxxx-xxxx-xxxx-xxxx",
    "vm_case_id": 1736,
    "psa_case_id": 1737
  }
}
```

### Step 2: Check Database for All Cases
```sql
-- Check all created cases
SELECT case_id, case_type, acc_num, source_bene_accno, status, created_at 
FROM case_main 
WHERE source_ack_no LIKE '%MULTIECBT002%' 
ORDER BY case_type, case_id;
```

### Step 3: Test Respond API
```bash
curl -X POST "http://localhost:8000/api/v2/banks/case-entry/MULTIECBT001/respond" \
  -H "Content-Type: application/json" \
  -d '{"manually_selected_transactions": []}'
```

## Verification Queries

### Check VM Case
```sql
SELECT * FROM case_main WHERE case_type = 'VM' AND source_ack_no LIKE '%MULTIECBT001%';
```

### Check PSA Case  
```sql
SELECT * FROM case_main WHERE case_type = 'PSA' AND source_ack_no LIKE '%MULTIECBT001%';
```

### Check ECBT Cases
```sql
SELECT * FROM case_main WHERE case_type = 'ECBT' AND source_ack_no LIKE '%MULTIECBT001%';
```

### Check ECBNT Cases
```sql
SELECT * FROM case_main WHERE case_type = 'ECBNT' AND source_ack_no LIKE '%MULTIECBT001%';
```

### Count All Cases
```sql
SELECT case_type, COUNT(*) as count 
FROM case_main 
WHERE source_ack_no LIKE '%MULTIECBT002%' 
GROUP BY case_type 
ORDER BY case_type;
```

## Expected Results Summary
- **VM**: 1 case (for 1111111111111111)
- **PSA**: 1 case (for 1111111111111111) 
- **ECBT**: 3 cases (1111111111111111 with each beneficiary)
- **ECBNT**: 5 cases (other customers with beneficiaries but no transactions)
- **Total**: 10 cases created
