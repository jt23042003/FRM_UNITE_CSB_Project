# 🧪 **API Test Payloads - Case Creation**

## **API Endpoint:**
```
POST http://127.0.0.1:8000/api/v2/banks/case-entry
Content-Type: application/json
```

---

## **📝 Test Scenarios (Ready to Use - Fresh RRNs)**

### **Scenario 1: VM Only (Beneficiary Not in Our System)**

**Expected Cases:** VM only  
**RRN:** `9000000101` (new)

```json
{
  "acknowledgement_no": "TEST101VMONLY",
  "sub_category": "E-Wallet Related Fraud",
  "instrument": {
    "requestor": "I4C-MHA",
    "payer_bank": "State Bank of India",
    "payer_bank_code": 1,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9000000001",
    "payer_account_number": "9000000000000001",
    "state": "DELHI",
    "district": "New Delhi",
    "transaction_type": "UPI Payment",
    "wallet": "Paytm"
  },
  "incidents": [
    {
      "amount": "5000.00",
      "rrn": "9000000101",
      "transaction_date": "2023-01-05",
      "transaction_time": "09:00:00",
      "disputed_amount": "5000.00",
      "layer": 0
    }
  ]
}
```

**Quick Test:**
```bash
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST101VMONLY","sub_category":"E-Wallet Related Fraud","instrument":{"requestor":"I4C-MHA","payer_bank":"State Bank of India","payer_bank_code":1,"mode_of_payment":"UPI","payer_mobile_number":"9000000001","payer_account_number":"9000000000000001","state":"DELHI","district":"New Delhi","transaction_type":"UPI Payment","wallet":"Paytm"},"incidents":[{"amount":"5000.00","rrn":"9000000101","transaction_date":"05-01-2023","transaction_time":"09:00:00","disputed_amount":"5000.00","layer":0}]}' | jq '.'
```

---

### **Scenario 2: VM + PSA (Both Accounts in Our System)**

**Expected Cases:** VM + PSA  
**RRN:** `9000000202` (new)

```json
{
  "acknowledgement_no": "TEST202VMPSA",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "requestor": "I4C-MHA",
    "payer_bank": "HDFC Bank",
    "payer_bank_code": 2,
    "mode_of_payment": "NEFT",
    "payer_mobile_number": "9000000002",
    "payer_account_number": "9000000000000002",
    "state": "MAHARASHTRA",
    "district": "Mumbai",
    "transaction_type": "NEFT Transfer",
    "wallet": ""
  },
  "incidents": [
    {
      "amount": "7500.00",
      "rrn": "9000000202",
      "transaction_date": "2023-01-06",
      "transaction_time": "14:30:00",
      "disputed_amount": "7500.00",
      "layer": 0
    }
  ]
}
```

**Quick Test:**
```bash
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST202VMPSA","sub_category":"UPI Related Frauds","instrument":{"requestor":"I4C-MHA","payer_bank":"HDFC Bank","payer_bank_code":2,"mode_of_payment":"NEFT","payer_mobile_number":"9000000002","payer_account_number":"9000000000000002","state":"MAHARASHTRA","district":"Mumbai","transaction_type":"NEFT Transfer","wallet":""},"incidents":[{"amount":"7500.00","rrn":"9000000202","transaction_date":"06-01-2023","transaction_time":"14:30:00","disputed_amount":"7500.00","layer":0}]}' | jq '.'
```

---

### **Scenario 3: VM + PSA + ECBT (With Transaction History)**

**Expected Cases:** VM + PSA + ECBT  
**RRN:** `9000000303` (new)

```json
{
  "acknowledgement_no": "TEST303ECBT",
  "sub_category": "Internet Banking Related Fraud",
  "instrument": {
    "requestor": "I4C-MHA",
    "payer_bank": "ICICI Bank",
    "payer_bank_code": 3,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9000000004",
    "payer_account_number": "9000000000000004",
    "state": "KARNATAKA",
    "district": "Bangalore",
    "transaction_type": "UPI Payment",
    "wallet": "Google Pay"
  },
  "incidents": [
    {
      "amount": "12000.00",
      "rrn": "9000000303",
      "transaction_date": "2023-01-07",
      "transaction_time": "11:45:00",
      "disputed_amount": "12000.00",
      "layer": 0
    }
  ]
}
```

