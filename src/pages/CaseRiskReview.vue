<template>
  <div class="case-entry-bg">
    <h1 class="screen-header">Complaint Details</h1>
    <div v-if="loading" class="case-details-loading">Loading...</div>
    <div v-else-if="error" class="case-details-error">{{ error }}</div>
    <div v-else>
      <!-- 1. Customer Details -->
      <section class="card-section">
        <h2>Customer Details</h2>
        <div class="display-grid">
          <div><strong>Acknowledgement No.:</strong> {{ caseData.ackNo }}</div>
          <div><strong>Sub Category of Complaint:</strong> {{ caseData.subCategory }}</div>
          <div><strong>Transaction Date:</strong> {{ caseData.transactionDate }}</div>
          <div><strong>Complaint Date:</strong> {{ caseData.complaintDate }}</div>
          <div><strong>Date & Time of Reporting / Escalation:</strong> {{ caseData.reportDateTime }}</div>
          <div><strong>State:</strong> {{ caseData.state }}</div>
          <div><strong>District:</strong> {{ caseData.district }}</div>
          <div><strong>Policestation:</strong> {{ caseData.policestation }}</div>
          <div><strong>Mode of Payment:</strong> {{ caseData.paymentMode }}</div>
          <div><strong>Account Number (Victim):</strong> {{ caseData.accountNumber }}</div>
          <div><strong>Card Number:</strong> {{ caseData.cardNumber }}</div>
          <div><strong>Transaction Id / UTR Number:</strong> {{ caseData.transactionId }}</div>
          <div><strong>Layers:</strong> {{ caseData.layers }}</div>
          <div><strong>Transaction Amount:</strong> {{ caseData.transactionAmount }}</div>
          <div><strong>Disputed Amount:</strong> {{ caseData.disputedAmount }}</div>
          <div><strong>Action:</strong> {{ caseData.action }}</div>
          <div><strong>Money transfer TO Bank:</strong> {{ caseData.toBank }}</div>
          <div><strong>Money transfer TO Account:</strong> {{ caseData.toAccount }}</div>
          <div><strong>IFSC Code (Non Mandatory):</strong> {{ caseData.ifsc }}</div>
          <div><strong>Money transfer TO Transaction Id / UTR Number:</strong> {{ caseData.toTransactionId }}</div>
          <div><strong>Money transfer TO Amount:</strong> {{ caseData.toAmount }}</div>
          <div><strong>Action Taken Date:</strong> {{ caseData.actionTakenDate }}</div>
          <div><strong>Lien Amount (Non Mandatory):</strong> {{ caseData.lienAmount }}</div>
          <div>
            <strong>Evidence Provided (Non Mandatory):</strong>
            <span v-if="caseData.evidenceName">{{ caseData.evidenceName }}</span>
            <span v-else>No evidence uploaded.</span>
          </div>
          <div class="span-2"><strong>Additional Information:</strong> {{ caseData.additionalInfo }}</div>
        </div>
      </section>

      <section class="card-section">
  <h2>Risk Entity Profiles</h2>
  <div v-if="riskEntityLoading" class="case-details-loading">Loading...</div>
  <div v-else-if="riskEntityError" class="case-details-error">{{ riskEntityError }}</div>
  <div v-else>
    <div class="tab-selector">
      <button
        :class="['tab-btn', selectedProfileTab === 'victim' ? 'active' : '']"
        @click="selectedProfileTab = 'victim'"
      >Victim Profile</button>
      <button
        :class="['tab-btn', selectedProfileTab === 'beneficiary' ? 'active' : '']"
        @click="selectedProfileTab = 'beneficiary'"
      >Beneficiary Profile</button>
    </div>
    <div v-if="selectedProfileTab === 'victim'" class="display-grid">
      <div><strong>Customer ID:</strong> {{ riskEntity.victim.cust_id || '-' }}</div>
      <div><strong>Full Name:</strong> {{ riskEntity.victim.full_name || '-' }}</div>
      <div><strong>Date of Birth:</strong> {{ riskEntity.victim.dob || '-' }}</div>
      <div><strong>National ID:</strong> {{ riskEntity.victim.nat_id || '-' }}</div>
      <div><strong>PAN:</strong> {{ riskEntity.victim.pan || '-' }}</div>
      <div><strong>Citizenship:</strong> {{ riskEntity.victim.citizen || '-' }}</div>
      <div><strong>Occupation:</strong> {{ riskEntity.victim.occupation || '-' }}</div>
      <div><strong>Segment:</strong> {{ riskEntity.victim.seg || '-' }}</div>
      <div><strong>Customer Type:</strong> {{ riskEntity.victim.cust_type || '-' }}</div>
      <div><strong>KYC Status:</strong> {{ riskEntity.victim.kyc_status || '-' }}</div>
      <div><strong>Risk Profile:</strong> {{ riskEntity.victim.risk_prof || '-' }}</div>
      <div><strong>Account Number:</strong> {{ riskEntity.victim.account_number || '-' }}</div>
      <div><strong>Account Type:</strong> {{ riskEntity.victim.acc_type || '-' }}</div>
      <div><strong>Account Status:</strong> {{ riskEntity.victim.acc_status || '-' }}</div>
      <div><strong>Account Opening Date:</strong> {{ riskEntity.victim.open_date || '-' }}</div>
      <div><strong>Current Balance:</strong> {{ riskEntity.victim.balance !== undefined ? riskEntity.victim.balance : '-' }}</div>
      <div><strong>Date of Last Transaction:</strong> {{ riskEntity.victim.last_txn_date || '-' }}</div>
      <div><strong>Credit Score:</strong> {{ riskEntity.victim.credit_score !== undefined ? riskEntity.victim.credit_score : '-' }}</div>
    </div>
    <div v-else class="display-grid">
      <div><strong>Customer ID:</strong> {{ riskEntity.beneficiary.cust_id || '-' }}</div>
      <div><strong>Full Name:</strong> {{ riskEntity.beneficiary.full_name || '-' }}</div>
      <div><strong>Date of Birth:</strong> {{ riskEntity.beneficiary.dob || '-' }}</div>
      <div><strong>National ID:</strong> {{ riskEntity.beneficiary.nat_id || '-' }}</div>
      <div><strong>PAN:</strong> {{ riskEntity.beneficiary.pan || '-' }}</div>
      <div><strong>Citizenship:</strong> {{ riskEntity.beneficiary.citizen || '-' }}</div>
      <div><strong>Occupation:</strong> {{ riskEntity.beneficiary.occupation || '-' }}</div>
      <div><strong>Segment:</strong> {{ riskEntity.beneficiary.seg || '-' }}</div>
      <div><strong>Customer Type:</strong> {{ riskEntity.beneficiary.cust_type || '-' }}</div>
      <div><strong>KYC Status:</strong> {{ riskEntity.beneficiary.kyc_status || '-' }}</div>
      <div><strong>Risk Profile:</strong> {{ riskEntity.beneficiary.risk_prof || '-' }}</div>
      <div><strong>Account Number:</strong> {{ riskEntity.beneficiary.account_number || '-' }}</div>
      <div><strong>Account Type:</strong> {{ riskEntity.beneficiary.acc_type || '-' }}</div>
      <div><strong>Account Status:</strong> {{ riskEntity.beneficiary.acc_status || '-' }}</div>
      <div><strong>Account Opening Date:</strong> {{ riskEntity.beneficiary.open_date || '-' }}</div>
      <div><strong>Current Balance:</strong> {{ riskEntity.beneficiary.balance !== undefined ? riskEntity.beneficiary.balance : '-' }}</div>
      <div><strong>Date of Last Transaction:</strong> {{ riskEntity.beneficiary.last_txn_date || '-' }}</div>
      <div><strong>Credit Score:</strong> {{ riskEntity.beneficiary.credit_score !== undefined ? riskEntity.beneficiary.credit_score : '-' }}</div>
    </div>
  </div>
