<template>
  <div class="dashboard-bg">
    <div class="dashboard-header">
      <div class="header-content">
        <h2>{{ pageTitle }}</h2>
        <div class="user-info">
          <span class="user-name">{{ userName }}</span>
          <span v-if="userType" class="user-type">{{ userType }}</span>
        </div>
      </div>
    </div>

    <div class="activity-layout">
      <div class="activity-list">
        <div class="section-header">
          <h3>Cases You Touched</h3>
          <div class="filters-row">
            <input v-model="globalSearch" class="filter-input enhanced-search-input" placeholder="Search cases..." @input="handleSearch" />
          </div>
        </div>

        <div class="table-responsive">
          <table class="case-table">
            <thead>
              <tr>
                <th @click="sortBy('case_id')">Case ID <span v-if="sortColumn==='case_id'">{{ sortDirection==='asc' ? '↑' : '↓' }}</span></th>
                <th @click="sortBy('source_ack_no')">ACK ID <span v-if="sortColumn==='source_ack_no'">{{ sortDirection==='asc' ? '↑' : '↓' }}</span></th>
                <th @click="sortBy('case_type')">Type <span v-if="sortColumn==='case_type'">{{ sortDirection==='asc' ? '↑' : '↓' }}</span></th>
                <th @click="sortBy('status')">Status <span v-if="sortColumn==='status'">{{ sortDirection==='asc' ? '↑' : '↓' }}</span></th>
                <th @click="sortBy('last_touched_at')">Last Touched <span v-if="sortColumn==='last_touched_at'">{{ sortDirection==='asc' ? '↑' : '↓' }}</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loadingCases">
                <td colspan="5" style="padding: 12px;">
                  <div class="skeleton-table">
                    <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
                    <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
                    <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
                  </div>
                </td>
              </tr>
              <tr v-else-if="filteredCases.length === 0">
                <td colspan="5" style="padding: 12px;">
                  <div class="empty-state">
                    <div class="icon">🗂️</div>
                    <div class="title">No cases yet</div>
                    <div class="hint">Once you interact with cases, they’ll appear here.</div>
                  </div>
                </td>
              </tr>
              <tr v-for="c in paginatedCases" :key="c.case_id" :class="{ selected: selectedCaseId === c.case_id }" @click="selectCase(c.case_id)">
                <td>#{{ c.case_id }}</td>
                <td>{{ c.source_ack_no || '—' }}</td>
                <td><span class="chip">{{ c.case_type || '—' }}</span></td>
                <td>
                  <span :class="['status-badge', (c.status || '').toLowerCase().replace(/ /g,'-') ]">{{ c.status || '-' }}</span>
                  <!-- Reopen button for super_user on closed cases -->
                  <button 
                    v-if="isSuperUser && c.status === 'Closed'"
                    @click.stop="reopenCase(c.case_id)"
                    class="reopen-btn"
                    title="Reopen this closed case"
                  >
                    🔓 Reopen
                  </button>

                </td>
                <td>{{ formatDateTime(c.last_touched_at) || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pagination-row" v-if="!loadingCases && filteredCases.length > 0">
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

      <div class="activity-logs">
        <div class="section-header">
          <h3 v-if="selectedCaseId">Case #{{ selectedCaseId }} Logs</h3>
          <h3 v-else-if="userType === 'super_user'">All Case Activity</h3>
          <h3 v-else>Logs</h3>
          
          <!-- Toggle for super_user to show all logs vs case-specific logs -->
          <div v-if="userType === 'super_user'" class="log-toggle">
            <button 
              @click="toggleLogView" 
              class="toggle-btn"
              :class="{ active: showAllLogs }"
            >
              {{ showAllLogs ? 'Show Case Logs' : 'Show All Activity' }}
            </button>
          </div>
        </div>
        
        <div class="logs-box">
          <div v-if="loadingLogs" class="logs-loading">
            <div class="skeleton-table">
              <div class="row"><div class="cell skeleton skeleton-line"></div></div>
              <div class="row"><div class="cell skeleton skeleton-line"></div></div>
              <div class="row"><div class="cell skeleton skeleton-line"></div></div>
            </div>
          </div>
          <div v-else-if="logs.length === 0" class="logs-empty">
            <div class="empty-state">
              <div class="icon">📝</div>
              <div class="title">No logs yet</div>
              <div class="hint">
                <span v-if="userType === 'super_user' && showAllLogs">No case activity found in the system.</span>
                <span v-else>Select a case to view its recent activity.</span>
              </div>
            </div>
          </div>
          <ul v-else class="case-log-list">
            <li v-for="log in logs" :key="log.id" class="case-log-item">
              <span class="log-time">{{ formatDateTime(log.created_at) }}</span>
              <span v-if="userType === 'super_user' && showAllLogs" class="log-case-info">
                Case #{{ log.case_id }} ({{ log.source_ack_no || 'N/A' }})
              </span>
              <span class="log-user">{{ log.user_name }}</span>
              <span class="log-action">[{{ log.action }}]</span>
              <span class="log-details">{{ log.details }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const userName = ref(localStorage.getItem('username') || '');
const userType = ref(localStorage.getItem('user_type') || '');

const pageTitle = computed(() => userType.value === 'others' ? 'My Case Activity' : 'Risk Officer Case Activity');

// Computed property for localStorage access in template
const localStorageUserType = computed(() => {
  if (typeof window !== 'undefined' && window.localStorage) {
    return localStorage.getItem('user_type');
  }
  return null;
});

// Computed property to check if user is super_user
const isSuperUser = computed(() => {
  return userType.value === 'super_user' || localStorageUserType.value === 'super_user';
});

const loadingCases = ref(true);
const loadingLogs = ref(false);
const cases = ref([]);
const logs = ref([]);
const selectedCaseId = ref(null);
const showAllLogs = ref(false); // For super_user to toggle between all logs and case-specific logs
const riskOfficers = ref([]); // For super_user reopen assignment dropdown



const globalSearch = ref('');
const sortColumn = ref('last_touched_at');
const sortDirection = ref('desc');
const page = ref(1);
const pageSize = 15;

const fetchActivityCases = async () => {
  loadingCases.value = true;
  try {
    const token = localStorage.getItem('jwt');
    const resp = await axios.get('/api/user/activity-cases', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (resp.data && Array.isArray(resp.data.cases)) {
      cases.value = resp.data.cases;
      if (resp.data.user_type) {
        userType.value = resp.data.user_type;
        localStorage.setItem('user_type', resp.data.user_type);
      }
    } else {
      cases.value = [];
    }
  } catch (e) {
    cases.value = [];
  } finally {
    loadingCases.value = false;
  }
};


const fetchLogs = async (caseId) => {
  loadingLogs.value = true;
  try {
    const token = localStorage.getItem('jwt');
    const resp = await axios.get(`/api/case/${caseId}/logs`, { headers: { 'Authorization': `Bearer ${token}` } });
    logs.value = resp.data?.logs || [];
  } catch (e) {
    logs.value = [];
  } finally {
    loadingLogs.value = false;
  }
};

const selectCase = (caseId) => {
  selectedCaseId.value = caseId;
  fetchLogs(caseId);
};

const reopenCase = async (caseId) => {
  // Show reopen dialog with risk officer assignment option
  const result = await showReopenAssignmentDialog(caseId);
  
  if (result.confirmed) {
    try {
      const token = localStorage.getItem('jwt');
      
      const requestData = {
        reopen_comment: result.comment
      };
      if (result.assignedRiskOfficer) {
        requestData.assigned_risk_officer = result.assignedRiskOfficer;
      }
      
      const response = await axios.post(`/api/case/${caseId}/reopen`, requestData, { 
        headers: { 'Authorization': `Bearer ${token}` } 
      });
      
      // Show success notification
      const assignmentMessage = response.data.assigned_to 
        ? ` and assigned to ${response.data.assigned_to}` 
        : '';
      
      if (window.showNotification) {
        window.showNotification('success', 'Case Reopened!', `Case #${caseId} has been successfully reopened${assignmentMessage}. Assignment functionality is enabled.`, 5000);
      } else {
        alert(`Case #${caseId} has been successfully reopened${assignmentMessage}!`);
      }
      
      fetchActivityCases(); // Refresh the list to show updated status
      fetchLogs(caseId); // Refresh logs for the reopened case
      
    } catch (e) {
      // Show error notification
      if (window.showNotification) {
        window.showNotification('error', 'Reopen Failed', `Failed to reopen case: ${e.response?.data?.message || e.message}`, 7000);
      } else {
        alert(`Failed to reopen case: ${e.response?.data?.message || e.message}`);
      }
    }
  }
};

// Function to fetch risk officers for assignment dropdown
const fetchRiskOfficers = async () => {
  if (!isSuperUser.value) return;
  
  try {
    const token = localStorage.getItem('jwt');
    const response = await axios.get('/api/risk-officers', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.data.success) {
      riskOfficers.value = response.data.risk_officers;
    }
  } catch (e) {
    console.error('Failed to fetch risk officers:', e);
  }
};

// Helper function to show reopen dialog with assignment option
const showReopenAssignmentDialog = (caseId) => {
  return new Promise((resolve) => {
    const dialog = document.createElement('div');
    dialog.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.6);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      backdrop-filter: blur(4px);
    `;
    
    const modal = document.createElement('div');
    modal.style.cssText = `
      background: white;
      border-radius: 16px;
      padding: 32px;
      max-width: 500px;
      width: 90%;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
      transform: scale(0.95);
      transition: transform 0.2s ease;
    `;
    
    // Create dropdown options
    const riskOfficerOptions = riskOfficers.value.map(officer => 
      `<option value="${officer.username}">${officer.username} (${officer.department})</option>`
    ).join('');
    
    modal.innerHTML = `
      <div style="text-align: center; margin-bottom: 24px;">
        <div style="
          width: 64px;
          height: 64px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 16px auto;
          font-size: 24px;
        ">🔓</div>
        <h3 style="
          font-size: 20px;
          font-weight: 600;
          color: #1f2937;
          margin: 0 0 8px 0;
        ">Reopen Case #${caseId}</h3>
      </div>
      
      <p style="
        font-size: 16px;
        color: #1f2937;
        line-height: 1.6;
        margin: 0 0 20px 0;
        text-align: center;
        font-weight: 500;
      ">Are you sure you want to reopen <strong>Case #${caseId}</strong>?</p>
      
      <div style="
        background: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 24px;
      ">
        <p style="
          font-size: 14px;
          color: #0c4a6e;
          margin: 0 0 12px 0;
          font-weight: 500;
        ">📋 Assignment Options:</p>
        <label style="
          display: block;
          font-size: 14px;
          color: #374151;
          margin-bottom: 8px;
          font-weight: 500;
        ">Assign to Risk Officer (Optional):</label>
        <select id="riskOfficerSelect" style="
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          font-size: 14px;
          background: white;
          margin-bottom: 12px;
        ">
          <option value="">-- Leave Unassigned --</option>
          ${riskOfficerOptions}
        </select>
        <label style="
          display: block;
          font-size: 14px;
          color: #374151;
          margin-bottom: 8px;
          font-weight: 500;
        ">Reopen Comment (Required):</label>
        <textarea id="reopenComment" style="
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          font-size: 14px;
          background: white;
          min-height: 80px;
          resize: vertical;
          font-family: inherit;
          box-sizing: border-box;
        " placeholder="Please provide a reason for reopening this case..." required></textarea>
        <p style="
          font-size: 12px;
          color: #6b7280;
          margin: 8px 0 0 0;
          font-style: italic;
        ">Case will be reopened with "Open" status and assignment functionality enabled. Your comment will be recorded in the case logs.</p>
      </div>
      
      <div style="
        display: flex;
        gap: 12px;
        justify-content: center;
      ">
        <button id="cancelBtn" style="
          background: #f3f4f6;
          color: #374151;
          padding: 12px 24px;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: background-color 0.2s;
        ">Cancel</button>
        <button id="confirmBtn" style="
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
          padding: 12px 24px;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.1s;
        ">🔓 Reopen Case</button>
      </div>
    `;
    
    dialog.appendChild(modal);
    document.body.appendChild(dialog);
    
    // Animate in
    requestAnimationFrame(() => {
      modal.style.transform = 'scale(1)';
    });
    
    const cleanup = () => {
      modal.style.transform = 'scale(0.95)';
      setTimeout(() => {
        if (dialog.parentNode) {
          document.body.removeChild(dialog);
        }
      }, 150);
    };
    
    const confirmBtn = modal.querySelector('#confirmBtn');
    const cancelBtn = modal.querySelector('#cancelBtn');
    const riskOfficerSelect = modal.querySelector('#riskOfficerSelect');
    const reopenComment = modal.querySelector('#reopenComment');
    
    confirmBtn.addEventListener('click', () => {
      const assignedRiskOfficer = riskOfficerSelect.value || null;
      const comment = reopenComment.value.trim();
      
      // Validate that comment is provided
      if (!comment) {
        alert('Please provide a reason for reopening this case.');
        reopenComment.focus();
        return;
      }
      
      cleanup();
      resolve({ confirmed: true, assignedRiskOfficer, comment });
    });
    
    cancelBtn.addEventListener('click', () => {
      cleanup();
      resolve({ confirmed: false, assignedRiskOfficer: null, comment: null });
    });
    
    // Close on backdrop click
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) {
        cleanup();
        resolve({ confirmed: false, assignedRiskOfficer: null, comment: null });
      }
    });
  });
};

// Helper function to show beautiful confirmation dialog (kept for backward compatibility)
const showReopenConfirmDialog = (caseId) => {
  return new Promise((resolve) => {
    const dialog = document.createElement('div');
    dialog.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(8px);
      z-index: 10000;
      display: flex;
      align-items: center;
      justify-content: center;
      animation: fadeIn 0.3s ease-out;
    `;
    
    dialog.innerHTML = `
      <div style="
        background: white;
        border-radius: 16px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        max-width: 500px;
        width: 90%;
        overflow: hidden;
        animation: slideUp 0.4s ease-out;
        border: 1px solid #e5e7eb;
      ">
        <div style="
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 24px 28px 20px;
          text-align: center;
        ">
          <div style="font-size: 48px; margin-bottom: 12px;">🔓</div>
          <h3 style="margin: 0; font-size: 24px; font-weight: 700;">Reopen Case</h3>
        </div>
        
        <div style="padding: 28px; background: #fafbfc;">
          <p style="
            font-size: 18px;
            color: #1f2937;
            line-height: 1.6;
            margin: 0 0 20px 0;
            text-align: center;
            font-weight: 500;
          ">Are you sure you want to reopen <strong>Case #${caseId}</strong>?</p>
          
          <div style="
            background: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 12px;
            padding: 20px;
          ">
            <div style="font-size: 24px; margin-bottom: 12px; text-align: center;">⚠️</div>
            <div style="color: #92400e; font-size: 14px; line-height: 1.6;">
              <strong style="color: #78350f;">Important:</strong> This action will:
              <ul style="margin: 12px 0 0 0; padding-left: 20px;">
                <li style="margin: 8px 0;">Change the case status from <span style="background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 6px; font-weight: 600; font-size: 12px;">Closed</span> to <span style="background: #fef2f2; color: #dc2626; padding: 2px 8px; border-radius: 6px; font-weight: 600; font-size: 12px;">Reopened</span></li>
                <li style="margin: 8px 0;">Disable assignment functionality for this case</li>
                <li style="margin: 8px 0;">Allow other operations to continue normally</li>
              </ul>
            </div>
          </div>
        </div>
        
        <div style="
          padding: 20px 28px 24px;
          display: flex;
          gap: 16px;
          justify-content: center;
          background: white;
          border-top: 1px solid #e5e7eb;
        ">
          <button id="cancelBtn" style="
            padding: 12px 24px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            border: 2px solid #d1d5db;
            background: #f3f4f6;
            color: #374151;
            transition: all 0.3s ease;
            min-width: 120px;
          ">Cancel</button>
          
          <button id="confirmBtn" style="
            padding: 12px 24px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            box-shadow: 0 4px 14px rgba(239, 68, 68, 0.4);
            transition: all 0.3s ease;
            min-width: 120px;
          ">Yes, Reopen Case</button>
        </div>
      </div>
    `;
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes slideUp {
        from { opacity: 0; transform: scale(0.9) translateY(20px); }
        to { opacity: 1; transform: scale(1) translateY(0); }
      }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(dialog);
    
    // Add event listeners
    const cancelBtn = dialog.querySelector('#cancelBtn');
    const confirmBtn = dialog.querySelector('#confirmBtn');
    
    const cleanup = () => {
      document.body.removeChild(dialog);
      document.head.removeChild(style);
    };
    
    cancelBtn.addEventListener('click', () => {
      cleanup();
      resolve(false);
    });
    
    confirmBtn.addEventListener('click', () => {
      cleanup();
      resolve(true);
    });
    
    // Close on backdrop click
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) {
        cleanup();
        resolve(false);
      }
    });
  });
};

