# Banks v2 API - Data Flow Diagram

## Overview
This document describes the complete data flow for the Banks v2 API (`/api/v2/banks/case-entry`), which ingests fraud case data from banks and creates multiple case types (VM, PSA, ECBT, ECBNT) based on bank transaction matching.

---

## 1. API Entry Point

```
POST /api/v2/banks/case-entry
└─> Input: CaseEntryV2 (JSON Payload)
    ├─ acknowledgement_no: str
    ├─ sub_category: str
    ├─ instrument: InstrumentData
    │   ├─ requestor: str
    │   ├─ payer_bank: str
    │   ├─ payer_bank_code: int
    │   ├─ mode_of_payment: str
    │   ├─ payer_mobile_number: str
    │   ├─ payer_account_number: str ⚠️ **KEY FIELD FOR VM MATCH**
    │   ├─ state: str
    │   ├─ district: str
    │   ├─ transaction_type: str (optional)
    │   └─ wallet: str (optional)
    └─ incidents: List[IncidentData]
        └─ Each incident contains:
            ├─ amount: str
            ├─ rrn: str ⚠️ **KEY FIELD FOR TRANSACTION MATCHING**
            ├─ transaction_date: str
            ├─ transaction_time: str (optional)
            ├─ disputed_amount: str
            └─ layer: int
```

---

## 2. Phase 1: Initial Data Storage & VM Case Creation

### 2.1 Upsert to case_main_v2 Table

```
┌─────────────────────────────────────────────────────────┐
│ PHASE 1: Data Storage & Validation                      │
└─────────────────────────────────────────────────────────┘

Step 1: Upsert Case Data
├─> INSERT INTO case_main_v2
    │   ├─ acknowledgement_no (unique)
    │   ├─ sub_category
    │   ├─ requestor
    │   ├─ payer_bank
    │   ├─ payer_bank_code
    │   ├─ mode_of_payment
    │   ├─ payer_mobile_number
    │   ├─ payer_account_number ⚠️ **KEY**
    │   ├─ state
    │   ├─ district
    │   ├─ transaction_type
    │   └─ wallet
    │
    └─> Returns: case_id
```

### 2.2 VM (Victim Match) Case Creation - **PRIORITY**

```
Step 2: VM Match Check (HAPPENS BEFORE RRN VALIDATION)
├─> Query: SELECT cust_id FROM account_customer 
    │         WHERE acc_num = payer_account_number
    │
    ├─> ❌ IF NO MATCH FOUND:
    │   └─> Return Error 20: "No matching customer account found"
    │       └─> STOP PROCESSING (No further cases created)
    │
    └─> ✅ IF MATCH FOUND:
        ├─> Get: victim_cust_id
        ├─> CREATE VM CASE IMMEDIATELY:
        │   ├─> INSERT INTO case_main
        │   │   ├─ case_type = "VM"
        │   │   ├─ source_ack_no = "{ack_no}_VM"
        │   │   ├─ cust_id = victim_cust_id
        │   │   ├─ acc_num = payer_account_number
        │   │   ├─ is_operational = true
        │   │   └─ status = "New"
        │   │
        │   ├─> INSERT INTO case_details_1
        │   │   ├─ cust_id = victim_cust_id
        │   │   ├─ casetype = "VM"
        │   │   ├─ acc_no = payer_account_number
        │   │   └─ match_flag = "VM Match"
        │   │
        │   └─> Returns: vm_case_id
        │
        └─> Continue to Incident Processing
```

---

## 3. Incident Processing & Transaction Matching

### 3.1 For Each Incident (RRN-based Processing)

