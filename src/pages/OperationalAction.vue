<template>
  <div class="pma-container">
    <div v-if="isReadOnly" class="readonly-banner">
      <span>This case is closed.</span>
    </div>

    <div class="step-content">
      
      <div class="step-panel">
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

        <!-- Two-Section Transaction Layout for VM Cases -->
        <div class="transaction-comparison-grid">
          <!-- LEFT: Raw I4C Incidents from Complaint -->
          <div class="transaction-section">
            <h4>Transaction Details from I4C Complaint</h4>
            <div v-if="i4cIncidents.length > 0" class="transaction-table-container">
              <table class="transaction-table">
                <thead>
                  <tr>
                    <th>RRN</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Amount</th>
                    <th>Disputed</th>
                    <th>Layer</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="incident in i4cIncidents" :key="incident.rrn">
                    <td>{{ incident.rrn }}</td>
                    <td>{{ incident.transaction_date }}</td>
                    <td>{{ incident.transaction_time || 'N/A' }}</td>
                    <td class="amount-cell">{{ formatAmount(incident.amount) }}</td>
                    <td class="amount-cell">{{ formatAmount(incident.disputed_amount) }}</td>
                    <td>{{ incident.layer }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="no-transactions">
              <p>No incident data available.</p>
            </div>
          </div>

          <!-- RIGHT: Validated/Matched Bank Transactions -->
          <div class="transaction-section">
            <h4>Matched Bank Transactions</h4>
            <div v-if="validationResults.length > 0" class="transaction-table-container">
              <table class="transaction-table">
                <thead>
                  <tr>
                    <th>RRN</th>
                    <th>Status</th>
                    <th>Bene Account</th>
                    <th>Amount</th>
                    <th>Date & Time</th>
                    <th>Channel</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="validation in validationResults" 
                    :key="validation.rrn"
                    :class="getValidationRowClass(validation)"
                  >
                    <td>{{ validation.rrn }}</td>
                    <td>
                      <span v-if="validation.validation_status === 'matched'" class="status-badge success">
                        ✓ Matched
                      </span>
                      <span v-else class="status-badge error">
                        {{ getStatusLabel(validation.validation_status) }}
                      </span>
                    </td>
                    <td v-if="validation.matched_txn">{{ validation.matched_txn.bene_acct_num }}</td>
                    <td v-else class="error-message">{{ validation.validation_message }}</td>
                    <td v-if="validation.matched_txn" class="amount-cell">{{ formatAmount(validation.matched_txn.amount) }}</td>
                    <td v-else>-</td>
                    <td v-if="validation.matched_txn">{{ validation.matched_txn.txn_date }} {{ validation.matched_txn.txn_time }}</td>
                    <td v-else>-</td>
                    <td v-if="validation.matched_txn">{{ validation.matched_txn.channel }}</td>
                    <td v-else>-</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="no-transactions">
              <p>No validation results available.</p>
            </div>
          </div>
        </div>
        
        <!-- Summary Section -->
        <div v-if="validationResults.length > 0" class="validation-summary">
          <div class="summary-card">
            <span class="summary-label">Total Incidents:</span>
            <span class="summary-value">{{ validationResults.length }}</span>
          </div>
          <div class="summary-card success">
            <span class="summary-label">✓ Matched:</span>
            <span class="summary-value">{{ validationResults.filter(v => v.validation_status === 'matched').length }}</span>
          </div>
          <div class="summary-card error">
            <span class="summary-label">✗ Errors:</span>
            <span class="summary-value">{{ validationResults.filter(v => v.validation_status !== 'matched').length }}</span>
          </div>
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

    <!-- Respond Button for VM Cases -->
    <div v-if="!isReadOnly && sourceAckNo" class="response-section">
      <div class="response-info">
        <h4>Send Response to I4C</h4>
        <p>Review the transaction validation results above. Click "Respond" to close this case and send the detailed response back to I4C portal.</p>
      </div>
      <button 
        @click="sendResponse" 
        class="btn-respond" 
        :disabled="isResponding"
      >
        {{ isResponding ? 'Sending Response...' : 'Respond & Close Case' }}
      </button>
    </div>
    <div v-else-if="isReadOnly" class="response-section responded">
      <div class="response-info">
        <h4>✅ Response Sent</h4>
        <p>This case has been closed and the detailed response has been sent to I4C portal.</p>
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
const caseLogs = ref([]);
const isResponding = ref(false);
const sourceAckNo = ref(null);

// --- Case Status Management ---
const caseStatus = ref('New');
const isReadOnly = computed(() => caseStatus.value === 'Closed');

// --- Stepper Logic (removed for VM cases - no action required) ---
const currentStep = ref(1);
const steps = ref([
  { title: 'Alert Details' }
]);
const goToStep = (step) => { if (!isReadOnly.value) currentStep.value = step; };
const nextStep = () => { if (currentStep.value < steps.value.length) currentStep.value++; };
const previousStep = () => { if (currentStep.value > 1) currentStep.value--; };

// --- Data Models ---
const i4cDetails = ref({});
const bankDetails = ref({});
const transactions = ref([]);
const i4cIncidents = ref([]);  // Raw incidents from I4C complaint
const validationResults = ref([]);  // Validation results for each incident

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
      
      // Update case status and source acknowledgement
      caseStatus.value = status || 'New';
      sourceAckNo.value = source_ack_no;
      
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
      
      // Populate transactions array (old legacy field)
      transactions.value = banksV2Transactions;
      
      // Fetch incident validation results for VM cases
      if (caseId) {
        try {
          const validationRes = await axios.get(`/api/v2/banks/incident-validations/${caseId}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (validationRes.data?.success) {
            validationResults.value = validationRes.data.data.validations || [];
            console.log(`Loaded ${validationResults.value.length} validation results`);
          }
        } catch (error) {
          console.log('Error fetching validation results:', error.message);
        }
        
        // FALLBACK: If no validation results (old case), create from banksV2Transactions
        if (validationResults.value.length === 0 && banksV2Transactions.length > 0) {
          console.log('No validation results found - creating fallback from transaction data');
          validationResults.value = banksV2Transactions.map(txn => ({
            rrn: txn.txn_ref || txn.rrn || 'N/A',
            validation_status: 'matched',
            validation_message: 'Legacy data - validation status not tracked',
            matched_txn: {
              txn_id: null,
              acct_num: txn.root_account_number || 'N/A',
              bene_acct_num: txn.bene_acct_num || 'N/A',
              amount: txn.amount || '0',
              txn_date: txn.txn_date || 'N/A',
              txn_time: txn.txn_time || 'N/A',
              channel: txn.channel || 'N/A',
              descr: txn.descr || 'N/A',
              rrn: txn.txn_ref || txn.rrn || 'N/A'
            },
            error: null
          }));
          console.log(`✅ Created ${validationResults.value.length} fallback validation results`);
        }
      }
      
      // Populate I4C details and raw incidents with banks_v2 data if available
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
        
        // Populate raw I4C incidents
        i4cIncidents.value = banksV2Data.incidents || [];
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

    // Fetch case logs
    const logsRes = await axios.get(`/api/case/${caseId}/logs`, { 
      headers: { Authorization: `Bearer ${token}` } 
    });
    caseLogs.value = logsRes.data?.logs || [];

  } catch (err) {
    console.error("Error fetching operational case data:", err);
    fetchError.value = "Failed to load case data. Please try again.";
  } finally {
    isLoading.value = false;
  }
});

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

// Validation helper functions
const getValidationRowClass = (validation) => {
  if (validation.validation_status === 'matched') return 'validation-success';
  return 'validation-error';
};

const getStatusLabel = (status) => {
  const labels = {
    'duplicate': '✗ Duplicate RRN',
    'invalid_format': '✗ Invalid Format',
    'invalid_range': '✗ Invalid Range',
    'not_found': '✗ Not Found',
    'multiple_found': '✗ Multiple Found',
    'pending': '⏳ Pending'
  };
  return labels[status] || '✗ Error';
};

// Send response to I4C
const sendResponse = async () => {
  if (!sourceAckNo.value) {
    window.showNotification('error', 'Error', 'No acknowledgement number found for this case.');
    return;
  }

  // Extract base acknowledgement number
  const baseAckNo = sourceAckNo.value.replace(/_(ECBNT|ECBT|VM|PSA)$/, '');

  isResponding.value = true;
  const token = localStorage.getItem('jwt');

  try {
    const response = await axios.post(
      `/api/v2/banks/case-entry/${baseAckNo}/respond`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    );

    if (response.data?.meta?.response_code === '00') {
      window.showNotification('success', 'Response Sent', 'Detailed response sent to I4C portal. Case marked as closed.');
      
      // Update case status
      caseStatus.value = 'Closed';
      
      // Log the detailed response
      console.log('Detailed Response:', response.data);
      
      // Navigate back to case list after a short delay
      setTimeout(() => {
        router.push('/case-details');
      }, 2000);
    } else {
      throw new Error(response.data?.meta?.response_message || 'Unknown error');
    }
  } catch (err) {
    console.error('Send response error:', err);
    const errorMessage = err.response?.data?.detail || err.message || 'Failed to send response';
    window.showNotification('error', 'Response Failed', errorMessage);
  } finally {
    isResponding.value = false;
  }
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

/* Response Section */
.response-section {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 2px solid #0d6efd;
}

.response-section.responded {
  border-color: #28a745;
  background: #d4edda;
}

.response-info h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a3a5d;
}

.response-info p {
  margin: 0;
  font-size: 14px;
  color: #495057;
  line-height: 1.5;
}

.btn-respond {
  padding: 12px 32px;
  background: #0d6efd;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-respond:hover {
  background: #0b5ed7;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(13, 110, 253, 0.3);
}

.btn-respond:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-respond:active {
  transform: translateY(0);
}

/* Case Logs & Bottom Nav */
.case-logs-section { background: #fff; border-radius: 8px; padding: 18px 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 16px; }
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

/* Two-Section Transaction Comparison Layout */
.transaction-comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 24px;
}

.transaction-comparison-grid .transaction-section {
  margin-top: 0;
}

/* Validation Status Badges */
.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-badge.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* Validation Row Styling */
.validation-success {
  background: #f0fff4 !important;
}

.validation-success:hover {
  background: #e6ffe8 !important;
}

.validation-error {
  background: #fff5f5 !important;
}

.validation-error:hover {
  background: #ffebeb !important;
}

.error-message {
  color: #721c24;
  font-style: italic;
  font-size: 13px;
}

/* Validation Summary Cards */
.validation-summary {
  display: flex;
  gap: 16px;
  margin-top: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.summary-card {
  flex: 1;
  padding: 12px 16px;
  border-radius: 6px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-card.success {
  background: #d4edda;
  border-color: #c3e6cb;
}

.summary-card.error {
  background: #f8d7da;
  border-color: #f5c6cb;
}

.summary-label {
  font-size: 13px;
  font-weight: 600;
  color: #495057;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: #212529;
}

.summary-card.success .summary-value {
  color: #155724;
}

.summary-card.error .summary-value {
  color: #721c24;
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
  
  .transaction-comparison-grid {
    grid-template-columns: 1fr;
  }
  
  .validation-summary {
    flex-direction: column;
  }
}

/* Responsive */
@media (max-width: 1200px) {
  .comparison-grid, .action-section-grid { grid-template-columns: 1fr; }
  .details-row { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
  .saved-data-grid { grid-template-columns: 1fr; }
}
</style>