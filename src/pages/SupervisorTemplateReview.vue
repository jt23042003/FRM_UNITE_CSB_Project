<template>
  <div class="supervisor-template-review">
    <div class="page-header">
      <h2>Supervisor Template Review</h2>
      <p>Review and approve/reject template responses from your department</p>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading template responses...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <div class="error-icon">❌</div>
      <h3>Error Loading Data</h3>
      <p>{{ error }}</p>
      <button @click="loadTemplateResponses" class="btn-retry">Try Again</button>
    </div>

    <div v-else-if="templateResponses.length === 0" class="empty-state">
      <div class="empty-icon">📋</div>
      <h3>No Template Responses</h3>
      <p>There are no template responses pending review for your department.</p>
    </div>

    <div v-else class="template-responses-container">
      <div class="responses-summary">
        <div class="summary-card">
          <div class="summary-number">{{ pendingCount }}</div>
          <div class="summary-label">Pending Review</div>
        </div>
        <div class="summary-card">
          <div class="summary-number">{{ approvedCount }}</div>
          <div class="summary-label">Approved</div>
        </div>
        <div class="summary-card">
          <div class="summary-number">{{ rejectedCount }}</div>
          <div class="summary-label">Rejected</div>
        </div>
      </div>

      <div class="responses-list">
        <div v-for="response in templateResponses" :key="response.id" class="response-card">
          <div class="response-header">
            <div class="response-info">
              <h4>{{ response.template_name }}</h4>
              <div class="response-meta">
                <span class="assigned-to">By: {{ response.assigned_to }}</span>
                <span class="department">Dept: {{ response.department }}</span>
                <span class="submitted-date">Submitted: {{ formatDate(response.created_at) }}</span>
              </div>
            </div>
            <div class="response-status">
              <span :class="['status-badge', response.status]">
                {{ formatStatus(response.status) }}
              </span>
            </div>
          </div>

          <div v-if="response.template_description" class="template-description">
            {{ response.template_description }}
          </div>

          <div class="response-questions">
            <h5>Responses:</h5>
            <div v-for="(value, questionId) in response.responses" :key="questionId" class="question-response">
              <div class="question-label">Question {{ questionId }}:</div>
              <div class="response-value">{{ value || 'No response' }}</div>
            </div>
          </div>

          <div v-if="response.rejection_reason" class="rejection-reason">
            <strong>Rejection Reason:</strong> {{ response.rejection_reason }}
          </div>

          <div v-if="response.status === 'pending_approval'" class="response-actions">
            <button @click="approveResponse(response.id)" class="btn-approve">
              ✅ Approve
            </button>
            <button @click="openRejectModal(response.id)" class="btn-reject">
              ❌ Reject
            </button>
          </div>

          <div v-if="response.status === 'approved'" class="approval-info">
            <span class="approved-by">Approved by: {{ response.approved_by }}</span>
            <span class="approved-date">on {{ formatDate(response.approved_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Reject Modal -->
    <div v-if="isRejectModalOpen" class="modal-overlay" @click="closeRejectModal">
      <div class="modal-content" @click.stop>
        <h3>Reject Template Response</h3>
        <div class="form-group">
          <label for="rejection-reason">Rejection Reason:</label>
          <textarea 
            id="rejection-reason"
            v-model="rejectionReason" 
            placeholder="Please provide a reason for rejection..."
            rows="4"
            class="rejection-textarea"
          ></textarea>
        </div>
        <div class="modal-actions">
          <button @click="closeRejectModal" class="btn-cancel">Cancel</button>
          <button @click="rejectResponse" class="btn-confirm-reject">Confirm Rejection</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const caseId = route.params.case_id;

// State
const loading = ref(true);
const error = ref(null);
const templateResponses = ref([]);
const isRejectModalOpen = ref(false);
const rejectionReason = ref('');
const currentResponseId = ref(null);

// Computed
const pendingCount = computed(() => 
  templateResponses.value.filter(r => r.status === 'pending_approval').length
);

const approvedCount = computed(() => 
  templateResponses.value.filter(r => r.status === 'approved').length
);

const rejectedCount = computed(() => 
  templateResponses.value.filter(r => r.status === 'rejected').length
);

// Methods
const loadTemplateResponses = async () => {
  try {
    loading.value = true;
    error.value = null;
    
    const token = localStorage.getItem('jwt');
    if (!token) {
      error.value = 'Authentication token not found';
      return;
    }

    const response = await axios.get(`/api/supervisor/template-responses/${caseId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.data && response.data.success) {
      templateResponses.value = response.data.responses;
    } else {
      error.value = 'Failed to load template responses';
    }
  } catch (err) {
    console.error('Error loading template responses:', err);
    error.value = err.response?.data?.detail || 'Failed to load template responses';
  } finally {
    loading.value = false;
  }
};

const approveResponse = async (responseId) => {
  try {
    const token = localStorage.getItem('jwt');
    const response = await axios.put(`/api/supervisor/template-responses/${responseId}/approve`, {}, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.data && response.data.success) {
      // Refresh the list
      await loadTemplateResponses();
      showSuccessMessage('Template response approved successfully');
    }
  } catch (err) {
    console.error('Error approving response:', err);
    showErrorMessage('Failed to approve template response');
  }
};

const openRejectModal = (responseId) => {
  currentResponseId.value = responseId;
  rejectionReason.value = '';
  isRejectModalOpen.value = true;
};

const closeRejectModal = () => {
  isRejectModalOpen.value = false;
  currentResponseId.value = null;
  rejectionReason.value = '';
};

const rejectResponse = async () => {
  if (!rejectionReason.value.trim()) {
    showErrorMessage('Please provide a rejection reason');
    return;
  }

  try {
    const token = localStorage.getItem('jwt');
    const response = await axios.put(`/api/supervisor/template-responses/${currentResponseId.value}/reject`, {
      rejection_reason: rejectionReason.value.trim()
    }, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.data && response.data.success) {
      closeRejectModal();
      await loadTemplateResponses();
      showSuccessMessage('Template response rejected successfully');
    }
  } catch (err) {
    console.error('Error rejecting response:', err);
    showErrorMessage('Failed to reject template response');
  }
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString();
};

const formatStatus = (status) => {
  const statusMap = {
    'pending_approval': 'Pending Review',
    'approved': 'Approved',
    'rejected': 'Rejected'
  };
  return statusMap[status] || status;
};

const showSuccessMessage = (message) => {
  if (window.showNotification) {
    window.showNotification('success', 'Success', message);
  } else {
    alert(message);
  }
};

const showErrorMessage = (message) => {
  if (window.showNotification) {
    window.showNotification('error', 'Error', message);
  } else {
    alert(message);
  }
};

// Lifecycle
onMounted(() => {
  if (caseId) {
    loadTemplateResponses();
  }
});
</script>

<style scoped>
.supervisor-template-review {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-header h2 {
  color: #1a3a5d;
  margin-bottom: 8px;
  font-size: 28px;
}

.page-header p {
  color: #6c757d;
  font-size: 16px;
}

.loading-container, .error-container, .empty-state {
  text-align: center;
  padding: 60px 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #0d6efd;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-container .error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.btn-retry {
  background: #0d6efd;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.empty-state .empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.responses-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.summary-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  text-align: center;
}

.summary-number {
  font-size: 36px;
  font-weight: bold;
  color: #0d6efd;
  margin-bottom: 8px;
}

.summary-label {
  color: #6c757d;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.responses-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.response-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-left: 4px solid #0d6efd;
}

.response-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.response-info h4 {
  margin: 0 0 8px 0;
  color: #1a3a5d;
  font-size: 18px;
}

.response-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #6c757d;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.pending_approval {
  background: #fff3cd;
  color: #856404;
}

.status-badge.approved {
  background: #d4edda;
  color: #155724;
}

.status-badge.rejected {
  background: #f8d7da;
  color: #721c24;
}

.template-description {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 16px;
  color: #495057;
  font-style: italic;
}

.response-questions h5 {
  margin: 0 0 12px 0;
  color: #1a3a5d;
  font-size: 16px;
}

.question-response {
  margin-bottom: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.question-label {
  font-weight: 600;
  color: #495057;
  margin-bottom: 4px;
  font-size: 14px;
}

.response-value {
  color: #212529;
  font-size: 14px;
}

.rejection-reason {
  background: #f8d7da;
  color: #721c24;
  padding: 12px;
  border-radius: 6px;
  margin: 16px 0;
  font-size: 14px;
}

.response-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.btn-approve, .btn-reject {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-approve {
  background: #28a745;
  color: white;
}

.btn-approve:hover {
  background: #218838;
}

.btn-reject {
  background: #dc3545;
  color: white;
}

.btn-reject:hover {
  background: #c82333;
}

.approval-info {
  margin-top: 16px;
  padding: 12px;
  background: #d4edda;
  color: #155724;
  border-radius: 6px;
  font-size: 14px;
  display: flex;
  gap: 16px;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 24px;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
}

.modal-content h3 {
  margin: 0 0 20px 0;
  color: #1a3a5d;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #495057;
}

.rejection-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-family: inherit;
  resize: vertical;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-cancel, .btn-confirm-reject {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
}

.btn-cancel {
  background: #6c757d;
  color: white;
}

.btn-confirm-reject {
  background: #dc3545;
  color: white;
}

@media (max-width: 768px) {
  .supervisor-template-review {
    padding: 16px;
  }
  
  .response-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .response-meta {
    flex-direction: column;
    gap: 4px;
  }
  
  .response-actions {
    flex-direction: column;
  }
  
  .modal-content {
    margin: 20px;
    width: auto;
  }
}
</style>
