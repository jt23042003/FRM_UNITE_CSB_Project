<template>
  <div class="dashboard-bg">
    <div class="dashboard-header">
      <h2>Review Assigned Cases</h2>
      <div v-if="globalSearch.trim()" class="search-results-info">
        Showing {{ totalFilteredItems }} of {{ totalItems }} cases matching "{{ globalSearch }}"
      </div>
      <div class="filters-row">
        <div class="search-bar-container">
          <span class="search-icon">
            <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7"/>
              <line x1="16.5" y1="16.5" x2="21" y2="21"/>
            </svg>
          </span>
          <input
            v-model="globalSearch"
            placeholder="Search across all columns..."
            class="filter-input enhanced-search-input"
            @input="handleGlobalSearch"
          />
        </div>

        <select v-model="timeFilter" class="filter-input enhanced-status-select">
          <option value="">All Time</option>
          <option value="0">Today</option>
          <option value="1">Yesterday</option>
          <option value="3">Last 3 Days</option>
          <option value="7">Last 7 Days</option>
          <option value="10">Last 10 Days</option>
          <option value=">10">More than 10 Days</option>
        </select>

        <select v-model="daysAssignedFilter" class="filter-input enhanced-status-select">
          <option value="">All Days</option>
          <option value="0">Today (0 days)</option>
          <option value="1">1 day</option>
          <option value="2">2 days</option>
          <option value="3">3 days</option>
          <option value="5">5 days</option>
          <option value="7">7 days</option>
          <option value="10">10 days</option>
          <option value="15">15 days</option>
          <option value="30">30 days</option>
          <option value=">30">More than 30 days</option>
        </select>
        
        <button @click="clearFilters" class="reset-btn">Clear All</button>
      </div>
    </div>
    <div class="dashboard-table-card">
      <div class="table-responsive">
        <table class="case-table">
        <colgroup>
          <col style="width: 8%"> <col style="width: 10%"> <col style="width: 14%"> <col style="width: 8%"> <col style="width: 10%"> <col style="width: 10%"> <col style="width: 10%"> <col style="width: 12%"> <col style="width: 8%"> <col style="width: 8%"> <col style="width: 12%">
        </colgroup>
        <thead>
          <tr>
            <th @click="sortBy('case_id')" class="sortable-header">
              Case ID
              <span v-if="sortColumn === 'case_id'" class="sort-icon">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('source_ack_no')" class="sortable-header">
              ACK ID
              <span v-if="sortColumn === 'source_ack_no'" class="sort-icon">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('case_type')" class="sortable-header">
              Complaint/Detection Type
              <span v-if="sortColumn === 'case_type'" class="sort-icon">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('is_operational')" class="sortable-header">
              Operational
              <span v-if="sortColumn === 'is_operational'" class="sort-icon">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('location')" class="sortable-header">
              Location
              <span v-if="sortColumn === 'location'" class="sort-icon">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('disputed_amount')" class="sortable-header">
              Disputed Amount
              <span v-if="sortColumn === 'disputed_amount'" class="sort-icon">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('created_by')" class="sortable-header">
              Created By
              <span v-if="sortColumn === 'created_by'" class="sort-icon">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('assign_date')" class="sortable-header">
              Assigned Time
              <span v-if="sortColumn === 'assign_date'" class="sort-icon">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('days_assigned')" class="sortable-header">
              Days Assigned
              <span v-if="sortColumn === 'days_assigned'" class="sort-icon">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('status')" class="sortable-header">
              Status
              <span v-if="sortColumn === 'status'" class="sort-icon">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('assigned_to')" class="sortable-header">
              Assigned To
              <span v-if="sortColumn === 'assigned_to'" class="sort-icon">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
             <td colspan="11" style="padding: 12px;">
               <div class="skeleton-table">
                 <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
                 <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
                 <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
               </div>
             </td>
          </tr>
          <tr v-else-if="paginatedCases.length > 0" v-for="caseItem in paginatedCases" :key="caseItem.case_id">
            <td>
              <router-link :to="getCaseLink(caseItem)" class="ack-link">
                {{ caseItem.case_id }}
              </router-link>
            </td>
            <td>{{ caseItem.source_ack_no || '—' }}</td>
            <td><span class="chip case-type">{{ caseItem.case_type || '—' }}</span></td>
            <td>
              <span :class="['badge', caseItem.is_operational ? 'operational' : 'non-operational']">
                {{ caseItem.is_operational ? 'Yes' : 'No' }}
              </span>
            </td>
            <td> <span class="location-null"> {{ caseItem.location || '—' }} </span></td>
            
            <td class="numeric">
              <span v-if="caseItem.disputed_amount !== null && !isNaN(Number(caseItem.disputed_amount))" class="disputed-amount">
                ₹{{ Number(caseItem.disputed_amount).toLocaleString('en-IN') }}
              </span>
              <span v-else class="disputed-amount-null">—</span>
            </td>
            <td>{{ caseItem.created_by || '—' }}</td>
            <td>
              <span v-if="caseItem.assign_date || caseItem.assign_time">
                {{ formatDateTimeIST(caseItem.assign_date, caseItem.assign_time) }}
              </span>
              <span v-else>—</span>
            </td>
            <td class="numeric">
              <span v-if="caseItem.assign_date" class="days-assigned">
                {{ calculateDaysAssigned(caseItem.assign_date) }}
              </span>
              <span v-else>—</span>
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
              <span v-else>—</span>
            </td>
          </tr>
          <tr v-else>
            <td colspan="11" style="padding: 12px;">
              <div class="empty-state">
                <div class="icon">📋</div>
                <div class="title">No assigned cases</div>
                <div class="hint">Once cases are assigned to you, they will appear here.</div>
              </div>
            </td>
          </tr>
        </tbody>
        </table>
      </div>

      <!-- Mobile Card View -->
      <div class="case-cards" v-if="!loading && paginatedCases.length > 0">
        <div class="case-card" v-for="caseItem in paginatedCases" :key="caseItem.case_id" @click="$router.push(getCaseLink(caseItem))">
          <div class="card-row header">
            <div class="case-id">#{{ caseItem.case_id }}</div>
            <div class="status"><span :class="['status-badge', caseItem.status ? caseItem.status.toLowerCase().replace(/ /g,'-') : '']">{{ caseItem.status || '-' }}</span></div>
          </div>
          <div class="card-row">
            <span class="label">ACK:</span>
            <span class="value">{{ caseItem.source_ack_no || '—' }}</span>
          </div>
          <div class="card-row">
            <span class="label">Type:</span>
            <span class="value chip">{{ caseItem.case_type || '—' }}</span>
          </div>
          <div class="card-row">
            <span class="label">Operational:</span>
            <span class="value"><span :class="['badge', caseItem.is_operational ? 'operational' : 'non-operational']">{{ caseItem.is_operational ? 'Yes' : 'No' }}</span></span>
          </div>
          <div class="card-row">
            <span class="label">Location:</span>
            <span class="value">{{ caseItem.location || '—' }}</span>
          </div>
          <div class="card-row">
            <span class="label">Disputed:</span>
            <span class="value">{{ caseItem.disputed_amount != null ? '₹' + Number(caseItem.disputed_amount).toLocaleString('en-IN') : '—' }}</span>
          </div>
          <div class="card-row">
            <span class="label">Assigned:</span>
            <span class="value">{{ formatDateTimeIST(caseItem.assign_date, caseItem.assign_time) }}</span>
          </div>
          <div class="card-row">
            <span class="label">Days:</span>
            <span class="value">{{ caseItem.assign_date ? calculateDaysAssigned(caseItem.assign_date) : '—' }}</span>
          </div>
          <div class="card-row footer">
            <span class="assigned">{{ caseItem.assigned_to || '—' }}</span>
          </div>
        </div>
      </div>
      <div class="pagination-row" v-if="!loading && totalFilteredItems > 0">
        <div>
          <span>Rows per page: {{ pageSize }}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
          <span v-if="!loading">{{ startIndex }}-{{ endIndex }} of {{ totalFilteredItems }}</span>
          <span v-else>Loading...</span>
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
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import '../assets/CaseDetails.css';
import { API_ENDPOINTS } from '../config/api.js';

