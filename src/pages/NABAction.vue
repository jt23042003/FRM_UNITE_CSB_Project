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
        <h3>Alert - NAB Action</h3>

        <div v-if="isLoading" class="loading-indicator">Loading Case Details...</div>
        <div v-else-if="fetchError" class="error-indicator">{{ fetchError }}</div>

        <div v-else>
            <div class="comparison-grid">
                <div class="details-section">
                    <h4>Customer Details - I4C</h4>
                    <div class="details-row">
                        <div class="field-group"><label>Name</label><input type="text" v-model="i4cDetails.name" :readonly="isReadOnly" /></div>
                        <div class="field-group"><label>Mobile</label><input type="text" v-model="i4cDetails.mobileNumber" :readonly="isReadOnly" /></div>
                        <div class="field-group"><label>Email</label><input type="text" v-model="i4cDetails.email" :readonly="isReadOnly" /></div>
                    </div>
                    <div class="details-row">
                        <div class="field-group"><label>IFSC Code</label><input type="text" v-model="i4cDetails.ifscCode" :readonly="isReadOnly" /></div>
                        <div class="field-group"><label>Beneficiary A/c</label><input type="text" v-model="i4cDetails.beneficiaryAccount" :readonly="isReadOnly" /></div>
                        <div class="field-group"><label>Bank Name</label><input type="text" v-model="i4cDetails.bankName" :readonly="isReadOnly" /></div>
                    </div>
                </div>

                <div class="details-section">
                    <h4>Customer Details - Bank</h4>
                    <div class="details-row">
                        <div class="field-group highlight"><label>Name</label><input type="text" v-model="bankDetails.name" :readonly="isReadOnly" /></div>
                        <div class="field-group highlight"><label>Mobile</label><input type="text" v-model="bankDetails.mobileNumber" :readonly="isReadOnly" /></div>
                        <div class="field-group highlight"><label>Email</label><input type="text" v-model="bankDetails.email" :readonly="isReadOnly" /></div>
                    </div>
                     <div class="details-row">
                        <div class="field-group"><label>IFSC Code</label><input type="text" v-model="bankDetails.ifscCode" :readonly="isReadOnly" /></div>
                        <div class="field-group"><label>Beneficiary A/c</label><input type="text" v-model="bankDetails.beneficiaryAccount" :readonly="isReadOnly" /></div>
                        <div class="field-group"><label>Bank Name</label><input type="text" v-model="bankDetails.bankName" :readonly="isReadOnly" /></div>
                    </div>
                    <div class="details-row">
                        <div class="field-group"><label>Customer ID</label><input type="text" v-model="bankDetails.customerId" :readonly="isReadOnly" /></div>
                        <div class="field-group"><label>Account Status</label><input type="text" v-model="bankDetails.acStatus" :readonly="isReadOnly" /></div>
                        <div class="field-group"><label>Product Code</label><input type="text" v-model="bankDetails.productCode" :readonly="isReadOnly" /></div>
                    </div>
                    <div class="details-row">
                        <div class="field-group"><label>AQB</label><input type="text" v-model="bankDetails.aqb" :readonly="isReadOnly" /></div>
                        <div class="field-group"><label>Available Balance</label><input type="text" v-model="bankDetails.availBal" :readonly="isReadOnly" /></div>
                        <div class="field-group"><label>Relationship Value</label><input type="text" v-model="bankDetails.relValue" :readonly="isReadOnly" /></div>
                    </div>
                    <div class="details-row">
                        <div class="field-group"><label>Vintage (MoB)</label><input type="text" v-model="bankDetails.mobVintage" :readonly="isReadOnly" /></div>
                         <div class="field-group"><label>Addl field1</label><input type="text" v-model="bankDetails.addl1" :readonly="isReadOnly" /></div>
                        <div class="field-group"><label>Addl field2</label><input type="text" v-model="bankDetails.addl2" :readonly="isReadOnly" /></div>
                    </div>
                    <div class="details-row">
                       <div class="field-group"><label>Addl field4</label><input type="text" v-model="bankDetails.addl4" :readonly="isReadOnly" /></div>
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
                <select v-model="action.analysisLOV" :disabled="isReadOnly" class="compact-select">
                  <option value="">Select Reason</option>
                  <option v-for="item in analysisReasons" :key="item.reason" :value="item.reason">{{ item.reason }}</option>
                </select>
                <textarea v-model="action.analysisUpdate" :disabled="isReadOnly" placeholder="Update details" class="compact-textarea"></textarea>
              </div>
            </div>
            
            <div class="field-group">
              <label>Data Uploads</label>
              
              <div v-for="(uploadBlock, blockIndex) in action.dataUploads" :key="uploadBlock.id" class="data-upload-block">
                
                <button @click="removeDataUploadBlock(blockIndex)" v-if="action.dataUploads.length > 1" :disabled="isReadOnly" class="btn-remove-row" title="Remove Upload Section">×</button>

                <div class="upload-comment-row">
                  <div class="file-drop-zone"
                    :class="{ 'drag-over': uploadBlock.isDragOver, 'has-files': uploadBlock.files.length > 0 }"
                    @dragover.prevent="onDragOver(blockIndex)"
                    @dragleave.prevent="onDragLeave(blockIndex)"
                    @drop.prevent="onFileDrop($event, blockIndex)"
                    @click="triggerFileInput(blockIndex)"
                    :disabled="isReadOnly"
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
                      :disabled="isReadOnly"
                    />
                  </div>
                  
                  <textarea v-model="uploadBlock.comment" :disabled="isReadOnly" placeholder="Add comments for your uploads..." class="compact-textarea data-uploads-textarea"></textarea>
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
                            :disabled="isReadOnly"
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
                        :disabled="isReadOnly"
                      >✏️</button>
                      <button
                        v-if="file.isRenaming"
                        @click="saveFileName(blockIndex, fileIndex)"
                        class="btn-file-action btn-save"
                        title="Save name"
                        :disabled="isReadOnly"
                      >✅</button>
                      <button
                        v-if="file.isRenaming"
                        @click="cancelRename(blockIndex, fileIndex)"
                        class="btn-file-action btn-cancel"
                        title="Cancel rename"
                        :disabled="isReadOnly"
                      >❌</button>
                      <button
                        @click="removeFile(blockIndex, fileIndex)"
                        class="btn-file-action btn-remove"
                        title="Remove file"
                        :disabled="isReadOnly"
                      >🗑️</button>
                    </div>
                  </div>
                </div>
              </div>
              <button @click="addDataUploadBlock" :disabled="isReadOnly" class="btn-add-row">+ Add Upload Section</button>
            </div>
            </div>

          <div class="form-section">
            <div class="field-group">
              <label v-if="userRole !== 'others'">Assignments</label>
              <label v-else>Send Back to Risk Officer</label>
              <div v-if="userRole !== 'others'">
                <div class="review-comment-row">
                  <div class="comment-user-selection-row">
                    <select v-model="action.reviews[0].selectedDepartment" :disabled="isReadOnly" class="compact-select" @change="handleDepartmentChange(action.reviews[0])">
                      <option value="">Select Department</option>
                      <option v-for="dept in departments" :key="dept.id" :value="dept.name">
                        {{ dept.name }}
                      </option>
                    </select>
                    <select v-model="action.reviews[0].userId" :disabled="isReadOnly || !action.reviews[0].selectedDepartment" class="compact-select">
                      <option value="">Select User</option>
                      <option v-for="user in action.reviews[0].userList" :key="user.id" :value="user.name">
                        {{ user.name }}
                      </option>
                    </select>
                  </div>
                  <textarea v-model="action.reviews[0].text" :disabled="isReadOnly" placeholder="Add comments..." class="compact-textarea"></textarea>
                </div>
                <button v-if="!isReadOnly" @click="assignCase" class="btn-assign">Assign</button>
              </div>
              <div v-else>
                <textarea v-model="sendBackComment" :disabled="isReadOnly" placeholder="Add comments for send back..." class="compact-textarea"></textarea>
                <button v-if="!isReadOnly" @click="sendBackCase" class="btn-assign">Send Back</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="userRole !== 'others' && currentStep === 3" class="step-panel">
        <h3>Final Closure</h3>
        <div class="form-grid">
          <div class="form-section">
            <div class="field-group">
              <label>Closure Remarks</label>
              <div class="input-row">
                <select v-model="action.closureLOV" :disabled="isReadOnly" class="compact-select">
                  <option value="">Select Reason</option>
                  <option v-for="item in closureReasons" :key="item.reason" :value="item.reason">
                    {{ item.reason }}
                  </option>
                </select>
                <textarea v-model="action.closureRemarks" :disabled="isReadOnly" placeholder="Closure remarks" class="compact-textarea"></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="userRole !== 'others' && currentStep === 4" class="step-panel">
        <h3>Confirmation</h3>
        <div class="confirmation-grid">
          <div class="confirm-section">
            <div class="confirm-row">
              <label>Confirmed Mule</label>
              <div class="radio-group">
                <label><input type="radio" v-model="action.confirmedMule" value="Yes" name="confirmedMule" :disabled="isReadOnly" /> Yes</label>
                <label><input type="radio" v-model="action.confirmedMule" value="No" name="confirmedMule" :disabled="isReadOnly" /> No</label>
              </div>
            </div>
            <div class="confirm-row">
              <label>Funds Saved</label>
              <input
                type="number"
                v-model="action.fundsSaved"
                :disabled="action.confirmedMule !== 'Yes' || isReadOnly"
                class="compact-input"
                placeholder="Amount"
              />
            </div>
          </div>
          <div class="confirm-section">
            <div class="confirm-row">
              <label>Digital Channel Blocked</label>
              <div class="radio-group">
                <label><input type="radio" v-model="action.digitalBlocked" value="Yes" name="digitalBlocked" :disabled="isReadOnly" /> Yes</label>
                <label><input type="radio" v-model="action.digitalBlocked" value="No" name="digitalBlocked" :disabled="isReadOnly" /> No</label>
              </div>
            </div>
            <div class="confirm-row">
              <label>Account Blocked</label>
              <div class="radio-group">
                <label><input type="radio" v-model="action.accountBlocked" value="Yes" name="accountBlocked" :disabled="isReadOnly" /> Yes</label>
                <label><input type="radio" v-model="action.accountBlocked" value="No" name="accountBlocked" :disabled="isReadOnly" /> No</label>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="currentStep === 2">
        <div v-if="previouslyUploadedFiles.length > 0" class="uploaded-files-list improved-upload-list">
          <h4>Previously Uploaded Files</h4>
          <ul>
            <li v-for="file in previouslyUploadedFiles" :key="file.id" class="uploaded-file-item">
              <a :href="`/fraud_uploads/${file.file_location.split('/').pop()}`" target="_blank" class="file-link">
                <span class="download-icon">⬇️</span> {{ file.original_filename }}
              </a>
              <div class="file-meta-small">
                Uploaded: {{ new Date(file.uploaded_at).toLocaleString() }}
                <span v-if="file.comment">- {{ file.comment }}</span>
              </div>
            </li>
          </ul>
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
        <button
          @click="previousStep"
          :disabled="currentStep === 1 || isReadOnly"
          class="btn-nav btn-prev"
        >
          Previous
        </button>
        <button
          @click="nextStep"
          v-if="currentStep < steps.length"
          class="btn-nav btn-next"
        >
          Next
        </button>
      </div>
      <div class="action-buttons">
        <button v-if="!isReadOnly" @click="saveAction" class="btn-save">Save</button>
        <button v-if="!isReadOnly && userRole !== 'others'" @click="submitAction" class="btn-submit">Submit</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();

