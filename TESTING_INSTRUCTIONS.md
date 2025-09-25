# 🧪 Testing Instructions for Email Case Creation System

## 📧 Sample Email Content

I've created a sample fraud case email for you to test with. The content is in `sample_fraud_email.txt` and contains:

- **ACK Number**: ACK202509250001
- **Victim Account**: 123456789012
- **Beneficiary Account**: 987654321098 (This will trigger BM + ECB cases)
- **Amount**: ₹25,000
- **All required fraud case fields** (PAN, Aadhaar, UPI ID, etc.)

## 🔍 Field Extraction Results

The email parser successfully extracts **28 fields** including:
- ackNo: ACK202509250001
- accountNumber: 123456789012 (Victim)
- toAccount: 987654321098 (Beneficiary - this is key for case creation)
- transactionAmount: 25000.0
- paymentMode: UPI
- state: Karnataka
- And many more...

## 🚀 Testing Steps

### Step 1: Send the Sample Email
1. Copy the content from `sample_fraud_email.txt`
2. Send it to your Gmail account (the one configured in .env)
3. Or create a new email with this subject and body

### Step 2: Get Message ID
```bash
curl -X GET "http://localhost:8000/dev/google/messages?max_results=5"
```
Look for the latest message and copy its `id`.

### Step 3: Test Email Parsing (Preview)
```bash
curl -X POST http://localhost:8000/email/parse/preview \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "message_id": "YOUR_MESSAGE_ID_HERE"
  }' | jq .
```

### Step 4: Test Automatic Case Creation
```bash
curl -X POST http://localhost:8000/api/email/parse/create-cases \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google", 
    "message_id": "YOUR_MESSAGE_ID_HERE"
  }' | jq .
```

## 📋 Expected Results

### Email Parsing:
- ✅ 28 fields extracted
- ✅ High confidence scores (0.85-0.95)
- ✅ All key case data available

### Case Creation:
1. **BM Case**: If account `987654321098` exists in your customer database
2. **ECBT Cases**: For customers who have `987654321098` as beneficiary + have transactions
3. **ECBNT Cases**: For customers who have `987654321098` as beneficiary but no transactions

### Sample Response Structure:
```json
{
  "id": "message_id",
  "provider": "google",
  "parsed_fields": {
    "ackNo": "ACK202509250001",
    "toAccount": "987654321098",
    "accountNumber": "123456789012",
    // ... 25+ more fields
  },
  "case_creation_results": {
    "bm_case": {
      "account_number": "987654321098",
      "customer_id": "CUST123",
      "case_result": { /* Case creation details */ }
    },
    "ecb_cases": [
      {
        "customer_id": "CUST456",
        "case_type": "ECBT",
        "has_transactions": true,
        "case_result": { /* Case details */ }
      }
    ],
    "summary": "Created BM case + X ECB cases"
  }
}
```

## 🔧 Troubleshooting

### If email parsing fails:
1. **Restart FastAPI server** (poppler installation requires restart):
   ```bash
   # Stop server (Ctrl+C)
   cd /Users/jalajtrivedi/frontend/backend
   uvicorn main:app --reload
   ```

### If no cases are created:
- Check if beneficiary account `987654321098` exists in your `account_customer` table
- Check if other customers have this account in `acc_bene` table
- Review the `case_creation_results.errors` array for specific issues

### Test endpoints:
```bash
# Basic connectivity
curl http://localhost:8000/api/email/test

# Test parsing without case creation  
curl -X POST http://localhost:8000/api/email/test-parsing \
  -H "Content-Type: application/json" \
  -d '{"provider": "google", "message_id": "test123"}'
```

## 🎯 Success Criteria

✅ **Email parsing extracts 28+ fields**  
✅ **BM case created if beneficiary account exists**  
✅ **ECBT/ECBNT cases created for related customers**  
✅ **All cases have proper ACK numbers and are assigned**  
✅ **Error handling works for edge cases**  

## 📝 Notes

- The sample email is designed to trigger maximum field extraction
- Account numbers are realistic format but fictional
- All fraud case types are represented
- Identity documents included for comprehensive testing

**Ready to test! 🚀**