</section>

<!-- Transaction Details -->
<section class="card-section">
  <h2>Transaction Details</h2>
  <div class="tab-selector">
    <button
      :class="['tab-btn', selectedTxnTab === 'victim' ? 'active' : '']"
      @click="selectedTxnTab = 'victim'"
    >Victim</button>
    <button
      :class="['tab-btn', selectedTxnTab === 'beneficiary' ? 'active' : '']"
      @click="selectedTxnTab = 'beneficiary'"
    >Beneficiary</button>
  </div>
  <div class="txn-date-range">
    <label>
      From:
      <input type="date" v-model="txnFilters.from" class="txn-date-input" />
    </label>
    <label>
      To:
      <input type="date" v-model="txnFilters.to" class="txn-date-input" />
    </label>
  </div>
  <div v-if="txnFilters.from && txnFilters.to">
    <div v-if="loadingTransactions" class="case-details-loading">Loading transactions...</div>
    <div v-else-if="transactionError" class="case-details-error">{{ transactionError }}</div>
    <div v-else>
      <button class="download-btn" @click="downloadTransactions">Download</button>
      <table class="txn-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Narration</th>
            <th>Chq./Ref.No.</th>
            <th>Value Dt</th>
            <th>Withdrawal Amt.</th>
            <th>Deposit Amt.</th>
            <th>Closing Balance</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(txn, i) in (selectedTxnTab === 'victim' ? victimTransactions : beneficiaryTransactions)" :key="i">
            <td>{{ txn.date }}</td>
            <td>{{ txn.narration }}</td>
            <td>{{ txn.refNo }}</td>
            <td>{{ txn.valueDate }}</td>
            <td>{{ txn.withdrawal ? Number(txn.withdrawal).toLocaleString('en-IN') : '' }}</td>
            <td>{{ txn.deposit ? Number(txn.deposit).toLocaleString('en-IN') : '' }}</td>
            <td>{{ txn.closingBalance ? Number(txn.closingBalance).toLocaleString('en-IN') : '' }}</td>
          </tr>
          <tr v-if="(selectedTxnTab === 'victim' ? victimTransactions : beneficiaryTransactions).length === 0">
            <td colspan="7" style="text-align:center;">No transactions found.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<section class="card-section">
  <h2>Fraud Notice Uploads</h2>
  <p class="section-subtitle">Attach all relevant documents. All uploads are optional.</p>
  
  <form @submit.prevent="submitUploadedFiles" class="multi-upload-form">
    
    <div class="upload-list">
      <div v-for="docType in documentTypes" :key="docType" class="upload-row">
        <label :for="docType" class="doc-label">{{ docType }}</label>
        <div class="file-input-wrapper">
          <input 
            type="file" 
            :id="docType"
            @change="handleFileSelection($event, docType)" 
            class="doc-file-input"
          />
          </div>
      </div>
    </div>

    <div class="action-buttons" style="justify-content: flex-start; margin-top: 15px;">
        <button type="button" class="submit-btn" @click="openCustomDocumentModal">
            Add Custom Document
        </button>
    </div>
    </form>

  <div class="evidence-panel">
    <div class="evidence-header">Previously Uploaded Documents</div>
    <ul class="doc-list">
      <li v-for="doc in existingDocuments" :key="doc.id" class="doc-list-item">
        <a :href="`/api/download-document/${doc.id}`" target="_blank" rel="noopener noreferrer" class="doc-list-name" style="color: #007bff; text-decoration: underline; cursor: pointer;">
          {{ doc.original_filename }}
        </a>
        <span class="doc-list-type">{{ doc.document_type }}</span>
        <span class="doc-list-date">{{ new Date(doc.uploaded_at).toLocaleString() }}</span>
        <p v-if="doc.comment" class="doc-comment-display">
          **Comment:** {{ doc.comment }}
        </p>
      </li>
      <li v-if="!existingDocuments.length">No documents uploaded for this case yet.</li>
    </ul>
  </div>
