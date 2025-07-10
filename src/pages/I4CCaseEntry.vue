<template>
  <div class="form-bg">
    <form class="entry-card grouped-form" @submit.prevent="onSubmit">
      <h2 class="form-title">I4C Fraud Complaint Entry</h2>
      
      <div v-if="generalError" class="error-message general-error span-all">
        {{ generalError }}
      </div>

      <div class="section-grid">
        <span class="section-heading span-all">Complaint related information</span> 
        <label :class="{ 'has-error': errors.ackNo }">
          <span class="label-text-wrapper">Acknowledgement No.<span class="required-star">*</span></span>
          <input v-model="form.ackNo" type="text" required />
          <span v-if="errors.ackNo" class="error-message">{{ errors.ackNo }}</span>
        </label>

        <label :class="{ 'has-error': errors.customerName }">
          <span class="label-text-wrapper">Customer Name<span class="required-star">*</span></span> 
          <input v-model="form.customerName" type="text" required />
          <span v-if="errors.customerName" class="error-message">{{ errors.customerName }}</span>
        </label>
        <label :class="{ 'has-error': errors.subCategory }">
          <span class="label-text-wrapper">Complaint Category<span class="required-star">*</span></span>
          <select v-model="form.subCategory" required>
            <option disabled value="">Select Sub Category</option>
            <option v-for="option in subCategoryOptions" :key="option" :value="option">{{ option }}</option>
          </select>
          <span v-if="errors.subCategory" class="error-message">{{ errors.subCategory }}</span>
        </label>
        <label :class="{ 'has-error': errors.complaintDate }">
          <span class="label-text-wrapper">Complaint Date<span class="required-star">*</span></span>
          <input v-model="form.complaintDate" type="date" :max="currentDate" required />
          <span v-if="errors.complaintDate" class="error-message">{{ errors.complaintDate }}</span>
        </label>
        <label :class="{ 'has-error': errors.reportDateTime }">
          <span class="label-text-wrapper">Date & Time of Reporting / Escalation<span class="required-star">*</span></span>
          <input v-model="form.reportDateTime" type="datetime-local" :max="currentDateTime" required />
          <span v-if="errors.reportDateTime" class="error-message">{{ errors.reportDateTime }}</span>
        </label>
        <label :class="{ 'has-error': errors.state }">
  <span class="label-text-wrapper">State<span class="required-star">*</span></span>
  <select v-model="form.state" required>
    <option disabled value="">Select State</option>
    <option v-for="st in stateOptions" :key="st" :value="st">{{ st }}</option>
  </select>
  <span v-if="errors.state" class="error-message">{{ errors.state }}</span>
</label>
<label :class="{ 'has-error': errors.district }">
  <span class="label-text-wrapper">District<span class="required-star">*</span></span>
  <select v-model="form.district" required>
    <option disabled value="">Select District</option>
    <option v-for="districtName in districtOptions" :key="districtName" :value="districtName">{{ districtName }}</option>
  </select>
  <span v-if="errors.district" class="error-message">{{ errors.district }}</span>
