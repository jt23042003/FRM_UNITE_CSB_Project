# 🚀 ECBT & ECBNT API Test Payloads (Ready to Use!)

✅ **Test data has been inserted into the database!**

---

## 📌 Test Scenario 1: ECBT Case

**What it tests:** Customer who HAS transactions with fraudulent beneficiary

**Expected Result:**
- ✅ VM case created
- ✅ ECBT case created 
- ✅ Potential Victim section shows account: `1234567890` (CUSTOMER account, not beneficiary)
- ✅ Transaction table shows 2 transactions from customer to beneficiary `7000723456789999`

### Payload:
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
      "rrn": "2024011501",
      "transaction_date": "2024-01-15",
      "transaction_time": "14:30:00",
      "disputed_amount": "5000.00",
      "layer": 0
    }
  ]
}
```

---

## 📌 Test Scenario 2: ECBNT Case

**What it tests:** Customer who has beneficiary saved but NO transactions

**Expected Result:**
- ✅ VM case created
- ✅ ECBNT case created
- ✅ Potential Victim section shows account: `5555666677778888` (CUSTOMER account, not beneficiary)
- ✅ No transaction table shown (because ECBNT = no transactions)

### Payload:
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
      "rrn": "2024012003",
      "transaction_date": "2024-01-20",
      "transaction_time": "10:15:00",
      "disputed_amount": "3000.00",
      "layer": 0
    }
  ]
}
```

---

## 📌 Test Scenario 3: Combined (Both ECBT & ECBNT)

**What it tests:** Multiple incidents that trigger both case types

**Expected Result:**
- ✅ VM case created
- ✅ ECBT case created (from first incident)
- ✅ ECBNT case created (from second incident)

### Payload:
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
    "payer_account_number": "9999888877776666",
    "state": "Delhi",
    "district": "New Delhi",
    "transaction_type": "UPI",
    "wallet": "PhonePe"
  },
  "incidents": [
    {
      "amount": "5000.00",
      "rrn": "2024011501",
      "transaction_date": "2024-01-15",
      "transaction_time": "14:30:00",
      "disputed_amount": "5000.00",
      "layer": 0
    },
    {
      "amount": "3000.00",
      "rrn": "2024012003",
      "transaction_date": "2024-01-20",
      "transaction_time": "10:15:00",
      "disputed_amount": "3000.00",
      "layer": 1
    }
  ]
}
```

---

## 🔧 How to Test

### Using Postman:

1. **Endpoint:** `POST http://localhost:8000/api/v2/banks/case-entry`
2. **Headers:**
   ```
   Content-Type: application/json
   Authorization: Bearer <your_jwt_token>
   ```
3. **Body:** Copy one of the payloads above
4. **Send Request**

### Using curl:

```bash
curl -X POST "http://localhost:8000/api/v2/banks/case-entry" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
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
      "rrn": "2024011501",
      "transaction_date": "2024-01-15",
      "transaction_time": "14:30:00",
      "disputed_amount": "5000.00",
      "layer": 0
    }]
  }'
```

---

## ✅ What to Verify in Frontend

### For ECBT Cases:
1. Open the ECBT case from case list
2. Check **"Potential Victim - Bank Customer Details"** section (RIGHT SIDE)
3. **Bank Account** field should show: `1234567890` ✅ (NOT `7000723456789999`)
4. Transaction table should show:
   - **Customer Account:** `1234567890`
   - **Beneficiary Account:** `7000723456789999`
   - **2 transactions** with amounts ₹5000 and ₹3500

### For ECBNT Cases:
1. Open the ECBNT case from case list
2. Check **"Potential Victim - Bank Customer Details"** section (RIGHT SIDE)
3. **Bank Account** field should show: `5555666677778888` ✅ (NOT `9000111122223333`)
4. Should show info banner: "No Transaction History" (because it's ECBNT)

---

## 📊 Test Data Summary

| Test Type | Customer Account | Beneficiary Account | Has Transactions? | RRN Used |
|-----------|------------------|---------------------|-------------------|----------|
| ECBT      | 1234567890       | 7000723456789999    | ✅ Yes (2 txns)   | 2024011501 |
| ECBNT     | 5555666677778888 | 9000111122223333    | ❌ No             | 2024012003 |

---

## 🐛 Troubleshooting

### If no cases are created:
1. Check backend logs: `tail -f backend/backend.log | grep -i ecb`
2. Verify the response JSON shows case IDs
3. Check database: `SELECT * FROM case_main WHERE source_ack_no LIKE '%ECBT%' OR source_ack_no LIKE '%ECBNT%'`

### If wrong account shown:
1. This was the bug we fixed!
2. Restart backend to ensure new code is loaded
3. Verify `case_main.acc_num` shows customer account, not beneficiary

---

**Happy Testing! 🎉**

