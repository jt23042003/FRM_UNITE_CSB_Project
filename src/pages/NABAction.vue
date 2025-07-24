<template>
  <div class="pma-container">
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
        <h3>Alert - NAB Action</h3>

        <div v-if="isLoading" class="loading-indicator">Loading Case Details...</div>
        <div v-else-if="fetchError" class="error-indicator">{{ fetchError }}</div>

        <div v-else>
            <div class="comparison-grid">
                <div class="details-section">
                    <h4>Customer Details - I4C</h4>
                    <div class="details-row">
                        <div class="field-group"><label>Name</label><input type="text" v-model="i4cDetails.name" readonly /></div>
                        <div class="field-group"><label>Mobile</label><input type="text" v-model="i4cDetails.mobileNumber" readonly /></div>
                        <div class="field-group"><label>Email</label><input type="text" v-model="i4cDetails.email" readonly /></div>
                    </div>
                    <div class="details-row">
                        <div class="field-group"><label>IFSC Code</label><input type="text" v-model="i4cDetails.ifscCode" readonly /></div>
                        <div class="field-group"><label>Beneficiary A/c</label><input type="text" v-model="i4cDetails.beneficiaryAccount" readonly /></div>
                        <div class="field-group"><label>Bank Name</label><input type="text" v-model="i4cDetails.bankName" readonly /></div>
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
                        <div class="field-group"><label>IFSC Code</label><input type="text" v-model="bankDetails.ifscCode" readonly /></div>
                        <div class="field-group"><label>Beneficiary A/c</label><input type="text" v-model="bankDetails.beneficiaryAccount" readonly /></div>
                        <div class="field-group"><label>Bank Name</label><input type="text" v-model="bankDetails.bankName" readonly /></div>
                    </div>
                    <div class="details-row">
                        <div class="field-group"><label>Customer ID</label><input type="text" v-model="bankDetails.customerId" readonly /></div>
                        <div class="field-group"><label>Account Status</label><input type="text" v-model="bankDetails.acStatus" readonly /></div>
                        <div class="field-group"><label>Product Code</label><input type="text" v-model="bankDetails.productCode" readonly /></div>
                    </div>
                    <div class="details-row">
                        <div class="field-group"><label>AQB</label><input type="text" v-model="bankDetails.aqb" readonly /></div>
                        <div class="field-group"><label>Available Balance</label><input type="text" v-model="bankDetails.availBal" readonly /></div>
                        <div class="field-group"><label>Relationship Value</label><input type="text" v-model="bankDetails.relValue" readonly /></div>
                    </div>
                    <div class="details-row">
                        <div class="field-group"><label>Vintage (MoB)</label><input type="text" v-model="bankDetails.mobVintage" readonly /></div>
                    </div>
                    <div class="details-row">
                        <div class="field-group"><label>Addl field1</label><input type="text" v-model="bankDetails.addl1" readonly /></div>
                        <div class="field-group"><label>Addl field2</label><input type="text" v-model="bankDetails.addl2" readonly /></div>
                        <div class="field-group"><label>Addl field4</label><input type="text" v-model="bankDetails.addl4" readonly /></div>
                    </div>
                </div>
            </div>

            <div class="details-section beneficiary-table-section">
                <h4>Transaction Details</h4>
                <div class="table-container">
                    <table class="details-table">
                    <thead>
                        <tr><th>Date</th><th>Time</th><th>Beneficiary</th><th>Amount</th><th>Mode</th><th>Txn. Ref #</th><th>Txn Description</th></tr>
                    </thead>
                    <tbody>
                        <tr v-for="txn in transactionDetails" :key="txn.txn_ref" :class="{ 'highlight-row': txn.is_bene_match }">
                            <td>{{ txn.txn_date || '-' }}</td>
                            <td>{{ txn.txn_time || '-' }}</td>
                            <td>{{ txn.bene_acct_num || '-' }}</td>
                            <td>{{ txn.amount ? '₹' + Number(txn.amount).toLocaleString('en-IN') : '-' }}</td>
                            <td>{{ txn.channel || '-' }}</td>
                            <td>{{ txn.txn_ref || '-' }}</td>
                            <td>{{ txn.descr || '-' }}</td>
                        </tr>
                        <tr v-if="!transactionDetails.length"><td colspan="7" class="no-data-cell">No transactions found.</td></tr>
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="6">Total Value @ Risk</td>
                            <td>₹{{ totalValueAtRisk ? totalValueAtRisk.toLocaleString('en-IN') : '0.00' }}</td>
                        </tr>
                    </tfoot>
                    </table>
                </div>
            </div>
        </div>
      </div>

      <div v-if="currentStep === 2" class="step-panel">
        <h3>Analysis & Investigation</h3>
        <div class="form-grid">
          <div class="form-section">
            <div class="field-group">
              <label>Analysis Update</label>
              <div class="input-row">
                <select v-model="action.analysisLOV" class="compact-select">
                  <option value="">Select Reason</option>
                  <option v-for="item in analysisReasons" :key="item.reason" :value="item.reason">{{ item.reason }}</option>
                </select>
                <textarea v-model="action.analysisUpdate" placeholder="Update details" class="compact-textarea"></textarea>
              </div>
            </div>

            <div class="field-group">
              <label>Data Uploads</label>
              
              <div v-for="(uploadBlock, blockIndex) in action.dataUploads" :key="uploadBlock.id" class="data-upload-block">
                
                <button @click="removeDataUploadBlock(blockIndex)" v-if="action.dataUploads.length > 1" class="btn-remove-row" title="Remove Upload Section">×</button>

                <textarea v-model="uploadBlock.comment" placeholder="Add comments for your uploads..." class="compact-textarea data-uploads-textarea"></textarea>
                
                <div class="file-upload-container">
                  <div
                    class="file-drop-zone"
                    :class="{ 'drag-over': uploadBlock.isDragOver, 'has-files': uploadBlock.files.length > 0 }"
                    @dragover.prevent="onDragOver(blockIndex)"
                    @dragleave.prevent="onDragLeave(blockIndex)"
                    @drop.prevent="onFileDrop($event, blockIndex)"
                    @click="triggerFileInput(blockIndex)"
                  >
                    <div class="upload-icon">📁</div>
                    <div class="upload-text">
                      <strong>Drop files here or click to browse</strong>
                      <p>Supports: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG (Max 10MB each)</p>
                    </div>
                    <input
                      :ref="el => { if (el) fileInputRefs[blockIndex] = el }"
                      type="file"
                      multiple
                      accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
                      @change="onFileSelect($event, blockIndex)"
                      class="hidden-file-input"
                    />
                  </div>
                  <div v-if="uploadBlock.files.length > 0" class="uploaded-files-list">
                    <div class="files-header">
                      <span>Uploaded Files ({{ uploadBlock.files.length }})</span>
                    </div>
                    <div
                      v-for="(file, fileIndex) in uploadBlock.files"
                      :key="fileIndex"
                      class="file-item"
                    >
                      <div class="file-info">
                        <div class="file-icon">{{ getFileIcon(file.type) }}</div>
                        <div class="file-details">
                          <div class="file-name-container">
                            <input
                              v-if="file.isRenaming"
                              v-model="file.newName"
                              @blur="saveFileName(blockIndex, fileIndex)"
                              @keyup.enter="saveFileName(blockIndex, fileIndex)"
                              @keyup.escape="cancelRename(blockIndex, fileIndex)"
                              class="file-name-input"
                              placeholder="Enter new name"
                            />
                            <span v-else class="file-name">{{ file.displayName }}</span>
                          </div>
                          <div class="file-meta">
                            {{ formatFileSize(file.size) }} • {{ file.type.split('/')[1].toUpperCase() }}
                          </div>
                        </div>
                      </div>
                      <div class="file-actions">
                         <button
                          v-if="!file.isRenaming"
                          @click="startRename(blockIndex, fileIndex)"
                          class="btn-file-action btn-rename"
                          title="Rename file"
                        >✏️</button>
                        <button
                          v-if="file.isRenaming"
                          @click="saveFileName(blockIndex, fileIndex)"
                          class="btn-file-action btn-save"
                          title="Save name"
                        >✅</button>
                        <button
                          v-if="file.isRenaming"
                          @click="cancelRename(blockIndex, fileIndex)"
                          class="btn-file-action btn-cancel"
                          title="Cancel rename"
                        >❌</button>
                        <button
                          @click="removeFile(blockIndex, fileIndex)"
                          class="btn-file-action btn-remove"
                          title="Remove file"
                        >🗑️</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <button @click="addDataUploadBlock" class="btn-add-row">+ Add Upload Section</button>
            </div>
            </div>
          <div class="form-section">
            <div class="field-group">
              <label>Review Comments</label>
              <div v-for="(review, index) in action.reviews" :key="review.id" class="review-comment-row">
                 <div class="comment-user-selection-row">
                    <select v-model="review.selectedDepartment" class="compact-select" @change="handleDepartmentChange(review)">
                      <option value="">Select Department</option>
                      <option v-for="dept in departments" :key="dept.id" :value="dept.name">{{ dept.name }}</option>
                    </select>
                    <select v-model="review.userId" class="compact-select" :disabled="!review.selectedDepartment">
                      <option value="">Select User</option>
                      <option v-for="user in review.userList" :key="user.id" :value="user.id">{{ user.name }}</option>
                    </select>
                 </div>
                 <textarea v-model="review.text" placeholder="Add comments..." class="compact-textarea"></textarea>
                 <button @click="removeReviewCommentRow(index)" v-if="action.reviews.length > 1" class="btn-remove-row" title="Remove Assignment">×</button>
              </div>
              <button @click="addReviewCommentRow" class="btn-add-row">+ Add Assignment</button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="currentStep === 3" class="step-panel">
        <h3>Final Closure</h3>
        <div class="form-grid">
          <div class="form-section">
            <div class="field-group">
              <label>Closure Remarks</label>
              <div class="input-row">
                <select v-model="action.closureLOV" class="compact-select">
                  <option value="">Select Reason</option>
                  <option v-for="item in closureReasons" :key="item.reason" :value="item.reason">{{ item.reason }}</option>
                </select>
                <textarea v-model="action.closureRemarks" placeholder="Closure remarks" class="compact-textarea"></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="currentStep === 4" class="step-panel">
        <h3>Confirmation</h3>
        <div class="confirmation-grid">
          <div class="confirm-section">
            <div class="confirm-row">
              <label>Confirmed Mule</label>
              <div class="radio-group">
                <label><input type="radio" v-model="action.confirmedMule" value="Yes" name="confirmedMule" /> Yes</label>
                <label><input type="radio" v-model="action.confirmedMule" value="No" name="confirmedMule" /> No</label>
              </div>
            </div>
            <div class="confirm-row">
              <label>Funds Saved</label>
              <input type="number" v-model="action.fundsSaved" :disabled="action.confirmedMule !== 'Yes'" class="compact-input" placeholder="Amount"/>
            </div>
          </div>
          <div class="confirm-section">
            <div class="confirm-row">
              <label>Digital Channel Blocked</label>
              <div class="radio-group">
                <label><input type="radio" v-model="action.digitalBlocked" value="Yes" name="digitalBlocked" /> Yes</label>
                <label><input type="radio" v-model="action.digitalBlocked" value="No" name="digitalBlocked" /> No</label>
              </div>
            </div>
            <div class="confirm-row">
              <label>Account Blocked</label>
              <div class="radio-group">
                <label><input type="radio" v-model="action.accountBlocked" value="Yes" name="accountBlocked" /> Yes</label>
                <label><input type="radio" v-model="action.accountBlocked" value="No" name="accountBlocked" /> No</label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bottom-navigation">
        <button @click="previousStep" :disabled="currentStep === 1" class="btn-nav btn-prev">Previous</button>
        <button @click="nextStep" v-if="currentStep < steps.length" class="btn-nav btn-next">Next</button>
      <div class="action-buttons">
        <button @click="saveAction" class="btn-save">Save</button>
        <button @click="submitAction" class="btn-submit">Submit</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