const router = useRouter();

// --- Reactive State ---
const cases = ref([]);
const page = ref(1);
const pageSize = 15;
const loading = ref(true);
const error = ref(null);
const totalItems = ref(0);

// Global search, sorting, and time filter
const globalSearch = ref('');
const sortColumn = ref('');
const sortDirection = ref('asc');
const timeFilter = ref('');
const daysAssignedFilter = ref('');

// --- API Fetching (Fetch ALL assigned cases) ---
const fetchCases = async () => {
  loading.value = true;
  error.value = null;
  try {
    const token = localStorage.getItem('jwt');
    if (!token) throw new Error("Authentication token not found");

    // Fetch ALL assigned cases with a large limit
    const response = await axios.get('/api/assigned-cases', {
      headers: { 'Authorization': `Bearer ${token}` },
      params: {
        skip: 0,
        limit: 10000, // Large limit to get all cases
      }
    });

    if (response.data && Array.isArray(response.data.cases)) {
      cases.value = response.data.cases;
      totalItems.value = response.data.cases.length;
    } else {
      throw new Error("Invalid response format");
    }
  } catch (err) {
    error.value = err.response?.data?.message || err.message;
    if (err.response?.status === 401) router.push('/login');
    cases.value = [];
    totalItems.value = 0;
  } finally {
    loading.value = false;
  }
};

