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
            </tr>
            <tr>
              <td class="action-label" :rowspan="reassignments.length + 1">Reassignment if required</td>
              <td colspan="4">
  <div v-for="reassignment in reassignments" :key="reassignment.id" class="reassignment-row">
    <span>Forward to:</span>
    
    <select v-model="reassignment.dept" class="form-input">
      <option value="">-- Select Department --</option>
      <option v-for="dept in deptOptions" :key="dept.name" :value="dept.name">
        {{ dept.name }}
      </option>
    </select>
    
    <select v-model="reassignment.userId" class="form-input" :disabled="!reassignment.dept || reassignment.userList.length === 0">
      <option value="">-- Select User --</option>
      <option v-for="user in reassignment.userList" :key="user.id" :value="user.id">
        {{ user.name }}
      </option>
    </select>

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
              <label>Confirmed Mule</label>
              <div class="radio-group">
                <label><input type="radio" v-model="confirmedMule" value="yes"> Yes</label>
                <label><input type="radio" v-model="confirmedMule" value="no"> No</label>
              </div>

              <label>Digital Channel blocked</label>
              <div class="radio-group">
                <label><input type="radio" v-model="digitalChannelBlocked" value="yes"> Yes</label>
                <label><input type="radio" v-model="digitalChannelBlocked" value="no"> No</label>
              </div>

              <label>A/c fully blocked and closed</label>
              <div class="radio-group">
                <label><input type="radio" v-model="accountBlocked" value="yes"> Yes</label>
                <label><input type="radio" v-model="accountBlocked" value="no"> No</label>
              </div>
          </div>

          <div class="action-buttons">
            <button @click="saveActionData" class="save-btn" :disabled="isSaving">
              {{ isSaving ? 'Saving...' : 'Save' }}
            </button>
            <button @click="submitFinalClosure" class="submit-btn" :disabled="isSaving">
              {{ isSaving ? 'Submitting...' : 'Submit' }}
            </button>
          </div>
        </div>

        <div v-else class="submitted-info">
            <h4>Action Submitted</h4>
            </div>
      </section>
      </div>
    </div>
    <div v-if="caseStatus !== 'Closed'">
    <table class="action-table">
      </table>
    <div class="final-closure-grid">
      </div>
    <!-- <div class="action-buttons">
      <button @click="saveActionData" class="save-btn">Save</button>
      <button @click="submitFinalClosure" class="submit-btn">Submit</button>
    </div> -->
  </div>

  <div v-else>
    <div v-if="submittedAction">
      <p class="section-subtitle">This case has been closed. The following actions were recorded:</p>
      
      <div class="history-item">
        <strong>Initial Review Feedback:</strong>
        <span>{{ submittedAction.initial_feedback?.text || 'No comment provided.' }}</span>
      </div>
      
      <div class="history-item">
        <strong>Review / Feedback from other functions (Reassignments):</strong>
      </div>
      <table class="history-table">
        <thead>
          <tr>
            <th>User ID / Dept</th>
            <th>Update - LOV</th>
            <th>Update - Text box</th>
            <th>Date/Time</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in submittedAction.reassignments" :key="item.id">
            <td>{{ item.userId }}</td>
            <td>{{ item.lov }}</td>
            <td>{{ item.freeFlow }}</td>
            <td>{{ new Date(item.timestamp).toLocaleString() }}</td> </tr>
          <tr v-if="!submittedAction.reassignments || submittedAction.reassignments.length === 0">
            <td colspan="4">No reassignments were made.</td>
          </tr>
        </tbody>
      </table>

      <div class="history-item">
        <strong>Final Closure Remarks:</strong>
        <span>{{ submittedAction.final_remarks?.text || 'No final remarks.' }}</span>
      </div>

      <div class="history-item">
        <strong>Uploaded Screenshot:</strong>
        <a
          v-if="submittedAction.screenshot_filename"
          :href="`http://34.47.219.225:9000/api/case-document/download/${submittedAction.screenshot_filename}`"
          target="_blank"
          rel="noopener"
        >
          {{ submittedAction.screenshot_filename }}
        </a>
        <span v-else>No screenshot uploaded.</span>
      </div>

      <div v-if="submittedAction.uploaded_documents && submittedAction.uploaded_documents.length > 0">
        <strong>Uploaded Documents:</strong>
        <ul>
          <li v-for="doc in submittedAction.uploaded_documents" :key="doc.id">
            <a :href="`http://34.47.219.225:9000/api/case-document/download/${doc.original_filename}`" target="_blank">
              {{ doc.original_filename }}
            </a>
          </li>
        </ul>
      </div>

    </div>
    <div v-else class="closed-case-notice">
      Loading action history...
    </div>
  </div>
  </template>
  
  <script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import '../assets/OperationalAction.css';
import '../assets/BeneficiaryAction.css';

const route = useRoute();
// const router = useRouter();
const case_id = route.params.case_id;
const caseStatus = computed(() => route.query.status);

// --- State Management ---
const loading = ref(true);
const error = ref('');
const riskEntity = reactive({ i4c: {}, bank: {} });
const isSaving = ref(false);

