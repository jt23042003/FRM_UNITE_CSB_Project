<template>
  <div class="pma-container">
    <!-- Progress Steps -->
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

    <!-- Step Content -->
    <div class="step-content">
      <!-- Step 1: Alert & Customer Details -->
      <div v-if="currentStep === 1" class="step-panel">
        <h3>Alert - Potential Suspect Account</h3>
        <div class="comparison-grid">
          <!-- I4C Details -->
          <div class="details-section">
            <h4>Customer Details - I4C</h4>
            <div class="details-row">
              <div class="field-group">
                <label>Name</label>
                <input type="text" v-model="i4cDetails.name" readonly />
              </div>
              <div class="field-group">
                <label>Mobile</label>
                <input type="text" v-model="i4cDetails.mobile" readonly />
              </div>
              <div class="field-group">
                <label>Email</label>
                <input type="text" v-model="i4cDetails.email" readonly />
              </div>
            </div>
            <div class="details-row">
              <div class="field-group">
                <label>PAN</label>
                <input type="text" v-model="i4cDetails.pan" readonly />
              </div>
              <div class="field-group">
                <label>Aadhaar</label>
                <input type="text" v-model="i4cDetails.aadhaar" readonly />
              </div>
              <div class="field-group">
                <label>GST</label>
                <input type="text" v-model="i4cDetails.gst" readonly />
              </div>
            </div>
          </div>

          <!-- Bank Details -->
          <div class="details-section">
            <h4>Customer Details - Bank</h4>
            <div class="details-row">
              <div class="field-group highlight">
                <label>Name</label>
                <input type="text" v-model="bankDetails.name" readonly />
              </div>
              <div class="field-group highlight">
                <label>Mobile</label>
                <input type="text" v-model="bankDetails.mobile" readonly />
              </div>
              <div class="field-group highlight">
                <label>Email</label>
                <input type="text" v-model="bankDetails.email" readonly />
              </div>
            </div>
            <div class="details-row">
              <div class="field-group">
                <label>Customer ID</label>
                <input type="text" v-model="bankDetails.customerId" readonly />
              </div>
              <div class="field-group">
                <label>AQB</label>
                <input type="text" v-model="bankDetails.aqb" readonly />
              </div>
              <div class="field-group">
                <label>Balance</label>
                <input type="text" v-model="bankDetails.availBal" readonly />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 2: Analysis & Investigation -->
      <div v-if="currentStep === 2" class="step-panel">
        <h3>Analysis & Investigation</h3>
        <div class="form-grid">
          <div class="form-section">
            <div class="field-group">
              <label>Analysis Update</label>
              <div class="input-row">
                <select v-model="action.analysisLOV" class="compact-select">
                  <option value="">Select LOV</option>
                  <option value="under-review">Under Review</option>
                  <option value="suspicious">Suspicious Activity</option>
                  <option value="cleared">Cleared</option>
                </select>
                <textarea v-model="action.analysisUpdate" placeholder="Update details" class="compact-textarea"></textarea>
              </div>
            </div>
            <div class="field-group">
              <label>Initial Review Feedback</label>
              <textarea v-model="action.initialReview" placeholder="Review feedback" class="compact-textarea"></textarea>
            </div>

            <!-- File Upload Section -->
            <div class="field-group">
              <label>Supporting Documents</label>
              <div class="file-upload-container">
                <div 
                  class="file-drop-zone"
                  :class="{ 'drag-over': isDragOver, 'has-files': uploadedFiles.length > 0 }"
                  @dragover.prevent="onDragOver"
                  @dragleave.prevent="onDragLeave"
                  @drop.prevent="onFileDrop"
                  @click="triggerFileInput"
                >
                  <div class="upload-icon">📁</div>
                  <div class="upload-text">
                    <strong>Drop files here or click to browse</strong>
                    <p>Supports: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG (Max 10MB each)</p>
                  </div>
                  <input 
                    ref="fileInput"
                    type="file" 
                    multiple
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
                    @change="onFileSelect"
                    class="hidden-file-input"
                  />
                </div>

                <!-- Uploaded Files List -->
                <div v-if="uploadedFiles.length > 0" class="uploaded-files-list">
                  <div class="files-header">
                    <span>Uploaded Files ({{ uploadedFiles.length }})</span>
                  </div>
                  <div 
                    v-for="(file, index) in uploadedFiles" 
                    :key="index"
                    class="file-item"
                  >
                    <div class="file-info">
                      <div class="file-icon">{{ getFileIcon(file.type) }}</div>
                      <div class="file-details">
                        <div class="file-name-container">
                          <input 
                            v-if="file.isRenaming"
                            v-model="file.newName"
                            @blur="saveFileName(index)"
                            @keyup.enter="saveFileName(index)"
                            @keyup.escape="cancelRename(index)"
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
                        @click="startRename(index)"
                        class="btn-file-action btn-rename"
                        title="Rename file"
                      >
                        ✏️
                      </button>
                      <button 
                        v-if="file.isRenaming"
                        @click="saveFileName(index)"
                        class="btn-file-action btn-save"
                        title="Save name"
                      >
                        ✅
                      </button>
                      <button 
                        v-if="file.isRenaming"
                        @click="cancelRename(index)"
                        class="btn-file-action btn-cancel"
                        title="Cancel rename"
                      >
                        ❌
                      </button>
                      <button 
                        @click="removeFile(index)"
                        class="btn-file-action btn-remove"
                        title="Remove file"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="form-section">
            <div class="field-group">
              <label>Reassignment</label>
              <div class="reassign-row">
                <input type="text" v-model="action.reassignments[0].userId" placeholder="User ID" class="compact-input" />
                <select v-model="action.reassignments[0].dept" class="compact-select">
                  <option value="LOV">LOV</option>
                </select>
              </div>
            </div>
            <div class="field-group">
              <label>Review Comments</label>
              <div class="review-compact">
                <input type="text" v-model="action.reviews[0].userId" placeholder="User/Dept" class="compact-input" />
                <textarea v-model="action.reviews[0].text" placeholder="Comments" class="compact-textarea"></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 3: Final Closure -->
      <div v-if="currentStep === 3" class="step-panel">
        <h3>Final Closure</h3>
        <div class="form-grid">
          <div class="form-section">
            <div class="field-group">
              <label>Closure Remarks</label>
              <div class="input-row">
                <select v-model="action.closureLOV" class="compact-select">
                  <option value="">Select LOV</option>
                  <option value="genuine">Genuine Transaction</option>
                  <option value="mule-confirmed">Mule Account Confirmed</option>
                  <option value="needs-investigation">Needs Further Investigation</option>
                </select>
                <textarea v-model="action.closureRemarks" placeholder="Closure remarks" class="compact-textarea"></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 4: Confirmation -->
      <div v-if="currentStep === 4" class="step-panel">
        <h3>Confirmation</h3>
        <div class="confirmation-grid">
          <div class="confirm-section">
            <div class="confirm-row">
              <label>Final Closure</label>
              <select v-model="action.confirmClosure" class="compact-select">
                <option value="No">No</option>
                <option value="Yes">Yes</option>
              </select>
            </div>
            <div class="confirm-row">
              <label>Confirmed Mule</label>
              <select v-model="action.confirmedMule" class="compact-select">
                <option value="No">No</option>
                <option value="Yes">Yes</option>
              </select>
            </div>
            <div class="confirm-row">
              <label>Funds Saved</label>
              <input 
                type="number" 
                v-model="action.fundsSaved" 
                :disabled="isReadOnly"
                class="compact-input"
                placeholder="Amount (INR)"
                min="0"
                step="0.01"
              />
            </div>
          </div>
          <div class="confirm-section">
            <div class="confirm-row">
              <label>Digital Channel Blocked</label>
              <select v-model="action.digitalBlocked" class="compact-select">
                <option value="No">No</option>
                <option value="Yes">Yes</option>
              </select>
            </div>
            <div class="confirm-row">
              <label>Account Blocked</label>
              <select v-model="action.accountBlocked" class="compact-select">
                <option value="No">No</option>
                <option value="Yes">Yes</option>
              </select>
            </div>
            <div class="confirm-row">
              <label>Closure Date & Time</label>
              <div class="datetime-row">
                <input 
                  type="date" 
                  v-model="action.closureDate" 
                  :disabled="action.confirmClosure !== 'Yes'" 
                  class="compact-input"
                />
                <input 
                  type="time" 
                  v-model="action.closureTime" 
                  :disabled="action.confirmClosure !== 'Yes'" 
                  class="compact-input"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation & Action Buttons -->
    <div class="bottom-navigation">
      <div class="nav-buttons">
        <button 
          @click="previousStep" 
          :disabled="currentStep === 1"
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
        <button @click="saveAction" class="btn-save">Save</button>
        <button @click="submitAction" class="btn-submit">Submit</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api.js';

