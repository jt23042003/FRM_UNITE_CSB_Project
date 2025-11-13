# Email Case Creation - Explanation of Multiple Cases

## Expected Behavior

When an email contains:
- **1 mobile number**: `4904099076`
- **1 account number**: `1155084761231503`

The system should:
1. **Match mobile** → Find customer → Create **1 PSA case** → Run ECB flow → Create ECB cases
2. **Match account** → Find customer → Create **1 PSA case** → Run ECB flow → Create ECB cases

**Total Expected**: 2 PSA cases (one per customer) + ECB cases for each customer

## What Actually Happened

From your email, the system created:
- **2 PSA cases** (Case IDs: 1935, 1936) - Both for customer `CUST112403`
- **2 ECBT cases** (Case IDs: 1937, 1938) - Both for customer `CUST112403`
- **2 ECBNT cases** (Case IDs: 1939, 1940) - Both for customer `CUST112403`

**Total Created**: 6 cases, all for the same customer `CUST112403`

## Root Cause Analysis

### Issue 1: Account Number Matching Failed

The account number `1155084761231503` from your email **should** match customer `CUST103841` (different from the mobile match), but **all 6 cases are for `CUST112403`**.

This suggests:
- The account number wasn't properly extracted from the email by n8n
- The account number matching logic failed
- The account number was sent with incorrect formatting (e.g., "Account No : 1155084761231503" wasn't normalized)

### Issue 2: ECB Flow Creates Cases for ALL Beneficiaries

The ECB (Existing Customer Beneficiary) flow works as follows:

1. **Gets ALL accounts** for the matched customer
2. **For EACH account**, finds ALL beneficiaries
3. **For EACH beneficiary**, creates either:
   - **ECBT** case (if transactions exist)
   - **ECBNT** case (if no transactions)

**Example**: Customer `CUST112403` has account `6171995905977901` with 2 beneficiaries:
- Beneficiary 1 (`987654321024031`): Has 1 transaction → Creates **ECBT** case
- Beneficiary 2 (`987654321024032`): Has 0 transactions → Creates **ECBNT** case

So from **1 mobile match**, you get:
- 1 PSA case
- 1 ECBT case (for beneficiary 1)
- 1 ECBNT case (for beneficiary 2)

### Issue 3: Duplicate Processing

The fact that you have **2 PSA cases** and **2 sets of ECB cases** (2 ECBT + 2 ECBNT) suggests the entire flow ran **twice** for the same customer.

**Possible causes:**
1. n8n workflow sent duplicate HTTP requests
2. The account number matching found the same customer somehow
3. There's a bug causing duplicate processing

## Database Evidence

```
Mobile 4904099076 → Matches CUST112403
Account 1155084761231503 → Should match CUST103841 (but didn't)

CUST112403 has:
- 3 accounts: 6171995905977901, 8085243386484585, 4187424643890063
- Account 6171995905977901 has 2 beneficiaries:
  * Beneficiary 1: Has transactions → ECBT
  * Beneficiary 2: No transactions → ECBNT
```

## Recommendations

### 1. Fix Account Number Extraction in n8n
Ensure the n8n workflow properly extracts and normalizes account numbers from emails. The account number should be sent as a clean numeric string (e.g., `"1155084761231503"`), not with prefixes like `"Account No : 1155084761231503"`.

### 2. Add Logging
Add detailed logging to track:
- Which mobile/account numbers were received
- Which customers were matched
- Why account number matching failed (if it did)

### 3. Prevent Duplicate Processing
Add idempotency checks to prevent the same customer from being processed twice in a single request.

### 4. Consider Limiting ECB Cases
If you only want ECB cases for the **matched account** (not all accounts), we need to modify the ECB flow to accept a specific account number filter.

## Next Steps

1. **Check n8n workflow logs** to see what data was actually sent to the API
2. **Verify account number extraction** - ensure `1155084761231503` was properly extracted and sent
3. **Check for duplicate HTTP requests** from n8n
4. **Review the account matching logic** to see why it didn't find `CUST103841`

Would you like me to:
- Add detailed logging to track what's happening?
- Modify the ECB flow to only create cases for the matched account (not all accounts)?
- Add duplicate prevention logic?

