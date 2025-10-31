## UNITE - CUB FRM Requirements: Capability Mapping and Gap Analysis

This document maps each client requirement to the current system state, with concrete references to implemented modules and endpoints, followed by gaps and feasible next steps using the existing FastAPI + PostgreSQL + Vue stack.

Legend:
- Supported: Implemented and in use
- Partially Supported: Some parts exist; more work needed
- Not Supported: Not present yet

### 1) Multiple CUB accounts under same acknowledgement number; funds to multiple CUB accounts
- Status: Partially Supported
- What works now:
  - Bank ingest v2 stores an envelope per `acknowledgement_no` in `public.case_main_v2`, and supports 1–25 incidents per ack (`backend/routers/banks_v2.py`).
  - VM case is created once per ack when payer account matches a customer.
  - Per-incident validation derives PSA/ECBT/ECBNT for all customers who saved the same beneficiary; multiple ECBT/ECBNT cases can fan out per ack (multi-customer coverage).
- Gap:
  - Explicit support for “multiple victim CUB accounts in a single email/ack” is not modeled as separate victim accounts under the same ack; current envelope assumes a single payer account.
  - Direct orchestration for “multiple CUB recipient accounts per ack” beyond ECB fan-out (e.g., consolidated lineage/graph per ack) is not formalized.
- Feasible Next Steps:
  - Extend `case_main_v2` to allow multiple payer accounts per ack (new table `case_payers_v2`), and link to VM case per payer.
  - Add a consolidated case graph endpoint for multi-account flows.

### 2) Email Processing and Case Assignment (FRM email auto-parse and actions)
- Status: Partially Supported
- What works now:
  - Email ingest implemented for Gmail Pub/Sub and Microsoft Graph; parses messages (`backend/routers/email_ingest.py`, `backend/services/email_parser.py`).
  - Endpoint can auto-create BM case and derived ECBT/ECBNT from parsed fields (`/api/email/parse/create-cases`).
  - Case assignment APIs exist (single and bulk) with logs and supervisor approval workflows (`backend/routers/assignment.py`).
- Gap:
  - Automated execution of debit freeze/credit freeze/full freeze/hold/lien in external systems (Bancs, NCCRP) is not implemented.
  - End-to-end SLA/queueing for multiple requests for the same case is basic (logs and assignments are available; no de-dup/retry orchestration).
- Feasible Next Steps:
  - Add action adapters to call Bancs/NCCRP APIs with audit logging and idempotency keys.
  - Add correlation keys by ack/account to de-duplicate repeated requests and attach to same case.

### 3) Case Initiation Module (court orders; suspicious sources like NPCI, Dark Web, card data)
- Status: Partially Supported
- What works now:
  - Generic case creation exists via `CaseEntryMatcher.insert_into_case_main` used by several flows (VM/PSA/ECB*).
  - Email ingest can seed cases from parsed inputs; manual UI supports creation via I4C entry page.
- Gap:
  - Dedicated module and UI for court-order driven case creation and branch assignment is not present.
  - Automated ingestion connectors for NPCI alerts, Dark Web, VISA/MasterCard compromised data are not present.
- Feasible Next Steps:
  - Add a “Case Initiation” router and page with sources: Court Order, NPCI, Threat Intel; minimal payload schemas → `CaseEntryData`.
  - Create tasks to fetch/import CSV/JSON feeds and map to case creation.

### 4) Search Module: Individual and Batch Mode (NCCR complaints by account; bulk queries)
- Status: Partially Supported
- What works now:
  - UI search for cases and lists is present (dashboard/list pages).
  - Backend has combined-case-data endpoints and case list/pagination.
- Gap:
  - Dedicated “NCCR complaints by account” search is not implemented.
  - Batch search (file upload or list of accounts/acks) is not implemented as a single API.
- Feasible Next Steps:
  - Add `/api/search/complaints?account=...` and `/api/search/bulk` (accept CSV/JSON of accounts/acks) to return cases and statuses.

### 5) System-Driven Escalation Protocol (auto escalation email beyond TAT)
- Status: Partially Supported
- What works now:
  - TAT thresholds defined in config; “Beyond TAT Cases” screens for super users and supervisors (`src/pages/DelayedCases.vue`).
  - No-code emails are not fired automatically.
- Gap:
  - Auto-escalation emails to matrix are not implemented.
- Feasible Next Steps:
  - Add a scheduled task (cron/APS) to compute beyond-TAT cases and send templated emails via SMTP/Graph with audit entries.

### 6) Manual Action Execution Module (sync to Bancs and NCCRP)
- Status: Not Supported
- What works now:
  - Manual action capture in UI (documents, approvals) and logging flows exist.
- Gap:
  - No live integration to update Bancs/NCCRP on manual freezes/holds/liens.
- Feasible Next Steps:
  - Build action execution adapters with transactional audit and retries; expose a queue + dashboard for status of external updates.

