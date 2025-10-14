# 🧪 Complete Test Scenarios - Manual Matching Feature

## ✅ Test Data Created (17 Transactions)

All test data is ready in your database! Just copy-paste the payloads below into Postman.

---

## 📋 **SCENARIO 1: Perfect Match (All RRNs Valid)** ✅✅✅

**Purpose:** All RRNs match automatically, NO manual review needed

**Postman:**
```
POST http://localhost:8000/api/v2/banks/case-entry
Content-Type: application/json

Body:
{
  "acknowledgement_no": "PERFECT001",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "7023612539672909",
    "state": "Maharashtra",
    "district": "Mumbai",
    "transaction_type": "P2P",
    "wallet": "PhonePe"
  },
  "incidents": [
    {"amount": "5000.00", "rrn": "3000111111", "transaction_date": "2025-10-13", "transaction_time": "09:00:00", "disputed_amount": "5000.00", "layer": 0},
    {"amount": "7500.00", "rrn": "3000222222", "transaction_date": "2025-10-13", "transaction_time": "10:30:00", "disputed_amount": "7500.00", "layer": 0},
    {"amount": "2000.00", "rrn": "3000333333", "transaction_date": "2025-10-13", "transaction_time": "14:15:00", "disputed_amount": "2000.00", "layer": 0}
  ]
}
```

**Expected:**
- ✅ All 3 RRNs matched (status_code: "00")
- ✅ Summary: Matched: 3, Errors: 0
- ❌ NO manual review section (all matched!)

---

## 📋 **SCENARIO 2: Mixed Valid/Invalid** ✅❌❌❌

**Purpose:** 1 valid, 3 invalid → Manual review section appears with 5 transactions to choose from

**Postman:**
```
POST http://localhost:8000/api/v2/banks/case-entry
Content-Type: application/json

Body:
{
  "acknowledgement_no": "MIXED002",
  "sub_category": "Internet Banking Related Fraud",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,
    "mode_of_payment": "NEFT",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "5478251911670246",
    "state": "Karnataka",
    "district": "Bangalore",
    "transaction_type": "P2A",
    "wallet": null
  },
  "incidents": [
    {"amount": "1200.50", "rrn": "4000111111", "transaction_date": "2025-10-14", "transaction_time": "08:30:00", "disputed_amount": "1200.50", "layer": 0},
    {"amount": "999.99", "rrn": "9999999991", "transaction_date": "2025-10-14", "transaction_time": "10:00:00", "disputed_amount": "999.99", "layer": 0},
    {"amount": "850.75", "rrn": "9999999992", "transaction_date": "2025-10-14", "transaction_time": "11:45:00", "disputed_amount": "850.75", "layer": 0},
    {"amount": "450.25", "rrn": "9999999993", "transaction_date": "2025-10-14", "transaction_time": "16:10:00", "disputed_amount": "450.25", "layer": 0}
  ]
}
```

**Expected:**
- ✅ RRN `4000111111`: Matched (₹1,200.50)
- ❌ RRN `9999999991`: Not Found
- ❌ RRN `9999999992`: Not Found (but ₹850.75 matches txn `4000222222`!)
- ❌ RRN `9999999993`: Not Found (but ₹450.25 matches txn `4000444444`!)

**Manual Review Shows:**
- 5 transactions available for selection
- User can check `4000222222` (₹850.75) to match incident 2
- User can check `4000444444` (₹450.25) to match incident 3

---

## 📋 **SCENARIO 3: All Invalid (Heavy Manual Review)** ❌❌❌❌

**Purpose:** NO auto-matches, user must manually select all from 5 available transactions

