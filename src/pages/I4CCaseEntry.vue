<template>
  <div class="form-bg">
    <form class="entry-card grouped-form" @submit.prevent="onSubmit">
      <h2 class="form-title">I4C Fraud Complaint Entry</h2>
      <div class="section-grid">

        <label>
          Acknowledgement No.
          <input v-model="form.ackNo" type="text" required />
        </label>
        <label>
          Sub Category of Complaint
          <select v-model="form.subCategory" required>
            <option disabled value="">Select Sub Category</option>
            <option v-for="option in subCategoryOptions" :key="option" :value="option">{{ option }}</option>
          </select>
        </label>
        <label>
          Transaction Date
          <input v-model="form.transactionDate" type="date" required />
        </label>
        
        <label>
          Mode of Payment
          <select v-model="form.paymentMode" required>
            <option disabled value="">Select Mode of Payment</option>
            <option v-for="mode in paymentModeOptions" :key="mode" :value="mode">{{ mode }}</option>
          </select>
        </label>

        <label>
          Account Number
          <input v-model="form.accountNumber" type="text" pattern="\d*" title="Please enter only numbers" :required="isFieldRequired('accountNumber')" />
        </label>
        <label>
          Card Number
          <input v-model="form.cardNumber" type="text" pattern="\d*" title="Please enter only numbers" :required="isFieldRequired('cardNumber')" />
        </label>
        <label>
          Money transfer TO Account
          <input v-model="form.toAccount" type="text" pattern="\d*" title="Please enter only numbers" :required="isFieldRequired('toAccount')" />
        </label>
        <label>
          IFSC Code (Non Mandatory)
          <input v-model="form.ifsc" type="text" :required="isFieldRequired('ifsc')" />
        </label>
        <label>
          UPI Id
          <input v-model="form.toUpiId" type="text" :required="isFieldRequired('toUpiId')" />
        </label>
        
        <label>
          Complaint Date
          <input v-model="form.complaintDate" type="date" required />
        </label>
        <label>
          Date & Time of Reporting / Escalation
          <input v-model="form.reportDateTime" type="datetime-local" required />
        </label>
        <label>
          State
          <select v-model="form.state" required>
            <option disabled value="">Select State</option>
            <option v-for="st in stateOptions" :key="st" :value="st">{{ st }}</option>
          </select>
        </label>
        <label>
          District
          <input v-model="form.district" type="text" required />
        </label>
        <label>
          Policestation
          <input v-model="form.policestation" type="text" required />
        </label>
        <label>
          Transaction Id / UTR Number
          <input v-model="form.transactionId" type="text" required />
        </label>
        <label>
          Layers
          <select v-model="form.layers" required>
            <option value="">Select Layer</option>
            <option v-for="n in 30" :key="n" :value="`Layer ${n}`">Layer {{ n }}</option>
          </select>
        </label>
        <label>
          Transaction Amount
          <input v-model.number="form.transactionAmount" type="number" min="0" step="any" required />
        </label>
        <label>
          Disputed Amount
          <input v-model.number="form.disputedAmount" type="number" min="0" step="any" required />
        </label>
        <label>
          Action (Non Mandatory)
          <select v-model="form.action">
            <option value="">Select Action</option>
            <option v-for="opt in actionOptions" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </label>
        <label>
          Money transfer TO Bank
          <input v-model="form.toBank" type="text" required/>
        </label>
        <label>
          Money transfer TO Transaction Id / UTR Number
          <input v-model="form.toTransactionId" type="text" required/>
        </label>
        <label>
          Money transfer TO Amount
          <input v-model.number="form.toAmount" type="number" min="0" step="any" required/>
        </label>
        <label>
          Action Taken Date
          <input v-model="form.actionTakenDate" type="date" required/>
        </label>
        <label>
          Lien Amount (Non Mandatory)
          <input v-model.number="form.lienAmount" type="number" min="0" step="any" />
        </label>
        <label>
          Evidence Provided (Non Mandatory)
          <input type="file" @change="onFileChange" ref="fileInputRef" />
          <span v-if="form.evidenceName" style="display:block;margin-top:0.3rem;color:#2563eb;">Selected: {{ form.evidenceName }}</span>
        </label>
        <label class="span-all">
          Additional Information (Non Mandatory)
          <textarea v-model="form.additionalInfo" placeholder="I was added in a WhatsApp group and..."></textarea>
        </label>
      </div>
      <div class="action-buttons span-all">
        <button class="submit-btn" type="submit">Submit/Save</button>
        <button class="reset-btn" type="button" @click="onReset">Reset/Clear</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import axios from 'axios';

