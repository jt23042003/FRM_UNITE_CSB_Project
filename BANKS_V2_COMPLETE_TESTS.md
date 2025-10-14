# 🧪 Banks V2 API - Complete Test Suite

## ⚡ Quick Start (Easiest Way to Test)

### **Single Command Test:**
```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry' -H 'Content-Type: application/json' -d '{"acknowledgement_no":"QUICKTEST01","sub_category":"UPI Related Frauds","instrument":{"requestor":"I4C Portal","payer_bank":"Test Bank","payer_bank_code":12345,"mode_of_payment":"UPI","payer_mobile_number":"9876543210","payer_account_number":"9579414475231007","state":"Maharashtra","district":"Mumbai","transaction_type":"P2P","wallet":"PhonePe"},"incidents":[{"amount":"100.00","rrn":"1000466753","transaction_date":"2025-08-01","transaction_time":"13:24:38","disputed_amount":"100.00","layer":0}]}' | jq '.data.vm_case_id'
```

**This returns:** `1735` (your VM case ID)

**Then:**
1. Open: `http://localhost:5173/operational-action/1735`
2. See two-section transaction layout
3. Click **"Respond & Close Case"** button
4. Case closes and detailed response sent!

---

## 🎯 All Test Scenarios in One Place

---

## **Test 1: ✅ VM Case Only (Simple)**
Creates only VM case, no other matches

**Command:**
```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry' \
-H 'Content-Type: application/json' \
-d '{
  "acknowledgement_no": "VMONLY001",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "9579414475231007",
    "state": "Maharashtra",
    "district": "Mumbai",
    "transaction_type": "P2P",
    "wallet": "PhonePe"
  },
  "incidents": [
    {"amount": "100.00", "rrn": "1000466753", "transaction_date": "2025-08-01", "transaction_time": "13:24:38", "disputed_amount": "100.00", "layer": 0}
  ]
}'
```

**Expected:** ✅ 1 VM case, 1 matched RRN

**Response:**
```json
{
  "meta": {"response_code": "00", "response_message": "Success"},
  "data": {
    "acknowledgement_no": "VMONLY001",
    "job_id": "BANKS-xxx",
    "vm_case_id": 1735,
    "psa_case_id": null
  },
  "transactions": [{"rrn_transaction_id": "1000466753", "status_code": "00", "response_message": "SUCCESS"}]
}
```

**Then send detailed response:**
```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry/VMONLY001/respond' \
-H 'Content-Type: application/json'
```

**Detailed Response:**
```json
{
  "meta": {"response_code": "00", "response_message": "Response sent successfully"},
  "data": {
    "acknowledgement_no": "VMONLY001",
    "vm_case_id": 1735,
    "psa_case_id": null,
    "status": "responded"
  },
  "transactions": [{
    "rrn_transaction_id": "1000466753",
    "payee_account_number": null,
    "amount": "100.00",
    "transaction_datetime": "2025-08-01 13:24:38",
    "status_code": "00",
    "response_message": "SUCCESS",
    "psa_case_id": null,
    "ecbt_case_id": null,
    "ecbnt_case_id": null
  }]
}
```

---

## **Test 2: ✅ VM + PSA Cases**
Payer is customer AND beneficiary is also customer

**Command:**
```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry' \
-H 'Content-Type: application/json' \
-d '{
  "acknowledgement_no": "VMPSA002",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "1870913315558618",
    "state": "Maharashtra",
    "district": "Mumbai",
    "transaction_type": "P2P",
    "wallet": "PhonePe"
  },
  "incidents": [
    {"amount": "250.75", "rrn": "1000464468", "transaction_date": "2025-01-15", "transaction_time": "15:04:04", "disputed_amount": "250.75", "layer": 0},
    {"amount": "1500.00", "rrn": "1000464471", "transaction_date": "2025-01-15", "transaction_time": "16:30:00", "disputed_amount": "1500.00", "layer": 0}
  ]
}'
```

