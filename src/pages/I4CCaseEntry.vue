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
      <div v-if="initLoading" class="skeleton-table" style="margin-bottom: 14px;">
        <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
        <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
        <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
      </div>
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
const initLoading = ref(true);

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
  finally {
    initLoading.value = false;
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

// Real-time validation for better UX
const validateFieldInRealTime = (fieldName, value) => {
  // Clear existing error first
  if (errors[fieldName]) errors[fieldName] = '';
  
  // Skip validation if field is empty (will be caught on submit)
  if (!value || value === '') return;
  
  let error = null;
  
  switch (fieldName) {
    case 'ackNo':
      error = validateAckNo(value);
      break;
    case 'customerName':
      error = validateCustomerName(value);
      break;
    case 'transactionId':
      error = validateTransactionId(value);
      break;
    case 'accountNumber':
      if (isFieldRequired('accountNumber')) {
        error = validateAccountNumber(value);
      }
      break;
    case 'cardNumber':
      if (isFieldRequired('cardNumber')) {
        error = validateCardNumber(value);
      }
      break;
    case 'ifsc':
      if (isFieldRequired('ifsc')) {
        error = validateIFSC(value);
      }
      break;
    case 'toUpiId':
      if (isFieldRequired('toUpiId')) {
        error = validateUPIId(value);
      }
      break;
    case 'toAccount':
      if (isFieldRequired('toAccount')) {
        error = validateAccountNumber(value);
      }
      break;
    case 'policestation':
      error = validatePoliceStation(value);
      break;
    case 'toBank':
      error = validateBeneficiaryBank(value);
      break;
    case 'transactionAmount':
      error = validateAmount(value, 'Transaction Amount');
      break;
    case 'disputedAmount':
      error = validateAmount(value, 'Disputed Amount');
      break;
    case 'toAmount':
      error = validateAmount(value, 'Beneficiary Transaction Amount');
      break;
    case 'complaintDate':
      error = validateDate(value, 'Complaint Date', currentDate.value);
      break;
    case 'transactionDate':
      error = validateDate(value, 'Transaction Date', currentDate.value);
      break;
    case 'reportDateTime':
      error = validateDateTime(value, 'Date & Time of Reporting');
      break;
    case 'actionTakenDate':
      error = validateDate(value, 'Action Taken Date', currentDate.value);
      break;
  }
  
  if (error) {
    errors[fieldName] = error;
  }
};

// Enhanced watchers with real-time validation
Object.keys(form).forEach(key => {
  watch(() => form[key], (newValue) => {
    // Clear general error when user starts typing
    if (generalError.value) generalError.value = '';
    
    // Clear existing error for this field
    if (errors[key]) errors[key] = '';
    
    // Apply real-time validation for specific fields
    validateFieldInRealTime(key, newValue);
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

// Enhanced validation functions
const validateAckNo = (value) => {
  if (!value) return 'Acknowledgement No. is required.';
  
  const ackNo = value.trim();
  
  // Length validation
  if (ackNo.length < 8) return 'Acknowledgement No. must be at least 8 characters long.';
  if (ackNo.length > 50) return 'Acknowledgement No. must not exceed 50 characters.';
  
  // Format validation - allow common acknowledgement number characters
  if (!/^[A-Z0-9_-]+$/i.test(ackNo)) {
    return 'Acknowledgement No. can only contain letters, numbers, hyphens, and underscores.';
  }
  
  // Check for common patterns
  const commonPatterns = [
    /^ACK\d{8,12}$/i,      // ACK202506120001
    /^REF\d{8,12}$/i,      // REF202506120001
    /^CASE\d{8,12}$/i,     // CASE202506120001
    /^COMP\d{8,12}$/i,     // COMP202506120001
    /^FRAUD\d{8,12}$/i,    // FRAUD202506120001
    /^I4C\d{8,12}$/i,      // I4C202506120001
    /^\d{8,16}$/,          // Pure numeric IDs
    /^[A-Z]{2,4}\d{8,12}$/i, // ICIC202506120001, HDFC202506120001
    /^[A-Z0-9]{8,20}$/i   // Alphanumeric IDs
  ];
  
  const isValidPattern = commonPatterns.some(pattern => pattern.test(ackNo));
  if (!isValidPattern) {
    // Not a strict error, just a suggestion
    console.log(`Acknowledgement No. ${ackNo} doesn't match common patterns - may be valid`);
  }
  
  // Additional checks
  if (ackNo.startsWith('-') || ackNo.endsWith('-') || ackNo.startsWith('_') || ackNo.endsWith('_')) {
    return 'Acknowledgement No. cannot start or end with hyphens or underscores.';
  }
  
  if (ackNo.includes('--') || ackNo.includes('__')) {
    return 'Acknowledgement No. cannot contain consecutive hyphens or underscores.';
  }
  
  // Check for reasonable length based on pattern
  if (ackNo.match(/^ACK\d+$/i) && ackNo.length < 12) {
    return 'ACK format numbers should be at least 12 characters long.';
  }
  
  if (ackNo.match(/^REF\d+$/i) && ackNo.length < 12) {
    return 'REF format numbers should be at least 12 characters long.';
  }
  
  if (ackNo.match(/^CASE\d+$/i) && ackNo.length < 12) {
    return 'CASE format numbers should be at least 12 characters long.';
  }
  
  // Check for date-like patterns in numeric parts
  const numericPart = ackNo.replace(/[A-Z_-]/gi, '');
  if (numericPart.length >= 8) {
    const year = numericPart.substring(0, 4);
    const month = numericPart.substring(4, 6);
    const day = numericPart.substring(6, 8);
    
    if (year >= '2020' && year <= '2030' && month >= '01' && month <= '12' && day >= '01' && day <= '31') {
      // This looks like a date - validate it's reasonable
      const date = new Date(year, month - 1, day);
      const today = new Date();
      const tenYearsAgo = new Date();
      tenYearsAgo.setFullYear(today.getFullYear() - 10);
      
      if (date > today) {
        return 'Acknowledgement No. contains a future date which is not allowed.';
      }
      
      if (date < tenYearsAgo) {
        return 'Acknowledgement No. contains a date more than 10 years old which seems unlikely.';
      }
    }
  }
  
  return null;
};

const validateCustomerName = (value) => {
  if (!value) return 'Customer Name is required.';
  
  const name = value.trim();
  
  // Length validation
  if (name.length < 2) return 'Customer Name must be at least 2 characters long.';
  if (name.length > 100) return 'Customer Name must not exceed 100 characters.';
  
  // Format validation - allow common name characters
  if (!/^[a-zA-Z\s\.'-]+$/.test(name)) {
    return 'Customer Name can only contain letters, spaces, dots, hyphens, and apostrophes.';
  }
  
  // Check for reasonable name patterns
  if (name.length < 3 && !name.includes(' ')) {
    return 'Customer Name seems too short. Please enter the full name.';
  }
  
  // Check for excessive spaces or special characters
  if (name.includes('  ')) {
    return 'Customer Name cannot contain consecutive spaces.';
  }
  
  if (name.startsWith(' ') || name.endsWith(' ')) {
    return 'Customer Name cannot start or end with spaces.';
  }
  
  if (name.startsWith('.') || name.endsWith('.') || name.startsWith('-') || name.endsWith('-')) {
    return 'Customer Name cannot start or end with dots or hyphens.';
  }
  
  if (name.startsWith("'") || name.endsWith("'")) {
    return 'Customer Name cannot start or end with apostrophes.';
  }
  
  // Check for consecutive special characters
  if (name.includes('..') || name.includes('--') || name.includes("''")) {
    return 'Customer Name cannot contain consecutive dots, hyphens, or apostrophes.';
  }
  
  // Check for reasonable name structure
  const nameParts = name.split(' ').filter(part => part.length > 0);
  if (nameParts.length < 1) {
    return 'Customer Name must contain at least one valid name part.';
  }
  
  // Check if any name part is too short (excluding initials)
  const shortParts = nameParts.filter(part => part.length === 1 && !part.match(/[A-Z]/));
  if (shortParts.length > 0) {
    return 'Customer Name parts should be at least 2 characters long (except for initials).';
  }
  
  // Check for reasonable total length
  if (name.length > 50 && nameParts.length < 3) {
    return 'Customer Name seems unusually long for the number of name parts.';
  }
  
  return null;
};

const validateTransactionId = (value) => {
  if (!value) return 'Transaction ID is required.';
  
  const txnId = value.trim();
  
  // Length validation
  if (txnId.length < 5) return 'Transaction ID must be at least 5 characters long.';
  if (txnId.length > 50) return 'Transaction ID must not exceed 50 characters.';
  
  // Format validation - allow common patterns
  if (!/^[A-Z0-9_-]+$/i.test(txnId)) {
    return 'Transaction ID can only contain letters, numbers, hyphens, and underscores.';
  }
  
  // Check for common patterns
  const commonPatterns = [
    /^TXN\d+$/i,           // TXN123456
    /^UTR\d+$/i,           // UTR123456
    /^REF\d+$/i,           // REF123456
    /^[A-Z]{2,4}\d{6,12}$/i, // ICIC123456789, HDFC123456
    /^\d{10,16}$/,         // Pure numeric IDs
    /^[A-Z0-9]{8,20}$/i   // Alphanumeric IDs
  ];
  
  const isValidPattern = commonPatterns.some(pattern => pattern.test(txnId));
  if (!isValidPattern) {
    // Not a strict error, just a suggestion
    console.log(`Transaction ID ${txnId} doesn't match common patterns - may be valid`);
  }
  
  // Additional checks
  if (txnId.startsWith('-') || txnId.endsWith('-') || txnId.startsWith('_') || txnId.endsWith('_')) {
    return 'Transaction ID cannot start or end with hyphens or underscores.';
  }
  
  if (txnId.includes('--') || txnId.includes('__')) {
    return 'Transaction ID cannot contain consecutive hyphens or underscores.';
  }
  
  // Check for reasonable length based on pattern
  if (txnId.match(/^TXN\d+$/i) && txnId.length < 8) {
    return 'TXN format IDs should be at least 8 characters long.';
  }
  
  if (txnId.match(/^UTR\d+$/i) && txnId.length < 8) {
    return 'UTR format IDs should be at least 8 characters long.';
  }
  
  return null;
};

const validateAccountNumber = (value) => {
  if (!value) return null; // Will be handled by isFieldRequired
  
  const accountNo = value.toString().trim();
  
  // Basic length validation
  if (accountNo.length < 9) return 'Account number must be at least 9 digits long.';
  if (accountNo.length > 18) return 'Account number must not exceed 18 digits.';
  
  // Format validation - only digits allowed
  if (!/^\d+$/.test(accountNo)) return 'Account number can only contain digits.';
  
  // Check for common Indian bank account number patterns
  const commonPatterns = [
    /^\d{9}$/,      // 9 digits (some cooperative banks)
    /^\d{10}$/,     // 10 digits (some private banks)
    /^\d{11}$/,     // 11 digits (some banks)
    /^\d{12}$/,     // 12 digits (most common - SBI, PNB, etc.)
    /^\d{13}$/,     // 13 digits (some banks)
    /^\d{14}$/,     // 14 digits (some banks)
    /^\d{15}$/,     // 15 digits (some banks)
    /^\d{16}$/,     // 16 digits (some banks)
    /^\d{17}$/,     // 17 digits (some banks)
    /^\d{18}$/      // 18 digits (some banks)
  ];
  
  const isValidPattern = commonPatterns.some(pattern => pattern.test(accountNo));
  if (!isValidPattern) {
    // Not a strict error, just a suggestion
    console.log(`Account number ${accountNo} doesn't match common patterns - may be valid`);
  }
  
  // Check for reasonable patterns
  if (accountNo.length === 12) {
    // Most common length for Indian banks
    if (accountNo.startsWith('0') && accountNo.length > 10) {
      return 'Account number should not start with 0 unless it\'s a valid format.';
    }
  }
  
  // Check for all zeros or all ones (suspicious)
  if (/^0+$/.test(accountNo)) {
    return 'Account number cannot be all zeros.';
  }
  
  if (/^1+$/.test(accountNo)) {
    return 'Account number cannot be all ones.';
  }
  
  // Check for sequential numbers (suspicious)
  if (/^(0123456789|1234567890|9876543210|0987654321)$/.test(accountNo)) {
    return 'Account number appears to be a sequential pattern which seems unlikely.';
  }
  
  // Check for repeated patterns (suspicious)
  if (accountNo.length >= 6) {
    const halfLength = Math.floor(accountNo.length / 2);
    const firstHalf = accountNo.substring(0, halfLength);
    const secondHalf = accountNo.substring(halfLength);
    
    if (firstHalf === secondHalf) {
      return 'Account number appears to have a repeated pattern which seems unlikely.';
    }
  }
  
  // Validate checksum for common lengths (basic validation)
  if (accountNo.length === 12) {
    // Basic checksum validation for 12-digit accounts
    let sum = 0;
    let weight = 1;
    
    for (let i = accountNo.length - 1; i >= 0; i--) {
      sum += parseInt(accountNo[i]) * weight;
      weight = weight === 1 ? 2 : 1;
    }
    
    if (sum % 10 === 0) {
      // Valid checksum - this is good
      console.log(`Account number ${accountNo} has valid checksum`);
    } else {
      // Invalid checksum - but don't reject, just log
      console.log(`Account number ${accountNo} has invalid checksum - may still be valid`);
    }
  }
  
  return null;
};

const validateCardNumber = (value) => {
  if (!value) return null; // Will be handled by isFieldRequired
  
  const cardNo = value.toString().trim();
  
  // Basic length validation
  if (cardNo.length < 12) return 'Card number must be at least 12 digits long.';
  if (cardNo.length > 19) return 'Card number must not exceed 19 digits.';
  
  // Format validation - only digits allowed
  if (!/^\d+$/.test(cardNo)) return 'Card number can only contain digits.';
  
  // Check for common card number patterns
  const commonPatterns = [
    /^\d{12}$/,     // 12 digits (some cards)
    /^\d{13}$/,     // 13 digits (some cards)
    /^\d{14}$/,     // 14 digits (some cards)
    /^\d{15}$/,     // 15 digits (some cards)
    /^\d{16}$/,     // 16 digits (most common - Visa, MasterCard, etc.)
    /^\d{17}$/,     // 17 digits (some cards)
    /^\d{18}$/,     // 18 digits (some cards)
    /^\d{19}$/      // 19 digits (some cards)
  ];
  
  const isValidPattern = commonPatterns.some(pattern => pattern.test(cardNo));
  if (!isValidPattern) {
    // Not a strict error, just a suggestion
    console.log(`Card number ${cardNo} doesn't match common patterns - may be valid`);
  }
  
  // Check for reasonable patterns
  if (cardNo.length === 16) {
    // Most common length for major card networks
    const firstDigit = parseInt(cardNo[0]);
    const firstTwoDigits = parseInt(cardNo.substring(0, 2));
    const firstFourDigits = parseInt(cardNo.substring(0, 4));
    
    // Check for common card network patterns
    if (firstDigit === 4) {
      // Visa cards start with 4
      console.log(`Card number ${cardNo} appears to be a Visa card`);
    } else if (firstTwoDigits >= 51 && firstTwoDigits <= 55) {
      // MasterCard starts with 51-55
      console.log(`Card number ${cardNo} appears to be a MasterCard`);
    } else if (firstTwoDigits === 34 || firstTwoDigits === 37) {
      // American Express starts with 34 or 37
      console.log(`Card number ${cardNo} appears to be an American Express card`);
    } else if (firstFourDigits === 6011 || (firstTwoDigits >= 64 && firstTwoDigits <= 65)) {
      // Discover starts with 6011, 64, or 65
      console.log(`Card number ${cardNo} appears to be a Discover card`);
    } else if (firstTwoDigits === 62) {
      // UnionPay starts with 62
      console.log(`Card number ${cardNo} appears to be a UnionPay card`);
    } else if (firstFourDigits >= 2200 && firstFourDigits <= 2204) {
      // MIR starts with 2200-2204
      console.log(`Card number ${cardNo} appears to be a MIR card`);
    } else {
      console.log(`Card number ${cardNo} doesn't match common card network patterns - may be valid`);
    }
  }
  
  // Check for all zeros or all ones (suspicious)
  if (/^0+$/.test(cardNo)) {
    return 'Card number cannot be all zeros.';
  }
  
  if (/^1+$/.test(cardNo)) {
    return 'Card number cannot be all ones.';
  }
  
  // Check for sequential numbers (suspicious)
  if (/^(0123456789|1234567890|9876543210|0987654321)$/.test(cardNo)) {
    return 'Card number appears to be a sequential pattern which seems unlikely.';
  }
  
  // Check for repeated patterns (suspicious)
  if (cardNo.length >= 8) {
    const halfLength = Math.floor(cardNo.length / 2);
    const firstHalf = cardNo.substring(0, halfLength);
    const secondHalf = cardNo.substring(halfLength);
    
    if (firstHalf === secondHalf) {
      return 'Card number appears to have a repeated pattern which seems unlikely.';
    }
  }
  
  // Luhn algorithm validation (checksum validation)
  if (cardNo.length >= 13) {
    let sum = 0;
    let isEven = false;
    
    // Loop through values starting from the rightmost side
    for (let i = cardNo.length - 1; i >= 0; i--) {
      let digit = parseInt(cardNo[i]);
      
      if (isEven) {
        digit *= 2;
        if (digit > 9) {
          digit -= 9;
        }
      }
      
      sum += digit;
      isEven = !isEven;
    }
    
    if (sum % 10 === 0) {
      // Valid checksum - this is good
      console.log(`Card number ${cardNo} has valid checksum (Luhn algorithm)`);
    } else {
      // Invalid checksum - this is a problem
      return 'Card number appears to be invalid (failed checksum validation).';
    }
  }
  
  return null;
};

const validateIFSC = (value) => {
  if (!value) return null; // Will be handled by isFieldRequired
  
  const ifsc = value.toUpperCase().trim();
  
  // Basic format validation
  if (!/^[A-Z]{4}0[A-Z0-9]{6}$/.test(ifsc)) {
    return 'IFSC Code must be 11 characters: 4 letters + 0 + 6 alphanumeric characters.';
  }
  
  // Check for common Indian bank patterns
  const bankCode = ifsc.substring(0, 4);
  const commonBanks = [
    'ICIC', 'HDFC', 'SBIN', 'PNBA', 'IDIB', 'BARB', 'KARB', 'UTIB', 'YESB', 'AXIS',
    'IOBA', 'UCBA', 'PSIB', 'JANA', 'KVBL', 'TJSB', 'COSB', 'KGBK', 'SVCB', 'DCBL'
  ];
  
  if (!commonBanks.includes(bankCode)) {
    // Not a warning, just informational
    console.log(`IFSC bank code ${bankCode} not in common list - may be valid`);
  }
  
  // Validate that the 5th character is '0'
  if (ifsc.charAt(4) !== '0') {
    return 'IFSC Code must have "0" as the 5th character.';
  }
  
  // Check for reasonable branch codes
  const branchCode = ifsc.substring(5);
  if (branchCode === '000000') {
    return 'IFSC Code branch part cannot be all zeros.';
  }
  
  return null;
};

const validateUPIId = (value) => {
  if (!value) return null; // Will be handled by isFieldRequired
  
  const upi = value.trim();
  
  // Basic format validation
  if (!upi.includes('@')) return 'UPI ID must contain an "@" symbol.';
  if (upi.length < 5) return 'UPI ID must be at least 5 characters long.';
  if (upi.length > 50) return 'UPI ID must not exceed 50 characters.';
  
  // Split by @ to validate parts
  const parts = upi.split('@');
  if (parts.length !== 2) return 'UPI ID must contain exactly one "@" symbol.';
  
  const [handle, provider] = parts;
  
  // Validate handle (part before @)
  if (handle.length < 3) return 'UPI handle (before @) must be at least 3 characters long.';
  if (handle.length > 30) return 'UPI handle (before @) must not exceed 30 characters.';
  if (!/^[a-zA-Z0-9._-]+$/.test(handle)) {
    return 'UPI handle can only contain letters, numbers, dots, hyphens, and underscores.';
  }
  
  // Validate provider (part after @)
  if (provider.length < 2) return 'UPI provider (after @) must be at least 2 characters long.';
  if (provider.length > 20) return 'UPI provider (after @) must not exceed 20 characters.';
  if (!/^[a-zA-Z0-9._-]+$/.test(provider)) {
    return 'UPI provider can only contain letters, numbers, dots, hyphens, and underscores.';
  }
  
  // Check for common UPI providers
  const commonProviders = [
    'okicici', 'paytm', 'phonepe', 'gpay', 'amazonpay', 'bhim', 'upi', 'bank',
    'icici', 'hdfc', 'sbi', 'axis', 'kotak', 'yes', 'idfc', 'fino', 'airtel'
  ];
  
  const providerLower = provider.toLowerCase();
  if (!commonProviders.some(p => providerLower.includes(p))) {
    // Not a warning, just informational
    console.log(`UPI provider ${provider} not in common list - may be valid`);
  }
  
  // Additional format checks
  if (upi.startsWith('.') || upi.endsWith('.') || upi.startsWith('-') || upi.endsWith('-')) {
    return 'UPI ID cannot start or end with dots or hyphens.';
  }
  
  if (upi.includes('..') || upi.includes('--') || upi.includes('__')) {
    return 'UPI ID cannot contain consecutive dots, hyphens, or underscores.';
  }
  
  return null;
};

const validateAmount = (value, fieldName) => {
  if (value === null || value === undefined || value === '') return `${fieldName} is required.`;
  
  // Convert to number and validate
  const amount = parseFloat(value);
  if (isNaN(amount)) return `${fieldName} must be a valid number.`;
  
  // Basic range validation
  if (amount < 0) return `${fieldName} must be a positive number.`;
  if (amount > 999999999.99) return `${fieldName} must not exceed ₹99,99,99,999.99`;
  if (amount < 0.01) return `${fieldName} must be at least ₹0.01`;
  
  // Check for reasonable amount limits
  if (amount > 100000000) return `${fieldName} seems unusually high. Please verify the amount.`;
  
  // Check for suspicious patterns
  if (amount === 0) return `${fieldName} cannot be zero.`;
  
  // Check for round numbers that might be suspicious
  if (amount % 1000000 === 0 && amount > 1000000) {
    console.log(`${fieldName} is a round million amount - may be valid`);
  }
  
  if (amount % 100000 === 0 && amount > 100000) {
    console.log(`${fieldName} is a round lakh amount - may be valid`);
  }
  
  // Check for common fraud amounts
  const suspiciousAmounts = [1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000];
  if (suspiciousAmounts.includes(amount)) {
    console.log(`${fieldName} is a common suspicious amount - may be valid`);
  }
  
  // Check for decimal precision
  const decimalPlaces = (amount.toString().split('.')[1] || '').length;
  if (decimalPlaces > 2) {
    return `${fieldName} cannot have more than 2 decimal places.`;
  }
  
  // Business logic validations based on field name
  if (fieldName === 'Transaction Amount') {
    if (amount > 10000000) {
      console.log(`${fieldName} is unusually high for a single transaction - may be valid`);
    }
    
    if (amount < 100) {
      console.log(`${fieldName} is unusually low for a fraud case - may be valid`);
    }
  }
  
  if (fieldName === 'Disputed Amount') {
    if (amount > 10000000) {
      console.log(`${fieldName} is unusually high for a disputed amount - may be valid`);
    }
  }
  
  if (fieldName === 'Beneficiary Transaction Amount') {
    if (amount > 10000000) {
      console.log(`${fieldName} is unusually high for a beneficiary amount - may be valid`);
    }
  }
  
  return null;
};

// Enhanced amount validation with business logic
const validateAmounts = () => {
  const errors = [];
  
  // Validate transaction amount vs disputed amount
  if (form.transactionAmount && form.disputedAmount) {
    if (form.disputedAmount > form.transactionAmount) {
      errors.push('Disputed amount cannot exceed transaction amount.');
    }
    if (form.disputedAmount < 0) {
      errors.push('Disputed amount cannot be negative.');
    }
  }
  
  // Validate beneficiary amount vs transaction amount
  if (form.transactionAmount && form.toAmount) {
    if (form.toAmount > form.transactionAmount * 1.1) {
      errors.push('Beneficiary amount seems unusually high compared to transaction amount.');
    }
  }
  
  // Validate that amounts are reasonable
  if (form.transactionAmount && form.transactionAmount > 10000000) {
    errors.push('Transaction amount seems unusually high. Please verify.');
  }
  
  return errors;
};

const validateDate = (value, fieldName, maxDate = null) => {
  if (!value) return `${fieldName} is required.`;
  
  const inputDate = new Date(value);
  const today = new Date();
  
  // Basic date validation
  if (isNaN(inputDate.getTime())) return `${fieldName} is not a valid date.`;
  
  // Check for future dates
  if (maxDate && inputDate > maxDate) {
    return `${fieldName} cannot be in the future.`;
  }
  
  // Check if date is not too old (more than 10 years)
  const tenYearsAgo = new Date();
  tenYearsAgo.setFullYear(today.getFullYear() - 10);
  if (inputDate < tenYearsAgo) {
    return `${fieldName} cannot be more than 10 years old.`;
  }
  
  // Additional business logic validations
  if (fieldName === 'Complaint Date') {
    // Complaint date should not be too far in the past for fraud cases
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    if (inputDate < oneYearAgo) {
      return `${fieldName} cannot be more than 1 year old for fraud complaints.`;
    }
  }
  
  if (fieldName === 'Transaction Date') {
    // Transaction date should not be too far in the past
    const twoYearsAgo = new Date();
    twoYearsAgo.setFullYear(today.getFullYear() - 2);
    if (inputDate < twoYearsAgo) {
      return `${fieldName} cannot be more than 2 years old.`;
    }
  }
  
  if (fieldName === 'Action Taken Date') {
    // Action taken date should not be too far in the past
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(today.getMonth() - 6);
    if (inputDate < sixMonthsAgo) {
      return `${fieldName} cannot be more than 6 months old.`;
    }
  }
  
  return null;
};

const validateDateTime = (value, fieldName) => {
  if (!value) return `${fieldName} is required.`;
  
  const inputDateTime = new Date(value);
  const now = new Date();
  
  // Basic datetime validation
  if (isNaN(inputDateTime.getTime())) return `${fieldName} is not a valid date and time.`;
  
  // Check for future datetime
  if (inputDateTime > now) {
    return `${fieldName} cannot be in the future.`;
  }
  
  // Check if datetime is not too old (more than 1 year)
  const oneYearAgo = new Date();
  oneYearAgo.setFullYear(now.getFullYear() - 1);
  if (inputDateTime < oneYearAgo) {
    return `${fieldName} cannot be more than 1 year old.`;
  }
  
  // Additional business logic validations
  if (fieldName === 'Date & Time of Reporting') {
    // Reporting datetime should not be too far in the past
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(now.getMonth() - 6);
    if (inputDateTime < sixMonthsAgo) {
      return `${fieldName} cannot be more than 6 months old.`;
    }
    
    // Check if reporting time is reasonable (not too early in the day for fraud cases)
    const hour = inputDateTime.getHours();
    if (hour < 6 && hour > 22) {
      // Not a strict error, just a suggestion
      console.log(`${fieldName} has unusual reporting time (${hour}:00) - may be valid`);
    }
  }
  
  // Check for reasonable time differences
  if (fieldName === 'Date & Time of Reporting') {
    const now = new Date();
    const timeDiff = now.getTime() - inputDateTime.getTime();
    const hoursDiff = timeDiff / (1000 * 60 * 60);
    
    if (hoursDiff < 0.1) {
      // Less than 6 minutes ago
      return `${fieldName} cannot be less than 6 minutes ago.`;
    }
    
    if (hoursDiff > 4380) {
      // More than 6 months ago
      return `${fieldName} cannot be more than 6 months ago.`;
    }
  }
  
  return null;
};

const validatePoliceStation = (value) => {
  if (!value) return 'Police Station is required.';
  
  const station = value.trim();
  
  // Length validation
  if (station.length < 3) return 'Police Station name must be at least 3 characters long.';
  if (station.length > 100) return 'Police Station name must not exceed 100 characters.';
  
  // Format validation - allow common police station name characters
  if (!/^[a-zA-Z\s\.'-]+$/.test(station)) {
    return 'Police Station name can only contain letters, spaces, dots, hyphens, and apostrophes.';
  }
  
  // Check for reasonable name patterns
  if (station.length < 5 && !station.includes(' ')) {
    return 'Police Station name seems too short. Please enter the full name.';
  }
  
  // Check for excessive spaces or special characters
  if (station.includes('  ')) {
    return 'Police Station name cannot contain consecutive spaces.';
  }
  
  if (station.startsWith(' ') || station.endsWith(' ')) {
    return 'Police Station name cannot start or end with spaces.';
  }
  
  if (station.startsWith('.') || station.endsWith('.') || station.startsWith('-') || station.endsWith('-')) {
    return 'Police Station name cannot start or end with dots or hyphens.';
  }
  
  if (station.startsWith("'") || station.endsWith("'")) {
    return 'Police Station name cannot start or end with apostrophes.';
  }
  
  // Check for consecutive special characters
  if (station.includes('..') || station.includes('--') || station.includes("''")) {
    return 'Police Station name cannot contain consecutive dots, hyphens, or apostrophes.';
  }
  
  // Check for common police station patterns
  const commonPatterns = [
    /police\s+station/i,
    /ps\s+/i,
    /thana/i,
    /chowki/i,
    /outpost/i
  ];
  
  const hasCommonPattern = commonPatterns.some(pattern => pattern.test(station));
  if (!hasCommonPattern && station.length < 8) {
    // Not a strict error, just a suggestion
    console.log(`Police Station name ${station} doesn't contain common patterns - may be valid`);
  }
  
  // Check for reasonable structure
  const nameParts = station.split(' ').filter(part => part.length > 0);
  if (nameParts.length < 1) {
    return 'Police Station name must contain at least one valid name part.';
  }
  
  // Check if any name part is too short
  const shortParts = nameParts.filter(part => part.length === 1 && !part.match(/[A-Z]/));
  if (shortParts.length > 0) {
    return 'Police Station name parts should be at least 2 characters long (except for initials).';
  }
  
  return null;
};

const validateBeneficiaryBank = (value) => {
  if (!value) return 'Beneficiary Bank is required.';
  
  const bank = value.trim();
  
  // Length validation
  if (bank.length < 3) return 'Bank name must be at least 3 characters long.';
  if (bank.length > 100) return 'Bank name must not exceed 100 characters.';
  
  // Format validation - allow common bank name characters
  if (!/^[a-zA-Z\s\.'&-]+$/.test(bank)) {
    return 'Bank name can only contain letters, spaces, dots, hyphens, apostrophes, and ampersands.';
  }
  
  // Check for reasonable name patterns
  if (bank.length < 5 && !bank.includes(' ')) {
    return 'Bank name seems too short. Please enter the full name.';
  }
  
  // Check for excessive spaces or special characters
  if (bank.includes('  ')) {
    return 'Bank name cannot contain consecutive spaces.';
  }
  
  if (bank.startsWith(' ') || bank.endsWith(' ')) {
    return 'Bank name cannot start or end with spaces.';
  }
  
  if (bank.startsWith('.') || bank.endsWith('.') || bank.startsWith('-') || bank.endsWith('-')) {
    return 'Bank name cannot start or end with dots or hyphens.';
  }
  
  if (bank.startsWith("'") || bank.endsWith("'")) {
    return 'Bank name cannot start or end with apostrophes.';
  }
  
  // Check for consecutive special characters
  if (bank.includes('..') || bank.includes('--') || bank.includes("''")) {
    return 'Bank name cannot contain consecutive dots, hyphens, or apostrophes.';
  }
  
  // Check for common bank patterns
  const commonPatterns = [
    /bank/i,
    /ltd/i,
    /limited/i,
    /cooperative/i,
    /sahakari/i,
    /gramin/i,
    /rural/i,
    /urban/i,
    /national/i,
    /state/i,
    /central/i
  ];
  
  const hasCommonPattern = commonPatterns.some(pattern => pattern.test(bank));
  if (!hasCommonPattern && bank.length < 8) {
    // Not a strict error, just a suggestion
    console.log(`Bank name ${bank} doesn't contain common patterns - may be valid`);
  }
  
  // Check for reasonable structure
  const nameParts = bank.split(' ').filter(part => part.length > 0);
  if (nameParts.length < 1) {
    return 'Bank name must contain at least one valid name part.';
  }
  
  // Check if any name part is too short
  const shortParts = nameParts.filter(part => part.length === 1 && !part.match(/[A-Z]/));
  if (shortParts.length > 0) {
    return 'Bank name parts should be at least 2 characters long (except for initials).';
  }
  
  // Check for common Indian bank names
  const commonBanks = [
    'State Bank of India', 'SBI', 'ICICI Bank', 'ICICI', 'HDFC Bank', 'HDFC',
    'Punjab National Bank', 'PNB', 'Bank of Baroda', 'BOB', 'Canara Bank',
    'Axis Bank', 'Axis', 'Kotak Mahindra Bank', 'Kotak', 'Yes Bank', 'Yes',
    'IDFC First Bank', 'IDFC', 'Federal Bank', 'Federal', 'Karnataka Bank',
    'Karnataka', 'Tamilnad Mercantile Bank', 'TMB', 'City Union Bank', 'CUB',
    'South Indian Bank', 'SIB', 'Dhanlaxmi Bank', 'Dhanlaxmi', 'Jammu & Kashmir Bank',
    'J&K Bank', 'Punjab & Sind Bank', 'PSB', 'UCO Bank', 'UCO', 'Union Bank of India',
    'Union Bank', 'Indian Bank', 'Indian', 'Bank of India', 'BOI', 'Central Bank of India',
    'Central Bank', 'Bank of Maharashtra', 'BOM', 'Indian Overseas Bank', 'IOB',
    'Punjab & Sind Bank', 'PSB', 'UCO Bank', 'UCO', 'Union Bank of India',
    'Union Bank', 'Indian Bank', 'Indian', 'Bank of India', 'BOI', 'Central Bank of India',
    'Central Bank', 'Bank of Maharashtra', 'BOM', 'Indian Overseas Bank', 'IOB'
  ];
  
  const bankLower = bank.toLowerCase();
  const isCommonBank = commonBanks.some(commonBank => 
    bankLower.includes(commonBank.toLowerCase())
  );
  
  if (!isCommonBank && bank.length < 10) {
    // Not a strict error, just a suggestion
    console.log(`Bank name ${bank} not in common list - may be valid`);
  }
  
  return null;
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
          const fieldName = err.loc[1];
          // Map backend field names to frontend field names if needed
          const fieldMapping = {
            'ack_no': 'ackNo',
            'customer_name': 'customerName',
            'sub_category': 'subCategory',
            'transaction_date': 'transactionDate',
            'complaint_date': 'complaintDate',
            'report_date_time': 'reportDateTime',
            'police_station': 'policestation',
            'payment_mode': 'paymentMode',
            'transaction_id': 'transactionId',
            'account_number': 'accountNumber',
            'card_number': 'cardNumber',
            'transaction_amount': 'transactionAmount',
            'disputed_amount': 'disputedAmount',
            'to_bank': 'toBank',
            'to_account': 'toAccount',
            'to_transaction_id': 'toTransactionId',
            'to_amount': 'toAmount',
            'to_upi_id': 'toUpiId',
            'action_taken_date': 'actionTakenDate'
          };
          const frontendField = fieldMapping[fieldName] || fieldName;
          
          // Enhance error messages for better user understanding
          let enhancedMessage = err.msg.charAt(0).toUpperCase() + err.msg.slice(1);
          
          // Add field-specific context to error messages
          if (fieldName === 'ack_no') {
            enhancedMessage = enhancedMessage.replace('ack_no', 'Acknowledgement Number');
          } else if (fieldName === 'customer_name') {
            enhancedMessage = enhancedMessage.replace('customer_name', 'Customer Name');
          } else if (fieldName === 'sub_category') {
            enhancedMessage = enhancedMessage.replace('sub_category', 'Complaint Category');
          } else if (fieldName === 'transaction_date') {
            enhancedMessage = enhancedMessage.replace('transaction_date', 'Transaction Date');
          } else if (fieldName === 'complaint_date') {
            enhancedMessage = enhancedMessage.replace('complaint_date', 'Complaint Date');
          } else if (fieldName === 'report_date_time') {
            enhancedMessage = enhancedMessage.replace('report_date_time', 'Reporting Date & Time');
          } else if (fieldName === 'police_station') {
            enhancedMessage = enhancedMessage.replace('police_station', 'Police Station');
          } else if (fieldName === 'payment_mode') {
            enhancedMessage = enhancedMessage.replace('payment_mode', 'Payment Mode');
          } else if (fieldName === 'transaction_id') {
            enhancedMessage = enhancedMessage.replace('transaction_id', 'Transaction ID');
          } else if (fieldName === 'account_number') {
            enhancedMessage = enhancedMessage.replace('account_number', 'Account Number');
          } else if (fieldName === 'card_number') {
            enhancedMessage = enhancedMessage.replace('card_number', 'Card Number');
          } else if (fieldName === 'transaction_amount') {
            enhancedMessage = enhancedMessage.replace('transaction_amount', 'Transaction Amount');
          } else if (fieldName === 'disputed_amount') {
            enhancedMessage = enhancedMessage.replace('disputed_amount', 'Disputed Amount');
          } else if (fieldName === 'to_bank') {
            enhancedMessage = enhancedMessage.replace('to_bank', 'Beneficiary Bank');
          } else if (fieldName === 'to_account') {
            enhancedMessage = enhancedMessage.replace('to_account', 'Beneficiary Account Number');
          } else if (fieldName === 'to_transaction_id') {
            enhancedMessage = enhancedMessage.replace('to_transaction_id', 'Beneficiary Transaction ID');
          } else if (fieldName === 'to_amount') {
            enhancedMessage = enhancedMessage.replace('to_amount', 'Beneficiary Amount');
          } else if (fieldName === 'to_upi_id') {
            enhancedMessage = enhancedMessage.replace('to_upi_id', 'UPI ID');
          } else if (fieldName === 'action_taken_date') {
            enhancedMessage = enhancedMessage.replace('action_taken_date', 'Action Taken Date');
          }
          
          errors[frontendField] = enhancedMessage;
        }
      });
    }
  } else if (typeof errorResponse?.detail === 'string') {
    generalError.value = errorResponse.detail;
  } else if (errorResponse?.status === 422) {
    generalError.value = 'Please check the form for validation errors.';
  } else if (errorResponse?.status === 400) {
    generalError.value = 'Invalid request. Please check your input and try again.';
  } else if (errorResponse?.status === 401) {
    generalError.value = 'Authentication required. Please log in again.';
  } else if (errorResponse?.status === 403) {
    generalError.value = 'Access denied. You do not have permission to perform this action.';
  } else if (errorResponse?.status === 404) {
    generalError.value = 'Service not found. Please contact support.';
  } else if (errorResponse?.status === 500) {
    generalError.value = 'Server error. Please try again later or contact support.';
  } else if (errorResponse?.status === 503) {
    generalError.value = 'Service temporarily unavailable. Please try again later.';
  } else {
    generalError.value = 'An unexpected error occurred. Please try again.';
  }
}

const onSubmit = async () => {
  Object.keys(errors).forEach(key => delete errors[key]);
  generalError.value = '';
  let hasClientSideError = false;

  // --- Comprehensive validation for all fields ---
  
  // Step 1: Basic Information
  const ackNoError = validateAckNo(form.ackNo);
  if (ackNoError) { errors.ackNo = ackNoError; hasClientSideError = true; }
  
  const customerNameError = validateCustomerName(form.customerName);
  if (customerNameError) { errors.customerName = customerNameError; hasClientSideError = true; }
  
  if (!form.subCategory) { errors.subCategory = 'Complaint Category is required.'; hasClientSideError = true; }
  
  // Validate subcategory selection
  if (form.subCategory && !subCategoryOptions.includes(form.subCategory)) {
    errors.subCategory = 'Please select a valid complaint category from the dropdown.';
    hasClientSideError = true;
  }
  
  // Business logic validation for subcategory
  if (form.subCategory && form.transactionAmount) {
    const amount = parseFloat(form.transactionAmount);
    
    // Some categories might have typical amount ranges
    if (form.subCategory === 'UPI/Wallet Frauds' && amount > 50000) {
      console.log(`UPI/Wallet fraud with high amount (${amount}) - may indicate sophisticated fraud`);
    }
    
    if (form.subCategory === 'Credit/Debit Card Fraud' && amount > 100000) {
      console.log(`Card fraud with high amount (${amount}) - may indicate sophisticated fraud`);
    }
    
    if (form.subCategory === 'Online Scams' && amount < 1000) {
      console.log(`Online scam with low amount (${amount}) - may be valid but unusual`);
    }
  }
  
  const complaintDateError = validateDate(form.complaintDate, 'Complaint Date', currentDate.value);
  if (complaintDateError) { errors.complaintDate = complaintDateError; hasClientSideError = true; }
  
  const reportDateTimeError = validateDateTime(form.reportDateTime, 'Date & Time of Reporting');
  if (reportDateTimeError) { errors.reportDateTime = reportDateTimeError; hasClientSideError = true; }
  
  if (!form.state) { errors.state = 'State is required.'; hasClientSideError = true; }
  if (!form.district) { errors.district = 'District is required.'; hasClientSideError = true; }
  
  // Validate state and district selection
  if (form.state && !stateOptions.value.includes(form.state)) {
    errors.state = 'Please select a valid state from the dropdown.';
    hasClientSideError = true;
  }
  
  if (form.district && !districtOptions.value.includes(form.district)) {
    errors.district = 'Please select a valid district from the dropdown.';
    hasClientSideError = true;
  }
  
  // Business logic validation for location
  if (form.state && form.district && form.policestation) {
    // Check if police station name contains state/district info
    const stateLower = form.state.toLowerCase();
    const districtLower = form.district.toLowerCase();
    const policeStationLower = form.policestation.toLowerCase();
    
    // This is just informational, not an error
    if (!policeStationLower.includes(stateLower) && !policeStationLower.includes(districtLower)) {
      console.log(`Police station name doesn't contain state/district info - may be valid`);
    }
    
    // Check for common location patterns
    const commonStatePatterns = {
      'Maharashtra': ['mumbai', 'pune', 'nagpur', 'thane', 'nashik'],
      'Delhi': ['new delhi', 'old delhi', 'south delhi', 'north delhi'],
      'Karnataka': ['bangalore', 'mysore', 'mangalore', 'hubli'],
      'Tamil Nadu': ['chennai', 'coimbatore', 'madurai', 'salem'],
      'Gujarat': ['ahmedabad', 'surat', 'vadodara', 'rajkot']
    };
    
    if (commonStatePatterns[form.state]) {
      const hasCommonCity = commonStatePatterns[form.state].some(city => 
        policeStationLower.includes(city)
      );
      if (!hasCommonCity) {
        console.log(`Police station name doesn't contain common city for ${form.state} - may be valid`);
      }
    }
  }
  
  const policeStationError = validatePoliceStation(form.policestation);
  if (policeStationError) { errors.policestation = policeStationError; hasClientSideError = true; }
  
  // Step 2: Transaction Details
  if (!form.paymentMode) { errors.paymentMode = 'Mode of Payment is required.'; hasClientSideError = true; }
  
  // Validate payment mode selection
  if (form.paymentMode && !paymentModeOptions.includes(form.paymentMode)) {
    errors.paymentMode = 'Please select a valid payment mode from the dropdown.';
    hasClientSideError = true;
  }
  
  // Business logic validation for payment mode
  if (form.paymentMode && form.transactionAmount) {
    const amount = parseFloat(form.transactionAmount);
    
    // Some payment modes have typical amount ranges
    if (form.paymentMode === 'UPI' && amount > 100000) {
      console.log(`UPI transaction with high amount (${amount}) - may be valid but unusual`);
    }
    
    if (form.paymentMode === 'Credit Card' && amount > 500000) {
      console.log(`Credit card transaction with high amount (${amount}) - may be valid but unusual`);
    }
    
    if (form.paymentMode === 'Digital Wallets / Mobile Wallets' && amount > 50000) {
      console.log(`Digital wallet transaction with high amount (${amount}) - may be valid but unusual`);
    }
    
    if (form.paymentMode === 'Cheque' && amount < 1000) {
      console.log(`Cheque transaction with low amount (${amount}) - may be valid but unusual`);
    }
    
    if (form.paymentMode === 'POS Terminals' && amount > 100000) {
      console.log(`POS transaction with high amount (${amount}) - may be valid but unusual`);
    }
  }
  
  const transactionDateError = validateDate(form.transactionDate, 'Transaction Date', currentDate.value);
  if (transactionDateError) { errors.transactionDate = transactionDateError; hasClientSideError = true; }
  
  const transactionIdError = validateTransactionId(form.transactionId);
  if (transactionIdError) { errors.transactionId = transactionIdError; hasClientSideError = true; }
  
  if (!form.layers) { errors.layers = 'Layers is required.'; hasClientSideError = true; }
  
  // Validate layers selection
  if (form.layers && !form.layers.startsWith('Layer ')) {
    errors.layers = 'Please select a valid layer from the dropdown.';
    hasClientSideError = true;
  }
  
  // Business logic validation for layers
  if (form.layers && form.transactionAmount) {
    const layerNumber = parseInt(form.layers.replace('Layer ', ''));
    const amount = parseFloat(form.transactionAmount);
    
    // Higher layer numbers might indicate more complex fraud
    if (layerNumber > 20 && amount < 10000) {
      console.log(`High layer number (${layerNumber}) with low amount (${amount}) - may indicate complex fraud`);
    }
    
    if (layerNumber > 25) {
      console.log(`Very high layer number (${layerNumber}) - may indicate sophisticated fraud scheme`);
    }
  }
  
  const transactionAmountError = validateAmount(form.transactionAmount, 'Transaction Amount');
  if (transactionAmountError) { errors.transactionAmount = transactionAmountError; hasClientSideError = true; }
  
  const disputedAmountError = validateAmount(form.disputedAmount, 'Disputed Amount');
  if (disputedAmountError) { errors.disputedAmount = disputedAmountError; hasClientSideError = true; }
  
  // Validate that disputed amount doesn't exceed transaction amount
  if (form.transactionAmount && form.disputedAmount && form.disputedAmount > form.transactionAmount) {
    errors.disputedAmount = 'Disputed amount cannot exceed transaction amount.';
    hasClientSideError = true;
  }
  
  // Business logic validation for disputed amount
  if (form.transactionAmount && form.disputedAmount) {
    const transactionAmount = parseFloat(form.transactionAmount);
    const disputedAmount = parseFloat(form.disputedAmount);
    
    // Check if disputed amount is reasonable compared to transaction amount
    if (disputedAmount > transactionAmount) {
      errors.disputedAmount = 'Disputed amount cannot exceed transaction amount.';
      hasClientSideError = true;
    }
    
    if (disputedAmount < transactionAmount * 0.1) {
      console.log(`Disputed amount (${disputedAmount}) is very small compared to transaction amount (${transactionAmount}) - may indicate partial dispute`);
    }
    
    if (disputedAmount === transactionAmount) {
      console.log(`Disputed amount equals transaction amount - may indicate full dispute`);
    }
    
    if (disputedAmount === 0) {
      errors.disputedAmount = 'Disputed amount cannot be zero.';
      hasClientSideError = true;
    }
    
    // Check for suspicious dispute patterns
    const disputeRatio = disputedAmount / transactionAmount;
    if (disputeRatio > 0.95) {
      console.log(`Very high dispute ratio (${(disputeRatio * 100).toFixed(1)}%) - may indicate full fraud`);
    }
    
    if (disputeRatio < 0.05) {
      console.log(`Very low dispute ratio (${(disputeRatio * 100).toFixed(1)}%) - may indicate partial fraud or fee dispute`);
    }
    
    // Check for common fraud dispute patterns
    const disputeDiff = transactionAmount - disputedAmount;
    if (disputeDiff < 100 && transactionAmount > 10000) {
      console.log(`Very small undisputed amount (${disputeDiff}) for large transaction - may indicate fee-based fraud`);
    }
    
    // Check for round number disputes
    if (disputedAmount % 1000 === 0 && disputedAmount > 1000) {
      console.log(`Round disputed amount (${disputedAmount}) - may indicate structured fraud`);
    }
  }
  
  // Step 3: Beneficiary Details
  const beneficiaryBankError = validateBeneficiaryBank(form.toBank);
  if (beneficiaryBankError) { errors.toBank = beneficiaryBankError; hasClientSideError = true; }
  
  const toTransactionIdError = validateTransactionId(form.toTransactionId);
  if (toTransactionIdError) { errors.toTransactionId = toTransactionIdError; hasClientSideError = true; }
  
  // Business logic validation for beneficiary transaction ID
  if (form.toTransactionId && form.transactionId) {
    // Check if beneficiary transaction ID is different from victim transaction ID
    if (form.toTransactionId === form.transactionId) {
      errors.toTransactionId = 'Beneficiary transaction ID should be different from victim transaction ID.';
      hasClientSideError = true;
    }
    
    // Check for similar patterns (might indicate same transaction)
    const victimTxn = form.transactionId.toLowerCase();
    const beneficiaryTxn = form.toTransactionId.toLowerCase();
    
    if (victimTxn.includes(beneficiaryTxn) || beneficiaryTxn.includes(victimTxn)) {
      console.log(`Transaction IDs are very similar - may indicate same transaction`);
    }
    
    // Check for common prefixes
    const commonPrefixes = ['txn', 'utr', 'ref', 'case'];
    const hasCommonPrefix = commonPrefixes.some(prefix => 
      victimTxn.startsWith(prefix) && beneficiaryTxn.startsWith(prefix)
    );
    
    if (hasCommonPrefix) {
      console.log(`Both transaction IDs have common prefix - may be related transactions`);
    }
  }
  
  const toAmountError = validateAmount(form.toAmount, 'Beneficiary Transaction Amount');
  if (toAmountError) { errors.toAmount = toAmountError; hasClientSideError = true; }
  
  // Business logic validation for amounts
  if (form.transactionAmount && form.toAmount) {
    const victimAmount = parseFloat(form.transactionAmount);
    const beneficiaryAmount = parseFloat(form.toAmount);
    
    // Check if beneficiary amount is reasonable compared to victim amount
    if (beneficiaryAmount > victimAmount * 1.1) {
      errors.toAmount = 'Beneficiary amount cannot exceed victim amount by more than 10%.';
      hasClientSideError = true;
    }
    
    if (beneficiaryAmount < victimAmount * 0.9) {
      console.log(`Beneficiary amount (${beneficiaryAmount}) is significantly less than victim amount (${victimAmount}) - may indicate partial fraud`);
    }
    
    // Check for suspicious amount patterns
    if (beneficiaryAmount === victimAmount) {
      console.log(`Beneficiary amount equals victim amount - may indicate direct transfer`);
    }
    
    if (beneficiaryAmount === 0) {
      errors.toAmount = 'Beneficiary amount cannot be zero.';
      hasClientSideError = true;
    }
    
    // Check for common fraud amount patterns
    const amountDiff = Math.abs(victimAmount - beneficiaryAmount);
    if (amountDiff < 100 && victimAmount > 10000) {
      console.log(`Very small difference (${amountDiff}) between large amounts - may indicate fee-based fraud`);
    }
    
    // Check for round number differences
    if (amountDiff % 1000 === 0 && amountDiff > 0) {
      console.log(`Round difference (${amountDiff}) between amounts - may indicate structured fraud`);
    }
  }
  
  // Step 4: Action Details
  const actionTakenDateError = validateDate(form.actionTakenDate, 'Action Taken Date', currentDate.value);
  if (actionTakenDateError) { errors.actionTakenDate = actionTakenDateError; hasClientSideError = true; }
  
  // Validate action selection (optional field but validate if provided)
  if (form.action && !actionOptions.includes(form.action)) {
    errors.action = 'Please select a valid action from the dropdown.';
    hasClientSideError = true;
  }
  
  // Business logic validation for action
  if (form.action && form.actionTakenDate && form.reportDateTime) {
    const actionDate = new Date(form.actionTakenDate);
    const reportDate = new Date(form.reportDateTime);
    const timeDiff = actionDate.getTime() - reportDate.getTime();
    const daysDiff = timeDiff / (1000 * 60 * 60 * 24);
    
    // Check if action was taken too quickly
    if (daysDiff < 0) {
      errors.actionTakenDate = 'Action taken date cannot be earlier than reporting date.';
      hasClientSideError = true;
    }
    
    // Check if action was taken too quickly (suspicious)
    if (daysDiff < 0.1) {
      console.log(`Action taken very quickly (${daysDiff.toFixed(2)} days) after reporting - may be valid`);
    }
    
    // Check if action was taken too late
    if (daysDiff > 30) {
      console.log(`Action taken very late (${daysDiff.toFixed(0)} days) after reporting - may indicate delay`);
    }
  }
  
  // Dynamic field validations based on payment mode
  ['accountNumber', 'cardNumber', 'toAccount', 'ifsc', 'toUpiId'].forEach(field => {
    if (isFieldRequired(field) && !form[field]) {
      const name = {
        accountNumber: 'Victim Account Number', 
        cardNumber: 'Victim Card Number', 
        toAccount: 'Beneficiary Account Number', 
        ifsc: 'IFSC Code', 
        toUpiId: 'UPI ID'
      }[field];
      errors[field] = `${name} is required for this payment mode.`;
      hasClientSideError = true;
    }
  });
  
  // Format validations for dynamic fields
  if (isFieldRequired('accountNumber') && form.accountNumber) {
    const accountError = validateAccountNumber(form.accountNumber);
    if (accountError) { errors.accountNumber = accountError; hasClientSideError = true; }
  }
  
  if (isFieldRequired('cardNumber') && form.cardNumber) {
    const cardError = validateCardNumber(form.cardNumber);
    if (cardError) { errors.cardNumber = cardError; hasClientSideError = true; }
  }
  
  if (isFieldRequired('toAccount') && form.toAccount) {
    const toAccountError = validateAccountNumber(form.toAccount);
    if (toAccountError) { errors.toAccount = toAccountError; hasClientSideError = true; }
  }
  
  if (isFieldRequired('ifsc') && form.ifsc) {
    const ifscError = validateIFSC(form.ifsc);
    if (ifscError) { errors.ifsc = ifscError; hasClientSideError = true; }
  }
  
  if (isFieldRequired('toUpiId') && form.toUpiId) {
    const upiError = validateUPIId(form.toUpiId);
    if (upiError) { errors.toUpiId = upiError; hasClientSideError = true; }
  }
  
  // Business logic validations
  if (form.complaintDate && form.transactionDate) {
    const complaintDate = new Date(form.complaintDate);
    const transactionDate = new Date(form.transactionDate);
    if (complaintDate < transactionDate) {
      errors.complaintDate = 'Complaint date cannot be earlier than transaction date.';
      hasClientSideError = true;
    }
  }
  
  if (form.reportDateTime && form.complaintDate) {
    const reportDateTime = new Date(form.reportDateTime);
    const complaintDate = new Date(form.complaintDate);
    if (reportDateTime < complaintDate) {
      errors.reportDateTime = 'Reporting date cannot be earlier than complaint date.';
      hasClientSideError = true;
    }
  }
  
  // Enhanced amount validations
  const amountErrors = validateAmounts();
  amountErrors.forEach(errorMsg => {
    if (errorMsg.includes('Disputed amount')) {
      errors.disputedAmount = errorMsg;
      hasClientSideError = true;
    } else if (errorMsg.includes('Beneficiary amount')) {
      errors.toAmount = errorMsg;
      hasClientSideError = true;
    } else if (errorMsg.includes('Transaction amount')) {
      errors.transactionAmount = errorMsg;
      hasClientSideError = true;
    }
  });
  
  // Additional business logic validations
  if (form.actionTakenDate && form.reportDateTime) {
    const actionDate = new Date(form.actionTakenDate);
    const reportDate = new Date(form.reportDateTime);
    if (actionDate < reportDate) {
      errors.actionTakenDate = 'Action taken date cannot be earlier than reporting date.';
      hasClientSideError = true;
    }
  }
  
  // Validate that all required fields have meaningful values
  if (form.customerName && form.customerName.trim().length < 2) {
    errors.customerName = 'Customer name must be at least 2 characters long.';
    hasClientSideError = true;
  }
  
  if (form.policestation && form.policestation.trim().length < 3) {
    errors.policestation = 'Police station name must be at least 3 characters long.';
    hasClientSideError = true;
  }
  
  // Overall form consistency validation
  if (form.paymentMode && form.transactionAmount && form.toAmount) {
    const paymentMode = form.paymentMode;
    const transactionAmount = parseFloat(form.transactionAmount);
    const beneficiaryAmount = parseFloat(form.toAmount);
    
    // Check for payment mode specific validations
    if (paymentMode === 'UPI' && transactionAmount > 100000) {
      console.log(`UPI transaction amount (${transactionAmount}) exceeds typical UPI limits - may be valid but unusual`);
    }
    
    if (paymentMode === 'Credit Card' && transactionAmount > 500000) {
      console.log(`Credit card transaction amount (${transactionAmount}) is very high - may be valid but unusual`);
    }
    
    if (paymentMode === 'Digital Wallets / Mobile Wallets' && transactionAmount > 50000) {
      console.log(`Digital wallet transaction amount (${transactionAmount}) exceeds typical wallet limits - may be valid but unusual`);
    }
    
    if (paymentMode === 'Cheque' && transactionAmount < 1000) {
      console.log(`Cheque transaction amount (${transactionAmount}) is very low - may be valid but unusual`);
    }
    
    // Check for amount consistency across payment modes
    if (paymentMode === 'UPI' && beneficiaryAmount > transactionAmount) {
      console.log(`UPI beneficiary amount exceeds transaction amount - may indicate fee structure`);
    }
    
    if (paymentMode === 'Credit Card' && beneficiaryAmount < transactionAmount * 0.95) {
      console.log(`Credit card beneficiary amount significantly less than transaction amount - may indicate processing fees`);
    }
  }
  
  // Check for suspicious patterns across multiple fields
  if (form.subCategory && form.transactionAmount && form.layers) {
    const category = form.subCategory;
    const amount = parseFloat(form.transactionAmount);
    const layerNumber = parseInt(form.layers.replace('Layer ', ''));
    
    // High-value transactions with high layer numbers might indicate sophisticated fraud
    if (amount > 100000 && layerNumber > 20) {
      console.log(`High-value transaction (${amount}) with high layer number (${layerNumber}) - may indicate sophisticated fraud`);
    }
    
    // Low-value transactions with high layer numbers might indicate complex fraud
    if (amount < 10000 && layerNumber > 25) {
      console.log(`Low-value transaction (${amount}) with very high layer number (${layerNumber}) - may indicate complex fraud`);
    }
    
    // Specific category validations
    if (category === 'UPI/Wallet Frauds' && amount > 100000) {
      console.log(`UPI/Wallet fraud with very high amount (${amount}) - may indicate sophisticated fraud`);
    }
    
    if (category === 'Credit/Debit Card Fraud' && amount > 500000) {
      console.log(`Card fraud with very high amount (${amount}) - may indicate sophisticated fraud`);
    }
    
    if (category === 'Online Scams' && amount < 1000) {
      console.log(`Online scam with very low amount (${amount}) - may be valid but unusual`);
    }
  }
  
  // Check for location-based validations
  if (form.state && form.district && form.transactionAmount) {
    const state = form.state;
    const amount = parseFloat(form.transactionAmount);
    
    // Some states might have typical fraud patterns
    const highFraudStates = ['Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu', 'Gujarat'];
    if (highFraudStates.includes(state) && amount > 500000) {
      console.log(`High-value fraud in ${state} - may indicate sophisticated fraud network`);
    }
    
    // Rural vs urban fraud patterns
    const ruralStates = ['Bihar', 'Jharkhand', 'Chhattisgarh', 'Odisha', 'Madhya Pradesh'];
    if (ruralStates.includes(state) && amount > 100000) {
      console.log(`High-value fraud in rural state ${state} - may be valid but unusual`);
    }
  }
  
  // If any error was found, navigate to the step with the first error
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
    const token = localStorage.getItem('jwt');
    await axios.post('/api/case-entry', formData, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    window.showNotification('success', 'Case Submitted', 'Case submitted successfully.');
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
    } else if (error.code === 'ECONNABORTED') {
      generalError.value = 'Request timed out. Please check your internet connection and try again.';
    } else if (error.code === 'ERR_NETWORK') {
      generalError.value = 'Network error. Please check your internet connection and try again.';
    } else if (error.code === 'ERR_BAD_REQUEST') {
      generalError.value = 'Invalid request. Please check your input and try again.';
    } else if (error.code === 'ERR_BAD_RESPONSE') {
      generalError.value = 'Invalid response from server. Please try again.';
    } else if (error.code === 'ERR_BAD_OPTION') {
      generalError.value = 'Configuration error. Please contact support.';
    } else if (error.code === 'ERR_CANCELED') {
      generalError.value = 'Request was canceled. Please try again.';
    } else if (error.message?.includes('timeout')) {
      generalError.value = 'Request timed out. Please try again.';
    } else if (error.message?.includes('Network Error')) {
      generalError.value = 'Network error. Please check your internet connection and try again.';
    } else if (error.message?.includes('Failed to fetch')) {
      generalError.value = 'Failed to connect to server. Please check your internet connection and try again.';
    } else if (error.message?.includes('ERR_INTERNET_DISCONNECTED')) {
      generalError.value = 'No internet connection. Please check your network and try again.';
    } else {
      generalError.value = 'Failed to submit case. Network error or server unreachable.';
    }
    
    // Log additional error details for debugging
    if (error.config) {
      console.log('Request config:', error.config);
    }
    if (error.request) {
      console.log('Request details:', error.request);
    }
    if (error.response) {
      console.log('Response details:', error.response);
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