### 7) Fraud Investigation Template (auto fetch full context by account)
- Status: Supported
- What works now:
  - Investigation pages fetch combined case details (customer/account/transactions), incident validations, logs, templates and approvals (PSA/VM/ECB* pages).
  - Template library and supervisor review flows exist.
- Gap:
  - A single “Investigation Template” view pre-populated by simply entering any account number (outside of a case) is not implemented.
- Feasible Next Steps:
  - Add `/api/investigation/context?account=...` endpoint (reusing combined-data + txn joins) and a small UI to pre-fill the template.

### 8) Chargeback Workflow Execution (201C replacement; future IB/MB routing)
- Status: Not Supported
- What works now:
  - Case creation/closure/assignment; no chargeback workflows.
- Gap:
  - Chargeback initiation, lifecycle tracking, and issuer/acquirer hand-offs are not implemented.
- Feasible Next Steps:
  - Define `chargebacks` tables and state machine; UI to initiate from a case; optional connector to 201C (transition path) or to NPCI rails.

### 9) Customer Communication Notification Management (email/SMS with templates + delivery status)
- Status: Partially Supported
- What works now:
  - Template management and supervisor review flows exist; email ingest present. No outbound comms API in use.
- Gap:
  - Outbound email/SMS sending with delivery tracking is not implemented.
- Feasible Next Steps:
  - Add notification service (SMTP/Graph + SMS gateway) with `communications` table to store requests, status webhooks, retries, and per-case views.

### 10) NCCRP – Digital Arrest Frauds, Investment scam (fetch from MHA, auto actions)
- Status: Not Supported
- What works now:
  - No MHA/NCCRP pull integration.
- Feasible Next Steps:
  - Add MHA/NCCRP connectors (polling/webhook) → normalize to `CaseEntryData` and route to branches; reuse comms module for customer notification.

### 11) MRNL, FRI, Suspect Registry; DOT portal updates
- Status: Not Supported
- What works now:
  - Not present.
- Feasible Next Steps:
  - Add registries/tables and matching logic (we already support mobile matching MM pattern; can extend to MRNL/FRI). Build DOT portal adapter for updates with audit.

### 12) Negative Database (cross-fraud identifiers, whitelist)
- Status: Not Supported
- What works now:
  - No negative DB or cross-channel distribution.
- Feasible Next Steps:
  - Introduce `negative_identifiers` with types (account, mobile, email, VPA, device, PAN), sources, scores; add whitelist workflow; publish to CBS/IB/MB via integration bus.

### 13) MIS and Dashboard Reports (issuer/acquirer, type-wise, branch-wise, pending, EDD, state-wise, NCCRP docs pending, action-wise, staff-wise, comms, TAT, others)
- Status: Partially Supported
- What works now:
  - Analytics dashboard with case counts, types, activity trends, department KPIs; delayed/TAT UI; recent cases and deep-links.
- Gap:
  - Specific MIS slices listed (issuer/acquirer, NCCRP docs pending, staff-wise actions, comms delivery status) are not yet implemented as downloadable reports.
- Feasible Next Steps:
  - Build report endpoints with filter params; generate CSV/XLSX snapshots; add “Reports” UI with saved queries and schedules.

---

## Summary Matrix

- Supported: Investigation templates via case pages (auto context), VM/PSA/ECBT/ECBNT case creation and validation; email ingest and case creation; assignments, approvals, logs; dashboards and delayed (TAT) views.
- Partially Supported: Multi-account per ack (fan-out to ECBT/ECBNT is present; multiple victim accounts per ack needs schema/UI), email-to-action orchestration, search (NCCR by account; bulk), escalation emails, outbound comms with templates, MIS reporting breadth.
- Not Supported: Bancs/NCCRP action updates, Chargeback workflow, NCCRP/MHA ingestion, MRNL/FRI/Suspect registry + DOT updates, Negative Database, formal bulk search, automated external escalations and delivery tracking.

## Why this is feasible

The current platform already centralizes case lifecycles (FastAPI), stores rich structures in PostgreSQL, and renders operational analytics in Vue. Adding adapters (Bancs, NCCRP, MHA, DOT, SMS) and new modules (negative DB, chargebacks, reports) is incremental and aligns with existing patterns: routers, services, audit logs, background executor, and structured tables.

## Immediate Next Steps (recommended)
1. Outbound Communications Module (email/SMS) with templates, status tracking, and webhooks.
2. Auto Escalation Scheduler using existing TAT thresholds; send emails to escalation matrix.
3. Search APIs: NCCR-by-account and bulk search ingest.
4. Action Adapters for Bancs/NCCRP; start with “record-only” dry-run to validate payloads; then enable live.
5. Reports API and UI (CSV/XLSX) for the requested MIS slices.
6. Extend bank ingest to support multiple payer accounts per ack (schema + UI adjustments).