const route = useRoute();

// --- State Management ---
const isLoading = ref(true);
const fetchError = ref(null);
const currentStep = ref(1);

// --- Dropdown Data ---
const analysisReasons = ref([]);
const departments = ref([]);
const closureReasons = ref([]);

// --- Stepper Logic ---
const steps = ref([
  { title: 'Alert Details' },
  { title: 'Analysis' },
  { title: 'Closure' },
  { title: 'Confirmation' }
]);
const goToStep = (step) => { if (!isLoading.value || step === 1) currentStep.value = step; };
const nextStep = () => { if (currentStep.value < steps.value.length) currentStep.value++; };
const previousStep = () => { if (currentStep.value > 1) currentStep.value--; };

// --- Data Models for NAB ---
const i4cDetails = ref({
    name: '', mobileNumber: '', email: '', ifscCode: '',
    beneficiaryAccount: '', bankName: ''
});
const bankDetails = ref({
  name: '', mobileNumber: '', email: '', ifscCode: '', beneficiaryAccount: '', bankName: '',
  customerId: '', acStatus: '', aqb: '', availBal: '', productCode: '', relValue: '',
  mobVintage: '', addl1: '', addl2: '', addl4: ''
});
const transactionDetails = ref([]);
const action = ref({
  analysisLOV: '',
  analysisUpdate: '',
  dataUploads: [{ id: Date.now(), comment: '', files: [], isDragOver: false }],
  reviews: [{ id: Date.now(), selectedDepartment: '', userId: '', text: '', userList: [] }],
  closureLOV: '',
  closureRemarks: '',
  confirmedMule: 'No',
  fundsSaved: null,
  digitalBlocked: 'No',
  accountBlocked: 'No',
});

