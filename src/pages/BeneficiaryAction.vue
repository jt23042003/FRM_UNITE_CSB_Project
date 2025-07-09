<template>
    <div class="action-page-bg">
      <h1 class="screen-header">Alert - Potential Mule Account</h1>
  
      <div v-if="loading" class="loading-container">Loading Case Data...</div>
      <div v-else-if="error" class="error-container">{{ error }}</div>
  
      <div v-else class="content-wrapper">
        <section class="card-section">
          <div class="side-by-side-container">
            <div class="profile-column">
              <h3 class="column-header">Customer Details - I4C</h3>
              <table class="inner-details-table">
                <thead>
                  <tr><th>Name</th><th>Mobile Number</th><th>Email</th><th>PAN</th></tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{{ riskEntity.i4c.name || '-' }}</td>
                    <td>{{ riskEntity.i4c.mobileNumber || '-' }}</td>
                    <td>{{ riskEntity.i4c.email || '-' }}</td>
                    <td>{{ riskEntity.i4c.pan || '-' }}</td>
                  </tr>
                </tbody>
              </table>
              <div class="separator-row-full"></div>
              <table class="inner-details-table">
                <thead>
                  <tr><th>Aadhaar</th><th>GST</th></tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{{ riskEntity.i4c.aadhaar || '-' }}</td>
                    <td>{{ riskEntity.i4c.gst || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
  
            <div class="profile-column">
               <h3 class="column-header">Customer Details - Bank</h3>
                <table class="inner-details-table">
                  <thead>
                    <tr><th>Name</th><th>Mobile Number</th><th>Email</th><th>PAN</th></tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td :class="{ 'highlight-match': isMatched('name') }">{{ riskEntity.bank.name || '-' }}</td>
                      <td :class="{ 'highlight-match': isMatched('mobileNumber') }">{{ riskEntity.bank.mobileNumber || '-' }}</td>
                      <td :class="{ 'highlight-match': isMatched('email') }">{{ riskEntity.bank.email || '-' }}</td>
                      <td :class="{ 'highlight-match': isMatched('pan') }">{{ riskEntity.bank.pan || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
                <div class="separator-row-full"></div>
                <table class="inner-details-table">
                   <thead>
                    <tr><th>Aadhaar</th><th>GST</th></tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td :class="{ 'highlight-match': isMatched('aadhaar') }">{{ riskEntity.bank.aadhaar || '-' }}</td>
                      <td :class="{ 'highlight-match': isMatched('gst') }">{{ riskEntity.bank.gst || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
                <div class="separator-row-full"></div>
                <table class="inner-details-table">
                  <thead>
                    <tr><th>Customer ID</th><th>AQB</th><th>Avail. Bal.</th><th>Product Code</th></tr>
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
                    <tr><th>Rel. Value</th><th>MOB / Vintage</th><th>A/c Status</th></tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>{{ riskEntity.bank.relValue || '-' }}</td>
                      <td>{{ riskEntity.bank.mobVintage || '-' }}</td>
                      <td>{{ riskEntity.bank.acStatus || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
                <div class="separator-row-full"></div>
                <table class="inner-details-table">
                    <thead>
                      <tr><th>Addl field1</th><th>Addl field2</th><th>Addl field4</th></tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>{{ riskEntity.bank.addl1 || '-' }}</td>
                        <td>{{ riskEntity.bank.addl2 || '-' }}</td>
                        <td>{{ riskEntity.bank.addl4 || '-' }}</td>
                      </tr>
                    </tbody>
                </table>
            </div>
          </div>
        </section>
  
        <section class="card-section">
  <h2>Action</h2>

  <div v-if="!submittedAction">
    <table class="action-table">
      <tr>
        <td class="action-label">Analysis / Investigation Update</td>
        <td colspan="3">
          <div class="action-row">
            <select v-model="initialFeedbackLOV" class="form-input">
              <option value="">-- Select Feedback --</option>
              </select>
            <input type="text" v-model="initialFeedbackText" placeholder="Update text..." class="form-input"/>
          </div>
        </td>
        <td class="action-label">Review / Feedback from other functions</td>
      </tr>

      <tr>
        <td class="action-label" rowspan="reassignments.length + 1">Reassignment if required</td>
        <td colspan="4">
          <div v-for="(reassignment, index) in reassignments" :key="reassignment.id" class="reassignment-row">
            <span>Forward to:</span>
            <select v-model="reassignment.userId" class="form-input"><option value="">-- Select User --</option></select>
            <select v-model="reassignment.lov" class="form-input"><option value="">-- Select LOV --</option></select>
            <input type="text" v-model="reassignment.freeFlow" placeholder="Update..." class="form-input"/>
            <button @click="removeReassignment(reassignment.id)" class="remove-btn" v-if="reassignments.length > 1">×</button>
          </div>
          <button @click="addReassignment" class="add-btn">+ Add Assignment</button>
        </td>
      </tr>

      <tr>
        <td class="action-label">Alert Final Closure remarks</td>
        <td colspan="4">
          <div class="action-row">
            <select v-model="finalClosureRemarksLOV" class="form-input"><option value="">-- Select Remark --</option></select>
            <input type="text" v-model="finalClosureRemarksText" placeholder="Update text..." class="form-input"/>
          </div>
        </td>
      </tr>
    </table>
    
    <div class="final-closure-grid">
        <div>
            <label>Confirm / Final Closure</label>
            <select v-model="finalClosureConfirm" class="form-input">
                <option value="">-- Yes/No --</option><option value="yes">Yes</option><option value="no">No</option>
            </select>
        </div>
        <div>
            <label>Confirmed Mule</label>
            <select v-model="confirmedMule" class="form-input">
                <option value="">-- Yes/No --</option><option value="yes">Yes</option><option value="no">No</option>
            </select>
        </div>
        <div>
            <label>If yes, funds saved</label>
            <input type="number" v-model="fundsSaved" placeholder="99999999.99" class="form-input"/>
        </div>
        <div>
            <label>Digital Channel blocked</label>
            <select v-model="digitalChannelBlocked" class="form-input">
                <option value="">-- Yes/No --</option><option value="yes">Yes</option><option value="no">No</option>
            </select>
        </div>
        <div>
            <label>A/c fully blocked and closed</label>
            <select v-model="accountBlocked" class="form-input">
                <option value="">-- Yes/No --</option><option value="yes">Yes</option><option value="no">No</option>
            </select>
        </div>
        <div class="submit-wrapper">
            <button @click="submitFinalClosure" class="submit-btn">Submit</button>
        </div>
    </div>
  </div>

  <div v-else class="submitted-info">
      <h4>Action Submitted</h4>
      <p><strong>Final Remark:</strong> {{ submittedAction.final_remarks.text }}</p>
      <p><strong>Assigned To:</strong></p>
      <ul>
        <li v-for="item in submittedAction.reassignments">{{ item.userId }} - {{ item.freeFlow }}</li>
      </ul>
  </div>

</section>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, reactive, onMounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import axios from 'axios';
  import '../assets/OperationalAction.css'; // Assuming you have a CSS file for styling
  
  const route = useRoute();
  const router = useRouter();
  const case_id = route.params.case_id;
  
  // --- State Management ---
  const loading = ref(true);
  const error = ref('');
  const riskEntity = reactive({ i4c: {}, bank: {} });

  // --- Add these new state variables for the Action Form ---

// For Analysis / Investigation Update
const initialFeedbackLOV = ref('');
const initialFeedbackText = ref('');

// For the multi-assignment feature
const reassignments = ref([
  { id: 1, userId: '', dept: '', lov: '', freeFlow: '' } // Start with one empty row
]);

// For Alert Final Closure remarks
const finalClosureRemarksLOV = ref('');
const finalClosureRemarksText = ref('');

// For the final confirmation checklist
const finalClosureConfirm = ref('');
const confirmedMule = ref('');
const fundsSaved = ref(null);
const digitalChannelBlocked = ref('');
const accountBlocked = ref('');

// To hold options for dropdowns, fetched from APIs
const userOptions = ref([]); // e.g., [{id: 'user1', name: 'John Doe'}]
const deptOptions = ref([]); // e.g., [{id: 'deptA', name: 'Fraud Dept'}]
const feedbackOptions = ref([]); // e.g., [{id: 'opt1', name: 'Initial findings match'}]

// For displaying the final submitted action
const submittedAction = ref(null);

// --- Add this new function to handle adding more assignments ---
function addReassignment() {
  const newId = reassignments.value.length ? Math.max(...reassignments.value.map(r => r.id)) + 1 : 1;
  reassignments.value.push({ id: newId, userId: '', dept: '', lov: '', freeFlow: '' });
}

function removeReassignment(id) {
    reassignments.value = reassignments.value.filter(r => r.id !== id);
}

// --- Add this new function for the final submission ---
async function submitFinalClosure() {
  const payload = {
    initial_feedback: {
      lov: initialFeedbackLOV.value,
      text: initialFeedbackText.value
    },
    reassignments: reassignments.value.filter(r => r.userId || r.dept), // Only send non-empty rows
    final_remarks: {
      lov: finalClosureRemarksLOV.value,
      text: finalClosureRemarksText.value
    },
    final_closure: {
      is_confirmed: finalClosureConfirm.value,
      is_mule_confirmed: confirmedMule.value,
      funds_saved_amount: fundsSaved.value,
      is_channel_blocked: digitalChannelBlocked.value,
      is_account_blocked: accountBlocked.value
    }
  };

  alert("Submitting Final Closure Data:\n" + JSON.stringify(payload, null, 2));

  // --- Here you would make your final API call ---
  // const response = await axios.post(`/api/beneficiary-action/submit`, payload);
  // if (response.data.success) {
  //   // Re-fetch the saved action to display it
  //   const res = await axios.get(`/api/case/${case_id}/action-log`);
  //   submittedAction.value = res.data.data;
  // }
}
  
  // --- Helper Functions ---
  function isMatched(key) {
    const i4cValue = riskEntity.i4c ? riskEntity.i4c[key] : undefined;
    const bankValue = riskEntity.bank ? riskEntity.bank[key] : undefined;
    return i4cValue && bankValue && String(i4cValue).trim() === String(bankValue).trim();
  }
  
  onMounted(async () => {
  loading.value = true;
  try {
    const token = localStorage.getItem('jwt');
    if (!token) {
      error.value = "Authentication token not found.";
      loading.value = false;
      return;
    }

    // We will run all API calls and check each result individually
    const [combinedDataRes, userListRes, deptListRes] = await Promise.allSettled([
      // Main data for the case (This one is required)
      axios.get(`http://34.47.219.225:9000/api/combined-case-data/${case_id}`, { headers: { 'Authorization': `Bearer ${token}` } }),
      // Optional data for user dropdown
      axios.get(`http://34.47.219.225:9000/api/users`, { headers: { 'Authorization': `Bearer ${token}` } }),
      // Optional data for department dropdown
      axios.get(`http://34.47.219.225:9000/api/departments`, { headers: { 'Authorization': `Bearer ${token}` } })
    ]);

    // --- Process main case data ---
    // This part is critical, so if it fails, we show an error.
    if (combinedDataRes.status === 'fulfilled' && combinedDataRes.value.data) {
      // Your existing mapping logic for riskEntity goes here...
    } else {
      console.error('CRITICAL: Failed to fetch combined case data:', combinedDataRes.reason);
      error.value = "Failed to load the main case data.";
      // Stop execution if the main data fails to load
      loading.value = false;
      return; 
    }

    // --- Process optional user list ---
    // If this fails, we just log the error and move on.
    if (userListRes.status === 'fulfilled' && userListRes.value.data) {
      userOptions.value = userListRes.value.data;
    } else {
      console.warn('Could not fetch user list (API not ready):', userListRes.reason);
    }

    // --- Process optional department list ---
    // If this fails, we also just log the error and move on.
    if (deptListRes.status === 'fulfilled' && deptListRes.value.data) {
      deptOptions.value = deptListRes.value.data;
    } else {
      console.warn('Could not fetch department list (API not ready):', deptListRes.reason);
    }

  } catch (err) {
    console.error("A critical error occurred during page setup:", err);
    error.value = "An unexpected error occurred.";
  } finally {
    loading.value = false;
  }
});
  </script>
  