const filteredCases = computed(() => {
  let list = [...cases.value];
  if (globalSearch.value.trim()) {
    const q = globalSearch.value.toLowerCase();
    list = list.filter(c => Object.values(c).some(v => v && String(v).toLowerCase().includes(q)));
  }
  if (sortColumn.value) {
    list.sort((a,b) => {
      let av = a[sortColumn.value];
      let bv = b[sortColumn.value];
      if (sortColumn.value === 'last_touched_at') {
        av = av ? new Date(av).getTime() : 0;
        bv = bv ? new Date(bv).getTime() : 0;
      } else if (sortColumn.value === 'case_id') {
        av = Number(av) || 0; bv = Number(bv) || 0;
      } else {
        av = (av ?? '').toString().toLowerCase();
        bv = (bv ?? '').toString().toLowerCase();
      }
      return sortDirection.value === 'asc' ? (av>bv?1:av<bv?-1:0) : (av<bv?1:av>bv?-1:0);
    });
  }
  return list;
});

const paginatedCases = computed(() => {
  const start = (page.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredCases.value.slice(start, end);
});

const totalPages = computed(() => Math.max(1, Math.ceil(filteredCases.value.length / pageSize)));
const startIndex = computed(() => (filteredCases.value.length > 0 ? (page.value - 1) * pageSize + 1 : 0));
const endIndex = computed(() => Math.min(page.value * pageSize, filteredCases.value.length));

const sortBy = (col) => {
  if (sortColumn.value === col) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn.value = col; sortDirection.value = 'asc';
  }
  page.value = 1;
};

