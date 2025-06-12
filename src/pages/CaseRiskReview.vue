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
          <div><strong>Account Number:</strong> {{ caseData.accountNumber }}</div>
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
        <div class="fraud-upload-container">
          <h2>Fraud Notice Uploads</h2>
          <form @submit.prevent="uploadDocument" class="upload-form">
            <select v-model="newDoc.type" required class="doc-type-select">
              <option value="">Select Document Type</option>
              <option>Account Statement</option>
              <option>Account Details</option>
              <option>Branch Details</option>
              <option>Lien Details</option>
              <option>AOF (Account Opening Form)</option>
              <option>KYC (Know Your Customer)</option>
              <option>65B Certificate</option>
              <option>Photo</option>
            </select>
            <input type="file" ref="fileInput" @change="onDocFileChange" required class="doc-file-input" />
            <button type="submit" class="upload-btn">Upload</button>
          </form>
          <div class="evidence-panel">
            <div class="evidence-header">Evidence/Documents Uploaded</div>
            <ul class="doc-list">
              <li v-for="doc in caseData.documents" :key="doc.id">
                <span class="doc-type">{{ doc.type }}</span>
                <a :href="doc.url" target="_blank">{{ doc.name }}</a>
                <button @click="deleteDocument(doc.id)" class="delete-doc-btn">Delete</button>
              </li>
              <li v-if="!caseData.documents.length">No documents uploaded.</li>
            </ul>
          </div>
        </div>
      </section>

      <section class="card-section">
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
</section>
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
    const riskRes = await axios.get(`http://34.47.219.225:9000/api/case/${ackno}/risk-entity-profile`)
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
const newDoc = reactive({ type: '', file: null })
const fileInput = ref(null)
function onDocFileChange(e) {
  newDoc.file = e.target.files[0] || null
}

async function uploadDocument() {
  if (!newDoc.type || !newDoc.file) {
    alert("Please select a document type and a file.");
    return;
  }

  // THIS IS THE DYNAMIC PART
  const ackno = route.params.ackno; // Get the ackno from the URL, e.g., /cases/ACKNEW123
  
  // Check if ackno was found
  if (!ackno) {
    alert("Could not determine the case ID from the URL.");
    return;
  }

  const formData = new FormData();
  formData.append('document_type', newDoc.type);
  formData.append('file', newDoc.file, newDoc.file.name);

  const url = `http://34.47.219.225:9000/api/case/${ackno}/upload-document`;

  try {
    const response = await axios.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    console.log('Upload successful:', response.data);
    // Now you can update your local list with the successful upload
    
  } catch (error) {
    console.error('Error uploading file:', error);
    alert('Failed to upload file.');
  }
}

function deleteDocument(id) {
  caseData.documents = caseData.documents.filter(doc => doc.id !== id)
}

// ---- Decisioning Console ----
const decisionConsole = reactive({
  riskScore: '',
  triggeringRules: '',
  comments: '',
  decisionAction: '',
  caseManagement: '',
  assignedEmployee: '',
  auditTrail: '', // Will be loaded from the backend
  systemRecommendation: '', // New field
  systemExplanation: ''     // New field
});

// --- Function to load existing decision data ---
const fetchDecisionData = async () => {
  if (!ackno) return;
  try {
    const res = await axios.get(`http://34.47.219.225:9000/api/case/${ackno}/decision`);
    if (res.data.success && res.data.data) {
      // Populate the form with data from the backend
      decisionConsole.riskScore = res.data.data.risk_score || '';
      decisionConsole.comments = res.data.data.comments || '';
      decisionConsole.decisionAction = res.data.data.decision_action || '';
      decisionConsole.assignedEmployee = res.data.data.assigned_employee || '';
      decisionConsole.auditTrail = res.data.data.audit_trail || 'No actions logged yet.';
      
      // Populate new fields (with placeholder logic for now)
      decisionConsole.systemRecommendation = res.data.data.system_recommendation || 'Recommendation: Monitor Account';
      decisionConsole.systemExplanation = res.data.data.system_explanation || 'Explanation: Transaction pattern matches moderate risk profile.';
    }
  } catch (error) {
    console.error('Failed to fetch decision data:', error);
  }
};

// --- Function to submit the decision ---
const submitDecisioningConsole = async () => {
  if (!ackno) return;
  try {
    const payload = {
      riskScore: decisionConsole.riskScore,
      triggeringRules: decisionConsole.triggeringRules,
      comments: decisionConsole.comments,
      decisionAction: decisionConsole.decisionAction,
      assignedEmployee: decisionConsole.assignedEmployee,
      auditTrail: decisionConsole.auditTrail,
      systemRecommendation: decisionConsole.systemRecommendation,
      systemExplanation: decisionConsole.systemExplanation,
    };
    
    const res = await axios.post(`http://34.47.219.225:9000/api/case/${ackno}/decision`, payload);
    
    if (res.data.success) {
      alert('Decision submitted successfully!');
    } else {
      alert('Failed to submit decision.');
    }
  } catch (error) {
    console.error('Error submitting decision:', error);
    alert('An error occurred while submitting the decision.');
  }
};

function assignCase() {
  if (decisionConsole.assignedEmployee) {
    alert(`Case assigned to employee ID: ${decisionConsole.assignedEmployee}`);
    // You could also trigger a save here if desired
    // submitDecisioningConsole();
  }
}

// --- Load data when the component is mounted ---
onMounted(() => {
  fetchDecisionData();
});


</script>

<!-- Import the CSS file -->
<script>
import '../assets/CaseRiskReview.css'
</script>
