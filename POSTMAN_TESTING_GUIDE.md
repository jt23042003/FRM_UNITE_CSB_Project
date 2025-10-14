# 📮 Postman Testing Guide - Banks V2 API

## 🔄 Complete Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 1: POST /api/v2/banks/case-entry                               │
│ ─────────────────────────────────────────────────────────────────── │
│ • Validates structure                                                │
│ • Checks VM match (payer account)                                    │
│ • Creates VM case IMMEDIATELY                                        │
│ • Validates each RRN                                                 │
│ • Creates PSA/ECBT/ECBNT cases                                       │
│ • Returns: vm_case_id, psa_case_id, status codes per RRN            │
└──────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 2: User Reviews in Frontend                                    │
│ ─────────────────────────────────────────────────────────────────── │
│ • LEFT: Transaction details from I4C complaint                      │
│ • RIGHT: Matched bank transactions with status badges               │
│ • IF unmatched RRNs exist:                                           │
│   ⚠️ Manual Review Section appears                                  │
│   Shows ALL victim transactions (up to 100 recent)                   │
│ • User clicks "Respond & Close Case" button                          │
└──────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 3: POST /api/v2/banks/case-entry/{ack_no}/respond              │
│ ─────────────────────────────────────────────────────────────────── │
│ • Marks VM case as "Closed"                                          │
│ • Returns detailed transaction response                              │
│ • Each RRN includes:                                                 │
│   - status_code (00=success, 01=not found, etc.)                    │
│   - Full transaction details if matched                              │
│   - Case IDs (psa_case_id, ecbt_case_id, ecbnt_case_id)            │
│ • Frontend redirects to case list                                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Step-by-Step Testing Instructions

---

## **STEP 1: Create a New Case (Initial POST)**

### **1.1 Create New Request in Postman**
1. Click **"New"** → **"HTTP Request"**
2. **Method**: Select **POST**
3. **URL**: `http://localhost:8000/api/v2/banks/case-entry`

### **1.2 Set Headers**
1. Click on **"Headers"** tab
2. Add header:
   - **Key**: `Content-Type`
   - **Value**: `application/json`

### **1.3 Set Request Body**
1. Click on **"Body"** tab
2. Select **"raw"**
3. Select **"JSON"** from dropdown (right side)
4. Paste this JSON:

```json
{
  "acknowledgement_no": "POSTMAN001",
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
    {
      "amount": "100.00",
      "rrn": "1000466753",
      "transaction_date": "2025-08-01",
      "transaction_time": "13:24:38",
      "disputed_amount": "100.00",
      "layer": 0
    },
    {
      "amount": "250.00",
      "rrn": "1000466754",
      "transaction_date": "2025-08-01",
      "transaction_time": "14:30:00",
      "disputed_amount": "250.00",
      "layer": 0
    }
  ]
}
```

### **1.4 Send Request**
1. Click **"Send"** button
2. **Expected Status**: `200 OK`

### **1.5 Check Response**
You should see:
```json
{
  "meta": {
    "response_code": "00",
    "response_message": "Success"
  },
  "data": {
    "acknowledgement_no": "POSTMAN001",
    "job_id": "BANKS-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "vm_case_id": 1735,
    "psa_case_id": null
  },
  "transactions": [
    {
      "rrn_transaction_id": "1000466753",
      "status_code": "00",
      "response_message": "SUCCESS"
    },
    {
      "rrn_transaction_id": "1000466754",
      "status_code": "00",
      "response_message": "SUCCESS"
    }
  ]
}
```