```
┌────────────────────────────────────────────────────────────────┐
│ INCIDENT PROCESSING LOOP (for each incident)                   │
└────────────────────────────────────────────────────────────────┘

For each incident in payload.incidents:

Step 1: Duplicate Check
├─> Query: SELECT case_id FROM case_incidents WHERE rrn = {rrn}
    │
    ├─> ❌ IF DUPLICATE: 
    │   ├─> Mark as "duplicate" status
    │   ├─> Store incident with error
    │   └─> Skip to next incident
    │
    └─> ✅ IF UNIQUE:
        └─> Continue to Step 2

Step 2: Store Incident
├─> INSERT INTO case_incidents
    │   ├─ case_id
    │   ├─ amount
    │   ├─ rrn
    │   ├─ transaction_date
    │   ├─ transaction_time
    │   ├─ disputed_amount
    │   └─ layer
    │
    └─> Continue to RRN Validation

Step 3: RRN Format Validation
├─> Check: rrn_is_numeric_and_length(rrn)
    │   └─> Must be 10-14 digits
    │
    ├─> ❌ IF INVALID FORMAT:
    │   ├─> Status: "invalid_format"
    │   └─> Error Code: "02"
    │
    └─> ✅ IF VALID:
        └─> Continue to Step 4

Step 4: RRN Range Validation
├─> Check: rrn_in_range(rrn)
    │   └─> Must be 1,000,000,000 to 99,999,999,999,999
    │
    ├─> ❌ IF INVALID RANGE:
    │   ├─> Status: "invalid_range"
    │   └─> Error Code: "03"
    │
    └─> ✅ IF VALID:
        └─> Continue to Transaction Lookup

Step 5: Transaction Table Lookup ⚠️ **CRITICAL MATCHING STEP**
├─> Query: SELECT * FROM txn WHERE rrn = {rrn}
    │
    ├─> ❌ IF NO MATCH (0 rows):
    │   ├─> Status: "not_found"
    │   └─> Error Code: "01"
    │
    ├─> ❌ IF MULTIPLE MATCHES (>1 row):
    │   ├─> Status: "multiple_found"
    │   └─> Error Code: "15"
    │
    └─> ✅ IF EXACTLY 1 MATCH (SUCCESS):
        ├─> Get transaction details:
        │   ├─ acct_num (customer account)
        │   ├─ bene_acct_num (beneficiary account) ⚠️ **KEY**
        │   ├─ amount
        │   ├─ txn_date
        │   ├─ txn_time
        │   ├─ channel
        │   └─ descr
        │
        └─> Continue to PSA/ECBT/ECBNT Logic
```

### 3.2 PSA (Payee/Accepting Account) Check

```
Step 6: PSA Check (for each matched transaction)
├─> Query: SELECT cust_id FROM account_customer 
    │         WHERE acc_num = bene_acct_num
    │
    ├─> ❌ IF NO MATCH:
    │   └─> PSA = False
    │
    └─> ✅ IF MATCH FOUND:
        ├─> Get: bene_cust_id
        ├─> PSA = True
        └─> Flag for PSA case creation
```

### 3.3 ECBT/ECBNT Logic (Existing Customer Beneficiary)

```
Step 7: ECBT/ECBNT Check ⚠️ **MOST COMPLEX LOGIC**
├─> Query: SELECT ab.cust_acct_num, ab.bene_acct_num, ac.cust_id
    │         FROM acc_bene ab
    │         JOIN account_customer ac 
    │           ON ab.cust_acct_num = ac.acc_num
    │         WHERE ab.bene_acct_num = {bene_acct_num}
    │
    ├─> ✅ IF MULTIPLE MATCHES FOUND (customers who have this beneficiary):
    │   │
    │   └─> For EACH customer who has this beneficiary:
    │       │
    │       ├─> Get: ecb_cust_acct_num
    │       ├─> Get: ecb_cust_id
    │       │
    │       ├─> Check if transaction exists:
    │       │   Query: SELECT 1 FROM txn 
    │       │          WHERE acct_num = {ecb_cust_acct_num} 
    │       │            AND bene_acct_num = {bene_acct_num}
    │       │
    │       ├─> ✅ IF TRANSACTION EXISTS:
    │       │   ├─> ECBT = True (Existing Customer Beneficiary with Transaction)
    │       │   └─> Flag for ECBT case creation
    │       │
    │       └─> ❌ IF NO TRANSACTION:
    │           ├─> ECBNT = True (Existing Customer Beneficiary with No Transaction)
    │           └─> Flag for ECBNT case creation
    │
    └─> ❌ IF NO MATCHES:
        └─> No ECBT/ECBNT cases created
```

### 3.4 Action Deferral