const route = useRoute();

// Multi-step form state
const currentStep = ref(1);
const steps = ref([
  { title: 'Alert Details', icon: 'alert' },
  { title: 'Analysis', icon: 'analysis' },
  { title: 'Closure', icon: 'closure' },
  { title: 'Confirmation', icon: 'confirm' }
]);

// Navigation methods
const goToStep = (step) => {
  currentStep.value = step;
};

const nextStep = () => {
  if (currentStep.value < steps.value.length) {
    currentStep.value++;
  }
};

const previousStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--;
  }
};

// Data structure for I4C details
const i4cDetails = ref({
  name: 'John Doe',
  mobile: '+91-9876543210',
  email: 'john.doe@email.com',
  pan: 'ABCDE1234F',
  aadhaar: '1234-5678-9012',
  gst: 'GST123456789'
});

// Data structure for Bank details
const bankDetails = ref({
  name: 'John Smith',
  mobile: '+91-9876543211',
  email: 'john.smith@email.com',
  pan: 'ABCDE1234G',
  aadhaar: '1234-5678-9013',
  gst: 'GST123456790',
  customerId: 'CUST001234',
  aqb: '50000',
  availBal: '₹1,25,000',
  productCode: 'SAV001',
  relValue: 'High',
  mob: '24 months',
  accountStatus: 'Active'
});