**Quick Test:**
```bash
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST303ECBT","sub_category":"Internet Banking Related Fraud","instrument":{"requestor":"I4C-MHA","payer_bank":"ICICI Bank","payer_bank_code":3,"mode_of_payment":"UPI","payer_mobile_number":"9000000004","payer_account_number":"9000000000000004","state":"KARNATAKA","district":"Bangalore","transaction_type":"UPI Payment","wallet":"Google Pay"},"incidents":[{"amount":"12000.00","rrn":"9000000303","transaction_date":"07-01-2023","transaction_time":"11:45:00","disputed_amount":"12000.00","layer":0}]}' | jq '.'
```

---

### **Scenario 4: VM + PSA + ECBNT (No Transaction History)**

**Expected Cases:** VM + PSA + ECBNT  
**RRN:** `9000000404` (new)

```json
{
  "acknowledgement_no": "TEST404ECBNT",
  "sub_category": "Demat /Depository Fraud",
  "instrument": {
    "requestor": "I4C-MHA",
    "payer_bank": "Kotak Mahindra Bank",
    "payer_bank_code": 4,
    "mode_of_payment": "RTGS",
    "payer_mobile_number": "9000000007",
    "payer_account_number": "9000000000000007",
    "state": "GUJARAT",
    "district": "Ahmedabad",
    "transaction_type": "RTGS Transfer",
    "wallet": ""
  },
  "incidents": [
    {
      "amount": "15000.00",
      "rrn": "9000000404",
      "transaction_date": "2023-01-08",
      "transaction_time": "16:20:00",
      "disputed_amount": "15000.00",
      "layer": 0
    }
  ]
}
```

**Quick Test:**
```bash
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST404ECBNT","sub_category":"Demat /Depository Fraud","instrument":{"requestor":"I4C-MHA","payer_bank":"Kotak Mahindra Bank","payer_bank_code":4,"mode_of_payment":"RTGS","payer_mobile_number":"9000000007","payer_account_number":"9000000000000007","state":"GUJARAT","district":"Ahmedabad","transaction_type":"RTGS Transfer","wallet":""},"incidents":[{"amount":"15000.00","rrn":"9000000404","transaction_date":"08-01-2023","transaction_time":"16:20:00","disputed_amount":"15000.00","layer":0}]}' | jq '.'
```

---

### **Scenario 5: VM + ECBT (No PSA - External Beneficiary)**

**Expected Cases:** VM + ECBT (no PSA)  
**RRN:** `9000000505` (new)

```json
{
  "acknowledgement_no": "TEST505VMECBT",
  "sub_category": "Fraud Call /Vishing",
  "instrument": {
    "requestor": "I4C-MHA",
    "payer_bank": "Punjab National Bank",
    "payer_bank_code": 6,
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9000000010",
    "payer_account_number": "9000000000000010",
    "state": "PUNJAB",
    "district": "Chandigarh",
    "transaction_type": "UPI Payment",
    "wallet": "PhonePe"
  },
  "incidents": [
    {
      "amount": "20000.00",
      "rrn": "9000000505",
      "transaction_date": "2023-01-09",
      "transaction_time": "13:30:00",
      "disputed_amount": "20000.00",
      "layer": 0
    }
  ]
}
```

**Quick Test:**
```bash
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST505VMECBT","sub_category":"Fraud Call /Vishing","instrument":{"requestor":"I4C-MHA","payer_bank":"Punjab National Bank","payer_bank_code":6,"mode_of_payment":"UPI","payer_mobile_number":"9000000010","payer_account_number":"9000000000000010","state":"PUNJAB","district":"Chandigarh","transaction_type":"UPI Payment","wallet":"PhonePe"},"incidents":[{"amount":"20000.00","rrn":"9000000505","transaction_date":"09-01-2023","transaction_time":"13:30:00","disputed_amount":"20000.00","layer":0}]}' | jq '.'
```

---

### **Scenario 6: Card Fraud with Multiple Incidents**