</section>

<div class="modal-overlay" v-if="showCommentPopup">
  <div class="modal-content">
    <h3>Add Comment for {{ currentDocTypeForComment }}</h3>
    
    <div v-if="isCustomUpload" style="margin-bottom: 15px;">
        <label for="customDocTypeInput" style="display: block; text-align: left; margin-bottom: 5px; font-weight: 500;">Document Type Name:</label>
        <input 
            type="text" 
            id="customDocTypeInput"
            v-model="customDocumentTypeName" 
            placeholder="e.g., Bank Statement (Custom)" 
            class="comment-modal-input" 
        />
    </div>
    <div v-if="isCustomUpload" style="margin-bottom: 20px;">
        <label for="customFileSelect" style="display: block; text-align: left; margin-bottom: 5px; font-weight: 500;">Select File:</label>
        <input 
            type="file" 
            id="customFileSelect"
            @change="handleCustomFileSelection" 
            class="comment-modal-file-input" 
        />
         <span v-if="selectedFileForUpload" style="display: block; text-align: left; margin-top: 5px; color: #555;">
            Selected: {{ selectedFileForUpload.name }}
        </span>
    </div>
    <textarea
      v-model="currentCommentText"
      placeholder="Enter your comment here..."
      rows="5"
      class="comment-modal-textarea"
    ></textarea>
    <div class="modal-actions">
      <button 
        class="modal-btn-save" 
        @click="saveCommentAndUpload" 
        :disabled="isUploadingSingle || (isCustomUpload && !customDocumentTypeName) || (isCustomUpload && !selectedFileForUpload)"
      >
        {{ isUploadingSingle ? 'Uploading...' : 'Save Comment and Upload' }}
      </button>
      <button class="modal-btn-cancel" @click="cancelComment">Cancel</button>
    </div>
  </div>
</div>