**Expected:** 
- ✅ 1 VM case (payer 1870913315558618 is customer)
- ✅ 1 PSA case (beneficiary 1030856350540889 is customer CUST100579)

---

## **Test 3: ✅ VM + PSA + ECBT Cases**
Complex scenario: VM + PSA + beneficiary in acc_bene WITH transactions

**Command:**
```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry' \
-H 'Content-Type: application/json' \
-d '{
  "acknowledgement_no": "VMPSAECBT003",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "1870913315558618",
    "state": "Maharashtra",
    "district": "Mumbai",
    "transaction_type": "P2P",
    "wallet": "PhonePe"
  },
  "incidents": [
    {"amount": "250.75", "rrn": "1000464468", "transaction_date": "2025-01-15", "transaction_time": "15:04:04", "disputed_amount": "250.75", "layer": 0},
    {"amount": "9999.99", "rrn": "1000464489", "transaction_date": "2025-01-16", "transaction_time": "12:00:00", "disputed_amount": "9999.99", "layer": 0}
  ]
}'
```

**Expected:**
- ✅ 1 VM case (payer 1870913315558618 is customer)
- ✅ 1 PSA case (RRN 1000464468: bene 1030856350540889 is customer)
- ✅ 1 ECBT case (RRN 1000464489: bene 72537282762746 in acc_bene + has transactions)

**Database Setup Verified:**
```sql
-- ECBT relationship exists with transaction
cust_acct_num: 6108799800821363
bene_acct_num: 72537282762746
txn_count: 1 (RRN 1000464489)
```

---

## **Test 4: ✅ VM + PSA + ECBNT Cases**
Complex scenario: VM + PSA + beneficiary in acc_bene WITHOUT transactions

**Command:**
```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry' \
-H 'Content-Type: application/json' \
-d '{
  "acknowledgement_no": "VMPSAECBNT004",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "1870913315558618",
    "state": "Maharashtra",
    "district": "Mumbai",
    "transaction_type": "P2P",
    "wallet": "PhonePe"
  },
  "incidents": [
    {"amount": "250.75", "rrn": "1000464468", "transaction_date": "2025-01-15", "transaction_time": "15:04:04", "disputed_amount": "250.75", "layer": 0},
    {"amount": "15000.00", "rrn": "1000999001", "transaction_date": "2025-01-16", "transaction_time": "10:30:00", "disputed_amount": "15000.00", "layer": 0}
  ]
}'
```

**Expected:**
- ✅ 1 VM case (payer 1870913315558618 is customer)
- ✅ 1 PSA case (RRN 1000464468: bene 1030856350540889 is customer)
- ✅ 1 ECBNT case (RRN 1000999001: bene 9999888877776666 in acc_bene but NO transactions from customer 1870913315558618)

**Database Setup:**
```sql
-- ECBNT relationship exists WITHOUT transaction
cust_acct_num: 1870913315558618
bene_acct_num: 9999888877776666
txn_count: 0 (beneficiary saved but never used)
```

---

## **Test 5: ✅ Mixed Validation Statuses**
Shows valid, not found, and invalid RRNs

**Command:**
```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry' \
-H 'Content-Type: application/json' \
-d '{
  "acknowledgement_no": "MIXED005",
  "sub_category": "Internet Banking Related Fraud",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,
    "mode_of_payment": "NEFT",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "7023612539672909",
    "state": "Karnataka",
    "district": "Bangalore",
    "transaction_type": "P2A",
    "wallet": null
  },
  "incidents": [
    {"amount": "5000.00", "rrn": "1000464994", "transaction_date": "2025-01-20", "transaction_time": "10:00:00", "disputed_amount": "5000.00", "layer": 0},
    {"amount": "10000.00", "rrn": "9999999999", "transaction_date": "2025-01-20", "transaction_time": "11:00:00", "disputed_amount": "10000.00", "layer": 1},
    {"amount": "2000.00", "rrn": "8888888888", "transaction_date": "2025-01-20", "transaction_time": "12:00:00", "disputed_amount": "2000.00", "layer": 2}
  ]
}'
```