</label>
        <label :class="{ 'has-error': errors.policestation }">
          <span class="label-text-wrapper">Policestation<span class="required-star">*</span></span>
          <input v-model="form.policestation" type="text" required />
          <span v-if="errors.policestation" class="error-message">{{ errors.policestation }}</span>
        </label>

        <span class="section-heading span-all">Transaction Related Information</span> 
        <label :class="{ 'has-error': errors.paymentMode }">
          <span class="label-text-wrapper">Mode of Payment<span class="required-star">*</span></span>
          <select v-model="form.paymentMode" required @change="clearDynamicErrors">
            <option disabled value="">Select Mode of Payment</option>
            <option v-for="mode in paymentModeOptions" :key="mode" :value="mode">{{ mode }}</option>
          </select>
          <span v-if="errors.paymentMode" class="error-message">{{ errors.paymentMode }}</span>
        </label>

        <label :class="{ 'has-error': errors.transactionDate }">
          <span class="label-text-wrapper">Transaction Date<span class="required-star">*</span></span>
          <input v-model="form.transactionDate" type="date" :max="currentDate" required />
          <span v-if="errors.transactionDate" class="error-message">{{ errors.transactionDate }}</span>
        </label>
        
        <label :class="{ 'has-error': errors.transactionId }">
          <span class="label-text-wrapper">Transaction Id / UTR Number<span class="required-star">*</span></span>
          <input v-model="form.transactionId" type="text" required />
          <span v-if="errors.transactionId" class="error-message">{{ errors.transactionId }}</span>
        </label>

        <label :class="{ 'has-error': errors.accountNumber }">
          <span class="label-text-wrapper">Victim Account Number<span v-if="isFieldRequired('accountNumber')" class="required-star">*</span></span>
          <input
            v-model="form.accountNumber"
            type="number"
            pattern="\d*"
            title="Please enter only numbers"
            :required="isFieldRequired('accountNumber')"
            minlength="9"
            maxlength="18"
          />
          <span v-if="errors.accountNumber" class="error-message">{{ errors.accountNumber }}</span>
        </label>
        <label :class="{ 'has-error': errors.cardNumber }">
          <span class="label-text-wrapper">Victim Card Number<span v-if="isFieldRequired('cardNumber')" class="required-star">*</span></span>
          <input
            v-model="form.cardNumber"
            type="number"
            pattern="\d*"
            title="Please enter only numbers"
            :required="isFieldRequired('cardNumber')"
            minlength="12"
            maxlength="19"
          />
          <span v-if="errors.cardNumber" class="error-message">{{ errors.cardNumber }}</span>
        </label>
        <label :class="{ 'has-error': errors.transactionAmount }">
          <span class="label-text-wrapper">Transaction Amount<span class="required-star">*</span></span>
          <input v-model.number="form.transactionAmount" type="number" min="0" step="any" required />
          <span v-if="errors.transactionAmount" class="error-message">{{ errors.transactionAmount }}</span>
        </label>
        <label :class="{ 'has-error': errors.disputedAmount }">
          <span class="label-text-wrapper">Disputed Amount<span class="required-star">*</span></span>
          <input v-model.number="form.disputedAmount" type="number" min="0" step="any" required />
          <span v-if="errors.disputedAmount" class="error-message">{{ errors.disputedAmount }}</span>
        </label>
        <label :class="{ 'has-error': errors.layers }">
          <span class="label-text-wrapper">Layers<span class="required-star">*</span></span>
          <select v-model="form.layers" required>
            <option value="">Select Layer</option>
            <option v-for="n in 30" :key="n" :value="`Layer ${n}`">Layer {{ n }}</option>
          </select>
          <span v-if="errors.layers" class="error-message">{{ errors.layers }}</span>
        </label>

        <span class="section-heading span-all">Beneficiary Details</span> 
        <label :class="{ 'has-error': errors.toBank }">
          <span class="label-text-wrapper">Beneficiary Bank Details<span class="required-star">*</span></span>
          <div class="autocomplete-container"> <input
              v-model="form.toBank"
              type="text"
              required
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
          <span v-if="errors.toBank" class="error-message">{{ errors.toBank }}</span>
        </label>

        <label :class="{ 'has-error': errors.toAccount }">
          <span class="label-text-wrapper">Beneficiary Account Number<span v-if="isFieldRequired('toAccount')" class="required-star">*</span></span>
          <input v-model="form.toAccount" type="number" pattern="\d*" title="Please enter only numbers" :required="isFieldRequired('toAccount')" />
          <span v-if="errors.toAccount" class="error-message">{{ errors.toAccount }}</span>
        </label>
        <label :class="{ 'has-error': errors.ifsc }">
          <span class="label-text-wrapper">IFSC Code <span v-if="isFieldRequired('ifsc')" class="required-star">*</span></span>
          <input
            v-model="form.ifsc"
            type="text"
            :required="isFieldRequired('ifsc')"
            :disabled="!form.toBank" placeholder="e.g., ICIC0000001"
          />
          <span v-if="errors.ifsc" class="error-message">{{ errors.ifsc }}</span>
        </label>
        <label :class="{ 'has-error': errors.toTransactionId }">
          <span class="label-text-wrapper">Transaction Id / UTR Number<span class="required-star">*</span></span>
          <input v-model="form.toTransactionId" type="text" required/>
          <span v-if="errors.toTransactionId" class="error-message">{{ errors.toTransactionId }}</span>
        </label>
        <label :class="{ 'has-error': errors.toAmount }">
          <span class="label-text-wrapper">Transaction Amount<span class="required-star">*</span></span>
          <input v-model.number="form.toAmount" type="number" min="0" step="any" required/>
          <span v-if="errors.toAmount" class="error-message">{{ errors.toAmount }}</span>
        </label>
        <label :class="{ 'has-error': errors.toUpiId }">
          <span class="label-text-wrapper">UPI Id<span v-if="isFieldRequired('toUpiId')" class="required-star">*</span></span>
          <input v-model="form.toUpiId" type="text" :required="isFieldRequired('toUpiId')" />
          <span v-if="errors.toUpiId" class="error-message">{{ errors.toUpiId }}</span>
        </label>
        
        <span class="section-heading span-all">Action</span> 
        <label :class="{ 'has-error': errors.action }">
          Action
          <select v-model="form.action">
            <option value="">Select Action</option>
            <option v-for="opt in actionOptions" :key="opt" :value="opt">{{ opt }}</option>
          </select>
          <span v-if="errors.action" class="error-message">{{ errors.action }}</span>
        </label>
        
        <label :class="{ 'has-error': errors.actionTakenDate }">
          <span class="label-text-wrapper">Action Taken Date<span class="required-star">*</span></span>
          <input v-model="form.actionTakenDate" type="date" :max="currentDate" required/>
          <span v-if="errors.actionTakenDate" class="error-message">{{ errors.actionTakenDate }}</span>
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
/* Main Form Container */
.form-bg {
  display: flex;
  justify-content: center;
  align-items: flex-start; /* Align to start to prevent form from being too high */
  min-height: 100vh;
  padding: 40px 20px; /* More vertical padding */
  background: linear-gradient(135deg, #f0f2f5 0%, #e0e6ed 100%); /* Lighter, subtle gradient */
}

.entry-card {
  background-color: #ffffff;
  padding: 60px; /* More generous padding */
  border-radius: 20px; /* Even softer corners */
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.1); /* More diffused shadow */
  width: 100%;
  max-width: 1300px; /* Keep max-width same */
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 35px; /* Increased gap */
  border: 1px solid #e9eef2; /* Very subtle border */
  margin-top: 40px; /* Push it down slightly from the top */
  margin-bottom: 40px; /* Ensure space at bottom */
}

