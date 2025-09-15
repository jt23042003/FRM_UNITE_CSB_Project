<template>
  <div class="template-display-container">
    <div class="page-header">
      <h1>Template Library</h1>
      <p class="page-description">View all available templates and their field requirements</p>
    </div>

    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading templates...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <div class="error-icon">⚠️</div>
      <h3>Error Loading Templates</h3>
      <p>{{ error }}</p>
      <button @click="fetchTemplates" class="retry-button">Try Again</button>
    </div>

    <div v-else-if="templates.length === 0" class="empty-container">
      <div class="empty-icon">📋</div>
      <h3>No Templates Available</h3>
      <p>There are currently no templates in the system.</p>
    </div>

    <div v-else class="templates-grid">
      <div v-for="template in templates" :key="template.id" class="template-card">
        <div class="template-header">
          <h3 class="template-name">{{ template.name }}</h3>
          <div class="template-status">
            <span class="status-badge active">Active</span>
          </div>
        </div>
        
        <div class="template-description">
          <p>{{ template.description || 'No description available' }}</p>
        </div>

        <div class="template-stats">
          <div class="stat-item">
            <span class="stat-label">Total Questions:</span>
            <span class="stat-value">{{ template.questions.length }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Required:</span>
            <span class="stat-value required">{{ getRequiredCount(template.questions) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Optional:</span>
            <span class="stat-value optional">{{ getOptionalCount(template.questions) }}</span>
          </div>
        </div>

        <div class="template-questions">
          <h4>Questions & Fields</h4>
          <div class="questions-list">
            <div v-for="(question, index) in template.questions" :key="question.id" class="question-item">
              <div class="question-header">
                <div class="question-number">{{ index + 1 }}</div>
                <div class="question-content">
                  <div class="question-text">{{ question.question }}</div>
                  <div class="question-meta">
                    <span class="question-type">{{ getQuestionTypeLabel(question.type) }}</span>
                    <span :class="['required-badge', question.required ? 'required' : 'optional']">
                      {{ question.required ? 'Required' : 'Optional' }}
                    </span>
                  </div>
                </div>
              </div>
              
              <div v-if="question.help_text" class="question-help">
                <span class="help-icon">💡</span>
                <span class="help-text">{{ question.help_text }}</span>
              </div>

              <!-- Question-specific details -->
              <div v-if="question.type === 'radio' && question.options" class="question-options">
                <span class="options-label">Options:</span>
                <div class="options-list">
                  <span v-for="option in question.options" :key="option" class="option-tag">
                    {{ option }}
                  </span>
                </div>
              </div>

              <div v-if="question.type === 'number'" class="question-constraints">
                <span v-if="question.min_value !== undefined" class="constraint">
                  Min: {{ question.min_value }}
                </span>
                <span v-if="question.max_value !== undefined" class="constraint">
                  Max: {{ question.max_value }}
                </span>
              </div>

              <div v-if="question.type === 'textarea'" class="question-constraints">
                <span v-if="question.max_length" class="constraint">
                  Max Length: {{ question.max_length }} characters
                </span>
              </div>

              <div v-if="question.type === 'file_upload'" class="question-constraints">
                <span v-if="question.allowed_types" class="constraint">
                  Allowed Types: {{ question.allowed_types.join(', ') }}
                </span>
                <span v-if="question.max_size_mb" class="constraint">
                  Max Size: {{ question.max_size_mb }}MB
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const templates = ref([]);
const isLoading = ref(true);
const error = ref(null);

const fetchTemplates = async () => {
  try {
    isLoading.value = true;
    error.value = null;
    
    const token = localStorage.getItem('jwt');
    const response = await axios.get('/api/templates', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.data && response.data.success) {
      templates.value = response.data.templates;
    } else {
      throw new Error('Failed to fetch templates');
    }
  } catch (err) {
    console.error('Error fetching templates:', err);
    error.value = err.response?.data?.detail || 'Failed to load templates';
  } finally {
    isLoading.value = false;
  }
};

const getRequiredCount = (questions) => {
  return questions.filter(q => q.required).length;
};

const getOptionalCount = (questions) => {
  return questions.filter(q => !q.required).length;
};

const getQuestionTypeLabel = (type) => {
  const typeLabels = {
    'radio': 'Multiple Choice',
    'text': 'Text Input',
    'textarea': 'Text Area',
    'number': 'Number Input',
    'date': 'Date Picker',
    'file_upload': 'File Upload'
  };
  return typeLabels[type] || type;
};

onMounted(() => {
  fetchTemplates();
});
</script>

<style scoped>
.template-display-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  background: #f8f9fa;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
  padding: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.page-header h1 {
  margin: 0 0 8px 0;
  color: #1a1a1a;
  font-size: 28px;
  font-weight: 700;
}

.page-description {
  margin: 0;
  color: #6c757d;
  font-size: 16px;
}

.loading-container, .error-container, .empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e9ecef;
  border-top: 4px solid #0d6efd;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon, .empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.retry-button {
  background: #0d6efd;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  margin-top: 16px;
}

.retry-button:hover {
  background: #0b5ed7;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 24px;
}

.template-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e9ecef;
}

.template-name {
  margin: 0;
  color: #1a1a1a;
  font-size: 20px;
  font-weight: 600;
  flex: 1;
}

.template-status {
  margin-left: 16px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.active {
  background: #d4edda;
  color: #155724;
}

.template-description {
  padding: 16px 24px;
  border-bottom: 1px solid #e9ecef;
}

.template-description p {
  margin: 0;
  color: #6c757d;
  line-height: 1.5;
}

.template-stats {
  display: flex;
  justify-content: space-around;
  padding: 16px 24px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.stat-value.required {
  color: #dc3545;
}

.stat-value.optional {
  color: #28a745;
}

.template-questions {
  padding: 20px 24px;
}

.template-questions h4 {
  margin: 0 0 16px 0;
  color: #1a1a1a;
  font-size: 16px;
  font-weight: 600;
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-item {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  background: #fafbfc;
}

.question-header {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.question-number {
  width: 24px;
  height: 24px;
  background: #0d6efd;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.question-content {
  flex: 1;
}

.question-text {
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 4px;
  line-height: 1.4;
}

.question-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.question-type {
  background: #e9ecef;
  color: #495057;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.required-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.required-badge.required {
  background: #f8d7da;
  color: #721c24;
}

.required-badge.optional {
  background: #d4edda;
  color: #155724;
}

.question-help {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #fff3cd;
  border-radius: 6px;
  border-left: 3px solid #ffc107;
}

.help-icon {
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 1px;
}

.help-text {
  font-size: 13px;
  color: #856404;
  line-height: 1.4;
}

.question-options {
  margin-top: 8px;
}

.options-label {
  font-size: 12px;
  color: #6c757d;
  font-weight: 500;
  margin-right: 8px;
}

.options-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.option-tag {
  background: #e7f3ff;
  color: #0d6efd;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.question-constraints {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.constraint {
  background: #f8f9fa;
  color: #495057;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid #dee2e6;
}

/* Responsive Design */
@media (max-width: 768px) {
  .template-display-container {
    padding: 16px;
  }
  
  .templates-grid {
    grid-template-columns: 1fr;
  }
  
  .template-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .question-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .question-constraints {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