**Expected:**
- ✅ 1 VM case
- ✅ RRN 1000464994: ✓ Matched
- ❌ RRN 9999999999: ✗ Not Found
- ❌ RRN 8888888888: ✗ Not Found

---

## **Test 6: ❌ No VM Match Error**
Should fail - no customer match

**Command:**
```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry' \
-H 'Content-Type: application/json' \
-d '{
  "acknowledgement_no": "NOVM006",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "External Bank",
    "payer_bank_code": 99999,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9999999999",
    "payer_account_number": "9999999999999999",
    "state": "Gujarat",
    "district": "Ahmedabad",
    "transaction_type": "P2P",
    "wallet": "Paytm"
  },
  "incidents": [
    {"amount": "5000.00", "rrn": "1000464468", "transaction_date": "2025-01-30", "transaction_time": "12:00:00", "disputed_amount": "5000.00", "layer": 0}
  ]
}'
```

**Expected:**
- ❌ Error code: 20
- ❌ NO cases created

---

## **Test 7: 🎯 ULTIMATE TEST - All Case Types**
Creates VM + PSA + ECBT + ECBNT in ONE payload!

**Command:**
```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry' \
-H 'Content-Type: application/json' \
-d '{
  "acknowledgement_no": "ULTIMATE007",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "1870913315558618",
    "state": "Maharashtra",
    "district": "Mumbai",
    "transaction_type": "P2P",
    "wallet": "PhonePe"
  },
  "incidents": [
    {"amount": "250.75", "rrn": "1000464468", "transaction_date": "2025-01-15", "transaction_time": "15:04:04", "disputed_amount": "250.75", "layer": 0},
    {"amount": "9999.99", "rrn": "1000464489", "transaction_date": "2025-01-16", "transaction_time": "12:00:00", "disputed_amount": "9999.99", "layer": 0},
    {"amount": "15000.00", "rrn": "1000999001", "transaction_date": "2025-01-17", "transaction_time": "10:30:00", "disputed_amount": "15000.00", "layer": 0},
    {"amount": "5000.00", "rrn": "9999999999", "transaction_date": "2025-01-18", "transaction_time": "14:00:00", "disputed_amount": "5000.00", "layer": 1}
  ]
}'
```