// --- Computed Property for Total ---
const totalValueAtRisk = computed(() => {
  return transactionDetails.value.reduce((total, txn) => total + Number(txn.amount || 0), 0);
});

// --- Dynamic Row Logic (Reviews) ---
const addReviewCommentRow = () => {
  action.value.reviews.push({
    id: Date.now(),
    selectedDepartment: '',
    userId: '',
    text: '',
    userList: []
  });
};
const removeReviewCommentRow = (index) => {
  if (action.value.reviews.length > 1) {
    action.value.reviews.splice(index, 1);
  }
};
const handleDepartmentChange = async (review) => {
  review.userId = '';
  review.userList = [];
  if (review.selectedDepartment) {
    try {
      const response = await axios.get(`/api/users?department_name=${review.selectedDepartment}`);
      if (response.data && Array.isArray(response.data)) {
        review.userList = response.data;
      }
    } catch (err) {
      console.error(`Failed to fetch users for department ${review.selectedDepartment}:`, err);
    }
  }
};

// --- Dynamic Upload Block Logic ---
const addDataUploadBlock = () => {
  action.value.dataUploads.push({
    id: Date.now(),
    comment: '',
    files: [],
    isDragOver: false
  });
};
const removeDataUploadBlock = (blockIndex) => {
  if (action.value.dataUploads.length > 1) {
    action.value.dataUploads.splice(blockIndex, 1);
  }
};

