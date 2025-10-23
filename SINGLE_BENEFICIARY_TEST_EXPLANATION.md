# SINGLE BENEFICIARY MULTIPLE CUSTOMERS TEST SCENARIO

## Database Setup Summary

### Account Customer Data
- **2222222222222222** (Rajesh Kumar) - Primary victim account (payer_account_number)
- **3333333333333333** (Priya Sharma) - Customer with beneficiary 1111111111111111
- **4444444444444444** (Amit Patel) - Customer with beneficiary 1111111111111111  
- **5555555555555555** (Sneha Gupta) - Customer with beneficiary 1111111111111111
- **1111111111111111** (Fraud Beneficiary) - Single fraud beneficiary

### Beneficiary Relationships (acc_bene)
**ALL customers have the SAME beneficiary: 1111111111111111**

1. **2222222222222222** → **1111111111111111** ✅ (HAS transaction - ECBT)
2. **3333333333333333** → **1111111111111111** ✅ (HAS transaction - ECBT)
3. **4444444444444444** → **1111111111111111** ❌ (NO transaction - ECBNT)
4. **5555555555555555** → **1111111111111111** ❌ (NO transaction - ECBNT)

### Transactions (txn)
- **RRN 9600000001**: 2222222222222222 → 1111111111111111 (₹5,000)
- **RRN 9600000002**: 3333333333333333 → 1111111111111111 (₹7,500)

## Expected Case Creation Results

### 1. VM Case (Victim Match)
- **Case ID**: Will be created for account 2222222222222222
- **Reason**: payer_account_number matches customer account
- **Status**: New (will be closed when "Respond" is clicked)

### 2. PSA Case (Payee Suspect Account)
- **Case ID**: Will be created for account 2222222222222222
- **Reason**: payer_account_number has beneficiaries in acc_bene table
- **Status**: New

### 3. ECBT Cases (2 cases)
- **ECBT Case 1**: Customer 2222222222222222 + Beneficiary 1111111111111111
  - **Reason**: Transaction exists between them (RRN 9600000001)
- **ECBT Case 2**: Customer 3333333333333333 + Beneficiary 1111111111111111
  - **Reason**: Transaction exists between them (RRN 9600000002)

### 4. ECBNT Cases (2 cases)
- **ECBNT Case 1**: Customer 4444444444444444 + Beneficiary 1111111111111111
  - **Reason**: NO transaction exists between them
- **ECBNT Case 2**: Customer 5555555555555555 + Beneficiary 1111111111111111
  - **Reason**: NO transaction exists between them

## Total Expected Cases: 6
- **1 VM Case**
- **1 PSA Case** 
- **2 ECBT Cases**
- **2 ECBNT Cases**

## Test Payload
```json
{
  "acknowledgement_no": "SINGLEBENE001",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "Test Bank",
    "payer_bank": "State Bank of India",
    "payer_bank_code": 1234,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "2222222222222222",
    "state": "Maharashtra",
    "district": "Mumbai"
  },
  "incidents": [
    {
      "amount": "5000.00",
      "rrn": "9600000001",
      "transaction_date": "2025-10-21",
      "transaction_time": "10:00:00",
      "disputed_amount": "5000.00",
      "layer": 0
    },
    {
      "amount": "7500.00",
      "rrn": "9600000002",
      "transaction_date": "2025-10-21",
      "transaction_time": "11:00:00",
      "disputed_amount": "7500.00",
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
  -d @SINGLE_BENEFICIARY_TEST.json
```

**Expected Response:**
```json
{
  "meta": {
    "response_code": "00",
    "response_message": "Success"
  },
  "data": {
    "acknowledgement_no": "SINGLEBENE001",
    "job_id": "BANKS-xxxx-xxxx-xxxx-xxxx",
    "vm_case_id": 1803,
    "psa_case_id": 1804
  }
}
```

### Step 2: Check Database for All Cases
```sql
-- Check all created cases
SELECT case_id, case_type, acc_num, source_bene_accno, status 
FROM case_main 
WHERE source_ack_no LIKE '%SINGLEBENE001%' 
ORDER BY case_type, case_id;
```

### Step 3: Test Respond API
```bash
curl -X POST "http://localhost:8000/api/v2/banks/case-entry/SINGLEBENE001/respond" \
  -H "Content-Type: application/json" \
  -d '{"manually_selected_transactions": []}'
```

## Verification Queries

### Check VM Case
```sql
SELECT * FROM case_main WHERE case_type = 'VM' AND source_ack_no LIKE '%SINGLEBENE001%';
```

### Check PSA Case  
```sql
SELECT * FROM case_main WHERE case_type = 'PSA' AND source_ack_no LIKE '%SINGLEBENE001%';
```

### Check ECBT Cases
```sql
SELECT * FROM case_main WHERE case_type = 'ECBT' AND source_ack_no LIKE '%SINGLEBENE001%';
```

### Check ECBNT Cases
```sql
SELECT * FROM case_main WHERE case_type = 'ECBNT' AND source_ack_no LIKE '%SINGLEBENE001%';
```

### Count All Cases
```sql
SELECT case_type, COUNT(*) as count 
FROM case_main 
WHERE source_ack_no LIKE '%SINGLEBENE001%' 
GROUP BY case_type 
ORDER BY case_type;
```

## Expected Results Summary
- **VM**: 1 case (for 2222222222222222)
- **PSA**: 1 case (for 2222222222222222) 
- **ECBT**: 2 cases (2222222222222222 and 3333333333333333 with beneficiary 1111111111111111)
- **ECBNT**: 2 cases (4444444444444444 and 5555555555555555 with beneficiary 1111111111111111)
- **Total**: 6 cases created

## Key Differences from Previous Test
- **Single Beneficiary**: Only one beneficiary (1111111111111111) instead of multiple
- **Multiple Customers**: 4 customers all have the same beneficiary
- **Fewer Cases**: 6 total cases instead of 10
- **Simpler Logic**: Easier to understand the ECBT/ECBNT differentiation
