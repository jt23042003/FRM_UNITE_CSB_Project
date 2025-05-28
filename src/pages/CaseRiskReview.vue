<template>
    <div class="case-entry-bg">
      <h1 class="screen-header">Complaint Details</h1>
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


      <!-- 1b. Bank Customer Details -->
      <section class="card-section">
  <h2>Risk Entity Profiles</h2>
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
    <div><strong>Customer ID/Number:</strong> {{ victimBankProfile.customerId }}</div>
    <div><strong>Full Name:</strong> {{ victimBankProfile.fullName }}</div>
    <div><strong>Date of Birth:</strong> {{ victimBankProfile.dob }}</div>
    <div><strong>Primary Residential Address:</strong> {{ victimBankProfile.address }}</div>
    <div><strong>National ID/Passport Number:</strong> {{ victimBankProfile.nationalId }}</div>
    <div><strong>PAN (Permanent Account Number):</strong> {{ victimBankProfile.pan }}</div>
    <div><strong>Citizenship:</strong> {{ victimBankProfile.citizenship }}</div>
    <div><strong>Occupation/Employment Details:</strong> {{ victimBankProfile.occupation }}</div>
    <div><strong>Customer Segment:</strong> {{ victimBankProfile.customerSegment }}</div>
    <div><strong>Customer Type:</strong> {{ victimBankProfile.customerType }}</div>
    <div><strong>KYC Status and Date of Last KYC Review:</strong> {{ victimBankProfile.kycStatus }}</div>
    <div><strong>Risk Profile:</strong> {{ victimBankProfile.riskProfile }}</div>
    <div><strong>Account Number:</strong> {{ victimBankProfile.accountNumber }}</div>
    <div><strong>Account Type:</strong> {{ victimBankProfile.accountType }}</div>
    <div><strong>Account Status:</strong> {{ victimBankProfile.accountStatus }}</div>
    <div><strong>Account Opening Date:</strong> {{ victimBankProfile.accountOpenDate }}</div>
    <div><strong>Current Balance:</strong> ₹{{ victimBankProfile.currentBalance }}</div>
    <div><strong>Date of Last Transaction:</strong> {{ victimBankProfile.lastTransactionDate }}</div>
    <div><strong>Credit Rating or Score:</strong> {{ victimBankProfile.creditScore }}</div>
    <div><strong>Recent High-Value Transactions:</strong> {{ victimBankProfile.recentHighValueTxns }}</div>
    <div><strong>Number of PAN-Linked Accounts:</strong> {{ victimBankProfile.panLinkedAccounts }}</div>
    <div><strong>Alerts or Flags Raised:</strong> {{ victimBankProfile.alerts }}</div>
    <div><strong>Watchlist/Sanctions Screening Status:</strong> {{ victimBankProfile.sanctionsStatus }}</div>
  </div>
  <div v-else class="display-grid">
    <div><strong>Customer ID/Number:</strong> {{ beneficiaryBankProfile.customerId }}</div>
    <div><strong>Full Name:</strong> {{ beneficiaryBankProfile.fullName }}</div>
    <div><strong>Date of Birth:</strong> {{ beneficiaryBankProfile.dob }}</div>
    <div><strong>Primary Residential Address:</strong> {{ beneficiaryBankProfile.address }}</div>
    <div><strong>National ID/Passport Number:</strong> {{ beneficiaryBankProfile.nationalId }}</div>
    <div><strong>PAN (Permanent Account Number):</strong> {{ beneficiaryBankProfile.pan }}</div>
    <div><strong>Citizenship:</strong> {{ beneficiaryBankProfile.citizenship }}</div>
    <div><strong>Occupation/Employment Details:</strong> {{ beneficiaryBankProfile.occupation }}</div>
    <div><strong>Customer Segment:</strong> {{ beneficiaryBankProfile.customerSegment }}</div>
    <div><strong>Customer Type:</strong> {{ beneficiaryBankProfile.customerType }}</div>
    <div><strong>KYC Status and Date of Last KYC Review:</strong> {{ beneficiaryBankProfile.kycStatus }}</div>
    <div><strong>Risk Profile:</strong> {{ beneficiaryBankProfile.riskProfile }}</div>
    <div><strong>Account Number:</strong> {{ beneficiaryBankProfile.accountNumber }}</div>
    <div><strong>Account Type:</strong> {{ beneficiaryBankProfile.accountType }}</div>
    <div><strong>Account Status:</strong> {{ beneficiaryBankProfile.accountStatus }}</div>
    <div><strong>Account Opening Date:</strong> {{ beneficiaryBankProfile.accountOpenDate }}</div>
    <div><strong>Current Balance:</strong> ₹{{ beneficiaryBankProfile.currentBalance }}</div>
    <div><strong>Date of Last Transaction:</strong> {{ beneficiaryBankProfile.lastTransactionDate }}</div>
    <div><strong>Credit Rating or Score:</strong> {{ beneficiaryBankProfile.creditScore }}</div>
    <div><strong>Recent High-Value Transactions:</strong> {{ beneficiaryBankProfile.recentHighValueTxns }}</div>
    <div><strong>Number of PAN-Linked Accounts:</strong> {{ beneficiaryBankProfile.panLinkedAccounts }}</div>
    <div><strong>Alerts or Flags Raised:</strong> {{ beneficiaryBankProfile.alerts }}</div>
    <div><strong>Watchlist/Sanctions Screening Status:</strong> {{ beneficiaryBankProfile.sanctionsStatus }}</div>
  </div>