// --- File Upload Logic ---
const fileInputRefs = ref([]); // Use an array of refs for file inputs

const getFileIcon = (type) => {
  if (type.startsWith('image/')) return '📸';
  if (type.startsWith('application/pdf')) return '📄';
  if (type.startsWith('application/msword') || type.startsWith('application/vnd.openxmlformats-officedocument.wordprocessingml.document')) return '📝';
  if (type.startsWith('application/vnd.ms-excel') || type.startsWith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) return '📊';
  return '📁';
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const triggerFileInput = (blockIndex) => {
  if(fileInputRefs.value[blockIndex]) {
    fileInputRefs.value[blockIndex].click();
  }
};

const addFiles = (files, blockIndex) => {
  const uploadBlock = action.value.dataUploads[blockIndex];
  files.forEach(file => {
    uploadBlock.files.push({ file, displayName: file.name, newName: file.name, size: file.size, type: file.type, isRenaming: false });
  });
};

const onFileSelect = (event, blockIndex) => {
  addFiles(Array.from(event.target.files), blockIndex);
  event.target.value = '';
};

const onDragOver = (blockIndex) => action.value.dataUploads[blockIndex].isDragOver = true;
const onDragLeave = (blockIndex) => action.value.dataUploads[blockIndex].isDragOver = false;
const onFileDrop = (event, blockIndex) => {
  action.value.dataUploads[blockIndex].isDragOver = false;
  addFiles(Array.from(event.dataTransfer.files), blockIndex);
};

const startRename = (blockIndex, fileIndex) => action.value.dataUploads[blockIndex].files[fileIndex].isRenaming = true;
const saveFileName = (blockIndex, fileIndex) => {
  const file = action.value.dataUploads[blockIndex].files[fileIndex];
  file.displayName = file.newName;
  file.isRenaming = false;
};
const cancelRename = (blockIndex, fileIndex) => {
  const file = action.value.dataUploads[blockIndex].files[fileIndex];
  file.newName = file.displayName;
  file.isRenaming = false;
};
const removeFile = (blockIndex, fileIndex) => {
  action.value.dataUploads[blockIndex].files.splice(fileIndex, 1);
};

// --- API Integration ---
const fetchAnalysisReasons = async () => {
  try {
    const response = await axios.get('http://34.47.219.225:9000/reasons/api/investigation-review');
    if (response.data) analysisReasons.value = response.data;
  } catch (err) { console.error("Failed to fetch analysis reasons:", err); }
};
const fetchDepartments = async () => {
  try {
    const response = await axios.get('/api/departments');
    if (response.data) departments.value = response.data;
  } catch (err) { console.error("Failed to fetch departments:", err); }
};
const fetchClosureReasons = async () => {
  try {
    const response = await axios.get('http://34.47.219.225:9000/reasons/api/final-closure');
    if (response.data) closureReasons.value = response.data;
  } catch (err) { console.error("Failed to fetch closure reasons:", err); }
};
const fetchCaseDetails = async () => {
  const caseId = route.params.case_id;
  const token = localStorage.getItem('jwt');
  if (!token) throw new Error('No authentication token found');
  const response = await axios.get(`/api/combined-case-data/${caseId}`, { headers: { 'Authorization': `Bearer ${token}` } });
  
  if (response.data) {
    const data = response.data;
    const i4cData = data.i4c_data || {};
    const customerDetails = data.customer_details || {};
    
    i4cDetails.value = {
        name: i4cData.customer_name || 'N/A',
        mobileNumber: i4cData.mobile || 'N/A',
        email: i4cData.email || 'N/A',
        ifscCode: i4cData.ifsc || 'N/A',
        beneficiaryAccount: i4cData.to_account || 'N/A',
        bankName: i4cData.to_bank || 'N/A'
    };
    
    bankDetails.value = {
        name: `${customerDetails.fname || ''} ${customerDetails.mname || ''} ${customerDetails.lname || ''}`.trim() || 'N/A',
        mobileNumber: customerDetails.mobile || 'N/A',
        email: customerDetails.email || 'N/A',
        ifscCode: customerDetails.ifsc || 'N/A',
        beneficiaryAccount: data.source_bene_accno || 'N/A',
        bankName: i4cData.to_bank || 'N/A',
        customerId: customerDetails.cust_id || 'N/A',
        acStatus: data.account_details?.acc_status || 'N/A',
        aqb: data.account_details?.aqb || 'N/A',
        availBal: data.account_details?.availBal || 'N/A',
        productCode: data.account_details?.productCode || 'N/A',
        relValue: data.account_details?.rel_value || 'N/A',
        mobVintage: data.account_details?.mob || 'N/A',
        addl1: data.account_details?.addl1 || 'N/A',
        addl2: data.account_details?.addl2 || 'N/A',
        addl4: data.account_details?.addl4 || 'N/A'
    };
    
    transactionDetails.value = data.transactions || [];
    if (data.action_details) {
      Object.assign(action.value, data.action_details);
      // Ensure dataUploads is an array, if loading saved data
      if (!Array.isArray(action.value.dataUploads) || action.value.dataUploads.length === 0) {
        action.value.dataUploads = [{ id: Date.now(), comment: '', files: [], isDragOver: false }];
      }
    }
  } else { 
    throw new Error('Received no data for this case.'); 
  }
};

onMounted(async () => {
  isLoading.value = true;
  fetchError.value = null;
  try {
    await Promise.all([
      fetchCaseDetails(),
      fetchAnalysisReasons(),
      fetchDepartments(),
      fetchClosureReasons()
    ]);
  } catch (error) {
    console.error('Error during component mount:', error);
    fetchError.value = 'Failed to load case details. Please try again later.';
  } finally {
    isLoading.value = false;
  }
});

// --- Action Buttons ---
const saveAction = async () => {
  console.log('Saving action:', action.value);
};
const submitAction = async () => {
  console.log('Submitting action:', action.value);
};
</script>

<style scoped>
/* Main Container */
.pma-container {
  height: 100vh;
  overflow: hidden;
  margin-left: 0px;
  padding: 16px;
  background: #f8f9fa;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

/* Progress Steps Header */
.steps-header {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.steps-container {
  display: flex;
  justify-content: space-between;
  max-width: 800px;
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
.step:hover {
  background: #f8f9fa;
}
.step.active {
  background: #0d6efd;
  color: white;
}
.step.completed {
  background: #28a745;
  color: white;
}
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
.step.active .step-number, .step.completed .step-number {
  background: rgba(255,255,255,0.3);
}
.step-title {
  font-size: 14px;
  font-weight: 500;
}

/* Step Content Panel */
.step-content {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow-y: auto;
  max-height: calc(100vh - 180px);
}
.step-panel h3 {
  margin: 0 0 20px 0;
  color: #1a1a1a;
  font-size: 20px;
  font-weight: 600;
  padding-bottom: 12px;
  border-bottom: 2px solid #e9ecef;
}

/* Loading and Error Indicators */
.loading-indicator, .error-indicator {
  text-align: center;
  padding: 40px;
  font-size: 16px;
  color: #6c757d;
}
.error-indicator {
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
}

/* Grids for Layout */
.comparison-grid, .form-grid, .confirmation-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.details-section {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 16px;
  border: 1px solid #e9ecef;
}
.details-section h4 {
  margin: 0 0 12px 0;
  color: #495057;
  font-size: 16px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid #dee2e6;
}
.details-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}
.details-row:last-child {
  margin-bottom: 0;
}

/* Transaction/Beneficiary Table */
.beneficiary-table-section {
    margin-top: 24px;
}
.table-container {
    width: 100%;
    overflow-x: auto;
}
.details-table {
    width: 100%;
    border-collapse: collapse;
}
.details-table tbody tr.highlight-row {
  background-color: #fff3cd; /* A light yellow highlight */
  font-weight: 500;
}
.details-table th, .details-table td {
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid #e9ecef;
    font-size: 13px;
    white-space: nowrap;
}
.details-table th {
    background-color: #f8fafc;
    font-weight: 600;
    color: #495057;
}
.details-table tfoot td {
    font-weight: bold;
    text-align: right;
    font-size: 1.1em;
    background-color: #f8fafc;
    border-top: 2px solid #e2e8f0;
}
.details-table tfoot td:last-child {
    text-align: left;
}
.no-data-cell {
    text-align: center;
    color: #6c757d;
    padding: 20px;
}

/* Form Elements */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.field-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field-group label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  margin-bottom: 6px;
}
.field-group input[type="text"], .field-group input[type="number"] {
  padding: 6px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  background: #e9ecef;
  height: 32px;
  box-sizing: border-box;
}
.field-group.highlight input {
  background: #fff3cd;
  border-color: #ffc107;
  font-weight: 500;
}
.input-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 12px;
  align-items: start;
}
.compact-select, .compact-input, .compact-textarea {
  padding: 6px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  background: #fff;
  height: 32px;
  box-sizing: border-box;
}
.compact-input {
  background: #fff;
}
.compact-textarea {
  min-height: 60px;
  max-height: 80px;
  resize: vertical;
  font-family: inherit;
}
.data-uploads-textarea {
  margin-bottom: 12px;
}

/* Dynamic Upload Block Style */
.data-upload-block {
  position: relative;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fdfdfd;
}

/* Comment/Assignment Rows */
.comment-user-selection-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}
.review-comment-row {
  position: relative;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
}
.btn-add-row {
  width: 100%;
  padding: 8px;
  background-color: #e7f3ff;
  color: #0d6efd;
  border: 1px dashed #0d6efd;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  margin-top: 4px;
}
.btn-add-row:hover {
  background-color: #d1e7ff;
}
.btn-remove-row {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid #dc3545;
  background-color: #fff;
  color: #dc3545;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  z-index: 10;
}

