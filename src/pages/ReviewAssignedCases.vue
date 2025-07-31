<template>
  <div class="dashboard-bg">
    <div class="dashboard-header">
      <h2>Review Assigned Cases</h2>
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
          <col style="width: 10%;"> <col style="width: 12%"> <col style="width: 18%"> <col style="width: 10%"> <col style="width: 10%"> <col style="width: 12%"> <col style="width: 12%"> <col style="width: 14%"> <col style="width: 10%"> <col style="width: 14%">  
        </colgroup>
        <thead>
          <tr>
            <th>Case ID</th>
            <th>ACK ID</th>
            <th>Complaint/Detection Type</th>
            <th>Operational</th>
            <th>Location</th>
            <th>Disputed Amount</th>
            <th>Created By</th>
            <th>Assigned Time</th>
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
            <td>
              <span :class="['badge', caseItem.is_operational ? 'operational' : 'non-operational']">
                {{ caseItem.is_operational ? 'Yes' : 'No' }}
              </span>
            </td>
            <td>{{ caseItem.location || '-' }}</td>
            <td>
              <span v-if="caseItem.disputed_amount !== null && !isNaN(Number(caseItem.disputed_amount))">
                ₹{{ Number(caseItem.disputed_amount).toLocaleString('en-IN') }}
              </span>
              <span v-else>-</span>
            </td>
            <td>{{ caseItem.created_by || '-' }}</td>
            <td>
              <!-- Show actual assignment date and time -->
              <span v-if="caseItem.assign_date || caseItem.assign_time">
                {{ caseItem.assign_date ? new Date(caseItem.assign_date).toLocaleDateString('en-IN') : '-' }}
                <span v-if="caseItem.assign_time">{{ ' ' + caseItem.assign_time.slice(0,8) }}</span>
              </span>
              <span v-else>-</span>
            </td>
            <td>
              <span :class="['status-badge', caseItem.status ? caseItem.status.toLowerCase().replace(/ /g,'-') : '']">
                {{ caseItem.status || '-' }}
              </span>
            </td>
            <td>
              <span v-if="caseItem.assigned_to" class="assigned-users">
                {{ caseItem.assigned_to }}
              </span>
              <span v-else>-</span>
            </td>
          </tr>
          <tr v-if="pagedCases.length === 0">
            <td colspan="10" style="text-align:center; padding: 20px;">No assigned cases found.</td>
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
const pageSize = 13
const loading = ref(false)
const error = ref(null)
const totalItems = ref(0)

const filters = ref({
  ackNo: '',
  status: '',
  complaintType: ''
})

// Computed properties for pagination display
const startIndex = computed(() => ((page.value - 1) * pageSize) + 1)
const endIndex = computed(() => Math.min(page.value * pageSize, totalItems.value))
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize))

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
    query: { status: caseItem.status, review: 'true' }
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

    const response = await axios.get('/api/assigned-cases', {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      params: {
        search_source_ack_no: filters.value.ackNo,
        status_filter: filters.value.status,
        skip: (page.value - 1) * pageSize,
        limit: pageSize
      }
    })

    if (response.data && Array.isArray(response.data.cases)) {
      cases.value = response.data.cases
      if (response.data.cases.length === pageSize) {
        totalItems.value = page.value * pageSize + 1
      } else {
        totalItems.value = (page.value - 1) * pageSize + response.data.cases.length
      }
    } else {
      throw new Error("Invalid response format")
    }
  } catch (err) {
    error.value = err.response?.data?.message || err.message
    if (err.response?.status === 401) {
      router.push('/login')
    }
    cases.value = []
    totalItems.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(fetchCases)

// Consolidate cases by case_id and combine assigned_to values
const pagedCases = computed(() => {
  const consolidatedCases = new Map()
  
  cases.value.forEach(caseItem => {
    const caseId = caseItem.case_id
    
    if (consolidatedCases.has(caseId)) {
      // Case already exists, append assigned_to to existing list
      const existingCase = consolidatedCases.get(caseId)
      if (caseItem.assigned_to && !existingCase.assigned_to.includes(caseItem.assigned_to)) {
        existingCase.assigned_to = existingCase.assigned_to + ', ' + caseItem.assigned_to
      }
    } else {
      // New case, add to map
      consolidatedCases.set(caseId, { ...caseItem })
    }
  })
  
  return Array.from(consolidatedCases.values())
})

const prevPage = () => {
  if (page.value > 1) {
    page.value--
    fetchCases()
  }
}

const nextPage = () => {
  if (page.value < totalPages.value) {
    page.value++
    fetchCases()
  }
}

const clearFilters = () => {
  filters.value.ackNo = ''
  filters.value.status = ''
  filters.value.complaintType = ''
  page.value = 1
  fetchCases()
}
</script>

<style scoped>
.dashboard-table-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  margin-top: 24px;
  padding: 0 0 16px 0;
  max-height: 60vh;
  overflow-y: auto;
}

.case-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 15px;
}

.case-table thead th {
  position: sticky;
  top: 0;
  background: #f7f7f7;
  z-index: 2;
}

.case-table th, .case-table td {
  padding: 10px 8px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.pagination-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding: 0 16px;
}

.assigned-users {
  display: inline-block;
  background: #f0f8ff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 13px;
  color: #2c5aa0;
  border: 1px solid #d1e7ff;
  white-space: normal;
  word-wrap: break-word;
  max-width: 250px;
  line-height: 1.3;
}
</style> 