</section>


  
<section class="card-section">
  <h2>Transaction Details</h2>
  <div class="tab-selector">
    <button
      :class="['tab-btn', selectedTxnTab === 'victim' ? 'active' : '']"
      @click="selectedTxnTab = 'victim'"
    >
      Victim
    </button>
    <button
      :class="['tab-btn', selectedTxnTab === 'beneficiary' ? 'active' : '']"
      @click="selectedTxnTab = 'beneficiary'"
    >
      Beneficiary
    </button>
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
        <tr v-for="(txn, i) in filteredTransactions" :key="i">
          <td>{{ txn.date }}</td>
          <td>{{ txn.narration }}</td>
          <td>{{ txn.refNo }}</td>
          <td>{{ txn.valueDate }}</td>
          <td>{{ txn.withdrawal ? Number(txn.withdrawal).toLocaleString('en-IN') : '' }}</td>
          <td>{{ txn.deposit ? Number(txn.deposit).toLocaleString('en-IN') : '' }}</td>
          <td>{{ txn.closingBalance ? Number(txn.closingBalance).toLocaleString('en-IN') : '' }}</td>
        </tr>
        <tr v-if="filteredTransactions.length === 0">
          <td colspan="7" style="text-align:center;">No transactions found.</td>
        </tr>
      </tbody>
    </table>
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
  
      <!-- 5. Action Buttons -->
      <section class="card-section">
  <h2>Decisioning Console</h2>
  <div class="display-grid">
    <!-- Risk Score -->
    <div>
      <label><strong>Risk Score:</strong></label>
      <select v-model="decisionConsole.riskScore" class="console-select">
        <option value="">Select</option>
        <option>Low</option>
        <option>Medium</option>
        <option>High</option>
      </select>
    </div>
    <!-- Triggering Rules -->
    <div>
      <label><strong>Triggering Rules:</strong></label>
      <input type="text" v-model="decisionConsole.triggeringRules" class="console-input" placeholder="(leave blank for now)" disabled />
    </div>
    <!-- Comments/Notes -->
    <div class="span-2">
      <label><strong>Comments/Notes:</strong></label>
      <textarea v-model="decisionConsole.comments" class="console-textarea" placeholder="Enter comments, context or collaborative notes"></textarea>
    </div>
    <!-- Decision/Actions -->
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
    <!-- Case Management -->
  <!-- Case Management (inline layout) -->
<div class="case-mgmt-row">
  <label style="margin-right: 0.7rem;"><strong>Case Management:</strong></label>
  <select v-model="decisionConsole.caseManagement" class="console-select" style="max-width: 160px;">
    <option value="">Select</option>
    <option value="assign">Assign To</option>
  </select>
  <template v-if="decisionConsole.caseManagement === 'assign'">
    <input
      v-model="decisionConsole.assignedEmployee"
      class="console-input"
      placeholder="Enter Employee ID (e.g., e2918)"
      autocomplete="off"
      style="max-width: 150px; margin-left: 1rem;"
    />
    <button class="assign-btn" @click="assignCase" :disabled="!decisionConsole.assignedEmployee" style="margin-left: 0.7rem;">
      Assign
    </button>
  </template>
</div>


    
    <!-- Audit Trail/History -->
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
  </template>
  
  <script setup>
import { reactive, ref, computed } from 'vue'