<section class="card-section" v-if="userType === 'CRO' || userType === 'risk_officer'">
        <h2>Case Management</h2>
        <div class="case-mgmt-row" style="padding-top: 10px;">
          <label style="margin-right: 0.7rem;"><strong>Action:</strong></label>
          <select v-model="caseManagementAction" class="console-select" style="max-width: 200px;">
            <option value="ops">Operations</option>
            <option value="assign">Assign To</option>
            <option value="readyToClose">Ready to Close</option>
          </select>

          <template v-if="caseManagementAction === 'ops'">
        <div style="margin-left: 1rem; display: flex; align-items: center;">
          <input 
            type="checkbox" 
            id="operationsCheckbox"
            :checked="operationsStatus" 
            disabled 
            style="margin-right: 0.5rem;"
          />
          <label for="operationsCheckbox"><strong>Operations Status</strong></label>
        </div>
      </template>

          <template v-if="caseManagementAction === 'assign'">
            <input v-model="assignedEmployee" class="console-input" placeholder="Enter Employee ID" style="max-width: 200px; margin-left: 1rem;" />
            
            <textarea
              v-model="assignmentNotes"
              class="console-textarea"
              placeholder="Add notes for this assignment..."
              rows="2"
              style="max-width: 300px; width: 100%; margin-left: 1rem; margin-top: 5px;"
            ></textarea>
            
            <button class="assign-btn" @click="assignCase" :disabled="!assignedEmployee" style="margin-left: 0.7rem; margin-top: 5px;">Assign</button>
          </template>
        </div>
      </section>

      <section class="card-section" v-else-if="userType === 'others'"> <h2>Case Actions</h2>
        <div class="display-grid">
          <div class="span-2">
            <label><strong>Notes for Sending Back:</strong></label>
            <textarea
              v-model="sentBackNotes"
              class="console-textarea"
              placeholder="Enter notes for why this case is being sent back..."
              rows="5"
            ></textarea>
          </div>
        </div>
        <button class="submit-btn" style="margin-top:1.2rem;" @click="sendBackCase" :disabled="!sentBackNotes.trim()">
          Send Case Back
        </button>
      </section>

      <div class="card-section" v-if="caseManagementAction === 'readyToClose'">
        <h2>Decisioning Console</h2>
    <div class="display-grid">
      <div>
        <label><strong>Risk Score:</strong></label>
        <select v-model="decisionConsole.riskScore" class="console-select">
          <option value="">Select</option>
          <option>Low</option>
          <option>Medium</option>
          <option>High</option>
        </select>
      </div>
      <div>
        <label><strong>Triggering Rules:</strong></label>
        <input type="text" v-model="decisionConsole.triggeringRules" class="console-input" placeholder="(leave blank for now)" disabled />
      </div>

      <div class="span-2">
          <label><strong>System Recommendation:</strong></label>
          <textarea v-model="decisionConsole.systemRecommendation" class="console-textarea" placeholder="AI-generated recommendation will appear here..." disabled></textarea>
      </div>
      <div class="span-2">
          <label><strong>System Explanation:</strong></label>
          <textarea v-model="decisionConsole.systemExplanation" class="console-textarea" placeholder="AI-generated explanation will appear here..." disabled></textarea>
      </div>

      <div class="span-2">
        <label><strong>Comments/Notes:</strong></label>
        <textarea v-model="decisionConsole.comments" class="console-textarea" placeholder="Enter comments, context or collaborative notes"></textarea>
      </div>
      <div>
        <label><strong>Decision/Actions:</strong></label>
        <select v-model="decisionConsole.decisionAction" class="console-select">
          <option value="">Select Action</option>
          <option>Already actioned</option>
          <option>To be Actioned</option>
          <option>Hold Funds</option>
          <option>Freeze Account</option>
          <option>Unfreeze Account</option>
          <option>Escalate</option>
          <option>Mark as False Positive</option>
          <option>Request Additional Info</option>
          <option>Block Transaction</option>
          <option>Monitor Account</option>
          <option>Dispute Resolution</option>
          <option>Report to Authorities</option>
          <option>Close Case</option>
        </select>
      </div>
      <div class="span-2">
        <label><strong>Audit Trail/History:</strong></label>
        <textarea v-model="decisionConsole.auditTrail" class="console-textarea" placeholder="Auto-generated, time-stamped log of actions" disabled />
      </div>
    </div>
    <button class="submit-btn" style="margin-top:1.2rem;" @click="submitDecisioningConsole">
      Submit Decision </button>
</div>
    </div>
  </div>
</template>

<script setup>
// Add watch to your imports
import { reactive, ref, computed, onMounted, watch } from 'vue'
// Add useRouter to the import from vue-router
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'


const route = useRoute()
// Initialize the router instance
const router = useRouter()
const ackno = route.params.ackno

// Case Data
const caseData = reactive({
  ackNo: '',
  subCategory: '',
  transactionDate: '',
  complaintDate: '',
  reportDateTime: '',
  state: '',
  district: '',
  policestation: '',
  paymentMode: '',
  accountNumber: '',
  cardNumber: '',
  transactionId: '',
  layers: '',
  transactionAmount: '',
  disputedAmount: '',
  action: '',
  toBank: '',
  toAccount: '',
  ifsc: '',
  toTransactionId: '',
  toAmount: '',
  actionTakenDate: '',
  lienAmount: '',
  evidence: null,
  evidenceName: '',
  additionalInfo: '',
  documents: []
})