// --- Helper function to format date and time in IST ---
const formatDateTimeIST = (assignDate, assignTime) => {
  if (!assignDate && !assignTime) return '—';
  
  try {
    let dateTime;
    
    if (assignDate && assignTime) {
      // Combine date and time
      const dateStr = assignDate.includes('T') ? assignDate : `${assignDate}T${assignTime}`;
      dateTime = new Date(dateStr);
    } else if (assignDate) {
      // Only date available
      dateTime = new Date(assignDate);
    } else {
      // Only time available (use current date)
      const today = new Date().toISOString().split('T')[0];
      dateTime = new Date(`${today}T${assignTime}`);
    }
    
    // Convert to IST (UTC+5:30)
    const istDateTime = new Date(dateTime.getTime() + (5.5 * 60 * 60 * 1000));
    
    // Format date in Indian format
    const dateStr = istDateTime.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
    
    // Format time in 24-hour format
    const timeStr = istDateTime.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
    
    return `${dateStr} ${timeStr}`;
  } catch (error) {
    console.error('Error formatting date/time:', error);
    return '—';
  }
};

// --- Helper function to calculate days assigned ---
const calculateDaysAssigned = (assignDate) => {
  if (!assignDate) return 0;
  
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Reset time to start of day
    
    const assignedDate = new Date(assignDate);
    assignedDate.setHours(0, 0, 0, 0); // Reset time to start of day
    
    const timeDiff = today.getTime() - assignedDate.getTime();
    const dayDiff = Math.floor(timeDiff / (1000 * 3600 * 24));
    
    // Return 0 if the date is in the future
    return Math.max(0, dayDiff);
  } catch (error) {
    console.error('Error calculating days assigned:', error);
    return 0;
  }
};

// --- Global Search Function ---
const handleGlobalSearch = () => {
  page.value = 1;
};

// --- Sorting Function ---
const sortBy = (column) => {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn.value = column;
    sortDirection.value = 'asc';
  }
  page.value = 1;
};

