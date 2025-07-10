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
      <option v-for="dept in deptOptions" :key="dept.id" :value="dept.id">
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
    <div class="action-buttons">
      <button @click="saveActionData" class="save-btn">Save</button>
      <button @click="submitFinalClosure" class="submit-btn">Submit</button>
    </div>
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

const route = useRoute();
const router = useRouter();
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
const finalClosureRemarksLOV = ref('');
const finalClosureRemarksText = ref('');
const confirmedMule = ref('');
const digitalChannelBlocked = ref('');
const accountBlocked = ref('');
const userOptions = ref([]); // This will be populated on demand
const deptOptions = ref([]); // This will be populated on mount
const feedbackOptions = ref([]);
const submittedAction = ref(null);

// --- Helper Functions & Watchers ---
async function fetchUsersForDepartment(reassignment) {
  if (!reassignment.dept) {
    reassignment.userList = [];
    reassignment.userId = '';
    return;
  }
  try {
    const res = await axios.get(`http://34.47.219.225:9000/api/users?department_id=${reassignment.dept}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('jwt')}` }
    });
    reassignment.userList = res.data;
  } catch (err) {
    console.error("Failed to fetch users for department:", err);
    reassignment.userList = [];
  }
}

watch(reassignments, (newReassignments, oldReassignments) => {
  for (let i = 0; i < newReassignments.length; i++) {
    const oldDept = oldReassignments && oldReassignments[i] ? oldReassignments[i].dept : null;
    if (newReassignments[i].dept !== oldDept) {
      fetchUsersForDepartment(newReassignments[i]);
    }
  }
}, { deep: true });

// CORRECTED: Ensure new rows have the `userList` property
function addReassignment() {
  reassignments.value.push({
    id: Date.now(),
    userId: '',
    dept: '',
    lov: '',
    freeFlow: '',
    userList: [] // This was the missing piece
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
        // ... your existing mapping logic for riskEntity goes here ...
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
        const actionLogRes = await axios.get(`http://.../api/case/${case_id}/action-log`, { headers: { 'Authorization': `Bearer ${token}` } });
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
  <style scoped>
  /* Main Page Layout */
  .action-page-bg { padding: 2rem; background-color: #f1f5f9; min-height: 100vh; }
  .screen-header { color: #1e293b; font-size: 2rem; margin-bottom: 1.5rem; }
  .content-wrapper { display: flex; flex-direction: column; gap: 1.5rem; }
  .card-section { background-color: #ffffff; border-radius: 12px; padding: 1.5rem 2rem; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
  .card-section h2 { margin-top: 0; font-size: 1.5rem; color: #334155; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.75rem; margin-bottom: 1.5rem; }
  
  /* Action Table for layout */
  .action-table { width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; }
  .action-table td { padding: 0.75rem; vertical-align: top; }
  .action-label { font-weight: 600; color: #475569; width: 25%; text-align: right; padding-right: 1.5rem; }
  
  /* Row styling for inputs */
  .action-row, .reassignment-row { display: flex; gap: 1rem; align-items: center; }
  .reassignment-row { margin-bottom: 0.75rem; }
  .form-input { flex-grow: 1; padding: 0.5rem 0.75rem; border-radius: 6px; border: 1px solid #cbd5e1; }
  .add-btn { background: none; border: 1px dashed #94a3b8; color: #475569; padding: 0.25rem 0.75rem; border-radius: 6px; cursor: pointer; }
  .remove-btn { background: #fee2e2; border: 1px solid #fca5a5; color: #991b1b; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-weight: bold; }
  
  /* Final Closure Grid */
  .final-closure-grid {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 1rem 1.5rem;
    align-items: center;
    border-top: 1px solid #e2e8f0;
    padding-top: 1.5rem;
    max-width: 800px;
  }
  .final-closure-grid label { font-weight: 600; color: #475569; text-align: right; }
  .radio-group { display: flex; gap: 1.5rem; }
  .radio-group label { font-weight: normal; display: flex; align-items: center; gap: 0.5rem; }
  
  /* Buttons */
  .action-buttons { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #e2e8f0; }
  .save-btn, .submit-btn { padding: 0.75rem 1.5rem; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
  .save-btn { background-color: #e2e8f0; color: #334155; }
  .submit-btn { background-color: #2563eb; color: white; }
  .history-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.5rem;
  font-size: 0.9em;
}

.history-table th,
.history-table td {
  padding: 0.75rem;
  text-align: left;
  border: 1px solid #e2e8f0;
}

.history-table th {
  background-color: #f8fafc;
  font-weight: 600;
}

.history-item {
  margin-top: 1.5rem;
  padding-bottom: 0.5rem;
}

.history-item strong {
  display: block;
  margin-bottom: 0.25rem;
  color: #475569;
}

.closed-case-notice {
  padding: 1rem;
  text-align: center;
  font-weight: 500;
  color: #475569;
  background-color: #f1f5f9;
  border-radius: 8px;
}
  </style>