**Postman:**
```
POST http://localhost:8000/api/v2/banks/case-entry
Content-Type: application/json

Body:
{
  "acknowledgement_no": "ALLMANUAL003",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "9882662191496395",
    "state": "Delhi",
    "district": "New Delhi",
    "transaction_type": "P2P",
    "wallet": "GooglePay"
  },
  "incidents": [
    {"amount": "100.00", "rrn": "9998888881", "transaction_date": "2025-10-15", "transaction_time": "07:00:00", "disputed_amount": "100.00", "layer": 0},
    {"amount": "250.50", "rrn": "9998888882", "transaction_date": "2025-10-15", "transaction_time": "09:30:00", "disputed_amount": "250.50", "layer": 0},
    {"amount": "1800.00", "rrn": "9998888883", "transaction_date": "2025-10-15", "transaction_time": "12:45:00", "disputed_amount": "1800.00", "layer": 0},
    {"amount": "500.75", "rrn": "9998888884", "transaction_date": "2025-10-15", "transaction_time": "15:20:00", "disputed_amount": "500.75", "layer": 0}
  ]
}
```

**Expected:**
- ❌ All 4 RRNs: Not Found
- ⚠️ Manual review shows 5 transactions
- User can match by amount:
  - `5000111111` (₹100.00) → matches incident 1
  - `5000222222` (₹250.50) → matches incident 2
  - `5000333333` (₹1,800.00) → matches incident 3
  - `5000444444` (₹500.75) → matches incident 4

---

## 📋 **SCENARIO 4: Duplicate Amounts (Amount Matching Test)** 💰💰💰

**Purpose:** Multiple transactions with same amount - test careful selection

**Postman:**
```
POST http://localhost:8000/api/v2/banks/case-entry
Content-Type: application/json

Body:
{
  "acknowledgement_no": "DUPAMT004",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "2975001693298967",
    "state": "Gujarat",
    "district": "Ahmedabad",
    "transaction_type": "P2P",
    "wallet": "Paytm"
  },
  "incidents": [
    {"amount": "1000.00", "rrn": "9997777771", "transaction_date": "2025-10-16", "transaction_time": "10:00:00", "disputed_amount": "1000.00", "layer": 0},
    {"amount": "1000.00", "rrn": "9997777772", "transaction_date": "2025-10-16", "transaction_time": "11:00:00", "disputed_amount": "1000.00", "layer": 0},
    {"amount": "2500.00", "rrn": "9997777773", "transaction_date": "2025-10-16", "transaction_time": "13:00:00", "disputed_amount": "2500.00", "layer": 0}
  ]
}
```

**Expected:**
- ❌ All 3 RRNs: Not Found
- ⚠️ Manual review shows 4 transactions
- **Challenge:** 3 transactions have ₹1,000.00 amount!
  - User must match by date/time/beneficiary
  - `6000111111` (10:00) → select for incident 1
  - `6000222222` (11:00) → select for incident 2
  - `6000444444` (₹2,500) → select for incident 3

---

## 📋 **SCENARIO 5: One Valid, One Invalid** ✅❌

**Purpose:** Simple manual matching with 1 unmatched RRN

**Postman:**
```
POST http://localhost:8000/api/v2/banks/case-entry
Content-Type: application/json

Body:
{
  "acknowledgement_no": "SIMPLE005",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",
    "payer_account_number": "5478251911670246",
    "state": "Maharashtra",
    "district": "Pune",
    "transaction_type": "P2P",
    "wallet": "PhonePe"
  },
  "incidents": [
    {"amount": "1200.50", "rrn": "4000111111", "transaction_date": "2025-10-14", "transaction_time": "08:30:00", "disputed_amount": "1200.50", "layer": 0},
    {"amount": "3500.00", "rrn": "9996666661", "transaction_date": "2025-10-14", "transaction_time": "13:20:00", "disputed_amount": "3500.00", "layer": 0}
  ]
}
```

**Expected:**
- ✅ RRN `4000111111`: Matched
- ❌ RRN `9996666661`: Not Found (but ₹3,500.00 = txn `4000333333`!)
- User selects `4000333333` from manual review

---

## 🎯 **Testing Workflow (Example with Scenario 2)**

### **Step 1: Send Payload in Postman**
```
POST http://localhost:8000/api/v2/banks/case-entry
[Use MIXED002 payload above]
```

**Response:**
```json
{
  "data": {"vm_case_id": 1751}
}
```

### **Step 2: Open Frontend**
```
http://localhost:5173/operational-action/1751
```

**You'll see:**
- LEFT: 4 incidents from I4C
- RIGHT: 1 ✓ Matched, 3 ✗ Not Found
- ⚠️ **MANUAL REVIEW**: 5 transactions with checkboxes