/* Form Title */
.form-title {
  grid-column: 1 / -1;
  text-align: center;
  color: #2F5892; /* Slightly darker primary blue for title */
  margin-bottom: 50px; /* More space below title */
  font-size: 2.8em; /* Larger font size */
  font-weight: 800;
  padding-bottom: 25px;
  position: relative;
  letter-spacing: -0.8px;
}
.form-title::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 0; 
  transform: translateX(-50%);
  width: 100px; /* A more prominent underline effect */
  height: 4px; /* Thicker underline */
  background-color: #3F72AF; /* Primary blue */
  border-radius: 2px;
}

/* Section Headings */
.section-heading {
  grid-column: 1 / -1;
  font-size: 1.5em; /* Larger section heading */
  font-weight: 700;
  color: #4A5568; 
  margin-top: 45px; 
  margin-bottom: 25px;
  padding-bottom: 10px;
  border-bottom: 2px solid #E0E0E0; /* Slightly thicker border */
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}
.section-heading::before {
    content: '';
    position: absolute;
    left: -20px; /* Adjust as needed for alignment */
    top: 50%;
    transform: translateY(-50%);
    width: 8px; /* Vertical accent bar */
    height: 100%;
    background-color: #3F72AF; /* Primary blue accent */
    border-radius: 4px;
}