const handleSearch = () => {
  page.value = 1;
};

const prevPage = () => { if (page.value > 1) page.value--; };
const nextPage = () => { if (page.value < totalPages.value) page.value++; };

const formatDateTime = (s) => {
  if (!s) return '';
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return s;
  return d.toLocaleString();
};

const toggleLogView = () => {
  showAllLogs.value = !showAllLogs.value;
  if (showAllLogs.value) {
    fetchAllCaseLogs();
  } else {
    selectedCaseId.value = null; // Clear selected case if toggling to case-specific logs
    fetchLogs(selectedCaseId.value); // Fetch logs for the currently selected case
  }
};

const fetchAllCaseLogs = async () => {
  loadingLogs.value = true;
  try {
    const token = localStorage.getItem('jwt');
    const resp = await axios.get('/api/super-user/all-case-logs', { headers: { 'Authorization': `Bearer ${token}` } });
    logs.value = resp.data?.logs || [];
  } catch (e) {
    console.error('Failed to fetch all case logs:', e);
    logs.value = [];
  } finally {
    loadingLogs.value = false;
  }
};



onMounted(() => {
  fetchActivityCases();
  fetchRiskOfficers(); // Fetch risk officers for super user
});
</script>

<style scoped>
.dashboard-bg { padding: 12px; }
.header-content { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.user-info { display: flex; align-items: center; gap: .75rem; }
.user-type { font-size: 0.875rem; font-weight: 500; color: #64748b; background: #f1f5f9; padding: 4px 8px; border-radius: 6px; text-transform: capitalize; }

.activity-layout { display: grid; grid-template-columns: 2fr 1.5fr; gap: 16px; }
.activity-list, .activity-logs { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px; }


.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.table-responsive { width: 100%; overflow-x: auto; }
.case-table { width: 100%; border-collapse: collapse; min-width: 800px; }
.case-table th, .case-table td { padding: 10px; border-bottom: 1px solid #eef2f7; text-align: left; }
.case-table tbody tr:hover { background: #f7fbff; cursor: pointer; }
.case-table tbody tr.selected { background: #eef6ff; }
.chip { display: inline-block; padding: 2px 8px; border-radius: 8px; background: #eef2ff; color: #4338ca; font-weight: 600; font-size: 12px; }
.status-badge { display: inline-block; padding: 4px 10px; border-radius: 999px; font-weight: 700; font-size: 12px; background: #f3f4f6; color: #111827; text-transform: capitalize; }

/* Specific status badge styles for better visibility */
.status-badge.new { background: #e0f2fe; color: #075985; }
.status-badge.assigned { background: #fef3c7; color: #92400e; }
.status-badge.closed { background: #dcfce7; color: #166534; }
.status-badge.open { background: #e9d5ff; color: #6b21a8; }
.status-badge.reopened { background: #fef2f2; color: #dc2626; }
.status-badge.pending { background: #fef3c7; color: #92400e; }
.status-badge.approved { background: #dcfce7; color: #166534; }
.status-badge.rejected { background: #fef2f2; color: #dc2626; }
.reopen-btn {
  margin-left: 8px;
  background-color: #4f46e5;
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  white-space: nowrap;
  transition: background-color 0.2s;
}
.reopen-btn:hover {
  background-color: #4338ca;
}
.reopen-btn:active {
  background-color: #3730a3;
}

/* Log Toggle Styles */
.log-toggle {
  display: flex;
  align-items: center;
}

.toggle-btn {
  padding: 6px 12px;
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn:hover {
  background-color: #e5e7eb;
  border-color: #9ca3af;
}

.toggle-btn.active {
  background-color: #4f46e5;
  color: white;
  border-color: #4f46e5;
}

.toggle-btn.active:hover {
  background-color: #4338ca;
  border-color: #4338ca;
}
.logs-box { min-height: 300px; border: 1px solid #edf2f7; border-radius: 8px; padding: 10px; background: #fafbfe; }
.case-log-list { list-style: none; padding: 0; margin: 0; }
.case-log-item { display: flex; gap: 10px; padding: 8px 0; border-bottom: 1px solid #e9eef5; font-size: 14px; align-items: center; }
.case-log-item:last-child { border-bottom: none; }
.log-time { color: #6b7280; min-width: 180px; font-size: 12px; }
.log-case-info { 
  color: #7c3aed; 
  font-weight: 600; 
  font-size: 12px; 
  min-width: 150px; 
  background: #f3f4f6; 
  padding: 2px 6px; 
  border-radius: 4px; 
}
.log-user { color: #0d6efd; font-weight: 600; }
.log-action { color: #059669; font-weight: 600; }
.logs-loading, .logs-empty { padding: 14px; color: #6b7280; }

@media (max-width: 1024px) {
  .activity-layout { grid-template-columns: 1fr; }
}

/* Beautiful Confirmation Dialog Styles */
.beautiful-confirmation-dialog {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  animation: backdrop-fade-in 0.3s ease-out;
}

@keyframes backdrop-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.dialog-container {
  position: relative;
  background: white;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  animation: dialog-slide-up 0.4s ease-out;
  border: 1px solid #e5e7eb;
}

@keyframes dialog-slide-up {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.dialog-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px 28px 20px;
  text-align: center;
  position: relative;
}

.dialog-icon {
  font-size: 48px;
  margin-bottom: 12px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.dialog-header h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.dialog-content {
  padding: 28px;
  background: #fafbfc;
}

.dialog-question {
  font-size: 18px;
  color: #1f2937;
  line-height: 1.6;
  margin: 0 0 20px 0;
  text-align: center;
  font-weight: 500;
}

.dialog-warning {
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 12px;
  padding: 20px;
  position: relative;
}

.warning-icon {
  font-size: 24px;
  margin-bottom: 12px;
  text-align: center;
}

.warning-text {
  color: #92400e;
  font-size: 14px;
  line-height: 1.6;
}

.warning-text strong {
  color: #78350f;
  font-weight: 600;
}

.warning-text ul {
  margin: 12px 0 0 0;
  padding-left: 20px;
}

.warning-text li {
  margin: 8px 0;
}

.status-closed {
  background: #dcfce7;
  color: #166534;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 12px;
}

.status-reopened {
  background: #fef2f2;
  color: #dc2626;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 12px;
}

.dialog-actions {
  padding: 20px 28px 24px;
  display: flex;
  gap: 16px;
  justify-content: center;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.btn-cancel, .btn-confirm {
  padding: 12px 24px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.3s ease;
  min-width: 120px;
  position: relative;
  overflow: hidden;
}

.btn-cancel {
  background: #f3f4f6;
  color: #374151;
  border: 2px solid #d1d5db;
}

.btn-cancel:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn-confirm {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.4);
}

.btn-confirm:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.5);
}

.btn-confirm:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
}

/* Responsive design */
@media (max-width: 640px) {
  .dialog-container {
    width: 95%;
    margin: 20px;
  }
  
  .dialog-content {
    padding: 20px;
  }
  
  .dialog-actions {
    flex-direction: column;
    gap: 12px;
  }
  
  .btn-cancel, .btn-confirm {
    width: 100%;
  }
}
</style>