**Expected Cases:** Multiple incidents for VM + PSA  
**RRNs:** `9000000601`, `9000000602` (new)

```json
{
  "acknowledgement_no": "TEST606MULTI",
  "sub_category": "Debit/Credit Card Fraud/Sim Swap Fraud",
  "instrument": {
    "requestor": "I4C-MHA",
    "payer_bank": "HDFC Bank",
    "payer_bank_code": 2,
    "mode_of_payment": "Card",
    "payer_mobile_number": "9000000002",
    "payer_account_number": "9000000000000002",
    "state": "MAHARASHTRA",
    "district": "Mumbai",
    "transaction_type": "POS Transaction"
  },
  "incidents": [
    {
      "amount": "5000.00",
      "rrn": "9000000601",
      "transaction_date": "2023-01-06",
      "transaction_time": "09:00:00",
      "disputed_amount": "5000.00",
      "layer": 0,
      "first6digit": "123456",
      "last4digit": "7890",
      "cardlength": "16"
    },
    {
      "amount": "7500.00",
      "rrn": "9000000602",
      "transaction_date": "2023-01-06",
      "transaction_time": "14:30:00",
      "disputed_amount": "7500.00",
      "layer": 1,
      "first6digit": "123456",
      "last4digit": "7890",
      "cardlength": "16"
    }
  ]
}
```

**Quick Test:**
```bash
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST606MULTI","sub_category":"Debit/Credit Card Fraud/Sim Swap Fraud","instrument":{"requestor":"I4C-MHA","payer_bank":"HDFC Bank","payer_bank_code":2,"mode_of_payment":"Card","payer_mobile_number":"9000000002","payer_account_number":"9000000000000002","state":"MAHARASHTRA","district":"Mumbai","transaction_type":"POS Transaction"},"incidents":[{"amount":"5000.00","rrn":"9000000601","transaction_date":"06-01-2023","transaction_time":"09:00:00","disputed_amount":"5000.00","layer":0,"first6digit":"123456","last4digit":"7890","cardlength":"16"},{"amount":"7500.00","rrn":"9000000602","transaction_date":"06-01-2023","transaction_time":"14:30:00","disputed_amount":"7500.00","layer":1,"first6digit":"123456","last4digit":"7890","cardlength":"16"}]}' | jq '.'
```

---

### **Scenario 7: AEPS Fraud**

**Expected Cases:** VM only  
**RRN:** `9000000707` (new)

```json
{
  "acknowledgement_no": "TEST707AEPS",
  "sub_category": "Aadhar Enabled Payment System (AEPS) Related Frauds",
  "instrument": {
    "requestor": "I4C-MHA",
    "payer_bank": "Central Bank of India",
    "payer_bank_code": 8,
    "mode_of_payment": "AEPS",
    "payer_mobile_number": "9000000001",
    "payer_account_number": "9000000000000001",
    "state": "BIHAR",
    "district": "Patna",
    "transaction_type": "Aadhar Payment"
  },
  "incidents": [
    {
      "amount": "10000.00",
      "rrn": "9000000707",
      "transaction_date": "2023-01-12",
      "transaction_time": "15:45:00",
      "disputed_amount": "10000.00",
      "layer": 0
    }
  ]
}
```

**Quick Test:**
```bash
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST707AEPS","sub_category":"Aadhar Enabled Payment System (AEPS) Related Frauds","instrument":{"requestor":"I4C-MHA","payer_bank":"Central Bank of India","payer_bank_code":8,"mode_of_payment":"AEPS","payer_mobile_number":"9000000001","payer_account_number":"9000000000000001","state":"BIHAR","district":"Patna","transaction_type":"Aadhar Payment"},"incidents":[{"amount":"10000.00","rrn":"9000000707","transaction_date":"12-01-2023","transaction_time":"15:45:00","disputed_amount":"10000.00","layer":0}]}' | jq '.'
```

---

## **🚀 Test All Scenarios at Once**

