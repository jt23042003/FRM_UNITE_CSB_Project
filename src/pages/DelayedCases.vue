<template>
  <div class="delayed-cases-page">
    <div class="page-header">
      <h1>Delayed Cases</h1>
      <p class="page-description">
        <span v-if="delayedCasesData.case_type === 'risk_officer'">
          Risk officer cases with no action for more than {{ delayedCasesData.threshold_days }} days
        </span>
        <span v-else-if="delayedCasesData.case_type === 'department'">
          {{ delayedCasesData.department }} department cases with no action for more than {{ delayedCasesData.threshold_days }} days
        </span>
        <span v-else>
          Cases that have been in the system for more than {{ delayedCasesData.threshold_days }} days with status 'new'
        </span>
      </p>
    </div>

    <div class="delayed-cases-content">
      <!-- Loading State -->
      <div v-if="loadingDelayedCases" class="loading-container">
        <div class="loading-spinner"></div>
        <p>Loading delayed cases...</p>
      </div>

      <!-- No Delayed Cases -->
      <div v-else-if="!delayedCasesData.delayed_cases || delayedCasesData.delayed_cases.length === 0" class="no-cases">
        <div class="no-cases-icon">✅</div>
        <h3>No Delayed Cases</h3>
        <p>All cases are being processed within the expected timeframe.</p>
      </div>

      <!-- Delayed Cases Table -->
      <div v-else class="delayed-cases-table-container">
        <div class="table-header">
          <h3>
            <span v-if="delayedCasesData.case_type === 'risk_officer'">Risk Officer Delayed Cases</span>
            <span v-else-if="delayedCasesData.case_type === 'department'">{{ delayedCasesData.department }} Department Delayed Cases</span>
            <span v-else>Delayed Cases</span>
            ({{ filteredCases.length }} of {{ delayedCasesData.total_count }} total)
          </h3>
          <div class="header-controls">
            <div class="search-container">
              <input 
                v-model="searchQuery" 
                type="text" 
                placeholder="Search by Case ID, ACK ID, Type, Status, Assigned To..." 
                class="search-input"
                @input="handleSearch"
              />
              <button 
                v-if="searchQuery" 
                @click="clearSearch" 
                class="clear-search-btn"
                title="Clear search"
              >
                ✕
              </button>
            </div>
            <div class="threshold-info">
              <span class="threshold-badge">Threshold: {{ delayedCasesData.threshold_days }} days</span>
            </div>
          </div>
        </div>

        <div class="table-wrapper">
          <table class="delayed-cases-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>ACK ID</th>
                <th>Type</th>
                <th>Status</th>
                <th>Days Old</th>
                <th>Assigned To</th>
                <th>Last Action</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="caseItem in filteredCases" :key="caseItem.case_id" class="delayed-row">
                <td class="case-id">{{ caseItem.case_id }}</td>
                <td class="ack-id">{{ caseItem.source_ack_no }}</td>
                <td class="case-type">
                  <span class="type-badge">{{ caseItem.case_type }}</span>
                </td>
                <td class="status">
                  <span class="status-badge" :class="caseItem.status?.toLowerCase()">{{ caseItem.status }}</span>
                </td>
                <td class="days-old">
                  <span :class="['days-old-badge', getDaysOldClass(caseItem.days_old)]">
                    {{ caseItem.days_old }} days
                  </span>
                </td>
                <td class="assigned-to">{{ caseItem.current_assigned_to || 'Unassigned' }}</td>
                <td class="last-action">{{ formatDate(caseItem.last_action_date) || 'No action' }}</td>
                <td class="created-date">{{ formatDate(caseItem.creation_date) }}</td>
                <td class="action">
                  <button 
                    @click="viewCaseDetails(caseItem.case_id, caseItem.case_type)" 
                    class="btn-view-case"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