// Action section data
const action = ref({
  analysisLOV: '',
  analysisUpdate: '',
  initialReview: '',
  reassignments: [
    { userId: '', dept: 'LOV', timestamp: '' }
  ],
  reviews: [
    { userId: '', lov: '', text: '', timestamp: '' }
  ],
  closureLOV: '',
  closureRemarks: '',
  confirmClosure: 'No',
  confirmedMule: 'No',
  fundsSaved: null,
  digitalBlocked: 'No',
  accountBlocked: 'No',
  closureDate: '',
  closureTime: ''
});

// File upload state
const fileInput = ref(null);
const isDragOver = ref(false);
const uploadedFiles = ref([]);

const getFileIcon = (type) => {
  if (type.startsWith('image/')) return '📸';
  if (type.startsWith('application/pdf')) return '📄';
  if (type.startsWith('application/msword') || type.startsWith('application/vnd.openxmlformats-officedocument.wordprocessingml.document')) return '📝';
  if (type.startsWith('application/vnd.ms-excel') || type.startsWith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) return '📊';
  return '��'; // Default icon
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const triggerFileInput = () => {
  fileInput.value.click();
};

const onFileSelect = (event) => {
  const files = Array.from(event.target.files);
  files.forEach(file => {
    const reader = new FileReader();
    reader.onload = (e) => {
      uploadedFiles.value.push({
        file: file,
        displayName: file.name,
        size: file.size,
        type: file.type,
        isRenaming: false,
        newName: file.name
      });
    };
    reader.readAsDataURL(file);
  });
  event.target.value = ''; // Clear the input for the same file
};

const onDragOver = () => {
  isDragOver.value = true;
};

const onDragLeave = () => {
  isDragOver.value = false;
};

const onFileDrop = (event) => {
  isDragOver.value = false;
  const files = Array.from(event.dataTransfer.files);
  files.forEach(file => {
    const reader = new FileReader();
    reader.onload = (e) => {
      uploadedFiles.value.push({
        file: file,
        displayName: file.name,
        size: file.size,
        type: file.type,
        isRenaming: false,
        newName: file.name
      });
    };
    reader.readAsDataURL(file);
  });
};

const startRename = (index) => {
  uploadedFiles.value[index].isRenaming = true;
};

const saveFileName = (index) => {
  uploadedFiles.value[index].isRenaming = false;
  // In a real app, you would send this new name to your backend
  // For now, we'll just update the display name
  uploadedFiles.value[index].displayName = uploadedFiles.value[index].newName;
};

const cancelRename = (index) => {
  uploadedFiles.value[index].isRenaming = false;
  uploadedFiles.value[index].newName = uploadedFiles.value[index].displayName;
};

const removeFile = (index) => {
  uploadedFiles.value.splice(index, 1);
};

// Fetch case details on component mount
onMounted(async () => {
  try {
    const caseId = route.params.case_id;
    const token = localStorage.getItem('jwt');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Uncomment when API is ready
    // const response = await axios.get(`${API_ENDPOINTS.CASE_DETAILS}/${caseId}`, {
    //   headers: { 'Authorization': `Bearer ${token}` }
    // });

    // if (response.data) {
    //   const data = response.data;
    //   Object.assign(i4cDetails.value, data.i4c_details || {});
    //   Object.assign(bankDetails.value, data.bank_details || {});
    //   if (data.action_details) {
    //     Object.assign(action.value, data.action_details);
    //   }
    // }
  } catch (error) {
    console.error('Error fetching case details:', error);
  }
});

// Save action details
const saveAction = async () => {
  try {
    const token = localStorage.getItem('jwt');
    const caseId = route.params.case_id;
    
    console.log('Saving action:', action.value);
    // Uncomment when API is ready
    // await axios.post(`${API_ENDPOINTS.SAVE_ACTION}/${caseId}`, {
    //   action_details: action.value
    // }, {
    //   headers: { 'Authorization': `Bearer ${token}` }
    // });
  } catch (error) {
    console.error('Error saving action:', error);
  }
};

// Submit final action
const submitAction = async () => {
  try {
    const token = localStorage.getItem('jwt');
    const caseId = route.params.case_id;
    
    console.log('Submitting action:', action.value);
    // Uncomment when API is ready
    // await axios.post(`${API_ENDPOINTS.SUBMIT_ACTION}/${caseId}`, {
    //   action_details: action.value
    // }, {
    //   headers: { 'Authorization': `Bearer ${token}` }
    // });
  } catch (error) {
    console.error('Error submitting action:', error);
  }
};
</script>

<style scoped>
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

/* Progress Steps */
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

.step.active .step-number,
.step.completed .step-number {
  background: rgba(255,255,255,0.3);
}

.step-title {
  font-size: 14px;
  font-weight: 500;
}

/* Step Content */
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

/* Comparison Grid - Step 1 */
.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
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

.field-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-group label {
  font-size: 12px;
  font-weight: 500;
  color: #6c757d;
  margin-bottom: 2px;
}

.field-group input {
  padding: 6px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  background: #fff;
  height: 32px;
  box-sizing: border-box;
}

.field-group.highlight input {
  background: #fff3cd;
  border-color: #ffc107;
  font-weight: 500;
}

/* Form Grid - Steps 2 & 3 */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-group label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  margin-bottom: 6px;
}

