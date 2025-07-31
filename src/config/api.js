// src/config/api.js

// This line now dynamically reads the correct base URL from your .env files
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Centralized API endpoints (Now much cleaner!)
export const API_ENDPOINTS = {
  // Authentication
  LOGIN: `${API_BASE_URL}/login`,

  // Case Management
  CASE_ENTRY: `${API_BASE_URL}/case-entry`,
  NEW_CASE_LIST: `${API_BASE_URL}/new-case-list`,
  CASE_DETAILS: (ackno) => `${API_BASE_URL}/case/${ackno}/customer-details`,
  CASE_RISK_PROFILE: (ackno) => `${API_BASE_URL}/case/${ackno}/risk-profile`,
  CASE_TRANSACTIONS: (ackno) => `${API_BASE_URL}/case/${ackno}/transactions`,
  CASE_DOCUMENTS: (ackno) => `${API_BASE_URL}/case/${ackno}/documents`,
  CASE_UPLOAD_DOCUMENTS: (ackno) => `${API_BASE_URL}/case/${ackno}/upload-documents`,
  CASE_SEND_BACK: (ackno) => `${API_BASE_URL}/case/${ackno}/send-back`,
  CASE_OPERATIONS_STATUS: (ackno) => `${API_BASE_URL}/case/${ackno}/operations-status`,
  CASE_DECISION: (ackno) => `${API_BASE_URL}/case/${ackno}/decision`,
  CASE_ASSIGN: (ackno) => `${API_BASE_URL}/case/${ackno}/assign`,
  
  
  // File Processing
  PROCESS_BULK_FILE: `${API_BASE_URL}/process-bulk-file`,
  DOWNLOAD_ERROR_LOG: (filePath) => `${API_BASE_URL}/download-error-log/${filePath}`,
  
  // External APIs (these don't use the VITE_API_BASE_URL and are correct as they are)
  STATES_API_URL: 'https://api.countrystatecity.in/v1/countries/IN/states',
  DISTRICTS_API_URL: 'https://api.countrystatecity.in/v1/countries/IN/states/',
  IFSC_VALIDATION_API_BASE_URL: 'https://ifsc.razorpay.com/'
};