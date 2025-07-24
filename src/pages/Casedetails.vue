<template>
  <div class="dashboard-bg">
    <div class="dashboard-header">
      <h2>Case View Dashboard</h2>
      <div class="filters-row">
        <div class="search-bar-container">
          <span class="search-icon">
            <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
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
        <button @click="fetchCases" class="search-btn">Search</button>
        <button @click="clearFilters" class="reset-btn">Clear</button>
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
        <div>
          <span>Rows per page: {{ pageSize }}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
          <span>{{ startIndex }}-{{ endIndex }} of {{ totalItems }}</span>
          <button @click="prevPage" :disabled="page === 1">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M15 18l-6-6 6-6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <button @click="nextPage" :disabled="page === totalPages">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M9 18l6-6-6-6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import '../assets/CaseDetails.css'
import { API_ENDPOINTS } from '../config/api.js'

const router = useRouter()

const statuses = [
  'New',
  'Open',
  'Assigned',
  'Closed',
  'Pending',
  'Resolved'
]

const complaintTypes = [
  'VM', 'BM', 'PMA', 'NAB', 'PSA', 'ECBT', 'ECBNT'
]

const cases = ref([])
const page = ref(1)
const pageSize = 13 // Changed to match the reference design
const loading = ref(false)
const error = ref(null)

const filters = ref({
  ackNo: '',
  status: '',
  complaintType: ''
})

// Computed properties for pagination display
const totalItems = computed(() => filteredCases.value.length)
const startIndex = computed(() => ((page.value - 1) * pageSize) + 1)
const endIndex = computed(() => Math.min(page.value * pageSize, totalItems.value))

function getCaseLink(caseItem) {
  const routeMap = {
    'VM': 'OperationalAction',
    'BM': 'BeneficiaryAction',
    'PMA': 'PMAAction',
    'PSA': 'PSAAction',
    'ECBT': 'ECBTAction',
    'ECBNT': 'ECBNTAction',
    'NAB': 'NABAction'
  }

  const routeName = routeMap[caseItem.case_type] || 'CaseRiskReview'
  return {
    name: routeName,
    params: { case_id: caseItem.case_id },
    query: { status: caseItem.status }
  }
}

const fetchCases = async () => {
  loading.value = true
  error.value = null
  try {
    const token = localStorage.getItem('jwt')
    if (!token) {
      throw new Error("Authentication token not found")
    }

    const response = await axios.get(API_ENDPOINTS.NEW_CASE_LIST, {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      params: {
        ack_no: filters.value.ackNo,
        status: filters.value.status,
        case_type: filters.value.complaintType
      }
    })

    if (response.data && Array.isArray(response.data.cases)) {
      cases.value = response.data.cases
      page.value = 1 // Reset to first page on new data
    } else {
      throw new Error("Invalid response format")
    }
  } catch (err) {
    error.value = err.response?.data?.message || err.message
    if (err.response?.status === 401) {
      router.push('/login')
    }
    cases.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchCases)

const filteredCases = computed(() => {
  return cases.value.filter(c => {
    const matchesAckNo = !filters.value.ackNo ||
                         (c.source_ack_no && c.source_ack_no.toLowerCase().includes(filters.value.ackNo.trim().toLowerCase()))

    const matchesStatus = !filters.value.status ||
                          (c.status && c.status.toLowerCase() === filters.value.status.toLowerCase())

    const matchesComplaintType = !filters.value.complaintType ||
                                 (c.case_type && c.case_type.toLowerCase() === filters.value.complaintType.toLowerCase())

    return matchesAckNo && matchesStatus && matchesComplaintType
  })
})

const totalPages = computed(() => Math.ceil(filteredCases.value.length / pageSize))

const pagedCases = computed(() =>
  filteredCases.value.slice((page.value - 1) * pageSize, page.value * pageSize)
)

const prevPage = () => {
  if (page.value > 1) page.value--
}

const nextPage = () => {
  if (page.value < totalPages.value) page.value++
}

const clearFilters = () => {
  filters.value.ackNo = ''
  filters.value.status = ''
  filters.value.complaintType = ''
  page.value = 1
  fetchCases()
}
</script>