// --- Client-Side Processing (Filtering and Sorting on ALL data) ---
const filteredAndSortedCases = computed(() => {
  let casesToProcess = [...cases.value];

  // Consolidate cases with multiple assignments
  const consolidated = new Map();
  casesToProcess.forEach(caseItem => {
    const caseId = caseItem.case_id;
    if (consolidated.has(caseId)) {
      const existingCase = consolidated.get(caseId);
      if (caseItem.assigned_to && !existingCase.assigned_to.includes(caseItem.assigned_to)) {
        existingCase.assigned_to += ', ' + caseItem.assigned_to;
      }
    } else {
      consolidated.set(caseId, { ...caseItem });
    }
  });
  casesToProcess = Array.from(consolidated.values());

  // Global search across all columns
  if (globalSearch.value.trim()) {
    const searchTerm = globalSearch.value.toLowerCase().trim();
    casesToProcess = casesToProcess.filter(caseItem => {
      return Object.values(caseItem).some(value => {
        if (value === null || value === undefined) return false;
        return String(value).toLowerCase().includes(searchTerm);
      });
    });
  }

  // Time filter
  if (timeFilter.value !== '') {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const selectedAge = timeFilter.value;

    casesToProcess = casesToProcess.filter(caseItem => {
      if (!caseItem.assign_date) return false;
      const assignDate = new Date(caseItem.assign_date);
      assignDate.setHours(0, 0, 0, 0);
      const timeDiff = today.getTime() - assignDate.getTime();
      const dayDiff = Math.floor(timeDiff / (1000 * 3600 * 24));
      if (dayDiff < 0) return false;

      if (selectedAge === '>10') {
        return dayDiff > 10;
      } else {
        const ageLimit = parseInt(selectedAge, 10);
        if (ageLimit === 0) return dayDiff === 0;
        if (ageLimit === 1) return dayDiff === 1;
        return dayDiff < ageLimit;
      }
    });
  }

  // Days Assigned filter
  if (daysAssignedFilter.value !== '') {
    const selectedDays = daysAssignedFilter.value;

    casesToProcess = casesToProcess.filter(caseItem => {
      const daysAssigned = calculateDaysAssigned(caseItem.assign_date);
      
      if (selectedDays === '>30') {
        return daysAssigned > 30;
      } else {
        const dayLimit = parseInt(selectedDays, 10);
        if (dayLimit === 0) return daysAssigned === 0;
        return daysAssigned === dayLimit;
      }
    });
  }

  // Sorting
  if (sortColumn.value) {
    casesToProcess.sort((a, b) => {
      let aValue = a[sortColumn.value];
      let bValue = b[sortColumn.value];

      // Special handling for days_assigned (calculated field)
      if (sortColumn.value === 'days_assigned') {
        aValue = calculateDaysAssigned(a.assign_date);
        bValue = calculateDaysAssigned(b.assign_date);
      } else {
        // Handle null/undefined values
        if (aValue === null || aValue === undefined) aValue = '';
        if (bValue === null || bValue === undefined) bValue = '';

        // Convert to string for comparison
        aValue = String(aValue).toLowerCase();
        bValue = String(bValue).toLowerCase();

        // Special handling for numeric values
        if (sortColumn.value === 'disputed_amount' || sortColumn.value === 'case_id') {
          aValue = parseFloat(aValue) || 0;
          bValue = parseFloat(bValue) || 0;
        }

        // Special handling for dates
        if (sortColumn.value === 'assign_date' || sortColumn.value === 'creation_date') {
          aValue = new Date(aValue || 0);
          bValue = new Date(bValue || 0);
        }

        // Special handling for boolean values
        if (sortColumn.value === 'is_operational') {
          aValue = aValue === 'true' || aValue === 'yes' ? 1 : 0;
          bValue = bValue === 'true' || bValue === 'yes' ? 1 : 0;
        }
      }

      if (sortDirection.value === 'asc') {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
      } else {
        return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
      }
    });
  }

  return casesToProcess;
});

// --- Pagination for filtered results ---
const paginatedCases = computed(() => {
  const startIndex = (page.value - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  return filteredAndSortedCases.value.slice(startIndex, endIndex);
});

// --- Updated total items based on filtered results ---
const totalFilteredItems = computed(() => filteredAndSortedCases.value.length);

// --- Actions and Pagination ---
function clearFilters() {
  globalSearch.value = '';
  sortColumn.value = '';
  sortDirection.value = 'asc';
  timeFilter.value = '';
  daysAssignedFilter.value = '';
  page.value = 1;
}

const totalPages = computed(() => Math.ceil(totalFilteredItems.value / pageSize));

const prevPage = () => {
  if (page.value > 1) {
    page.value--;
  }
};

const nextPage = () => {
  if (page.value < totalPages.value) {
    page.value++;
  }
};

// --- Computed properties for pagination display ---
const startIndex = computed(() => (totalFilteredItems.value > 0 ? (page.value - 1) * pageSize + 1 : 0));
const endIndex = computed(() => Math.min((page.value - 1) * pageSize + paginatedCases.value.length, totalFilteredItems.value));

// --- Navigation ---
function getCaseLink(caseItem) {
  const routeMap = {
    'VM': 'OperationalAction', 
    'BM': 'BeneficiaryAction', 
    'PMA': 'PMAAction',
    'PVA': 'PVAAction',
    'PSA': 'PSAAction', 
    'ECBT': 'ECBTAction', 
    'ECBNT': 'ECBNTAction', 
    'NAB': 'NABAction',
    'MM': 'MobileMatchingAction'
  };
  let routeName = routeMap[caseItem.case_type] || 'CaseRiskReview';
  if (caseItem.case_type === 'PSA' && caseItem.created_by === 'EmailSystem') {
    routeName = 'PSAEmailAction';
  }
  if (caseItem.case_type === 'ECBT' && caseItem.created_by === 'EmailSystem') {
    routeName = 'ECBTEmailAction';
  }
  if (caseItem.case_type === 'ECBNT' && caseItem.created_by === 'EmailSystem') {
    routeName = 'ECBNTEmailAction';
  }
  return {
    name: routeName,
    params: { case_id: caseItem.case_id },
    query: { status: caseItem.status, review: 'true' }
  };
}

// --- Lifecycle Hook ---
onMounted(fetchCases);
</script>

<style scoped>
.filters-row {
  flex-wrap: wrap;
  gap: 12px;
}

.dashboard-table-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  margin-top: 24px;
  padding: 0 0 16px 0;
  max-height: 85vh;
  overflow-y: auto;
}