```
Step 8: Create Deferred Actions
├─> Build action list:
    │   ├─ rrn
    │   ├─ bene_cust_id (for PSA)
    │   ├─ bene_acc
    │   ├─ psa: boolean
    │   ├─ ecbt: boolean
    │   ├─ ecbnt: boolean
    │   ├─ ecb_cust_id: str (for ECBT/ECBNT)
    │   ├─ ecb_cust_acct_num: str (for ECBT/ECBNT)
    │   └─ ecb_bene_acct_num: str (for ECBT/ECBNT)
    │
    └─> Defer case creation to Phase 2 (after all incidents processed)
```

### 3.5 Store Validation Results

```
Step 9: Store Incident Validation Results
├─> INSERT INTO incident_validation_results
    │   ├─ case_id (vm_case_id)
    │   ├─ rrn
    │   ├─ validation_status
    │   ├─ validation_message
    │   ├─ matched_txn_data (JSON)
    │   └─ error_message
    │
    └─> Link to VM case for frontend retrieval
```

---

## 4. Phase 2: PSA/ECBT/ECBNT Case Creation

### 4.1 Deduplication

```
┌─────────────────────────────────────────────────────────┐
│ PHASE 2: PSA/ECBT/ECBNT Case Creation                   │
└─────────────────────────────────────────────────────────┘

Step 1: Deduplicate Actions
├─> For each action in deferred_actions:
    │
    ├─> IF ECBT/ECBNT action:
    │   ├─> Create unique key: "{ecb_cust_id}_{ecb_bene_acct_num}"
    │   └─> Merge duplicate keys (avoid multiple cases for same customer-beneficiary)
    │
    └─> IF PSA action:
        └─> Create unique key: "psa_{rrn}"
```

### 4.2 PSA Case Creation

```
Step 2: Create PSA Case (if applicable)
├─> IF action["psa"] == True:
    │
    ├─> INSERT INTO case_main
    │   ├─ case_type = "PSA"
    │   ├─ source_ack_no = "{ack_no}_PSA"
    │   ├─ cust_id = bene_cust_id
    │   ├─ acc_num = bene_acc
    │   ├─ is_operational = true
    │   ├─ status = "New"
    │   └─ source_bene_accno = bene_acc
    │
    ├─> INSERT INTO case_details_1
    │   ├─ cust_id = bene_cust_id
    │   ├─ casetype = "PSA"
    │   ├─ acc_no = bene_acc
    │   └─ match_flag = "PSA Match"
    │
    └─> Store validation results linked to PSA case
```

### 4.3 ECBT Case Creation (Multiple Possible)

```
Step 3: Create ECBT Cases (if applicable)
└─> For each action where ecbt == True:
    
    ├─> Build ECBCaseData payload:
    │   ├─ sourceAckNo = "{ack_no}_ECBT_{ecb_cust_id}_{ecb_bene_acct_num}"
    │   ├─ customerId = ecb_cust_id
    │   ├─ customerAccountNumber = ecb_cust_acct_num
    │   ├─ beneficiaryAccountNumber = ecb_bene_acct_num
    │   ├─ hasTransaction = True
    │   └─ remarks = "Automated ECBT case from bank ingest"
    │
    ├─> Call: matcher.create_ecb_case(ecb_payload)
    │   │
    │   └─> Creates ECBT case in case_main table
    │
    └─> Track: ecbt_case_ids.append(ecbt_case_id)
```

### 4.4 ECBNT Case Creation (Multiple Possible)

```
Step 4: Create ECBNT Cases (if applicable)
└─> For each action where ecbnt == True:
    
    ├─> Build ECBCaseData payload:
    │   ├─ sourceAckNo = "{ack_no}_ECBNT_{ecb_cust_id}_{ecb_bene_acct_num}"
    │   ├─ customerId = ecb_cust_id
    │   ├─ customerAccountNumber = ecb_cust_acct_num
    │   ├─ beneficiaryAccountNumber = ecb_bene_acct_num
    │   ├─ hasTransaction = False
    │   └─ remarks = "Automated ECBNT case from bank ingest"
    │
    ├─> Call: matcher.create_ecb_case(ecbn_payload)
    │   │
    │   └─> Creates ECBNT case in case_main table
    │
    └─> Track: ecbnt_case_ids.append(ecbnt_case_id)
```

---

## 5. Response Generation

