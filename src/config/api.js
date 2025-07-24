// src/config/api.js
// Dynamically sets the API base URL from Vite environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Centralized API endpoints
export const API_ENDPOINTS = {
  // Authentication
  LOGIN: `${API_BASE_URL}/api/login`,

  // Case Management
  CASE_ENTRY: `${API_BASE_URL}/api/case-entry`,
  NEW_CASE_LIST: `${API_BASE_URL}/api/new-case-list`,
  CASE_DETAILS: (ackno) => `${API_BASE_URL}/api/case/${ackno}/customer-details`,
  CASE_RISK_PROFILE: (ackno) => `${API_BASE_URL}/api/case/${ackno}/risk-profile`,
  CASE_TRANSACTIONS: (ackno) => `${API_BASE_URL}/api/case/${ackno}/transactions`,
  CASE_DOCUMENTS: (ackno) => `${API_BASE_URL}/api/case/${ackno}/documents`,
  CASE_UPLOAD_DOCUMENTS: (ackno) => `${API_BASE_URL}/api/case/${ackno}/upload-documents`,
  CASE_SEND_BACK: (ackno) => `${API_BASE_URL}/api/case/${ackno}/send-back`,
  CASE_OPERATIONS_STATUS: (ackno) => `${API_BASE_URL}/api/case/${ackno}/operations-status`,
  CASE_DECISION: (ackno) => `${API_BASE_URL}/api/case/${ackno}/decision`,
  CASE_ASSIGN: (ackno) => `${API_BASE_URL}/api/case/${ackno}/assign`,
  
  // File Processing
  PROCESS_BULK_FILE: `${API_BASE_URL}/api/process-bulk-file`,
  DOWNLOAD_ERROR_LOG: (filePath) => `${API_BASE_URL}/api/download-error-log/${filePath}`,
  
  // External APIs (these might need separate configuration)
  STATES_API_URL: 'https://api.countrystatecity.in/v1/countries/IN/states',
  DISTRICTS_API_URL: 'https://api.countrystatecity.in/v1/countries/IN/states/',
  IFSC_VALIDATION_API_BASE_URL: 'https://ifsc.razorpay.com/'
};

// Export the base URL for direct use if needed
export { API_BASE_URL }; 