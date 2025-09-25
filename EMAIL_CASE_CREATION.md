# Email-Based Automatic Case Creation System

## Overview

This system automatically creates fraud cases based on parsed email data from risk officers. The workflow assumes that email contains information about beneficiary (BM) accounts and automatically triggers:

1. **BM Case Creation** - For beneficiary accounts that exist in our customer database
2. **ECBT/ECBNT Case Creation** - For existing customers who have added the beneficiary account

## Implementation

### New Endpoint: `/api/email/parse/create-cases`

**Method:** POST

**Request Payload:**
```json
{
  "provider": "google",        // or "microsoft"  
  "message_id": "19977059b311c62a"
}
```

**Response:**
```json
{
  "id": "19977059b311c62a",
  "provider": "google",
  "parsed_fields": {
    // All extracted fields from email
    "ackNo": "ACK202509230001",
    "toAccount": "987654321098",  // This is the beneficiary account
    "accountNumber": "123456789012", // This is the victim account
    // ... other fields
  },
  "evidence": {
    // Evidence with confidence scores
  },
  "case_creation_results": {
    "bm_case": {
      "account_number": "987654321098",
      "customer_id": "CUST123",
      "case_result": {
        "message": "Case entry 'ACK202509230001' processed..."
      }
    },
    "ecb_cases": [
      {
        "customer_id": "CUST456",
        "customer_account": "111222333444",
        "beneficiary_account": "987654321098",
        "case_type": "ECBT",  // or "ECBNT"
        "has_transactions": true,
        "case_result": {
          "ack_no": "ECBT_ACK202509230001_CUST456_1695123456",
          "case_id": 789,
          "message": "ECBT case created successfully."
        }
      }
    ],
    "errors": [],
    "summary": "Created BM case for beneficiary account 987654321098. Found 1 ECB cases."
  }
}
```

## Case Creation Logic

### 1. BM Case Creation
- Extract `toAccount` (beneficiary account) from parsed email
- Check if this account exists in `account_customer` table
- If found, create a **BM case** using existing `CaseEntryMatcher.match_data()`

### 2. ECBT/ECBNT Case Creation
- Find all customers who have added this beneficiary account in `acc_bene` table
- For each customer:
  - Check if they have transactions with this beneficiary in `txn` table
  - **ECBT** = Customer has transactions with beneficiary
  - **ECBNT** = Customer has beneficiary added but no transactions
- Create cases using existing `CaseEntryMatcher.create_ecb_case()`

## Database Tables Used

1. **account_customer**: Links customer IDs to account numbers
2. **acc_bene**: Stores beneficiary relationships (customer → beneficiary accounts)  
3. **txn**: Transaction history between customers and beneficiaries
4. **case_main**: Primary case storage table
5. **customer**: Customer details for matching

## Key Features

- **Email Parsing**: Extracts fraud case details using AI/regex from email content
- **Automatic Matching**: Matches beneficiary accounts against customer database
- **Multi-Case Creation**: Creates BM + multiple ECBT/ECBNT cases in one operation
- **Evidence Tracking**: Maintains confidence scores for extracted data
- **Error Handling**: Comprehensive error tracking and reporting

## Usage Example

```bash
# Test the endpoint
curl -X POST http://localhost:8000/api/email/parse/create-cases \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "message_id": "19977059b311c62a"
  }'
```

## Original Email Parsing Flow (Unchanged)

The existing `/email/parse/preview` endpoint remains unchanged for just viewing parsed data without creating cases.

## Prerequisites

1. **Poppler Utils**: Required for PDF processing
   ```bash
   brew install poppler  # macOS
   ```

2. **Environment Variables**: 
   - `DEV_GOOGLE_ACCESS_TOKEN`: Google OAuth token
   - `DEV_GOOGLE_EMAIL`: Email address

3. **Database Setup**: All case management tables must be created

## Error Handling

- Invalid provider/message_id → 400 Bad Request
- Missing OAuth token → 400 Bad Request  
- Database errors → 500 Internal Server Error with details
- No beneficiary account found → Success with no cases created
- Parsing errors → Captured in case_creation_results.errors

## Case Types Created

- **BM**: Beneficiary/Mule account case
- **ECBT**: Existing Customer Beneficiary with Transactions
- **ECBNT**: Existing Customer Beneficiary No Transactions

All cases are created with `is_operational=False` (Stage 2 cases) and automatically assigned to risk officers.

## Files Modified

- `/backend/routers/email_ingest.py`: Added new endpoint and case creation logic
- Uses existing services: `EmailParser`, `CaseEntryMatcher`, `ECBCaseData`

This system enables risk officers to send emails and automatically have fraud cases created based on the extracted information, significantly reducing manual case entry overhead.
