<template>
        <div class="dashboard-bg">
    <div class="dashboard-header">
      <div class="header-content">
        <h2>Case View Dashboard</h2>
      </div>
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
        <button @click="toggleHelpDesk" class="help-desk-btn" :class="{ active: showHelpDesk }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10"/>
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          {{ showHelpDesk ? 'Hide Help' : 'Case Types Help' }}
        </button>
        <button v-if="userRole !== 'others'" @click="toggleBulkAction" class="bulk-action-btn" :class="{ active: isBulkActionMode }">
          {{ isBulkActionMode ? 'Cancel Bulk Action' : 'Perform Bulk Action' }}
        </button>
      </div>
    </div>

    <!-- Bulk Action Controls -->
    <div v-if="isBulkActionMode" class="bulk-action-controls">
      <div class="bulk-action-info">
        <div class="selection-info">
          <span class="selected-count">{{ selectedCases.length }} case(s) selected</span>
          <span v-if="showAssignment" class="assignable-info">
            ({{ assignableCasesCount }} assignable)
          </span>
          <span v-if="showClose" class="closable-info">
            ({{ selectedCases.length }} closable)
          </span>
        </div>
        <div class="selection-actions">
          <button @click="selectAllCases" class="select-all-btn">Select All</button>
          <button @click="clearSelection" class="clear-selection-btn">Clear Selection</button>
        </div>
      </div>
      <div class="bulk-action-buttons">
        <button @click="showAssignmentSection" class="bulk-assign-btn" :class="{ active: showAssignment }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="8.5" cy="7" r="4"></circle>
            <line x1="20" y1="8" x2="20" y2="14"></line>
            <line x1="23" y1="11" x2="17" y2="11"></line>
          </svg>
          Assign
        </button>
        <button @click="showCloseSection" class="bulk-close-btn" :class="{ active: showClose }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M18 6L6 18M6 6l12 12"></path>
          </svg>
          Close
        </button>
      </div>
    </div>

    <!-- Bulk Assignment Section -->
    <div v-if="isBulkActionMode && showAssignment" class="bulk-section">
      <div class="bulk-section-header">
        <h3>Bulk Assignment</h3>
        <p class="section-description">Assign selected cases to users with comments</p>
      </div>
      <div class="bulk-assignment-form">
        <div class="form-section">
          <div class="field-group">
            <label class="section-label">Assignments</label>
            <div class="assignments-container">
              <div v-for="(review, reviewIndex) in bulkAssignment.reviews" :key="review.id" class="review-comment-row">
                <div class="comment-user-selection-row">
                  <div class="select-group">
                    <label>Department</label>
                    <select v-model="review.selectedDepartment" class="compact-select" @change="handleBulkDepartmentChange(review)">
                      <option value="">Select Department</option>
                      <option v-for="dept in departments" :key="dept.id" :value="dept.name">
                        {{ dept.name }}
                      </option>
                    </select>
                  </div>
                  <div class="select-group">
                    <label>User</label>
                    <select v-model="review.userId" class="compact-select">
                      <option value="">Select User</option>
                      <option v-for="user in review.userList" :key="user.id" :value="user.name">
                        {{ user.name }}
                      </option>
                    </select>
                  </div>
                </div>
                <div class="comment-group">
                  <label>Comments</label>
                  <textarea v-model="review.text" placeholder="Add comments for this assignment..." class="compact-textarea"></textarea>
                </div>
                <button @click="removeBulkReviewCommentRow(reviewIndex)" v-if="bulkAssignment.reviews.length > 1" class="btn-remove-row" title="Remove Assignment Section">×</button>
              </div>
              <div class="action-buttons">
                <button @click="addBulkReviewCommentRow" class="btn-add-row">+ Add Assignment Section</button>
                <button @click="bulkAssignCases" class="btn-assign-primary">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="8.5" cy="7" r="4"></circle>
                    <line x1="20" y1="8" x2="20" y2="14"></line>
                    <line x1="23" y1="11" x2="17" y2="11"></line>
                  </svg>
                  Assign Selected Cases
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bulk Close Section -->
    <div v-if="isBulkActionMode && showClose" class="bulk-section">
      <div class="bulk-section-header">
        <h3>Bulk Close Cases</h3>
        <p class="section-description">Close selected cases with closure details and confirmation</p>
      </div>
      <div class="bulk-close-form">
        <div class="form-section">
          <div class="field-group">
            <label class="section-label">Closure Details</label>
            <div class="closure-details-container">
              <div class="closure-reason-group">
                <label>Closure Reason</label>
                <select v-model="bulkClose.closureLOV" class="compact-select">
                  <option value="">Select Reason</option>
                  <option v-for="item in closureReasons" :key="item.reason" :value="item.reason">
                    {{ item.reason }}
                  </option>
                </select>
              </div>
              <div class="closure-remarks-group">
                <label>Closure Remarks</label>
                <textarea v-model="bulkClose.closureRemarks" placeholder="Add detailed closure remarks..." class="compact-textarea"></textarea>
              </div>
            </div>
          </div>
        </div>
        
        <div class="form-section">
          <label class="section-label">Confirmation</label>
          <div class="confirmation-container">
            <div class="confirmation-grid">
              <div class="confirm-section">
                <div class="confirm-row">
                  <label>Confirmed Mule</label>
                  <div class="radio-group">
                    <label><input type="radio" v-model="bulkClose.confirmedMule" value="Yes" name="bulkConfirmedMule" /> Yes</label>
                    <label><input type="radio" v-model="bulkClose.confirmedMule" value="No" name="bulkConfirmedMule" /> No</label>
                  </div>
                </div>
                <div class="confirm-row">
                  <label>Funds Saved</label>
                  <input
                    type="number"
                    v-model="bulkClose.fundsSaved"
                    :disabled="bulkClose.confirmedMule !== 'Yes'"
                    class="compact-input"
                    placeholder="Amount"
                  />
                </div>
              </div>
              <div class="confirm-section">
                <div class="confirm-row">
                  <label>Digital Channel Blocked</label>
                  <div class="radio-group">
                    <label><input type="radio" v-model="bulkClose.digitalBlocked" value="Yes" name="bulkDigitalBlocked" /> Yes</label>
                    <label><input type="radio" v-model="bulkClose.digitalBlocked" value="No" name="bulkDigitalBlocked" /> No</label>
                  </div>
                </div>
                <div class="confirm-row">
                  <label>Account Blocked</label>
                  <div class="radio-group">
                    <label><input type="radio" v-model="bulkClose.accountBlocked" value="Yes" name="bulkAccountBlocked" /> Yes</label>
                    <label><input type="radio" v-model="bulkClose.accountBlocked" value="No" name="bulkAccountBlocked" /> No</label>
                  </div>
                </div>
              </div>
            </div>
            <div class="action-buttons">
              <button @click="bulkCloseCases" class="btn-close-primary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M18 6L6 18M6 6l12 12"></path>
                </svg>
                Close Selected Cases
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Help Desk Section -->
    <div v-if="showHelpDesk" class="help-desk-section">
      <div class="help-desk-header">
        <h3>Case Types Reference</h3>
        <p class="help-description">Quick reference guide for all case types and their meanings</p>
      </div>
      <div class="case-types-grid">
        <div class="case-type-card" v-for="caseType in caseTypes" :key="caseType.code">
          <div class="case-type-header">
            <span class="case-code">{{ caseType.code }}</span>
            <span class="case-status" :class="caseType.category">{{ caseType.category }}</span>
          </div>
          <div class="case-type-content">
            <h4>{{ caseType.fullName }}</h4>
            <p>{{ caseType.description }}</p>
            <div class="case-type-details">
              <div class="detail-item">
                <span class="detail-label">Type:</span>
                <span class="detail-value">{{ caseType.type }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Stage:</span>
                <span class="detail-value">{{ caseType.stage }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="dashboard-table-card">
      <div class="table-responsive">
        <table class="case-table">
          <colgroup>
            <col style="width: 5%"> <col style="width: 10%"> <col style="width: 14%"> <col style="width: 16%"> <col style="width: 10%"> <col style="width: 10%"> <col style="width: 12%"> <col style="width: 12%"> <col style="width: 14%"> <col style="width: 10%"> <col style="width: 14%">
          </colgroup>
          <thead>
            <tr>
              <th v-if="isBulkActionMode" class="checkbox-header">
                <input 
                  type="checkbox" 
                  :checked="isAllSelected" 
                  @change="toggleSelectAll"
                  class="select-all-checkbox"
                />
              </th>
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
              <td :colspan="isBulkActionMode ? 11 : 10" style="padding: 12px;">
                <div class="skeleton-table">
                  <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
                  <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
                  <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
                  <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
                </div>
              </td>
            </tr>
            <tr v-else-if="paginatedCases.length > 0" v-for="caseItem in paginatedCases" :key="caseItem.case_id">
              <td v-if="isBulkActionMode" class="checkbox-cell">
                <input 
                  type="checkbox" 
                  :value="caseItem.case_id"
                  v-model="selectedCases"
                  :disabled="caseItem.status === 'Closed'"
                  class="case-checkbox"
                  :title="caseItem.status === 'Closed' ? 'Cannot select closed cases' : ''"
                />
              </td>
              <td>
                <router-link :to="getCaseLink(caseItem)" class="ack-link">
                  {{ caseItem.case_id }}
                </router-link>
              </td>
              <td>{{ caseItem.source_ack_no || '—' }}</td>
              <td>
                <span class="chip">{{ caseItem.case_type || '—' }}</span>
              </td>
              <td>
                <span :class="['badge', caseItem.is_operational ? 'operational' : 'non-operational']">
                  {{ caseItem.is_operational ? 'Yes' : 'No' }}
                </span>
              </td>
              <td>{{ caseItem.location || '—' }}</td>
              <td class="numeric">
                <span v-if="caseItem.disputed_amount !== null && !isNaN(Number(caseItem.disputed_amount))">
                  ₹{{ Number(caseItem.disputed_amount).toLocaleString('en-IN') }}
                </span>
                <span v-else>—</span>
              </td>
              <td>{{ caseItem.created_by || '—' }}</td>
              <td>
                <span v-if="caseItem.creation_date || caseItem.creation_time">
                  {{ formatDateTimeIST(caseItem.creation_date, caseItem.creation_time) }}
                </span>
                <span v-else>—</span>
              </td>
              <td>
                <span :class="['status-badge', caseItem.status ? caseItem.status.toLowerCase().replace(/ /g,'-') : '']">
                  {{ caseItem.status || '-' }}
                </span>
              </td>
              <td>{{ caseItem.assigned_to || '—' }}</td>
            </tr>
            <tr v-else>
              <td :colspan="isBulkActionMode ? 11 : 10" style="padding: 12px;">
                <div class="empty-state">
                  <div class="icon">🔍</div>
                  <div class="title">No cases found</div>
                  <div class="hint">Try adjusting filters or click "Clear All" to reset.</div>
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
            <span class="value">{{ caseItem.disputed_amount != null ? '₹' + Number(caseItem.disputed_amount).toLocaleString('en-IN') : '-' }}</span>
          </div>
          <div class="card-row footer">
            <span class="created">{{ formatDateTimeIST(caseItem.creation_date, caseItem.creation_time) }}</span>
            <span class="assigned">{{ caseItem.assigned_to || '—' }}</span>
          </div>
        </div>
      </div>

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
const userType = ref('');

// Global search and sorting
const globalSearch = ref('');
const sortColumn = ref('');
const sortDirection = ref('asc');

// --- Bulk Action State ---
const isBulkActionMode = ref(false);
const selectedCases = ref([]);
const showAssignment = ref(false);
const showClose = ref(false);
const departments = ref([]);
const closureReasons = ref([]);
const userRole = ref('');

// --- Help Desk State ---
const showHelpDesk = ref(false);
const caseTypes = ref([
  {
    code: 'VM',
    fullName: 'Victim Match',
    description: 'Cases where the victim account matches existing customer records.',
    type: 'Operational',
    stage: 'Stage 1',
    category: 'operational'
  },
  {
    code: 'BM',
    fullName: 'Beneficiary Match',
    description: 'Cases where the beneficiary account matches existing customer records.',
    type: 'Operational',
    stage: 'Stage 1',
    category: 'operational'
  },
  {
    code: 'ECBT',
    fullName: 'Potential Victim - Transactions already made to flagged beneficiaries',
    description: 'Cases where there are transactions between victim to beneficiary account.',
    type: 'Internal',
    stage: 'Stage 2',
    category: 'internal'
  },
  {
    code: 'ECBNT',
    fullName: 'Potential Victim - Beneficiary added  but yet to transfer money',
    description: 'Cases where the beneficiary is enrolled as payee but there are no transactions between victim to beneficiary account.',
    type: 'Internal',
    stage: 'Stage 2',
    category: 'internal'
  },
  {
    code: 'PSA',
    fullName: 'Potential Suspect Account',
    description: 'Cases flagged for potential suspect account who have same mobile number, email, PAN or Aadhar.',
    type: 'Screening',
    stage: 'Stage 2',
    category: 'screening'
  },
  {
    code: 'NAB',
    fullName: 'New Account Beneficiary',
    description: 'Cases involving newly created accounts that are flagged as beneficiaries in fraud cases, and are also matched agaisnt suspect entries.',
    type: 'Screening',
    stage: 'Stage 2',
    category: 'screening'
  },
  {
    code: 'PMA',
    fullName: 'Potential Mule Account',
    description: 'Cases flagged when new accounts are opened and details matched with either I4C or suspect entries.',
    type: 'Screening',
    stage: 'Stage 2',
    category: 'screening'
  },
  {
    code: 'MM',
    fullName: 'Mobile Number Matching',
    description: 'Cases created when customer mobile numbers match with reverification flags in the system, based on telecom data.',
    type: 'Matching',
    stage: 'Stage 2',
    category: 'matching'
  }
]);

// Bulk assignment data
const bulkAssignment = ref({
  reviews: [{ id: Date.now(), selectedDepartment: '', userId: '', text: '', userList: [] }]
});

// Bulk close data
const bulkClose = ref({
  closureLOV: '',
  closureRemarks: '',
  confirmedMule: 'No',
  fundsSaved: null,
  digitalBlocked: 'No',
  accountBlocked: 'No'
});

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

// --- Help Desk Functions ---
const toggleHelpDesk = () => {
  showHelpDesk.value = !showHelpDesk.value;
};

// --- Bulk Action Functions ---
const toggleBulkAction = () => {
  isBulkActionMode.value = !isBulkActionMode.value;
  if (!isBulkActionMode.value) {
    selectedCases.value = [];
    showAssignment.value = false;
    showClose.value = false;
  }
};

const selectAllCases = () => {
  selectedCases.value = paginatedCases.value
    .filter(caseItem => caseItem.status !== 'Closed')
    .map(caseItem => caseItem.case_id);
};

const clearSelection = () => {
  selectedCases.value = [];
};

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedCases.value = [];
  } else {
    selectedCases.value = paginatedCases.value
      .filter(caseItem => caseItem.status !== 'Closed')
      .map(caseItem => caseItem.case_id);
  }
};

