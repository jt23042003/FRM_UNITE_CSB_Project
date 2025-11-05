# Banks V2 API Documentation & VM Case Flow

## Overview
This document explains all APIs in `banks_v2.py` and how they interact with `OperationalAction.vue` for VM (Victim Match) cases.

---

## API Endpoints in `banks_v2.py`

### 1. POST `/api/v2/banks/case-entry`
**Purpose**: Main entry point for bank case ingestion. This is called when I4C sends a fraud complaint.

**Flow**:
1. **Validation**: Checks if incidents exist (1-25 incidents allowed)
2. **VM Match Check** (PRIORITY):
   - Checks if `payer_account_number` exists in `account_customer` table
   - If NO match → Returns error code "20" (No matching customer account found)
   - If MATCH found → Creates VM case IMMEDIATELY (before RRN validation)
3. **RRN Validation** (for each incident):
   - Validates RRN format (10-14 digits, numeric)
   - Validates RRN range (1 billion to 99 trillion)
   - Looks up RRN in `txn` table
   - Statuses: `matched`, `not_found`, `duplicate`, `invalid_format`, `invalid_range`, `multiple_found`
4. **Store Validation Results**:
   - Saves all validation results to `incident_validation_results` table
   - Links to VM case via `case_id`
5. **Phase 2 - Create Other Cases**:
   - PSA case (if beneficiary account matches customer)
   - ECBT cases (if customer has beneficiary + transaction exists)
   - ECBNT cases (if customer has beneficiary + NO transaction)

**Response**: Returns VM case ID, PSA case ID, ECBT/ECBNT case IDs, and transaction statuses

**Key Tables Updated**:
- `case_main_v2` (envelope data)
- `case_incidents` (raw I4C incidents)
- `case_main` (VM/PSA/ECBT/ECBNT cases)
- `incident_validation_results` (validation results per RRN)

---

### 2. GET `/api/v2/banks/case-data/{ack_no}`
**Purpose**: Get case envelope data and incidents from banks_v2 tables.

**Returns**:
- Case metadata (sub_category, requestor, payer_bank, etc.)
- Instrument details (payer_account_number, payer_mobile_number, etc.)
- All incidents (RRN, amount, transaction_date, disputed_amount, layer)
- Card details (if any)
- UPI details (if any)

**Used by**: `OperationalAction.vue` to populate I4C details section (left side)

---

### 3. GET `/api/v2/banks/incident-validations/{case_id}`
**Purpose**: **CRITICAL API for VM cases** - Returns all validation results (matched/unmatched transactions).

**Query**: Fetches from `incident_validation_results` table where `case_id = {case_id}`

**Returns**:
```json
{
  "success": true,
  "data": {
    "case_id": 123,
    "validations": [
      {
        "rrn": "1234567890",
        "validation_status": "matched",  // or "not_found", "duplicate", etc.
        "validation_message": "Transaction found and matched successfully",
        "matched_txn": {
          "txn_id": 456,
          "acct_num": "123456789",
          "bene_acct_num": "987654321",
          "amount": "5000.00",
          "txn_date": "2024-01-15",
          "txn_time": "14:30:00",
          "channel": "UPI",
          "descr": "Payment to merchant",
          "rrn": "1234567890"
        },
        "error": null
      }
    ],
    "total_incidents": 5,
    "matched_count": 3,
    "error_count": 2
  }
}
```

**Used by**: `OperationalAction.vue` to populate "Matched Bank Transactions" table (right side)

**Key Point**: This is the ONLY API that provides the matched transaction data for the VM case display.

---

### 4. GET `/api/v2/banks/victim-transactions/{account_number}`
**Purpose**: Get ALL transactions by victim account for manual review when RRNs are unmatched.

**Query**: Fetches from `txn` table where `acct_num = {account_number}` (LIMIT 100)

**Returns**:
```json
{
  "success": true,
  "data": {
    "account_number": "123456789",
    "transactions": [
      {
        "id": 789,
        "txn_date": "15-01-2024",
        "txn_time": "14:30:00",
        "acct_num": "123456789",
        "bene_acct_num": "987654321",
        "amount": "5000.00",
        "channel": "UPI",
        "rrn": "1234567890",
        "descr": "Payment"
      }
    ],
    "total_count": 50,
    "total_amount": 250000.00
  }
}
```

**Used by**: `OperationalAction.vue` to show manual review section when `hasUnmatchedRRNs = true`