// Risk Entity Data
const riskEntity = reactive({
  victim: {},
  beneficiary: {}
})

// Loading & Error States
const loading = ref(true)
const error = ref('')
const riskEntityLoading = ref(true)
const riskEntityError = ref('')

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    // Fetch Complaint Details
    const complaintRes = await axios.get(`http://34.47.219.225:9000/api/case/${ackno}/customer-details`)
    const apiToFrontendMap = {
      ackNo: "Acknowledgement No.",
      subCategory: "Sub Category of Complaint",
      transactionDate: "Transaction Date",
      complaintDate: "Complaint Date",
      reportDateTime: "Date & Time of Reporting / Escalation",
      state: "State",
      district: "District",
      policestation: "Policestation",
      paymentMode: "Mode of Payment",
      accountNumber: "Account Number",
      cardNumber: "Card Number",
      transactionId: "Transaction Id / UTR Number",
      layers: "Layers",
      transactionAmount: "Transaction Amount",
      disputedAmount: "Disputed Amount",
      action: "Action",
      toBank: "Money transfer TO Bank",
      toAccount: "Money transfer TO Account",
      ifsc: "IFSC Code (Non Mandatory)",
      toTransactionId: "Money transfer TO Transaction Id / UTR Number",
      toAmount: "Money transfer TO Amount",
      actionTakenDate: "Action Taken Date",
      lienAmount: "Lien Amount (Non Mandatory)",
      evidenceName: "Evidence Provided (Non Mandatory)",
      additionalInfo: "Additional Information"
    }
    const apiData = complaintRes.data
    for (const [frontendKey, apiKey] of Object.entries(apiToFrontendMap)) {
      caseData[frontendKey] = apiData[apiKey] !== undefined ? apiData[apiKey] : ''
    }

    // Fetch Risk Entity Data (no mapping needed)
    riskEntityLoading.value = true
    const riskRes = await axios.get(`http://34.47.219.225:9000/api/case/${ackno}/risk-profile`)
    Object.assign(riskEntity, riskRes.data)
    
  } catch (e) {
    error.value = 'Failed to fetch case details: ' + (e.message || 'Unknown error')
  } finally {
    loading.value = false
    riskEntityLoading.value = false
  }
})


// ---- Risk Entity Profiles Section ----
const selectedProfileTab = ref('victim')

const selectedTxnTab = ref('victim')
const txnFilters = ref({ from: '', to: '' })
const victimTransactions = ref([])
const beneficiaryTransactions = ref([])
const loadingTransactions = ref(false)
const transactionError = ref('')

// Watch for date or tab changes
// Watch for date changes and fetch transactions
watch(
  () => [txnFilters.value.from, txnFilters.value.to, selectedTxnTab.value],
  async ([from, to, tab]) => {
    if (from && to) {
      loadingTransactions.value = true
      transactionError.value = ''
      try {
        const res = await axios.get(`http://34.47.219.225:9000/api/case/${ackno}/transactions`, {
          params: { from, to, type: tab }
        })
        if (tab === 'victim') {
          victimTransactions.value = res.data.transactions || []
        } else {
          beneficiaryTransactions.value = res.data.transactions || []
        }
      } catch (e) {
        transactionError.value = 'Failed to fetch transactions.'
        victimTransactions.value = []
        beneficiaryTransactions.value = []
      }
      loadingTransactions.value = false
    }
  }
)


