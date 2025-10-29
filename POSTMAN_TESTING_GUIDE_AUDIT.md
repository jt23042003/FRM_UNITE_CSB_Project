# Postman Testing Guide - Audit Logging Feature

## Prerequisites

1. **Ensure the table is created**:
   ```bash
   cd backend
   python scripts/create_failed_requests_table.py
   ```

2. **Start your backend server**:
   ```bash
   cd backend
   python main.py
   ```

3. **Import the Postman collection**: Import `Banks_V2_Audit_Tests.postman_collection.json` into Postman

---

## Test Scenarios

### Test 1: Invalid Account Number (Too Short - 3 digits)
**Expected Result**: Validation error + Stored in audit table

**Payload**:
```json
{
  "acknowledgement_no": "TEST_INVALID_001",
  "sub_category": "UPI Related Frauds",
  "instrument": {
    "payer_account_number": "123",  // Too short!
    "payer_mobile_number": "9876543210",
    ...
  },
  "incidents": [...]
}
```

**What to Check**:
1. Response code: `200`
2. Response message: "Validation Error"
3. Error code: `01`
4. Should NOT create any cases
5. Verify in database: `SELECT * FROM banks_v2_failed_requests WHERE acknowledgement_no = 'TEST_INVALID_001';`

---

### Test 2: Invalid Account Number (Too Long - 50 digits)
**Expected Result**: Validation error + Stored in audit table

**Payload**:
```json
{
  "acknowledgement_no": "TEST_INVALID_002",
  "instrument": {
    "payer_account_number": "12345678901234567890123456789012345678901234567890"  // Too long!
  },
  ...
}
```

**What to Check**:
1. Response code: `200`
2. Validation error returned
3. Verify in database that raw request body is stored

---

### Test 3: Invalid Mobile Number
**Expected Result**: Validation error + Stored in audit table

**Payload**:
```json
{
  "acknowledgement_no": "TEST_INVALID_003",
  "instrument": {
    "payer_mobile_number": "12345",  // Too short!
    "payer_account_number": "7710902234001"
  },
  ...
}
```

**What to Check**:
1. Validation error for mobile number field
2. Request stored in audit table

---

### Test 4: Invalid RRN Format
**Expected Result**: Validation error + Stored in audit table

**Payload**:
```json
{
  "acknowledgement_no": "TEST_INVALID_004",
  "incidents": [
    {
      "rrn": "12345",  // Too short! Should be 10-14 digits
      ...
    }
  ]
}
```

**What to Check**:
1. Validation error for RRN field
2. Request stored in audit table

---

### Test 5: No VM Match (Valid but Non-existent Account)
**Expected Result**: VM match error (code 20) + Stored in audit table

**Payload**:
```json
{
  "acknowledgement_no": "TEST_NO_VM_001",
  "instrument": {
    "payer_account_number": "999888777666555",  // Valid format but doesn't exist
    ...
  },
  "incidents": [
    {
      "rrn": "9992000300",
      ...
    }
  ]
}
```

**What to Check**:
1. Response code: `200`
2. Response message: "No matching customer account found"
3. Error code: `20`
4. Verify in database:
   ```sql
   SELECT 
       acknowledgement_no,
       failure_reason,
       failure_type,
       error_details->>'payer_account_number' as payer_account,
       raw_request_body
   FROM banks_v2_failed_requests 
   WHERE acknowledgement_no = 'TEST_NO_VM_001';
   ```

**Expected database record**:
- `failure_type`: `vm_match_failed`
- `failure_reason`: Contains payer account number
- `error_details`: JSON with payer_account_number
- `raw_request_body`: Complete request body

---

### Test 6: Valid Request (Should Succeed)
**Expected Result**: Success + VM case created (NO audit record)

**Payload**:
```json
{
  "acknowledgement_no": "TEST_VALID_001",
  "instrument": {
    "payer_account_number": "7710902234001",  // Valid and exists
    ...
  },
  "incidents": [
    {
      "rrn": "9992000300",
      ...
    }
  ]
}
```

**What to Check**:
1. Response code: `200`
2. Response message: "Success"
3. Error code: `00`
4. `vm_case_id` should be present in response
5. NO record in `banks_v2_failed_requests` table

---

## How to Verify Audit Records

### Query All Failed Requests
```sql
SELECT * FROM banks_v2_failed_requests ORDER BY created_at DESC;
```

### Query Validation Errors Only
```sql
SELECT 
    id,
    acknowledgement_no,
    failure_reason,
    created_at
FROM banks_v2_failed_requests 
WHERE failure_type = 'validation_error'
ORDER BY created_at DESC;
```

### Query VM Match Failures Only
```sql
SELECT 
    id,
    acknowledgement_no,
    failure_reason,
    error_details->>'payer_account_number' as payer_account,
    created_at
FROM banks_v2_failed_requests 
WHERE failure_type = 'vm_match_failed'
ORDER BY created_at DESC;
```

### Query Specific ACK
```sql
SELECT * FROM banks_v2_failed_requests 
WHERE acknowledgement_no = 'TEST_NO_VM_001';
```

### View Raw Request Body
```sql
SELECT 
    acknowledgement_no,
    raw_request_body,
    failure_reason
FROM banks_v2_failed_requests 
WHERE id = 1;
```

---

## Expected Results Summary

| Test | ACK | Expected Status | Audit Stored? | Table Record |
|------|-----|-----------------|---------------|--------------|
| Test 1 | TEST_INVALID_001 | Validation Error | ✅ Yes | `validation_error` |
| Test 2 | TEST_INVALID_002 | Validation Error | ✅ Yes | `validation_error` |
| Test 3 | TEST_INVALID_003 | Validation Error | ✅ Yes | `validation_error` |
| Test 4 | TEST_INVALID_004 | Validation Error | ✅ Yes | `validation_error` |
| Test 5 | TEST_NO_VM_001 | VM Match Failed (code 20) | ✅ Yes | `vm_match_failed` |
| Test 6 | TEST_VALID_001 | Success (code 00) | ❌ No | No record |

---

## Quick Postman Workflow

1. **Import Collection**: Import `Banks_V2_Audit_Tests.postman_collection.json`
2. **Run Test 1-4**: Should return validation errors
3. **Run Test 5**: Should return VM match error (code 20)
4. **Run Test 6**: Should return success
5. **Verify in Database**: Run SQL queries above

---

## Troubleshooting

### Issue: No records in audit table
**Solution**: Make sure the table exists and backend server is running

### Issue: Server returns 500 error
**Solution**: Check backend logs for errors, ensure database connection is working

### Issue: Validation errors not stored
**Solution**: Check that exception handler is being called (check logs for `[AUDIT]` messages)

### Issue: VM match failures not stored
**Solution**: Check that storage happens before rollback in banks_v2.py

---

## Next Steps After Testing

1. **Verify all failed requests are stored**
2. **Test query operations on audit table**
3. **Try to manually resolve a failed request**
4. **Document any issues found**

---

## Additional Notes

- All failed requests are stored BEFORE returning error response
- Storage failure doesn't affect API response
- Raw request body is stored as JSONB for querying
- Can be marked as resolved later for tracking