---

### 5. POST `/api/v2/banks/case-entry/{ack_no}/respond`
**Purpose**: Send response to I4C when user clicks "Respond & Close Case" button.

**Request Body**:
```json
{
  "manually_selected_transactions": [
    {
      "rrn": "1234567890",
      "bene_acct_num": "987654321",
      "amount": "5000.00",
      "txn_date": "15-01-2024",
      "txn_time": "14:30:00",
      "channel": "UPI",
      "descr": "Payment",
      "acct_num": "123456789"
    }
  ]
}
```

**Process**:
1. Marks VM case as "Closed" in `case_main` table
2. Fetches all validation results for VM case
3. Builds transaction response array:
   - Includes all matched transactions (from validation results)
   - Includes manually selected transactions (for unmatched RRNs)
4. Returns detailed response with all transaction statuses

**Used by**: `OperationalAction.vue` when user clicks "Respond & Close Case"

---

### 6. GET `/api/v2/banks/transaction-details/{ack_no}`
**Purpose**: Get transaction details formatted for display (legacy endpoint, not heavily used by VM cases).

**Returns**: Formatted incident data as transactions

---

### 7. GET `/api/v2/banks/ecbt-transactions/{case_id}`
**Purpose**: Get ALL transactions between customer and beneficiary for ECBT cases (not used by VM cases).

**Used by**: ECBTAction.vue, not OperationalAction.vue

---

## VM Case Flow: How OperationalAction.vue Uses These APIs

### Step 1: Page Load (`onMounted`)
When user opens VM case page, `OperationalAction.vue` makes these API calls:

#### 1.1 Get Case Status
```javascript
GET /api/combined-case-data/{caseId}
```
- Gets case status (New/Closed)
- Gets `source_ack_no` (e.g., "ACK123_VM")

#### 1.2 Get Case Data (I4C Details)
```javascript
GET /api/v2/banks/case-data/{baseAckNo}
```
- Extracts base ack_no: `source_ack_no.replace(/_(ECBNT|ECBT|VM|PSA)$/, '')`
- Example: "ACK123_VM" → "ACK123"
- Returns: I4C complaint details, payer account, incidents list
- **Used to populate**: Left side "Customer Details - I4C" section

#### 1.3 Get Validation Results (Matched Bank Transactions)
```javascript
GET /api/v2/banks/incident-validations/{caseId}
```
- **CRITICAL API** - This is what populates the "Matched Bank Transactions" table
- Returns array of validation results with:
  - `validation_status`: "matched", "not_found", "duplicate", etc.
  - `matched_txn`: Full transaction details if matched
- **Used to populate**: Right side "Matched Bank Transactions" table

#### 1.4 Get Victim Transactions (If Unmatched RRNs Exist)
```javascript
GET /api/v2/banks/victim-transactions/{victimAccountNumber}
```
- Only called if `hasUnmatchedRRNs = true` (computed property)
- Fetches ALL transactions from victim account
- **Used to populate**: "Manual Review Required" section with checkboxes

### Step 2: Display Data
The UI shows:
- **Left**: I4C complaint incidents (raw data from I4C)
- **Right**: Matched bank transactions (from `incident-validations` API)
- **Bottom** (if needed): Manual review section with all victim transactions

### Step 3: User Action - Respond
When user clicks "Respond & Close Case":

```javascript
POST /api/v2/banks/case-entry/{baseAckNo}/respond
```

**Request includes**:
- `manually_selected_transactions`: Array of transactions user selected from manual review section

**Backend processes**:
1. Marks VM case as "Closed"
2. Fetches all validation results
3. Builds response with:
   - All matched transactions (from validation results)
   - Manually selected transactions (for unmatched RRNs)
4. Returns detailed transaction response for I4C

---

## Data Flow Diagram

```
I4C Portal
    ↓
POST /api/v2/banks/case-entry
    ↓
[VM Match Check] → Creates VM case immediately
    ↓
[RRN Validation] → Validates each incident RRN
    ↓
[Store Results] → incident_validation_results table
    ↓
[Create Other Cases] → PSA, ECBT, ECBNT cases
    ↓
Response with case IDs

─────────────────────────────────────────

OperationalAction.vue (VM Case Page)
    ↓
1. GET /api/combined-case-data/{caseId}
   → Get case status, source_ack_no
    ↓
2. GET /api/v2/banks/case-data/{baseAckNo}
   → Get I4C complaint details (left side)
    ↓
3. GET /api/v2/banks/incident-validations/{caseId}
   → Get matched bank transactions (right side) ⭐
    ↓
4. GET /api/v2/banks/victim-transactions/{accountNumber}
   → Get all victim transactions (if unmatched RRNs exist)
    ↓
User reviews and selects manual transactions
    ↓
5. POST /api/v2/banks/case-entry/{baseAckNo}/respond
   → Send response to I4C, close case
```