### **Step 3: Manual Selection**

Look at unmatched RRNs:
- Incident RRN `9999999992` (₹850.75) → Check `4000222222` (₹850.75)
- Incident RRN `9999999993` (₹450.25) → Check `4000444444` (₹450.25)

Rows highlight in **yellow** when checked.

### **Step 4: Click "Respond & Close Case"**

**Automatic API Call:**
```
POST /api/v2/banks/case-entry/MIXED002/respond
```

**Response includes:**
- 1 auto-matched (status "00")
- 2 failed (status "01")  
- 2 manually matched (status "00", "manually_matched": true)

---

## 📊 **Quick Summary Table**

| Scenario | Account | Valid RRNs | Invalid RRNs | Manual Review Txns | Purpose |
|----------|---------|:----------:|:------------:|:------------------:|---------|
| **1. Perfect** | 7023612539672909 | 3 | 0 | 0 | All match automatically |
| **2. Mixed** | 5478251911670246 | 1 | 3 | 5 | Amount-based matching |
| **3. All Manual** | 9882662191496395 | 0 | 4 | 5 | Heavy manual review |
| **4. Dup Amount** | 2975001693298967 | 0 | 3 | 4 | Multiple same amounts |
| **5. Simple** | 5478251911670246 | 1 | 1 | 5 | Basic manual match |

---

## 🚀 **Quick Test Commands (Copy-Paste Ready)**

### **Scenario 2 (Recommended First Test):**
```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry' \
-H 'Content-Type: application/json' \
-d '{"acknowledgement_no":"MIXED002","sub_category":"Internet Banking Related Fraud","instrument":{"requestor":"I4C Portal","payer_bank":"Test Bank","payer_bank_code":12345,"mode_of_payment":"NEFT","payer_mobile_number":"9876543210","payer_account_number":"5478251911670246","state":"Karnataka","district":"Bangalore","transaction_type":"P2A","wallet":null},"incidents":[{"amount":"1200.50","rrn":"4000111111","transaction_date":"2025-10-14","transaction_time":"08:30:00","disputed_amount":"1200.50","layer":0},{"amount":"999.99","rrn":"9999999991","transaction_date":"2025-10-14","transaction_time":"10:00:00","disputed_amount":"999.99","layer":0},{"amount":"850.75","rrn":"9999999992","transaction_date":"2025-10-14","transaction_time":"11:45:00","disputed_amount":"850.75","layer":0},{"amount":"450.25","rrn":"9999999993","transaction_date":"2025-10-14","transaction_time":"16:10:00","disputed_amount":"450.25","layer":0}]}' | jq '.data.vm_case_id'
```

**Then open:** `http://localhost:5173/operational-action/[vm_case_id]`

### **Scenario 3 (All Invalid):**
```bash
curl -X POST 'http://localhost:8000/api/v2/banks/case-entry' \
-H 'Content-Type: application/json' \
-d '{"acknowledgement_no":"ALLMANUAL003","sub_category":"UPI Related Frauds","instrument":{"requestor":"I4C Portal","payer_bank":"Test Bank","payer_bank_code":12345,"mode_of_payment":"UPI","payer_mobile_number":"9876543210","payer_account_number":"9882662191496395","state":"Delhi","district":"New Delhi","transaction_type":"P2P","wallet":"GooglePay"},"incidents":[{"amount":"100.00","rrn":"9998888881","transaction_date":"2025-10-15","transaction_time":"07:00:00","disputed_amount":"100.00","layer":0},{"amount":"250.50","rrn":"9998888882","transaction_date":"2025-10-15","transaction_time":"09:30:00","disputed_amount":"250.50","layer":0},{"amount":"1800.00","rrn":"9998888883","transaction_date":"2025-10-15","transaction_time":"12:45:00","disputed_amount":"1800.00","layer":0},{"amount":"500.75","rrn":"9998888884","transaction_date":"2025-10-15","transaction_time":"15:20:00","disputed_amount":"500.75","layer":0}]}' | jq '.data.vm_case_id'
```

---

## 🔍 **What to Test in Frontend**

### **For Scenario 2 (MIXED002):**