// --- State Management ---
const isLoading = ref(true);
const fetchError = ref(null);
const currentStep = ref(1);

// --- Dropdown Data ---
const analysisReasons = ref([]);
const departments = ref([]);
const closureReasons = ref([]);

const userRole = ref('');

// Fetch user role on mount (from /api/new-case-list)
const fetchUserRole = async () => {
  const token = localStorage.getItem('jwt');
  const response = await axios.get('/api/new-case-list', {
    headers: { 'Authorization': `Bearer ${token}` },
    params: { ack_no: caseAckNo.value }
  });
  if (response.data && response.data.logged_in_user_type) {
    userRole.value = response.data.logged_in_user_type;
  }
};

// Adjust steps based on userRole
const steps = ref([
  { title: 'Alert Details' },
  { title: 'Analysis' },
  { title: 'Closure' },
  { title: 'Confirmation' }
]);

watch(userRole, (role) => {
  if (role === 'others') {
    steps.value = [
      { title: 'Alert Details' },
      { title: 'Analysis' }
    ];
    if (currentStep.value > 2) currentStep.value = 2;
  } else {
    steps.value = [
      { title: 'Alert Details' },
      { title: 'Analysis' },
      { title: 'Closure' },
      { title: 'Confirmation' }
    ];
  }
});

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
  if(fileInputRefs.value[blockIndex] && !isReadOnly.value) {
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
  if (!isReadOnly.value) {
    addFiles(Array.from(event.target.files), blockIndex);
  }
  event.target.value = '';
};

