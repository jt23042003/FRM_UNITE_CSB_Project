-- Create table to store failed/invalid requests for audit purposes
-- This table will store all requests that fail validation or VM matching
CREATE TABLE IF NOT EXISTS banks_v2_failed_requests (
    id SERIAL PRIMARY KEY,
    acknowledgement_no VARCHAR(50),
    raw_request_body JSONB NOT NULL,
    failure_reason TEXT NOT NULL,
    failure_type VARCHAR(50) NOT NULL, -- 'validation_error', 'vm_match_failed', 'processing_error'
    error_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    notes TEXT
);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_failed_requests_ack_no ON banks_v2_failed_requests(acknowledgement_no);
CREATE INDEX IF NOT EXISTS idx_failed_requests_created ON banks_v2_failed_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_failed_requests_type ON banks_v2_failed_requests(failure_type);
CREATE INDEX IF NOT EXISTS idx_failed_requests_resolved ON banks_v2_failed_requests(resolved);

-- Add comment to table
COMMENT ON TABLE banks_v2_failed_requests IS 'Stores all failed/invalid banks v2 requests for audit and troubleshooting purposes';