.input-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 12px;
  align-items: start;
}

.reassign-row {
  display: grid;
  grid-template-columns: 1fr 120px;
  gap: 12px;
}

.review-compact {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 12px;
  align-items: start;
}

/* Compact Form Elements */
.compact-select {
  padding: 6px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  background: #fff;
  height: 32px;
  box-sizing: border-box;
}

.compact-input {
  padding: 6px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  background: #fff;
  height: 32px;
  box-sizing: border-box;
}

.compact-textarea {
  padding: 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  background: #fff;
  min-height: 60px;
  max-height: 80px;
  resize: vertical;
  font-family: inherit;
  box-sizing: border-box;
}

/* Confirmation Grid - Step 4 */
.confirmation-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

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

.datetime-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
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
  margin-top: 10px;
}

.file-drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  border: 2px dashed #ced4da;
  border-radius: 6px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #f8f9fa;
  margin-top: 10px;
}

.file-drop-zone.drag-over {
  border-color: #0d6efd;
  background: #e9ecef;
}

.file-drop-zone.has-files {
  border-style: solid;
  border-color: #0d6efd;
}

.upload-icon {
  font-size: 48px;
  color: #0d6efd;
  margin-bottom: 10px;
}

  .upload-text {
    font-size: 14px;
    color: #6c757d;
    margin-bottom: 10px;
  }

  .hidden-file-input {
    display: none;
  }