.table-responsive { width: 100%; overflow-x: auto; }
.case-table { width: 100%; border-collapse: collapse; font-size: 15px; min-width: 980px; }

.case-table thead th { position: sticky; top: 0; background: #f7f7f7; z-index: 2; padding: 14px 10px; font-weight: 700; color: #1e293b; text-transform: uppercase; letter-spacing: .4px; border-bottom: 2px solid #e9eef5; }

.case-table th, .case-table td { padding: 12px 10px; text-align: left; border-bottom: 1px solid #eef2f7; vertical-align: middle; }
.case-table tbody tr:nth-child(even) { background: #fbfdff; }
.case-table tbody tr:hover { background: #f3f7ff; transition: background .15s ease; }
.case-table td.numeric { text-align: right; font-variant-numeric: tabular-nums; }

.sortable-header {
  cursor: pointer;
  user-select: none;
  position: relative;
  transition: background-color 0.2s;
}

.sortable-header:hover { background-color: #eef4ff; }

.sort-icon {
  margin-left: 6px; font-weight: bold; color: #007bff;
}

.search-results-info {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
  font-style: italic;
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
.disputed-amount{
  margin-right: 100px;
}
.disputed-amount-null{
  margin-right: 130px;
}
.location-null{
  margin-left : 25px;
}
.case-type{
  margin-left: 50px;
}
.days-assigned {
  display: inline-block;
  background: #f8fafc;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  border: 1px solid #e2e8f0;
  min-width: 35px;
  text-align: center;
  margin-right: 75px;
}

/* Chips and badges (match Case Details) */
.chip { display: inline-block; padding: 2px 8px; border-radius: 8px; background: #eef2ff; color: #4338ca; font-weight: 600; font-size: 12px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; margin-left: 20px;}
.badge.operational { background: #e6f4ea; color: #18794e; }
.badge.non-operational { background: #fee2e2; color: #991b1b; }
.status-badge { display: inline-block; padding: 4px 10px; border-radius: 999px; font-weight: 700; font-size: 12px; }
.status-badge.new { background: #e0f2fe; color: #075985; }
.status-badge.assigned { background: #fef3c7; color: #92400e; }
.status-badge.closed { background: #dcfce7; color: #166534; }
.status-badge.open { background: #e9d5ff; color: #6b21a8; }

/* Mobile Card View */
.case-cards { display: none; }
.case-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); display: flex; flex-direction: column; gap: 6px; }
.case-card .card-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.case-card .card-row.header { margin-bottom: 4px; }
.case-card .case-id { font-weight: 700; color: #0f172a; }
.case-card .label { color: #64748b; font-size: 12px; }
.case-card .value { color: #0f172a; font-weight: 600; }
.case-card .footer { gap: 12px; font-size: 12px; color: #475569; }
.case-card:hover { border-color: #0d6efd; box-shadow: 0 2px 8px rgba(13,110,253,.15); cursor: pointer; }

@media (max-width: 768px) {
  .table-responsive { display: none; }
  .case-cards { display: grid; grid-template-columns: 1fr; gap: 10px; }
}
</style>