function downloadTransactions() {
  const txns = selectedTxnTab.value === 'victim' ? victimTransactions.value : beneficiaryTransactions.value
  if (!txns.length) return
  const header = ['Date', 'Narration', 'Chq./Ref.No.', 'Value Dt', 'Withdrawal Amt.', 'Deposit Amt.', 'Closing Balance']
  const rows = txns.map(txn => [
    txn.date, txn.narration, txn.refNo, txn.valueDate,
    txn.withdrawal, txn.deposit, txn.closingBalance
  ])
  const csvContent = [header, ...rows].map(e => e.join(',')).join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${selectedTxnTab.value}_transactions.csv`
  a.click()
  URL.revokeObjectURL(url)
}


// ---- Document Uploads ----

const documentTypes = [
  'Account Statement', 'Account Details', 'Branch Details', 'Lien Details',
  'AOF (Account Opening Form)', 'KYC (Know Your Customer)', '65B Certificate', 'Photo'
];

// Reactive state for the list of documents already on the server
const existingDocuments = ref([]);
const isUploadingSingle = ref(false); // New state for individual upload loading

// NEW States for the comment popup and custom upload
const showCommentPopup = ref(false);
const currentDocTypeForComment = ref(''); // For predefined types
const currentCommentText = ref('');
const selectedFileForUpload = ref(null);

// NEW State for custom uploads specifically
const isCustomUpload = ref(false); // Flag to know if it's a custom upload flow
const customDocumentTypeName = ref(''); // Used only when isCustomUpload is true


// MODIFIED: handleFileSelection for predefined types
function handleFileSelection(event, docType) {
  const file = event.target.files[0];
  if (file) {
    isCustomUpload.value = false; // It's not a custom upload if from a predefined type
    selectedFileForUpload.value = file;
    currentDocTypeForComment.value = docType; // Set the document type from the predefined list
    currentCommentText.value = ''; // Clear previous comment
    showCommentPopup.value = true;
    event.target.value = null; // Clear input for re-selection
  }
}

// NEW: Function to open the modal for custom document upload
function openCustomDocumentModal() {
  isCustomUpload.value = true; // Set flag for custom upload
  selectedFileForUpload.value = null; // Clear any previously selected file
  customDocumentTypeName.value = ''; // Clear custom type name
  currentDocTypeForComment.value = 'Custom Document'; // Placeholder for modal title
  currentCommentText.value = ''; // Clear comment
  showCommentPopup.value = true;
}

// NEW: Handle file selection for the custom file input inside the modal
function handleCustomFileSelection(event) {
  selectedFileForUpload.value = event.target.files[0];
  // No need to open modal here, it's already open
}

// MODIFIED: saveCommentAndUpload function
async function saveCommentAndUpload() {
  let docTypeToUpload = currentDocTypeForComment.value; // Default for predefined
  let fileToUpload = selectedFileForUpload.value;

  // If it's a custom upload, use the custom type and ensure a file is selected
  if (isCustomUpload.value) {
    if (!customDocumentTypeName.value.trim()) {
      alert("Please enter a name for your custom document type.");
      return;
    }
    if (!selectedFileForUpload.value) {
      alert("Please select a file for your custom document.");
      return;
    }
    docTypeToUpload = customDocumentTypeName.value.trim();
  }

  if (!fileToUpload) {
    alert("No file selected for upload."); // Should be caught by earlier checks, but good to have
    return;
  }
  if (!ackno) {
    alert("Could not determine the case ID for upload.");
    return;
  }

  isUploadingSingle.value = true;
  const formData = new FormData();
  formData.append('file', fileToUpload);
  formData.append('document_type', docTypeToUpload); // Use the resolved document type
  formData.append('comment', currentCommentText.value || '');

  console.log('DEBUG FE: Preparing individual upload.');
  console.log('DEBUG FE: File Name:', fileToUpload.name);
  console.log('DEBUG FE: Document Type:', docTypeToUpload);
  console.log('DEBUG FE: Comment:', currentCommentText.value);

  const url = `http://34.47.219.225:9000/api/case/${ackno}/upload-documents`;

  try {
    const response = await axios.post(url, formData, {
      headers: { /* Axios handles Content-Type for FormData */ }
    });

    console.log('DEBUG FE: API Response:', response.data);

    if (response.data.success && response.data.documents) {
      existingDocuments.value.push(response.data.documents);
      alert('File uploaded successfully!');
    } else {
      alert('Upload failed: ' + (response.data.message || 'Unknown error.'));
    }
  } catch (error) {
    console.error('Error uploading file:', error);
    const errorMessage = error.response?.data?.message || error.message || 'Failed to upload file due to a network error.';
    alert(errorMessage);
  } finally {
    isUploadingSingle.value = false;
    // Reset all popup-related states
    showCommentPopup.value = false;
    selectedFileForUpload.value = null;
    currentDocTypeForComment.value = '';
    currentCommentText.value = '';
    isCustomUpload.value = false; // Reset custom upload flag
    customDocumentTypeName.value = ''; // Clear custom name
  }
}

// MODIFIED: cancelComment - ensure it resets custom upload states too
function cancelComment() {
  showCommentPopup.value = false;
  selectedFileForUpload.value = null;
  currentDocTypeForComment.value = '';
  currentCommentText.value = '';
  isCustomUpload.value = false; // Reset custom upload flag
  customDocumentTypeName.value = ''; // Clear custom name
}

// ... fetchExistingDocuments and onMounted remain the same ...
async function fetchExistingDocuments() {
    if (!ackno) return;
    try {
      const res = await axios.get(`http://34.47.219.225:9000/api/case/${ackno}/documents`);
        if (res.data.success) {
            existingDocuments.value = res.data.documents; 
        }
    } catch (error) {
        console.error("Failed to fetch documents:", error);
    }
}

onMounted(() => {
    fetchExistingDocuments();
});