.uploaded-files-list {
  margin-top: 15px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 10px;
  max-height: 150px; /* Adjust as needed */
  overflow-y: auto;
}

.files-header {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  padding-bottom: 8px;
  border-bottom: 1px solid #dee2e6;
  margin-bottom: 8px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #e9ecef;
  cursor: grab; /* Indicate draggable */
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  font-size: 24px;
  color: #0d6efd;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.file-name-container {
  display: flex;
  align-items: center;
  gap: 5px;
}

.file-name-input {
  flex: 1;
  padding: 4px 6px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  background: #fff;
  height: 24px;
  box-sizing: border-box;
}

.file-name-input:focus {
  outline: none;
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.file-meta {
  font-size: 12px;
  color: #6c757d;
}

.file-actions {
  display: flex;
  gap: 5px;
}

.btn-file-action {
  padding: 4px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background: #fff;
  color: #495057;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-file-action:hover:not(:disabled) {
  background: #e9ecef;
  border-color: #adb5bd;
}

.btn-file-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-rename {
  color: #0d6efd;
  border-color: #0d6efd;
}

.btn-rename:hover {
  background: #e9ecef;
  border-color: #adb5bd;
}

.btn-save {
  color: #28a745;
  border-color: #28a745;
}

.btn-save:hover {
  background: #e9ecef;
  border-color: #adb5bd;
}

.btn-cancel {
  color: #dc3545;
  border-color: #dc3545;
}

.btn-cancel:hover {
  background: #e9ecef;
  border-color: #adb5bd;
}

.btn-remove {
  color: #dc3545;
  border-color: #dc3545;
}

.btn-remove:hover {
  background: #e9ecef;
  border-color: #adb5bd;
}

/* Bottom Navigation */
.bottom-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-buttons {
  display: flex;
  gap: 12px;
}

.btn-nav {
  padding: 8px 16px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background: #fff;
  color: #495057;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-nav:hover:not(:disabled) {
  background: #e9ecef;
  border-color: #adb5bd;
}

.btn-nav:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-next {
  background: #0d6efd;
  color: #fff;
  border-color: #0d6efd;
}

.btn-next:hover {
  background: #0b5ed7;
  border-color: #0b5ed7;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.btn-save,
.btn-submit {
  padding: 8px 20px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-save {
  background: #6c757d;
  color: #fff;
}

.btn-save:hover {
  background: #5c636a;
}

.btn-submit {
  background: #28a745;
  color: #fff;
}

.btn-submit:hover {
  background: #218838;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .comparison-grid,
  .form-grid,
  .confirmation-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .details-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .input-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .review-compact {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}

@media (max-width: 768px) {
  .pma-container {
    padding: 12px;
  }
  
  .steps-container {
    flex-direction: column;
    gap: 8px;
  }
  
  .step {
    justify-content: flex-start;
  }
  
  .details-row {
    grid-template-columns: 1fr;
  }
  
  .confirm-row {
    grid-template-columns: 1fr;
    gap: 4px;
  }
  
  .bottom-navigation {
    flex-direction: column;
    gap: 12px;
  }
  
  .nav-buttons,
  .action-buttons {
    width: 100%;
    justify-content: center;
  }
}

/* Custom Scrollbar */
.step-content::-webkit-scrollbar {
  width: 6px;
}

.step-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.step-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.step-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>