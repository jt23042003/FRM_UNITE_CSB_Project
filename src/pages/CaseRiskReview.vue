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

      <!-- 4. Document Uploads (Upload + List) -->
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
          <span v-if="filesToUpload[docType]" class="file-name-display">
            {{ filesToUpload[docType].name }}
          </span>
        </div>
      </div>
    </div>

    <div class="action-buttons">
      <button type="submit" class="submit-btn" :disabled="isUploading">
        {{ isUploading ? 'Uploading...' : 'Upload Selected Files' }}
      </button>
    </div>
  </form>

  <div class="evidence-panel">
    <div class="evidence-header">Previously Uploaded Documents</div>
    <ul class="doc-list">
      <li v-for="doc in existingDocuments" :key="doc.id">
        </li>
      <li v-if="!existingDocuments.length">No documents uploaded for this case yet.</li>
    </ul>
  </div>
</section>

<div class="card-section">
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
      <div class="case-mgmt-row">
        <label style="margin-right: 0.7rem;"><strong>Case Management:</strong></label>
        <select v-model="decisionConsole.caseManagement" class="console-select" style="max-width: 160px;">
          <option value="">Select</option>
          <option value="assign">Assign To</option>
        </select>
        <template v-if="decisionConsole.caseManagement === 'assign'">
          <input v-model="decisionConsole.assignedEmployee" class="console-input" placeholder="Enter Employee ID" style="max-width: 150px; margin-left: 1rem;" />
          <button class="assign-btn" @click="assignCase" :disabled="!decisionConsole.assignedEmployee" style="margin-left: 0.7rem;">Assign</button>
        </template>
      </div>
      <div class="span-2">
        <label><strong>Audit Trail/History:</strong></label>
        <textarea v-model="decisionConsole.auditTrail" class="console-textarea" placeholder="Auto-generated, time-stamped log of actions" disabled />
      </div>
    </div>
    <button class="submit-btn" style="margin-top:1.2rem;" @click="submitDecisioningConsole">
      Submit
    </button>
</div>
    </div>
  </div>
</template>

<script setup>
// Add watch to your imports
import { reactive, ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'


const route = useRoute()
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

// Use a reactive object to hold the files staged for upload
// Keys are the document types, values are the File objects
const filesToUpload = reactive({});

// Reactive state for the list of documents already on the server
const existingDocuments = ref([]);
const isUploading = ref(false);

// This function is called whenever any file input changes
function handleFileSelection(event, docType) {
  const file = event.target.files[0];
  if (file) {
    filesToUpload[docType] = file;
  } else {
    // If the user cancels file selection, remove it
    delete filesToUpload[docType];
  }
}

// This function uploads all selected files at once
async function submitUploadedFiles() {
  if (Object.keys(filesToUpload).length === 0) {
    alert("Please select at least one file to upload.");
    return;
  }
  if (!ackno) {
    alert("Could not determine the case ID.");
    return;
  }

  isUploading.value = true;
  const formData = new FormData();

  // Append each selected file to the FormData object
  // The key will be the document type string
  for (const docType in filesToUpload) {
    formData.append(docType, filesToUpload[docType]);
  }

  const url = `http://34.47.219.225:9000/api/case/${ackno}/upload-documents`; // Note the new URL

  try {
    const response = await axios.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    alert('Files uploaded successfully!');
    console.log('Upload successful:', response.data);
    
    // After successful upload, clear the selection and refresh the list of documents
    Object.keys(filesToUpload).forEach(key => delete filesToUpload[key]);
    fetchExistingDocuments(); 

  } catch (error) {
    console.error('Error uploading files:', error);
    alert('Failed to upload files.');
  } finally {
    isUploading.value = false;
  }
}

// --- Function to get the list of existing documents ---
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

// --- Load existing documents when the component is first loaded ---
onMounted(() => {
    fetchExistingDocuments();
});

// --- Your reactive object where data is stored ---
// Ensure all these properties exist in your reactive object
// and match the camelCase keys returned by the backend.
// --- Reactive state for form data ---
const decisionConsole = reactive({
  // ackno: ackno, // REMOVE THIS LINE: ackno is a separate ref, don't nest it here unless truly needed
  riskScore: '',
  triggeringRules: '',
  comments: '',
  decisionAction: '',
  caseManagement: '', // Ensure this is reactive to control the assign input visibility
  assignedEmployee: '', // This will hold the employee ID for assignment
  auditTrail: '',
  systemRecommendation: '',
  systemExplanation: '',
  // Add other reactive properties if your form has them and they should be updated
  // e.g., lastUpdatedAt: null,
});

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
      decisionConsole.caseManagement = backendData.caseManagement || ''; // If backend sends this
      decisionConsole.assignedEmployee = backendData.assignedEmployee || ''; // Populate assignedEmployee from fetch
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
  }
};

// --- NEW/MODIFIED Function to assign the case ---
const assignCase = async () => {
  const employeeName = decisionConsole.assignedEmployee; // Get employee name from v-model
  const currentAckNo = ackno; // Get ACK ID

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
      assigned_to_employee: employeeName // Key MUST match backend's @Body() parameter
    };

    const res = await axios.post(
      `http://34.47.219.225:9000/api/case/${ackno}/assign`,
      payload
    );

    if (res.data.success) {
      alert("Case ${ackno} assigned to ${employeeName} successfully!");
      console.log('Assignment success:', res.data);
      // Optional: Re-fetch decision data to update the console (e.g., status badge on dashboard)
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
  try {
    const payload = {
      riskScore: decisionConsole.riskScore,
      triggeringRules: decisionConsole.triggeringRules,
      comments: decisionConsole.comments,
      decisionAction: decisionConsole.decisionAction,
      // Do NOT send assignedEmployee as part of this payload, it's handled by /assign API
      // systemRecommendation and systemExplanation are disabled, so they shouldn't be part of payload
      // unless you explicitly enable and expect user to edit them for submission.
      auditTrail: decisionConsole.auditTrail,
    };
    
    // axios.post for the main decision data (save_decision_api)
    const res = await axios.post(`http://34.47.219.225:9000/api/case/${ackno}/decision`, payload);
    
    if (res.data.success) {
      alert('Decision submitted successfully!');
      console.log('Decision submission success:', res.data);
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


// --- Load data when the component is mounted ---
onMounted(() => {
  console.log("Component mounted, fetching decision data for ackno:", ackno);
  fetchDecisionData();
});


</script>

<!-- Import the CSS file -->
<script>
import '../assets/CaseRiskReview.css'
</script>