```bash
# Run all 7 test scenarios sequentially
cd /Users/jalajtrivedi/frontend

echo "=== Scenario 1: VM Only ===" && \
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST101VMONLY","sub_category":"E-Wallet Related Fraud","instrument":{"requestor":"I4C-MHA","payer_bank":"State Bank of India","payer_bank_code":1,"mode_of_payment":"UPI","payer_mobile_number":"9000000001","payer_account_number":"9000000000000001","state":"DELHI","district":"New Delhi","transaction_type":"UPI Payment","wallet":"Paytm"},"incidents":[{"amount":"5000.00","rrn":"9000000101","transaction_date":"05-01-2023","transaction_time":"09:00:00","disputed_amount":"5000.00","layer":0}]}' | jq '.meta' && \

echo "=== Scenario 2: VM + PSA ===" && \
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST202VMPSA","sub_category":"UPI Related Frauds","instrument":{"requestor":"I4C-MHA","payer_bank":"HDFC Bank","payer_bank_code":2,"mode_of_payment":"NEFT","payer_mobile_number":"9000000002","payer_account_number":"9000000000000002","state":"MAHARASHTRA","district":"Mumbai","transaction_type":"NEFT Transfer","wallet":""},"incidents":[{"amount":"7500.00","rrn":"9000000202","transaction_date":"06-01-2023","transaction_time":"14:30:00","disputed_amount":"7500.00","layer":0}]}' | jq '.meta' && \

echo "=== Scenario 3: VM + PSA + ECBT ===" && \
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST303ECBT","sub_category":"Internet Banking Related Fraud","instrument":{"requestor":"I4C-MHA","payer_bank":"ICICI Bank","payer_bank_code":3,"mode_of_payment":"UPI","payer_mobile_number":"9000000004","payer_account_number":"9000000000000004","state":"KARNATAKA","district":"Bangalore","transaction_type":"UPI Payment","wallet":"Google Pay"},"incidents":[{"amount":"12000.00","rrn":"9000000303","transaction_date":"07-01-2023","transaction_time":"11:45:00","disputed_amount":"12000.00","layer":0}]}' | jq '.meta' && \

echo "=== Scenario 4: VM + PSA + ECBNT ===" && \
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST404ECBNT","sub_category":"Demat /Depository Fraud","instrument":{"requestor":"I4C-MHA","payer_bank":"Kotak Mahindra Bank","payer_bank_code":4,"mode_of_payment":"RTGS","payer_mobile_number":"9000000007","payer_account_number":"9000000000000007","state":"GUJARAT","district":"Ahmedabad","transaction_type":"RTGS Transfer","wallet":""},"incidents":[{"amount":"15000.00","rrn":"9000000404","transaction_date":"08-01-2023","transaction_time":"16:20:00","disputed_amount":"15000.00","layer":0}]}' | jq '.meta' && \

echo "=== Scenario 5: VM + ECBT (No PSA) ===" && \
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST505VMECBT","sub_category":"Fraud Call /Vishing","instrument":{"requestor":"I4C-MHA","payer_bank":"Punjab National Bank","payer_bank_code":6,"mode_of_payment":"UPI","payer_mobile_number":"9000000010","payer_account_number":"9000000000000010","state":"PUNJAB","district":"Chandigarh","transaction_type":"UPI Payment","wallet":"PhonePe"},"incidents":[{"amount":"20000.00","rrn":"9000000505","transaction_date":"09-01-2023","transaction_time":"13:30:00","disputed_amount":"20000.00","layer":0}]}' | jq '.meta' && \

echo "=== Scenario 6: Card Fraud (Multiple Incidents) ===" && \
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST606MULTI","sub_category":"Debit/Credit Card Fraud/Sim Swap Fraud","instrument":{"requestor":"I4C-MHA","payer_bank":"HDFC Bank","payer_bank_code":2,"mode_of_payment":"Card","payer_mobile_number":"9000000002","payer_account_number":"9000000000000002","state":"MAHARASHTRA","district":"Mumbai","transaction_type":"POS Transaction"},"incidents":[{"amount":"5000.00","rrn":"9000000601","transaction_date":"06-01-2023","transaction_time":"09:00:00","disputed_amount":"5000.00","layer":0,"first6digit":"123456","last4digit":"7890","cardlength":"16"},{"amount":"7500.00","rrn":"9000000602","transaction_date":"06-01-2023","transaction_time":"14:30:00","disputed_amount":"7500.00","layer":1,"first6digit":"123456","last4digit":"7890","cardlength":"16"}]}' | jq '.meta' && \

echo "=== Scenario 7: AEPS Fraud ===" && \
curl -s -X POST "http://127.0.0.1:8000/api/v2/banks/case-entry" -H "Content-Type: application/json" -d '{"acknowledgement_no":"TEST707AEPS","sub_category":"Aadhar Enabled Payment System (AEPS) Related Frauds","instrument":{"requestor":"I4C-MHA","payer_bank":"Central Bank of India","payer_bank_code":8,"mode_of_payment":"AEPS","payer_mobile_number":"9000000001","payer_account_number":"9000000000000001","state":"BIHAR","district":"Patna","transaction_type":"Aadhar Payment"},"incidents":[{"amount":"10000.00","rrn":"9000000707","transaction_date":"12-01-2023","transaction_time":"15:45:00","disputed_amount":"10000.00","layer":0}]}' | jq '.meta'

echo "=== All Tests Complete! ==="
```