### **1.6 Note Down Important Data**
📝 **Copy these from response:**
- `vm_case_id`: **1735** (you'll need this!)
- `acknowledgement_no`: **POSTMAN001**
- Status codes per RRN

---

## **STEP 2: Review Case in Frontend**

### **2.1 Open VM Case in Browser**
1. Open browser
2. Navigate to: `http://localhost:5173/operational-action/1735`
   (Replace `1735` with your actual `vm_case_id`)

### **2.2 What You Should See**

**A. Two-Section Transaction Layout:**
```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│ Transaction Details from I4C         │ Matched Bank Transactions            │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ RRN          Date        Amount      │ RRN          Status      Bene Acct   │
│ 1000466753   08-01-25   ₹100.00     │ 1000466753   ✓ Matched   (empty)     │
│ 1000466754   08-01-25   ₹250.00     │ 1000466754   ✓ Matched   (empty)     │
└──────────────────────────────────────┴──────────────────────────────────────┘

Summary: Total: 2 | ✓ Matched: 2 | ✗ Errors: 0
```

**B. Manual Review Section (ONLY if unmatched RRNs exist):**

If ANY RRN has status ✗ Not Found / Invalid / Duplicate, you'll see:

```
┌──────────────────────────────────────────────────────────────────────┐
│ ⚠️ Manual Review Required - All Victim Transactions                 │
│ Some RRNs could not be automatically matched. Review all            │
│ transactions by victim account 9579414475231007 below.               │
├──────────────────────────────────────────────────────────────────────┤
│ Date       Time      RRN          Bene Acct    Amount    Channel    │
│ 08-01-25   13:24:38  1000466753   ...          ₹100.00   UPI        │
│ 07-30-25   10:15:20  1000466700   ...          ₹500.00   NEFT       │
│ 07-29-25   14:30:00  1000466650   ...          ₹1,200.00 UPI        │
│ ... (showing up to 100 recent transactions) ...                      │
├──────────────────────────────────────────────────────────────────────┤
│ Total Victim Transactions: 45                                        │
│ 💡 Tip: Compare RRNs from I4C complaint with this list              │
└──────────────────────────────────────────────────────────────────────┘
```

**Purpose:** Allows investigator to manually find transactions that automated matching missed

**C. Respond Button:**
```
[Respond & Close Case] button at bottom
```

---

## **STEP 3: Send Detailed Response (Second POST)**

### **3.1 Create Second Request in Postman**
1. Click **"New"** → **"HTTP Request"**
2. **Method**: Select **POST**
3. **URL**: `http://localhost:8000/api/v2/banks/case-entry/POSTMAN001/respond`
   (Use the `acknowledgement_no` from Step 1)

### **4.2 Set Headers**
1. Click on **"Headers"** tab
2. Add header:
   - **Key**: `Content-Type`
   - **Value**: `application/json`

### **4.3 Body**
1. Click on **"Body"** tab
2. Select **"raw"** and **"JSON"**
3. **Option A - No Manual Selection:**
   ```json
   {}
   ```

4. **Option B - With Manual Selection:**
   ```json
   {
     "manually_selected_transactions": [
       {
         "rrn": "1000466700",
         "bene_acct_num": "1234567890",
         "amount": "500.00",
         "txn_date": "30-07-2025",
         "txn_time": "10:15:20",
         "channel": "UPI",
         "descr": "Payment to merchant",
         "acct_num": "9579414475231007"
       }
     ]
   }
   ```
   
   **Note:** In real usage, user selects these via checkboxes in frontend. This JSON is automatically generated when clicking "Respond" button.

### **4.4 Send Request**
1. Click **"Send"** button
2. **Expected Status**: `200 OK`

### **4.5 Check Detailed Response**
You should see:
```json
{
  "meta": {
    "response_code": "00",
    "response_message": "Response sent successfully"
  },
  "data": {
    "acknowledgement_no": "POSTMAN001",
    "vm_case_id": 1735,
    "psa_case_id": null,
    "ecbt_case_ids": [],
    "ecbnt_case_ids": [],
    "status": "responded"
  },
  "transactions": [
    {
      "rrn_transaction_id": "1000466753",
      "status_code": "00",
      "response_message": "SUCCESS",
      "payee_account_number": null,
      "amount": "100.00",
      "transaction_datetime": "2025-08-01 13:24:38",
      "root_account_number": "9579414475231007",
      "root_rrn_transaction_id": "1000466753",
      "psa_case_id": null,
      "ecbt_case_id": null,
      "ecbnt_case_id": null
    },
    {
      "rrn_transaction_id": "1000466754",
      "status_code": "00",
      "response_message": "SUCCESS",
      "payee_account_number": null,
      "amount": "100.00",
      "transaction_datetime": "2025-08-01 13:24:38",
      "root_account_number": "7329194845494971",
      "root_rrn_transaction_id": "1000466754",
      "psa_case_id": null,
      "ecbt_case_id": null,
      "ecbnt_case_id": null
    }
  ]
}
```

---

## **STEP 5: Verify in Frontend**

### **5.1 Refresh Browser**
Go back to: `http://localhost:5173/operational-action/1735`

### **5.2 What You Should See**
- ✅ Green banner: "Response Sent - This case has been closed"
- ❌ "Respond" button should be GONE
- ✅ Case status changed to "Closed"

---

## 🎯 **Test Different Scenarios**

### **Test Scenario 2: Mixed Validation with Manual Review**

This scenario demonstrates the manual review feature when RRNs don't match!

**Step 1: Create Case**
```
POST http://localhost:8000/api/v2/banks/case-entry

Body:
{
  "acknowledgement_no": "POSTMANMIX",
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
    {
      "amount": "100.00",
      "rrn": "1000466753",
      "transaction_date": "2025-08-01",
      "transaction_time": "13:24:38",
      "disputed_amount": "100.00",
      "layer": 0
    },
    {
      "amount": "999.99",
      "rrn": "9999999999",
      "transaction_date": "2025-08-02",
      "transaction_time": "14:00:00",
      "disputed_amount": "999.99",
      "layer": 0
    }
  ]
}
```

**Response:**
```json
{
  "data": {"vm_case_id": 1750},
  "transactions": [
    {"rrn_transaction_id": "1000466753", "status_code": "00"},
    {"rrn_transaction_id": "9999999999", "status_code": "01", "response_message": "Record not found"}
  ]
}
```

**Step 2: Open in Frontend**
`http://localhost:5173/operational-action/1750`

**You'll See:**
1. Two-section layout
2. RRN 1000466753: ✓ Matched
3. RRN 9999999999: ✗ Not Found
4. **⚠️ Manual Review Section appears!** (Yellow warning box)
   - Shows ALL transactions by victim account 9579414475231007
   - Up to 100 most recent transactions
   - User can manually look for the RRN or matching amount/date

**Step 3: Send Detailed Response**
```
POST http://localhost:8000/api/v2/banks/case-entry/POSTMANMIX/respond
```

**Detailed Response (with manual selection):**
```json
{
  "meta": {"response_code": "00", "response_message": "Response sent successfully"},
  "data": {"vm_case_id": 1750, "status": "responded"},
  "transactions": [
    {
      "rrn_transaction_id": "1000464994",
      "status_code": "00",
      "response_message": "SUCCESS",
      "payee_account_number": "1234567890",
      "amount": "5000.00"
    },
    {
      "rrn_transaction_id": "9999999999",
      "status_code": "01",
      "response_message": "Record not found"
    },
    {
      "rrn_transaction_id": "1000466700",
      "status_code": "00",
      "response_message": "SUCCESS - Manually Matched",
      "payee_account_number": "1234567890",
      "amount": "500.00",
      "manually_matched": true
    }
  ]
}
```

**Key Points:**
- ✅ Auto-matched RRN (1000464994): Normal SUCCESS
- ❌ Unmatched RRN (9999999999): Shows error code "01"
- ✅ Manually selected (1000466700): Marked as "Manually Matched"

---

### **Test Scenario 3: VM + PSA Cases**

**Step 1: Create Case**
```
POST http://localhost:8000/api/v2/banks/case-entry

Body:
{
  "acknowledgement_no": "POSTMAN002",
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
    {
      "amount": "250.75",
      "rrn": "1000464468",
      "transaction_date": "2025-01-15",
      "transaction_time": "15:04:04",
      "disputed_amount": "250.75",
      "layer": 0
    }
  ]
}
```

**Expected Response:**
```json
{
  "data": {
    "vm_case_id": 1736,
    "psa_case_id": 1737  // <-- PSA case also created!
  }
}
```

**Step 2: Send Response**
```
POST http://localhost:8000/api/v2/banks/case-entry/POSTMAN002/respond
```

**Expected:**
```json
{
  "data": {
    "vm_case_id": 1736,
    "psa_case_id": 1737
  },
  "transactions": [{
    "status_code": "00",
    "psa_case_id": 1737  // <-- Shows PSA was created
  }]
}
```

---

### **Test Scenario 3: Mixed Validation (Some Valid, Some Invalid)**

**Step 1: Create Case**
```
POST http://localhost:8000/api/v2/banks/case-entry

Body:
{
  "acknowledgement_no": "POSTMAN003",
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
    {
      "amount": "5000.00",
      "rrn": "1000464994",
      "transaction_date": "2025-01-20",
      "transaction_time": "10:00:00",
      "disputed_amount": "5000.00",
      "layer": 0
    },
    {
      "amount": "10000.00",
      "rrn": "9999999999",
      "transaction_date": "2025-01-20",
      "transaction_time": "11:00:00",
      "disputed_amount": "10000.00",
      "layer": 1
    }
  ]
}
```

**Expected Response:**
```json
{
  "transactions": [
    {
      "rrn_transaction_id": "1000464994",
      "status_code": "00",
      "response_message": "SUCCESS"
    },
    {
      "rrn_transaction_id": "9999999999",
      "status_code": "01",
      "response_message": "Record not found"
    }
  ]
}
```

**Step 2: Review in Frontend**
- RRN 1000464994: ✓ Green checkmark
- RRN 9999999999: ✗ Red error "Not Found"

**Step 3: Send Response**
```
POST http://localhost:8000/api/v2/banks/case-entry/POSTMAN003/respond
```

**Detailed Response Shows:**
- First RRN: status_code = "00"
- Second RRN: status_code = "01" (Record not found)

---

### **Test Scenario 4: Error - No VM Match**

**Step 1: Create Case**
```
POST http://localhost:8000/api/v2/banks/case-entry

Body:
{
  "acknowledgement_no": "POSTMAN004",
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
    {
      "amount": "5000.00",
      "rrn": "1000464468",
      "transaction_date": "2025-01-30",
      "transaction_time": "12:00:00",
      "disputed_amount": "5000.00",
      "layer": 0
    }
  ]
}
```

**Expected Response:**
```json
{
  "meta": {
    "response_code": "20",
    "response_message": "No matching customer account found"
  },
  "data": {
    "acknowledgement_no": "POSTMAN004",
    "job_id": "BANKS-xxx",
    "error": "Payer account number '9999999999999999' does not match any customer in the system."
  }
}
```

**Status**: `200 OK` (but with error code in meta)

**Step 2: No Respond Step** - Case was not created, nothing to respond to

---

## 🎯 **Ultimate Test: All Case Types (VM + PSA + ECBT + ECBNT)**

### **Step 1: Create Case**
```
POST http://localhost:8000/api/v2/banks/case-entry

Body:
{
  "acknowledgement_no": "POSTMAN999",
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
    {
      "amount": "250.75",
      "rrn": "1000464468",
      "transaction_date": "2025-01-15",
      "transaction_time": "15:04:04",
      "disputed_amount": "250.75",
      "layer": 0
    },
    {
      "amount": "9999.99",
      "rrn": "1000464489",
      "transaction_date": "2025-01-16",
      "transaction_time": "12:00:00",
      "disputed_amount": "9999.99",
      "layer": 0
    },
    {
      "amount": "15000.00",
      "rrn": "1000999001",
      "transaction_date": "2025-01-17",
      "transaction_time": "10:30:00",
      "disputed_amount": "15000.00",
      "layer": 0
    },
    {
      "amount": "5000.00",
      "rrn": "9999999999",
      "transaction_date": "2025-01-18",
      "transaction_time": "14:00:00",
      "disputed_amount": "5000.00",
      "layer": 1
    }
  ]
}
```

### **Step 2: Check Response - 4 CASES CREATED!**
```json
{
  "meta": {"response_code": "00"},
  "data": {
    "vm_case_id": 1740,
    "psa_case_id": 1741
  },
  "transactions": [
    {
      "rrn_transaction_id": "1000464468",
      "status_code": "00",
      "psa_case_id": 1741,
      "ecbt_case_id": null,
      "ecbnt_case_id": null
    },
    {
      "rrn_transaction_id": "1000464489",
      "status_code": "00",
      "psa_case_id": null,
      "ecbt_case_id": 1742,
      "ecbnt_case_id": null
    },
    {
      "rrn_transaction_id": "1000999001",
      "status_code": "00",
      "psa_case_id": null,
      "ecbt_case_id": null,
      "ecbnt_case_id": 1743
    },
    {
      "rrn_transaction_id": "9999999999",
      "status_code": "01",
      "response_message": "Record not found"
    }
  ]
}
```

### **Step 3: Open Each Case in Browser**
- VM Case: `http://localhost:5173/operational-action/1740`
- PSA Case: `http://localhost:5173/psa-action/1741`
- ECBT Case: `http://localhost:5173/ecbt-action/1742`
- ECBNT Case: `http://localhost:5173/ecbnt-action/1743`

### **Step 4: Send Detailed Response**
```
POST http://localhost:8000/api/v2/banks/case-entry/POSTMAN999/respond
```

**Detailed Response:**
```json
{
  "meta": {"response_code": "00", "response_message": "Response sent successfully"},
  "data": {
    "vm_case_id": 1740,
    "psa_case_id": 1741,
    "ecbt_case_ids": [1742],
    "ecbnt_case_ids": [1743],
    "status": "responded"
  },
  "transactions": [
    {
      "rrn_transaction_id": "1000464468",
      "status_code": "00",
      "response_message": "SUCCESS",
      "payee_account_number": "1030856350540889",
      "amount": "250.75",
      "transaction_datetime": "2025-01-15 15:04:04",
      "psa_case_id": 1741,
      "ecbt_case_id": null,
      "ecbnt_case_id": null
    },
    {
      "rrn_transaction_id": "1000464489",
      "status_code": "00",
      "response_message": "SUCCESS",
      "payee_account_number": "72537282762746",
      "amount": "9999.99",
      "transaction_datetime": "2025-01-16 12:00:00",
      "psa_case_id": null,
      "ecbt_case_id": 1742,
      "ecbnt_case_id": null
    },
    {
      "rrn_transaction_id": "1000999001",
      "status_code": "00",
      "response_message": "SUCCESS",
      "payee_account_number": "9999888877776666",
      "amount": "15000.00",
      "transaction_datetime": "2025-01-17 10:30:00",
      "psa_case_id": null,
      "ecbt_case_id": null,
      "ecbnt_case_id": 1743
    },
    {
      "rrn_transaction_id": "9999999999",
      "status_code": "01",
      "response_message": "Record not found",
      "payee_account_number": null,
      "amount": "5000.00",
      "transaction_datetime": "2025-01-18 14:00:00",
      "psa_case_id": null,
      "ecbt_case_id": null,
      "ecbnt_case_id": null
    }
  ]
}
```

---

## 📋 **Postman Collection Setup (Optional)**

### **Save as Collection:**
1. Create folder: **"Banks V2 API"**
2. Save requests:
   - **"1. Create Case - Simple VM"**
   - **"2. Respond - Simple VM"**
   - **"3. Create Case - All Types"**
   - **"4. Respond - All Types"**
   - **"5. Error - No VM Match"**

### **Use Variables:**
1. Click **"Environments"** (top right)
2. Create environment: **"Banks V2 Local"**
3. Add variables:
   - `base_url`: `http://localhost:8000`
   - `ack_no`: `POSTMAN001` (update per test)
   - `vm_case_id`: (update from response)

### **Update URLs to use variables:**
- Step 1: `{{base_url}}/api/v2/banks/case-entry`
- Step 2: `{{base_url}}/api/v2/banks/case-entry/{{ack_no}}/respond`

---

## ✅ **Success Checklist**

- [ ] Step 1 returns `response_code: "00"`
- [ ] `vm_case_id` returned in data
- [ ] Frontend shows VM case with two-section layout
- [ ] "Respond & Close Case" button visible
- [ ] Click button → Case status changes to Closed
- [ ] Step 2 returns detailed `transactions` array
- [ ] Each RRN has appropriate `status_code`
- [ ] Failed RRNs show error codes (01, 02, 03, etc.)
- [ ] Created case IDs attached per RRN

---

## 🐛 **Troubleshooting**

### **Error: "No matching customer account found"**
- **Issue**: `payer_account_number` not in `account_customer` table
- **Fix**: Use one of these valid accounts:
  - `9579414475231007`
  - `1870913315558618`
  - `7023612539672909`

### **Error: "Duplicate RRN"**
- **Issue**: RRN already exists in `case_incidents` table
- **Fix**: Change `acknowledgement_no` to something new (e.g., `POSTMAN005`)

### **No validation results in frontend**
- **Issue**: Old case without validation data
- **Fix**: Fallback should show green checkmarks - refresh browser

### **"Respond" endpoint returns empty transactions**
- **Issue**: No validation results stored
- **Fix**: This means it's an old case. Only new cases (created after implementation) have validation results

---

## 🎉 **Ready to Test!**

Start with **Test Scenario 1** (Simple VM) to get familiar, then move to the **Ultimate Test** to see all 4 case types created at once!

**Pro Tip:** Keep backend logs open in a separate terminal:
```bash
tail -f /Users/jalajtrivedi/frontend/backend/backend.log
```

Look for:
- `[v2] VM MATCH FOUND!`
- `[v2] VM CASE CREATED!`
- `[v2] VM case XXX marked as Closed`

