# Banks v2 API - Audit Data Guide

This document explains what data gets stored in the `banks_v2_failed_requests` table and what constitutes a valid request body.

---

## What Gets Stored in `banks_v2_failed_requests` Table

Any request that **CANNOT BE PROCESSED** gets stored for audit purposes.

### 1. Pydantic Validation Errors (failure_type = `validation_error`)

These are requests with **invalid field formats**:

#### Invalid Account Number
```json
"payer_account_number": "123"  // ❌ Too short (need 9-18 digits)
"payer_account_number": "123456789012345678901234567890"  // ❌ Too long
"payer_account_number": "9579414475231007w857863"  // ❌ Has letter 'w'
```

#### Invalid Mobile Number
```json
"payer_mobile_number": "12345"  // ❌ Too short (need 10-15 digits)
```

#### Invalid RRN
```json
"rrn": "7654"  // ❌ Too short (need 10-14 digits)
"rrn": "100067531234567890-"  // ❌ Has dash, invalid format
```

#### Invalid Amount Format
```json
"amount": "15000"  // ❌ Missing .00
"amount": "15000.0"  // ❌ Missing second decimal
```

#### Invalid Date Format
```json
"transaction_date": "01-08-2025"  // ❌ Wrong format (need YYYY-MM-DD)
```

#### Invalid Sub-Category
```json
"sub_category": "Unknown Category"  // ❌ Not in allowed list
```

#### Invalid Acknowledgement Number
```json
"acknowledgement_no": "TEST_INVALID"  // ❌ Contains underscore (need alphanumeric only)
"acknowledgement_no": "AB"  // ❌ Too short (need 8-20 characters)
```

---

### 2. VM Match Failures (failure_type = `vm_match_failed`)

**Valid format** but account doesn't exist in our database:

```json
{
  "payer_account_number": "999888777666555",  // ✅ Valid format (12-15 digits)
  "payer_mobile_number": "9876543210",  // ✅ Valid
  "rrn": "9992000300123",  // ✅ Valid
  // ... all other fields valid
}
```

**Why it fails**: Format is correct, but this account number doesn't exist in the `account_customer` table.

---

## Correct/Valid Input Body Format

Here's an example of a **valid request**:

```json
{
  "acknowledgement_no": "TEST12345",  // ✅ 8-20 alphanumeric (no underscores)
  "sub_category": "UPI Related Frauds",  // ✅ Must be from allowed list
  "instrument": {
    "requestor": "I4C Portal",
    "payer_bank": "Test Bank",
    "payer_bank_code": 12345,  // ✅ Integer
    "mode_of_payment": "UPI",
    "payer_mobile_number": "9876543210",  // ✅ 10-15 digits
    "payer_account_number": "7710902234001",  // ✅ 9-18 DIGITS ONLY
    "state": "TamilNadu",
    "district": "Chennai",
    "transaction_type": "P2P",  // Optional
    "wallet": "PhonePe"  // Optional
  },
  "incidents": [  // ✅ 1-25 incidents
    {
      "amount": "15000.00",  // ✅ Must be NNNN.NN format
      "rrn": "9992000300123",  // ✅ 10-14 NUMERIC digits only
      "transaction_date": "2025-10-20",  // ✅ YYYY-MM-DD format
      "transaction_time": "14:15:00",  // ✅ HH:MM:SS (24-hour)
      "disputed_amount": "15000.00",  // ✅ Must be NNNN.NN format
      "layer": 0  // ✅ Integer
    }
  ]
}
```

---

## Validation Rules Summary

| Field | Valid Format | Invalid Examples |
|-------|-------------|------------------|
| `acknowledgement_no` | 8-20 alphanumeric characters (A-Z, a-z, 0-9) | `TEST_INVALID` (underscore), `AB` (too short), `TOOLONGNAME12345` (too long) |
| `payer_account_number` | 9-18 digits only | `123` (too short), `123456789012345678901234567890` (too long), `9579414475231007w857863` (has letter) |
| `payer_mobile_number` | 10-15 digits only | `12345` (too short) |
| `rrn` | 10-14 numeric digits only | `7654` (too short), `100067531234567890-` (has dash), `ABC123` (has letters) |
| `amount` | NNNN.NN (exactly 2 decimals) | `15000` (missing .00), `15000.0` (missing second decimal) |
| `transaction_date` | YYYY-MM-DD | `01-08-2025` (wrong format), `01/08/2025` (slashes) |
| `transaction_time` | HH:MM:SS (24-hour) | `2:15 PM` (12-hour), `14:15` (missing seconds) |
| `sub_category` | Must be from allowed list | `Custom Fraud` (not in list) |
| `incidents` | Array with 1-25 items | `[]` (empty), 30 items (too many) |