**1. Check Validation Results:**
- RRN `4000111111`: Should show ✓ Matched (green badge)
- RRN `9999999991`, `9999999992`, `9999999993`: Should show ✗ Not Found (red badges)

**2. Verify Manual Review Section Appears:**
- Yellow warning box visible
- Checkbox column present
- 5 transactions listed (4000111111, 4000222222, 4000333333, 4000444444, 4000555555)

**3. Manual Matching by Amount:**
- Incident ₹850.75 → Check txn `4000222222` (₹850.75)
- Incident ₹450.25 → Check txn `4000444444` (₹450.25)
- Rows highlight yellow when checked
- Counter updates: "Manually Selected: 2"

**4. Click "Respond & Close Case":**
- Success notification appears
- Case redirects to case list
- Check backend logs: `[v2] Response includes 2 manually matched transactions`

**5. Verify Response in Postman:**
```
POST http://localhost:8000/api/v2/banks/case-entry/MIXED002/respond

Expected: 4 transactions in response (1 auto + 3 failures + 2 manual = 6 total)
```

---

## 🎨 **Expected Frontend Display (Scenario 2)**

```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│ Transaction Details from I4C         │ Matched Bank Transactions            │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ 4000111111   14-10-25   ₹1,200.50   │ 4000111111   ✓ Matched   1234567...  │
│ 9999999991   14-10-25   ₹999.99     │ 9999999991   ✗ Not Found  -          │
│ 9999999992   14-10-25   ₹850.75     │ 9999999992   ✗ Not Found  -          │
│ 9999999993   14-10-25   ₹450.25     │ 9999999993   ✗ Not Found  -          │
└──────────────────────────────────────┴──────────────────────────────────────┘

Summary: Total: 4 | ✓ Matched: 1 | ✗ Errors: 3

┌───────────────────────────────────────────────────────────────────────────┐
│ ⚠️ Manual Review Required - Select Matching Transactions                 │
│ Some RRNs could not be automatically matched. Select transactions below.  │
├───────────────────────────────────────────────────────────────────────────┤
│ [✓] | 14-10-25 | 08:30:00 | 4000111111 | 1111000022223333 | ₹1,200.50    │
│ [✓] | 14-10-25 | 11:45:00 | 4000222222 | 2222000033334444 | ₹850.75  ✓   │
│ [ ] | 14-10-25 | 13:20:00 | 4000333333 | 3333000044445555 | ₹3,500.00    │
│ [✓] | 14-10-25 | 16:10:00 | 4000444444 | 4444000055556666 | ₹450.25  ✓   │
│ [ ] | 14-10-25 | 18:30:00 | 4000555555 | 5555000066667777 | ₹6,200.00    │
├───────────────────────────────────────────────────────────────────────────┤
│ Total: 5 | Manually Selected: 2                                          │
└───────────────────────────────────────────────────────────────────────────┘

[Respond & Close Case] Button
```

---

## 🧹 **Cleanup After Testing**

```sql
-- Delete test cases
DELETE FROM case_main WHERE source_ack_no LIKE '%PERFECT001%' OR source_ack_no LIKE '%MIXED002%' OR source_ack_no LIKE '%ALLMANUAL003%' OR source_ack_no LIKE '%DUPAMT004%' OR source_ack_no LIKE '%SIMPLE005%';

-- Delete test incidents
DELETE FROM case_main_v2 WHERE acknowledgement_no IN ('PERFECT001', 'MIXED002', 'ALLMANUAL003', 'DUPAMT004', 'SIMPLE005');

-- Delete test transactions (optional - keep for future tests)
DELETE FROM txn WHERE rrn LIKE '3000%' OR rrn LIKE '4000%' OR rrn LIKE '5000%' OR rrn LIKE '6000%';
```

---

## 🎉 **Start Testing!**

**Recommended Order:**
1. **Scenario 1** (Perfect) - See all green checkmarks
2. **Scenario 2** (Mixed) - Practice manual selection
3. **Scenario 3** (All Manual) - Test heavy manual review
4. **Scenario 4** (Dup Amount) - Test careful matching

All payloads are **ready to copy-paste** into Postman! 🚀