/* Form Labels and Inputs */
.grouped-form label {
  display: flex; /* Keeps label as a flex container */
  flex-direction: column; /* Stacks the label content (text+star) above the input */
  font-weight: 500;
  color: #555;
  gap: 8px; /* Space between the label text/star block and the input field */
  position: relative; 
}

/* New rule for the label-text-wrapper to ensure inline flow */
.grouped-form label .label-text-wrapper {
    display: inline; /* Crucial: Ensures text and asterisk stay on the same line */
    white-space: nowrap; /* Prevents line breaks within the label text and star */
}

.grouped-form input[type="text"],
.grouped-form input[type="date"],
.grouped-form input[type="datetime-local"],
.grouped-form input[type="number"],
.grouped-form select,
.grouped-form textarea {
  width: 100%;
  padding: 16px; /* More padding */
  border: 1px solid #D1D5DB; /* Lighter border color */
  border-radius: 10px; /* Softer corners */
  font-size: 1.05rem; /* Slightly larger font */
  color: #333;
  background-color: #F8F9FA; /* Slightly more noticeable off-white background */
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  box-sizing: border-box;
}

.grouped-form input[type="text"]:focus,
.grouped-form input[type="date"]:focus,
.grouped-form input[type="datetime-local"]:focus,
.grouped-form input[type="number"]:focus,
.grouped-form select:focus,
.grouped-form textarea:focus {
  border-color: #3F72AF; 
  box-shadow: 0 0 0 5px rgba(63, 114, 175, 0.25); /* Stronger, softer blue glow */
  outline: none;
}

.grouped-form textarea {
  min-height: 100px; /* Taller textarea */
  resize: vertical;
}

/* Section Grid (nested within entry-card) */
.section-grid {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px; /* Consistent gap */
}

.span-all {
  grid-column: 1 / -1;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  justify-content: center; /* Center buttons */
  gap: 25px; /* More space between buttons */
  margin-top: 50px; 
  padding-top: 30px;
  border-top: 1px solid #E0E0E0;
}

.submit-btn,
.reset-btn {
  padding: 18px 40px; /* Larger buttons */
  border: none;
  border-radius: 10px; /* Softer corners */
  font-size: 1.15rem; /* Larger font */
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1); /* Clearer shadow */
}

.submit-btn {
  background-color: #3F72AF; 
  color: white;
}

.submit-btn:hover {
  background-color: #2F5892; /* Darker blue on hover */
  transform: translateY(-3px); /* More pronounced lift */
  box-shadow: 0 8px 20px rgba(63, 114, 175, 0.35); /* Stronger shadow on hover */
}

.reset-btn {
  background-color: #E2E8F0; /* Lighter gray for reset */
  color: #4A5568; /* Darker text for reset button */
}

.reset-btn:hover {
  background-color: #CBD5E0; /* Darker gray on hover */
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(160, 174, 192, 0.35);
}

/* Error and Required Star Styles */
.error-message {
  color: #E53E3E; 
  font-size: 0.95em; /* Slightly larger error text */
  margin-top: 6px; 
  display: block;
  font-weight: 500;
}

.general-error {
  text-align: center;
  font-weight: 600;
  padding: 18px; /* More padding */
  background-color: #FEF2F2; /* Very light red background */
  border: 1px solid #FC8181; /* Slightly darker red border */
  border-radius: 8px;
  margin-bottom: 30px; /* More space */
  color: #C53030; /* Darker red text */
}

/* The critical correction for the red star */
.required-star {
  color: #E53E3E; 
  font-weight: bold;
  font-size: 1.1em; 
  margin-left: 0px; /* Crucial: No margin-left for it to touch the text */
  vertical-align: top; /* Align it slightly higher with the text for a superscript effect */
  display: inline; /* Ensure it behaves as inline text */
}


label.has-error input,
label.has-error select,
label.has-error textarea {
  border-color: #E53E3E; 
  box-shadow: 0 0 0 5px rgba(229, 62, 62, 0.25); 
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .entry-card {
    padding: 40px;
    max-width: 900px;
  }
  .form-title {
    font-size: 2.4em;
  }
  .section-heading::before {
    left: -15px; 
  }
}