const showAssignmentSection = () => {
  showAssignment.value = true;
  showClose.value = false;
};

const showCloseSection = () => {
  showClose.value = true;
  showAssignment.value = false;
};

// --- Bulk Assignment Functions ---
const addBulkReviewCommentRow = () => {
  bulkAssignment.value.reviews.push({
    id: Date.now(),
    selectedDepartment: '',
    userId: '',
    text: '',
    userList: []
  });
};

const removeBulkReviewCommentRow = (index) => {
  if (bulkAssignment.value.reviews.length > 1) {
    bulkAssignment.value.reviews.splice(index, 1);
  }
};

const handleBulkDepartmentChange = async (review) => {
  review.userId = '';
  review.userList = [];
  if (review.selectedDepartment) {
    try {
      const response = await axios.get(`/api/users?department_name=${review.selectedDepartment}`);
      if (response.data && Array.isArray(response.data)) {
        review.userList = response.data;
      }
    } catch (err) {
      console.error(`Failed to fetch users for department ${review.selectedDepartment}:`, err);
    }
  }
};

const bulkAssignCases = async () => {
  if (selectedCases.value.length === 0) {
    window.showNotification('warning', 'No Cases Selected', 'Please select at least one case to assign.');
    return;
  }

  const validAssignments = bulkAssignment.value.reviews.filter(review => review.userId && review.userId.trim());
  if (validAssignments.length === 0) {
    window.showNotification('warning', 'No Users Selected', 'Please select at least one user to assign.');
    return;
  }
  


  const token = localStorage.getItem('jwt');
  if (!token) {
    window.showNotification('error', 'Authentication Error', 'Authentication token not found.');
    return;
  }

  try {
    // Prepare assignments data for bulk operation
    const assignments = [];
    
    for (const caseId of selectedCases.value) {
      for (const review of validAssignments) {
        assignments.push({
          case_id: caseId,
          assigned_to: review.userId,
          comment: review.text || ''
        });
      }
    }
    
    // Use bulk assign endpoint
    const response = await axios.post('/api/case/bulk-assign', 
      { assignments: assignments }, 
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    if (response.data.successful_assigns > 0) {
      let message = `Successfully assigned ${response.data.successful_assigns} case(s) to ${validAssignments.length} user(s)!`;
      if (response.data.failed_assigns > 0) {
        message += `\n\nFailed to assign ${response.data.failed_assigns} case(s):`;
        response.data.failed_assignments.forEach(failed => {
          message += `\n- Case ${failed.case_id}: ${failed.error}`;
        });
      }
      window.showNotification('success', 'Assignment Complete', message);
    } else {
      let message = 'No cases were assigned. Failed cases:';
      response.data.failed_assignments.forEach(failed => {
        message += `\n- Case ${failed.case_id}: ${failed.error}`;
      });
      window.showNotification('error', 'Assignment Failed', message);
    }
    
    // Reset and refresh
    selectedCases.value = [];
    showAssignment.value = false;
    isBulkActionMode.value = false;
    await fetchCases();
  } catch (err) {
    window.showNotification('error', 'Assignment Failed', 'Failed to assign cases. Please try again.');
    console.error('Bulk assignment error:', err);
  }
};

// --- Bulk Close Functions ---
const bulkCloseCases = async () => {
  if (selectedCases.value.length === 0) {
    window.showNotification('warning', 'No Cases Selected', 'Please select at least one case to close.');
    return;
  }

  if (!bulkClose.value.closureLOV) {
    window.showNotification('warning', 'Missing Information', 'Please select a closure reason.');
    return;
  }

  const token = localStorage.getItem('jwt');
  if (!token) {
    window.showNotification('error', 'Authentication Error', 'Authentication token not found.');
    return;
  }

  try {
    // Use bulk close endpoint
    const response = await axios.post('/api/case/bulk-close', {
      case_ids: selectedCases.value,
      closure_data: bulkClose.value
    }, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.data.successful_closes > 0) {
      let message = `Successfully closed ${response.data.successful_closes} case(s)!`;
      if (response.data.failed_closes > 0) {
        message += `\n\nFailed to close ${response.data.failed_closes} case(s):`;
        response.data.failed_cases.forEach(failed => {
          message += `\n- Case ${failed.case_id}: ${failed.error}`;
        });
      }
      window.showNotification('success', 'Cases Closed', message);
    } else {
      let message = 'No cases were closed. Failed cases:';
      response.data.failed_cases.forEach(failed => {
        message += `\n- Case ${failed.case_id}: ${failed.error}`;
      });
      window.showNotification('error', 'Close Failed', message);
    }
    
    // Reset and refresh
    selectedCases.value = [];
    showClose.value = false;
    isBulkActionMode.value = false;
    await fetchCases();
  } catch (err) {
    window.showNotification('error', 'Close Failed', 'Failed to close cases. Please try again.');
    console.error('Bulk close error:', err);
  }
};

// --- Computed Properties for Bulk Actions ---
const isAllSelected = computed(() => {
  const selectableCases = paginatedCases.value.filter(caseItem => caseItem.status !== 'Closed');
  return selectableCases.length > 0 && selectedCases.value.length === selectableCases.length;
});

const assignableCasesCount = computed(() => {
  return selectedCases.value.filter(caseId => {
    const caseItem = cases.value.find(c => c.case_id === caseId);
    return caseItem && caseItem.case_type !== 'VM';
  }).length;
});

// --- Load User Information ---
const loadUserInfo = () => {
  const storedUserType = localStorage.getItem('user_type');
  
  if (storedUserType) {
    userType.value = storedUserType;
  }
};

// --- Fetch User Role ---
const fetchUserRole = async () => {
  try {
    // First try localStorage (faster, no API call needed)
    const storedRole = localStorage.getItem('user_type');
    if (storedRole) {
      userRole.value = storedRole;
      return;
    }
    
    const token = localStorage.getItem('jwt');
    if (!token) return;
    
    // Fallback to lightweight user profile API (much faster than new-case-list)
    const response = await axios.get('/api/user/profile', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.data && response.data.logged_in_user_type) {
      userRole.value = response.data.logged_in_user_type;
      // Store in localStorage for consistency
      localStorage.setItem('user_type', response.data.logged_in_user_type);
    }
    
    // Also fetch user name if available
    if (response.data && response.data.logged_in_user_name) {
      localStorage.setItem('username', response.data.logged_in_user_name);
    }
  } catch (err) { 
    console.error("Failed to fetch user role:", err); 
  }
};

// --- Fetch Dropdown Data ---
const fetchDepartments = async () => {
  try {
    const response = await axios.get('/api/departments');
    if (response.data) departments.value = response.data;
  } catch (err) { console.error("Failed to fetch departments:", err); }
};

const fetchClosureReasons = async () => {
  try {
    const response = await axios.get('/api/final-closure');
    if (response.data) closureReasons.value = response.data;
  } catch (err) { console.error("Failed to fetch closure reasons:", err); }
};

// --- Helper function to check if search term is an account number ---
const isAccountNumber = (searchTerm) => {
  return /^\d+$/.test(searchTerm.trim());
};

// --- Helper function to format date and time in IST ---
const formatDateTimeIST = (creationDate, creationTime) => {
  console.log('formatDateTimeIST called with:', { creationDate, creationTime });
  
  if (!creationDate && !creationTime) return '—';
  
  try {
    let dateTime;
    
    if (creationDate && creationTime) {
      // Always use the separate date and time fields, not the combined datetime
      // Extract just the date part - handle both formats:
      // Format 1: "2025-09-08 00:00:00+00:00" (space separator)
      // Format 2: "2025-09-08T00:00:00Z" (T separator with Z)
      let dateOnly;
      if (creationDate.includes(' ')) {
        // Format 1: Split by space
        dateOnly = creationDate.split(' ')[0];
      } else if (creationDate.includes('T')) {
        // Format 2: Split by T
        dateOnly = creationDate.split('T')[0];
      } else {
        // Fallback: use as is
        dateOnly = creationDate;
      }
      console.log('Date only:', dateOnly);
      
      // Check if this is an old case with UTC time (before IST fix)
      // Old cases have times like "05:40:22" (UTC) - convert to IST
      // New cases have times like "11:15:40" (IST) - use directly
      const timeStr = creationTime.toString();
      const hour = parseInt(timeStr.split(':')[0]);
      console.log('Time string:', timeStr, 'Hour:', hour);
      
      // If hour is less than 6, it's likely UTC time (old cases)
      // Convert UTC to IST by adding 5.5 hours
      if (hour < 6) {
        const dateStr = `${dateOnly}T${creationTime}Z`; // Treat as UTC
        console.log('UTC format:', dateStr);
        dateTime = new Date(dateStr);
        console.log('UTC Date object:', dateTime);
        // Convert UTC to IST
        dateTime = new Date(dateTime.getTime() + (5.5 * 60 * 60 * 1000));
        console.log('IST Date object:', dateTime);
      } else {
        // New cases with IST time - use directly
        const dateStr = `${dateOnly}T${creationTime}`;
        console.log('IST format:', dateStr);
        dateTime = new Date(dateStr);
        console.log('IST Date object:', dateTime);
      }
    } else if (creationDate) {
      // Only date available - extract date part
      let dateOnly;
      if (creationDate.includes(' ')) {
        dateOnly = creationDate.split(' ')[0];
      } else if (creationDate.includes('T')) {
        dateOnly = creationDate.split('T')[0];
      } else {
        dateOnly = creationDate;
      }
      dateTime = new Date(dateOnly);
    } else {
      // Only time available (use current date)
      const today = new Date().toISOString().split('T')[0];
      dateTime = new Date(`${today}T${creationTime}`);
    }
    
    console.log('Final dateTime:', dateTime, 'isValid:', !isNaN(dateTime.getTime()));
    
    // Check if date is valid
    if (isNaN(dateTime.getTime())) {
      console.error('Invalid date created:', dateTime);
      return '—';
    }
    
    // Format date in Indian format
    const dateStr = dateTime.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
    
    // Format time in 24-hour format
    const timeStr = dateTime.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
    
    console.log('Formatted result:', `${dateStr} ${timeStr}`);
    return `${dateStr} ${timeStr}`;
  } catch (error) {
    console.error('Error formatting date/time:', error, { creationDate, creationTime });
    return '—';
  }
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
    'PSA': 'PSAAction', 'ECBT': 'ECBTAction', 'ECBNT': 'ECBNTAction', 'NAB': 'NABAction',
    'MM': 'MobileMatchingAction'  // Add MM case routing
  };
  const routeName = routeMap[caseItem.case_type] || 'CaseRiskReview';
  return {
    name: routeName,
    params: { case_id: caseItem.case_id },
    query: { status: caseItem.status }
  };
}