// Action Form State
const initialFeedbackLOV = ref('');
const initialFeedbackText = ref('');
const reassignments = ref([
  { id: 1, userId: '', dept: '', userList: [] }
]);
const deptOptions = ref([]);
const finalClosureRemarksLOV = ref('');
const finalClosureRemarksText = ref('');
const confirmedMule = ref('');
const digitalChannelBlocked = ref('');
const accountBlocked = ref('');
// const userOptions = ref([]); // This will be populated on demand
// const feedbackOptions = ref([]);
const submittedAction = ref(null);

const departmentSelections = computed(() => reassignments.value.map(r => r.dept));

// --- Helper Functions & Watchers ---
async function fetchUsersForDepartment(reassignment) {
  if (!reassignment.dept) {
    reassignment.userList = [];
    reassignment.userId = '';
    return;
  }
  try {
    const res = await axios.get(`http://34.47.219.225:9000/api/users?department_name=${reassignment.dept}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('jwt')}` }
    });
    reassignment.userList = res.data;
  } catch (err) {
    console.error("Failed to fetch users for department:", err);
    reassignment.userList = [];
  }
}

watch(departmentSelections, (newDepts, oldDepts) => {
  // Find which department changed
  for (let i = 0; i < newDepts.length; i++) {
    if (newDepts[i] !== oldDepts[i]) {
      console.log(`Department changed for row ${i} to ${newDepts[i]}. Fetching users...`);
      // Use the index 'i' to get the correct reassignment object
      fetchUsersForDepartment(reassignments.value[i]);
    }
  }
});

function addReassignment() {
  reassignments.value.push({
    id: Date.now(),
    userId: '',
    dept: '',
    lov: '',
    freeFlow: '',
    userList: []
  });
}

function removeReassignment(id) {
  reassignments.value = reassignments.value.filter(r => r.id !== id);
}

// --- Action Functions ---
async function saveActionData() {
  // ... your save logic ...
}

async function submitFinalClosure() {
  // ... your submit logic ...
}

function isMatched(key) {
  const i4cValue = riskEntity.i4c ? riskEntity.i4c[key] : undefined;
  const bankValue = riskEntity.bank ? riskEntity.bank[key] : undefined;
  return i4cValue && bankValue && String(i4cValue).trim() === String(bankValue).trim();
}

// --- Data Fetching on Mount ---
onMounted(async () => {
  loading.value = true;
  try {
    const token = localStorage.getItem('jwt');
    if (!token) {
      error.value = "Authentication token not found.";
      loading.value = false;
      return;
    }

    // CORRECTED: Fetch only the required data on page load
    const [combinedDataRes, deptListRes] = await Promise.allSettled([
      axios.get(`http://34.47.219.225:9000/api/combined-case-data/${case_id}`, { headers: { 'Authorization': `Bearer ${token}` } }),
      axios.get(`http://34.47.219.225:9000/api/departments`, { headers: { 'Authorization': `Bearer ${token}` } })
    ]);

    // Process main case data
    if (combinedDataRes.status === 'fulfilled' && combinedDataRes.value.data) {
      const responseData = combinedDataRes.value.data;
      const i4cData = responseData.i4c_data || {};
      const customerDetails = responseData.customer_details || {};
      
      riskEntity.i4c = { name: i4cData.customer_name, mobileNumber: i4cData.mobile, bankAc: i4cData.account_number, email: i4cData.email };
      riskEntity.bank = { name: `${customerDetails.fname || ''} ${customerDetails.mname || ''} ${customerDetails.lname || ''}`.trim(), mobileNumber: customerDetails.mobile, bankAc: responseData.acc_num, email: customerDetails.email, pan: customerDetails.pan, aadhaar: customerDetails.nat_id, customerId: customerDetails.cust_id, acStatus: responseData.account_details?.acc_status, aqb: responseData.account_details?.aqb, availBal: responseData.account_details?.availBal, productCode: responseData.account_details?.productCode, relValue: customerDetails?.rel_value, mobVintage: customerDetails?.mob };
 
    } else {
      console.error('CRITICAL: Failed to fetch combined case data:', combinedDataRes.reason);
      error.value = "Failed to load the main case data.";
      loading.value = false;
      return; 
    }

    // Process department list for the dropdown
    if (deptListRes.status === 'fulfilled' && deptListRes.value.data) {
      deptOptions.value = deptListRes.value.data;
    } else {
      console.warn('Could not fetch department list:', deptListRes.reason);
    }
    if (caseStatus.value === 'Closed') {
      try {
        const actionLogRes = await axios.get(`http://34.47.219.225:9000/api/case/${case_id}/action-log`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (actionLogRes.data && actionLogRes.data.success) {
          // Store the fetched history data
          submittedAction.value = actionLogRes.data.data;
        }
      } catch (logErr) {
        console.warn('Could not load action history:', logErr);
      }
    }

  } catch (err) {
    console.error("A critical error occurred during page setup:", err);
    error.value = "An unexpected error occurred.";
  } finally {
    loading.value = false;
  }
});
  </script>