const selectedProfileTab = ref('victim')

  // 1. Customer and Beneficiary Details (dummy data for now)
  const caseData = reactive({
  complaintRef: 'CMP20250506-001',
  incidentDateTime: '2025-05-04T14:30',
  complaintType: 'UPI Fraud',
  victimName: 'Rohit Sharma',
  victimContact: '9876543210',
  victimEmail: 'rohit.sharma@email.com',
  victimAccountNumber: '123456789012',
  victimBankName: 'Gpay',
  transactionId: '238428347',
  ifsc: 'SBIN0001234',
  victimRelativeName: 'Kriti Sharma',
  victimAddress: '13/6 Ghanapati Street, T.nagar',
  victimState: 'Tamil Nadu',
  victimCity: 'Chennai',
  victimPincode: '600033',
  fraudAmount: '10000',
  lienAmount: '10000',
  beneficiaryAccountNumber: '987654321234',
  beneficiaryMobile: '9123456789',
  beneficiaryEmail: 'amit.kumar@email.com',
  beneficiaryUPI: 'amitkumar@upi',
  beneficiaryIp: '38.239.329.234',
  beneficiaryInfo: 'Known fraudster, flagged in registry.',
  documents: [],
  urls: 'PhonePe, www.fakebank.com',
  actionRequested: 'Freeze Account',
  policeName: 'OC-Mangaldai',
  policeDesignation: 'Station house officer (SHO)',
  policeMobile: '9101056789',
  policeEmail: 'Mangadai@assampolice.gov.in',
  additionalInfo: 'I was added in a WhatsApp group and...',
  ackNo: 'ACK20250506-001',
  subCategory: 'Phishing',
  transactionDate: '2025-05-04',
  complaintDate: '2025-05-05',
  reportDateTime: '2025-05-05T10:30',
  state: 'Karnataka',
  district: 'Bangalore',
  policestation: 'MG Road PS',
  paymentMode: 'UPI',
  accountNumber: '123456789012',
  cardNumber: '41',
  transactionId: 'TXN00123ABC',
  layers: 'Layer 3',
  transactionAmount: 15000,
  disputedAmount: 15000,
  action: 'Freeze',
  toBank: 'HDFC',
  toAccount: '99887766554',
  ifsc: 'HDFC0001234',
  toTransactionId: 'TXN998877',
  toAmount: 15000,
  actionTakenDate: '2025-05-06',
  lienAmount: 5000,
  evidence: null, // file object, not displayed here
  evidenceName: 'fraud_doc.pdf', // or '' if not uploaded
  additionalInfo: 'Victim approached us within 6 hours of incident'
})

  
const selectedTxnTab = ref('victim')
const txnFilters = ref({ from: '', to: '' })

const victimBankProfile = reactive({
  customerId: caseData.victimCustomerId || 'CUST123456',
  fullName: caseData.victimName || 'Rajesh Kumar',
  dob: caseData.victimDOB || '1985-07-15',
  address: caseData.victimAddress || '123 MG Road, Bengaluru, Karnataka',
  nationalId: caseData.victimAadhaar || 'Aadhar: 1234-5678-9012',
  pan: caseData.victimPAN || 'ABCDE1234F',
  citizenship: caseData.victimCitizenship || 'Indian',
  occupation: caseData.victimOccupation || 'Software Engineer',
  customerSegment: caseData.victimSegment || 'Retail',
  customerType: caseData.victimType || 'Individual',
  kycStatus: caseData.victimKYCStatus || 'Verified, Last Review: 2024-12-01',
  riskProfile: caseData.victimRiskProfile || 'Medium Risk',
  accountNumber: caseData.victimAccountNumber || 'SB1234567890',
  accountType: caseData.victimAccountType || 'Savings',
  accountStatus: caseData.victimAccountStatus || 'Active',
  accountOpenDate: caseData.victimAccountOpenDate || '2010-05-20',
  currentBalance: caseData.victimCurrentBalance || '1,50,000',
  lastTransactionDate: caseData.victimLastTxnDate || '2025-05-05',
  creditScore: caseData.victimCreditScore || '750',
  recentHighValueTxns: caseData.victimRecentHighValueTxns || '3 transactions above ₹1,00,000 in last month',
  panLinkedAccounts: caseData.victimPANLinkedAccounts || '2',
  alerts: caseData.victimAlerts || 'No alerts',
  sanctionsStatus: caseData.victimSanctionsStatus || 'Clear'
})