---

## **📊 Case Creation Logic Summary**

### **VM (Victim Match)**
- Created when: `payer_account_number` exists in `account_customer` table
- Always checked first

### **PSA (Potential Suspect Account)**
- Created when: `bene_acct_num` (from transaction) exists in `account_customer` table
- Checked after VM

### **ECBT (Existing Customer Beneficiary with Transaction)**
- Created when:
  1. `bene_acct_num` exists in `acc_bene` table
  2. Transaction exists between `cust_acct_num` and `bene_acct_num`

### **ECBNT (Existing Customer Beneficiary with No Transaction)**
- Created when:
  1. `bene_acct_num` exists in `acc_bene` table
  2. NO transaction exists between `cust_acct_num` and `bene_acct_num`

---

## **📋 Supported Sub-Categories**

1. E-Wallet Related Fraud
2. Debit/Credit Card Fraud/Sim Swap Fraud
3. Debit/Credit Card Fraud/Sim Swap Fraud (VISA, Master Card, Debit Card, American Express, Rupay)
4. Internet Banking Related Fraud
5. Demat /Depository Fraud
6. Business Email Compromise/Email Takeover
7. Fraud Call /Vishing
8. UPI Related Frauds
9. Aadhar Enabled Payment System (AEPS) Related Frauds

---

## **✅ Validation Rules**

- **acknowledgement_no**: 8-20 alphanumeric characters
- **amount**: Format NNNN.NN (e.g., 5000.00)
- **rrn**: 10-14 numeric digits (must be unique across all incidents)
- **transaction_date**: YYYY-MM-DD format (e.g., 2025-10-09)
- **transaction_time**: HH:MM:SS format (optional)
- **payer_mobile_number**: 10-15 digits
- **payer_account_number**: 9-18 digits
- **incidents**: 1-25 incidents per request

## **📋 Response Codes**

| Code | Message | Description |
|------|---------|-------------|
| 00 | Success | Request processed successfully |
| 01 | Validation Error | Field format validation failed |
| 16 | Duplicate RRN | RRN already exists in the system |
| 31 | Database Error | Database operation failed |
| 99 | Internal Error | Unexpected server error |

---

## **🔍 Verify Created Cases**

```bash
# Check cases in database
PGPASSWORD='password123' psql -h 34.47.219.225 -p 5433 -U jalaj -d csb_new_db -c \
  "SELECT case_id, source_ack_no, case_type, status FROM public.case_main WHERE source_ack_no LIKE 'TEST%' ORDER BY case_id;"
```

---

**Important Notes:**
- ⚠️ **RRNs must be unique!** If you submit with a duplicate RRN, the API will return error code "16" (Duplicate RRN)
- ✅ All new RRNs (9000000101-9000000707) are ready to use
- 💡 Each scenario uses a unique RRN range for easy identification
- 🔒 **Why?** In real banking systems, each RRN represents one unique transaction - duplicates are not allowed

**Last Updated:** October 9, 2025