export default {
  name: 'DelayedCases',
  setup() {
    const loadingDelayedCases = ref(false)
    const searchQuery = ref('')
    const delayedCasesData = ref({
      delayed_cases: [],
      threshold_days: 0,
      total_count: 0,
      case_type: '',
      department: ''
    })

    const fetchDelayedCases = async () => {
      try {
        loadingDelayedCases.value = true
        
        // Get authentication token
        const token = localStorage.getItem('jwt')
        if (!token) {
          throw new Error('No authentication token found')
        }
        
        // Determine which endpoint to call based on user type
        const userType = localStorage.getItem('user_type')
        let endpoint = ''
        
        if (userType === 'super_user') {
          endpoint = '/api/super-user/delayed-cases'
        } else if (userType === 'supervisor') {
          endpoint = '/api/supervisor/delayed-cases'
        } else {
          throw new Error('Unauthorized access to delayed cases')
        }
        
        const response = await axios.get(endpoint, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        delayedCasesData.value = response.data
      } catch (error) {
        console.error('Error fetching delayed cases:', error)
        window.showNotification('Error loading delayed cases', 'error')
      } finally {
        loadingDelayedCases.value = false
      }
    }

    // Computed property for filtered cases based on search query
    const filteredCases = computed(() => {
      if (!searchQuery.value.trim()) {
        return delayedCasesData.value.delayed_cases
      }
      
      const query = searchQuery.value.toLowerCase().trim()
      return delayedCasesData.value.delayed_cases.filter(caseItem => {
        return (
          caseItem.case_id?.toString().toLowerCase().includes(query) ||
          caseItem.source_ack_no?.toLowerCase().includes(query) ||
          caseItem.case_type?.toLowerCase().includes(query) ||
          caseItem.status?.toLowerCase().includes(query) ||
          caseItem.current_assigned_to?.toLowerCase().includes(query) ||
          caseItem.assigned_by?.toLowerCase().includes(query)
        )
      })
    })

    const handleSearch = () => {
      // Search is handled by the computed property
      // This function can be used for additional search logic if needed
    }

    const clearSearch = () => {
      searchQuery.value = ''
    }

    const getDaysOldClass = (daysOld) => {
      if (daysOld >= 10) return 'critical'
      if (daysOld >= 7) return 'high'
      return 'medium'
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const viewCaseDetails = (caseId, caseType) => {
      let route = ''
      switch (caseType?.toUpperCase()) {
        case 'VM':
          route = `/operational-action/${caseId}`
          break
        case 'BM':
          route = `/beneficiary-action/${caseId}`
          break
        case 'PMA':
          route = `/pma-action/${caseId}`
          break
        case 'PVA':
          route = `/pva-action/${caseId}`
          break
        case 'PSA':
          route = `/psa-action/${caseId}`
          break
        case 'ECBT':
          route = `/ecbt-action/${caseId}`
          break
        case 'ECBNT':
          route = `/ecbnt-action/${caseId}`
          break
        case 'NAB':
          route = `/nab-action/${caseId}`
          break
        case 'MM':
          route = `/mobile-matching-action/${caseId}`
          break
        default:
          route = `/case-details/${caseId}`
          break
      }
      window.location.href = route
    }

    onMounted(() => {
      fetchDelayedCases()
    })

    return {
      loadingDelayedCases,
      searchQuery,
      delayedCasesData,
      filteredCases,
      fetchDelayedCases,
      handleSearch,
      clearSearch,
      getDaysOldClass,
      formatDate,
      viewCaseDetails
    }
  }
}
</script>

<style scoped>
.delayed-cases-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  color: #2c3e50;
  margin-bottom: 8px;
  font-size: 2rem;
}

.page-description {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin: 0;
}

.delayed-cases-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.loading-container {
  padding: 60px 20px;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.no-cases {
  padding: 60px 20px;
  text-align: center;
}

.no-cases-icon {
  font-size: 3rem;
  margin-bottom: 20px;
}

.no-cases h3 {
  color: #27ae60;
  margin-bottom: 10px;
}

.no-cases p {
  color: #7f8c8d;
  font-size: 1.1rem;
}

.delayed-cases-table-container {
  padding: 20px;
}

.table-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #ecf0f1;
}

.header-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  gap: 20px;
}

.search-container {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-input {
  width: 100%;
  padding: 10px 40px 10px 12px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  background: white;
}

.search-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.clear-search-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.clear-search-btn:hover {
  background: #c0392b;
  transform: translateY(-50%) scale(1.1);
}

.table-header h3 {
  color: #2c3e50;
  margin: 0;
  font-size: 1.3rem;
}

.threshold-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.threshold-badge {
  background: #e74c3c;
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
}

.table-wrapper {
  overflow-x: auto;
}

.delayed-cases-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.delayed-cases-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  padding: 15px 12px;
  text-align: left;
  border-bottom: 2px solid #dee2e6;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.delayed-cases-table td {
  padding: 15px 12px;
  border-bottom: 1px solid #e9ecef;
  vertical-align: middle;
}

.delayed-row:hover {
  background-color: #f8f9fa;
}

.case-id {
  font-weight: 600;
  color: #2c3e50;
  font-family: 'Courier New', monospace;
}

.ack-id {
  font-family: 'Courier New', monospace;
  color: #7f8c8d;
}

.type-badge {
  background: #3498db;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.status-badge.new {
  background: #e0f2fe;
  color: #075985;
}

.status-badge.assigned {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.closed {
  background: #dcfce7;
  color: #166534;
}

.status-badge.open {
  background: #e9d5ff;
  color: #6b21a8;
}

.status-badge.reopened {
  background: #fef2f2;
  color: #dc2626;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.approved {
  background: #dcfce7;
  color: #166534;
}

.status-badge.rejected {
  background: #fef2f2;
  color: #dc2626;
}

.days-old-badge {
  padding: 6px 10px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.85rem;
  text-align: center;
  display: inline-block;
  min-width: 80px;
}

.days-old-badge.medium {
  background: #f39c12;
  color: white;
}

.days-old-badge.high {
  background: #e67e22;
  color: white;
  animation: pulse 2s infinite;
}

.days-old-badge.critical {
  background: #e74c3c;
  color: white;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.assigned-to {
  color: #2c3e50;
  font-weight: 500;
}

.created-date {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.btn-view-case {
  background: #27ae60;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-view-case:hover {
  background: #229954;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.btn-view-case:active {
  transform: translateY(0);
}

/* Responsive Design */
@media (max-width: 768px) {
  .delayed-cases-page {
    padding: 15px;
  }
  
  .page-header h1 {
    font-size: 1.5rem;
  }
  
  .header-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  
  .search-container {
    max-width: none;
  }
  
  .delayed-cases-table th,
  .delayed-cases-table td {
    padding: 10px 8px;
    font-size: 0.85rem;
  }
  
  .days-old-badge {
    min-width: 60px;
    font-size: 0.8rem;
  }
}
</style>