// --- Lifecycle Hook ---
onMounted(async () => {
  loadUserInfo(); // Load user info from localStorage first
  await fetchCases();
  await Promise.all([
    fetchUserRole(),
    fetchDepartments(),
    fetchClosureReasons()
  ]);
});
</script>

<style scoped>
/* Header Content Styles */
.header-content { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-content h2 { margin: 0; color: #1e293b; font-size: 1.875rem; font-weight: 600; }
.user-avatar img { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #e2e8f0; }

.table-responsive { width: 100%; overflow-x: auto; }
.case-table { width: 100%; border-collapse: collapse; font-size: 15px; min-width: 1000px; }
.case-table thead th { position: sticky; top: 0; background: #f7f7f7; z-index: 2; padding: 16px 12px; font-weight: 700; font-size: 16px; color: #1e293b; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #e2e8f0; }
.case-table th, .case-table td { padding: 12px 10px; text-align: left; border-bottom: 1px solid #eef2f7; vertical-align: middle; }
.case-table tbody tr:nth-child(even) { background: #fbfdff; }
.case-table tbody tr:hover { background: #f3f7ff; transition: background 0.15s ease; }
.case-table td.numeric { text-align: right; font-variant-numeric: tabular-nums; }
.sortable-header { cursor: pointer; user-select: none; position: relative; transition: background-color 0.2s; }
.sortable-header:hover { background-color: #e8e8e8; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.sort-icon { margin-left: 6px; font-weight: bold; color: #007bff; font-size: 14px; }

.ack-link { color: #0d6efd; font-weight: 600; text-decoration: none; }
.ack-link:hover { text-decoration: underline; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.badge.operational { background: #e6f4ea; color: #18794e; }
.badge.non-operational { background: #fee2e2; color: #991b1b; }

.chip { display: inline-block; padding: 2px 8px; border-radius: 8px; background: #eef2ff; color: #4338ca; font-weight: 600; font-size: 12px; }

.status-badge { display: inline-block; padding: 4px 10px; border-radius: 999px; font-weight: 700; font-size: 12px; }
.status-badge.new { background: #e0f2fe; color: #075985; }
.status-badge.assigned { background: #fef3c7; color: #92400e; }
.status-badge.closed { background: #dcfce7; color: #166534; }
.status-badge.open { background: #e9d5ff; color: #6b21a8; }
.status-badge.reopened { background: #fef2f2; color: #dc2626; }
.status-badge.pending { background: #fef3c7; color: #92400e; }
.status-badge.approved { background: #dcfce7; color: #166534; }
.status-badge.rejected { background: #fef2f2; color: #dc2626; }

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
  .dashboard-table-card { padding: 0 0 12px 0; }
  .table-responsive { display: none; }
  .case-cards { display: grid; grid-template-columns: 1fr; gap: 10px; }
}

/* Help Desk Styles */
.help-desk-btn {
  padding: 10px 20px;
  background: #6f42c1;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 8px;
}

.help-desk-btn:hover {
  background: #5a32a3;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.help-desk-btn.active {
  background: #dc3545;
}

.help-desk-section {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #dee2e6;
  border-radius: 12px;
  padding: 24px;
  margin-top: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.help-desk-header {
  margin-bottom: 24px;
  text-align: center;
}

.help-desk-header h3 {
  margin: 0 0 8px 0;
  color: #2c3e50;
  font-size: 24px;
  font-weight: 600;
}

.help-description {
  margin: 0;
  color: #6c757d;
  font-size: 16px;
  font-style: italic;
}

.case-types-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.case-type-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.case-type-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  border-color: #007bff;
}

.case-type-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f1f3f4;
}

.case-code {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.case-status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.case-status.operational {
  background: #e3f2fd;
  color: #1976d2;
}

.case-status.internal {
  background: #f3e5f5;
  color: #7b1fa2;
}

.case-status.screening {
  background: #fff3e0;
  color: #f57c00;
}

.case-status.matching {
  background: #e8f5e8;
  color: #388e3c;
}

.case-type-content h4 {
  margin: 0 0 8px 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.3;
}

.case-type-content p {
  margin: 0 0 16px 0;
  color: #6c757d;
  font-size: 14px;
  line-height: 1.5;
}

.case-type-details {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 12px;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
}

/* Responsive Design for Help Desk */
@media (max-width: 768px) {
  .case-types-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .case-type-card {
    padding: 16px;
  }
  
  .case-type-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .case-type-details {
    flex-direction: column;
    gap: 12px;
  }
  
  .help-desk-section {
    padding: 16px;
    margin-top: 16px;
  }
}

/* Bulk Action Styles */
.bulk-action-btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.bulk-action-btn:hover {
  background: #0056b3;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.bulk-action-btn.active {
  background: #dc3545;
}

.bulk-action-controls {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #dee2e6;
  border-radius: 12px;
  padding: 20px;
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.bulk-action-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.selection-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selected-count {
  font-weight: 600;
  color: #495057;
  font-size: 16px;
}

.assignable-info {
  color: #28a745;
  font-size: 13px;
  font-weight: 500;
  background: rgba(40, 167, 69, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
}

.closable-info {
  color: #007bff;
  font-size: 13px;
  font-weight: 500;
  background: rgba(0, 123, 255, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
}

.selection-actions {
  display: flex;
  gap: 8px;
}

.select-all-btn, .clear-selection-btn {
  padding: 6px 12px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s;
}

.select-all-btn:hover, .clear-selection-btn:hover {
  background: #5a6268;
  transform: translateY(-1px);
}

.bulk-action-buttons {
  display: flex;
  gap: 12px;
}

.bulk-assign-btn, .bulk-close-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.bulk-assign-btn {
  background: #28a745;
  color: white;
}

.bulk-assign-btn:hover {
  background: #218838;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.bulk-assign-btn.active {
  background: #1e7e34;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
}

.bulk-close-btn {
  background: #dc3545;
  color: white;
}

.bulk-close-btn:hover {
  background: #c82333;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.bulk-close-btn.active {
  background: #bd2130;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
}



/* Bulk Section Styles */
.bulk-section {
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 12px;
  padding: 24px;
  margin-top: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  max-height: 70vh;
  overflow-y: auto;
}

.bulk-section-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e9ecef;
}

.bulk-section-header h3 {
  margin: 0 0 8px 0;
  color: #2c3e50;
  font-size: 20px;
  font-weight: 600;
}

.section-description {
  margin: 0;
  color: #6c757d;
  font-size: 14px;
  font-style: italic;
}

.section-label {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 12px;
  display: block;
}

/* Checkbox Styles */
.checkbox-header, .checkbox-cell {
  width: 40px;
  text-align: center;
}

.select-all-checkbox, .case-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.case-checkbox:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Form Styles (reused from BeneficiaryAction) */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-group label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  margin-bottom: 6px;
}

.input-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 12px;
  align-items: start;
}

.compact-select, .compact-input, .compact-textarea {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
  height: 36px;
  box-sizing: border-box;
  transition: all 0.2s;
}

.compact-select:focus, .compact-input:focus, .compact-textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.compact-textarea {
  min-height: 80px;
  max-height: 120px;
  resize: vertical;
  font-family: inherit;
  line-height: 1.4;
}

/* New Form Elements */
.assignments-container, .closure-details-container, .confirmation-container {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  margin-top: 12px;
}

.select-group, .comment-group, .closure-reason-group, .closure-remarks-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.select-group label, .comment-group label, .closure-reason-group label, .closure-remarks-group label {
  font-size: 13px;
  font-weight: 600;
  color: #495057;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e9ecef;
}

.btn-assign-primary, .btn-close-primary {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.btn-assign-primary {
  background: #28a745;
  color: white;
}

.btn-assign-primary:hover {
  background: #218838;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.btn-close-primary {
  background: #dc3545;
  color: white;
}

.btn-close-primary:hover {
  background: #c82333;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.review-comment-row {
  position: relative;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  transition: all 0.2s;
}

.review-comment-row:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  border-color: #007bff;
}

.comment-user-selection-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.btn-add-row {
  width: 100%;
  padding: 8px;
  background-color: #e7f3ff;
  color: #0d6efd;
  border: 1px dashed #0d6efd;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  margin-top: 4px;
}

.btn-add-row:hover {
  background-color: #d1e7ff;
}

.btn-remove-row {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid #dc3545;
  background-color: #fff;
  color: #dc3545;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  z-index: 10;
}

.btn-assign, .btn-submit {
  width: 100%;
  padding: 8px;
  background-color: #e7f3ff;
  color: #0d6efd;
  border: 1px solid #0d6efd;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  margin-top: 8px;
}

.btn-assign:hover, .btn-submit:hover {
  background-color: #d1e7ff;
}

/* Confirmation Styles */
.confirmation-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 16px;
}

.confirm-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.confirm-row {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 12px;
  align-items: center;
}

.confirm-row label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
}

.radio-group {
  display: flex;
  gap: 20px;
  align-items: center;
  height: 100%;
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  font-size: 13px;
  cursor: pointer;
}

.radio-group input[type="radio"] {
  accent-color: #0d6efd;
}

/* Responsive Design */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .user-info {
    align-self: flex-end;
  }
  
  .bulk-action-controls {
    flex-direction: column;
    gap: 16px;
  }
  
  .bulk-action-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .selection-info {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .bulk-action-buttons {
    width: 100%;
    justify-content: center;
  }
  
  .confirmation-grid {
    grid-template-columns: 1fr;
  }
  
  .confirm-row {
    grid-template-columns: 1fr;
  }
  
  .input-row {
    grid-template-columns: 1fr;
  }
  
  .comment-user-selection-row {
    grid-template-columns: 1fr;
  }
  
  .bulk-section {
    padding: 16px;
    margin-top: 16px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn-assign-primary, .btn-close-primary {
    width: 100%;
    justify-content: center;
  }
}
</style>