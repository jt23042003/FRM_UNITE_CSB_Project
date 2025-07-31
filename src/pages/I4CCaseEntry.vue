<template>
  <div class="i4c-form-container">
    <div class="progress-container">
      <div class="step-indicators">
        <div 
          v-for="step in 4" 
          :key="step"
          class="step-indicator"
          :class="{ 
            'active': step === currentStep,
            'completed': step < currentStep 
          }"
        >
          <div class="step-number">
            <i v-if="step < currentStep" class="fa fa-check"></i>
            <span v-else>{{ step }}</span>
          </div>
          <span class="step-title">{{ getStepTitle(step) }}</span>
        </div>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${((currentStep - 1) / 3) * 100}%` }"></div>
      </div>
    </div>

    <div class="form-wrapper">
      <div v-if="generalError" class="error-banner">
        <i class="fa fa-exclamation-triangle"></i>
        <span>{{ generalError }}</span>
      </div>

      <div v-if="currentStep === 1" class="step-content">
        <div class="step-header">
          <h2>Basic Information</h2>
          <p>Enter complaint and customer details.</p>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">Acknowledgement No. <span class="required">*</span></label>
            <input v-model="form.ackNo" type="text" class="form-input" :class="{ 'error': errors.ackNo }" placeholder="e.g., ACK202506120001" />
            <span v-if="errors.ackNo" class="error-text">{{ errors.ackNo }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Customer Name <span class="required">*</span></label>
            <input v-model="form.customerName" type="text" class="form-input" :class="{ 'error': errors.customerName }" placeholder="Enter customer name" />
            <span v-if="errors.customerName" class="error-text">{{ errors.customerName }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Complaint Category <span class="required">*</span></label>
            <select v-model="form.subCategory" class="form-select" :class="{ 'error': errors.subCategory }">
              <option value="">Select complaint category</option>
              <option v-for="option in subCategoryOptions" :key="option" :value="option">{{ option }}</option>
            </select>
            <span v-if="errors.subCategory" class="error-text">{{ errors.subCategory }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Complaint Date <span class="required">*</span></label>
            <input v-model="form.complaintDate" type="date" class="form-input" :class="{ 'error': errors.complaintDate }" :max="currentDate" />
            <span v-if="errors.complaintDate" class="error-text">{{ errors.complaintDate }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Date & Time of Reporting <span class="required">*</span></label>
            <input v-model="form.reportDateTime" type="datetime-local" class="form-input" :class="{ 'error': errors.reportDateTime }" :max="currentDateTime" />
            <span v-if="errors.reportDateTime" class="error-text">{{ errors.reportDateTime }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">State <span class="required">*</span></label>
            <select v-model="form.state" class="form-select" :class="{ 'error': errors.state }">
              <option value="">Select state</option>
              <option v-for="st in stateOptions" :key="st" :value="st">{{ st }}</option>
            </select>
            <span v-if="errors.state" class="error-text">{{ errors.state }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">District <span class="required">*</span></label>
            <select v-model="form.district" class="form-select" :class="{ 'error': errors.district }">
              <option value="">Select district</option>
              <option v-for="districtName in districtOptions" :key="districtName" :value="districtName">{{ districtName }}</option>
            </select>
            <span v-if="errors.district" class="error-text">{{ errors.district }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Police Station <span class="required">*</span></label>
            <input v-model="form.policestation" type="text" class="form-input" :class="{ 'error': errors.policestation }" placeholder="Enter police station name" />
            <span v-if="errors.policestation" class="error-text">{{ errors.policestation }}</span>
          </div>
        </div>
      </div>

      <div v-if="currentStep === 2" class="step-content">
        <div class="step-header">
          <h2>Transaction Details</h2>
          <p>Enter payment and transaction information.</p>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">Mode of Payment <span class="required">*</span></label>
            <select v-model="form.paymentMode" class="form-select" :class="{ 'error': errors.paymentMode }" @change="clearDynamicErrors">
              <option value="">Select payment mode</option>
              <option v-for="mode in paymentModeOptions" :key="mode" :value="mode">{{ mode }}</option>
            </select>
            <span v-if="errors.paymentMode" class="error-text">{{ errors.paymentMode }}</span>
          </div>
           <div class="form-group">
            <label class="form-label">Transaction Date <span class="required">*</span></label>
            <input v-model="form.transactionDate" type="date" class="form-input" :class="{ 'error': errors.transactionDate }" :max="currentDate" />
            <span v-if="errors.transactionDate" class="error-text">{{ errors.transactionDate }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Transaction ID / UTR Number <span class="required">*</span></label>
            <input v-model="form.transactionId" type="text" class="form-input" :class="{ 'error': errors.transactionId }" placeholder="e.g., TXN987654321" />
            <span v-if="errors.transactionId" class="error-text">{{ errors.transactionId }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Victim Account Number <span v-if="isFieldRequired('accountNumber')" class="required">*</span></label>
            <input v-model="form.accountNumber" type="number" class="form-input" :class="{ 'error': errors.accountNumber }" placeholder="Enter account number" :required="isFieldRequired('accountNumber')" minlength="9" maxlength="18" />
            <span v-if="errors.accountNumber" class="error-text">{{ errors.accountNumber }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Victim Card Number <span v-if="isFieldRequired('cardNumber')" class="required">*</span></label>
            <input v-model="form.cardNumber" type="number" class="form-input" :class="{ 'error': errors.cardNumber }" placeholder="Enter card number" :required="isFieldRequired('cardNumber')" minlength="12" maxlength="19" />
            <span v-if="errors.cardNumber" class="error-text">{{ errors.cardNumber }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Layers <span class="required">*</span></label>
            <select v-model="form.layers" class="form-select" :class="{ 'error': errors.layers }">
              <option value="">Select layer</option>
              <option v-for="n in 30" :key="n" :value="`Layer ${n}`">Layer {{ n }}</option>
            </select>
            <span v-if="errors.layers" class="error-text">{{ errors.layers }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Transaction Amount <span class="required">*</span></label>
            <div class="amount-input-wrapper">
              <span class="currency-symbol">₹</span>
              <input v-model.number="form.transactionAmount" type="number" class="form-input amount-input" :class="{ 'error': errors.transactionAmount }" placeholder="0.00" min="0" step="any" />
            </div>
            <span v-if="errors.transactionAmount" class="error-text">{{ errors.transactionAmount }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Disputed Amount <span class="required">*</span></label>
            <div class="amount-input-wrapper">
              <span class="currency-symbol">₹</span>
              <input v-model.number="form.disputedAmount" type="number" class="form-input amount-input" :class="{ 'error': errors.disputedAmount }" placeholder="0.00" min="0" step="any" />
            </div>
            <span v-if="errors.disputedAmount" class="error-text">{{ errors.disputedAmount }}</span>
          </div>
        </div>
      </div>

      <div v-if="currentStep === 3" class="step-content">
        <div class="step-header">
          <h2>Beneficiary Details</h2>
          <p>Enter recipient bank and account information.</p>
        </div>
        <div class="form-grid">
          <div class="form-group full-width">
            <label class="form-label">Beneficiary Bank Details <span class="required">*</span></label>
            <div class="autocomplete-container">
              <input v-model="form.toBank" type="text" class="form-input" :class="{ 'error': errors.toBank }" placeholder="Start typing bank name..." @focus="onBankInputFocus" @blur="onBankInputBlur" @keydown="onBankInputKeydown" />
              <ul v-if="showBankSuggestions && bankSuggestions.length > 0" class="suggestions-list">
                <li v-for="(suggestion, index) in bankSuggestions" :key="index" :class="{ 'active': index === activeSuggestionIndex }" @mousedown.prevent="selectSuggestion(suggestion)">
                  {{ suggestion }}
                </li>
              </ul>
            </div>
            <span v-if="errors.toBank" class="error-text">{{ errors.toBank }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Beneficiary Account Number <span v-if="isFieldRequired('toAccount')" class="required">*</span></label>
            <input v-model="form.toAccount" type="number" class="form-input" :class="{ 'error': errors.toAccount }" placeholder="Enter account number" :required="isFieldRequired('toAccount')" />
            <span v-if="errors.toAccount" class="error-text">{{ errors.toAccount }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">IFSC Code <span v-if="isFieldRequired('ifsc')" class="required">*</span></label>
            <input v-model="form.ifsc" type="text" class="form-input" :class="{ 'error': errors.ifsc }" placeholder="e.g., ICIC0000001" :required="isFieldRequired('ifsc')" :disabled="!form.toBank" />
            <span v-if="errors.ifsc" class="error-text">{{ errors.ifsc }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Beneficiary Transaction ID <span class="required">*</span></label>
            <input v-model="form.toTransactionId" type="text" class="form-input" :class="{ 'error': errors.toTransactionId }" placeholder="e.g., TXN765432109" />
            <span v-if="errors.toTransactionId" class="error-text">{{ errors.toTransactionId }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Transaction Amount <span class="required">*</span></label>
            <div class="amount-input-wrapper">
              <span class="currency-symbol">₹</span>
              <input v-model.number="form.toAmount" type="number" class="form-input amount-input" :class="{ 'error': errors.toAmount }" placeholder="0.00" min="0" step="any" />
            </div>
            <span v-if="errors.toAmount" class="error-text">{{ errors.toAmount }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">UPI ID <span v-if="isFieldRequired('toUpiId')" class="required">*</span></label>
            <input v-model="form.toUpiId" type="text" class="form-input" :class="{ 'error': errors.toUpiId }" placeholder="e.g., user@upi" :required="isFieldRequired('toUpiId')" />
            <span v-if="errors.toUpiId" class="error-text">{{ errors.toUpiId }}</span>
          </div>
        </div>
      </div>

      <div v-if="currentStep === 4" class="step-content">
        <div class="step-header">
          <h2>Action Details</h2>
          <p>Enter action taken and follow-up information.</p>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">Action</label>
            <select v-model="form.action" class="form-select" :class="{ 'error': errors.action }">
              <option value="">Select action</option>
              <option v-for="opt in actionOptions" :key="opt" :value="opt">{{ opt }}</option>
            </select>
            <span v-if="errors.action" class="error-text">{{ errors.action }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">Action Taken Date <span class="required">*</span></label>
            <input v-model="form.actionTakenDate" type="date" class="form-input" :class="{ 'error': errors.actionTakenDate }" :max="currentDate" />
            <span v-if="errors.actionTakenDate" class="error-text">{{ errors.actionTakenDate }}</span>
          </div>
        </div>
      </div>

      <div class="form-navigation">
        <button v-if="currentStep > 1" type="button" class="nav-button prev" @click="previousStep">
          <i class="fa fa-arrow-left"></i> Previous
        </button>
         <button v-else type="button" class="nav-button prev" @click="onReset">
            <i class="fa fa-refresh"></i> Reset
        </button>
        <button v-if="currentStep < 4" type="button" class="nav-button next" @click="nextStep">
          Next <i class="fa fa-arrow-right"></i>
        </button>
        <button v-if="currentStep === 4" type="button" class="nav-button submit" @click="onSubmit">
          <i class="fa fa-paper-plane"></i> Submit Case
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch, onMounted } from 'vue';
import axios from 'axios';
import { banks } from '../data/bank.js';

// --- Multi-Step Form State ---
const currentStep = ref(1);

// Maps a form field to the step it appears on. Crucial for error navigation.
const fieldToStepMap = {
    // Step 1
    ackNo: 1, customerName: 1, subCategory: 1, complaintDate: 1, reportDateTime: 1, state: 1, district: 1, policestation: 1,
    // Step 2
    paymentMode: 2, transactionDate: 2, transactionId: 2, accountNumber: 2, cardNumber: 2, layers: 2, transactionAmount: 2, disputedAmount: 2,
    // Step 3
    toBank: 3, toAccount: 3, ifsc: 3, toTransactionId: 3, toAmount: 3, toUpiId: 3,
    // Step 4
    action: 4, actionTakenDate: 4,
};


// --- Dropdown Options ---
const subCategoryOptions = [ 'Online Scams', 'Phishing', 'Unauthorized Transactions', 'Credit/Debit Card Fraud', 'UPI/Wallet Frauds', 'SIM Swap Fraud', 'Vishing (Voice Phishing)', 'Smishing (SMS Phishing)', 'Fake Banking Websites/Apps', 'Online Payment Gateway Frauds', 'KYC Update Frauds', 'Loan App Frauds', 'Others' ];
const actionOptions = [ 'Freeze Account', 'Reverse Transaction', 'Block/Restrict Account Access', 'Investigation','others' ];
const paymentModeOptions = [ 'UPI', 'Net Banking / Internet Banking', 'Credit Card', 'Debit Card', 'Digital Wallets / Mobile Wallets', 'Cheque', 'IMPS', 'NEFT', 'RTGS', 'AEPS', 'POS Terminals' ];

// --- Dynamic Data Refs ---
const stateOptions = ref([]);
const districtOptions = ref([]);
const allDistricts = ref([]);

// --- API Endpoints ---
const STATES_API_URL = 'https://api.data.gov.in/resource/a71e60f0-a21d-43de-a6c5-fa5d21600cdb?api-key=579b464db66ec23bdd000001cdc3b564546246a772a26393094f5645&offset=0&limit=all&format=json';
const DISTRICTS_API_URL = 'https://api.data.gov.in/resource/37231365-78ba-44d5-ac22-3deec40b9197?api-key=579b464db66ec23bdd000001cdc3b564546246a772a26393094f5645&offset=0&limit=all&format=json';
const IFSC_VALIDATION_API_BASE_URL = 'https://ifsc.razorpay.com/';

// --- Bank Autocomplete Refs ---
const allBanks = ref([]);
const bankSuggestions = ref([]);
const showBankSuggestions = ref(false);
const activeSuggestionIndex = ref(-1);

// --- Rules Engine for Dynamic Fields ---
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
  'POS Terminals': ['accountNumber', 'toBank', 'toUpiId', 'toAccount', 'ifsc'],
  'exception':[]
};

// --- Form State & Errors ---
const form = reactive({
  ackNo: '', customerName: '', subCategory: '', transactionDate: '', complaintDate: '',
  reportDateTime: '', state: '', district: '', policestation: '', paymentMode: '',
  accountNumber: '', cardNumber: '', transactionId: '', layers: '', transactionAmount: null,
  disputedAmount: null, action: '', toBank: '', toAccount: '', ifsc: '',
  toTransactionId: '', toUpiId: '', toAmount: null, actionTakenDate: '',
});

const errors = reactive({});
const generalError = ref('');

// --- Computed Properties for Dates ---
const currentDate = computed(() => {
  const today = new Date();
  return today.toISOString().split('T')[0];
});

const currentDateTime = computed(() => {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
});

// --- Step Navigation Logic ---
const getStepTitle = (step) => {
  const titles = { 1: 'Basic Info', 2: 'Transaction', 3: 'Beneficiary', 4: 'Action' };
  return titles[step] || '';
};

const nextStep = () => {
  if (currentStep.value < 4) currentStep.value++;
};

const previousStep = () => {
  if (currentStep.value > 1) currentStep.value--;
};

// --- Data Fetching & Initialization ---
onMounted(async () => {
  try {
    const [stateResponse, districtResponse] = await Promise.all([
      axios.get(STATES_API_URL),
      axios.get(DISTRICTS_API_URL)
    ]);

    if (stateResponse.data?.records) {
      stateOptions.value = stateResponse.data.records
        .map(r => r.state_name_english)
        .sort((a, b) => a.localeCompare(b));
    }
    if (districtResponse.data?.records) {
      allDistricts.value = districtResponse.data.records;
    }
    allBanks.value = Object.values(banks);
  } catch (error) {
    console.error('Error fetching initial data:', error);
    generalError.value = 'Failed to load location data. Please try again later.';
    // Fallback data
    stateOptions.value = [ 'Andaman And Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chandigarh', 'Chhattisgarh', 'Delhi', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jammu And Kashmir', 'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Puducherry', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'The Dadra And Nagar Haveli And Daman And Diu', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal' ].sort();
  }
});

// --- Watchers for Dynamic Behavior ---
watch(() => form.state, (newState) => {
  form.district = '';
  districtOptions.value = newState ? allDistricts.value
    .filter(d => d.state_name_english === newState)
    .map(d => d.district_name_english)
    .sort((a, b) => a.localeCompare(b)) : [];
});

watch(() => form.toBank, (newBankInput) => {
  activeSuggestionIndex.value = -1;
  if (newBankInput && newBankInput.length > 2) {
    const query = newBankInput.toLowerCase();
    bankSuggestions.value = allBanks.value
      .filter(bank => bank.toLowerCase().includes(query))
      .slice(0, 7);
    showBankSuggestions.value = bankSuggestions.value.length > 0;
  } else {
    showBankSuggestions.value = false;
  }
});

// Clear errors on input
Object.keys(form).forEach(key => {
  watch(() => form[key], () => {
    if (errors[key]) errors[key] = '';
    if (generalError.value) generalError.value = '';
  });
});

// --- Autocomplete Handlers ---
const selectSuggestion = (suggestion) => {
  form.toBank = suggestion;
  showBankSuggestions.value = false;
};
const onBankInputFocus = () => {
  if (form.toBank && form.toBank.length > 2) showBankSuggestions.value = true;
};
const onBankInputBlur = () => setTimeout(() => { showBankSuggestions.value = false; }, 150);
const onBankInputKeydown = (e) => {
  if (!showBankSuggestions.value || bankSuggestions.value.length === 0) return;
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    activeSuggestionIndex.value = (activeSuggestionIndex.value + 1) % bankSuggestions.value.length;
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    activeSuggestionIndex.value = (activeSuggestionIndex.value - 1 + bankSuggestions.value.length) % bankSuggestions.value.length;
  } else if (e.key === 'Enter' && activeSuggestionIndex.value > -1) {
    e.preventDefault();
    selectSuggestion(bankSuggestions.value[activeSuggestionIndex.value]);
  } else if (e.key === 'Escape') {
    showBankSuggestions.value = false;
  }
};

// --- Validation and Submission Logic ---
function isFieldRequired(fieldName) {
  if (fieldName === 'action') return false;
  const alwaysRequired = ['ackNo', 'customerName', 'subCategory', 'transactionDate', 'complaintDate', 'reportDateTime', 'state', 'district', 'policestation', 'paymentMode', 'transactionId', 'layers', 'transactionAmount', 'disputedAmount', 'toTransactionId', 'toAmount', 'actionTakenDate', 'toBank'];
  if (alwaysRequired.includes(fieldName)) return true;

  const mode = form.paymentMode;
  if (!mode) return true;

  const rulesForMode = nonMandatoryRules[mode] || nonMandatoryRules['exception'];
  return !rulesForMode.includes(fieldName);
}

const clearDynamicErrors = () => {
  const dynamicFields = ['accountNumber', 'cardNumber', 'toAccount', 'ifsc', 'toUpiId'];
  dynamicFields.forEach(field => {
    if (!isFieldRequired(field) && errors[field]) errors[field] = '';
  });
};

function parseBackendErrors(errorResponse) {
  Object.keys(errors).forEach(key => delete errors[key]);
  generalError.value = '';

  if (errorResponse?.detail?.error_code) {
    const detail = errorResponse.detail;
    generalError.value = detail.message || 'An unexpected error occurred.';
    if (Array.isArray(detail.validation_errors)) {
      detail.validation_errors.forEach(err => {
        if (err.loc && err.loc.length > 1) {
          errors[err.loc[1]] = err.msg.charAt(0).toUpperCase() + err.msg.slice(1);
        }
      });
    }
  } else if (typeof errorResponse?.detail === 'string') {
    generalError.value = errorResponse.detail;
  } else {
    generalError.value = 'An unexpected error occurred. Please try again.';
  }
}

const onSubmit = async () => {
  Object.keys(errors).forEach(key => delete errors[key]);
  generalError.value = '';
  let hasClientSideError = false;

  // --- Run ALL validations ---
  if (!form.ackNo) { errors.ackNo = 'Acknowledgement No. is required.'; hasClientSideError = true; }
  if (!form.customerName) { errors.customerName = 'Customer Name is required.'; hasClientSideError = true; }
  if (!form.subCategory) { errors.subCategory = 'Complaint Category is required.'; hasClientSideError = true; }
  if (!form.transactionDate) { errors.transactionDate = 'Transaction Date is required.'; hasClientSideError = true; }
  if (!form.complaintDate) { errors.complaintDate = 'Complaint Date is required.'; hasClientSideError = true; }
  if (!form.reportDateTime) { errors.reportDateTime = 'Reporting Date is required.'; hasClientSideError = true; }
  if (!form.state) { errors.state = 'State is required.'; hasClientSideError = true; }
  if (!form.district) { errors.district = 'District is required.'; hasClientSideError = true; }
  if (!form.policestation) { errors.policestation = 'Police Station is required.'; hasClientSideError = true; }
  if (!form.paymentMode) { errors.paymentMode = 'Mode of Payment is required.'; hasClientSideError = true; }
  if (!form.transactionId) { errors.transactionId = 'Transaction ID is required.'; hasClientSideError = true; }
  if (!form.layers) { errors.layers = 'Layers is required.'; hasClientSideError = true; }
  if (form.transactionAmount == null) { errors.transactionAmount = 'Transaction Amount is required.'; hasClientSideError = true; }
  if (form.disputedAmount == null) { errors.disputedAmount = 'Disputed Amount is required.'; hasClientSideError = true; }
  if (!form.toBank) { errors.toBank = 'Beneficiary Bank is required.'; hasClientSideError = true; }
  if (!form.toTransactionId) { errors.toTransactionId = 'Beneficiary Transaction ID is required.'; hasClientSideError = true; }
  if (form.toAmount == null) { errors.toAmount = 'Beneficiary Amount is required.'; hasClientSideError = true; }
  if (!form.actionTakenDate) { errors.actionTakenDate = 'Action Taken Date is required.'; hasClientSideError = true; }
  
  // Dynamic fields
  ['accountNumber', 'cardNumber', 'toAccount', 'ifsc', 'toUpiId'].forEach(field => {
      if (isFieldRequired(field) && !form[field]) {
          const name = {accountNumber: 'Victim Account Number', cardNumber: 'Victim Card Number', toAccount: 'Beneficiary Account Number', ifsc: 'IFSC Code', toUpiId: 'UPI ID'}[field];
          errors[field] = `${name} is required for this payment mode.`;
          hasClientSideError = true;
      }
  });

  // Specific format validations
  if (isFieldRequired('toUpiId') && form.toUpiId && !form.toUpiId.includes('@')) {
      errors.toUpiId = 'UPI ID must contain an "@" symbol.';
      hasClientSideError = true;
  }
  // Add other specific validations (account length, etc.) here if needed.

  // --- THIS IS THE FIX ---
  // If any error was found, navigate to the step with the first error.
  if (hasClientSideError) {
    const firstErrorField = Object.keys(errors).find(key => errors[key]);
    if (firstErrorField && fieldToStepMap[firstErrorField]) {
      currentStep.value = fieldToStepMap[firstErrorField];
    }
    generalError.value = 'Please correct the highlighted errors before submitting.';
    return;
  }

  // --- Proceed with submission ---
  const formData = new FormData();
  Object.keys(form).forEach(key => {
    formData.append(key, form[key] ?? '');
  });

  try {
    await axios.post('http://34.47.219.225:9000/api/case-entry', formData);
    alert('Case submitted successfully.');
    onReset();
  } catch (error) {
    console.error('Submission error:', error.response?.data || error.message);
    if (error.response?.data) {
      parseBackendErrors(error.response.data);
      // Also navigate to the correct step for backend errors
      const firstErrorField = Object.keys(errors).find(key => errors[key]);
      if (firstErrorField && fieldToStepMap[firstErrorField]) {
          currentStep.value = fieldToStepMap[firstErrorField];
      }
    } else {
      generalError.value = 'Failed to submit case. Network error or server unreachable.';
    }
  }
};

const onReset = () => {
  Object.keys(form).forEach(key => {
    form[key] = typeof form[key] === 'number' ? null : '';
  });
  Object.keys(errors).forEach(key => delete errors[key]);
  
  districtOptions.value = [];
  bankSuggestions.value = [];
  showBankSuggestions.value = false;
  activeSuggestionIndex.value = -1;
  generalError.value = '';
  
  // Reset to the first step
  currentStep.value = 1;
};
</script>


<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Main Container */
.i4c-form-container {
  height: 100vh;
  width: 100%;
  background: #f4f7f9;
  font-family: 'Inter', sans-serif;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Progress Bar */
.progress-container {
  background: #ffffff;
  border-bottom: 1px solid #e9ecef;
  z-index: 100;
  padding: 1rem 3rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  box-sizing: border-box;
}

.step-indicators {
  display: flex;
  gap: 2.5rem;
  align-items: center;
}

.step-indicator {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  opacity: 0.6;
  transition: opacity 0.3s ease;
  position: relative;
}

.step-indicator:not(:last-child)::after {
    content: '';
    position: absolute;
    left: 100%;
    top: 50%;
    transform: translateY(-50%);
    width: 2rem; 
    height: 2px;
    background: #dee2e6;
    margin-left: 0.75rem;
}

.step-indicator.active, .step-indicator.completed {
  opacity: 1;
}

.step-indicator.completed:not(:last-child)::after {
    background: #007bff;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e9ecef;
  color: #495057;
  border: 2px solid #e9ecef;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.step-indicator.active .step-number {
  background: #fff;
  border-color: #007bff;
  color: #007bff;
}

.step-indicator.completed .step-number {
  background: #007bff;
  border-color: #007bff;
  color: white;
}

.step-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: #495057;
}

.step-indicator.active .step-title {
  font-weight: 600;
  color: #212529;
}

.progress-bar {
    display: none; /* Removed in favor of connector lines */
}

/* Form Wrapper */
.form-wrapper {
  flex-grow: 1;
  padding: 2rem 3rem;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
}

.error-banner {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  padding: 1rem 1.5rem;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #721c24;
  font-weight: 500;
  animation: fadeIn 0.3s ease;
}

/* Step Content */
.step-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding-right: 1rem;
  animation: fadeInUp 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Step Header */
.step-header {
  margin-bottom: 2rem;
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 1rem;
}
.step-header h2 {
  font-size: 1.75rem;
  font-weight: 600;
  color: #212529;
}
.step-header p {
  color: #6c757d;
  font-size: 1rem;
  margin-top: 0.25rem;
}

/* Form Elements */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem 2rem;
  padding-bottom: 2rem;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.form-group.full-width {
  grid-column: 1 / -1;
}
.form-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #495057;
}
.required {
  color: #dc3545;
  margin-left: 2px;
}
.form-input, .form-select {
  width: 100%;
  padding: 0.65rem 1rem;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: all 0.2s ease-in-out;
  background-color: #fff;
  color: #495057;
  height: 42px;
}
.form-input:focus, .form-select:focus {
  border-color: #80bdff;
  outline: 0;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}
.form-input.error, .form-select.error {
  border-color: #dc3545;
}
.form-input.error:focus, .form-select.error:focus {
  box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
}
.error-text {
  color: #dc3545;
  font-size: 0.85rem;
}

/* Amount Input */
.amount-input-wrapper {
  position: relative;
}
.currency-symbol {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #6c757d;
}
.amount-input {
  padding-left: 2.2rem;
}

/* Autocomplete */
.autocomplete-container {
  position: relative;
}
.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
  background: white;
  border: 1px solid #ced4da;
  border-top: none;
  border-radius: 0 0 6px 6px;
  max-height: 220px;
  overflow-y: auto;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  list-style: none;
  padding: 0.25rem 0;
  margin: 0;
}
.suggestions-list li {
  padding: 0.75rem 1rem;
  cursor: pointer;
  color: #495057;
  transition: all 0.2s ease;
}
.suggestions-list li:hover, .suggestions-list li.active {
  background: #007bff;
  color: white;
}

/* Navigation */
.form-navigation {
  display: flex;
  justify-content: space-between;
  padding: 1.5rem 0 0;
  margin-top: auto;
  border-top: 1px solid #e9ecef;
}

.nav-button {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 120px;
  justify-content: center;
  border: 1px solid transparent;
}
.nav-button.prev {
  background: #fff;
  color: #495057;
  border-color: #ced4da;
}
.nav-button.prev:hover {
  background-color: #f8f9fa;
}
.nav-button.next, .nav-button.submit {
  background: #007bff;
  color: #fff;
}
.nav-button.next:hover, .nav-button.submit:hover {
  background: #0056b3;
}
</style>