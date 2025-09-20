-- Performance optimization indexes for faster query execution
-- Run these SQL commands on your database to improve performance

-- Index for case_main queries (most important for dashboard and case loading)
CREATE INDEX IF NOT EXISTS idx_case_main_creation_date_desc ON public.case_main (creation_date DESC, creation_time DESC);
CREATE INDEX IF NOT EXISTS idx_case_main_status ON public.case_main (status);
CREATE INDEX IF NOT EXISTS idx_case_main_source_ack_no ON public.case_main (source_ack_no);
CREATE INDEX IF NOT EXISTS idx_case_main_cust_id ON public.case_main (cust_id);
CREATE INDEX IF NOT EXISTS idx_case_main_acc_num ON public.case_main (acc_num);

-- Index for assignment queries (critical for role-based filtering)
CREATE INDEX IF NOT EXISTS idx_assignment_case_id_active ON public.assignment (case_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_assignment_assigned_to ON public.assignment (assigned_to) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_assignment_assign_date_desc ON public.assignment (assign_date DESC, assign_time DESC);
-- NEW: Critical index for assigned-cases API performance
CREATE INDEX IF NOT EXISTS idx_assignment_assigned_by_active ON public.assignment (assigned_by, is_active, assignment_type) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_assignment_case_id_assigned_by ON public.assignment (case_id, assigned_by, assigned_to);

-- Index for user_table queries (for cached user type lookups)
CREATE INDEX IF NOT EXISTS idx_user_table_user_name ON user_table (user_name);

-- Index for customer table (for JOINs in optimized combined data query)
CREATE INDEX IF NOT EXISTS idx_customer_cust_id ON customer (cust_id);

-- Index for account table (for JOINs in optimized combined data query)
CREATE INDEX IF NOT EXISTS idx_account_acc_num ON account (acc_num);

-- Index for transactions (for case detail transaction loading)
CREATE INDEX IF NOT EXISTS idx_txn_acct_num_date ON txn (acct_num, txn_date DESC, txn_time DESC);
CREATE INDEX IF NOT EXISTS idx_txn_bene_acct_num ON txn (bene_acct_num);

-- Index for case history (for case detail loading)
CREATE INDEX IF NOT EXISTS idx_case_history_case_id_time ON public.case_history (case_id, created_time DESC);

-- Index for case documents (for case detail loading)
CREATE INDEX IF NOT EXISTS idx_case_documents_case_id_time ON public.case_documents (case_id, uploaded_at DESC);

-- Index for case_entry_form (for I4C data lookup)
CREATE INDEX IF NOT EXISTS idx_case_entry_form_ack_no ON case_entry_form (ack_no);

-- Composite index for dashboard role-based queries
CREATE INDEX IF NOT EXISTS idx_case_main_assignment_dashboard ON public.case_main (status, creation_date DESC) 
    INCLUDE (case_id, source_ack_no, case_type, creation_time);

-- Index for account_customer lookups (used in matching logic)
CREATE INDEX IF NOT EXISTS idx_account_customer_acc_num ON account_customer (acc_num);
CREATE INDEX IF NOT EXISTS idx_account_customer_cust_id ON account_customer (cust_id);

-- Index for acc_bene lookups (used in beneficiary matching)
CREATE INDEX IF NOT EXISTS idx_acc_bene_cust_acct_num ON acc_bene (cust_acct_num);
CREATE INDEX IF NOT EXISTS idx_acc_bene_bene_acct_num ON acc_bene (bene_acct_num);

-- Analyze tables after creating indexes to update statistics
ANALYZE public.case_main;
ANALYZE public.assignment;
ANALYZE user_table;
ANALYZE customer;
ANALYZE account;
ANALYZE txn;
ANALYZE public.case_history;
ANALYZE public.case_documents;
ANALYZE case_entry_form;
ANALYZE account_customer;
ANALYZE acc_bene;

-- Optional: Create partial indexes for active cases only (if most queries are for active cases)
-- CREATE INDEX IF NOT EXISTS idx_case_main_active_status ON public.case_main (creation_date DESC, creation_time DESC) 
--     WHERE status IN ('New', 'Assigned');

-- Optional: Create expression index for case type matching (if you frequently query by case type patterns)
-- CREATE INDEX IF NOT EXISTS idx_case_main_case_type_pattern ON public.case_main (case_type) 
--     WHERE case_type IN ('VM', 'BM', 'ECBT', 'ECBNT', 'NAB', 'PSA');

-- PERFORMANCE OPTIMIZATION INDEXES FOR BULK PROCESSING
-- These indexes significantly improve query performance for bulk file uploads

-- Account customer lookups (most critical for bulk processing)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_account_customer_acc_num_hash 
ON account_customer USING hash(acc_num);

-- Case main table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_case_main_source_ack_no 
ON case_main(source_ack_no);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_case_main_creation_date 
ON case_main(creation_date DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_case_main_case_type 
ON case_main(case_type);

-- Optimize transaction lookups for ECB case creation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_txn_acct_bene_date 
ON txn(acct_num, bene_acct_num, txn_date);

-- Additional performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_case_main_cust_id 
ON case_main(cust_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_case_main_status 
ON case_main(status);

-- Assignment table indexes for case assignment operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignment_case_id 
ON assignment(case_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignment_assigned_to 
ON assignment(assigned_to);

-- Case history indexes for logging operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_case_history_case_id 
ON case_history(case_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_case_history_updated_at 
ON case_history(updated_at DESC);

COMMIT;