const beneficiaryBankProfile = reactive({
  customerId: caseData.beneficiaryCustomerId || 'CUST654321',
  fullName: caseData.beneficiaryName || 'Amit Kumar',
  dob: caseData.beneficiaryDOB || '1990-02-10',
  address: caseData.beneficiaryAddress || '22/1 MG Road, Bengaluru, Karnataka',
  nationalId: caseData.beneficiaryAadhaar || 'Aadhar: 4321-8765-2109',
  pan: caseData.beneficiaryPAN || 'XYZDE9876P',
  citizenship: caseData.beneficiaryCitizenship || 'Indian',
  occupation: caseData.beneficiaryOccupation || 'Business Owner',
  customerSegment: caseData.beneficiarySegment || 'SME',
  customerType: caseData.beneficiaryType || 'Individual',
  kycStatus: caseData.beneficiaryKYCStatus || 'Verified, Last Review: 2025-01-15',
  riskProfile: caseData.beneficiaryRiskProfile || 'High Risk',
  accountNumber: caseData.beneficiaryAccountNumber || 'SB9876543210',
  accountType: caseData.beneficiaryAccountType || 'Current',
  accountStatus: caseData.beneficiaryAccountStatus || 'Active',
  accountOpenDate: caseData.beneficiaryAccountOpenDate || '2015-03-10',
  currentBalance: caseData.beneficiaryCurrentBalance || '2,10,000',
  lastTransactionDate: caseData.beneficiaryLastTxnDate || '2025-05-06',
  creditScore: caseData.beneficiaryCreditScore || '720',
  recentHighValueTxns: caseData.beneficiaryRecentHighValueTxns || '2 transactions above ₹2,00,000 in last month',
  panLinkedAccounts: caseData.beneficiaryPANLinkedAccounts || '1',
  alerts: caseData.beneficiaryAlerts || 'No alerts',
  sanctionsStatus: caseData.beneficiarySanctionsStatus || 'Clear'
})

function assignCase() {
  if (decisionConsole.assignedEmployee) {
    alert(`Case assigned to employee ID: ${decisionConsole.assignedEmployee}`)
    // Here, you can call your API or perform the actual assignment logic
    // Example: await axios.post('/api/assign-case', { employeeId: decisionConsole.assignedEmployee, ... })
  }
}


const victimTransactions = ref([
  {
    date: '07/05/25',
    narration: 'UPI-FOOD ORDER-ZOMATO',
    refNo: 'TXN20250507001',
    valueDate: '07/05/25',
    withdrawal: 250.00,
    deposit: '',
    closingBalance: 12000.00
  },
  {
    date: '08/05/25',
    narration: 'NEFT-SALARY CREDIT',
    refNo: 'TXN20250508002',
    valueDate: '08/05/25',
    withdrawal: '',
    deposit: 50000.00,
    closingBalance: 62000.00
  }
])

const beneficiaryTransactions = ref([
  {
    date: '07/05/25',
    narration: 'IMPS-RECEIVED',
    refNo: 'TXN20250507003',
    valueDate: '07/05/25',
    withdrawal: '',
    deposit: 1500.00,
    closingBalance: 5000.00
  }
])


const filteredTransactions = computed(() => {
  const txns = selectedTxnTab.value === 'victim' ? victimTransactions.value : beneficiaryTransactions.value
  if (txnFilters.value.from && txnFilters.value.to) {
    // Convert yyyy-mm-dd to dd/mm/yy for comparison
    const from = formatDate(txnFilters.value.from)
    const to = formatDate(txnFilters.value.to)
    return txns.filter(txn =>
      txn.date >= from && txn.date <= to
    )
  }
  return []
})



// Helper to format yyyy-mm-dd to dd/mm/yy
function formatDate(input) {
  if (!input) return ''
  const [yyyy, mm, dd] = input.split('-')
  return `${dd}/${mm}/${yyyy.slice(2)}`
}


// Download as CSV
function downloadTransactions() {
  const txns = filteredTransactions.value
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
  const newDoc = reactive({ type: '', file: null })
  const fileInput = ref(null)
  
  function onDocFileChange(e) {
    newDoc.file = e.target.files[0] || null
  }
  
  function uploadDocument() {
    if (!newDoc.type || !newDoc.file) return
    // Simulate upload and add to list (replace with real API call)
    const id = Date.now()
    caseData.documents.push({
      id,
      type: newDoc.type,
      name: newDoc.file.name,
      url: URL.createObjectURL(newDoc.file)
    })
    newDoc.type = ''
    newDoc.file = null
    if (fileInput.value) fileInput.value.value = ''
  }
  
  function deleteDocument(id) {
    caseData.documents = caseData.documents.filter(doc => doc.id !== id)
  }

  const decisionConsole = reactive({
  riskScore: '',
  triggeringRules: '',
  comments: '',
  decisionAction: '',
  caseManagement: '',
  assignedEmployee: '',
  auditTrail: '2025-05-09 15:54:00 - Case created by Risk Officer\n2025-05-09 16:02:00 - Status changed to Under Investigation'
})



function submitDecisioningConsole() {
  alert('Decisioning Console submitted!\n' + JSON.stringify(decisionConsole, null, 2))
  // Replace with actual API call as needed
}

  
  // 4. Action Buttons
  const selectedAction = ref('')
  const actionRemark = ref('')
  </script>
  
  <!-- Import the CSS file -->
  <script>
  import '../assets/CaseRiskReview.css'
  </script>
  