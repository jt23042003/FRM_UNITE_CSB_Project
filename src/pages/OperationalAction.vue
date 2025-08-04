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
        <div v-if="isLoading" class="loading-indicator">Loading Case Details...</div>
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
      </div>

      <div v-if="currentStep === 2" class="step-panel">
        <h3>Action</h3>
        <div v-if="isLoading" class="loading-indicator">Loading Action Items...</div>
        <div v-else class="action-section-grid">
          
          <div class="document-checklist">
            <h4>I4C Requirements</h4>
            <ul class="document-list">
              <li v-for="doc in documentList" :key="doc.id">
                <label>
                  <input type="checkbox" v-model="doc.checked" :disabled="isReadOnly" />
                  <span>{{ doc.name }}</span>
                </label>
              </li>
            </ul>
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
            </div>
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

    <div class="bottom-navigation">
      <div class="nav-buttons">
        <button @click="previousStep" :disabled="currentStep === 1" class="btn-nav btn-prev">Previous</button>
        <button @click="nextStep" v-if="currentStep < steps.length" class="btn-nav btn-next">Next</button>
      </div>
      <div class="action-buttons">
        <button v-if="!isReadOnly" @click="saveAction" class="btn-save" :disabled="isSaving">Save</button>
        <button
          v-if="!isReadOnly"
          @click="submitAction"
          class="btn-submit"
          :disabled="!isSubmittable || isSaving"
          title="You must save the case before you can submit it."
        >
          Submit
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

// --- NEW State Management for Status ---
const caseStatus = ref(route.query.status || 'New');
const isReadOnly = computed(() => caseStatus.value === 'Closed');
const isSubmittable = computed(() => caseStatus.value === 'Open');

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

const caseId = route.params.case_id;

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
    const [caseDataRes, docListRes, logsRes, savedActionRes] = await Promise.all([
      axios.get(`/api/combined-case-data/${caseId}`, { headers: { Authorization: `Bearer ${token}` } }),
      axios.get('/api/i4c-document-list', { headers: { Authorization: `Bearer ${token}` } }),
      axios.get(`/api/case/${caseId}/logs`, { headers: { Authorization: `Bearer ${token}` } }),
      // Fetch saved data if the case is not 'New'
      caseStatus.value !== 'New' ? axios.get(`/api/case/${caseId}/action-log`, { headers: { Authorization: `Bearer ${token}` } }) : Promise.resolve(null)
    ]);

    if (caseDataRes.data) {
      const { i4c_data = {}, customer_details = {}, account_details = {}, acc_num } = caseDataRes.data;
      i4cDetails.value = {
        name: i4c_data.customer_name || 'N/A',
        mobileNumber: i4c_data.mobile || 'N/A',
        bankAc: i4c_data.account_number || 'N/A',
        email: i4c_data.email || 'N/A',
      };
      bankDetails.value = {
        name: `${customer_details.fname || ''} ${customer_details.mname || ''} ${customer_details.lname || ''}`.trim() || 'N/A',
        mobileNumber: customer_details.mobile || 'N/A',
        bankAc: acc_num || 'N/A',
        email: customer_details.email || 'N/A',
        customerId: customer_details.cust_id || 'N/A',
        acStatus: account_details?.acc_status || 'N/A',
        aqb: account_details?.aqb || 'N/A',
        availBal: account_details?.availBal || 'N/A',
        productCode: account_details?.productCode || 'N/A',
        relValue: customer_details?.rel_value || 'N/A',
        mobVintage: customer_details?.mob || 'N/A',
      };
    }

    if (docListRes.data?.success) {
      documentList.value = docListRes.data.documents.map(doc => ({
        id: doc.seq_id,
        name: doc.file_name,
        checked: false,
      }));
    }

    caseLogs.value = logsRes.data?.logs || [];

    // Pre-fill form if data was fetched for 'Open' or 'Closed' cases
    if (savedActionRes?.data?.success && savedActionRes.data.data) {
      const savedData = savedActionRes.data.data;
      referenceNo.value = savedData.proof_of_upload_ref || '';
      const checkedDocs = savedData.checked_documents || [];
      documentList.value.forEach(doc => {
        if (checkedDocs.includes(doc.name)) {
          doc.checked = true;
        }
      });
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
  screenshotFile.value = event.target.files[0] || null;
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
  isSaving.value = true;
  const formData = createActionPayload();
  formData.append('confirmation_action_status', 'saved');

  try {
    const response = await axios.post('/api/operational-confirm', formData, {
      headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` },
    });
    if (response.data.success) {
      alert('Case data saved successfully! You can now submit.');
      if (response.data.new_status) {
        caseStatus.value = response.data.new_status; // This should be 'Open'
      }
    } else {
      throw new Error(response.data.message || 'Unknown error');
    }
  } catch (err) {
    console.error('Save action error:', err);
    alert(`Failed to save data: ${err.message}`);
  } finally {
    isSaving.value = false;
  }
};

const submitAction = async () => {
  if (!isSubmittable.value) { // Safety check
      alert('You must save the case before submitting.');
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
      alert('Case submitted successfully!');
      caseStatus.value = 'Closed'; // Update status before navigating away
      router.push('/case-details');
    } else {
      throw new Error(response.data.message || 'Unknown error');
    }
  } catch (err) {
    console.error('Submit action error:', err);
    alert(`Failed to submit case: ${err.message}`);
  } finally {
    isSaving.value = false;
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
.document-list { list-style: none; padding: 0; margin: 0; max-height: 200px; overflow-y: auto; }
.document-list li { margin-bottom: 12px; }
.document-list label { display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 14px; }
.document-list input[type="checkbox"] { width: 18px; height: 18px; accent-color: #0d6efd; }
.reference-upload { display: flex; flex-direction: column; gap: 24px; }
.action-input { padding: 8px 10px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background: #fff; }
.screenshot-uploader { display: flex; align-items: center; gap: 12px; }
.btn-browse { padding: 6px 12px; border: 1px solid #0d6efd; background-color: #e7f3ff; color: #0d6efd; border-radius: 4px; cursor: pointer; font-weight: 500; }
.hidden-file-input { display: none; }
.file-name-display { font-size: 13px; color: #6c757d; font-style: italic; }

/* Case Logs & Bottom Nav */
.case-logs-section, .bottom-navigation { background: #fff; border-radius: 8px; padding: 18px 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: auto; }
.case-logs-section h4 { margin: 0 0 12px 0; font-size: 16px; color: #1a3a5d; }
.case-log-list { list-style: none; padding: 0; margin: 0; }
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

/* Responsive */
@media (max-width: 1200px) {
  .comparison-grid, .action-section-grid { grid-template-columns: 1fr; }
  .details-row { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
}
</style>