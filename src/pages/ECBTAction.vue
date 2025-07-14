<template>
  <div class="action-page-bg">
    <h1 class="screen-header">Alert - Potential Victim Account - Amount Transferred to Suspect Beneficiaries</h1>

    <div v-if="loading" class="loading-container">Loading Case Data...</div>
    <div v-else-if="error" class="error-container">{{ error }}</div>

    <div v-else class="content-wrapper">
      <section class="card-section">
        <div class="side-by-side-container">
          <div class="profile-column">
            <h3 class="column-header">Customer Details - I4C</h3>
            <table class="inner-details-table">
              <thead>
                <tr><th>Name</th><th>Mobile Number</th><th>Email</th><th>IFSC Code</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ riskEntity.i4c.name || '-' }}</td>
                  <td>{{ riskEntity.i4c.mobileNumber || '-' }}</td>
                  <td>{{ riskEntity.i4c.email || '-' }}</td>
                  <td>{{ riskEntity.i4c.ifscCode || '-' }}</td>
                </tr>
              </tbody>
            </table>
            <div class="separator-row-full"></div>
            <table class="inner-details-table">
              <thead>
                <tr><th>Beneficiary Account Number</th><th>Bank Name</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ riskEntity.i4c.beneficiaryAccount || '-' }}</td>
                  <td>{{ riskEntity.i4c.bankName || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="profile-column">
             <h3 class="column-header">Customer Details - Bank</h3>
              <table class="inner-details-table">
                <thead>
                  <tr><th>Name</th><th>Mobile Number</th><th>Email</th><th>IFSC Code</th></tr>
                </thead>
                <tbody>
                  <tr>
                    <td :class="{ 'highlight-match': isMatched('name') }">{{ riskEntity.bank.name || '-' }}</td>
                    <td :class="{ 'highlight-match': isMatched('mobileNumber') }">{{ riskEntity.bank.mobileNumber || '-' }}</td>
                    <td :class="{ 'highlight-match': isMatched('email') }">{{ riskEntity.bank.email || '-' }}</td>
                    <td :class="{ 'highlight-match': isMatched('ifscCode') }">{{ riskEntity.bank.ifscCode || '-' }}</td>
                  </tr>
                </tbody>
              </table>
              <div class="separator-row-full"></div>
               <table class="inner-details-table">
                <thead>
                  <tr><th>Beneficiary Account Number</th><th>Bank Name</th></tr>
                </thead>
                <tbody>
                  <tr>
                    <td :class="{ 'highlight-match': isMatched('beneficiaryAccount') }">{{ riskEntity.bank.beneficiaryAccount || '-' }}</td>
                    <td :class="{ 'highlight-match': isMatched('bankName') }">{{ riskEntity.bank.bankName || '-' }}</td>
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
        <h2>Transaction Details</h2>
        <div class="table-container">
          <table class="details-table">
            <thead>
              <tr><th>Date</th><th>Time</th><th>Beneficiary</th><th>Amount</th><th>Mode</th><th>Txn. Ref #</th><th>Txn Description</th></tr>
            </thead>
            <tbody>
              <tr v-for="txn in transactionDetails" :key="txn.id">
                <td>{{ txn.date || '-' }}</td>
                <td>{{ txn.time || '-' }}</td>
                <td>{{ txn.beneficiary || '-' }}</td>
                <td>{{ txn.amount ? '₹' + Number(txn.amount).toLocaleString('en-IN') : '-' }}</td>
                <td>{{ txn.mode || '-' }}</td>
                <td>{{ txn.refNo || '-' }}</td>
                <td>{{ txn.description || '-' }}</td>
              </tr>
              <tr v-if="!transactionDetails.length"><td colspan="7" style="text-align:center;">No transactions found.</td></tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="6">Total Value @ Risk</td>
                <td>₹{{ totalValueAtRisk ? totalValueAtRisk.toLocaleString('en-IN') : '0.00' }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>

      <section class="card-section">
        <h2>Action</h2>
        <div v-if="caseStatus !== 'Closed'">
          <table class="action-table">
            <tr>
              <td class="action-label">Analysis / Investigation Update</td>
              <td colspan="4">
                <div class="action-row">
                  <select v-model="initialFeedbackLOV" class="form-input"><option value="">-- Select Feedback --</option></select>
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
                    <option v-for="dept in deptOptions" :key="dept.name" :value="dept.name">{{ dept.name }}</option>
                  </select>
                  <select v-model="reassignment.userId" class="form-input" :disabled="!reassignment.dept">
                    <option value="">-- Select User --</option>
                    <option v-for="user in reassignment.userList" :key="user.id" :value="user.id">{{ user.name }}</option>
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
              <label>Confirmed Victim</label>
              <div class="radio-group"><label><input type="radio" v-model="confirmedMule" value="yes"> Yes</label><label><input type="radio" v-model="confirmedMule" value="no"> No</label></div>
              <label>Digital Channel blocked</label>
              <div class="radio-group"><label><input type="radio" v-model="digitalChannelBlocked" value="yes"> Yes</label><label><input type="radio" v-model="digitalChannelBlocked" value="no"> No</label></div>
              <label>A/c fully blocked and closed</label>
              <div class="radio-group"><label><input type="radio" v-model="accountBlocked" value="yes"> Yes</label><label><input type="radio" v-model="accountBlocked" value="no"> No</label></div>
          </div>
          <div class="action-buttons">
            <button @click="saveActionData" class="save-btn" :disabled="isSaving">Save</button>
            <button @click="submitFinalClosure" class="submit-btn" :disabled="isSaving">Submit</button>
          </div>
        </div>
        <div v-else>
          <div v-if="submittedAction">
            <p class="section-subtitle">This case was closed on {{ new Date(submittedAction.submitted_at).toLocaleString() }} by {{ submittedAction.submitted_by }}.</p>
            <div class="history-grid">
              <strong>Documents Confirmed:</strong>
              <ul class="history-doc-list">
                <li v-for="doc in submittedAction.checked_documents" :key="doc">{{ doc }}</li>
                <li v-if="!submittedAction.checked_documents || submittedAction.checked_documents.length === 0">None</li>
              </ul>
              <strong>Proof of Upload Ref:</strong>
              <span>{{ submittedAction.proof_of_upload_ref || 'N/A' }}</span>
              <strong>Uploaded Screenshot:</strong>
              <span v-if="submittedAction.screenshot_filename"><a :href="`/api/download/${submittedAction.screenshot_filename}`" target="_blank">{{ submittedAction.screenshot_filename }}</a></span>
              <span v-else>None</span>
            </div>
          </div>
          <div v-else class="closed-case-notice">Loading action history...</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const case_id = route.params.case_id;
const caseStatus = computed(() => route.query.status);

// --- State Management ---
const loading = ref(true);
const error = ref('');
const riskEntity = reactive({ i4c: {}, bank: {} });
const transactionDetails = ref([]);
const isSaving = ref(false);

// Action Form State
const initialFeedbackLOV = ref('');
const initialFeedbackText = ref('');
const reassignments = ref([{ id: 1, userId: '', dept: '', lov: '', freeFlow: '', userList: [] }]);
const finalClosureRemarksLOV = ref('');
const finalClosureRemarksText = ref('');
const confirmedMule = ref('');
const digitalChannelBlocked = ref('');
const accountBlocked = ref('');
const deptOptions = ref([]);
const submittedAction = ref(null);

// --- Computed Properties ---
const totalValueAtRisk = computed(() => {
  return transactionDetails.value.reduce((total, txn) => total + Number(txn.amount || 0), 0);
});

const departmentSelections = computed(() => reassignments.value.map(r => r.dept));

// --- Functions ---
async function fetchUsersForDepartment(reassignment) {
  if (!reassignment.dept) {
    reassignment.userList = [];
    reassignment.userId = '';
    return;
  }
  try {
    const res = await axios.get(`http://34.47.219.225:9000/api/users?department_name=${reassignment.dept}`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('jwt')}` } });
    reassignment.userList = res.data;
  } catch (err) {
    console.error("Failed to fetch users for department:", err);
    reassignment.userList = [];
  }
}

watch(departmentSelections, (newDepts, oldDepts) => {
  for (let i = 0; i < newDepts.length; i++) {
    if (newDepts[i] !== oldDepts[i]) {
      fetchUsersForDepartment(reassignments.value[i]);
    }
  }
});

function addReassignment() {
  reassignments.value.push({ id: Date.now(), userId: '', dept: '', lov: '', freeFlow: '', userList: [] });
}

function removeReassignment(id) {
  reassignments.value = reassignments.value.filter(r => r.id !== id);
}

function isMatched(key) {
  const i4cValue = riskEntity.i4c ? riskEntity.i4c[key] : undefined;
  const bankValue = riskEntity.bank ? riskEntity.bank[key] : undefined;
  return i4cValue && bankValue && String(i4cValue).trim() === String(bankValue).trim();
}

async function saveActionData() { alert('Save action triggered!'); }
async function submitFinalClosure() { alert('Submit action triggered!'); }

onMounted(async () => {
  loading.value = true;
  try {
    const token = localStorage.getItem('jwt');
    if (!token) { throw new Error("Authentication token not found."); }

    const [combinedDataRes, deptListRes] = await Promise.allSettled([
      axios.get(`http://34.47.219.225:9000/api/combined-case-data/${case_id}`, { headers: { 'Authorization': `Bearer ${token}` } }),
      axios.get(`http://34.47.219.225:9000/api/departments`, { headers: { 'Authorization': `Bearer ${token}` } })
    ]);

    if (combinedDataRes.status === 'fulfilled' && combinedDataRes.value.data) {
      const data = combinedDataRes.value.data;
      const i4cData = data.i4c_data || {};
      const customerDetails = data.customer_details || {};
      
      riskEntity.i4c = { name: i4cData.customer_name, mobileNumber: i4cData.mobile, email: i4cData.email, ifscCode: i4cData.ifsc, beneficiaryAccount: i4cData.to_account, bankName: i4cData.to_bank };
      riskEntity.bank = { name: `${customerDetails.fname || ''} ${customerDetails.mname || ''} ${customerDetails.lname || ''}`.trim(), mobileNumber: customerDetails.mobile, email: customerDetails.email, ifscCode: customerDetails.ifsc, beneficiaryAccount: data.source_bene_accno, bankName: i4cData.to_bank, customerId: customerDetails.cust_id, acStatus: data.account_details?.acc_status, aqb: data.account_details?.aqb, availBal: data.account_details?.availBal, productCode: data.account_details?.productCode, relValue: data.account_details?.rel_value, mobVintage: data.account_details?.mob, addl1: data.account_details?.addl1, addl2: data.account_details?.addl2, addl4: data.account_details?.addl4 };
      transactionDetails.value = data.transactions || [];
    } else {
      error.value = "Failed to load main case data.";
    }

    if (deptListRes.status === 'fulfilled' && deptListRes.value.data) {
      deptOptions.value = deptListRes.value.data;
    } else {
      console.warn('Could not fetch department list');
    }

    if (caseStatus.value === 'Closed') {
      const actionLogRes = await axios.get(`http://34.47.219.225:9000/api/case/${case_id}/action-log`, { headers: { 'Authorization': `Bearer ${token}` } });
      if (actionLogRes.data?.success) {
        submittedAction.value = actionLogRes.data.data;
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

<style scoped>
  /* All necessary CSS from BeneficiaryAction.vue, plus styles for the transaction table */
  .action-page-bg { padding: 2rem; background-color: #f1f5f9; min-height: 100vh; }
  .screen-header { color: #1e293b; font-size: 2rem; margin-bottom: 1.5rem; }
  .content-wrapper { display: flex; flex-direction: column; gap: 1.5rem; }
  .card-section { background-color: #ffffff; border-radius: 12px; padding: 1.5rem 2rem; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
  .card-section h2 { margin-top: 0; font-size: 1.5rem; color: #334155; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.75rem; margin-bottom: 1.5rem; }
  .side-by-side-container { display: flex; gap: 1.5rem; }
  .profile-column { flex: 1; }
  .column-header { font-size: 1.2rem; margin-bottom: 1rem; color: #475569; }
  .inner-details-table { width: 100%; }
  .inner-details-table th, .inner-details-table td { text-align: left; padding: 0.5rem 0.25rem; }
  .inner-details-table th { font-weight: 600; font-size: 0.9em; color: #64748b; }
  td.highlight-match { background-color: #fef9c3; border-radius: 4px; }
  .separator-row-full { width: 100%; border-top: 1px dashed #cbd5e1; margin: 1rem 0; }
  .table-container { width: 100%; overflow-x: auto; }
  .details-table { width: 100%; border-collapse: collapse; }
  .details-table th, .details-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #e2e8f0; }
  .details-table th { background-color: #f8fafc; }
  .details-table tfoot td { font-weight: bold; text-align: right; font-size: 1.1em; background-color: #f8fafc; border-top: 2px solid #e2e8f0; }
  .details-table tfoot td:last-child { text-align: left; }
  .action-table { width: 100%; margin-bottom: 1.5rem; }
  .action-table td { padding: 0.75rem; vertical-align: top; }
  .action-label { font-weight: 600; color: #475569; width: 25%; text-align: right; padding-right: 1.5rem; }
  .action-row, .reassignment-row { display: flex; gap: 1rem; align-items: center; }
  .reassignment-row { margin-bottom: 0.75rem; }
  .form-input { flex-grow: 1; padding: 0.5rem 0.75rem; border-radius: 6px; border: 1px solid #cbd5e1; }
  .add-btn { background: none; border: 1px dashed #94a3b8; color: #475569; padding: 0.25rem 0.75rem; border-radius: 6px; cursor: pointer; }
  .remove-btn { background: #fee2e2; border: 1px solid #fca5a5; color: #991b1b; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-weight: bold; }
  .final-closure-grid { display: grid; grid-template-columns: auto 1fr; gap: 1rem 1.5rem; align-items: center; border-top: 1px solid #e2e8f0; padding-top: 1.5rem; }
  .final-closure-grid label { font-weight: 600; color: #475569; text-align: right; }
  .radio-group { display: flex; gap: 1.5rem; }
  .radio-group label { font-weight: normal; display: flex; align-items: center; gap: 0.5rem; }
  .action-buttons { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #e2e8f0; }
  .save-btn, .submit-btn { padding: 0.75rem 1.5rem; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
  .save-btn { background-color: #e2e8f0; color: #334155; }
  .submit-btn { background-color: #2563eb; color: white; }
  .history-grid { display: grid; grid-template-columns: 200px 1fr; gap: 1rem; margin-top: 1.5rem; font-size: 0.9em; }
  .history-grid strong { font-weight: 600; color: #475569; }
  .history-doc-list { margin: 0; padding-left: 1.2rem; }
  .closed-case-notice, .section-subtitle { padding: 1rem; text-align: center; font-weight: 500; color: #475569; background-color: #f1f5f9; border-radius: 8px; }
</style>