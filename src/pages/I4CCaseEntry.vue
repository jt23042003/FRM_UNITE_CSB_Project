<template>
  <div class="i4c-form-container">
    <!-- Progress Bar -->
    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${(currentStep / 4) * 100}%` }"></div>
      </div>
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
          <div class="step-number">{{ step }}</div>
          <span class="step-title">{{ getStepTitle(step) }}</span>
        </div>
      </div>
    </div>

    <!-- Form Container -->
    <div class="form-wrapper">
      <div v-if="generalError" class="error-banner">
        <i class="fa fa-exclamation-triangle"></i>
        <span>{{ generalError }}</span>
      </div>

      <!-- Step 1: Basic Information -->
      <div v-if="currentStep === 1" class="step-content">
        <div class="step-header">
          <h2>Basic Information</h2>
          <p>Enter complaint and customer details</p>
        </div>

        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">
              Acknowledgement No. <span class="required">*</span>
        </label>
            <input 
              v-model="form.ackNo" 
              type="text" 
              class="form-input"
              :class="{ 'error': errors.ackNo }"
              placeholder="e.g., ACK202506120001"
            />
            <span v-if="errors.ackNo" class="error-text">{{ errors.ackNo }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Customer Name <span class="required">*</span>
        </label>
            <input 
              v-model="form.customerName" 
              type="text" 
              class="form-input"
              :class="{ 'error': errors.customerName }"
              placeholder="Enter customer name"
            />
            <span v-if="errors.customerName" class="error-text">{{ errors.customerName }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Complaint Category <span class="required">*</span>
            </label>
            <select 
              v-model="form.subCategory" 
              class="form-select"
              :class="{ 'error': errors.subCategory }"
            >
              <option value="">Select complaint category</option>
              <option v-for="option in subCategoryOptions" :key="option" :value="option">
                {{ option }}
              </option>
          </select>
            <span v-if="errors.subCategory" class="error-text">{{ errors.subCategory }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Transaction Date <span class="required">*</span>
        </label>
            <input 
              v-model="form.transactionDate" 
              type="date" 
              class="form-input"
              :class="{ 'error': errors.transactionDate }"
              :max="currentDate"
            />
            <span v-if="errors.transactionDate" class="error-text">{{ errors.transactionDate }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Complaint Date <span class="required">*</span>
        </label>
            <input 
              v-model="form.complaintDate" 
              type="date" 
              class="form-input"
              :class="{ 'error': errors.complaintDate }"
              :max="currentDate"
            />
            <span v-if="errors.complaintDate" class="error-text">{{ errors.complaintDate }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Date & Time of Reporting <span class="required">*</span>
        </label>
            <input 
              v-model="form.reportDateTime" 
              type="datetime-local" 
              class="form-input"
              :class="{ 'error': errors.reportDateTime }"
              :max="currentDateTime"
            />
            <span v-if="errors.reportDateTime" class="error-text">{{ errors.reportDateTime }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              State <span class="required">*</span>
            </label>
            <select 
              v-model="form.state" 
              class="form-select"
              :class="{ 'error': errors.state }"
            >
              <option value="">Select state</option>
    <option v-for="st in stateOptions" :key="st" :value="st">{{ st }}</option>
  </select>
            <span v-if="errors.state" class="error-text">{{ errors.state }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              District <span class="required">*</span>
</label>
            <select 
              v-model="form.district" 
              class="form-select"
              :class="{ 'error': errors.district }"
            >
              <option value="">Select district</option>
              <option v-for="districtName in districtOptions" :key="districtName" :value="districtName">
                {{ districtName }}
              </option>
  </select>
            <span v-if="errors.district" class="error-text">{{ errors.district }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Police Station <span class="required">*</span>
</label>
            <input 
              v-model="form.policestation" 
              type="text" 
              class="form-input"
              :class="{ 'error': errors.policestation }"
              placeholder="Enter police station name"
            />
            <span v-if="errors.policestation" class="error-text">{{ errors.policestation }}</span>
          </div>
        </div>
      </div>

      <!-- Step 2: Transaction Details -->
      <div v-if="currentStep === 2" class="step-content">
        <div class="step-header">
          <h2>Transaction Details</h2>
          <p>Enter payment and transaction information</p>
        </div>

        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">
              Mode of Payment <span class="required">*</span>
            </label>
            <select 
              v-model="form.paymentMode" 
              class="form-select"
              :class="{ 'error': errors.paymentMode }"
              @change="clearDynamicErrors"
            >
              <option value="">Select payment mode</option>
            <option v-for="mode in paymentModeOptions" :key="mode" :value="mode">{{ mode }}</option>
          </select>
            <span v-if="errors.paymentMode" class="error-text">{{ errors.paymentMode }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Transaction ID / UTR Number <span class="required">*</span>
        </label>
            <input 
              v-model="form.transactionId" 
              type="text" 
              class="form-input"
              :class="{ 'error': errors.transactionId }"
              placeholder="e.g., TXN987654321"
            />
            <span v-if="errors.transactionId" class="error-text">{{ errors.transactionId }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Victim Account Number <span v-if="isFieldRequired('accountNumber')" class="required">*</span>
        </label>
          <input
            v-model="form.accountNumber"
            type="number"
              class="form-input"
              :class="{ 'error': errors.accountNumber }"
              placeholder="Enter account number"
            :required="isFieldRequired('accountNumber')"
            minlength="9"
            maxlength="18"
          />
            <span v-if="errors.accountNumber" class="error-text">{{ errors.accountNumber }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Victim Card Number <span v-if="isFieldRequired('cardNumber')" class="required">*</span>
        </label>
          <input
            v-model="form.cardNumber"
            type="number"
              class="form-input"
              :class="{ 'error': errors.cardNumber }"
              placeholder="Enter card number"
            :required="isFieldRequired('cardNumber')"
            minlength="12"
            maxlength="19"
          />
            <span v-if="errors.cardNumber" class="error-text">{{ errors.cardNumber }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Layers <span class="required">*</span>
        </label>
            <select 
              v-model="form.layers" 
              class="form-select"
              :class="{ 'error': errors.layers }"
            >
              <option value="">Select layer</option>
            <option v-for="n in 30" :key="n" :value="`Layer ${n}`">Layer {{ n }}</option>
          </select>
            <span v-if="errors.layers" class="error-text">{{ errors.layers }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Transaction Amount <span class="required">*</span>
        </label>
            <div class="amount-input-wrapper">
              <span class="currency-symbol">₹</span>
              <input 
                v-model.number="form.transactionAmount" 
                type="number" 
                class="form-input amount-input"
                :class="{ 'error': errors.transactionAmount }"
                placeholder="0.00"
                min="0" 
                step="any"
              />
            </div>
            <span v-if="errors.transactionAmount" class="error-text">{{ errors.transactionAmount }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Disputed Amount <span class="required">*</span>
            </label>
            <div class="amount-input-wrapper">
              <span class="currency-symbol">₹</span>
              <input 
                v-model.number="form.disputedAmount" 
                type="number" 
                class="form-input amount-input"
                :class="{ 'error': errors.disputedAmount }"
                placeholder="0.00"
                min="0" 
                step="any"
              />
            </div>
            <span v-if="errors.disputedAmount" class="error-text">{{ errors.disputedAmount }}</span>
          </div>
        </div>
      </div>

      <!-- Step 3: Beneficiary Details -->
      <div v-if="currentStep === 3" class="step-content">
        <div class="step-header">
          <h2>Beneficiary Details</h2>
          <p>Enter recipient bank and account information</p>
        </div>

        <div class="form-grid">
          <div class="form-group full-width">
            <label class="form-label">
              Beneficiary Bank Details <span class="required">*</span>
            </label>
            <div class="autocomplete-container">
              <input 
              v-model="form.toBank"
              type="text"
                class="form-input"
                :class="{ 'error': errors.toBank }"
                placeholder="Start typing bank name..."
              @focus="onBankInputFocus"
              @blur="onBankInputBlur"
              @keydown="onBankInputKeydown"
            />
            <ul v-if="showBankSuggestions && bankSuggestions.length > 0" class="suggestions-list">
              <li
                v-for="(suggestion, index) in bankSuggestions"
                :key="index"
                :class="{ 'active': index === activeSuggestionIndex }"
                @mousedown.prevent="selectSuggestion(suggestion)"
              >
                {{ suggestion }}
              </li>
            </ul>
          </div>
            <span v-if="errors.toBank" class="error-text">{{ errors.toBank }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Beneficiary Account Number <span v-if="isFieldRequired('toAccount')" class="required">*</span>
        </label>
            <input 
              v-model="form.toAccount" 
              type="number" 
              class="form-input"
              :class="{ 'error': errors.toAccount }"
              placeholder="Enter account number"
              :required="isFieldRequired('toAccount')"
            />
            <span v-if="errors.toAccount" class="error-text">{{ errors.toAccount }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              IFSC Code <span v-if="isFieldRequired('ifsc')" class="required">*</span>
        </label>
          <input
            v-model="form.ifsc"
            type="text"
              class="form-input"
              :class="{ 'error': errors.ifsc }"
              placeholder="e.g., ICIC0000001"
            :required="isFieldRequired('ifsc')"
              :disabled="!form.toBank"
            />
            <span v-if="errors.ifsc" class="error-text">{{ errors.ifsc }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Beneficiary Transaction ID <span class="required">*</span>
        </label>
            <input 
              v-model="form.toTransactionId" 
              type="text" 
              class="form-input"
              :class="{ 'error': errors.toTransactionId }"
              placeholder="e.g., TXN765432109"
            />
            <span v-if="errors.toTransactionId" class="error-text">{{ errors.toTransactionId }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Transaction Amount <span class="required">*</span>
        </label>
            <div class="amount-input-wrapper">
              <span class="currency-symbol">₹</span>
              <input 
                v-model.number="form.toAmount" 
                type="number" 
                class="form-input amount-input"
                :class="{ 'error': errors.toAmount }"
                placeholder="0.00"
                min="0" 
                step="any"
              />
            </div>
            <span v-if="errors.toAmount" class="error-text">{{ errors.toAmount }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              UPI ID <span v-if="isFieldRequired('toUpiId')" class="required">*</span>
        </label>
            <input 
              v-model="form.toUpiId" 
              type="text" 
              class="form-input"
              :class="{ 'error': errors.toUpiId }"
              placeholder="e.g., user@upi"
              :required="isFieldRequired('toUpiId')"
            />
            <span v-if="errors.toUpiId" class="error-text">{{ errors.toUpiId }}</span>
          </div>
        </div>
      </div>

      <!-- Step 4: Action Details -->
      <div v-if="currentStep === 4" class="step-content">
        <div class="step-header">
          <h2>Action Details</h2>
          <p>Enter action taken and follow-up information</p>
        </div>

        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">
          Action
            </label>
            <select 
              v-model="form.action" 
              class="form-select"
              :class="{ 'error': errors.action }"
            >
              <option value="">Select action</option>
            <option v-for="opt in actionOptions" :key="opt" :value="opt">{{ opt }}</option>
          </select>
            <span v-if="errors.action" class="error-text">{{ errors.action }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Action Taken Date <span class="required">*</span>
        </label>
            <input 
              v-model="form.actionTakenDate" 
              type="date" 
              class="form-input"
              :class="{ 'error': errors.actionTakenDate }"
              :max="currentDate"
            />
            <span v-if="errors.actionTakenDate" class="error-text">{{ errors.actionTakenDate }}</span>
          </div>
        </div>
      </div>

      <!-- Navigation Buttons -->
      <div class="form-navigation">
        <button 
          v-if="currentStep > 1" 
          type="button" 
          class="nav-button prev" 
          @click="previousStep"
        >
          <i class="fa fa-arrow-left"></i>
          Previous
        </button>
        
        <button 
          v-if="currentStep < 4" 
          type="button" 
          class="nav-button next" 
          @click="nextStep"
        >
          Next
          <i class="fa fa-arrow-right"></i>
        </button>
        
        <button 
          v-if="currentStep === 4" 
          type="button" 
          class="nav-button next" 
          @click="onSubmit"
        >
          <i class="fa fa-paper-plane"></i>
          Submit Case
        </button>
      </div>
      </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch, onMounted } from 'vue';
import axios from 'axios';
import { banks } from '../data/bank.js';

// --- Dropdown Options (no change) ---
const subCategoryOptions = [ 'Online Scams', 'Phishing', 'Unauthorized Transactions', 'Credit/Debit Card Fraud', 'UPI/Wallet Frauds', 'SIM Swap Fraud', 'Vishing (Voice Phishing)', 'Smishing (SMS Phishing)', 'Fake Banking Websites/Apps', 'Online Payment Gateway Frauds', 'KYC Update Frauds', 'Loan App Frauds', 'Others' ];
const actionOptions = [ 'Freeze Account', 'Reverse Transaction', 'Block/Restrict Account Access', 'Investigation','others' ];
const paymentModeOptions = [ 'UPI', 'Net Banking / Internet Banking', 'Credit Card', 'Debit Card', 'Digital Wallets / Mobile Wallets', 'Cheque', 'IMPS', 'NEFT', 'RTGS', 'AEPS', 'POS Terminals' ];

// This will now be dynamically populated
const stateOptions = ref([]); // <--- Change to ref and initialize as empty array
const districtOptions = ref([]); // This will hold districts for the selected state
const allDistricts = ref([]);   // This will store ALL districts fetched from the API
// --- API endpoint ---
const STATES_API_URL = 'https://api.data.gov.in/resource/a71e60f0-a21d-43de-a6c5-fa5d21600cdb?api-key=579b464db66ec23bdd000001cdc3b564546246a772a26393094f5645&offset=0&limit=all&format=json';
const DISTRICTS_API_URL = 'https://api.data.gov.in/resource/37231365-78ba-44d5-ac22-3deec40b9197?api-key=579b464db66ec23bdd000001cdc3b564546246a772a26393094f5645&offset=0&limit=all&format=json';
const IFSC_VALIDATION_API_BASE_URL = 'https://ifsc.razorpay.com/';


// NEW: Bank Autocomplete Related Refs and Data
const allBanks = ref([]); // To store the full bank names as an array for easier filtering
const bankSuggestions = ref([]); // To store filtered suggestions
const showBankSuggestions = ref(false); // To control visibility of suggestion list
const activeSuggestionIndex = ref(-1); // For keyboard navigation within suggestions


// --- The Rules Engine (no change) ---
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
  'exception':[] // This is a catch-all for any payment mode not explicitly defined
};


const form = reactive({
  ackNo: '',
  customerName: '', // NEW: Customer Name field
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
  // lienAmount: null,
  // evidence: null,
  // evidenceName: '',
  // additionalInfo: ''
});

const errors = reactive({});
const generalError = ref('');

const currentDate = computed(() => {
  const today = new Date();
  const year = today.getFullYear();
  const month = (today.getMonth() + 1).toString().padStart(2, '0');
  const day = today.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
});

const currentDateTime = computed(() => {
  const now = new Date();
  const year = now.getFullYear();
  const month = (now.getMonth() + 1).toString().padStart(2, '0');
  const day = now.getDate().toString().padStart(2, '0');
  const hours = now.getHours().toString().padStart(2, '0');
  const minutes = now.getMinutes().toString().padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
});

// --- Step Navigation ---
const currentStep = ref(1);

const getStepTitle = (step) => {
  const titles = {
    1: 'Basic Info',
    2: 'Transaction',
    3: 'Beneficiary',
    4: 'Action'
  };
  return titles[step] || '';
};

const nextStep = () => {
  if (currentStep.value < 4) {
    currentStep.value++;
  }
};

const previousStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--;
  }
};

// --- Fetch states on component mount ---
onMounted(async () => {
  try {
    // Fetch States
    const stateResponse = await axios.get(STATES_API_URL);
    if (stateResponse.data && stateResponse.data.records) {
      const fetchedStates = stateResponse.data.records
        .map(record => record.state_name_english)
        .sort((a, b) => a.localeCompare(b)); 
      stateOptions.value = fetchedStates;
    }

    // Fetch All Districts
    const districtResponse = await axios.get(DISTRICTS_API_URL);
    if (districtResponse.data && districtResponse.data.records) {
      allDistricts.value = districtResponse.data.records;
    }
    // NEW: Load Bank Data from imported JSON
    allBanks.value = Object.values(banks); // Convert the bank object to an array of bank names


  } catch (error) {
    console.error('Error fetching data:', error);
    generalError.value = 'Failed to load states or districts. Please try again later.';
    // Fallback to predefined states if API fails
    stateOptions.value = [
      'Andaman And Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chandigarh', 'Chhattisgarh', 'Delhi', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jammu And Kashmir', 'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Puducherry', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'The Dadra And Nagar Haveli And Daman And Diu', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
    ].sort((a, b) => a.localeCompare(b));
    // Keep districtOptions empty on API failure for districts as it's a dependent field
  }
});

watch(() => form.state, (newState) => {
  form.district = ''; // Clear selected district when state changes
  if (newState) {
    const filtered = allDistricts.value
      .filter(district => district.state_name_english === newState)
      .map(district => district.district_name_english)
      .sort((a, b) => a.localeCompare(b)); 
    districtOptions.value = filtered;
  } else {
    districtOptions.value = []; // Clear districts if no state is selected
  }
});

// NEW: Watch for changes in form.toBank for autocomplete suggestions
watch(() => form.toBank, (newBankInput) => {
  activeSuggestionIndex.value = -1; // Reset active suggestion
  if (newBankInput.length > 2) { // Start suggesting after 2 characters
    const query = newBankInput.toLowerCase();
    bankSuggestions.value = allBanks.value
      .filter(bankName => bankName.toLowerCase().includes(query))
      .slice(0, 7); // Limit to 7 suggestions
    showBankSuggestions.value = bankSuggestions.value.length > 0;
  } else {
    bankSuggestions.value = [];
    showBankSuggestions.value = false;
  }
});

// NEW: Autocomplete Event Handlers
const selectSuggestion = (suggestion) => {
  form.toBank = suggestion;
  showBankSuggestions.value = false; // Hide suggestions after selection
  bankSuggestions.value = []; // Clear suggestions
};

const onBankInputFocus = () => {
  // If there's already input, show suggestions again on focus
  if (form.toBank.length > 2 && bankSuggestions.value.length > 0) {
    showBankSuggestions.value = true;
  }
};

const onBankInputBlur = () => {
  // Use a timeout to allow click event on suggestion to register before hiding
  setTimeout(() => {
    showBankSuggestions.value = false;
  }, 150); 
};

const onBankInputKeydown = (event) => {
  if (!showBankSuggestions.value || bankSuggestions.value.length === 0) return;

  if (event.key === 'ArrowDown') {
    event.preventDefault(); // Prevent cursor from moving
    activeSuggestionIndex.value = (activeSuggestionIndex.value + 1) % bankSuggestions.value.length;
  } else if (event.key === 'ArrowUp') {
    event.preventDefault(); // Prevent cursor from moving
    activeSuggestionIndex.value = (activeSuggestionIndex.value - 1 + bankSuggestions.value.length) % bankSuggestions.value.length;
  } else if (event.key === 'Enter' && activeSuggestionIndex.value !== -1) {
    event.preventDefault(); // Prevent form submission
    selectSuggestion(bankSuggestions.value[activeSuggestionIndex.value]);
  } else if (event.key === 'Escape') {
    showBankSuggestions.value = false;
    activeSuggestionIndex.value = -1;
  }
};


function isFieldRequired(fieldName) {
  // Fields that are always non-mandatory regardless of payment mode
  if (fieldName === 'action') {
    return false;
  }

  // Static required fields as per your FastAPI endpoint
  const alwaysRequiredFields = [
    'ackNo', 'customerName', 'subCategory', 'transactionDate', 'complaintDate', 'reportDateTime',
    'state', 'district', 'policestation', 'paymentMode', 'transactionId',
    'layers', 'transactionAmount', 'disputedAmount', 'toTransactionId',
    'toAmount', 'actionTakenDate', 'toBank'
  ];

  if (alwaysRequiredFields.includes(fieldName)) {
    return true;
  }

  const mode = form.paymentMode;
  // If no mode is selected, dynamically-required fields are treated as required
  if (!mode) return true;

  const rulesForMode = nonMandatoryRules[mode];
  if (rulesForMode && rulesForMode.includes(fieldName)) {
    return false; // The field is listed as non-mandatory for this mode
  }
  
  // Default to required if no specific rule makes it non-mandatory for the current mode.
  return true;
}


// Watchers to clear errors on input
for (const key in form) {
  if (Object.prototype.hasOwnProperty.call(form, key)) {
    watch(() => form[key], () => {
      if (errors[key]) {
        errors[key] = '';
      }
      if (generalError.value) {
          generalError.value = '';
      }
    });
  }
}

const clearDynamicErrors = () => {
    generalError.value = '';
    const dynamicFields = ['accountNumber', 'cardNumber', 'toAccount', 'ifsc', 'toUpiId'];
    dynamicFields.forEach(field => {
        if (!isFieldRequired(field) && errors[field]) {
            errors[field] = '';
        }
    });
};

// --- MODIFIED: parseBackendErrors function ---
function parseBackendErrors(errorResponse) {
  // Clear all previous errors
  for (const key in errors) {
    delete errors[key];
  }
  generalError.value = '';

  // Check if errorResponse has the new structured 'detail'
  if (errorResponse && errorResponse.detail && typeof errorResponse.detail === 'object' && errorResponse.detail.error_code) {
    const backendErrorDetail = errorResponse.detail;

    generalError.value = backendErrorDetail.message || 'An unexpected error occurred.'; // Display overall message

    // If there are specific validation_errors (from Pydantic's RequestValidationError)
    if (backendErrorDetail.validation_errors && Array.isArray(backendErrorDetail.validation_errors)) {
      backendErrorDetail.validation_errors.forEach(err => {
        // Pydantic validation errors have loc: ['body', 'fieldName']
        if (err.loc && err.loc.length > 1 && typeof err.loc[1] === 'string') {
          const fieldName = err.loc[1];
          // Message might be "value is not a valid date (YYYY-MM-DD)" etc.
          errors[fieldName] = err.msg.charAt(0).toUpperCase() + err.msg.slice(1);
        } else {
          // Fallback for general Pydantic errors without specific fieldName
          generalError.value += (generalError.value ? '; ' : '') + (err.msg || 'Validation failed for an unknown field.');
        }
      });
    } else if (backendErrorDetail.message) {
      // If it's a backend ValueError (e.g., from validate_numeric_field)
      // The backend will send a message like "Validation Error: ... Details: ..."
      // Extract the relevant part or display as is.
      generalError.value = backendErrorDetail.message;
    }
  } else if (typeof errorResponse.detail === 'string') {
    // This handles older/simpler string-based error details
    generalError.value = errorResponse.detail;
  } else {
    // Fallback for completely unexpected error formats
    generalError.value = 'An unexpected error occurred. Please try again.';
  }
}


const onSubmit = async () => {
  // Clear all previous errors
  for (const key in errors) {
    delete errors[key];
  }
  generalError.value = '';

  let hasClientSideError = false;

  // --- Date/Time Validation ---
  const today = new Date(currentDate.value);
  const now = new Date(currentDateTime.value);

  if (form.transactionDate && new Date(form.transactionDate) > today) { errors.transactionDate = 'Transaction Date cannot be in the future.'; hasClientSideError = true; }
  if (form.complaintDate && new Date(form.complaintDate) > today) { errors.complaintDate = 'Complaint Date cannot be in the future.'; hasClientSideError = true; }
  if (form.reportDateTime && new Date(form.reportDateTime) > now) { errors.reportDateTime = 'Date & Time of Reporting/Escalation cannot be in the future.'; hasClientSideError = true; }
  if (form.actionTakenDate && new Date(form.actionTakenDate) > today) { errors.actionTakenDate = 'Action Taken Date cannot be in the future.'; hasClientSideError = true; }
  
  // --- Required Field & Type Validation ---
  if (!form.ackNo) { errors.ackNo = 'Acknowledgement No. is required.'; hasClientSideError = true; }
  if (!form.customerName) { errors.customerName = 'Customer Name is required.'; hasClientSideError = true; } // NEW: Customer Name required
  if (!form.subCategory) { errors.subCategory = 'Complaint Category is required.'; hasClientSideError = true; }
  if (!form.paymentMode) { errors.paymentMode = 'Mode of Payment is required.'; hasClientSideError = true; }
  if (!form.state) { errors.state = 'State is required.'; hasClientSideError = true; }
  if (!form.district) { errors.district = 'District is required.'; hasClientSideError = true; }
  if (!form.policestation) { errors.policestation = 'Policestation is required.'; hasClientSideError = true; }
  if (!form.transactionId) { errors.transactionId = 'Transaction Id / UTR Number is required.'; hasClientSideError = true; }
  if (!form.layers) { errors.layers = 'Layers is required.'; hasClientSideError = true; }
  
  // Amount fields validation
  if (form.transactionAmount === null || form.transactionAmount === '') {
      errors.transactionAmount = 'Transaction Amount is required.'; hasClientSideError = true;
  } else if (typeof form.transactionAmount !== 'number' || form.transactionAmount < 0) {
      errors.transactionAmount = 'Invalid Transaction Amount. Must be a non-negative number.'; hasClientSideError = true;
  }
  if (form.disputedAmount === null || form.disputedAmount === '') {
      errors.disputedAmount = 'Disputed Amount is required.'; hasClientSideError = true;
  } else if (typeof form.disputedAmount !== 'number' || form.disputedAmount < 0) {
      errors.disputedAmount = 'Invalid Disputed Amount. Must be a non-negative number.'; hasClientSideError = true;
  }
  if (!form.toBank) { errors.toBank = 'Beneficiary Bank Details is required.'; hasClientSideError = true; }
  if (!form.toTransactionId) { errors.toTransactionId = 'Beneficiary Transaction Id / UTR Number is required.'; hasClientSideError = true; }
  if (form.toAmount === null || form.toAmount === '') {
      errors.toAmount = 'Money transfer TO Amount (Transaction Amount) is required.'; hasClientSideError = true;
  } else if (typeof form.toAmount !== 'number' || form.toAmount < 0) {
      errors.toAmount = 'Invalid Money transfer TO Amount. Must be a non-negative number.'; hasClientSideError = true;
  }

  // Check dynamically required fields
  const dynamicCheckFields = ['accountNumber', 'cardNumber', 'toAccount', 'ifsc', 'toUpiId'];
  dynamicCheckFields.forEach(field => {
      if (isFieldRequired(field) && (form[field] === null || form[field] === '')) {
          // Adjust message for clarity based on field name
          const displayName = field.replace(/([A-Z])/g, ' $1').trim().replace('to Upi Id', 'UPI Id').replace('to Account', 'Beneficiary Account Number').replace('Ifsc', 'IFSC Code');
          errors[field] = `${displayName} is required for this payment mode.`;
          hasClientSideError = true;
      }
  });

  // --- Account Number and Card Number Length Validation ---
  if (isFieldRequired('accountNumber') && form.accountNumber) {
    const accountNumberStr = String(form.accountNumber);
    if (accountNumberStr.length < 9 || accountNumberStr.length > 18) {
      errors.accountNumber = 'Victim Account Number must be between 9 and 18 digits.';
      hasClientSideError = true;
    } else if (!/^\d+$/.test(accountNumberStr)) {
      errors.accountNumber = 'Victim Account Number must contain only digits.';
      hasClientSideError = true;
    }
  }

  if (isFieldRequired('cardNumber') && form.cardNumber) {
    const cardNumberStr = String(form.cardNumber);
    if (cardNumberStr.length < 12 || cardNumberStr.length > 19) {
      errors.cardNumber = 'Victim Card Number must be between 12 and 19 digits.';
      hasClientSideError = true;
    } else if (!/^\d+$/.test(cardNumberStr)) {
      errors.cardNumber = 'Victim Card Number must contain only digits.';
      hasClientSideError = true;
    }
  }

  // --- NEW: UPI ID @ Symbol Validation ---
  if (isFieldRequired('toUpiId') && form.toUpiId) {
    if (!form.toUpiId.includes('@')) {
      errors.toUpiId = 'UPI Id must contain an "@" symbol.';
      hasClientSideError = true;
    }
  }

  // IFSC Validation on Submit
  if (isFieldRequired('ifsc') && form.ifsc) { // Only validate if IFSC is required and provided
    try {
      const ifscValidationResponse = await axios.get(`${IFSC_VALIDATION_API_BASE_URL}${form.ifsc}`);
      
      // Check if Razorpay API returned a specific error (e.g., BAD_REQUEST)
      if (ifscValidationResponse.data && ifscValidationResponse.data.code && ifscValidationResponse.data.code === 'BAD_REQUEST') {
        errors.ifsc = ifscValidationResponse.data.message || 'Invalid IFSC Code.';
        hasClientSideError = true;
      } 
      // Check for a valid bank name in the response (a sign of successful validation)
      else if (!ifscValidationResponse.data.BANK) { 
         errors.ifsc = 'Could not validate IFSC Code. Please check or enter manually.';
         hasClientSideError = true;
      } 
      // NEW LOGIC: If IFSC is valid and a BANK property is returned
      else {
        const validatedBankName = ifscValidationResponse.data.BANK;
        
        // Scenario 1: User did NOT fill the bank name, so autofill it
        if (!form.toBank) {
          form.toBank = validatedBankName;
        } 
        // Scenario 2: User DID fill the bank name, check for mismatch
        else if (form.toBank.toLowerCase() !== validatedBankName.toLowerCase()) {
          errors.toBank = `Bank name mismatch: IFSC code corresponds to "${validatedBankName}". Please correct the bank name or IFSC.`;
          hasClientSideError = true;
        }
      }

    } catch (error) {
      console.error('IFSC Validation API error:', error);
      // For network errors or API being down
      errors.ifsc = 'Failed to validate IFSC Code. Please check your network or try again.';
      hasClientSideError = true;
    }
  }
  
  // --- END NEW Validation ---

  if (hasClientSideError) {
    return; // Stop submission if any client-side validation failed
  }

  const formData = new FormData();

  for (const key in form) {
      formData.append(key, form[key] === null ? '' : form[key]);
    }

  try {
    await axios.post(
      'http://34.47.219.225:9000/api/case-entry',
      formData
    );
    alert('Case submitted successfully.');
    onReset();
  } catch (error) {
    console.error('Submission error:', error.response?.data || error.message);
    if (error.response && error.response.data) {
      parseBackendErrors(error.response.data);
    } else {
      generalError.value = 'Failed to submit case. Network error or server unreachable.';
    }
  }
};

const onReset = () => {
  for (const key in form) {
    const fieldType = typeof form[key];
    if (fieldType === 'number') {
      form[key] = null;
    } else if (fieldType === 'object' && form[key] !== null) {
      form[key] = null;
    } else {
      form[key] = '';
    }
  }
  districtOptions.value = []; 
  bankSuggestions.value = []; // NEW: Clear bank suggestions on reset
  showBankSuggestions.value = false; // NEW: Hide suggestions on reset
  activeSuggestionIndex.value = -1; // NEW: Reset active index

  for (const key in errors) {
    delete errors[key];
  }
  generalError.value = '';
};

</script>

<style scoped>
/* Full Screen Form Container */
.i4c-form-container {
  height: 100vh;
  width: calc(100vw - 250px); /* Account for sidebar width */
  margin-left: 250px; /* Shift content to the right of sidebar */
  background: #f8f9fa;
  padding: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
  align-items: flex-start; /* Align to left for full width usage */
  justify-content: flex-start;
  overflow: auto; /* Allow scrolling if content overflows */
  position: relative;
  box-sizing: border-box;
  min-width: 0;
}

/* Progress Bar Container */
.progress-container {
  position: fixed;
  top: 0;
  left: 250px;
  right: 0;
  background: #ffffff;
  border-bottom: 1px solid #e9ecef;
  z-index: 100;
  padding: 0.75rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Progress Bar */
.progress-bar {
  flex-grow: 1;
  height: 4px;
  background: #e9ecef;
  border-radius: 2px;
  overflow: hidden;
  max-width: 300px;
}

.progress-fill {
  height: 100%;
  background: #212529;
  border-radius: 2px;
  transition: width 0.3s ease-in-out;
}

.step-indicators {
  display: flex;
  gap: 1.5rem;
  align-items: center;
  flex-shrink: 0;
}

.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  opacity: 0.5;
  transition: all 0.3s ease;
}

.step-indicator.active {
  opacity: 1;
}

.step-indicator.completed {
  opacity: 0.8;
}

.step-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #212529;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.85rem;
  box-shadow: 0 2px 4px rgba(33, 37, 41, 0.2);
}

.step-indicator.completed .step-number {
  background: #6c757d;
}

.step-title {
  font-size: 0.7rem;
  font-weight: 500;
  color: #495057;
  text-align: center;
  white-space: nowrap;
}

/* Adjust when sidebar is collapsed */
.sidebar-ui.collapsed ~ .i4c-form-container {
  margin-left: 70px;
}

.sidebar-ui.collapsed ~ .i4c-form-container .progress-container {
  left: 70px;
}

/* Form Container */
.i4c-form-container {
  margin-left: 0px;
  height: 100vh;
  background: #f8f9fa;
  padding-top: 80px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* Form Wrapper */
.form-wrapper {
  flex: 1;
  padding: 3rem;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
}

/* Error Banner */
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
  box-shadow: 0 2px 4px rgba(220, 53, 69, 0.1);
}

.error-banner i {
  font-size: 1.1rem;
}

/* Step Content */
.step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

/* Step Header */
.step-header {
  margin-bottom: 1.5rem;
  padding: 0 0.5rem;
}

.step-header h2 {
  font-size: 1.4rem;
  font-weight: 600;
  color: #212529;
  margin-bottom: 0.25rem;
}

.step-header p {
  color: #6c757d;
  font-size: 0.9rem;
}

/* Form Grid */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
  padding: 0 0.5rem;
  align-content: start;
}

/* Form Groups */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin: 0;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

/* Labels */
.form-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.required {
  color: #dc3545;
  font-weight: 700;
  font-size: 1rem;
}

/* Inputs */
.form-input,
.form-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
  background: #fff;
  height: 36px;
}

.form-input:focus,
.form-select:focus {
  border-color: #212529;
  outline: none;
}

.form-input.error,
.form-select.error {
  border-color: #dc3545;
}

.form-input::placeholder {
  color: #6c757d;
}

/* Amount Input */
.amount-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.currency-symbol {
  position: absolute;
  left: 1rem;
  color: #495057;
  font-weight: 600;
  z-index: 1;
}

.amount-input {
  padding-left: 2.5rem;
}

/* Error Text */
.error-text {
  color: #dc3545;
  font-size: 0.85rem;
  font-weight: 500;
  margin-top: 0.25rem;
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
  border: 2px solid #e9ecef;
  border-top: none;
  border-radius: 0 0 8px 8px;
  max-height: 200px;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  list-style: none;
  padding: 0;
  margin: 0;
}

.suggestions-list li {
  padding: 0.875rem 1rem;
  cursor: pointer;
  font-size: 1rem;
  color: #212529;
  transition: all 0.2s ease;
  border-bottom: 1px solid #f8f9fa;
}

.suggestions-list li:last-child {
  border-bottom: none;
}

.suggestions-list li:hover,
.suggestions-list li.active {
  background: #212529;
  color: white;
}

/* Navigation Buttons */
.form-navigation {
  display: flex;
  justify-content: space-between;
  padding: 1rem 1rem 0;
  margin-top: 1rem;
  border-top: 1px solid #e9ecef;
}

.nav-button {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 100px;
  justify-content: center;
}

.nav-button.prev {
  background: #e9ecef;
  color: #495057;
  border: none;
}

.nav-button.next {
  background: #212529;
  color: #fff;
  border: none;
}

.nav-button:hover {
  transform: translateY(-1px);
}

.nav-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .form-wrapper {
    width: 95%;
    padding: 1.5rem;
  }
  
  .form-grid {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
  }
}

@media (max-width: 768px) {
  .i4c-form-container {
    padding: 0;
  }
  
  .progress-container {
    padding: 0.75rem 1rem;
    gap: 1rem;
  }
  
  .step-indicators {
    gap: 1rem;
  }
  
  .step-number {
    width: 28px;
    height: 28px;
    font-size: 0.8rem;
  }
  
  .step-title {
    font-size: 0.65rem;
  }
  
  .form-wrapper {
    width: 98%;
    padding: 1rem;
    margin-top: 70px;
    height: calc(100vh - 100px);
  }
  
  .step-header h2 {
    font-size: 1.5rem;
  }
  
  .step-header p {
    font-size: 0.9rem;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .navigation-buttons {
    flex-direction: column;
    gap: 1rem;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .progress-container {
    padding: 0.5rem 0.75rem;
  }
  
  .step-indicators {
    gap: 0.5rem;
  }
  
  .step-number {
    width: 24px;
    height: 24px;
    font-size: 0.7rem;
  }
  
  .step-title {
    font-size: 0.6rem;
  }
  
  .form-wrapper {
    width: 100%;
    padding: 1rem;
    margin-top: 60px;
    border-radius: 0;
    height: calc(100vh - 80px);
  }
  
  .step-header h2 {
    font-size: 1.25rem;
  }
  
  .step-header p {
    font-size: 0.8rem;
  }
  
  .form-input,
  .form-select {
    padding: 0.75rem 0.875rem;
    font-size: 0.9rem;
  }
  
  .btn-primary,
  .btn-secondary {
    padding: 0.75rem 1.5rem;
    font-size: 0.9rem;
  }
}

/* Animation for step transitions */
.step-content {
  animation: fadeInUp 0.4s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Hover effects */
.form-group:hover .form-label {
  color: #212529;
}

.form-input:hover:not(:focus) {
  border-color: #adb5bd;
  background: #f8f9fa;
}

.form-select:hover:not(:focus) {
  border-color: #adb5bd;
  background: #f8f9fa;
}

/* Custom scrollbar for step content */
.step-content::-webkit-scrollbar {
  width: 6px;
}

.step-content::-webkit-scrollbar-track {
  background: #f1f3f4;
  border-radius: 3px;
}

.step-content::-webkit-scrollbar-thumb {
  background: #c1c7cd;
  border-radius: 3px;
}

.step-content::-webkit-scrollbar-thumb:hover {
  background: #a8b0b8;
}
</style>