/* Confirmation Screen Styles */
.confirm-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.confirm-row {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 12px;
  align-items: center;
}
.confirm-row label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
}
.radio-group {
  display: flex;
  gap: 20px;
  align-items: center;
  height: 100%;
}
.radio-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  font-size: 13px;
  cursor: pointer;
}
.radio-group input[type="radio"] {
  accent-color: #0d6efd;
}

/* File Upload Styles */
.file-upload-container {
  border: 2px dashed #ced4da;
  border-radius: 6px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #f8f9fa;
}
.file-drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.file-drop-zone.drag-over {
  border-color: #0d6efd;
  background: #e9ecef;
}
.upload-icon {
  font-size: 48px;
  color: #0d6efd;
  margin-bottom: 10px;
}
.upload-text {
  font-size: 14px;
  color: #6c757d;
}
.hidden-file-input { display: none; }
.uploaded-files-list {
  margin-top: 15px;
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  max-height: 150px;
  overflow-y: auto;
  text-align: left;
}
.files-header {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  padding: 8px 12px;
  border-bottom: 1px solid #dee2e6;
}
.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #e9ecef;
}
.file-item:last-child { border-bottom: none; }
.file-info { display: flex; align-items: center; gap: 10px; }
.file-icon { font-size: 24px; }
.file-details { display: flex; flex-direction: column; }
.file-name-container { display: flex; align-items: center; gap: 5px; }
.file-name-input { padding: 4px 6px; border: 1px solid #ced4da; border-radius: 4px; font-size: 13px; }
.file-meta { font-size: 12px; color: #6c757d; }
.file-actions { display: flex; gap: 5px; }
.btn-file-action { background: none; border: none; cursor: pointer; padding: 4px; font-size: 16px;}

/* Bottom Navigation */
.bottom-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 -2px 4px rgba(0,0,0,0.05);
  margin-top: auto;
}
.nav-buttons, .action-buttons {
  display: flex;
  gap: 12px;
}
.btn-nav, .btn-save, .btn-submit {
  padding: 8px 16px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-nav:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-prev { background: #fff; color: #495057; }
.btn-next { background: #0d6efd; color: #fff; border-color: #0d6efd; }
.btn-save { background: #6c757d; color: #fff; border-color: #6c757d; }
.btn-submit { background: #28a745; color: #fff; border-color: #28a745; }

/* Responsive Design */
@media (max-width: 1200px) {
  .comparison-grid, .form-grid, .confirmation-grid { grid-template-columns: 1fr; }
  .details-row { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
  .input-row, .comment-user-selection-row { grid-template-columns: 1fr; gap: 8px; }
}
@media (max-width: 768px) {
  .pma-container { padding: 12px; }
  .steps-container { flex-direction: column; gap: 8px; }
  .step { justify-content: flex-start; }
  .details-row, .confirm-row { grid-template-columns: 1fr; }
  .bottom-navigation { flex-direction: column; gap: 12px; }
  .nav-buttons, .action-buttons { width: 100%; justify-content: center; }
}

/* Custom Scrollbar */
.step-content::-webkit-scrollbar { width: 6px; }
.step-content::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 3px; }
.step-content::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 3px; }
.step-content::-webkit-scrollbar-thumb:hover { background: #a8a8a8; }
</style>