// NEW: State for the new Case Management dropdown
const userType = ref('');
const caseManagementAction = ref(''); // Will hold 'assign', 'readyToClose', or ''
const assignedEmployee = ref(''); // Will hold the employee ID for 'Assign To'
// NEW: State for notes when assigning a case
const assignmentNotes = ref('');
// NEW: State for notes when sending case back
const sentBackNotes = ref(''); // <--- ADD THIS LINE
const operationsStatus = ref(false);
// --- Reactive state for form data ---
const decisionConsole = reactive({
  ackno: ackno, // REMOVE THIS LINE: ackno is a separate ref, don't nest it here unless truly needed
  riskScore: '',
  triggeringRules: '',
  comments: '',
  decisionAction: '',
  auditTrail: '',
  systemRecommendation: '',
  systemExplanation: '',
});

const sendBackCase = async () => {
  if (!ackno) {
    alert('ACK ID is missing. Cannot send case back.');
    return;
  }
  if (!sentBackNotes.value.trim()) {
    alert('Please add some notes before sending the case back.');
    return;
  }

  try {
    const payload = {
      ackNo: ackno,
      notes: sentBackNotes.value,
      sent_by_user_type: userType.value, // Include user type for backend audit
      sent_by_username: localStorage.getItem('username') // Include username
    };

    // IMPORTANT: Confirm this API endpoint with your backend.
    const res = await axios.post(`http://34.47.219.225:9000/api/case/${ackno}/send-back`, payload);

    if (res.data.success) {
      alert(`Case ${ackno} sent back successfully with notes.`);
      console.log('Case sent back success:', res.data);
      sentBackNotes.value = ''; // Clear notes after successful send
      router.push('/dashboard'); // Or '/case-details' or wherever is appropriate after sending back
    } else {
      alert('Failed to send case back: ' + (res.data.message || 'Unknown error.'));
      console.error('Send back error:', res.data);
    }
  } catch (error) {
    console.error('An error occurred while sending the case back:', error.response?.data || error.message);
    alert('An error occurred while sending the case back. Check console for details.');
  }
};

// 3. NEW: Function to fetch the operations status from the API
const fetchOperationsStatus = async () => {
  if (!ackno) {
    console.error("ACK ID is missing. Cannot fetch operations status.");
    operationsStatus.value = false; // Ensure it's unchecked if no ID
    return;
  }
  try {
    // NOTE: You must replace this URL with your actual API endpoint
    const res = await axios.get(`http://34.47.219.225:9000/api/case/${ackno}/operations-status`);
    
    // Assuming the API returns a boolean in `res.data.status`
    if (res.data && typeof res.data.status === 'boolean') {
      operationsStatus.value = res.data.status;
    } else {
      console.warn("API response for operations status was not a valid boolean.", res.data);
      operationsStatus.value = false; // Default to false on invalid response
    }
  } catch (error) {
    console.error('Failed to fetch operations status:', error.response?.data || error.message);
    operationsStatus.value = false; // Ensure it's unchecked on API error
    alert('An error occurred while fetching the operations status.');
  }
};
// --- Dynamic Validation Function (Your existing code) ---
// ... (isFieldRequired) ...

// --- Function to load existing decision data ---
const fetchDecisionData = async () => {
  // Use ackno.value consistently for the API call
  console.log("Fetching decision data for ackno:", ackno); 
  if (!ackno) {
    console.error("ACK ID is missing from URL parameters. Cannot fetch decision data.");
    return;
  }

  try {
    const res = await axios.get(`http://34.47.219.225:9000/api/case/${ackno}/decision`);
    
    if (res.data.success && res.data.data) {
      const backendData = res.data.data;
      console.log("Fetched decision data:", backendData);

      // FIX: Assign all relevant fields from backend (camelCase) to decisionConsole
      decisionConsole.riskScore = backendData.riskScore || '';
      decisionConsole.triggeringRules = backendData.triggeringRules || '';
      decisionConsole.comments = backendData.comments || '';
      decisionConsole.decisionAction = backendData.decisionAction || '';
      assignedEmployee.value = backendData.assignedEmployee || ''; // Populate assignedEmployee from fetch
      decisionConsole.auditTrail = backendData.auditTrail || '';
      decisionConsole.systemRecommendation = backendData.systemRecommendation || '';
      decisionConsole.systemExplanation = backendData.systemExplanation || '';
      // ... assign other fields if they exist in backendData and decisionConsole

    } else {
        // If success is true but data is null/empty, or success is false
        console.log("No decision data found in backend or backend reported no success. Clearing form fields.");
        // FIX: Clear or set initial placeholders
        decisionConsole.riskScore = '';
        decisionConsole.triggeringRules = '';
        decisionConsole.comments = '';
        decisionConsole.decisionAction = '';
        decisionConsole.assignedEmployee = ''; // Clear assignedEmployee on empty data
        decisionConsole.auditTrail = '';
        decisionConsole.systemRecommendation = '';
        decisionConsole.systemExplanation = '';
        assignedEmployee.value = '';
    }
  } catch (error) {
    console.error('Failed to fetch decision data:', error.response?.data || error.message);
    alert('Failed to load decision data. Check console for details.');
    // FIX: Clear fields on error
    decisionConsole.riskScore = '';
    decisionConsole.triggeringRules = '';
    decisionConsole.comments = '';
    decisionConsole.decisionAction = '';
    decisionConsole.assignedEmployee = '';
    decisionConsole.auditTrail = '';
    decisionConsole.systemRecommendation = '';
    decisionConsole.systemExplanation = '';
    assignedEmployee.value = '';
  }
};