### 5.1 Final Response

```
┌──────────────────────────────────────────────────────────┐
│ API RESPONSE                                              │
└──────────────────────────────────────────────────────────┘

{
  "meta": {
    "response_code": "00",
    "response_message": "Success"
  },
  "data": {
    "acknowledgement_no": "{ack_no}",
    "job_id": "BANKS-{uuid}",
    "vm_case_id": 123,          // ⚠️ Always created if payer_account matches
    "psa_case_id": 124,          // Created if bene_acct_num matches customer
    "ecbt_case_ids": [125, 126], // Multiple possible (one per matched customer)
    "ecbnt_case_ids": [127, 128] // Multiple possible (one per matched customer)
  },
  "transactions": [
    {
      "rrn_transaction_id": "9992000300",
      "status_code": "00",              // Success codes: 00
      "response_message": "SUCCESS",    //     Error codes: 01, 02, 03, etc.
      "payee_account_number": "9990234567899999",
      "amount": "15000.00",
      "transaction_datetime": "2025-10-20 14:15:00",
      "root_account_number": "7710902234001",
      "root_rrn_transaction_id": "9992000300",
      "psa_case_id": 124,
      "ecbt_case_ids": [125],
      "ecbnt_case_ids": [127]
    }
    // ... more transactions
  ]
}
```

---

## 6. Database Tables Used

### 6.1 Input Storage Tables

```
case_main_v2
├─ Stores: Instrument data from bank
└─ Fields: acknowledgement_no, payer_account_number, sub_category, etc.

case_incidents
├─ Stores: Individual incidents (RRNs) from bank
└─ Fields: case_id, rrn, amount, transaction_date, etc.

incident_validation_results
├─ Stores: Validation results for each incident
└─ Fields: case_id, rrn, validation_status, matched_txn_data
```

### 6.2 Reference Lookup Tables

```
account_customer
├─ Purpose: Match payer_account_number to find victim customer
├─ Purpose: Match bene_acct_num to find PSA customer
└─ Fields: acc_num → cust_id

txn
├─ Purpose: Match RRN to find actual transaction details
└─ Fields: rrn, acct_num, bene_acct_num, amount, etc.

acc_bene
├─ Purpose: Find all customers who have added a specific beneficiary
└─ Fields: cust_acct_num, bene_acct_num
```

### 6.3 Output Case Tables

```
case_main
├─ Stores: VM case (victim)
├─ Stores: PSA case (payee)
├─ Stores: ECBT cases (customers with transactions)
└─ Stores: ECBNT cases (customers without transactions)
└─ Fields: case_id, case_type, cust_id, acc_num, etc.

case_details_1
├─ Stores: Additional case details
└─ Fields: cust_id, casetype, acc_no, match_flag
```

---

## 7. Case Type Definitions

### 7.1 VM (Victim Match)

```
Condition: payer_account_number matches account_customer.acc_num
├─ victim_cust_id = cust_id from account_customer
└─ CREATE 1 VM case for the victim
```

### 7.2 PSA (Payee/Accepting Account)

```
Condition: bene_acct_num from txn matches account_customer.acc_num
├─ bene_cust_id = cust_id from account_customer
└─ CREATE 1 PSA case
```

### 7.3 ECBT (Existing Customer Beneficiary with Transaction)

```
Condition: 
├─ Customer has added bene_acct_num as beneficiary (in acc_bene)
└─ Transaction exists between customer and bene_acct_num (in txn)
   └─ CREATE multiple ECBT cases (one per customer who matches)
```

### 7.4 ECBNT (Existing Customer Beneficiary with No Transaction)

```
Condition:
├─ Customer has added bene_acct_num as beneficiary (in acc_bene)
└─ NO transaction exists between customer and bene_acct_num (in txn)
   └─ CREATE multiple ECBNT cases (one per customer who matches)
```

---

## 8. Decision Tree

