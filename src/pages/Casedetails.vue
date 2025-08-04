<template>
    <div class="dashboard-bg">
    <div class="dashboard-header">
      <h2>Case View Dashboard</h2>
              <div v-if="globalSearch.trim()" class="search-results-info">
                  <span v-if="isAccountNumber(globalSearch)">
          Showing {{ totalFilteredItems }} of {{ totalItems }} cases matching account number "{{ globalSearch }}"
        </span>
          <span v-else>
            Showing {{ totalFilteredItems }} of {{ totalItems }} cases matching "{{ globalSearch }}"
          </span>
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
              placeholder="Search across all columns or by account number..."
              class="filter-input enhanced-search-input"
              @input="handleGlobalSearch"
            />
        </div>
        
        <button @click="clearFilters" class="reset-btn">Clear All</button>
      </div>
    </div>

    <div class="dashboard-table-card">
      <table class="case-table">
        <colgroup>
          <col style="width: 10%;"> <col style="width: 12%"> <col style="width: 18%"> <col style="width: 10%"> <col style="width: 10%"> <col style="width: 12%"> <col style="width: 12%"> <col style="width: 14%"> <col style="width: 10%"> <col style="width: 14%">  
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
            <th @click="sortBy('creation_date')" class="sortable-header">
              Created Time
              <span v-if="sortColumn === 'creation_date'" class="sort-icon">
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
            <td colspan="10" style="text-align:center; padding: 20px;">⏳ Loading cases...</td>
          </tr>
          <tr v-else-if="paginatedCases.length > 0" v-for="caseItem in paginatedCases" :key="caseItem.case_id">
            <td>
              <router-link :to="getCaseLink(caseItem)" class="ack-link">
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
              <span v-if="caseItem.creation_date || caseItem.creation_time">
                {{ caseItem.creation_date ? new Date(caseItem.creation_date).toLocaleDateString('en-IN') : '-' }}
                <span v-if="caseItem.creation_time">{{ ' ' + caseItem.creation_time.slice(0,8) }}</span>
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
          <tr v-else>
            <td colspan="10" style="text-align:center; padding: 20px;">No cases found matching your criteria.</td>
          </tr>
        </tbody>
      </table>
      <div class="pagination-row">
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
const cases = ref([]); // Holds raw data for the current page from the API
const page = ref(1);
const pageSize = 15;
const loading = ref(true);
const error = ref(null);
const totalItems = ref(0);

// Global search and sorting
const globalSearch = ref('');
const sortColumn = ref('');
const sortDirection = ref('asc');

// --- API Fetching (Fetch ALL cases for client-side processing) ---
const fetchCases = async () => {
  loading.value = true;
  error.value = null;
  try {
    const token = localStorage.getItem('jwt');
    if (!token) throw new Error("Authentication token not found");

    // Fetch ALL cases with a large limit to get complete dataset
    const response = await axios.get(API_ENDPOINTS.NEW_CASE_LIST, {
      headers: { 'Authorization': `Bearer ${token}` },
      params: {
        skip: 0,
        limit: 10000, // Large limit to get all cases
      },
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

// --- Helper function to check if search term is an account number ---
const isAccountNumber = (searchTerm) => {
  return /^\d+$/.test(searchTerm.trim());
};

// --- Global Search Function ---
const handleGlobalSearch = () => {
  // Reset to page 1 when searching
  page.value = 1;
  // The filtering is handled by computed property
};

// --- Sorting Function ---
const sortBy = (column) => {
  if (sortColumn.value === column) {
    // Toggle direction if same column
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    // New column, start with ascending
    sortColumn.value = column;
    sortDirection.value = 'asc';
  }
  // Reset to page 1 when sorting
  page.value = 1;
};

// --- Client-Side Processing (Filtering and Sorting on ALL data) ---
const filteredAndSortedCases = computed(() => {
  let casesToProcess = [...cases.value];

  // Global search across all columns
  if (globalSearch.value.trim()) {
    const searchTerm = globalSearch.value.toLowerCase().trim();
    casesToProcess = casesToProcess.filter(caseItem => {
      // Check if search term matches any direct field values
      const directMatch = Object.values(caseItem).some(value => {
        if (value === null || value === undefined) return false;
        return String(value).toLowerCase().includes(searchTerm);
      });

      // If direct match found, include the case
      if (directMatch) return true;

      // Special handling for account number search
      // Check if the search term looks like an account number (contains only digits)
      if (isAccountNumber(searchTerm)) {
        // Search in i4c_data fields if available
        if (caseItem.i4c_data) {
          const toAccount = caseItem.i4c_data.to_account;
          const accountNumber = caseItem.i4c_data.account_number;
          
          // Check if search term matches either account number field
          if ((toAccount && String(toAccount).includes(searchTerm)) ||
              (accountNumber && String(accountNumber).includes(searchTerm))) {
            return true;
          }
        }
      }

      return false;
    });
  }

  // Sorting
  if (sortColumn.value) {
    casesToProcess.sort((a, b) => {
      let aValue = a[sortColumn.value];
      let bValue = b[sortColumn.value];

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
      if (sortColumn.value === 'creation_date') {
        aValue = new Date(aValue || 0);
        bValue = new Date(bValue || 0);
      }

      // Special handling for boolean values
      if (sortColumn.value === 'is_operational') {
        aValue = aValue === 'true' || aValue === 'yes' ? 1 : 0;
        bValue = bValue === 'true' || bValue === 'yes' ? 1 : 0;
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
  page.value = 1;
  // No need to fetch again since we have all data
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
    'VM': 'OperationalAction', 'BM': 'BeneficiaryAction', 'PMA': 'PMAAction',
    'PSA': 'PSAAction', 'ECBT': 'ECBTAction', 'ECBNT': 'ECBNTAction', 'NAB': 'NABAction'
  };
  const routeName = routeMap[caseItem.case_type] || 'CaseRiskReview';
  return {
    name: routeName,
    params: { case_id: caseItem.case_id },
    query: { status: caseItem.status }
  };
}

// --- Lifecycle Hook ---
onMounted(fetchCases);
</script>

<style scoped>
/* Your existing styles are fine and will work with this logic */
.dashboard-table-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  margin-top: 24px;
  padding: 0 0 16px 0;
  max-height: 65vh;
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
  padding: 12px 8px;
}

.case-table th, .case-table td {
  padding: 10px 8px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.sortable-header {
  cursor: pointer;
  user-select: none;
  position: relative;
  transition: background-color 0.2s;
}

.sortable-header:hover {
  background-color: #e8e8e8;
}

.sort-icon {
  margin-left: 4px;
  font-weight: bold;
  color: #007bff;
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
</style>