@media (max-width: 768px) {
  .entry-card {
    padding: 25px;
    grid-template-columns: 1fr; /* Stack columns on smaller screens */
    gap: 25px;
  }

  .form-title {
    font-size: 2em;
    margin-bottom: 35px;
    padding-bottom: 20px;
  }
  .form-title::after {
      width: 80px;
      height: 3px;
  }

  .section-heading {
    font-size: 1.3em;
    margin-top: 30px;
    margin-bottom: 20px;
  }
  .section-heading::before {
    width: 6px;
    left: -10px;
  }

  .action-buttons {
    flex-direction: column;
    align-items: stretch;
    gap: 18px;
    margin-top: 35px;
  }

  .submit-btn,
  .reset-btn {
    width: 100%;
    padding: 15px 30px;
    font-size: 1.05rem;
  }

  /* No specific required-star adjustments needed for responsiveness in this setup */
}

@media (max-width: 480px) {
    .entry-card {
        padding: 20px;
        border-radius: 15px;
    }
    .form-title {
        font-size: 1.8em;
        margin-bottom: 25px;
        padding-bottom: 15px;
    }
    .form-title::after {
        width: 60px;
        height: 2px;
    }
    .section-heading {
        font-size: 1.2em;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    .section-heading::before {
        width: 4px;
        left: -8px;
    }
    .grouped-form input,
    .grouped-form select,
    .grouped-form textarea {
        padding: 12px;
        font-size: 0.95rem;
        border-radius: 8px;
    }
    .error-message {
        font-size: 0.85em;
    }
    .submit-btn, .reset-btn {
        padding: 12px 25px;
        font-size: 1rem;
        border-radius: 8px;
    }
}
/* ... (Existing styles for form-bg, entry-card, form-title, section-heading, labels, inputs, etc.) ... */

/* NEW: Autocomplete Styles */
.autocomplete-container {
  position: relative; /* Crucial for positioning the suggestion list */
  width: 100%;
}

.suggestions-list {
  position: absolute;
  top: 100%; /* Position below the input field */
  left: 0;
  right: 0;
  z-index: 100; /* Ensure it appears above other elements */
  background-color: #fff;
  border: 1px solid #D1D5DB;
  border-top: none; /* Optical trick: makes it look connected to the input */
  border-radius: 0 0 10px 10px; /* Rounded bottom corners */
  max-height: 200px; /* Limit height and make it scrollable */
  overflow-y: auto;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  list-style: none; /* Remove bullet points */
  padding: 0;
  margin: 0;
}

.suggestions-list li {
  padding: 12px 16px;
  cursor: pointer;
  font-size: 1rem;
  color: #333;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.suggestions-list li:hover,
.suggestions-list li.active {
  background-color: #F0F8FF; /* Light blue background for hover/active */
  color: #3F72AF; /* Primary blue text for hover/active */
}

/* Ensure border-radius for input is maintained */
.autocomplete-container input {
    border-radius: 10px; /* Keep consistent rounding for input */
}

/* Adjust input border if suggestions are shown to make it look connected */
.autocomplete-container input:focus + .suggestions-list {
    border-top: 1px solid #3F72AF; /* Add top border on focus if list is shown */
}

/* When suggestions are visible, sometimes you want to flatten the bottom border of the input */
.autocomplete-container input:focus:not(:placeholder-shown),
.autocomplete-container input.has-suggestions { /* Add a class 'has-suggestions' via JS if needed, or rely on v-if */
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
}

.label.has-error input,
.label.has-error select,
.label.has-error textarea {
  border-color: #E53E3E; /* Red border */
  box-shadow: 0 0 0 5px rgba(229, 62, 62, 0.25); /* Red glow */
}
.error-message {
  color: #E53E3E; /* Red text for error messages */
  font-size: 0.95em;
  margin-top: 6px;
  display: block;
  font-weight: 500;
}

/* ... (Remaining existing styles) ... */
</style>