const onDragOver = (blockIndex) => action.value.dataUploads[blockIndex].isDragOver = true;
const onDragLeave = (blockIndex) => action.value.dataUploads[blockIndex].isDragOver = false;
const onFileDrop = (event, blockIndex) => {
  action.value.dataUploads[blockIndex].isDragOver = false;
  if (!isReadOnly.value) {
    addFiles(Array.from(event.dataTransfer.files), blockIndex);
  }
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
  if (!isReadOnly.value) {
    action.value.dataUploads[blockIndex].files.splice(fileIndex, 1);
  }
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

const caseAckNo = ref('');

const fetchCaseDetails = async () => {
  const caseId = route.params.case_id;
  const token = localStorage.getItem('jwt');
  if (!token) throw new Error('No authentication token found');

  const response = await axios.get(`/api/combined-case-data/${caseId}`, { headers: { 'Authorization': `Bearer ${token}` } });
  
  if (response.data) {
    // Corrected data handling to prevent null errors
    const i4c_data = response.data.i4c_data || {};
    const customer_details = response.data.customer_details || {};
    const account_details = response.data.account_details || {};
    const { transactions = [], action_details, status, source_ack_no, source_bene_accno } = response.data;

    caseAckNo.value = source_ack_no || '';
    
    i4cDetails.value = {
        name: i4c_data.customer_name || 'N/A',
        mobileNumber: i4c_data.mobile || 'N/A',
        email: i4c_data.email || 'N/A',
        ifscCode: i4c_data.ifsc || 'N/A',
        beneficiaryAccount: i4c_data.to_account || 'N/A',
        bankName: i4c_data.to_bank || 'N/A'
    };
    
    bankDetails.value = {
        name: `${customer_details.fname || ''} ${customer_details.mname || ''} ${customer_details.lname || ''}`.trim() || 'N/A',
        mobileNumber: customer_details.mobile || 'N/A',
        email: customer_details.email || 'N/A',
        ifscCode: customer_details.ifsc || 'N/A',
        beneficiaryAccount: source_bene_accno || 'N/A',
        bankName: i4c_data.to_bank || 'N/A',
        customerId: customer_details.cust_id || 'N/A',
        acStatus: account_details.acc_status || 'N/A',
        aqb: account_details.aqb || 'N/A',
        availBal: account_details.availBal || 'N/A',
        productCode: account_details.productCode || 'N/A',
        relValue: customer_details.rel_value || 'N/A',
        mobVintage: customer_details.mob || 'N/A',
        addl1: account_details.addl1 || 'N/A',
        addl2: account_details.addl2 || 'N/A',
        addl4: account_details.addl4 || 'N/A'
    };
    
    transactionDetails.value = transactions;

    if (action_details) {
      Object.assign(action.value, action_details);
      if (!Array.isArray(action.value.dataUploads) || action.value.dataUploads.length === 0) {
        action.value.dataUploads = [{ id: Date.now(), comment: '', files: [], isDragOver: false }];
      }
    }
    
    if (typeof status === 'string' && status.trim().toLowerCase() === 'closed') {
      isReadOnly.value = true;
    } else {
      isReadOnly.value = false;
    }
  } else { 
    throw new Error('Received no data for this case.'); 
  }
};

const previouslyUploadedFiles = ref([]);
const isReadOnly = ref(false);
const caseLogs = ref([]);

const sendBackComment = ref('');
const hasUnsavedChanges = ref(false);

watch(action, () => { hasUnsavedChanges.value = true; }, { deep: true });

const sendBackCase = async () => {
  if (hasUnsavedChanges.value) {
    alert('Please click on Save before Send Back.');
    return;
  }
  if (!sendBackComment.value.trim()) {
    alert('Please enter a comment before sending back.');
    return;
  }
  const ackNo = caseAckNo.value;
  const token = localStorage.getItem('jwt');
  try {
    await axios.post(`/api/case/${ackNo}/send-back`, { comment: sendBackComment.value }, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    alert('Case sent back successfully!');
    sendBackComment.value = '';
    const caseId = route.params.case_id;
    const logsResp = await axios.get(`/api/case/${caseId}/logs`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    caseLogs.value = logsResp.data.logs || [];
    await fetchUserRole();
    window.location.href = `/case-details`;
  } catch (err) {
    alert('Failed to send back case.');
    console.error('Send back error:', err);
  }
};

const goToStep = (step) => {
  if (isLoading.value) return;
  if (userRole.value === 'others' && step > 2) return;
  currentStep.value = step;
};
const nextStep = () => {
  if (userRole.value === 'others') {
    if (currentStep.value < 2) currentStep.value++;
  } else {
    if (currentStep.value < steps.value.length) currentStep.value++;
  }
};
const previousStep = () => {
  if (currentStep.value > 1) currentStep.value--;
};

onMounted(async () => {
  isLoading.value = true;
  fetchError.value = null;
  try {
    const caseId = route.params.case_id;
    const token = localStorage.getItem('jwt');
    const resp = await axios.get('/api/case-action/latest', {
      params: { case_id: caseId },
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (resp.data && resp.data.action_data && resp.data.action_data.action_data) {
      Object.assign(action.value, resp.data.action_data.action_data);
    }
    if (resp.data && resp.data.files) {
      previouslyUploadedFiles.value = resp.data.files;
    }
    const logsResp = await axios.get(`/api/case/${caseId}/logs`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    caseLogs.value = logsResp.data.logs || [];
    await fetchCaseDetails();
    await fetchUserRole();
    await Promise.all([
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
  const caseId = route.params.case_id;
  const caseType = 'NAB';
  const formData = new FormData();
  formData.append('case_id', caseId);
  formData.append('case_type', caseType);
  formData.append('action_data', JSON.stringify(action.value));

  action.value.dataUploads.forEach((block) => {
    if (block.files && block.files.length > 0) {
      block.files.forEach((fileObj) => {
        if (fileObj.file && (fileObj.file instanceof File || fileObj.file instanceof Blob)) {
          formData.append('files', fileObj.file, fileObj.displayName || fileObj.file.name);
        }
      });
    }
  });

  try {
    const token = localStorage.getItem('jwt');
    await axios.post('/api/case-action/save', formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data',
      },
    });
    alert('Case action saved successfully!');
    hasUnsavedChanges.value = false;
  } catch (err) {
    alert('Failed to save case action.');
    console.error('Failed to save case action:', err);
  }
};

const submitAction = async () => {
  if (hasUnsavedChanges.value) {
    alert('Please click on Save before Submit.');
    return;
  }
  const caseId = route.params.case_id;
  try {
    const token = localStorage.getItem('jwt');
    await axios.post('/api/case/submit',
      { case_id: caseId },
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    window.location.href = `/case-details`;
  } catch (err) {
    console.error('Failed to submit case:', err);
  }
};

const assignCase = async () => {
  if (hasUnsavedChanges.value) {
    alert('Please click on Save before Assign.');
    return;
  }
  const assignedTo = action.value.reviews[0].userId;
  const token = localStorage.getItem('jwt');
  const ackNo = caseAckNo.value;
  if (!assignedTo) {
    alert('Please select a user to assign.');
    return;
  }
  if (!ackNo) {
    alert('No valid case ACK No found.');
    return;
  }
  try {
    await axios.post(`/api/case/${ackNo}/assign`,
      { assigned_to_employee: assignedTo },
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    alert('Case assigned to ' + assignedTo);
    window.location.href = `/case-details`;
  } catch (err) {
    alert('Failed to assign case.');
    console.error('Assignment error:', err);
  }
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
    grid-column: 1 / -1; /* Span across both columns if in a grid */
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
  background-color: #fff3cd;
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

/* Upload Comment Row with File Drop Zone */
.upload-comment-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 12px;
}

.upload-comment-row .data-uploads-textarea {
  flex: 1;
  margin-bottom: 0;
  min-height: 120px;
  max-height: 200px;
  width: 50%;
}

.upload-comment-row .file-drop-zone {
  flex: 1;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
  border: 1px dashed #ced4da;
  border-radius: 6px;
  background: #f8f9fa;
  cursor: pointer;
  transition: all 0.2s;
  width: 50%;
}

.upload-comment-row .file-drop-zone:hover {
  border-color: #0d6efd;
  background: #e9ecef;
}

.upload-comment-row .file-drop-zone.drag-over {
  border-color: #0d6efd;
  background: #e9ecef;
}

.upload-comment-row .upload-icon {
  font-size: 24px;
  color: #0d6efd;
  margin-bottom: 8px;
}

.upload-comment-row .upload-text {
  font-size: 11px;
  color: #6c757d;
  line-height: 1.3;
  text-align: center;
}

.upload-comment-row .upload-text strong {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  color: #495057;
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
  border: 1px dashed #ced4da;
  border-radius: 4px;
  padding: 8px;
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
  font-size: 24px;
  color: #0d6efd;
  margin-bottom: 4px;
}
.upload-text {
  font-size: 11px;
  color: #6c757d;
  line-height: 1.3;
}
.hidden-file-input { display: none; }
.uploaded-files-list {
  margin-top: 8px;
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  max-height: 100px;
  overflow-y: auto;
  text-align: left;
}
.files-header {
  font-size: 12px;
  font-weight: 500;
  color: #495057;
  padding: 4px 8px;
  border-bottom: 1px solid #dee2e6;
}
.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  border-bottom: 1px solid #e9ecef;
}
.file-item:last-child { border-bottom: none; }
.file-info { display: flex; align-items: center; gap: 10px; }
.file-icon { font-size: 16px; }
.file-details { display: flex; flex-direction: column; }
.file-name-container { display: flex; align-items: center; gap: 5px; }
.file-name-input { padding: 3px 5px; border: 1px solid #ced4da; border-radius: 3px; font-size: 12px; }
.file-meta { font-size: 10px; color: #6c757d; }
.file-actions { display: flex; gap: 5px; }
.btn-file-action { background: none; border: none; cursor: pointer; padding: 3px; font-size: 14px;}

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
  
  .upload-comment-row {
    flex-direction: column;
    gap: 8px;
  }
  
  .upload-comment-row .file-drop-zone {
    min-width: auto;
    width: 100%;
    min-height: 80px;
  }
}

/* Custom Scrollbar */
.step-content::-webkit-scrollbar { width: 6px; }
.step-content::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 3px; }
.step-content::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 3px; }
.step-content::-webkit-scrollbar-thumb:hover { background: #a8a8a8; }
.readonly-banner {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 6px;
  padding: 14px 20px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.5px;
}
.improved-upload-list {
  background: #f7fafd;
  border: 1px solid #e3e8ee;
  border-radius: 8px;
  padding: 18px 24px 10px 24px;
  margin-bottom: 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.improved-upload-list h4 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #1a3a5d;
}
.uploaded-file-item {
  margin-bottom: 10px;
  padding: 10px 0 8px 0;
  border-bottom: 1px solid #e3e8ee;
  display: flex;
  flex-direction: column;
}
.uploaded-file-item:last-child {
  border-bottom: none;
}
.file-link {
  font-size: 15px;
  font-weight: 500;
  color: #0d6efd;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
}
.file-link:hover {
  text-decoration: underline;
}
.download-icon {
  font-size: 18px;
  color: #0d6efd;
}
.file-meta-small {
  font-size: 12px;
  color: #6c757d;
  margin-left: 26px;
  margin-top: 2px;
}
.btn-assign {
  width: 100%;
  padding: 8px;
  background-color: #e7f3ff;
  color: #0d6efd;
  border: 1px solid #0d6efd;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  margin-top: 8px;
}
.btn-assign:hover {
  background-color: #d1e7ff;
}
.case-logs-section {
  background: #f8f9fa;
  border: 1px solid #e3e8ee;
  border-radius: 8px;
  padding: 18px 24px 10px 24px;
  margin-top: 24px;
  margin-bottom: 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.case-logs-section h4 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #1a3a5d;
}
.case-log-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.case-log-item {
  margin-bottom: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #e3e8ee;
  font-size: 14px;
  display: flex;
  gap: 12px;
  align-items: center;
}
.case-log-item:last-child {
  border-bottom: none;
}
.log-time {
  color: #6c757d;
  font-size: 12px;
  min-width: 120px;
}
.log-user {
  color: #0d6efd;
  font-weight: 500;
}
.log-action {
  color: #28a745;
  font-weight: 500;
}
.log-details {
  color: #495057;
  font-size: 13px;
}
</style>