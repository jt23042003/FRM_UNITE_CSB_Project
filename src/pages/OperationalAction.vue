<template>
  <div class="action-page-bg">
    <h1 class="screen-header">Victim Match Report - I4C Operational Response tracking</h1>

    <div v-if="loading" class="loading-container">Loading Case Data...</div>
    <div v-else-if="error" class="error-container">{{ error }}</div>

    <div v-else class="content-wrapper">
      <section class="card-section">
        <div class="side-by-side-container">
          <div class="profile-column">
            <h3 class="column-header">Customer Details - I4C</h3>
            <table class="inner-details-table">
              <thead>
                <tr><th>Name</th><th>Mobile Number</th><th>Bank A/c #</th><th>Email</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ riskEntity.i4c.name || '-' }}</td>
                  <td>{{ riskEntity.i4c.mobileNumber || '-' }}</td>
                  <td>{{ riskEntity.i4c.bankAc || '-' }}</td>
                  <td>{{ riskEntity.i4c.email || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="profile-column">
<h3 class="column-header">Customer Details - Bank</h3>

<table class="inner-details-table">
  <thead>
    <tr>
      <th>Name</th>
      <th>Mobile Number</th>
      <th>Bank A/c #</th>
      <th>Email</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td :class="{ 'highlight-match': isMatched('name') }">{{ riskEntity.bank.name || '-' }}</td>
      <td :class="{ 'highlight-match': isMatched('mobileNumber') }">{{ riskEntity.bank.mobileNumber || '-' }}</td>
      <td :class="{ 'highlight-match': isMatched('bankAc') }">{{ riskEntity.bank.bankAc || '-' }}</td>
      <td :class="{ 'highlight-match': isMatched('email') }">{{ riskEntity.bank.email || '-' }}</td>
    </tr>
  </tbody>
</table>

<div class="separator-row-full"></div>

<table class="inner-details-table">
  <thead>
    <tr>
      <th>Customer ID</th>
      <th>AQB</th>
      <th>Avail. Bal.</th>
      <th>Product Code</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>{{ riskEntity.bank.customerId || '-' }}</td>
      <td>{{ riskEntity.bank.aqb || '-' }}</td>
      <td>{{ riskEntity.bank.availBal || '-' }}</td>
      <td>{{ riskEntity.bank.productCode || '-' }}</td>
    </tr>
  </tbody>
</table>

<div class="separator-row-full"></div>

<table class="inner-details-table">
  <thead>
    <tr>
      <th>Rel. Value</th>
      <th>MOB / Vintage</th>
      <th>A/c Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>{{ riskEntity.bank.relValue || '-' }}</td>
      <td>{{ riskEntity.bank.mobVintage || '-' }}</td>
      <td>{{ riskEntity.bank.acStatus || '-' }}</td>
    </tr>
  </tbody>
</table>

</div>
        </div>
      </section>

      <section class="card-section">
<h2>Action</h2>

<div v-if="caseStatus !== 'Closed'">
  <div class="i4c-requirements-table-container">
    <h4>I4C Requirements</h4>
    <table class="details-table">
      <thead>
        <tr>
          <th style="width: 10%;">S.No.</th>
          <th>Documents</th>
          <th style="width: 20%; text-align: center;">Check Box</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(doc, index) in i4cRequirements" :key="doc.id">
          <td>{{ index + 1 }}</td>
          <td>{{ doc.name }}</td>
          <td style="text-align: center;">
            <input type="checkbox" v-model="doc.checked" class="action-checkbox"/>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  
  <div class="action-form-grid">
    <label for="proof-upload">Proof of upload:</label>
    <input 
      id="proof-upload" 
      type="text" 
      v-model="proofOfUploadRef" 
      placeholder="Enter Ref Number" 
      class="form-input" 
    />
    
    <label for="screenshot-upload">Screen Shot:</label>
    <input id="screenshot-upload" type="file" @change="handleScreenshotUpload" class="form-input-file" />
  </div>

  <div class="action-buttons">
    <button @click="saveActionData" class="save-btn" :disabled="isSavingAction">Save</button>
    <button @click="submitActionData" class="submit-btn" :disabled="isSavingAction">Submit</button>
  </div>
</div>

<div v-else>
  <div v-if="savedActionData">
    <p class="section-subtitle">This case was closed on {{ new Date(savedActionData.submitted_at).toLocaleString() }} by {{ savedActionData.submitted_by }}.</p>
    
    <div class="history-grid">
        <strong>Documents Confirmed:</strong>
        <ul class="history-doc-list">
          <li v-for="doc in savedActionData.checked_documents" :key="doc">{{ doc }}</li>
          <li v-if="!savedActionData.checked_documents || savedActionData.checked_documents.length === 0">None</li>
        </ul>

        <strong>Proof of Upload Ref:</strong>
        <span>{{ savedActionData.proof_of_upload_ref || 'N/A' }}</span>

        <strong>Uploaded Screenshot:</strong>
        <span v-if="savedActionData.screenshot_filename">
          <a
            :href="`http://34.47.219.225:9000/api/case-document/download/${savedActionData.screenshot_filename}`"
            target="_blank"
            rel="noopener"
          >
            {{ savedActionData.screenshot_filename }}
          </a>
        </span>
        <span v-else>None</span>
    </div>
  </div>
  <div v-else class="closed-case-notice">
    Loading action history...
  </div>
</div>

</section>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter,useRoute } from 'vue-router';
import axios from 'axios';
import '../assets/OperationalAction.css'; // Assuming you have a CSS file for styling

const route = useRoute();
const router = useRouter(); // Add this line
const case_id = route.params.case_id;
const caseStatus = computed(() => route.query.status);
// Add this new state variable to your <script setup>
const savedActionData = ref(null);

// --- State Management ---
const loading = ref(true);
const error = ref('');
const riskEntity = reactive({ i4c: {}, bank: {} });
const i4cRequirements = ref([]); // Initialize as empty

const proofOfUploadRef = ref('');
const screenshotFile = ref(null);
const isSavingAction = ref(false);

// --- Helper Functions ---
function isMatched(key) {
  const i4cValue = riskEntity.i4c ? riskEntity.i4c[key] : undefined;
  const bankValue = riskEntity.bank ? riskEntity.bank[key] : undefined;
  return i4cValue && bankValue && String(i4cValue).trim() === String(bankValue).trim();
}

function handleScreenshotUpload(event) {
  const file = event.target.files[0];
  if (file) {
    screenshotFile.value = file;
  }
}

async function submitActionData() {
isSavingAction.value = true;

// 1. Get the list of checked document names
const checkedDocs = i4cRequirements.value
  .filter(doc => doc.checked)
  .map(doc => doc.name);
  
// 2. Get the filename from the selected file, if it exists
const screenshotFilename = screenshotFile.value ? screenshotFile.value.name : null;

// 3. Create a standard JSON payload with all the data
const payload = {
  case_id: case_id,
  checked_documents: checkedDocs,
  proof_of_upload_ref: proofOfUploadRef.value,
  screenshot_filename: screenshotFilename, // Sending filename only
  status: 'saved'
};

// 4. Make the POST request to the API
try {
  const response = await axios.post(
    '/api/i4c-manual-file-confirm',
    payload, // Sending the JSON payload directly
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('jwt')}`
      }
    }
  );

  if (response.data.success) {
    alert('Case submited successfully!');
    router.push('/case-details');
  } else {
    alert(`Save failed: ${response.data.message || 'Unknown error'}`);
  }

} catch (err) {
  console.error(`Error during 'save' action:`, err);
  alert(`An error occurred while saving. Please check the console.`);
} finally {
  isSavingAction.value = false;
}
}

async function saveActionData() {
isSavingAction.value = true;
const formData = new FormData();

const checkedDocs = i4cRequirements.value
  .filter(doc => doc.checked)
  .map(doc => doc.name);

formData.append('case_id', case_id);
formData.append('checked_documents', JSON.stringify(checkedDocs));
formData.append('proof_of_upload_ref', proofOfUploadRef.value);

// This is the only change needed to match your Postman test
formData.append('confirmation_action_status', 'submitted');

if (screenshotFile.value) {
  formData.append('screenshot', screenshotFile.value);
}

try {
  const response = await axios.post(
    '/api/operational-confirm',
    formData,
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('jwt')}`
      }
    }
  );

  if (response.data.success) {
    alert('Case saved successfully!');
    // router.push('/case-details');
  } else {
    alert(`Submission failed: ${response.data.message || 'Unknown error'}`);
  }

} catch (err) {
  console.error(`Error during 'submit' action:`, err);
  alert(`An error occurred during submission. Please check the console.`);
} finally {
  isSavingAction.value = false;
}
}