// --- NEW/MODIFIED Function to assign the case ---
const assignCase = async () => {
  const employeeName = assignedEmployee.value; // Get employee name from new ref
  const notes = assignmentNotes.value;

  if (!ackno) {
    alert('ACK ID is missing. Cannot assign case.');
    return;
  }
  if (!employeeName.trim()) {
    alert('Please enter an employee name to assign the case.');
    return;
  }

  try {
    const payload = {
      assigned_to_employee: employeeName, // Key MUST match backend's @Body() parameter
      assignment_notes: notes
    };

    const res = await axios.post(
      `http://34.47.219.225:9000/api/case/${ackno}/assign`,
      payload
    );

    if (res.data.success) {
      alert(`Case ${ackno} assigned to ${employeeName} successfully!`);
      console.log('Assignment success:', res.data);
      router.push('/case-details');
      // Optrouterional: Re-fetch decision data to update the console (e.g., status badge on dashboard)
      // fetchDecisionData(); 
      // If the dashboard needs to reflect the change immediately, you might dispatch an event
      // or implement a refresh mechanism on the dashboard component.
    } else {
      alert('Failed to assign case: ' + (res.data.message || 'Unknown error.'));
      console.error('Assignment error:', res.data);
    }
  } catch (error) {
    console.error('Error assigning case:', error.response?.data || error.message);
    alert('An error occurred while assigning the case. Check console for details.');
  }
};

// --- Function to submit the overall decision (unrelated to direct assign) ---
const submitDecisioningConsole = async () => {

  if (!ackno) {
    alert('ACK ID is missing. Cannot submit decision.');
    return;
  }
  if (caseManagementAction.value !== 'readyToClose') {
    alert('Please select "Ready to Close" in Case Management to submit a decision.');
    return;
  }
  try {
    const payload = {
      riskScore: decisionConsole.riskScore,
      triggeringRules: decisionConsole.triggeringRules,
      comments: decisionConsole.comments,
      decisionAction: decisionConsole.decisionAction,
      // Ensure these are NOT in the payload if you removed them from decisionConsole
      // Do NOT send assignedEmployee as part of this payload, it's handled by /assign API
      auditTrail: decisionConsole.auditTrail,
      // If your backend expects them even disabled, keep these:
      systemRecommendation: decisionConsole.systemRecommendation,
      systemExplanation: decisionConsole.systemExplanation,
    };
    
    // axios.post for the main decision data (save_decision_api)
    const res = await axios.post(`http://34.47.219.225:9000/api/case/${ackno}/decision`, payload);
    
    if (res.data.success) {
      alert('Decision submitted successfully!');
      console.log('Decision submission success:', res.data);
      router.push('/case-details');
      // Optional: Re-fetch data to update audit trail etc.
      // fetchDecisionData();
    } else {
      alert('Failed to submit decision.');
      console.error('Decision submission error:', res.data);
    }
  } catch (error) {
    console.error('Error submitting decision:', error.response?.data || error.message);
    alert('An error occurred while submitting the decision.');
  }
};

// 4. NEW: Add a watcher to trigger the API call when 'Operations' is selected
watch(caseManagementAction, (newAction) => {
  if (newAction === 'ops') {
    fetchOperationsStatus();
  }
});


// --- Load data when the component is mounted ---
onMounted(() => {
  console.log("Component mounted, fetching decision data for ackno:", ackno);
  fetchDecisionData();
});

// --- Load data when the component is mounted ---
onMounted(async () => { // Make sure onMounted is `async` if it performs async operations
  console.log("Component mounted, fetching decision data for ackno:", ackno);

  // Retrieve user_type from localStorage
  const storedUserType = localStorage.getItem('user_type');
  if (storedUserType) {
    userType.value = storedUserType;
    console.log("User Type loaded:", userType.value);
  } else {
    console.warn("User type not found in localStorage. Ensure user is logged in and user_type is set.");
    // Optional: Redirect to login or set a default if userType is critical
    // router.push('/login');
  }

  // --- Your existing data fetching logic below this line ---
  // Example:
  // await fetchDecisionData(); // Make sure this is awaited if it's async

  // Your existing `fetchDecisionData()` call is already there
  fetchDecisionData();
});


</script>

<!-- Import the CSS file -->
<script>
import '../assets/CaseRiskReview.css'
</script>