// --- Dropdown Options ---
const subCategoryOptions = [ 'Online Scams', 'Phishing', 'Unauthorized Transactions', 'Credit/Debit Card Fraud', 'UPI/Wallet Frauds', 'SIM Swap Fraud', 'Vishing (Voice Phishing)', 'Smishing (SMS Phishing)', 'Fake Banking Websites/Apps', 'Online Payment Gateway Frauds', 'KYC Update Frauds', 'Loan App Frauds', 'Others' ];
const stateOptions = [ 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal' ];
const actionOptions = [ 'Freeze Account', 'Reverse Transaction', 'Block/Restrict Account Access', 'Investigation' ];
const paymentModeOptions = [ 'UPI', 'Net Banking / Internet Banking', 'Credit Card', 'Debit Card', 'Digital Wallets / Mobile Wallets', 'Cheque', 'IMPS', 'NEFT', 'RTGS', 'AEPS', 'POS Terminals' ];

// --- The Rules Engine ---
// Defines which fields are NOT required for a given payment mode.
const nonMandatoryRules = {
  'UPI': ['cardNumber', 'toAccount', 'ifsc'],
  'Net Banking / Internet Banking': ['cardNumber', 'toUpiId'],
  'Credit Card': ['accountNumber', 'toUpiId'],
  'Debit Card': ['toUpiId'],
  'Digital Wallets / Mobile Wallets': ['accountNumber', 'toUpiId'],
  'Cheque': ['toUpiId'],
  'IMPS': ['cardNumber', 'toUpiId'],
  'NEFT': ['cardNumber', 'toUpiId'],
  'RTGS': ['cardNumber', 'toUpiId'],
  'AEPS': ['cardNumber', 'toUpiId'],
  'POS Terminals': ['accountNumber', 'toBank', 'toUpiId', 'toAccount', 'ifsc']
};

const fileInputRef = ref(null); // Reference to the file input element

const form = reactive({
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
  transactionAmount: null,
  disputedAmount: null,
  action: '',
  toBank: '',
  toAccount: '',
  ifsc: '',
  toTransactionId: '',
  toUpiId: '',
  toAmount: null,
  actionTakenDate: '',
  lienAmount: null,
  evidence: null,      // will hold the file object
  evidenceName: '',    // for display only
  additionalInfo: ''
});

// --- Dynamic Validation Function ---
// This function checks the rules to see if a field is required.
function isFieldRequired(fieldName) {
  const mode = form.paymentMode;
  if (!mode) return true; // If no mode is selected, all fields are required by default

  const rulesForMode = nonMandatoryRules[mode];
  if (rulesForMode && rulesForMode.includes(fieldName)) {
    return false; // The field is listed as non-mandatory for this mode
  }
  
  return true; // Otherwise, the field is required
}

// --- UPDATED FILE CHANGE HANDLER ---
function onFileChange(e) {
  const file = e.target.files[0];
  if (!file) {
    form.evidence = null;
    form.evidenceName = '';
    return;
  }

  const MAX_FILE_SIZE_MB = 4;
  if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
    alert(`File size cannot exceed ${MAX_FILE_SIZE_MB}MB. Please choose a smaller file.`);
    // Reset the file input
    if (fileInputRef.value) {
      fileInputRef.value.value = '';
    }
    form.evidence = null;
    form.evidenceName = '';
    return;
  }

  form.evidence = file;
  form.evidenceName = file.name;
}

// --- UPDATED SUBMIT HANDLER ---
const onSubmit = async () => {
  // Create FormData to handle file upload
  const formData = new FormData();
  
  // Append all form fields to formData
  for (const key in form) {
    if (key !== 'evidence' && form[key] !== null && form[key] !== '') {
      formData.append(key, form[key]);
    }
  }

  // Append the file if it exists
  if (form.evidence) {
    formData.append('evidence', form.evidence, form.evidenceName);
  }

  try {
    // Axios will automatically set the correct 'multipart/form-data' header
    await axios.post(
      'http://34.47.219.225:9000/api/case-entry',
      formData
    );
    alert('Case submitted successfully.');
    onReset();
  } catch (error) {
    alert('Failed to submit case. Check console for details.');
    console.error('Submission error:', error.response?.data || error.message);
  }
};

const onReset = () => {
  for (const key in form) {
    // Reset based on type to avoid issues
    const fieldType = typeof form[key];
    if (fieldType === 'number') {
      form[key] = null;
    } else if (fieldType === 'object' && form[key] !== null) {
      // Handles the file object
      form[key] = null;
    } else {
      form[key] = '';
    }
  }
  // Also reset the file input element itself
  if (fileInputRef.value) {
      fileInputRef.value.value = '';
  }
};
</script>