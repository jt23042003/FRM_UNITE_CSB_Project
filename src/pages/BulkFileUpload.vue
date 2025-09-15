<template>
  <div class="page-container">
    <h1 class="screen-header">Bulk Complaint Processing</h1>
    
    <div class="upload-card">
      <h2 class="card-title">Upload I4C File</h2>
      <p class="card-subtitle">
        Select a file containing an array of complaint records. The system will process each record individually.
      </p>

      <div 
        class="file-input-area"
        :class="{ 'uploading': isLoading }"
        @dragover.prevent
        @drop.prevent="handleFileDrop"
      >
        <label for="json-upload" class="file-upload-label">
          <span class="button-style">{{ file ? 'File Selected' : 'Choose File' }}</span>
          <span class="file-name">{{ file ? file.name : 'No file chosen' }}</span>
        </label>
        <input 
          id="json-upload"
          type="file" 
          @change="handleFileSelect" 
          accept=".json"
          class="visually-hidden"
        />
        
        <!-- File size info -->
        <div v-if="file" class="file-info">
          <span class="file-size">
            Size: {{ (file.size / (1024 * 1024)).toFixed(2) }}MB
            <span class="size-limit">/ 5MB limit</span>
          </span>
        </div>
        
        <!-- File size warning -->
        <div class="file-size-warning">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
          </svg>
          Maximum file size: 5MB
        </div>
      </div>

      <!-- Empty state when no file chosen yet -->
      <div v-if="!file && !isLoading && !result" class="empty-state" style="margin-top: 14px;">
        <div class="icon">📁</div>
        <div class="title">No file selected</div>
        <div class="hint">Choose or drag a .json file to begin processing.</div>
      </div>

      <button 
        @click="startProcessing" 
        :disabled="!file || isLoading" 
        :class="{ 'processing': isLoading }"
        class="process-btn"
      >
        <span v-if="isLoading">Processing...</span>
        <span v-else>Start Processing</span>
      </button>

      <!-- Loading skeleton while server processes -->
      <div v-if="isLoading" class="skeleton-table" style="margin-top: 12px;">
        <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
        <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
        <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
      </div>

      <div v-if="result" class="results-panel">
        <h3 class="results-title">{{ result.message }}</h3>
        
        <!-- Regular case entry results -->
        <div v-if="!isReverificationFlagsResult" class="results-grid">
          <div class="result-item success">
            <span class="count">{{ result.success_count }}</span>
            <span class="label">Records Succeeded</span>
          </div>
          <div class="result-item failed">
            <span class="count">{{ result.failed_count }}</span>
            <span class="label">Records Failed</span>
          </div>
        </div>
        
        <!-- Reverification flags results -->
        <div v-else class="reverification-results">
          <div class="results-grid">
            <div class="result-item info">
              <span class="count">{{ result.records_processed || 0 }}</span>
              <span class="label">Records Processed</span>
            </div>
            <div class="result-item success">
              <span class="count">{{ result.records_inserted || 0 }}</span>
              <span class="label">Flags Inserted</span>
            </div>
            <div class="result-item warning">
              <span class="count">{{ result.mm_cases_created || 0 }}</span>
              <span class="label">MM Cases Created</span>
            </div>
            <div class="result-item primary">
              <span class="count">{{ result.ecb_cases_created || 0 }}</span>
              <span class="label">ECB Cases Created</span>
            </div>
          </div>
          
          <!-- Case details if available -->
          <div v-if="result.mm_cases_details && result.mm_cases_details.length > 0" class="case-details-section">
            <h4>📱 MM Cases Created:</h4>
            <div class="case-list">
              <div v-for="(case_item, index) in result.mm_cases_details" :key="index" class="case-item">
                <strong>{{ case_item.ack_no }}</strong> - Customer: {{ case_item.customer_id }} ({{ case_item.mobile }})
              </div>
            </div>
          </div>
          
          <div v-if="result.ecb_cases_details && result.ecb_cases_details.length > 0" class="case-details-section">
            <h4>🏦 ECB Cases Created:</h4>
            <div class="case-list">
              <div v-for="(case_item, index) in result.ecb_cases_details" :key="index" class="case-item">
                <strong>{{ case_item.ack_no }}</strong> - {{ case_item.case_type }}: {{ case_item.customer_id }} → {{ case_item.beneficiary_name }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Error Summary (hidden by default) -->
        <div v-if="showInlineErrorDetails && result.errors && result.errors.length > 0" class="error-summary">
          <h4>Error Summary</h4>
          <div class="error-summary-grid">
            <div v-if="duplicateErrorCount > 0" class="error-summary-item duplicate">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              <div class="error-summary-content">
                <span class="error-count">{{ duplicateErrorCount }}</span>
                <span class="error-label">Duplicate ACK Numbers</span>
                <div class="duplicate-ack-list">
                  <div v-for="err in duplicateErrors" :key="err.index" class="duplicate-ack-item">
                    {{ err.record && (err.record.ackNo || err.record.ackno || err.record.ack_no) }}
                  </div>
                </div>
              </div>
            </div>
            <div v-if="noMatchErrorCount > 0" class="error-summary-item no-match">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10"/>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              <div class="error-summary-content">
                <span class="error-count">{{ noMatchErrorCount }}</span>
                <span class="error-label">No Matches Found</span>
              </div>
            </div>
            <div v-if="validationErrorCount > 0" class="error-summary-item validation">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
              </svg>
              <div class="error-summary-content">
                <span class="error-count">{{ validationErrorCount }}</span>
                <span class="error-label">Validation Errors</span>
              </div>
            </div>
            <div v-if="otherErrorCount > 0" class="error-summary-item other">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <div class="error-summary-content">
                <span class="error-count">{{ otherErrorCount }}</span>
                <span class="error-label">Other Errors</span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="result && result.error_file_path" class="error-file-info">
          <p>An error log has been generated for the failed records.</p>
          <strong>Download:</strong> 
          <a :href="result.download_url" target="_blank" class="download-link">
            {{ result.error_file_path }}
          </a>
        </div>
        <!-- Detailed errors for failed records (hidden by default) -->
        <div v-if="showInlineErrorDetails && result.errors && result.errors.length > 0" class="bulk-error-details">
          <h4>Failed Records Details</h4>
          <table class="bulk-error-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Error</th>
                <th>Record Data</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="err in result.errors" :key="err.index">
                <td>{{ err.index + 1 }}</td>
                <td>
                  <div v-if="typeof err.error === 'string'">{{ err.error }}</div>
                  <div v-else-if="err.error && err.error.type === 'validation'">
                    <ul>
                      <li v-for="(v, i) in err.error.detail" :key="i">
                        <span v-if="v.loc && v.loc.length > 1">{{ v.loc[1] }}: </span>{{ v.msg }}
                      </li>
                    </ul>
                  </div>
                  <div v-else-if="err.error && err.error.type === 'db' && (err.error.detail && (err.error.detail.includes('duplicate key value violates unique constraint') || err.error.detail.includes('already exists'))) ">
                    <div class="error-message duplicate-error">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="15" y1="9" x2="9" y2="15"/>
                        <line x1="9" y1="9" x2="15" y2="15"/>
                      </svg>
                      <div class="duplicate-error-content">
                        <div class="duplicate-error-main">
                          <strong>Duplicate ACK Number:</strong> 
                          <span class="highlighted-ack">{{ err.record && (err.record.ackNo || err.record.ackno || err.record.ack_no) }}</span> 
                          already exists in the system.
                        </div>
                        <div class="duplicate-error-detail">
                          This record cannot be processed because the ACK number has been used before.
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else-if="err.error && err.error.type === 'no_match'">
                    <div class="error-message no-match-error">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                        <line x1="12" y1="17" x2="12.01" y2="17"/>
                      </svg>
                      <span>
                        <strong>No Match Found:</strong> {{ err.error.detail || 'No victim or beneficiary account match found for this record.' }}
                      </span>
                    </div>
                  </div>
                  <div v-else-if="err.error && err.error.detail && err.error.detail.includes('Validation Error')">
                    <div class="error-message validation-error">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                      </svg>
                      <span>
                        <strong>Validation Error:</strong> {{ err.error.detail.replace('Validation Error for ack_no ' + (err.record && (err.record.ackNo || err.record.ackno || err.record.ack_no)) + ': ', '') }}
                      </span>
                    </div>
                  </div>
                  <div v-else-if="err.error && err.error.detail">
                    <div class="error-message generic-error">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                      <span>{{ err.error.detail }}</span>
                    </div>
                  </div>
                  <div v-else>
                    {{ err.error ? JSON.stringify(err.error) : 'Unknown error' }}
                  </div>
                </td>
                <td>
                  <div class="record-data-container">
                    <div class="record-highlight">
                      <strong>ACK Number:</strong> 
                      <span class="highlighted-ack-in-json">{{ err.record && (err.record.ackNo || err.record.ackno || err.record.ack_no) }}</span>
                    </div>
                    <pre class="record-json">{{ JSON.stringify(err.record, null, 2) }}</pre>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- End error details -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';
import '../assets/BulkFileUpload.css'

const file = ref(null);
const isLoading = ref(false);
const result = ref(null);
// Hide inline error tables; rely on downloadable error file instead
const showInlineErrorDetails = ref(false);

// Computed property to detect reverification flags results
const isReverificationFlagsResult = computed(() => {
  if (!result.value) return false;
  return result.value.hasOwnProperty('records_processed') && 
         result.value.hasOwnProperty('records_inserted') &&
         result.value.hasOwnProperty('mm_cases_created') &&
         result.value.hasOwnProperty('ecb_cases_created');
});

// Computed properties for error counts
const duplicateErrorCount = computed(() => {
  if (!result.value?.errors) return 0;
  return result.value.errors.filter(err => 
    err.error && err.error.detail && 
    (err.error.detail.includes('duplicate key value violates unique constraint') || 
     err.error.detail.includes('already exists'))
  ).length;
});

const noMatchErrorCount = computed(() => {
  if (!result.value?.errors) return 0;
  return result.value.errors.filter(err => 
    err.error && err.error.type === 'no_match'
  ).length;
});

const validationErrorCount = computed(() => {
  if (!result.value?.errors) return 0;
  return result.value.errors.filter(err => 
    err.error && err.error.detail && 
    err.error.detail.includes('Validation Error')
  ).length;
});

const otherErrorCount = computed(() => {
  if (!result.value?.errors) return 0;
  return result.value.errors.filter(err => 
    err.error && err.error.detail && 
    !err.error.detail.includes('duplicate key value violates unique constraint') &&
    !err.error.detail.includes('already exists') &&
    err.error.type !== 'no_match' &&
    !err.error.detail.includes('Validation Error')
  ).length;
});

// Get duplicate errors for display
const duplicateErrors = computed(() => {
  if (!result.value?.errors) return [];
  return result.value.errors.filter(err => 
    err.error && err.error.detail && 
    (err.error.detail.includes('duplicate key value violates unique constraint') || 
     err.error.detail.includes('already exists'))
  );
});

function handleFileSelect(event) {
  const selectedFile = event.target.files[0];
  if (!selectedFile) return;
  
  // Check file type
  if (selectedFile.type !== 'application/json') {
    window.showNotification('error', 'Invalid File Type', 'Please select a valid .json file.');
    file.value = null;
    event.target.value = '';
    return;
  }
  
  // Check file size (5MB limit)
  const maxSize = 5 * 1024 * 1024; // 5MB in bytes
  if (selectedFile.size > maxSize) {
    window.showNotification('error', 'File Too Large', `File size must be less than 5MB. Current size: ${(selectedFile.size / (1024 * 1024)).toFixed(2)}MB`);
    file.value = null;
    event.target.value = '';
    return;
  }
  
  file.value = selectedFile;
  result.value = null;
  window.showNotification('success', 'File Selected', `${selectedFile.name} has been selected successfully.`);
}

function handleFileDrop(event) {
  const droppedFile = event.dataTransfer.files[0];
  if (!droppedFile) return;
  
  // Check file type
  if (droppedFile.type !== 'application/json') {
    window.showNotification('error', 'Invalid File Type', 'Please drop a valid .json file.');
    return;
  }
  
  // Check file size (5MB limit)
  const maxSize = 5 * 1024 * 1024; // 5MB in bytes
  if (droppedFile.size > maxSize) {
    window.showNotification('error', 'File Too Large', `File size must be less than 5MB. Current size: ${(droppedFile.size / (1024 * 1024)).toFixed(2)}MB`);
    return;
  }
  
  file.value = droppedFile;
  result.value = null;
  window.showNotification('success', 'File Dropped', `${droppedFile.name} has been dropped successfully.`);
}

async function startProcessing() {
  if (!file.value) return;

  isLoading.value = true;
  result.value = null;
  
  const formData = new FormData();
  formData.append('file', file.value);

  try {
    const token = localStorage.getItem('jwt');
    const res = await axios.post('/api/process-bulk-file', formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${token}`
      }
    });
    
    result.value = res.data;

    if (result.value.error_file_path) {
      result.value.download_url = `/api/download-error-log/${result.value.error_file_path}`;
    }
    
    // Show success notification with specific error details
    if (result.value.success_count > 0 && result.value.failed_count === 0) {
      window.showNotification('success', 'Processing Complete', `Successfully processed ${result.value.success_count} records!`);
    } else if (result.value.success_count > 0 && result.value.failed_count > 0) {
      const duplicateErrors = result.value.errors ? result.value.errors.filter(err => 
        err.error && err.error.detail && 
        (err.error.detail.includes('duplicate key value violates unique constraint') || 
         err.error.detail.includes('already exists'))
      ).length : 0;
      
      const noMatchErrors = result.value.errors ? result.value.errors.filter(err => 
        err.error && err.error.detail && 
        err.error.detail.includes('No Victim or Beneficiary account match found')
      ).length : 0;
      
      let message = `Processed ${result.value.success_count} records successfully, ${result.value.failed_count} failed.`;
      if (duplicateErrors > 0) message += ` ${duplicateErrors} duplicate ACK numbers.`;
      if (noMatchErrors > 0) message += ` ${noMatchErrors} no matches found.`;
      
      window.showNotification('warning', 'Processing Complete with Errors', message);
    } else if (result.value.failed_count > 0) {
      const duplicateErrors = result.value.errors ? result.value.errors.filter(err => 
        err.error && err.error.detail && 
        (err.error.detail.includes('duplicate key value violates unique constraint') || 
         err.error.detail.includes('already exists'))
      ).length : 0;
      
      const noMatchErrors = result.value.errors ? result.value.errors.filter(err => 
        err.error && err.error.detail && 
        err.error.detail.includes('No Victim or Beneficiary account match found')
      ).length : 0;
      
      let message = `All ${result.value.failed_count} records failed.`;
      if (duplicateErrors > 0) message += ` ${duplicateErrors} duplicate ACK numbers.`;
      if (noMatchErrors > 0) message += ` ${noMatchErrors} no matches found.`;
      
      window.showNotification('error', 'Processing Failed', message);
    }

  } catch (error) {
    console.error("Failed to process file:", error.response?.data || error.message);
    const errorMessage = error.response?.data?.detail || 'Please check the console.';
    window.showNotification('error', 'Processing Failed', errorMessage);
    result.value = {
      message: 'Processing failed due to a server error.',
      success_count: 'N/A',
      failed_count: 'N/A',
      error_file_path: null
    };
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.bulk-error-details {
  margin-top: 2rem;
  background: #fff3cd;
  border: 1px solid #ffeeba;
  border-radius: 8px;
  padding: 1.5rem;
}
.bulk-error-details h4 {
  color: #856404;
  margin-bottom: 1rem;
}
.bulk-error-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}
.bulk-error-table th, .bulk-error-table td {
  border: 1px solid #ffeeba;
  padding: 0.75rem 1rem;
  text-align: left;
  vertical-align: top;
  font-size: 0.95rem;
}
.bulk-error-table th {
  background: #fff8e1;
  color: #856404;
}
.bulk-error-table tr:nth-child(even) {
  background: #fffdf5;
}
.record-json {
  font-size: 0.85rem;
  background: #f8f9fa;
  border-radius: 4px;
  padding: 0.5rem;
  overflow-x: auto;
  max-width: 400px;
  white-space: pre-wrap;
}

/* File size info styles */
.file-info {
  margin-top: 8px;
  text-align: center;
}

.file-size {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.size-limit {
  color: #6b7280;
  font-weight: 400;
}

.file-size-warning {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 6px;
  color: #92400e;
  font-size: 13px;
  font-weight: 500;
}

.file-size-warning svg {
  color: #f59e0b;
  flex-shrink: 0;
}

/* Error Message Styles */
.error-message {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.4;
}

.error-message svg {
  flex-shrink: 0;
  margin-top: 2px;
}

.duplicate-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.duplicate-error svg {
  color: #dc2626;
}

.duplicate-error-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.duplicate-error-main {
  font-weight: 500;
}

.duplicate-error-detail {
  font-size: 13px;
  color: #991b1b;
  font-style: italic;
}

.highlighted-ack {
  background: #fef2f2;
  border: 2px solid #dc2626;
  border-radius: 4px;
  padding: 2px 8px;
  font-weight: 700;
  color: #dc2626;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.record-data-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-highlight {
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  border-left: 4px solid #dc2626;
}

.highlighted-ack-in-json {
  background: #dc2626;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.no-match-error {
  background: #fef3c7;
  border: 1px solid #fde68a;
  color: #d97706;
}

.no-match-error svg {
  color: #d97706;
}

.validation-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.validation-error svg {
  color: #dc2626;
}

.generic-error {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  color: #374151;
}

.generic-error svg {
  color: #6b7280;
}

/* Enhanced error table styling */
.bulk-error-table td:first-child {
  width: 60px;
  text-align: center;
  font-weight: 600;
  color: #6b7280;
}

.bulk-error-table td:nth-child(2) {
  min-width: 300px;
  max-width: 400px;
}

.bulk-error-table td:last-child {
  width: 300px;
  max-width: 300px;
}

/* Summary error counts with better styling */
.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin: 20px 0;
}

.result-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s ease;
}

.result-item:hover {
  transform: translateY(-2px);
}

.result-item.success {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  border: 1px solid #6ee7b7;
  color: #065f46;
}

.result-item.failed {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border: 1px solid #f87171;
  color: #991b1b;
}

.result-item .count {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
}

.result-item .label {
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Error Summary Styles */
.error-summary {
  margin: 24px 0;
  padding: 20px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 12px;
}

.error-summary h4 {
  margin: 0 0 16px 0;
  color: #495057;
  font-size: 18px;
  font-weight: 600;
}

.error-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.error-summary-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  background: white;
  border: 1px solid #e9ecef;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  transition: transform 0.2s ease;
}

.error-summary-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.error-summary-item.duplicate {
  border-left: 4px solid #dc2626;
}

.error-summary-item.no-match {
  border-left: 4px solid #d97706;
}

.error-summary-item.validation {
  border-left: 4px solid #dc2626;
}

.error-summary-item.other {
  border-left: 4px solid #6b7280;
}

.error-summary-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.error-count {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
}

.error-label {
  font-size: 12px;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.error-summary-item.duplicate svg {
  color: #dc2626;
}

.error-summary-item.no-match svg {
  color: #d97706;
}

.error-summary-item.validation svg {
  color: #dc2626;
}

.error-summary-item.other svg {
  color: #6b7280;
}

.duplicate-ack-list {
  margin-top: 8px;
  max-height: 120px;
  overflow-y: auto;
}

.duplicate-ack-item {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 4px;
  padding: 4px 8px;
  margin: 2px 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  font-weight: 600;
  color: #dc2626;
  text-align: center;
}

/* Reverification flags results styles */
.reverification-results {
  margin-top: 1rem;
}

.case-details-section {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.case-details-section h4 {
  margin: 0 0 1rem 0;
  color: #495057;
  font-size: 1.1rem;
}

.case-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.case-item {
  padding: 0.75rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  font-size: 0.9rem;
  color: #495057;
}

.case-item strong {
  color: #007bff;
  font-weight: 600;
}

/* Additional result item styles for reverification flags */
.result-item.info {
  background: linear-gradient(135deg, #17a2b8, #138496);
  color: white;
}

.result-item.warning {
  background: linear-gradient(135deg, #ffc107, #e0a800);
  color: #212529;
}

.result-item.primary {
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
}

/* Responsive design for error summary */
@media (max-width: 768px) {
  .error-summary-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .error-summary-item {
    padding: 12px;
  }
  
  .error-count {
    font-size: 20px;
  }
  
  .case-details-section {
    padding: 0.75rem;
  }
  
  .case-item {
    padding: 0.5rem;
    font-size: 0.85rem;
  }
}
</style>