onMounted(async () => {
loading.value = true;
try {
  const token = localStorage.getItem('jwt');
  if (!token) {
    error.value = "Authentication token not found. Please log in.";
    loading.value = false;
    return;
  }

  // 1. Correctly destructure all three results from the API calls
  const [combinedDataRes, documentListRes, savedActionRes] = await Promise.allSettled([
    axios.get(`/api/combined-case-data/${case_id}`, { headers: { 'Authorization': `Bearer ${token}` } }),
    axios.get('/api/i4c-document-list', { headers: { 'Authorization': `Bearer ${token}` } }),
  ]);

  // --- Process combined case data result ---
  if (combinedDataRes.status === 'fulfilled' && combinedDataRes.value.data) {
    const responseData = combinedDataRes.value.data;
    const i4cData = responseData.i4c_data || {};
    const customerDetails = responseData.customer_details || {};
    
    riskEntity.i4c = { name: i4cData.customer_name, mobileNumber: i4cData.mobile, bankAc: i4cData.account_number, email: i4cData.email };
    riskEntity.bank = { name: `${customerDetails.fname || ''} ${customerDetails.mname || ''} ${customerDetails.lname || ''}`.trim(), mobileNumber: customerDetails.mobile, bankAc: responseData.acc_num, email: customerDetails.email, customerId: customerDetails.cust_id, acStatus: responseData.account_details?.acc_status, aqb: responseData.account_details?.aqb, availBal: responseData.account_details?.availBal, productCode: responseData.account_details?.productCode, relValue: customerDetails?.rel_value, mobVintage: customerDetails?.mob };
  } else {
    console.error('Failed to fetch combined case data:', combinedDataRes.reason);
    error.value = "Failed to load operational case data.";
  }

  // --- Process the document list result ---
  if (documentListRes.status === 'fulfilled' && documentListRes.value.data.success) {
    i4cRequirements.value = documentListRes.value.data.documents.map(doc => ({
      id: doc.seq_id,
      name: doc.file_name,
      checked: false
    }));
  } else {
    console.error('Failed to fetch I4C document list:', documentListRes.reason);
  }

  if (caseStatus.value === 'Closed') {
    console.log('Case is closed, fetching action log...');
    try {
      const savedActionRes = await axios.get(`http://34.47.219.225:9000/api/case/${case_id}/action-log`, { headers: { 'Authorization': `Bearer ${token}` } });
      
      if (savedActionRes.data && savedActionRes.data.success) {
        const savedData = savedActionRes.data.data;
        if (savedData) {
          // Pre-fill the form fields with the saved data
          proofOfUploadRef.value = savedData.proof_of_upload_ref || '';
          const previouslyCheckedDocs = savedData.checked_documents || [];
          i4cRequirements.value.forEach(req => {
            if (previouslyCheckedDocs.includes(req.name)) {
              req.checked = true;
            }
          });
          savedActionData.value = savedData; 
        }
      }
    } catch (logErr) {
      // This won't stop the page from loading, just log an error.
      console.warn('Could not load saved action data:', logErr);
    }
  }

} catch (err) {
  console.error(err);
  error.value = "An error occurred while loading page data.";
} finally {
  loading.value = false;
}
});
</script>