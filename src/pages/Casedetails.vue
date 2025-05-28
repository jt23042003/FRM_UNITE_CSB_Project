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
            v-model="filters.caseId"
            placeholder="Search by Acknowledgement Number"
            class="filter-input enhanced-search-input"
          />
        </div>
        <select v-model="filters.status" class="filter-input enhanced-status-select">
          <option value="">All Statuses</option>
          <option v-for="status in statuses" :key="status">{{ status }}</option>
        </select>
        <button @click="fetchCases" class="search-btn enhanced-search-btn">Search</button>
        <button @click="clearFilters" class="reset-btn enhanced-reset-btn">Clear</button>
      </div>
    </div>
    <div class="dashboard-table-card">
      <table class="case-table">
        <colgroup>
          <col style="width: 13%;">
          <col style="width: 18%;">
          <col style="width: 13%;">
          <col style="width: 12%;">
          <col style="width: 12%;">
          <col style="width: 15%;">
          <col style="width: 17%;">
        </colgroup>
        <thead>
          <tr>
            <th>ACK ID</th>
            <th>Complaint/Detection Type</th>
            <th>Source</th>
            <th>Case Label</th>
            <th>Location</th>
            <th>Transaction/Case Amount</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="caseItem in pagedCases" :key="caseItem.ack_no">
          <td>
            <router-link
              :to="`/case-details/${caseItem.ack_no}`"
              class="ack-link"
            >
              {{ caseItem.ack_no }}
            </router-link>
          </td>
          <td>{{ caseItem.complaint_type || '-' }}</td>
          <td>{{ caseItem.source || '-' }}</td>
          <td>{{ caseItem.match_type || '-' }}</td>
          <td>{{ caseItem.location || '-' }}</td>
          <td>
            <span v-if="caseItem.transaction_amount !== null && caseItem.transaction_amount !== undefined">
              ₹{{ Number(caseItem.transaction_amount).toLocaleString('en-IN') }}
            </span>
            <span v-else>-</span>
          </td>
          <td>
            <span :class="['status-badge', caseItem.status?.toLowerCase().replace(/ /g,'-')]">
              {{ caseItem.status || '-' }}
            </span>
          </td>
        </tr>
          <tr v-if="pagedCases.length === 0">
            <td colspan="7" style="text-align:center;">No cases found.</td>
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
import '../assets/CaseViewDashboard.css'

const statuses = [
  'New',
  'Open'
]

const cases = ref([])
const page = ref(1)
const pageSize = 25

const filters = ref({
  caseId: '',
  status: ''
})

const fetchCases = async () => {
  try {
    const res = await axios.get('http://34.47.219.225:9000/api/case-list')
    cases.value = Array.isArray(res.data.cases) ? res.data.cases : []
    page.value = 1
  } catch (err) {
    console.error('Failed to fetch data:', err)
    cases.value = []
  }
}


// Fetch data on mount
onMounted(fetchCases)

// Filter on frontend for search and status
const filteredCases = computed(() => {
  return cases.value.filter(c =>
    (!filters.value.caseId || (c.ack_no && c.ack_no.toLowerCase().includes(filters.value.caseId.trim().toLowerCase()))) &&
    (!filters.value.status || c.status === filters.value.status)
  )
})


const totalPages = computed(() =>
  Math.ceil(filteredCases.value.length / pageSize)
)

const pagedCases = computed(() =>
  filteredCases.value.slice((page.value - 1) * pageSize, page.value * pageSize)
)

const prevPage = () => { if (page.value > 1) page.value-- }
const nextPage = () => { if (page.value < totalPages.value) page.value++ }
const clearFilters = () => {
  filters.value.caseId = ''
  filters.value.status = ''
  page.value = 1
  fetchCases()
}
</script>
