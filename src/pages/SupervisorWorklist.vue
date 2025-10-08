<template>
  <div class="dashboard-bg">
    <div class="dashboard-header">
      <div class="header-content">
        <h2>Supervisor Worklist</h2>
      </div>
    </div>
    <div class="search-section">
      <div class="search-container">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Search by Case ID, ACK number, or Case Type..." 
          class="search-input"
        />
        <button 
          v-if="searchQuery" 
          @click="clearSearch" 
          class="clear-button"
          title="Clear search"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
    <div class="dashboard-table-card">
      <div class="table-responsive">
        <table class="case-table">
          <thead>
            <tr>
              <th>Case ID</th>
              <th>ACK</th>
              <th>Type</th>
              <th>Status</th>
              <th>Created</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" style="padding: 12px;">
                <div class="skeleton-table">
                  <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
                  <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
                </div>
              </td>
            </tr>
            <tr v-else-if="filteredCases.length === 0">
              <td colspan="6" style="padding: 12px;">
                <div class="empty-state">
                  <div class="icon">✅</div>
                  <div class="title">All clear</div>
                  <div class="hint">No pending approvals at the moment.</div>
                </div>
              </td>
            </tr>
            <tr v-else v-for="c in paginatedCases" :key="c.case_id">
              <td>
                <router-link :to="toCase(c)" class="link">#{{ c.case_id }}</router-link>
              </td>
              <td>{{ c.source_ack_no || '—' }}</td>
              <td><span class="chip">{{ c.case_type || '—' }}</span></td>
              <td><span :class="['status-badge', (c.status || '').toLowerCase().replace(/ /g,'-')]">{{ c.status || '-' }}</span></td>
              <td>{{ formatDateIST(c.creation_date) }}</td>
              <td>
                <router-link :to="toCase(c)" class="link">Open</router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="pagination-row" v-if="!loading && filteredCases.length > 0">
        <div>
          <span>Rows per page: {{ pageSize }}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
          <span>{{ startIndex }}-{{ endIndex }} of {{ filteredCases.length }}</span>
          <button @click="prevPage" :disabled="page === 1">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M15 18l-6-6 6-6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <button @click="nextPage" :disabled="page >= totalPages">
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
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

const loading = ref(true)
const cases = ref([])
const page = ref(1)
const pageSize = 15
const searchQuery = ref('')



function toCase(c) {
  // Navigate to beneficiary/operational/etc based on type
  const map = { 
    VM: 'OperationalAction', 
    BM: 'BeneficiaryAction', 
    PMA: 'PMAAction', 
    PVA: 'PVAAction',
    PSA: 'PSAAction', 
    ECBT: 'ECBTAction', 
    ECBNT: 'ECBNTAction', 
    NAB: 'NABAction',
    MM: 'MobileMatchingAction'
  }
  const name = map[c.case_type] || 'CaseRiskReview'
  return { name, params: { case_id: c.case_id }, query: { review: 'true' } }
}

// Helper function to format date in IST
function formatDateIST(creationDate) {
  if (!creationDate) return '—';
  
  try {
    const date = new Date(creationDate);
    // Convert to IST (UTC+5:30)
    const istDate = new Date(date.getTime() + (5.5 * 60 * 60 * 1000));
    
    // Format date in Indian format
    return istDate.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return '—';
  }
}

onMounted(async () => {
  try {
    const token = localStorage.getItem('jwt')
    const resp = await axios.get('/api/supervisor/pending-approvals', { headers: { Authorization: `Bearer ${token}` } })
    cases.value = resp.data?.cases || []
  } catch (e) {
    cases.value = []
  } finally {
    loading.value = false
  }
})

// Filter cases based on search query
const filteredCases = computed(() => {
  if (!searchQuery.value.trim()) {
    return cases.value
  }
  
  const query = searchQuery.value.toLowerCase().trim()
  return cases.value.filter(caseItem => {
    return (
      caseItem.case_id?.toString().toLowerCase().includes(query) ||
      caseItem.source_ack_no?.toLowerCase().includes(query) ||
      caseItem.case_type?.toLowerCase().includes(query) ||
      caseItem.status?.toLowerCase().includes(query)
    )
  })
})

const paginatedCases = computed(() => {
  const start = (page.value - 1) * pageSize
  const end = start + pageSize
  return filteredCases.value.slice(start, end)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredCases.value.length / pageSize)))
const startIndex = computed(() => (filteredCases.value.length > 0 ? (page.value - 1) * pageSize + 1 : 0))
const endIndex = computed(() => Math.min(page.value * pageSize, filteredCases.value.length))

const prevPage = () => { if (page.value > 1) page.value-- }
const nextPage = () => { if (page.value < totalPages.value) page.value++ }

// Reset page when search query changes
watch(searchQuery, () => {
  page.value = 1
})

// Clear search function
const clearSearch = () => {
  searchQuery.value = ''
}


</script>

<style scoped>
.dashboard-bg { padding: 16px; }
.dashboard-header { margin-bottom: 12px; }
.header-content h2 { margin: 0; }
.search-section { margin-bottom: 16px; display: flex; justify-content: flex-start; }
.search-container { max-width: 400px; position: relative; }
.search-input { 
  width: 100%; 
  padding: 8px 40px 8px 12px; 
  border: 1px solid #d1d5db; 
  border-radius: 6px; 
  font-size: 14px; 
  background: white;
  transition: border-color 0.2s;
}
.search-input:focus { 
  outline: none; 
  border-color: #3b82f6; 
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
.clear-button {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  color: #6b7280;
  transition: color 0.2s, background-color 0.2s;
}
.clear-button:hover {
  color: #374151;
  background-color: #f3f4f6;
}
.table-responsive { overflow-x: auto; }
.case-table { width: 100%; border-collapse: collapse; }
.case-table th, .case-table td { padding: 10px; border-bottom: 1px solid #eee; text-align: left; }
.chip { display: inline-block; padding: 2px 8px; border-radius: 8px; background: #eef2ff; color: #4338ca; font-weight: 600; font-size: 12px; }
.status-badge { display: inline-block; padding: 4px 10px; border-radius: 999px; font-weight: 700; font-size: 12px; background: #f3f4f6; color: #111827; text-transform: capitalize; }
.link { color: #0d6efd; text-decoration: none; font-weight: 600; }
.link:hover { text-decoration: underline; }
</style>