---

## Key Database Tables

### `incident_validation_results`
**Purpose**: Stores validation results for each RRN per case

**Columns**:
- `case_id`: Links to VM case (or PSA case)
- `rrn`: RRN from I4C incident
- `validation_status`: "matched", "not_found", "duplicate", etc.
- `validation_message`: Human-readable message
- `matched_txn_data`: JSON blob with full transaction details (if matched)
- `error_message`: Error details (if validation failed)

**Critical**: This table is the source of truth for "Matched Bank Transactions" in the UI.

### `case_incidents`
**Purpose**: Stores raw I4C incidents

**Columns**:
- `case_id`: Links to `case_main_v2`
- `rrn`: RRN from I4C
- `amount`: Transaction amount
- `transaction_date`: Date
- `transaction_time`: Time
- `disputed_amount`: Disputed amount
- `layer`: Layer number

### `case_main_v2`
**Purpose**: Stores envelope data from I4C complaint

**Columns**:
- `acknowledgement_no`: Base acknowledgement number
- `payer_account_number`: Victim account number
- `payer_mobile_number`: Victim mobile
- `sub_category`: Fraud category
- All instrument details

### `txn`
**Purpose**: Bank transaction table (source of truth for matching)

**Columns**:
- `rrn`: RRN (used for matching)
- `acct_num`: Payer account (victim)
- `bene_acct_num`: Beneficiary account
- `amount`: Transaction amount
- `txn_date`, `txn_time`: Date and time
- `channel`: Payment channel (UPI, NEFT, etc.)
- `descr`: Description

---

## Important Notes

1. **VM Case Creation**: VM case is created IMMEDIATELY when payer_account_number matches, BEFORE any RRN validation. This ensures the case exists even if all RRNs fail validation.

2. **Validation Results Storage**: All validation results are stored in `incident_validation_results` table during case entry, not computed on-the-fly. This allows the UI to show historical validation results even if the `txn` table changes later.

3. **Manual Review**: When RRNs are unmatched, the UI fetches ALL victim transactions (not just unmatched ones) so the user can manually select which transactions match.

4. **Response Flow**: When user responds, the backend combines:
   - Matched transactions (from validation results)
   - Manually selected transactions (from user input)
   - This creates a complete response for I4C

5. **Case Status**: VM case status is stored in `case_main.status` field. When status = "Closed", the UI shows read-only mode.

---

## API Summary Table

| API Endpoint | Method | Purpose | Used By VM Cases? |
|-------------|--------|---------|-------------------|
| `/api/v2/banks/case-entry` | POST | Ingest bank case | ✅ Creates VM case |
| `/api/v2/banks/case-data/{ack_no}` | GET | Get case envelope | ✅ Yes (I4C details) |
| `/api/v2/banks/incident-validations/{case_id}` | GET | Get validation results | ✅ **CRITICAL** (matched transactions) |
| `/api/v2/banks/victim-transactions/{account_number}` | GET | Get victim transactions | ✅ Yes (manual review) |
| `/api/v2/banks/case-entry/{ack_no}/respond` | POST | Send response to I4C | ✅ Yes (close case) |
| `/api/v2/banks/transaction-details/{ack_no}` | GET | Get transaction details | ❌ Legacy, not used |
| `/api/v2/banks/ecbt-transactions/{case_id}` | GET | Get ECBT transactions | ❌ For ECBT cases only |

---

## Troubleshooting

### Issue: "Matched Bank Transactions" table is empty
**Solution**: Check if `GET /api/v2/banks/incident-validations/{case_id}` returns data. Verify `incident_validation_results` table has records for this case_id.

### Issue: Manual review section not showing
**Solution**: Check if `hasUnmatchedRRNs` computed property is true. This depends on `validationResults` having entries with `validation_status !== 'matched'`.

### Issue: Respond button not working
**Solution**: Verify `sourceAckNo` is set correctly. Check backend logs for `/api/v2/banks/case-entry/{ack_no}/respond` endpoint errors.

