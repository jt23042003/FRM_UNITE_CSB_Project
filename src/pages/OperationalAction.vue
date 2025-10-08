<template>
  <div class="pma-container">
    <div v-if="isReadOnly" class="readonly-banner">
      <span>This case is closed. Editing is disabled.</span>
    </div>

    <div class="steps-header">
      <div class="steps-container">
        <div
          v-for="(step, index) in steps"
          :key="index"
          :class="['step', { active: currentStep === index + 1, completed: currentStep > index + 1 }]"
          @click="goToStep(index + 1)"
        >
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-title">{{ step.title }}</div>
        </div>
      </div>
    </div>

    <div class="step-content">
      
      <div v-if="currentStep === 1" class="step-panel">
        <h3>Alert - I4C Operational Response</h3>
        <div v-if="isLoading" class="loading-indicator">
          Loading Case Details...
          <div class="skeleton-table" style="margin-top: 12px;">
            <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
            <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
            <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
          </div>
        </div>
        <div v-else-if="fetchError" class="error-indicator">{{ fetchError }}</div>
        <div v-else class="comparison-grid">
          <div class="details-section">
            <h4>Customer Details - I4C</h4>
            <div class="details-row">
              <div class="field-group"><label>Name</label><input type="text" v-model="i4cDetails.name" readonly /></div>
              <div class="field-group"><label>Mobile</label><input type="text" v-model="i4cDetails.mobileNumber" readonly /></div>
              <div class="field-group"><label>Email</label><input type="text" v-model="i4cDetails.email" readonly /></div>
            </div>
            <div class="details-row">
              <div class="field-group"><label>Bank A/c #</label><input type="text" v-model="i4cDetails.bankAc" readonly /></div>
              <div class="field-group"><label>Sub Category</label><input type="text" v-model="i4cDetails.subCategory" readonly /></div>
            </div>
            <div class="details-row">
              <div class="field-group"><label>Requestor</label><input type="text" v-model="i4cDetails.requestor" readonly /></div>
              <div class="field-group"><label>Payer Bank</label><input type="text" v-model="i4cDetails.payerBank" readonly /></div>
            </div>
            <div class="details-row">
              <div class="field-group"><label>Mode of Payment</label><input type="text" v-model="i4cDetails.modeOfPayment" readonly /></div>
              <div class="field-group"><label>State</label><input type="text" v-model="i4cDetails.state" readonly /></div>
            </div>
            <div class="details-row">
              <div class="field-group"><label>District</label><input type="text" v-model="i4cDetails.district" readonly /></div>
              <div class="field-group"><label>Transaction Type</label><input type="text" v-model="i4cDetails.transactionType" readonly /></div>
            </div>
          </div>
          <div class="details-section">
            <h4>Customer Details - Bank</h4>
            <div class="details-row">
              <div class="field-group highlight"><label>Name</label><input type="text" v-model="bankDetails.name" readonly /></div>
              <div class="field-group highlight"><label>Mobile</label><input type="text" v-model="bankDetails.mobileNumber" readonly /></div>
              <div class="field-group highlight"><label>Email</label><input type="text" v-model="bankDetails.email" readonly /></div>
            </div>
            <div class="details-row">
              <div class="field-group"><label>Bank A/c #</label><input type="text" v-model="bankDetails.bankAc" readonly /></div>
              <div class="field-group"><label>Customer ID</label><input type="text" v-model="bankDetails.customerId" readonly /></div>
              <div class="field-group"><label>A/c Status</label><input type="text" v-model="bankDetails.acStatus" readonly /></div>
            </div>
            <div class="details-row">
              <div class="field-group"><label>Product Code</label><input type="text" v-model="bankDetails.productCode" readonly /></div>
              <div class="field-group"><label>AQB</label><input type="text" v-model="bankDetails.aqb" readonly /></div>
              <div class="field-group"><label>Available Balance</label><input type="text" v-model="bankDetails.availBal" readonly /></div>
            </div>
            <div class="details-row">
              <div class="field-group"><label>Relationship Value</label><input type="text" v-model="bankDetails.relValue" readonly /></div>
              <div class="field-group"><label>Vintage (MoB)</label><input type="text" v-model="bankDetails.mobVintage" readonly /></div>
            </div>
          </div>
        </div>

        <!-- Transaction Table for VM (from banks_v2 incidents) -->
        <div v-if="transactions.length > 0" class="transaction-section">
          <h4>Transaction History - I4C Incidents</h4>
          <div class="transaction-table-container">
            <table class="transaction-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>RRN / Reference</th>
                  <th>Amount</th>
                  <th>Disputed Amount</th>
                  <th>Layer</th>
                  <th>Channel</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="transaction in transactions" 
                  :key="transaction.txn_ref || transaction.rrn"
                >
                  <td>{{ formatDate(transaction.txn_date) }}</td>
                  <td>{{ formatTime(transaction.txn_time) }}</td>
                  <td>{{ transaction.txn_ref }}</td>
                  <td class="amount-cell">{{ formatAmount(transaction.amount) }}</td>
                  <td class="amount-cell">{{ formatAmount(transaction.disputed_amount) }}</td>
                  <td>{{ transaction.layer }}</td>
                  <td>{{ transaction.channel }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="transaction-summary">
            <p><strong>Total Transactions:</strong> {{ transactions.length }}</p>
            <p><strong>Total Value at Risk:</strong> {{ formatAmount(calculateTotalValueAtRisk()) }}</p>
          </div>
        </div>
        <div v-else class="transaction-section">
          <h4>Transaction History - I4C Incidents</h4>
          <div class="no-transactions">
            <p>No transaction data available for this case.</p>
          </div>
        </div>
      </div>

      <div v-if="currentStep === 2" class="step-panel">
        <h3>Action</h3>
        <div v-if="isLoading" class="loading-indicator">Loading Action Items...</div>
        <div v-else class="action-section-grid">
          
          <div class="document-checklist">
            <h4>I4C Requirements <span class="required-indicator">*</span></h4>
            <div v-if="documentList.length === 0" class="no-documents-message">
              No documents available for this case.
            </div>
            <ul v-else class="document-list">
              <li v-for="doc in documentList" :key="doc.id">
                <label>
                  <input type="checkbox" v-model="doc.checked" :disabled="isReadOnly" />
                  <span>{{ doc.name }}</span>
                </label>
              </li>
            </ul>
            <div v-if="documentList.length > 0" class="document-validation-message">
              <small class="text-muted">
                <span v-if="!hasSelectedDocuments" class="validation-warning">⚠️ Please select at least one document to proceed.</span>
                <span v-else class="validation-success">✅ {{ documentList.filter(doc => doc.checked).length }} document(s) selected</span>
              </small>
            </div>
          </div>

          <div class="reference-upload">
            <div class="field-group">
              <label>Reference No.</label>
              <input type="text" v-model="referenceNo" placeholder="Enter reference number" :disabled="isReadOnly" class="action-input"/>
            </div>
            <div class="field-group">
              <label>Screenshot Upload</label>
              <div class="screenshot-uploader">
                <button @click="triggerFileInput" :disabled="isReadOnly" class="btn-browse">Browse...</button>
                <input ref="fileInputRef" type="file" @change="handleFileSelect" accept="image/*" class="hidden-file-input" />
                <span class="file-name-display">{{ screenshotFile ? screenshotFile.name : 'No file selected' }}</span>
              </div>
              <div v-if="screenshotFile" class="file-validation-success">
                <small class="text-success">✅ File validated successfully</small>
              </div>
              <div class="file-help-text">
                <small class="text-muted">Supported formats: PNG, JPG, JPEG, GIF, WebP (Max: 10MB)</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Show saved data if available -->
    <div v-if="savedActionData && !isLoading" class="saved-data-section">
      <h4>Last Saved Action</h4>
      <div class="saved-data-grid">
        <div class="saved-item">
          <label>Reference No:</label>
          <span>{{ savedActionData.proof_of_upload_ref || 'Not provided' }}</span>
        </div>
        <div class="saved-item">
          <label>Checked Documents:</label>
          <div v-if="savedActionData.checked_documents && savedActionData.checked_documents.length > 0" class="checked-documents-list">
            <ul>
              <li v-for="doc in savedActionData.checked_documents" :key="doc">{{ doc }}</li>
            </ul>
          </div>
          <span v-else>{{ savedActionData.checked_documents?.length || 0 }} documents selected</span>
        </div>
        <div class="saved-item">
          <label>Screenshot:</label>
          <div v-if="savedActionData.screenshot_filename">
            <a 
              :href="`/api/download-document/${savedActionData.screenshot_document_id}`" 
              target="_blank"
              class="screenshot-download-link"
              v-if="savedActionData.screenshot_document_id"
            >
              {{ savedActionData.screenshot_filename }}
            </a>
            <span v-else>{{ savedActionData.screenshot_filename }}</span>
          </div>
          <span v-else>No screenshot uploaded</span>
        </div>
        <div class="saved-item">
          <label>Status:</label>
          <span :class="['status-badge', savedActionData.confirmation_action_status]">
            {{ savedActionData.confirmation_action_status }}
          </span>
        </div>
        <div class="saved-item">
          <label>Submitted By:</label>
          <span>{{ savedActionData.submitted_by || 'Unknown' }}</span>
        </div>
        <div class="saved-item">
          <label>Submitted At:</label>
          <span>{{ savedActionData.submitted_at ? new Date(savedActionData.submitted_at).toLocaleString() : 'Unknown' }}</span>
        </div>
      </div>
    </div>

    <div v-if="caseLogs.length > 0" class="case-logs-section">
      <h4>Case Activity Log</h4>
      <ul class="case-log-list">
        <li v-for="log in caseLogs" :key="log.id" class="case-log-item">
          <span class="log-time">{{ new Date(log.created_at).toLocaleString() }}</span>
          <span class="log-user">{{ log.user_name }}</span>
          <span class="log-action">[{{ log.action }}]</span>
          <span class="log-details">{{ log.details }}</span>
        </li>
      </ul>
    </div>
    <div v-else class="case-logs-section">
      <div class="empty-state">
        <div class="icon">📝</div>
        <div class="title">No activity yet</div>
        <div class="hint">Actions and updates will appear here.</div>
      </div>
    </div>

    <div class="bottom-navigation">
      <div class="nav-buttons">
        <button @click="previousStep" :disabled="currentStep === 1" class="btn-nav btn-prev">Previous</button>
        <button @click="nextStep" v-if="currentStep < steps.length" class="btn-nav btn-next">Next</button>
      </div>
      <div class="action-buttons">
        <button v-if="!isReadOnly" @click="saveAction" class="btn-save" :disabled="isSaving || !hasSelectedDocuments">
          {{ isSaving ? 'Saving...' : 'Save' }}
        </button>
        <button
          v-if="!isReadOnly"
          @click="submitAction"
          class="btn-submit"
          :disabled="isSaving || !hasSelectedDocuments"
        >
          {{ isSaving ? 'Submitting...' : 'Submit & Close Case' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();

// --- State Management ---
const isLoading = ref(true);
const fetchError = ref(null);
const isSaving = ref(false);
const caseLogs = ref([]);
const savedActionData = ref(null);

// --- Case Status Management ---
const caseStatus = ref('New');
const isReadOnly = computed(() => caseStatus.value === 'Closed'); // Only closed cases should be read-only
const isAssignmentDisabled = computed(() => caseStatus.value === 'Reopened'); // Only assignment is disabled for reopened cases
const hasSelectedDocuments = computed(() => documentList.value.some(doc => doc.checked));

// --- Stepper Logic ---
const currentStep = ref(1);
const steps = ref([
  { title: 'Alert Details' },
  { title: 'Action' }
]);
const goToStep = (step) => { if (!isReadOnly.value) currentStep.value = step; };
const nextStep = () => { if (currentStep.value < steps.value.length) currentStep.value++; };
const previousStep = () => { if (currentStep.value > 1) currentStep.value--; };

// --- Data Models ---
const i4cDetails = ref({});
const bankDetails = ref({});
const documentList = ref([]);
const referenceNo = ref('');
const screenshotFile = ref(null);
const fileInputRef = ref(null);
const transactions = ref([]);

const caseId = parseInt(route.params.case_id);

// --- API Integration ---
onMounted(async () => {
  isLoading.value = true;
  fetchError.value = null;
  const token = localStorage.getItem('jwt');
  if (!token) {
    fetchError.value = "Authentication token not found. Please log in.";
    isLoading.value = false;
    return;
  }

  try {
    // First, get case data to determine status
    const caseDataRes = await axios.get(`/api/combined-case-data/${caseId}`, { 
      headers: { Authorization: `Bearer ${token}` } 
    });

    if (caseDataRes.data) {
      const { i4c_data = {}, customer_details = {}, account_details = {}, acc_num, status, source_ack_no } = caseDataRes.data;
      
      // Update case status
      caseStatus.value = status || 'New';
      
      // Try to fetch banks_v2 data and transaction details if we have a source_ack_no
      let banksV2Data = null;
      let banksV2Transactions = [];
      if (source_ack_no) {
        try {
          // Extract base acknowledgement number by removing suffixes like _ECBNT, _VM, etc.
          const baseAckNo = source_ack_no.replace(/_(ECBNT|ECBT|VM|PSA)$/, '');
          
          // Fetch case data
          const banksV2Res = await axios.get(`/api/v2/banks/case-data/${baseAckNo}`, { 
            headers: { Authorization: `Bearer ${token}` } 
          });
          if (banksV2Res.data?.success) {
            banksV2Data = banksV2Res.data.data;
          }
          
          // Fetch transaction details
          const banksV2TxnRes = await axios.get(`/api/v2/banks/transaction-details/${baseAckNo}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (banksV2TxnRes.data?.success) {
            banksV2Transactions = banksV2TxnRes.data.data.transactions || [];
          }
        } catch (error) {
          console.log('No banks_v2 data found for this case:', error.message);
        }
      }
      
      // Populate transactions array
      transactions.value = banksV2Transactions;
      
      // Populate I4C details with banks_v2 data if available, otherwise fallback to original data
      if (banksV2Data) {
        i4cDetails.value = {
          name: banksV2Data.instrument?.payer_account_number ? `Account ${banksV2Data.instrument.payer_account_number}` : 'N/A',
          mobileNumber: banksV2Data.instrument?.payer_mobile_number || 'N/A',
          bankAc: banksV2Data.instrument?.payer_account_number || 'N/A',
          email: 'N/A', // Not available in banks_v2 data
          subCategory: banksV2Data.sub_category || 'N/A',
          requestor: banksV2Data.instrument?.requestor || 'N/A',
          payerBank: banksV2Data.instrument?.payer_bank || 'N/A',
          modeOfPayment: banksV2Data.instrument?.mode_of_payment || 'N/A',
          state: banksV2Data.instrument?.state || 'N/A',
          district: banksV2Data.instrument?.district || 'N/A',
          transactionType: banksV2Data.instrument?.transaction_type || 'N/A',
          incidents: banksV2Data.incidents || []
        };
      } else {
        // Fallback to original I4C data
        i4cDetails.value = {
          name: i4c_data?.customer_name || 'N/A',
          mobileNumber: i4c_data?.mobile || 'N/A',
          bankAc: i4c_data?.account_number || 'N/A',
          email: i4c_data?.email || 'N/A',
        };
      }
      bankDetails.value = {
        name: `${customer_details?.fname || ''} ${customer_details?.mname || ''} ${customer_details?.lname || ''}`.trim() || 'N/A',
        mobileNumber: customer_details?.mobile || 'N/A',
        bankAc: acc_num || 'N/A',
        email: customer_details?.email || 'N/A',
        customerId: customer_details?.cust_id || 'N/A',
        acStatus: account_details?.acc_status || 'N/A',
        aqb: account_details?.aqb || 'N/A',
        availBal: account_details?.availBal || 'N/A',
        productCode: account_details?.productCode || 'N/A',
        relValue: customer_details?.rel_value || 'N/A',
        mobVintage: customer_details?.mob || 'N/A',
      };
    }

    // Fetch other data in parallel
    const [docListRes, logsRes] = await Promise.all([
      axios.get('/api/i4c-document-list', { headers: { Authorization: `Bearer ${token}` } }),
      axios.get(`/api/case/${caseId}/logs`, { headers: { Authorization: `Bearer ${token}` } })
    ]);

    if (docListRes.data?.success) {
      documentList.value = docListRes.data.documents.map(doc => ({
        id: doc.seq_id,
        name: doc.file_name,
        checked: false,
      }));
    }

    caseLogs.value = logsRes.data?.logs || [];

    // Only fetch operational confirmation if case is not "New"
    if (caseStatus.value !== 'New') {
      try {
        const operationalConfirmationRes = await axios.get(`/api/case/${caseId}/operational-confirmation`, { 
          headers: { Authorization: `Bearer ${token}` } 
        });
        
        if (operationalConfirmationRes.data?.success && operationalConfirmationRes.data.data) {
          savedActionData.value = operationalConfirmationRes.data.data;
          
          // Pre-fill form with saved data
          referenceNo.value = savedActionData.value.proof_of_upload_ref || '';
          const checkedDocs = savedActionData.value.checked_documents || [];
          documentList.value.forEach(doc => {
            doc.checked = checkedDocs.includes(doc.name);
          });
        }
      } catch (operationalConfirmationErr) {
        console.log("No operational confirmation found for case (this is normal for new cases):", operationalConfirmationErr.message);
        // This is expected for new cases, so we don't treat it as an error
      }
    }

  } catch (err) {
    console.error("Error fetching operational case data:", err);
    fetchError.value = "Failed to load case data. Please try again.";
  } finally {
    isLoading.value = false;
  }
});

// --- UI Interaction ---
const triggerFileInput = () => {
  fileInputRef.value.click();
};

const handleFileSelect = (event) => {
  const file = event.target.files[0];
  if (!file) {
    screenshotFile.value = null;
    return;
  }

  // Validate file type
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    window.showNotification('error', 'Invalid File Type', 'Please select an image file (PNG, JPG, JPEG, GIF, or WebP).');
    event.target.value = ''; // Clear the input
    screenshotFile.value = null;
    return;
  }

  // Validate file size (max 10MB)
  const maxSize = 10 * 1024 * 1024; // 10MB in bytes
  if (file.size > maxSize) {
    window.showNotification('error', 'File Too Large', 'Please select an image file smaller than 10MB.');
    event.target.value = ''; // Clear the input
    screenshotFile.value = null;
    return;
  }

  screenshotFile.value = file;
};

// --- Action Buttons ---
const createActionPayload = () => {
  const formData = new FormData();
  const checkedDocs = documentList.value
    .filter(doc => doc.checked)
    .map(doc => doc.name);
  
  formData.append('case_id', caseId);
  formData.append('checked_documents', JSON.stringify(checkedDocs));
  formData.append('proof_of_upload_ref', referenceNo.value);
  
  if (screenshotFile.value) {
    formData.append('screenshot', screenshotFile.value);
  }
  return formData;
};

const saveAction = async () => {
  // Validate that at least one document is checked
  const checkedDocs = documentList.value.filter(doc => doc.checked);
  if (checkedDocs.length === 0) {
    window.showNotification('error', 'Validation Error', 'Please select at least one document before saving.');
    return;
  }

  isSaving.value = true;
  const formData = createActionPayload();
  formData.append('confirmation_action_status', 'saved');

  try {
    const response = await axios.post('/api/operational-confirm', formData, {
      headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` },
    });
    
    if (response.data.success) {
    window.showNotification('success', 'Action Saved', 'Case data saved successfully! You can now submit when ready.');
      caseStatus.value = 'Open'; // Update status to Open
      
      // Refresh saved action data
      try {
        const operationalConfirmationRes = await axios.get(`/api/case/${caseId}/operational-confirmation`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
        });
        if (operationalConfirmationRes.data?.success && operationalConfirmationRes.data.data) {
          savedActionData.value = operationalConfirmationRes.data.data;
        }
      } catch (refreshErr) {
        console.log("Operational confirmation not found yet (normal for first save):", refreshErr.message);
        // This is normal for first-time saves
      }
    } else {
      throw new Error(response.data.message || 'Unknown error');
    }
  } catch (err) {
    console.error('Save action error:', err);
    
    // Provide better error messages based on error type
    let errorMessage = 'Failed to save data';
    if (err.response?.status === 422) {
      errorMessage = 'Invalid file format or file too large. Please check your screenshot file.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response.data?.detail || 'Invalid data provided. Please check your inputs.';
    } else if (err.response?.status === 413) {
      errorMessage = 'File too large. Please upload a smaller screenshot.';
    } else if (err.response?.status === 415) {
      errorMessage = 'Unsupported file type. Please upload an image file (PNG, JPG, JPEG).';
    } else if (err.response?.data?.detail) {
      errorMessage = err.response.data.detail;
    } else if (err.message) {
      errorMessage = err.message;
    }
    
    window.showNotification('error', 'Save Failed', errorMessage);
  } finally {
    isSaving.value = false;
  }
};

const submitAction = async () => {
  // Validate that at least one document is checked
  const checkedDocs = documentList.value.filter(doc => doc.checked);
  if (checkedDocs.length === 0) {
    window.showNotification('error', 'Validation Error', 'Please select at least one document before submitting.');
    return;
  }

  isSaving.value = true;
  const formData = createActionPayload();
  formData.append('confirmation_action_status', 'submitted');

  try {
    const response = await axios.post('/api/operational-confirm', formData, {
      headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` },
    });
    
    if (response.data.success) {
    window.showNotification('success', 'Case Submitted', 'Case submitted and closed successfully!');
      caseStatus.value = 'Closed'; // Update status to Closed
      
      // Refresh saved action data
      try {
        const operationalConfirmationRes = await axios.get(`/api/case/${caseId}/operational-confirmation`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
        });
        if (operationalConfirmationRes.data?.success && operationalConfirmationRes.data.data) {
          savedActionData.value = operationalConfirmationRes.data.data;
        }
      } catch (refreshErr) {
        console.log("Operational confirmation not found yet (normal for first submit):", refreshErr.message);
        // This is normal for first-time submits
      }
      
      // Navigate back to case details after a short delay
      setTimeout(() => {
        router.push('/case-details');
      }, 2000);
    } else {
      throw new Error(response.data.message || 'Unknown error');
    }
  } catch (err) {
    console.error('Submit action error:', err);
    
    // Provide better error messages based on error type
    let errorMessage = 'Failed to submit case';
    if (err.response?.status === 422) {
      errorMessage = 'Invalid file format or file too large. Please check your screenshot file.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response.data?.detail || 'Invalid data provided. Please check your inputs.';
    } else if (err.response?.status === 413) {
      errorMessage = 'File too large. Please upload a smaller screenshot.';
    } else if (err.response?.status === 415) {
      errorMessage = 'Unsupported file type. Please upload an image file (PNG, JPG, JPEG).';
    } else if (err.response?.data?.detail) {
      errorMessage = err.response.data.detail;
    } else if (err.message) {
      errorMessage = err.message;
    }
    
    window.showNotification('error', 'Submit Failed', errorMessage);
  } finally {
    isSaving.value = false;
  }
};

// Transaction formatting functions
const formatDate = (dateString) => {
  if (!dateString) return '-';
  // Handle DD-MM-YYYY format from banks_v2
  if (typeof dateString === 'string' && dateString.includes('-')) {
    return dateString; // Already in DD-MM-YYYY format
  }
  return new Date(dateString).toLocaleDateString();
};

const formatTime = (timeString) => {
  if (!timeString) return '-';
  return timeString;
};

const formatAmount = (amount) => {
  if (!amount) return '-';
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(numAmount)) return '-';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR'
  }).format(numAmount);
};

const calculateTotalValueAtRisk = () => {
  if (!transactions.value || transactions.value.length === 0) return 0;
  return transactions.value.reduce((total, txn) => {
    const amount = typeof txn.amount === 'string' ? parseFloat(txn.amount) : txn.amount;
    return total + (isNaN(amount) ? 0 : amount);
  }, 0);
};
</script>

<style scoped>
/* Main Container */
.pma-container {
  height: 100vh;
  overflow: hidden;
  padding: 16px;
  background: #f8f9fa;
  display: flex;
  flex-direction: column;
}

/* Stepper Header */
.steps-header {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.steps-container {
  display: flex;
  justify-content: space-around;
  max-width: 500px;
  margin: 0 auto;
}
.step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  flex: 1;
  justify-content: center;
}
.step:hover { background: #f8f9fa; }
.step.active { background: #0d6efd; color: white; }
.step.completed { background: #28a745; color: white; }
.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}
.step.active .step-number, .step.completed .step-number { background: rgba(255,255,255,0.3); }
.step-title { font-size: 14px; font-weight: 500; }

/* Main Content Area */
.step-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 16px;
}
.step-panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 16px;
}
.step-panel h3 {
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
  padding-bottom: 12px;
  border-bottom: 2px solid #e9ecef;
}
.step-panel h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid #dee2e6;
}

/* Indicators */
.loading-indicator, .error-indicator, .readonly-banner {
  text-align: center;
  padding: 14px 20px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 6px;
}
.loading-indicator { color: #6c757d; }
.error-indicator { color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; }
.readonly-banner { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }

/* Customer Details Section */
.comparison-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.details-section { background: #f8f9fa; border-radius: 6px; padding: 16px; border: 1px solid #e9ecef; }
.details-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px; }
.details-row:last-child { margin-bottom: 0; }
.field-group { display: flex; flex-direction: column; gap: 4px; }
.field-group label { font-size: 14px; font-weight: 600; color: #2c3e50; margin-bottom: 4px; }
.field-group input[type="text"] { padding: 6px 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: 13px; background: #e9ecef; }
.field-group.highlight input { background: #fff3cd; border-color: #ffc107; font-weight: 500; }

/* Action Section */
.action-section-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.document-checklist { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 16px; }
.document-list { list-style: none; padding: 0; margin: 0; }
.document-list li { margin-bottom: 12px; }
.document-list label { display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 14px; }
.document-list input[type="checkbox"] { width: 18px; height: 18px; accent-color: #0d6efd; }
.required-indicator { color: #dc3545; font-weight: bold; }
.no-documents-message { color: #6c757d; font-style: italic; padding: 8px 0; }
.document-validation-message { margin-top: 12px; padding-top: 8px; border-top: 1px solid #dee2e6; }
.text-muted { color: #6c757d; }
.validation-warning { color: #dc3545; font-weight: 500; }
.validation-success { color: #28a745; font-weight: 500; }
.reference-upload { display: flex; flex-direction: column; gap: 24px; }
.action-input { padding: 8px 10px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background: #fff; }
.screenshot-uploader { display: flex; align-items: center; gap: 12px; }
.btn-browse { padding: 6px 12px; border: 1px solid #0d6efd; background-color: #e7f3ff; color: #0d6efd; border-radius: 4px; cursor: pointer; font-weight: 500; }
.hidden-file-input { display: none; }
.file-name-display { font-size: 13px; color: #6c757d; font-style: italic; }
.file-validation-success { margin-top: 4px; }
.text-success { color: #28a745; font-weight: 500; }
.file-help-text { margin-top: 4px; }

/* Saved Data Section */
.saved-data-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 16px;
}
.saved-data-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1a3a5d;
  padding-bottom: 8px;
  border-bottom: 1px solid #dee2e6;
}
.saved-data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}
.saved-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.saved-item label {
  font-size: 12px;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.saved-item span {
  font-size: 14px;
  color: #495057;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}
.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}
.status-badge.saved {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}
.status-badge.submitted {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

/* Checked Documents List */
.checked-documents-list ul {
  margin: 8px 0;
  padding-left: 20px;
}
.checked-documents-list li {
  margin-bottom: 4px;
  color: #495057;
  font-size: 14px;
}

/* Screenshot Download Link */
.screenshot-download-link {
  color: #0d6efd;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}
.screenshot-download-link:hover {
  color: #0a58ca;
  text-decoration: underline;
}

/* Case Logs & Bottom Nav */
.case-logs-section, .bottom-navigation { background: #fff; border-radius: 8px; padding: 18px 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: auto; }
.case-logs-section h4 { margin: 0 0 12px 0; font-size: 16px; color: #1a3a5d; }
.case-log-list { list-style: none; padding: 0; margin: 0; }
.case-logs-section .case-log-list { max-height: 40vh; overflow-y: auto; padding-right: 8px; }
.case-log-item { display: flex; gap: 12px; align-items: center; font-size: 14px; padding: 8px 0; border-bottom: 1px solid #e3e8ee; }
.case-log-item:last-child { border-bottom: none; }
.log-time { color: #6c757d; font-size: 12px; min-width: 120px; }
.log-user { color: #0d6efd; font-weight: 500; }
.log-action { color: #28a745; font-weight: 500; }
.log-details { color: #495057; font-size: 13px; }

.bottom-navigation { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; margin-top: 16px; }
.nav-buttons, .action-buttons { display: flex; gap: 12px; }
.btn-nav, .btn-save, .btn-submit { padding: 8px 16px; border: 1px solid; border-radius: 4px; font-size: 14px; font-weight: 500; cursor: pointer; }
.btn-nav:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-prev { background: #fff; color: #495057; border-color: #ced4da; }
.btn-next { background: #0d6efd; color: #fff; border-color: #0d6efd; }
.btn-save { background: #6c757d; color: #fff; border-color: #6c757d; }
.btn-submit { background: #28a745; color: #fff; border-color: #28a745; }
.btn-save:disabled, .btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

/* Transaction Table Styles */
.transaction-section {
  margin-top: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.transaction-section h4 {
  margin: 0 0 16px 0;
  color: #495057;
  font-size: 16px;
  font-weight: 600;
}

.transaction-table-container {
  overflow-x: auto;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  background: white;
}

.transaction-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.transaction-table th {
  background: #e9ecef;
  color: #495057;
  font-weight: 600;
  padding: 12px 8px;
  text-align: left;
  border-bottom: 2px solid #dee2e6;
  white-space: nowrap;
}

.transaction-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #f1f3f4;
  vertical-align: top;
}

.transaction-table tbody tr:hover {
  background: #f8f9fa;
}

.amount-cell {
  text-align: right;
  font-weight: 600;
  color: #28a745;
}

.transaction-summary {
  margin-top: 16px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.transaction-summary p {
  margin: 4px 0;
  font-size: 14px;
  color: #495057;
}

.no-transactions {
  text-align: center;
  padding: 40px 20px;
  color: #6c757d;
  font-style: italic;
}

/* Responsive transaction table */
@media (max-width: 768px) {
  .transaction-table th,
  .transaction-table td {
    padding: 8px 4px;
    font-size: 12px;
  }
  
  .transaction-table th:nth-child(n+5),
  .transaction-table td:nth-child(n+5) {
    display: none;
  }
}

/* Responsive */
@media (max-width: 1200px) {
  .comparison-grid, .action-section-grid { grid-template-columns: 1fr; }
  .details-row { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
  .saved-data-grid { grid-template-columns: 1fr; }
}
</style>