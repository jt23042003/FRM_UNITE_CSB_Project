<template>
  <div class="dashboard-bg">
    <div class="dashboard-header">
      <h2>Case View Dashboard</h2>
      <div class="filters-row enhanced-search-row">
        <div class="search-bar-container">
          <span class="search-icon">
            <svg width="20" height="20" fill="none" stroke="#2563eb" stroke-width="2" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7"/>
              <line x1="16.5" y1="16.5" x2="21" y2="21"/>
            </svg>
          </span>
          <input
            v-model="filters.ackNo"
            placeholder="Search by Acknowledgement Number"
            class="filter-input enhanced-search-input"
          />
        </div>
        <select v-model="filters.status" class="filter-input enhanced-status-select">
          <option value="">All Statuses</option>
          <option v-for="status in statuses" :key="status">{{ status }}</option>
        </select>
        <select v-model="filters.complaintType" class="filter-input enhanced-type-select">
          <option value="">All Types</option>
          <option v-for="type in complaintTypes" :key="type">{{ type }}</option>
        </select>
        <button @click="fetchCases" class="search-btn enhanced-search-btn">Search</button>
        <button @click="clearFilters" class="reset-btn enhanced-reset-btn">Clear</button>
      </div>
    </div>
    <div class="dashboard-table-card">
      <table class="case-table">
        <colgroup>
          <col style="width: 10%;"> <col style="width: 12%;"> <col style="width: 15%;"> <col style="width: 8%;">  <col style="width: 8%;">  <col style="width: 8%;">  <col style="width: 10%;"> <col style="width: 12%;"> <col style="width: 8%;">  <col style="width: 9%;">  </colgroup>
        <thead>
          <tr>
            <th>Case ID</th>
            <th>ACK ID</th>
            <th>Complaint/Detection Type</th>
            <th>Source</th>
            <th>Case Label</th>
            <th>Operational</th>
            <th>Location</th>
            <th>Transaction/Case Amount</th>
            <th>Status</th>
            <th>Assigned To</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="caseItem in pagedCases" :key="caseItem.case_id">
            <td>
              <router-link
  :to="getCaseLink(caseItem)"
  class="ack-link"
>
  {{ caseItem.case_id }}
</router-link>
            </td>
            <td>{{ caseItem.source_ack_no || '-' }}</td>
            <td>{{ caseItem.case_type || '-' }}</td>
            <td>{{ caseItem.source || '-' }}</td>
            <td>{{ caseItem.match_type || '-' }}</td>
            <td>
              <span :class="['badge', caseItem.is_operational ? 'operational' : 'non-operational']">
                {{ caseItem.is_operational ? 'Yes' : 'No' }}
              </span>
            </td>
            <td>{{ caseItem.location || '-' }}</td>
            <td>
              <span v-if="caseItem.transaction_amount !== null && !isNaN(Number(caseItem.transaction_amount))">
                ₹{{ Number(caseItem.transaction_amount).toLocaleString('en-IN') }}
              </span>
              <span v-else>-</span>
            </td>
            <td>
              <span :class="['status-badge', caseItem.status ? caseItem.status.toLowerCase().replace(/ /g,'-') : '']">
                {{ caseItem.status || '-' }}
              </span>
            </td>
            <td>{{ caseItem.assigned_to || '-' }}</td>
          </tr>
          <tr v-if="pagedCases.length === 0">
            <td colspan="10" style="text-align:center; padding: 20px;">No cases found.</td>
          </tr>
        </tbody>
      </table>
      <div class="pagination-row">
        <button @click="prevPage" :disabled="page === 1">Prev</button>
        <span>Page {{ page }} of {{ totalPages }}</span>
        <button @click="nextPage" :disabled="page === totalPages">Next</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import '../assets/CaseDetails.css'

const statuses = [
  'New',
  'Open',
  'Assigned',
  'Closed',
  'Pending', // Added based on CSS
  'Resolved' // Example: if you have more statuses
]

const complaintTypes = [
  'VM', 'BM', 'PMA', 'NAB', 'PSA', 'ECBT', 'ECBNT'
]

const cases = ref([])
const page = ref(1)
const pageSize = 25

const filters = ref({
  ackNo: '', // Renamed from caseId to ackNo for clarity
  status: '',
  complaintType: ''
})

function getCaseLink(caseItem) {
  // If the case type is 'VM', go to the operational page
  if (caseItem.case_type === 'VM') {
    return { name: 'OperationalAction', params: { case_id: caseItem.case_id }, query: { status: caseItem.status } };
  }

  // If the case type is 'BM', go to the new beneficiary page
  if (caseItem.case_type === 'BM') {
    return { name: 'BeneficiaryAction', params: { case_id: caseItem.case_id },  };
  }

  // Fallback for all other case types
  return { name: 'CaseRiskReview', params: { case_id: caseItem.case_id }, query: { status: caseItem.status } };
}

const fetchCases = async () => {
  try {
    const token = localStorage.getItem('jwt');

    if (!token) {
      console.error("Authentication token not found. Please log in.");
      alert("You are not logged in or your session has expired. Please log in.");
      return;
    }

    // Backend URL: ensure this is correct
    const apiUrl = 'http://34.47.219.225:9000/api/new-case-list';

    // If your backend supports filtering, you would pass parameters here.
    // For now, we are relying on frontend filtering as per your initial setup.
    // Example if backend filtering was enabled:
    // const params = {};
    // if (filters.value.ackNo) params.ack_no = filters.value.ackNo;
    // if (filters.value.status) params.status = filters.value.status;
    // if (filters.value.complaintType) params.compl_type = filters.value.complaintType; // Adjust param name as per your backend API spec

    const res = await axios.get(apiUrl, {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      // params: params // Uncomment this line if you enable backend filtering
    });

    // Ensure res.data.cases is an array before assigning
    cases.value = Array.isArray(res.data.cases) ? res.data.cases : [];
    page.value = 1; // Reset to first page on new data fetch
    console.log("Cases fetched successfully:", cases.value);

  } catch (err) {
    console.error('Failed to fetch data:', err.response?.data || err.message);
    if (err.response && err.response.status === 401) {
      alert("Unauthorized: Please log in again.");
      // Optionally redirect to login page
      router.push('/login');
    } else {
      alert("Failed to load cases. Check console for details.");
    }
    cases.value = []; // Clear cases on error
  }
};

onMounted(fetchCases)

const filteredCases = computed(() => {
  return cases.value.filter(c => {
    const matchesAckNo = !filters.value.ackNo ||
                         (c.source_ack_no && c.source_ack_no.toLowerCase().includes(filters.value.ackNo.trim().toLowerCase()));

    const matchesStatus = !filters.value.status ||
                          (c.status && c.status.toLowerCase() === filters.value.status.toLowerCase());

    const matchesComplaintType = !filters.value.complaintType ||
                                 (c.case_type && c.case_type.toLowerCase() === filters.value.complaintType.toLowerCase());

    return matchesAckNo && matchesStatus && matchesComplaintType;
  });
});


const totalPages = computed(() =>
  Math.ceil(filteredCases.value.length / pageSize)
)

const pagedCases = computed(() =>
  filteredCases.value.slice((page.value - 1) * pageSize, page.value * pageSize)
)

const prevPage = () => { if (page.value > 1) page.value-- }
const nextPage = () => { if (page.value < totalPages.value) page.value++ }

const clearFilters = () => {
  filters.value.ackNo = ''; // Clear ackNo filter
  filters.value.status = '';
  filters.value.complaintType = ''; // Clear complaintType filter
  page.value = 1;
  fetchCases(); // Re-fetch all cases after clearing filters
}
</script>