---

## Allowed Sub-Categories

The `sub_category` field must be one of these exact values:

1. "E-Wallet Related Fraud"
2. "Debit/Credit Card Fraud/Sim Swap Fraud"
3. "Debit/Credit Card Fraud/Sim Swap Fraud (VISA, Master Card, Debit Card, American Express, Rupay)"
4. "Internet Banking Related Fraud"
5. "Demat /Depository Fraud"
6. "Business Email Compromise/Email Takeover"
7. "Fraud Call /Vishing"
8. "UPI Related Frauds"
9. "Aadhar Enabled Payment System (AEPS) Related Frauds"

---

## What Gets Stored vs What Gets Processed

### ✅ Stored in `banks_v2_failed_requests`:
1. Any validation error (invalid format)
2. Valid format but no VM match (account doesn't exist)
3. Any Pydantic validation failure
4. Processing errors

### ✅ Not Stored (Processed Successfully):
1. Valid request with successful processing
2. All fields valid
3. VM match successful
4. Cases created successfully

---

## Example Scenarios

### Scenario 1: Stored (Validation Error)
```json
{
  "acknowledgement_no": "INVALID10122",
  "payer_account_number": "9579414475231007w857863",  // ❌ Has 'w'
  "incidents": [{"rrn": "12345", ...}]  // ❌ Too short
}
```
**Result**: Stored in `banks_v2_failed_requests` with `failure_type = 'validation_error'`

### Scenario 2: Stored (VM Match Failed)
```json
{
  "acknowledgement_no": "TEST005",
  "payer_account_number": "999888777666555",  // ✅ Valid format
  "incidents": [{"rrn": "9992000300123", ...}]  // ✅ Valid
  // All fields valid format
}
```
**Result**: Stored in `banks_v2_failed_requests` with `failure_type = 'vm_match_failed'`

### Scenario 3: Not Stored (Success)
```json
{
  "acknowledgement_no": "TEST006",
  "payer_account_number": "7710902234001",  // ✅ Valid AND exists
  "incidents": [{"rrn": "9992000300123", ...}]  // ✅ Valid
  // All fields valid format AND account exists
}
```
**Result**: Processed successfully, cases created, NOT stored in failed_requests

---

## Quick Decision Tree

```
Will your request be stored in failed_requests table?
├─ Does it have ANY validation error?
│   ├─ Yes → ✅ STORED (validation_error)
│   └─ No → Continue ↓
│
└─ Is the account number valid format?
    ├─ No → ✅ STORED (validation_error)
    └─ Yes → Continue ↓
        │
        └─ Does account exist in database?
            ├─ No → ✅ STORED (vm_match_failed)
            └─ Yes → ❌ NOT STORED (Processed Successfully)
```

---

## Key Points to Remember

1. **Store Everything Invalid**: All validation errors and VM match failures are stored
2. **Complete Audit Trail**: You have proof of every invalid request
3. **Valid But Non-Existent**: Valid format but account not in database = stored
4. **Cannot Be Processed = Stored**: If we can't process it, we store it
5. **No Storage = Success**: If not stored, it means it was processed successfully

---

## Table Storage Details

**Table Name**: `banks_v2_failed_requests`

**What Gets Stored**:
- Complete raw request body (as JSONB)
- Acknowledgement number
- Failure reason
- Failure type (validation_error / vm_match_failed)
- Error details
- Timestamp

**What Does NOT Get Stored**:
- Successfully processed requests
- Requests that create cases successfully

---

## Summary

**The audit table stores everything we receive but cannot process**, providing a complete audit trail for compliance and troubleshooting purposes.