**Expected Result - 4 CASES CREATED:**
1. ✅ **VM Case** (payer 1870913315558618 is customer CUST111915)
2. ✅ **PSA Case** (RRN 1000464468: beneficiary 1030856350540889 is customer CUST100579)
3. ✅ **ECBT Case** (RRN 1000464489: beneficiary 72537282762746 in acc_bene + has transactions)
4. ✅ **ECBNT Case** (RRN 1000999001: beneficiary 9999888877776666 in acc_bene but NO transactions from payer's customer account)

**Validation Results:**
- ✓ RRN 1000464468: Matched
- ✓ RRN 1000464489: Matched
- ✓ RRN 1000999001: Matched
- ✗ RRN 9999999999: Not Found

**Frontend Verification:**
- Open VM case: Shows 4 incidents (LEFT) vs 4 validation results (RIGHT)
- Open PSA case: Shows matched RRNs only
- Open ECBT case: Shows actual transactions from txn table
- Open ECBNT case: Shows info banner (no transactions)

---

## 📊 Quick Summary Table

| Test | VM | PSA | ECBT | ECBNT | Error RRNs |
|------|:--:|:---:|:----:|:-----:|:----------:|
| Test 1 | ✅ | ❌ | ❌ | ❌ | 0 |
| Test 2 | ✅ | ✅ | ❌ | ❌ | 0 |
| Test 3 | ✅ | ✅ | ✅ | ❌ | 0 |
| Test 4 | ✅ | ✅ | ❌ | ✅ | 0 |
| Test 5 | ✅ | ❌ | ❌ | ❌ | 2 |
| Test 6 | ❌ | ❌ | ❌ | ❌ | Error 20 |
| Test 7 | ✅ | ✅ | ✅ | ✅ | 1 |

---

## 📊 Two-Step Testing Process

### **Testing Flow:**

1. **POST case-entry** → Creates cases, returns case IDs
2. **Open VM case in frontend** → Review validation results
3. **Click "Respond" button** → Marks case closed, returns detailed response
4. **Verify closed** → Case should redirect to case list

### **Manual Testing Both Steps:**

```bash
# Step 1: Create case
RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v2/banks/case-entry' \
-H 'Content-Type: application/json' \
-d '{"acknowledgement_no":"VMONLY001","sub_category":"UPI Related Frauds","instrument":{"requestor":"I4C Portal","payer_bank":"Test Bank","payer_bank_code":12345,"mode_of_payment":"UPI","payer_mobile_number":"9876543210","payer_account_number":"9579414475231007","state":"Maharashtra","district":"Mumbai","transaction_type":"P2P","wallet":"PhonePe"},"incidents":[{"amount":"100.00","rrn":"1000466753","transaction_date":"2025-08-01","transaction_time":"13:24:38","disputed_amount":"100.00","layer":0}]}')

echo "Initial Response:"
echo $RESPONSE | jq

# Extract VM case ID
VM_CASE_ID=$(echo $RESPONSE | jq -r '.data.vm_case_id')
echo "VM Case ID: $VM_CASE_ID"

# Open in browser: http://localhost:5173/operational-action/$VM_CASE_ID

# Step 2: Send detailed response (after user reviews)
echo "\n--- Waiting 5 seconds for you to review in frontend ---"
sleep 5

curl -X POST "http://localhost:8000/api/v2/banks/case-entry/VMONLY001/respond" \
-H 'Content-Type: application/json' | jq

echo "\nVM Case should now be Closed!"
```

---

## 🔍 Verify Cases Created

```sql
-- Get all cases from test runs
SELECT 
  case_id, 
  source_ack_no, 
  case_type, 
  status,
  created_at
FROM case_main 
WHERE source_ack_no LIKE '%ULTIMATE007%'
   OR source_ack_no LIKE '%VMPSA%'
   OR source_ack_no LIKE '%VMONLY%'
ORDER BY created_at DESC;

-- Check validation results
SELECT 
  ivr.case_id,
  cm.source_ack_no,
  ivr.rrn,
  ivr.validation_status,
  ivr.validation_message
FROM incident_validation_results ivr
JOIN case_main cm ON ivr.case_id = cm.case_id
WHERE cm.source_ack_no LIKE '%007%'
ORDER BY ivr.case_id, ivr.rrn;

-- Verify ECBT transactions
SELECT * FROM incident_validation_results 
WHERE case_id IN (
  SELECT case_id FROM case_main WHERE source_ack_no LIKE '%ECBT%'
)
ORDER BY created_at DESC LIMIT 5;
```

---

## 🎯 Test Data Setup (Already Done)

```sql
-- ECBT: Beneficiary with transactions
cust_acct_num: 6108799800821363
bene_acct_num: 72537282762746
Transactions: 1 (RRN 1000464489)
Status: ✅ Ready for ECBT testing

-- ECBNT: Beneficiary without transactions  
cust_acct_num: 1870913315558618
bene_acct_num: 9999888877776666
Transactions: 0 (beneficiary saved but never used)
Status: ✅ Ready for ECBNT testing
```

---

## 🚀 Quick Test - Run Test 7 (Ultimate Test)

This ONE command creates ALL 4 case types:

```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry' -H 'Content-Type: application/json' -d '{"acknowledgement_no":"ULTIMATE007","sub_category":"UPI Related Frauds","instrument":{"requestor":"I4C Portal","payer_bank":"Test Bank","payer_bank_code":12345,"mode_of_payment":"UPI","payer_mobile_number":"9876543210","payer_account_number":"1870913315558618","state":"Maharashtra","district":"Mumbai","transaction_type":"P2P","wallet":"PhonePe"},"incidents":[{"amount":"250.75","rrn":"1000464468","transaction_date":"2025-01-15","transaction_time":"15:04:04","disputed_amount":"250.75","layer":0},{"amount":"9999.99","rrn":"1000464489","transaction_date":"2025-01-16","transaction_time":"12:00:00","disputed_amount":"9999.99","layer":0},{"amount":"15000.00","rrn":"1000999001","transaction_date":"2025-01-17","transaction_time":"10:30:00","disputed_amount":"15000.00","layer":0},{"amount":"5000.00","rrn":"9999999999","transaction_date":"2025-01-18","transaction_time":"14:00:00","disputed_amount":"5000.00","layer":1}]}' | jq
```

**Look for in response:**
```json
{
  "data": {
    "vm_case_id": 1234,
    "psa_case_id": 5678
  },
  "transactions": [
    {"rrn_transaction_id": "1000464468", "status_code": "00", "psa_case_id": 5678},
    {"rrn_transaction_id": "1000464489", "status_code": "00", "ecbt_case_id": 9012},
    {"rrn_transaction_id": "1000999001", "status_code": "00", "ecbnt_case_id": 3456},
    {"rrn_transaction_id": "9999999999", "status_code": "01"}
  ]
}
```

**Then open cases:**
- VM: `http://localhost:5173/operational-action/1234`
- PSA: `http://localhost:5173/psa-action/5678`
- ECBT: `http://localhost:5173/ecbt-action/9012`
- ECBNT: `http://localhost:5173/ecbnt-action/3456`

---

## 🎨 Expected Frontend Display Per Case Type:

### **VM Case (operational-action):**
```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│ Transaction Details from I4C         │ Matched Bank Transactions            │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ RRN          Date        Amount      │ RRN          Status      Bene Acct   │
│ 1000464468   15-01-25   ₹250.75     │ 1000464468   ✓ Matched   1030856...  │
│ 1000464489   16-01-25   ₹9,999.99   │ 1000464489   ✓ Matched   725372...   │
│ 1000999001   17-01-25   ₹15,000.00  │ 1000999001   ✓ Matched   999988...   │
│ 9999999999   18-01-25   ₹5,000.00   │ 9999999999   ✗ Not Found  -          │
└──────────────────────────────────────┴──────────────────────────────────────┘

Summary: Total: 4 | ✓ Matched: 3 | ✗ Errors: 1
```

### **PSA Case (psa-action):**
Same two-section layout, shows only matched RRNs

### **ECBT Case (ecbt-action):**
Shows ALL transactions from txn table between customer 6108799800821363 and beneficiary 72537282762746

### **ECBNT Case (ecbnt-action):**
Shows info banner: "No transactions exist between customer and beneficiary"

---

## 🔧 Cleanup After Testing

```sql
-- Delete test cases
DELETE FROM case_main WHERE source_ack_no LIKE '%ULTIMATE%' OR source_ack_no LIKE '%VMPSA%' OR source_ack_no LIKE '%VMONLY%' OR source_ack_no LIKE '%MIXED%';

-- Delete test data
DELETE FROM case_main_v2 WHERE acknowledgement_no LIKE 'ULTIMATE%' OR acknowledgement_no LIKE 'VMPSA%' OR acknowledgement_no LIKE 'VMONLY%' OR acknowledgement_no LIKE 'MIXED%';

-- Remove test beneficiary
DELETE FROM acc_bene WHERE cust_acct_num = '1870913315558618' AND bene_acct_num = '9999888877776666';

-- Remove test transaction
DELETE FROM txn WHERE rrn = '1000999001';
```

---

## 🎉 Ready to Test!

**Recommended Testing Order:**
1. Start with Test 1 (simple VM only)
2. Then Test 2 (VM + PSA)
3. Then Test 7 (Ultimate - all case types)
4. Finally Test 6 (error scenario)

Each curl command is **ready to copy-paste** and run! 🚀