```
                    INGEST REQUEST
                           │
                           ▼
                  ┌─────────────────┐
                  │ payer_account_number │
                  │    matches customer? │
                  └─────────────────┘
                           │
                  ┌────────┴────────┐
                  │                 │
              NO  │                 │  YES
                  │                 │
                  ▼                 ▼
            Return Error 20    CREATE VM Case
                  │                 │
                  │                 ▼
                  │        Process Each Incident
                  │                 │
                  │                 ▼
                  │        ┌────────────────┐
                  │        │ RRN exists in txn? │
                  │        └────────────────┘
                  │                 │
                  │        ┌────────┴────────┐
                  │        │                 │
                  │     NO │                 │  YES (1 match)
                  │        │                 │
                  │        ▼                 ▼
                  │   Error Code 01    Get bene_acct_num
                  │                      ├─ Check PSA (bene_acct_num → customer?)
                  │                      └─ Check ECBT/ECBNT (acc_bene lookup)
                  │
                  └─────────────────────────┘
                           │
                           ▼
                    CREATE CASES:
                    ├─ VM (1 case)
                    ├─ PSA (1 case if match)
                    ├─ ECBT (N cases - one per matched customer)
                    └─ ECBNT (M cases - one per matched customer)
                           │
                           ▼
                      Return Response
```

---

## 9. Key Field Mapping

### From Bank Payload → Database Lookups → Cases

```
INSTRUMENT
└─ payer_account_number
   ├─> Lookup: account_customer.acc_num
   └─> Result: vict

im_cust_id
      └─> CREATE: VM case

INCIDENTS (Each RRN)
└─ rrn
   ├─> Lookup: txn.rrn
   │   │
   │   ├─> Get: acct_num (payer account)
   │   ├─> Get: bene_acct_num (payee account) ⚠️
   │   │   │
   │   │   ├─> Lookup: account_customer.acc_num = bene_acct_num
   │   │   │   └─> CREATE: PSA case
   │   │   │
   │   │   └─> Lookup: acc_bene.bene_acct_num = bene_acct_num
   │   │       │
   │   │       ├─> For each customer in results:
   │   │       │   │
   │   │       │   ├─> Check: txn WHERE acct_num = cust_acct AND bene_acct = bene_acct
   │   │       │   │
   │   │       │   ├─> IF transaction exists:
   │   │       │   │   └─> CREATE: ECBT case
   │   │       │   │
   │   │       │   └─> IF no transaction:
   │   │       │       └─> CREATE: ECBNT case
   │   │       │
   │   │       └─> Result: Multiple ECBT/ECBNT cases possible
   │   │
   │   └─> Result: One PSA + Multiple ECBT/ECBNT cases
   │
   └─> Result: Complete set of cases for fraud investigation
```

---

## 10. Endpoints Reference

### Main Ingestion
- `POST /api/v2/banks/case-entry` - Ingest bank data, create cases

### Data Retrieval
- `GET /api/v2/banks/case-data/{ack_no}` - Get case data from case_main_v2
- `GET /api/v2/banks/transaction-details/{ack_no}` - Get transaction details
- `GET /api/v2/banks/victim-transactions/{account_number}` - Get all victim transactions
- `GET /api/v2/banks/incident-validations/{case_id}` - Get validation results
- `GET /api/v2/banks/ecbt-transactions/{case_id}` - Get ECBT transactions

### Response
- `POST /api/v2/banks/case-entry/{ack_no}/respond` - Send response back to bank

---

## 11. Error Codes Reference

```
00  - Success
01  - Record not found
02  - Invalid RRN format
03  - Invalid RRN range
04  - Invalid incidents count (>25)
11  - Structure validation failed
15  - Multiple Records Found
16  - Duplicate RRN
20  - No matching customer account found (VM fail)
31  - Pending
32  - Failure (generic DB error)
99  - Internal error
```

---

## Summary

The Banks v2 API follows this flow:

1. **Input**: Bank sends payload with payer account + incidents (RRNs)
2. **Storage**: Upsert to case_main_v2, store incidents to case_incidents
3. **VM Check**: Match payer_account_number → if NO match, return error 20
4. **VM Case**: CREATE victim case immediately
5. **For Each Incident**: Lookup RRN in txn table
   - If not found → Error 01
   - If found → Check PSA/ECBT/ECBNT
6. **Phase 2**: CREATE PSA + ECBT/ECBNT cases (if applicable)
7. **Response**: Return case IDs + transaction details

The system can create **1 VM + 1 PSA + N ECBT + M ECBNT** cases from a single bank ingest request.

