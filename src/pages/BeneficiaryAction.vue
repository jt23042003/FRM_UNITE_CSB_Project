<template>
  <div class="pma-container">
    <div v-if="isReadOnly" class="readonly-banner">
      <span>This case is closed. Editing is disabled.</span>
    </div>
    <div class="steps-header">
      <div class="steps-container">
        <div
          v-for="(step, index) in steps"
          :key="index"
          :class="['step', { active: currentStep === index + 1, completed: currentStep > index + 1 }]"
          @click="goToStep(index + 1)"
        >
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-title">{{ step.title }}</div>
        </div>
      </div>
    </div>

    <div class="step-content">
      <div v-if="currentStep === 1" class="step-panel">
        <h3>Alert - Potential Mule Account</h3>

        <div v-if="isLoading" class="loading-indicator">
          Loading Case Details...
          <div class="skeleton-table" style="margin-top: 12px;">
            <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
            <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
            <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
          </div>
        </div>
        <div v-else-if="fetchError" class="error-indicator">{{ fetchError }}</div>

        <div v-else class="comparison-grid">
          <div class="details-section">
            <h4>Customer Details - I4C</h4>
            <div class="details-row">
              <div class="field-group">
                <label>Name</label>
                <input type="text" v-model="i4cDetails.name" readonly />
              </div>
              <div class="field-group">
                <label>Mobile</label>
                <input type="text" v-model="i4cDetails.mobile" readonly />
              </div>
               <div class="field-group">
                <label>Email</label>
                <input type="text" v-model="i4cDetails.email" readonly />
              </div>
            </div>
            <div class="details-row">
              <div class="field-group">
                <label>Bank Account</label>
                <input type="text" v-model="i4cDetails.bankAc" readonly />
              </div>
            </div>
          </div>

          <div class="details-section">
            <h4>Customer Details - Bank</h4>
            <div class="details-row">
              <div class="field-group highlight">
                <label>Name</label>
                <input type="text" v-model="bankDetails.name" readonly />
              </div>
              <div class="field-group highlight">
                <label>Mobile</label>
                <input type="text" v-model="bankDetails.mobile" readonly />
              </div>
              <div class="field-group highlight">
                <label>Email</label>
                <input type="text" v-model="bankDetails.email" readonly />
              </div>
            </div>
            <div class="details-row">
               <div class="field-group">
                <label>Customer ID</label>
                <input type="text" v-model="bankDetails.customerId" readonly />
              </div>
              <div class="field-group">
                <label>Bank Account</label>
                <input type="text" v-model="bankDetails.bankAc" readonly />
              </div>
              <div class="field-group">
                <label>Account Status</label>
                <input type="text" v-model="bankDetails.acStatus" readonly />
              </div>
            </div>
             <div class="details-row">
              <div class="field-group">
                <label>PAN</label>
                <input type="text" v-model="bankDetails.pan" readonly />
              </div>
              <div class="field-group">
                <label>Aadhaar</label>
                <input type="text" v-model="bankDetails.aadhaar" readonly />
              </div>
              <div class="field-group">
                <label>Product Code</label>
                <input type="text" v-model="bankDetails.productCode" readonly />
              </div>
            </div>
             <div class="details-row">
              <div class="field-group">
                <label>AQB</label>
                <input type="text" v-model="bankDetails.aqb" readonly />
              </div>
               <div class="field-group">
                <label>Balance</label>
                <input type="text" v-model="bankDetails.availBal" readonly />
              </div>
              <div class="field-group">
                <label>Relationship Value</label>
                <input type="text" v-model="bankDetails.relValue" readonly />
              </div>
            </div>
             <div class="details-row">
              <div class="field-group">
                <label>Vintage (MoB)</label>
                <input type="text" v-model="bankDetails.mobVintage" readonly />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="currentStep === 2" class="step-panel">
        <h3>Analysis & Investigation <span v-if="userRole === 'supervisor' && latestActionStatus" :class="['status-chip', latestActionStatus === 'approved' ? 'approved' : (latestActionStatus === 'pending_approval' ? 'pending' : 'rejected')]">{{ latestActionStatus === 'approved' ? 'Approved' : (latestActionStatus === 'pending_approval' ? 'Pending approval' : 'Rejected') }}</span></h3>
        
        <!-- Loading indicator for analysis data -->
        <div v-if="isLoadingAdditionalDetails && !isAnalysisDataLoaded" class="section-loading">
          <div class="loading-spinner"></div>
          <span>Loading analysis data, templates, and saved work...</span>
        </div>
        
        <!-- Approved Template Responses Summary for Risk Officers -->
        <div v-if="userRole === 'risk_officer' && approvedTemplateResponses.length > 0" class="approved-responses-summary">
          <div class="summary-header">
            <span class="summary-icon">✅</span>
            <h4>Approved Template Responses</h4>
          </div>
          <div class="summary-content">
            <p><strong>{{ approvedTemplateResponses.length }}</strong> template response(s) have been approved and are ready for review.</p>
            <div class="template-summary-list">
              <div v-for="response in approvedTemplateResponses" :key="response.id" class="template-summary-item">
                <span class="template-name">{{ response.template_name }}</span>
                <span class="template-meta">
                  by {{ response.assigned_to }} • {{ response.department }} • {{ new Date(response.approved_at).toLocaleDateString() }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Latest Changes Summary for Risk Officers (Only show non-Risk departments) -->
        <div v-if="userRole === 'risk_officer' && mergedFromDepartments && mergedFromDepartments.filter(d => d !== '__base__').length > 0" class="latest-changes-summary">
          <div class="summary-header">
            <span class="summary-icon">📋</span>
            <h4>Latest Case Changes</h4>
          </div>
          <div class="summary-content">
            <p>This case has been updated by the following departments:</p>
            <div class="department-list">
              <div v-for="dept in mergedFromDepartments.filter(d => d !== '__base__')" :key="dept" class="department-item">
                <span class="dept-name">{{ dept }}</span>
                <span class="dept-status">✅ Approved</span>
              </div>
            </div>
          </div>
        </div>
        <div class="form-section compact-analysis">
          <div class="field-group">
            <label>Analysis Update</label>
            <div class="input-row">
              <select v-model="action.analysisLOV" :disabled="isReadOnly" class="compact-select">
                <option value="">Select Reason</option>
                <option v-for="item in analysisReasons" :key="item.reason" :value="item.reason">{{ item.reason }}</option>
              </select>
              <textarea v-model="action.analysisUpdate" :disabled="isReadOnly" placeholder="Update details" class="compact-textarea analysis-textarea"></textarea>
            </div>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-section">
            <div class="field-group">
              <label>Data Uploads</label>
              
              <div v-for="(uploadBlock, blockIndex) in action.dataUploads" :key="uploadBlock.id" class="data-upload-block">
                
                <button 
                  @click="removeDataUploadBlock(blockIndex)"
                  v-if="action.dataUploads.length > 1 && userRole === 'risk_officer'"
                  :disabled="isReadOnly"
                  class="btn-remove-row"
                  title="Remove Upload Section"
                >×</button>

                <div class="upload-comment-row">
                  <!-- Show file drop zone only if no files uploaded yet -->
                  <div v-if="uploadBlock.files.length === 0" class="file-drop-zone"
                    :class="{ 'drag-over': uploadBlock.isDragOver }"
                    @dragover.prevent="onDragOver(blockIndex)"
                    @dragleave.prevent="onDragLeave(blockIndex)"
                    @drop.prevent="onFileDrop($event, blockIndex)"
                    @click="triggerFileInput(blockIndex)"
                    :disabled="isReadOnly"
                  >
                    <div class="upload-icon">📁</div>
                    <div class="upload-text">
                      <strong>Drop files here or click to browse</strong>
                      <p>Supports: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG (Max 10MB each)</p>
                    </div>
                    <input
                      :ref="el => { if (el) fileInputRefs[blockIndex] = el }"
                      type="file"
                      multiple
                      accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
                      @change="onFileSelect($event, blockIndex)"
                      class="hidden-file-input"
                      :disabled="isReadOnly"
                    />
                  </div>
                  
                  <!-- No file input when files already exist - just show textarea and files -->
                  
                  <textarea v-model="uploadBlock.comment" :disabled="isReadOnly" placeholder="Add comments for your uploads..." class="compact-textarea data-uploads-textarea"></textarea>
                </div>
                
                <div v-if="uploadBlock.files.length > 0" class="uploaded-files-list">
                  <div class="files-header">
                    <span>Uploaded Files ({{ uploadBlock.files.length }})</span>
                  </div>
                  <div
                    v-for="(file, fileIndex) in uploadBlock.files"
                    :key="fileIndex"
                    class="file-item"
                  >
                    <div class="file-info">
                      <div class="file-icon">{{ getFileIcon(file.type) }}</div>
                      <div class="file-details">
                        <div class="file-name-container">
                          <input
                            v-if="file.isRenaming"
                            v-model="file.newName"
                            @blur="saveFileName(blockIndex, fileIndex)"
                            @keyup.enter="saveFileName(blockIndex, fileIndex)"
                            @keyup.escape="cancelRename(blockIndex, fileIndex)"
                            class="file-name-input"
                            placeholder="Enter new name"
                            :disabled="isReadOnly"
                          />
                          <span v-else class="file-name">{{ file.displayName }}</span>
                        </div>
                        <div class="file-meta">
                          {{ formatFileSize(file.size) }} • {{ file.type.split('/')[1].toUpperCase() }}
                        </div>
                      </div>
                    </div>
                    <div class="file-actions">
                       <button
                        v-if="!file.isRenaming"
                        @click="startRename(blockIndex, fileIndex)"
                        class="btn-file-action btn-rename"
                        title="Rename file"
                        :disabled="isReadOnly"
                      >✏️</button>
                      <button
                        v-if="file.isRenaming"
                        @click="saveFileName(blockIndex, fileIndex)"
                        class="btn-file-action btn-save"
                        title="Save name"
                        :disabled="isReadOnly"
                      >✅</button>
                      <button
                        v-if="file.isRenaming"
                        @click="cancelRename(blockIndex, fileIndex)"
                        class="btn-file-action btn-cancel"
                        title="Cancel rename"
                        :disabled="isReadOnly"
                      >❌</button>
                      <button
                        @click="removeFile(blockIndex, fileIndex)"
                        class="btn-file-action btn-remove"
                        title="Remove file"
                        :disabled="isReadOnly"
                      >🗑️</button>
                    </div>
                  </div>
                </div>
              </div>
              <button @click="addDataUploadBlock" :disabled="isReadOnly || isReviewMode" class="btn-add-row">+ Add Document</button>
            </div>

          </div>
          
          <!-- Assignment Section - Only show for non-review mode -->
          <div class="form-section" v-if="!isReviewMode">
            <!-- Warning for reopened cases -->
            <div v-if="status === 'Reopened'" class="reopened-warning">
              <div class="warning-icon">⚠️</div>
              <div class="warning-text">
                <strong>Case Reopened:</strong> This case was reopened by a super user. <strong>Assignment functionality is disabled</strong>
              </div>
            </div>
            <div class="field-group">
              <label v-if="userRole === 'risk_officer'">Assignments</label>
              <label v-else-if="userRole === 'others'">Send Back</label>
              <label v-else-if="userRole === 'supervisor'">Review & Approve</label>
              
              <!-- Assignment UI for Risk Officers -->
              <div v-if="userRole === 'risk_officer'">
                <div v-for="(review, reviewIndex) in action.reviews" :key="review.id" class="review-comment-row">
                  <div class="comment-user-selection-row">
                    <select v-model="review.selectedDepartment" :disabled="isAssignmentDisabled" class="compact-select" @change="handleDepartmentChange(review)">
                      <option value="">Select Department</option>
                      <option v-for="dept in departments" :key="dept.id" :value="dept.name">
                        {{ dept.name }}
                      </option>
                    </select>
                    <select v-model="review.userId" :disabled="isAssignmentDisabled || !review.selectedDepartment" class="compact-select">
                      <option value="">Select User</option>
                      <option v-for="user in review.userList" :key="user.id" :value="user.name">
                        {{ user.name }}
                      </option>
                    </select>
                  </div>
                  <!-- Template Selection -->
                  <div class="template-selection-row">
                    <select v-model="review.templateId" :disabled="isAssignmentDisabled" class="compact-select">
                      <option value="">Select Template (Optional)</option>
                      <option v-for="template in availableTemplates" :key="template.id" :value="template.id">
                        {{ template.name }}
                      </option>
                    </select>
                    <div v-if="review.templateId" class="template-info">
                      <small>{{ getTemplateDescription(review.templateId) }}</small>
                    </div>
                  </div>
                  <textarea v-model="review.text" :disabled="isAssignmentDisabled" placeholder="Add comments (required)..." class="compact-textarea" required></textarea>
                  <button @click="removeReviewCommentRow(reviewIndex)" v-if="action.reviews.length > 1" :disabled="isAssignmentDisabled" class="btn-remove-row" title="Remove Assignment Section">×</button>
                </div>
                <button @click="addReviewCommentRow" :disabled="isAssignmentDisabled" class="btn-add-row">+ Add Assignment</button>
                <button v-if="!isAssignmentDisabled" @click="assignCase" class="btn-assign btn-assign-prominent">
                  <span class="assignment-icon">⚡</span>
                  <span>Proceed with Assignment</span>
                </button>
              </div>
              
              <!-- Send Back UI for Others -->
              <div v-else-if="userRole === 'others'">
                <div class="input-row" style="gap:8px; align-items:flex-start;">
                  <select v-model="sendBackReasonId" :disabled="isReadOnly" class="compact-select">
                    <option value="">Select Reason</option>
                    <option v-for="r in sendBackReasons" :key="r.id" :value="r.id">{{ r.reason }}</option>
                  </select>
                  <textarea v-model="sendBackComment" :disabled="isReadOnly" placeholder="Add comments for send back..." class="compact-textarea"></textarea>
                </div>
                <button v-if="!isReadOnly" @click="sendBackCase" class="btn-assign">Send Back</button>
              </div>
              
              <!-- Supervisor Review UI -->
              <div v-else-if="userRole === 'supervisor'">
                <div class="supervisor-info-box">
                  <div class="info-icon">ℹ️</div>
                  <div class="info-content">
                    <strong>Supervisor Review Mode</strong>
                    <p>You can review template responses, data uploads, and approve or reject changes from department users.</p>
                    <p>Use the sections below to review submitted work and make approval decisions.</p>
                  </div>
                  <!-- NEW: Button to access dedicated template review page -->
                  <div class="supervisor-actions">
                    <router-link 
                      :to="{ name: 'SupervisorTemplateReview', params: { case_id: $route.params.case_id } }"
                      class="btn-template-review"
                    >
                      📋 Review Templates in Detail
                    </router-link>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Template Section for Others Users -->
          <div v-if="userRole === 'others' && assignedTemplate" class="form-section">
            <div class="field-group">
              <label>Template: {{ assignedTemplate.name }}</label>
              <div class="template-description">{{ assignedTemplate.description }}</div>
              
              <div class="template-questions">
                <div v-for="question in assignedTemplate.questions" :key="question.id" class="question-item">
                  <div class="question-header">
                    <span class="question-text">{{ question.question }}</span>
                    <span v-if="question.required" class="required-indicator">*</span>
                  </div>
                  
                  <!-- Radio Button Questions -->
                  <div v-if="question.type === 'radio'" class="question-options">
                    <label v-for="option in question.options" :key="option" class="radio-option">
                      <input 
                        type="radio" 
                        :name="question.id" 
                        :value="option" 
                        v-model="templateResponses[question.id]"
                        :disabled="isReadOnly"
                      />
                      <span>{{ option }}</span>
                    </label>
                  </div>
                  
                  <!-- Text Input Questions -->
                  <div v-else-if="question.type === 'text'" class="question-input">
                    <input 
                      type="text" 
                      v-model="templateResponses[question.id]"
                      :placeholder="question.help_text"
                      :disabled="isReadOnly"
                      class="compact-input"
                    />
                  </div>
                  
                  <!-- Textarea Questions -->
                  <div v-else-if="question.type === 'textarea'" class="question-input">
                    <textarea 
                      v-model="templateResponses[question.id]"
                      :placeholder="question.help_text"
                      :disabled="isReadOnly"
                      :maxlength="question.max_length"
                      class="compact-textarea"
                    ></textarea>
                  </div>
                  
                  <!-- Number Input Questions -->
                  <div v-else-if="question.type === 'number'" class="question-input">
                    <input 
                      type="number" 
                      v-model="templateResponses[question.id]"
                      :placeholder="question.help_text"
                      :min="question.min_value"
                      :max="question.max_value"
                      :disabled="isReadOnly"
                      class="compact-input"
                    />
                  </div>
                  
                  <!-- Date Input Questions -->
                  <div v-else-if="question.type === 'date'" class="question-input">
                    <input 
                      type="date" 
                      v-model="templateResponses[question.id]"
                      :disabled="isReadOnly"
                      class="compact-input"
                    />
                  </div>
                  
                  <!-- File Upload Questions -->
                  <div v-else-if="question.type === 'file_upload'" class="question-input">
                    <input 
                      type="file" 
                      multiple
                      @change="handleTemplateFileUpload($event, question.id)"
                      :accept="question.allowed_types?.join(',')"
                      :disabled="isReadOnly"
                      class="compact-input"
                    />
                    <small class="help-text">{{ question.help_text }}</small>
                    <small class="help-text">Files will be automatically added to the Data Uploads section above.</small>
                    
                    <!-- Show uploaded files for this question -->
                    <div v-if="getTemplateQuestionFiles(question.id).length > 0" class="template-files-preview">
                      <div class="template-files-header">
                        <span>📁 Files uploaded for this question:</span>
                      </div>
                      <div class="template-files-list">
                        <div v-for="file in getTemplateQuestionFiles(question.id)" :key="file.displayName" class="template-file-item">
                          <span class="file-icon">{{ getFileIcon(file.type) }}</span>
                          <span class="file-name">{{ file.displayName }}</span>
                          <span class="file-size">{{ formatFileSize(file.size) }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div v-if="question.help_text" class="help-text">{{ question.help_text }}</div>
                </div>
              </div>
              
              <button v-if="!isReadOnly" @click="saveTemplateResponses" class="btn-save">Save Template Responses</button>
            </div>
          </div>

          <!-- Template Responses Review Section for Supervisors -->
          <div v-if="userRole === 'supervisor' && caseTemplateResponses.length > 0" class="form-section">
            <div class="field-group">
              <label>Template Responses for Review</label>
              <div class="template-responses-review">
                <div v-for="response in caseTemplateResponses" :key="response.id" class="template-response-item">
                  <div class="template-response-header">
                    <h4>{{ response.template_name }}</h4>
                    <span :class="['template-response-status', response.status]">{{ response.status.replace('_', ' ') }}</span>
                  </div>
                  <div class="template-response-meta">
                    <span><strong>Submitted by:</strong> {{ response.assigned_to }}</span>
                    <span><strong>Department:</strong> {{ response.department || 'N/A' }}</span>
                    <span><strong>Submitted on:</strong> {{ new Date(response.created_at).toLocaleString() }}</span>
                  </div>
                  <div v-if="response.template_description" class="template-description">{{ response.template_description }}</div>
                  
                  <div class="template-questions-review">
                    <div v-for="question in getTemplateQuestions(response.template_id)" :key="question.id" class="question-review-item">
                      <div class="question-review-header">
                        <span class="question-text">{{ question.question }}</span>
                        <span v-if="question.required" class="required-indicator">*</span>
                      </div>
                      
                      <div class="question-response">
                        <strong>Response:</strong>
                        <span class="response-value">
                          {{ getResponseValue(response.responses, question.id) || 'No response provided' }}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div v-if="response.rejection_reason" class="rejection-reason">
                    <strong>Rejection Reason:</strong> {{ response.rejection_reason }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Approved Template Responses Section for Risk Officers -->
          <div v-if="userRole === 'risk_officer' && caseTemplateResponses.length > 0" class="form-section">
            <div class="field-group">
              <label>Approved Template Responses</label>
              <div class="template-responses-review">
                <div v-for="response in caseTemplateResponses" :key="response.id" class="template-response-item approved-response">
                  <div class="template-response-header">
                    <h4>{{ response.template_name }}</h4>
                    <span :class="['template-response-status', response.status]">{{ response.status.replace('_', ' ') }}</span>
                  </div>
                  <div class="template-response-meta">
                    <span><strong>Submitted by:</strong> {{ response.assigned_to }}</span>
                    <span><strong>Department:</strong> {{ response.department || 'N/A' }}</span>
                    <span><strong>Submitted on:</strong> {{ new Date(response.created_at).toLocaleString() }}</span>
                    <span v-if="response.approved_by"><strong>Approved by:</strong> {{ response.approved_by }}</span>
                    <span v-if="response.approved_at"><strong>Approved on:</strong> {{ new Date(response.approved_at).toLocaleString() }}</span>
                  </div>
                  <div v-if="response.template_description" class="template-description">{{ response.template_description }}</div>
                  
                  <div class="template-questions-review">
                    <div v-for="question in getTemplateQuestions(response.template_id)" :key="question.id" class="question-review-item">
                      <div class="question-review-header">
                        <span class="question-text">{{ question.question }}</span>
                        <span v-if="question.required" class="required-indicator">*</span>
                      </div>
                      
                      <div class="question-response">
                        <strong>Response:</strong>
                        <span class="response-value">
                          {{ getResponseValue(response.responses, question.id) || 'No response provided' }}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div v-if="response.rejection_reason" class="rejection-reason">
                    <strong>Rejection Reason:</strong> {{ response.rejection_reason }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Supervisor Approval Section -->
          <div class="form-section" v-if="userRole === 'supervisor'">
            <div class="field-group">
              <label>Supervisor Decision</label>
              <div class="input-row">
                <textarea v-model="supervisorComment" :disabled="isReadOnly" placeholder="Please provide your comment" class="compact-textarea"></textarea>
              </div>
              <div class="supervisor-actions">
                <button @click="approveDeptChanges" :disabled="isReadOnly" class="btn-approve">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 6L9 17l-5-5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  Approve Changes
                </button>
                <button @click="rejectDeptChanges" :disabled="isReadOnly" class="btn-reject">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  Reject Changes
                </button>
              </div>
            </div>
          </div>
          
          <!-- Assignment Status for Review Mode - Parallel to Data Uploads -->
          <div v-if="isReviewMode && assignmentStatus.length > 0" class="form-section">
            <div class="field-group">
              <label>Assignment Status</label>
              <div class="assignment-status-section">
                <div class="assignment-list">
                  <div v-for="assignment in assignmentStatus" :key="assignment.assigned_to" class="assignment-item">
                    <div class="assignment-info">
                      <span class="assigned-user">{{ assignment.assigned_to }}</span>
                      <span class="assignment-date">{{ formatDateIST(assignment.assign_date) }}</span>
                      <span v-if="assignment.comment" class="assignment-comment">- {{ assignment.comment }}</span>
                    </div>
                    <div class="assignment-actions">
                      <button 
                        v-if="userRole === 'risk_officer' && !assignment.sent_back" 
                        @click="revokeAssignment(assignment.assigned_to)"
                        class="btn-revoke"
                        :disabled="isAssignmentDisabled"
                      >
                        Revoke Assignment
                      </button>
                      <span v-if="assignment.sent_back" class="sent-back-badge">Sent Back</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="userRole === 'risk_officer' && currentStep === 3" class="step-panel">
        <h3>Final Closure</h3>
        
        <!-- Loading indicator for closure data -->
        <div v-if="isLoadingAdditionalDetails && !isClosureDataLoaded" class="section-loading">
          <div class="loading-spinner"></div>
          <span>Loading closure data...</span>
        </div>
        
        <div class="form-grid">
          <div class="form-section">
            <div class="field-group">
              <label>Closure Remarks</label>
              <div class="input-row">
                <select v-model="action.closureLOV" :disabled="isReadOnly" class="compact-select">
                  <option value="">Select Reason</option>
                  <option v-for="item in closureReasons" :key="item.reason" :value="item.reason">
                    {{ item.reason }}
                  </option>
                </select>
                <textarea v-model="action.closureRemarks" :disabled="isReadOnly" placeholder="Closure remarks" class="compact-textarea"></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="userRole === 'risk_officer' && currentStep === 4" class="step-panel">
        <h3>Confirmation</h3>
        <div v-if="!canAccessConfirmation" class="locked-section-warning" 
             style="background: #fff3cd; border: 2px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 8px; display: flex; align-items: center; gap: 15px;">
          <span class="warning-icon" style="font-size: 24px; color: #b45309;">🔒</span>
          <span class="warning-text" style="color: #b45309; font-size: 16px; font-weight: 600;">
            <strong style="color: #b45309; font-weight: 700;">Section Locked:</strong> Please complete the closure section first before accessing confirmation.
          </span>
        </div>
        <div class="confirmation-grid" :class="{ 'locked-section': !canAccessConfirmation }">
          <div class="confirm-section">
            <div class="confirm-row">
              <label>Confirmed Mule</label>
              <div class="radio-group">
                <label><input type="radio" v-model="action.confirmedMule" value="Yes" name="confirmedMule" :disabled="isReadOnly || !canAccessConfirmation" /> Yes</label>
                <label><input type="radio" v-model="action.confirmedMule" value="No" name="confirmedMule" :disabled="isReadOnly || !canAccessConfirmation" /> No</label>
              </div>
            </div>
              <div class="confirm-row">
                <label>Funds Saved</label>
                <input
                  type="number"
                  v-model="action.fundsSaved"
                  :disabled="isReadOnly || !canAccessConfirmation"
                  class="compact-input"
                  placeholder="Amount (INR)"
                  min="0"
                  step="0.01"
                />
              </div>
          </div>
          <div class="confirm-section">
            <div class="confirm-row">
              <label>Digital Channel Blocked</label>
              <div class="radio-group">
                <label><input type="radio" v-model="action.digitalBlocked" value="Yes" name="digitalBlocked" :disabled="isReadOnly || !canAccessConfirmation" /> Yes</label>
                <label><input type="radio" v-model="action.digitalBlocked" value="No" name="digitalBlocked" :disabled="isReadOnly || !canAccessConfirmation" /> No</label>
              </div>
            </div>
            <div class="confirm-row">
              <label>Account Blocked</label>
              <div class="radio-group">
                <label><input type="radio" v-model="action.accountBlocked" value="Yes" name="accountBlocked" :disabled="isReadOnly || !canAccessConfirmation" /> Yes</label>
                <label><input type="radio" v-model="action.accountBlocked" value="No" name="accountBlocked" :disabled="isReadOnly || !canAccessConfirmation" /> No</label>
              </div>
            </div>
          </div>
        </div>
      </div>
              <div v-if="currentStep === 2">
        <div v-if="previouslyUploadedFiles.length > 0" class="uploaded-files-list improved-upload-list">
          <h4>Previously Uploaded Files</h4>
          <div class="previously-uploaded-files">
            <div v-for="file in previouslyUploadedFiles" :key="file.id" class="uploaded-file-item">
              <a :href="`/api/download/${file.id}`" target="_blank" class="file-link">
                <span class="download-icon">⬇️</span> {{ file.original_filename }}
              </a>
              <div class="file-meta-small">
                Uploaded: {{ new Date(file.uploaded_at).toLocaleString() }}
                <span v-if="file.comment">- {{ file.comment }}</span>
                <span v-if="userRole === 'supervisor' && (file.approval_status || 'approved')" :class="['status-chip', (file.approval_status || 'approved') === 'approved' ? 'approved' : ((file.approval_status || '') === 'pending_approval' ? 'pending' : 'rejected')]">
                  {{ (file.approval_status || 'approved') === 'approved' ? 'Approved' : ((file.approval_status || '') === 'pending_approval' ? 'Pending approval' : 'Rejected') }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="uploaded-files-list improved-upload-list">
          <div class="empty-state">
            <div class="icon">📄</div>
            <div class="title">No documents uploaded</div>
            <div class="hint">Upload supporting documents in Analysis to see them listed here.</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="caseLogs.length > 0" class="case-logs-section">
      <h4>Case Activity Log</h4>
      <ul class="case-log-list">
        <li v-for="log in limitedCaseLogs" :key="log.id" class="case-log-item">
          <span class="log-time">{{ new Date(log.created_at).toLocaleString() }}</span>
          <span class="log-user">{{ log.user_name }}</span>
          <span class="log-action">[{{ log.action }}]</span>
          <span class="log-details">{{ log.details }}</span>
        </li>
      </ul>
    </div>
    <div v-else class="case-logs-section">
      <div class="empty-state">
        <div class="icon">📝</div>
        <div class="title">No activity yet</div>
        <div class="hint">Actions and updates will appear here.</div>
      </div>
    </div>

    <div class="bottom-navigation">
      <div class="nav-buttons">
        <button
          @click="previousStep"
          :disabled="currentStep === 1 || isReadOnly"
          class="btn-nav btn-prev"
        >
          Previous
        </button>
        <button
          @click="nextStep"
          v-if="currentStep < steps.length"
          class="btn-nav btn-next"
        >
          Next
        </button>
      </div>
      <div class="action-buttons">
        <!-- Only show Save button for non-others users -->
        <button v-if="!isReadOnly && !isReviewMode && userRole !== 'others'" @click="saveAction" class="btn-save">Save</button>
        <button v-if="!isReadOnly && userRole === 'risk_officer' && !isReviewMode && showSubmitButton" @click="submitAction" class="btn-submit">Submit</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { API_ENDPOINTS } from '@/config/api';

const route = useRoute();
const router = useRouter();

// Check if we're in review mode
const isReviewMode = computed(() => route.query.review === 'true');

// Helper function to format date in IST
const formatDateIST = (assignDate) => {
  if (!assignDate) return '—';
  
  try {
    const date = new Date(assignDate);
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
};

// --- State Management ---
const isLoading = ref(true);
const fetchError = ref(null);
const currentStep = ref(1);

// --- Dropdown Data ---
const analysisReasons = ref([]);
const departments = ref([]);
const closureReasons = ref([]);

// Get user role from localStorage immediately to avoid UI flicker
const userRole = ref(localStorage.getItem('user_type') || 'others');
const status = ref('New'); // Track case status
const latestActionStatus = ref('');
const assignmentStatus = ref([]); // Track assignment status for review mode

// Fetch user role on mount (from lightweight /api/user/profile)
const fetchUserRole = async () => {
  // First try localStorage (faster, no API call needed)
  const storedRole = localStorage.getItem('user_type');
  if (storedRole) {
    userRole.value = storedRole;
    return;
  }
  
  // Fallback to lightweight user profile API (much faster than new-case-list)
  const token = localStorage.getItem('jwt');
  const response = await axios.get('/api/user/profile', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (response.data && response.data.logged_in_user_type) {
    userRole.value = response.data.logged_in_user_type;
    // Store in localStorage for future use
    localStorage.setItem('user_type', response.data.logged_in_user_type);
  }
};

// Compute steps based on userRole and review mode (no flicker)
const steps = computed(() => {
  if (userRole.value === 'others' || userRole.value === 'supervisor' || isReviewMode.value) {
    return [
      { title: 'Alert Details' },
      { title: 'Analysis' }
    ];
  }
  return [
    { title: 'Alert Details' },
    { title: 'Analysis' },
    { title: 'Closure' },
    { title: 'Confirmation' }
  ];
});

// Watch for step changes to adjust currentStep if needed
watch([userRole, isReviewMode], ([role, reviewMode]) => {
  if ((role === 'others' || role === 'supervisor' || reviewMode) && currentStep.value > 2) {
    currentStep.value = 2;
  }
}, { immediate: true });

// --- Data Models ---
const i4cDetails = ref({});
const bankDetails = ref({});
const action = ref({
  analysisLOV: '',
  analysisUpdate: '',
  // dataUploads is an array of objects for dynamic sections
  dataUploads: [{ id: Date.now(), comment: '', files: [], isDragOver: false }],
  reviews: [{ id: Date.now(), selectedDepartment: '', userId: '', text: '', userList: [], templateId: '' }],
  closureLOV: '',
  closureRemarks: '',
  confirmedMule: 'No',
  fundsSaved: null,
  digitalBlocked: 'No',
  accountBlocked: 'No',
});

// --- Template Related Data ---
const availableTemplates = ref([]);
const assignedTemplate = ref(null);
const templateResponses = ref({});
const templateFiles = ref({});
const caseTemplateResponses = ref([]); // For displaying submitted template responses
const mergedFromDepartments = ref([]); // For showing which departments have made changes

// Computed property to filter only approved template responses for risk officers
const approvedTemplateResponses = computed(() => {
  if (userRole.value === 'risk_officer') {
    return caseTemplateResponses.value.filter(response => response.status === 'approved');
  }
  return caseTemplateResponses.value;
});

// --- Dynamic Row Logic (Reviews) ---
const addReviewCommentRow = () => {
  action.value.reviews.push({
    id: Date.now(),
    selectedDepartment: '',
    userId: '',
    text: '',
    userList: [],
    templateId: ''
  });
};

const removeReviewCommentRow = (index) => {
  if (action.value.reviews.length > 1) {
    action.value.reviews.splice(index, 1);
  }
};

const handleDepartmentChange = async (review) => {
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

// --- Dynamic Upload Block Logic ---
const addDataUploadBlock = () => {
  action.value.dataUploads.push({
    id: Date.now(),
    comment: '',
    files: [],
    isDragOver: false
  });
};
const removeDataUploadBlock = (blockIndex) => {
  if (action.value.dataUploads.length > 1) {
    action.value.dataUploads.splice(blockIndex, 1);
  }
};

// --- File Upload Logic ---
const fileInputRefs = ref([]); // Use an array of refs for file inputs

const getFileIcon = (type) => {
  if (type.startsWith('image/')) return '📸';
  if (type.startsWith('application/pdf')) return '📄';
  if (type.startsWith('application/msword') || type.startsWith('application/vnd.openxmlformats-officedocument.wordprocessingml.document')) return '📝';
  if (type.startsWith('application/vnd.ms-excel') || type.startsWith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) return '📊';
  return '📁';
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const triggerFileInput = (blockIndex) => {
  if(fileInputRefs.value[blockIndex] && !isReadOnly.value) {
    fileInputRefs.value[blockIndex].click();
  }
};

const addFiles = (files, blockIndex) => {
  const uploadBlock = action.value.dataUploads[blockIndex];
  files.forEach(file => {
    uploadBlock.files.push({ file, displayName: file.name, newName: file.name, size: file.size, type: file.type, isRenaming: false });
  });
};

const onFileSelect = (event, blockIndex) => {
  if (!isReadOnly.value) {
    addFiles(Array.from(event.target.files), blockIndex);
  }
  event.target.value = '';
};

const onDragOver = (blockIndex) => action.value.dataUploads[blockIndex].isDragOver = true;
const onDragLeave = (blockIndex) => action.value.dataUploads[blockIndex].isDragOver = false;
const onFileDrop = (event, blockIndex) => {
  action.value.dataUploads[blockIndex].isDragOver = false;
  if (!isReadOnly.value) {
    addFiles(Array.from(event.dataTransfer.files), blockIndex);
  }
};

const startRename = (blockIndex, fileIndex) => action.value.dataUploads[blockIndex].files[fileIndex].isRenaming = true;
const saveFileName = (blockIndex, fileIndex) => {
  const file = action.value.dataUploads[blockIndex].files[fileIndex];
  file.displayName = file.newName;
  file.isRenaming = false;
};
const cancelRename = (blockIndex, fileIndex) => {
  const file = action.value.dataUploads[blockIndex].files[fileIndex];
  file.newName = file.displayName;
  file.isRenaming = false;
};
const removeFile = (blockIndex, fileIndex) => {
  if (!isReadOnly.value) {
    action.value.dataUploads[blockIndex].files.splice(fileIndex, 1);
  }
};


// --- API Integration ---
const fetchAnalysisReasons = async () => {
  try {
    const response = await axios.get('/api/investigation-review');
    if (response.data) analysisReasons.value = response.data;
  } catch (err) { console.error("Failed to fetch analysis reasons:", err); }
};

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

// Section-based loading flags
const isAnalysisDataLoaded = ref(false);
const isClosureDataLoaded = ref(false);
const isLoadingAdditionalDetails = ref(false);

// Load analysis section data when user navigates to step 2
const loadAnalysisData = async () => {
  if (isAnalysisDataLoaded.value) return;
  
  isLoadingAdditionalDetails.value = true;
  try {
    // Load basic analysis data
    await Promise.all([
      fetchAnalysisReasons(),
      fetchDepartments(),
      fetchAvailableTemplates()
    ]);
    
    // Load template-related data based on user role
    if (userRole.value === 'others') {
      await fetchAssignedTemplate();
      await fetchCaseTemplateResponses();
    }
    
    if (userRole.value === 'supervisor' || userRole.value === 'risk_officer') {
      await fetchCaseTemplateResponses();
    }
    
    // Load send-back analysis reasons for Others
    try {
      const r = await axios.get(API_ENDPOINTS.SEND_BACK_ANALYSIS);
      sendBackReasons.value = Array.isArray(r.data) ? r.data : [];
    } catch (e) { 
      console.error('Failed to load send-back reasons:', e); 
    }
    
    // Load latest saved action data and files (moved from onMounted for better performance)
    try {
      const caseId = parseInt(route.params.case_id);
      const token = localStorage.getItem('jwt');
      const resp = await axios.get('/api/case-action/latest', {
        params: { case_id: caseId },
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (resp.data && resp.data.merged_action_data && typeof resp.data.merged_action_data === 'object') {
        Object.assign(action.value, resp.data.merged_action_data);
      } else if (resp.data && resp.data.action_data && resp.data.action_data.action_data) {
        Object.assign(action.value, resp.data.action_data.action_data);
      }
      
      if (resp.data && resp.data.files) {
        previouslyUploadedFiles.value = resp.data.files;
      }
      
      if (resp.data && resp.data.action_data) {
        latestActionStatus.value = resp.data.action_data.status || '';
      }
      
      if (resp.data && resp.data.merged_from_departments) {
        mergedFromDepartments.value = resp.data.merged_from_departments;
      }
      
      // After loading action data, inject existing files into Data Uploads
      if (previouslyUploadedFiles.value && previouslyUploadedFiles.value.length > 0) {
        injectExistingFilesIntoDataUploads(previouslyUploadedFiles.value);
      }
    } catch (e) {
      console.error('Failed to load latest case action data:', e);
    }
    
    isAnalysisDataLoaded.value = true;
  } catch (error) {
    console.error('Error loading analysis data:', error);
  } finally {
    isLoadingAdditionalDetails.value = false;
  }
};

// Load closure section data when user navigates to step 3
const loadClosureData = async () => {
  if (isClosureDataLoaded.value) return;
  
  isLoadingAdditionalDetails.value = true;
  try {
    await fetchClosureReasons();
    isClosureDataLoaded.value = true;
  } catch (error) {
    console.error('Error loading closure data:', error);
  } finally {
    isLoadingAdditionalDetails.value = false;
  }
};

const caseAckNo = ref('');

const fetchCaseDetails = async () => {
  const caseId = parseInt(route.params.case_id);
  const token = localStorage.getItem('jwt');
  if (!token) throw new Error('No authentication token found');

  const response = await axios.get(`/api/combined-case-data/${caseId}`, { headers: { 'Authorization': `Bearer ${token}` } });
  
  if (response.data) {
    const { i4c_data = null, customer_details = null, account_details, acc_num, action_details, status: caseStatus, source_ack_no } = response.data;
    caseAckNo.value = source_ack_no || '';
    status.value = caseStatus || 'New'; // Update the status ref
    i4cDetails.value = { 
      name: i4c_data?.customer_name || 'N/A', 
      mobile: i4c_data?.mobile || 'N/A', 
      email: i4c_data?.email || 'N/A', 
      bankAc: i4c_data?.account_number || 'N/A' 
    };
    bankDetails.value = { 
      name: `${customer_details?.fname || ''} ${customer_details?.mname || ''} ${customer_details?.lname || ''}`.trim() || 'N/A', 
      mobile: customer_details?.mobile || 'N/A', 
      email: customer_details?.email || 'N/A', 
      customerId: customer_details?.cust_id || 'N/A', 
      bankAc: acc_num || 'N/A', 
      acStatus: account_details?.acc_status || 'N/A', 
      pan: customer_details?.pan || 'N/A', 
      aadhaar: customer_details?.nat_id || 'N/A', 
      productCode: account_details?.productCode || 'N/A', 
      aqb: account_details?.aqb || 'N/A', 
      availBal: account_details?.availBal || 'N/A', 
      relValue: customer_details?.rel_value || 'N/A', 
      mobVintage: customer_details?.mob || 'N/A' 
    };
    if (action_details) {
      Object.assign(action.value, action_details);
       // Ensure dataUploads is an array, if loading saved data
      if (!Array.isArray(action.value.dataUploads) || action.value.dataUploads.length === 0) {
        action.value.dataUploads = [{ id: Date.now(), comment: '', files: [], isDragOver: false }];
      }
      // Ensure reviews is an array, if loading saved data
      if (!Array.isArray(action.value.reviews) || action.value.reviews.length === 0) {
        action.value.reviews = [{ id: Date.now(), selectedDepartment: '', userId: '', text: '', userList: [], templateId: '' }];
      }
    }
    // Set isReadOnly based on real case status (only closed cases should be read-only)
    if (typeof status.value === 'string' && status.value.trim().toLowerCase() === 'closed') {
      isReadOnly.value = true;
    } else {
      isReadOnly.value = false;
    }
  } else { 
    throw new Error('Received no data for this case.'); 
  }
};

const previouslyUploadedFiles = ref([]);
const isReadOnly = ref(false);
const isAssignmentDisabled = computed(() => status.value === 'Reopened' || status.value === 'Closed'); // Assignment is disabled for reopened and closed cases
const caseLogs = ref([]);

// --- Workflow Logic ---
const hasClosureActivity = computed(() => {
  return !!(action.value.closureLOV || action.value.closureRemarks?.trim());
});

const canAccessConfirmation = computed(() => {
  return hasClosureActivity.value;
});

const showSubmitButton = computed(() => {
  return userRole.value === 'risk_officer' && hasClosureActivity.value;
});

// Send-back analysis reasons
const sendBackReasons = ref([]);
const sendBackReasonId = ref('');
// Show only the latest 5 logs on the action page to avoid overflow
const limitedCaseLogs = computed(() => {
  if (!Array.isArray(caseLogs.value)) return [];
  // logs come in ascending order per API; slice last 5
  const last = caseLogs.value.slice(-5);
  return last;
});

const sendBackComment = ref('');
const hasUnsavedChanges = ref(false);
const supervisorComment = ref('');

// Mark as unsaved on any change
watch(action, () => { hasUnsavedChanges.value = true; }, { deep: true });

  // Inject existing approved/base files into Data Uploads blocks for display
  const injectExistingFilesIntoDataUploads = (filesArray) => {
    try {
      if (!Array.isArray(filesArray)) return;
      if (!Array.isArray(action.value.dataUploads)) {
        action.value.dataUploads = [{ id: Date.now(), comment: '', files: [], isDragOver: false }];
      }
      // Build a set of existing filenames in current blocks to avoid duplicates
      const existingNames = new Set();
      action.value.dataUploads.forEach(block => {
        if (Array.isArray(block.files)) {
          block.files.forEach(f => {
            if (f && typeof f.displayName === 'string') {
              existingNames.add(f.displayName.trim().toLowerCase());
            }
          });
        }
      });
      // Group incoming files by comment to form logical blocks
      const groupedByComment = new Map();
      filesArray.forEach(f => {
        // Only include base (NULL) and approved docs; pending/rejected are filtered server-side already
        const key = (f.comment || '').trim();
        if (!groupedByComment.has(key)) groupedByComment.set(key, []);
        const displayName = f.original_filename || '';
        if (displayName && !existingNames.has(displayName.trim().toLowerCase())) {
          groupedByComment.get(key).push({
            displayName,
            size: 0,
            type: f.file_mime_type || 'application/octet-stream',
            isRenaming: false,
            isExisting: true,
          });
          existingNames.add(displayName.trim().toLowerCase());
        }
      });
      // Append grouped blocks
      groupedByComment.forEach((files, comment) => {
        if (files.length === 0) return;
        action.value.dataUploads.push({ id: `existing-${Date.now()}-${Math.random()}`, comment, files, isDragOver: false });
      });
    } catch (e) {
      console.error('Failed to inject existing files into Data Uploads:', e);
    }
  };

const sendBackCase = async () => {
  // For "others" users, automatically trigger the Save functionality (files, data uploads, etc.) before sending back
  if (userRole.value === 'others' && hasUnsavedChanges.value) {
    try {
      // Auto-save all changes (files, data uploads, etc.) before sending back
      await saveAction();
      window.showNotification('info', 'Changes Auto-Saved', 'All changes automatically saved before sending back.');
    } catch (err) {
      window.showNotification('error', 'Auto-Save Failed', 'Failed to auto-save changes. Please try again.');
      return;
    }
  }
  
  // For non-others users, check if there are unsaved changes
  if (userRole.value !== 'others' && hasUnsavedChanges.value) {
    window.showNotification('warning', 'Unsaved Changes', 'Please click on Save before Send Back.');
    return;
  }
  
  if (!sendBackReasonId.value) {
    window.showNotification('warning', 'Reason Required', 'Please select a send-back reason.');
    return;
  }
  if (!sendBackComment.value.trim()) {
    window.showNotification('warning', 'Missing Comment', 'Please enter a comment before sending back.');
    return;
  }
  const ackNo = caseAckNo.value;
  const token = localStorage.getItem('jwt');
  try {
    await axios.post(`/api/case/${ackNo}/send-back-optimized`, { comment: sendBackComment.value, reason_id: sendBackReasonId.value }, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    window.showNotification('success', 'Case Sent Back', 'Case sent back successfully!');
    sendBackComment.value = '';
    // Refresh logs and assignment
    const caseId = parseInt(route.params.case_id);
    const logsResp = await axios.get(`/api/case/${caseId}/logs`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    caseLogs.value = logsResp.data.logs || [];
    await fetchUserRole();
    // Redirect to case details page after successful send back
    window.location.href = `/case-details`;
  } catch (err) {
    window.showNotification('error', 'Send Back Failed', 'Failed to send back case.');
    console.error('Send back error:', err);
  }
};

const approveDeptChanges = async () => {
  if (!supervisorComment.value || !supervisorComment.value.trim()) {
    window.showNotification('warning', 'Comment Required', 'Please provide a comment before approving changes.');
    return;
  }
  
  const ackNo = caseAckNo.value;
  const token = localStorage.getItem('jwt');
  try {
    await axios.post(`/api/case/${ackNo}/approve-dept`, { approval_comment: supervisorComment.value }, { headers: { 'Authorization': `Bearer ${token}` } });
    window.showNotification('success', 'Approved', 'Department changes approved and routed back to Risk Officer.');
    window.location.href = `/supervisor-worklist`;
  } catch (err) {
    window.showNotification('error', 'Approval Failed', 'Failed to approve changes.');
    console.error('Approve error:', err);
  }
};

const rejectDeptChanges = async () => {
  if (!supervisorComment.value || !supervisorComment.value.trim()) {
    window.showNotification('warning', 'Comment Required', 'Please provide a comment before rejecting changes.');
    return;
  }
  
  const ackNo = caseAckNo.value;
  const token = localStorage.getItem('jwt');
  try {
    await axios.post(`/api/case/${ackNo}/reject-dept`, { rejection_reason: supervisorComment.value }, { headers: { 'Authorization': `Bearer ${token}` } });
    window.showNotification('success', 'Rejected', 'Department changes rejected and routed back to Risk Officer.');
    window.location.href = `/supervisor-worklist`;
  } catch (err) {
    window.showNotification('error', 'Rejection Failed', 'Failed to reject changes.');
    console.error('Reject error:', err);
  }
};

const goToStep = async (step) => {
  if (isLoading.value) return;
  if ((userRole.value === 'others' || userRole.value === 'supervisor') && step > 2) return;
  
  // Prevent direct access to confirmation step (step 4) without closure activity
  if (step === 4 && !canAccessConfirmation.value) {
    if (window.showNotification) {
      window.showNotification('Please complete the closure section before accessing confirmation.', 'warning');
    }
    return;
  }
  
  currentStep.value = step;
  
  // Load data based on the step user is navigating to
  if (step === 2) {
    // Load analysis data when user goes to Analysis & Investigation
    await loadAnalysisData();
  } else if (step === 3) {
    // Load closure data when user goes to Closure & Confirmation
    await loadClosureData();
  }
};
const nextStep = async () => {
  if (userRole.value === 'others' || userRole.value === 'supervisor') {
    if (currentStep.value < 2) {
      currentStep.value++;
      // Load analysis data when moving to step 2
      if (currentStep.value === 2) {
        await loadAnalysisData();
      }
    }
  } else {
    // Prevent access to confirmation step (step 4) without closure activity
    if (currentStep.value === 3 && !canAccessConfirmation.value) {
      // Show notification that closure section must be completed first
      if (window.showNotification) {
        window.showNotification('Please complete the closure section before proceeding to confirmation.', 'warning');
      }
      return;
    }
    
    if (currentStep.value < steps.value.length) {
      currentStep.value++;
      // Load data based on the step user is moving to
      if (currentStep.value === 2) {
        await loadAnalysisData();
      } else if (currentStep.value === 3) {
        await loadClosureData();
      }
    }
  }
};
const previousStep = () => {
  if (currentStep.value > 1) currentStep.value--;
};

const fetchAssignmentStatus = async () => {
  if (!isReviewMode.value) return;
  
  const caseId = parseInt(route.params.case_id);
  const token = localStorage.getItem('jwt');
  try {
    const response = await axios.get(`/api/case/${caseId}/assignments`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    assignmentStatus.value = response.data.assignments || [];
  } catch (err) {
    console.error('Failed to fetch assignment status:', err);
  }
};

const revokeAssignment = async (assignedTo) => {
  const ackNo = caseAckNo.value;
  const token = localStorage.getItem('jwt');
  try {
    await axios.post(`/api/case/${ackNo}/revoke-assignment`, 
      { assigned_to_employee: assignedTo },
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    window.showNotification('success', 'Assignment Revoked', `Assignment revoked from ${assignedTo} successfully!`);
    await fetchAssignmentStatus();
    // Refresh logs
    const caseId = parseInt(route.params.case_id);
    const logsResp = await axios.get(`/api/case/${caseId}/logs`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    caseLogs.value = logsResp.data.logs || [];
  } catch (err) {
    window.showNotification('error', 'Revoke Failed', 'Failed to revoke assignment.');
    console.error('Revoke error:', err);
  }
};

onMounted(async () => {
  isLoading.value = true;
  fetchError.value = null;
  try {
    // Fetch latest saved action data and files
    const caseId = parseInt(route.params.case_id);
    const token = localStorage.getItem('jwt');
    const resp = await axios.get('/api/case-action/latest', {
      params: { case_id: caseId },
      headers: { 'Authorization': `Bearer ${token}` }
    });
  if (resp.data && resp.data.merged_action_data && typeof resp.data.merged_action_data === 'object') {
    Object.assign(action.value, resp.data.merged_action_data);
  } else if (resp.data && resp.data.action_data && resp.data.action_data.action_data) {
    Object.assign(action.value, resp.data.action_data.action_data);
  }
    if (resp.data && resp.data.files) {
      previouslyUploadedFiles.value = resp.data.files;
    }
  if (resp.data && resp.data.action_data) {
    latestActionStatus.value = resp.data.action_data.status || '';
  }
    if (resp.data && resp.data.merged_from_departments) {
      mergedFromDepartments.value = resp.data.merged_from_departments;
    }
    // Fetch logs
    const logsResp = await axios.get(`/api/case/${caseId}/logs`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    caseLogs.value = logsResp.data.logs || [];
    await fetchCaseDetails();
    // After case details may reset action.dataUploads, inject existing files into Data Uploads
    if (previouslyUploadedFiles.value && previouslyUploadedFiles.value.length > 0) {
      injectExistingFilesIntoDataUploads(previouslyUploadedFiles.value);
    }
    await fetchUserRole();
    await fetchAssignmentStatus();
    // Note: Analysis and closure data will be loaded when user navigates to those sections
    // Note: Template responses, send-back analysis, and case action data will be loaded when user navigates to analysis section
  } catch (error) {
    console.error('Error during component mount:', error);
    fetchError.value = 'Failed to load case details. Please try again later.';
  } finally {
    isLoading.value = false;
  }
});

// --- Action Buttons ---
const saveAction = async () => {
  const caseId = parseInt(route.params.case_id);
  // You may need to get case_type from route or data; here we use a placeholder
  const caseType = bankDetails.value.caseType || 'BM'; // Adjust as needed
  const formData = new FormData();
  formData.append('case_id', caseId);
  formData.append('case_type', caseType);
  formData.append('action_data', JSON.stringify(action.value));

  // Collect all files from all upload blocks
  action.value.dataUploads.forEach((block) => {
    if (block.files && block.files.length > 0) {
      block.files.forEach((fileObj) => {
        if (fileObj.file && (fileObj.file instanceof File || fileObj.file instanceof Blob)) {
          formData.append('files', fileObj.file, fileObj.displayName || fileObj.file.name);
        }
      });
    }
  });

  try {
    const token = localStorage.getItem('jwt');
    await axios.post('/api/case-action/save-optimized', formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data',
      },
    });
    window.showNotification('success', 'Action Saved', 'Case action saved successfully!');
    hasUnsavedChanges.value = false;
  } catch (err) {
    window.showNotification('error', 'Save Failed', 'Failed to save case action.');
    console.error('Failed to save case action:', err);
  }
};

const submitAction = async () => {
  if (hasUnsavedChanges.value) {
    window.showNotification('warning', 'Unsaved Changes', 'Please click on Save before Submit.');
    return;
  }
  
  // Require Funds Saved for risk officers on submit (closing)
  if (userRole.value !== 'others') {
    const amount = Number(action.value.fundsSaved);
    if (!Number.isFinite(amount) || amount < 0) {
      window.showNotification('warning', 'Funds Saved Required', 'Please enter a valid non-negative amount for Funds Saved before submitting.');
      return;
    }
  }
  const caseId = parseInt(route.params.case_id);
  try {
    const token = localStorage.getItem('jwt');
    await axios.post('/api/case/submit-optimized',
      { case_id: caseId },
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    window.showNotification('success', 'Case Submitted', 'Case submitted successfully!');
    // Redirect to case details page after successful submit
    window.location.href = `/case-details`;
  } catch (err) {
    window.showNotification('error', 'Submit Failed', 'Failed to submit case.');
    console.error('Failed to submit case:', err);
  }
};

const assignCase = async () => {
  if (hasUnsavedChanges.value) {
    window.showNotification('warning', 'Unsaved Changes', 'Please click on Save before Assign.');
    return;
  }
  
  // Validate that all assignments have users selected and comments provided
  const validAssignments = action.value.reviews.filter(review => review.userId && review.userId.trim());
  if (validAssignments.length === 0) {
    window.showNotification('warning', 'No Users Selected', 'Please select at least one user to assign.');
    return;
  }
  
  // Check if all valid assignments have comments
  const assignmentsWithoutComments = validAssignments.filter(review => !review.text || !review.text.trim());
  if (assignmentsWithoutComments.length > 0) {
    window.showNotification('warning', 'Comments Required', 'Please provide comments for all assignments before proceeding.');
    return;
  }
  
  const token = localStorage.getItem('jwt');
  const ackNo = caseAckNo.value;
  if (!ackNo) {
    window.showNotification('error', 'Invalid Case', 'No valid case ACK No found.');
    return;
  }
  
  try {
    // Assign to multiple users
    const assignmentPromises = validAssignments.map(async (review) => {
      const assignmentData = {
        assigned_to_employee: review.userId,
        comment: review.text || '',
        template_id: review.templateId || null
      };
      
      return axios.post(`/api/case/${ackNo}/assign-optimized`, assignmentData, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
    });
    
    await Promise.all(assignmentPromises);
    window.showNotification('success', 'Case Assigned', `Case assigned to ${validAssignments.length} user(s) successfully!`);
    // Redirect to case details page after successful assignment
    window.location.href = `/case-details`;
  } catch (err) {
    window.showNotification('error', 'Assignment Failed', 'Failed to assign case.');
    console.error('Assignment error:', err);
  }
};

// --- Template Methods ---
const fetchAvailableTemplates = async () => {
  try {
    const token = localStorage.getItem('jwt');
    const response = await axios.get('/api/templates', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (response.data && response.data.success) {
      availableTemplates.value = response.data.templates;
    }
  } catch (err) {
    console.error("Failed to fetch templates:", err);
  }
};

const getTemplateDescription = (templateId) => {
  const template = availableTemplates.value.find(t => t.id === templateId);
  return template ? template.description : '';
};

const fetchAssignedTemplate = async () => {
  if (userRole.value !== 'others') {
    return;
  }
  
  try {
    const caseId = parseInt(route.params.case_id);
    const token = localStorage.getItem('jwt');
    const currentUsername = localStorage.getItem('username'); // Get actual username
    
    if (!currentUsername) {
      console.error("Username not found in localStorage");
      return;
    }
    
    // Use the new my-assignment endpoint instead of assignments
    const response = await axios.get(`/api/case/${caseId}/my-assignment`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.data && response.data.assignment) {
      const myAssignment = response.data.assignment;
      
      if (myAssignment && myAssignment.template_id) {
        const templateResponse = await axios.get(`/api/templates/${myAssignment.template_id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (templateResponse.data && templateResponse.data.success) {
          assignedTemplate.value = templateResponse.data.template;
          
          // Initialize template responses
          assignedTemplate.value.questions.forEach(q => {
            if (!templateResponses.value.hasOwnProperty(q.id)) {
              templateResponses.value[q.id] = '';
            }
          });
          

        }
      }
    }
  } catch (err) {
    console.error("Failed to fetch assigned template:", err);
  }
};

const handleTemplateFileUpload = (event, questionId) => {
  const files = Array.from(event.target.files);
  if (files.length > 0) {
    // Store in templateFiles for backward compatibility (only first file)
    templateFiles.value[questionId] = files[0];
    
    // Automatically add to data uploads section with question identification
    if (assignedTemplate.value && assignedTemplate.value.questions) {
      const question = assignedTemplate.value.questions.find(q => q.id === questionId);
      if (question) {
        // Create a meaningful comment identifying the template question
        const questionComment = `Template: ${assignedTemplate.value.name} - ${question.question}`;
        
        // Find if there's already a data upload block with this comment
        let existingBlock = action.value.dataUploads.find(block => 
          block.comment === questionComment
        );
        
        if (existingBlock) {
          // Add files to existing block
          files.forEach(file => {
            existingBlock.files.push({
              file: file,
              displayName: file.name,
              newName: file.name,
              size: file.size,
              type: file.type,
              isRenaming: false
            });
          });
        } else {
          // Create new data upload block
          const newFiles = files.map(file => ({
            file: file,
            displayName: file.name,
            newName: file.name,
            size: file.size,
            type: file.type,
            isRenaming: false
          }));
          
          action.value.dataUploads.push({
            id: `template-${Date.now()}-${Math.random()}`,
            comment: questionComment,
            files: newFiles,
            isDragOver: false
          });
        }
        
        // Show success notification
        if (files.length === 1) {
          window.showNotification('success', 'File Added', `File "${files[0].name}" added to data uploads section.`);
        } else {
          window.showNotification('success', 'Files Added', `${files.length} files added to data uploads section.`);
        }
      }
    }
  }
};

const saveTemplateResponses = async () => {
  try {
    const caseId = parseInt(route.params.case_id);
    const token = localStorage.getItem('jwt');
    
    // Get the actual department name from user profile
    let userDepartment = 'others';
    try {
      const userResponse = await axios.get('/api/user/department', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (userResponse.data && userResponse.data.success && userResponse.data.department) {
        userDepartment = userResponse.data.department;
      }
    } catch (err) {
      console.error("Failed to get user department, using default:", err);
    }
    
    // Prepare responses data
    const responsesData = {
      case_id: caseId,
      template_id: assignedTemplate.value.id,
      responses: templateResponses.value,
      department: userDepartment
    };
    
    const response = await axios.post('/api/template-responses', responsesData, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.data && response.data.success) {
      window.showNotification('success', 'Template Responses Saved', 'Your template responses have been saved successfully!');
      
      // Clear template files since they're now in data uploads
      templateFiles.value = {};
      
      // Refresh template responses for all users
      await fetchCaseTemplateResponses();
    }
  } catch (err) {
    window.showNotification('error', 'Save Failed', 'Failed to save template responses.');
    console.error('Failed to save template responses:', err);
  }
};

const fetchCaseTemplateResponses = async () => {
  try {
    const caseId = parseInt(route.params.case_id);
    const token = localStorage.getItem('jwt');
    const response = await axios.get(`/api/case/${caseId}/template-responses`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.data && response.data.success) {
      caseTemplateResponses.value = response.data.responses;
      
      // For "others" users, restore their own saved responses into the template form
      if (userRole.value === 'others') {
        const currentUser = localStorage.getItem('username');
        const userResponses = response.data.responses.find(r => r.assigned_to === currentUser);
        if (userResponses && userResponses.responses) {
          // Restore saved template responses
          Object.assign(templateResponses.value, userResponses.responses);
        }
      }
    }
  } catch (err) {
    console.error("Failed to fetch template responses:", err);
  }
};

// Helper function to get template questions by template ID
const getTemplateQuestions = (templateId) => {
  const template = availableTemplates.value.find(t => t.id === templateId);
  return template ? template.questions : [];
};

// Helper function to get response value for a question
const getResponseValue = (responses, questionId) => {
  if (!responses || typeof responses !== 'object') return '';
  return responses[questionId] || '';
};

// Helper function to get files uploaded for a specific template question
const getTemplateQuestionFiles = (questionId) => {
  if (!assignedTemplate.value || !assignedTemplate.value.questions) return [];
  
  const question = assignedTemplate.value.questions.find(q => q.id === questionId);
  if (!question) return [];
  
  // Look for files in data uploads that match this question
  const questionComment = `Template: ${assignedTemplate.value.name} - ${question.question}`;
  const uploadBlock = action.value.dataUploads.find(block => block.comment === questionComment);
  
  return uploadBlock ? uploadBlock.files : [];
};
</script>

<style scoped>
/* Main Container */
.pma-container {
  height: 100vh;
  overflow: hidden;
  margin-left: 0px;
  padding: 16px;
  background: #f8f9fa;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

/* Progress Steps Header */
.steps-header {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.steps-container {
  display: flex;
  justify-content: space-between;
  max-width: 800px;
  margin: 0 auto;
}
.step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  flex: 1;
  justify-content: center;
}
.step:hover {
  background: #f8f9fa;
}
.step.active {
  background: #0d6efd;
  color: white;
}
.step.completed {
  background: #28a745;
  color: white;
}
.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}
.step.active .step-number, .step.completed .step-number {
  background: rgba(255,255,255,0.3);
}
.step-title {
  font-size: 14px;
  font-weight: 500;
}

/* Step Content Panel */
.step-content {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow-y: auto;
  max-height: calc(100vh - 180px);
}
.step-panel h3 {
  margin: 0 0 20px 0;
  color: #1a1a1a;
  font-size: 20px;
  font-weight: 600;
  padding-bottom: 12px;
  border-bottom: 2px solid #e9ecef;
}

/* Loading and Error Indicators */
.loading-indicator, .error-indicator {
  text-align: center;
  padding: 40px;
  font-size: 16px;
  color: #6c757d;
}
.error-indicator {
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
}

/* Grids for Layout */
.comparison-grid, .form-grid, .confirmation-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.details-section {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 16px;
  border: 1px solid #e9ecef;
}
.details-section h4 {
  margin: 0 0 12px 0;
  color: #495057;
  font-size: 16px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid #dee2e6;
}
.details-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}
.details-row:last-child {
  margin-bottom: 0;
}

/* Form Elements */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.field-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field-group label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  margin-bottom: 6px;
}
.field-group input[type="text"], .field-group input[type="number"] {
  padding: 6px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  background: #e9ecef;
  height: 32px;
  box-sizing: border-box;
}
.field-group.highlight input {
  background: #fff3cd;
  border-color: #ffc107;
  font-weight: 500;
}
.input-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 12px;
  align-items: start;
}
.compact-select, .compact-input, .compact-textarea {
  padding: 6px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  background: #fff;
  height: 32px;
  box-sizing: border-box;
}
.compact-input {
  background: #fff;
}
.compact-textarea {
  min-height: 60px;
  max-height: 80px;
  resize: vertical;
  font-family: inherit;
}

/* Professional Styling */
/* .step-panel {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 24px;
  margin-bottom: 20px;
}

.step-panel h3 {
  color: #2c3e50;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e9ecef;
} */

/* Compact Analysis Section */
.compact-analysis {
  margin-bottom: 16px;
}

.analysis-textarea {
  min-height: 40px !important;
  max-height: 60px !important;
}





/* Professional Button Styling */


/* .btn-add-row {
  background: #e9ecef;
  color: #495057;
  border: 2px dashed #ced4da;
}

.btn-add-row:hover {
  background: #dee2e6;
  border-color: #adb5bd;
}

.btn-assign, .btn-save, .btn-submit {
  background: #0d6efd;
  color: white;
}

.btn-assign:hover, .btn-save:hover, .btn-submit:hover {
  background: #0b5ed7;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Professional File Upload Styling */
/* .file-drop-zone {
  border: 2px dashed #dee2e6 !important;
  background: #f8f9fa !important;
  transition: all 0.3s ease !important;
}

.file-drop-zone:hover {
  border-color: #0d6efd !important;
  background: #e7f3ff !important;
}

.file-drop-zone.drag-over {
  border-color: #0d6efd !important;
  background: #e7f3ff !important;
  transform: scale(1.02);
}

/* Professional Section Headers */
.field-group label {
  font-weight: 600 !important;
  color: #2c3e50 !important;
  margin-bottom: 8px !important;
  font-size: 14px !important;
}
.data-uploads-textarea {
  margin-bottom: 12px;
}  

/* Dynamic Upload Block Style */
.data-upload-block {
  position: relative;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fdfdfd;
}

/* Upload Comment Row with File Drop Zone */
.upload-comment-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 12px;
}

.upload-comment-row .data-uploads-textarea {
  flex: 1;
  margin-bottom: 0;
  min-height: 120px;
  max-height: 200px;
  width: 50%;
}

.upload-comment-row .file-drop-zone {
  flex: 1;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
  border: 1px dashed #ced4da;
  border-radius: 6px;
  background: #f8f9fa;
  cursor: pointer;
  transition: all 0.2s;
  width: 50%;
}

.upload-comment-row .file-drop-zone:hover {
  border-color: #0d6efd;
  background: #e9ecef;
}

.upload-comment-row .file-drop-zone.drag-over {
  border-color: #0d6efd;
  background: #e9ecef;
}

.upload-comment-row .upload-icon {
  font-size: 24px;
  color: #0d6efd;
  margin-bottom: 8px;
}

.upload-comment-row .upload-text {
  font-size: 11px;
  color: #6c757d;
  line-height: 1.3;
  text-align: center;
}

.upload-comment-row .upload-text strong {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  color: #495057;
}

/* Comment/Assignment Rows */
.comment-user-selection-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}
.review-comment-row {
  position: relative;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
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

/* Confirmation Screen Styles */
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

/* File Upload Styles */
.file-upload-container {
  border: 1px dashed #ced4da;
  border-radius: 4px;
  padding: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #f8f9fa;
}
.file-drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.file-drop-zone.drag-over {
  border-color: #0d6efd;
  background: #e9ecef;
}
.upload-icon {
  font-size: 24px;
  color: #0d6efd;
  margin-bottom: 4px;
}
.upload-text {
  font-size: 11px;
  color: #6c757d;
  line-height: 1.3;
}
.hidden-file-input { display: none; }
.uploaded-files-list {
  margin-top: 8px;
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  text-align: left;
}

/* Remove scroll for previously uploaded files */
.improved-upload-list.uploaded-files-list {
  max-height: none;
  overflow-y: visible;
}
.files-header {
  font-size: 12px;
  font-weight: 500;
  color: #495057;
  padding: 4px 8px;
  border-bottom: 1px solid #dee2e6;
}
.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  border-bottom: 1px solid #e9ecef;
}
.file-item:last-child { border-bottom: none; }
.file-info { display: flex; align-items: center; gap: 10px; }
.file-icon { font-size: 16px; }
.file-details { display: flex; flex-direction: column; }
.file-name-container { display: flex; align-items: center; gap: 5px; }
.file-name-input { padding: 3px 5px; border: 1px solid #ced4da; border-radius: 3px; font-size: 12px; }
.file-meta { font-size: 10px; color: #6c757d; }
.file-actions { display: flex; gap: 5px; }
.btn-file-action { background: none; border: none; cursor: pointer; padding: 3px; font-size: 14px;}

/* Bottom Navigation */
.bottom-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 -2px 4px rgba(0,0,0,0.05);
  margin-top: auto;
}
.nav-buttons, .action-buttons {
  display: flex;
  gap: 12px;
}
.btn-nav, .btn-save, .btn-submit {
  padding: 8px 16px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-nav:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-prev { background: #fff; color: #495057; }
.btn-next { background: #0d6efd; color: #fff; border-color: #0d6efd; }
.btn-save { background: #6c757d; color: #fff; border-color: #6c757d; }
.btn-submit { background: #28a745; color: #fff; border-color: #28a745; }

/* Responsive Design */
@media (max-width: 1200px) {
  .comparison-grid, .form-grid, .confirmation-grid { grid-template-columns: 1fr; }
  .details-row { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
  .input-row, .comment-user-selection-row { grid-template-columns: 1fr; gap: 8px; }
}

@media (max-width: 768px) {
  .pma-container { padding: 12px; }
  .steps-container { flex-direction: column; gap: 8px; }
  .step { justify-content: flex-start; }
  .details-row, .confirm-row { grid-template-columns: 1fr; }
  .bottom-navigation { flex-direction: column; gap: 12px; }
  .nav-buttons, .action-buttons { width: 100%; justify-content: center; }
  
  .upload-comment-row {
    flex-direction: column;
    gap: 8px;
  }
  
  .upload-comment-row .file-drop-zone {
    min-width: auto;
    width: 100%;
    min-height: 80px;
  }
}

/* Custom Scrollbar */
.step-content::-webkit-scrollbar { width: 6px; }
.step-content::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 3px; }
.step-content::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 3px; }
.step-content::-webkit-scrollbar-thumb:hover { background: #a8a8a8; }
.readonly-banner {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 6px;
  padding: 14px 20px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.5px;
}
.improved-upload-list {
  background: #f7fafd;
  border: 1px solid #e3e8ee;
  border-radius: 8px;
  padding: 18px 24px 10px 24px;
  margin-bottom: 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.previously-uploaded-files {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.improved-upload-list h4 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #1a3a5d;
}
.uploaded-file-item {
  margin-bottom: 10px;
  padding: 10px 0 8px 0;
  border-bottom: 1px solid #e3e8ee;
  display: flex;
  flex-direction: column;
}
.uploaded-file-item:last-child {
  border-bottom: none;
}
.file-link {
  font-size: 15px;
  font-weight: 500;
  color: #0d6efd;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
}
.file-link:hover {
  text-decoration: underline;
}
.download-icon {
  font-size: 18px;
  color: #0d6efd;
}
.file-meta-small {
  font-size: 12px;
  color: #6c757d;
  margin-left: 26px;
  margin-top: 2px;
}
.status-chip {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}
.status-chip.pending { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
.status-chip.approved { background: #e6f4ea; color: #18794e; border: 1px solid #c7eed8; }
.status-chip.rejected { background: #fde2e2; color: #a61b1b; border: 1px solid #f5b5b5; }

/* Supervisor approval buttons */
.supervisor-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}
.btn-approve, .btn-reject {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
}
.btn-approve {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: #fff;
}
.btn-approve:hover { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(22,163,74,0.25); }
.btn-approve:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-reject {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: #fff;
}
.btn-reject:hover { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(220,38,38,0.25); }
.btn-reject:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-assign {
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
.btn-assign:hover {
  background-color: #d1e7ff;
}

/* Simple Assignment Button Styling - Like Save/Submit */
.btn-assign-prominent {
  background: #0d6efd !important;
  color: white !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  padding: 12px 24px !important;
  border-radius: 6px !important;
  border: none !important;
  box-shadow: 0 2px 4px rgba(13, 110, 253, 0.2) !important;
  transition: all 0.2s ease !important;
  text-transform: none !important;
  letter-spacing: 0.2px !important;
  position: relative !important;
  width: 100% !important;
  max-width: 280px !important;
  margin: 16px auto !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  cursor: pointer !important;
}

.btn-assign-prominent:hover {
  background: #0b5ed7 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(13, 110, 253, 0.3) !important;
}

.btn-assign-prominent:active {
  transform: translateY(0) !important;
  box-shadow: 0 2px 4px rgba(13, 110, 253, 0.2) !important;
}

.btn-assign-prominent:disabled {
  background: #6c757d !important;
  cursor: not-allowed !important;
  transform: none !important;
  box-shadow: none !important;
  opacity: 0.6 !important;
}

/* Icon styling within the button */
.btn-assign-prominent .assignment-icon {
  font-size: 16px;
}

/* Enhanced Add Section Buttons - Nice but Simple */
.btn-add-row {
  background: #f8f9fa !important;
  color: #495057 !important;
  border: 2px dashed #dee2e6 !important;
  border-radius: 8px !important;
  padding: 12px 20px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  margin: 12px 0 !important;
}

.btn-add-row:hover {
  background: #e9ecef !important;
  border-color: #adb5bd !important;
  color: #212529 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

.btn-add-row:active {
  transform: translateY(0) !important;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1) !important;
}



/* Locked Section Styling */
.locked-section-warning {
  background: #fff3cd !important;
  border: 2px solid #ffc107 !important;
  border-radius: 8px !important;
  padding: 20px !important;
  margin: 20px 0 !important;
  display: flex !important;
  align-items: center !important;
  gap: 15px !important;
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3) !important;
  width: 100% !important;
  box-sizing: border-box !important;
  position: relative !important;
  z-index: 10 !important;
}

.locked-section-warning .warning-icon {
  font-size: 24px !important;
  color: #b45309 !important;
  font-weight: bold !important;
  flex-shrink: 0 !important;
  display: inline-block !important;
}

.locked-section-warning .warning-text {
  color: #b45309 !important;
  font-size: 16px !important;
  line-height: 1.5 !important;
  font-weight: 600 !important;
  flex: 1 !important;
  display: block !important;
}

.locked-section-warning .warning-text strong {
  color: #b45309 !important;
  font-weight: 700 !important;
}

.locked-section {
  opacity: 0.5;
  pointer-events: none;
  position: relative;
}

.locked-section::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  z-index: 1;
}
.case-logs-section {
  background: #f8f9fa;
  border: 1px solid #e3e8ee;
  border-radius: 8px;
  padding: 18px 24px 10px 24px;
  margin-top: 24px;
  margin-bottom: 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.case-logs-section h4 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #1a3a5d;
}
.case-log-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.case-logs-section .case-log-list {
  max-height: 40vh;
  overflow-y: auto;
  padding-right: 8px;
}
.case-log-item {
  margin-bottom: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #e3e8ee;
  font-size: 14px;
  display: flex;
  gap: 12px;
  align-items: center;
}
.case-log-item:last-child {
  border-bottom: none;
}
.log-time {
  color: #6c757d;
  font-size: 12px;
  min-width: 120px;
}
.log-user {
  color: #0d6efd;
  font-weight: 500;
}
.log-action {
  color: #28a745;
  font-weight: 500;
}
.log-details {
  color: #495057;
  font-size: 13px;
}

/* Assignment Status Styles */
.assignment-status-section {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  margin-top: 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.assignment-status-section h4 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #1a3a5d;
  padding-bottom: 8px;
  border-bottom: 1px solid #dee2e6;
}
.assignment-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.assignment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 14px;
  color: #343a40;
}
.assignment-info {
  display: flex;
  flex-direction: column;
}
.assigned-user {
  font-weight: 500;
  color: #0d6efd;
}
.assignment-date {
  font-size: 12px;
  color: #6c757d;
  margin-top: 2px;
}
.assignment-comment {
  font-style: italic;
  font-size: 12px;
  color: #6c757d;
  margin-top: 4px;
}
.assignment-actions {
  display: flex;
  gap: 8px;
}
.btn-revoke {
  padding: 4px 8px;
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-revoke:hover {
  background-color: #f5c6cb;
  border-color: #dc3545;
  color: #dc3545;
}
.btn-revoke:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #f8d7da;
  border-color: #f5c6cb;
  color: #721c24;
}
.sent-back-badge {
  padding: 4px 8px;
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeeba;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

/* Reopened Case Warning Styles */
.reopened-warning {
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.warning-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.warning-text {
  color: #856404;
  font-size: 14px;
  line-height: 1.4;
}

.warning-text strong {
  color: #856404;
  font-weight: 600;
}

/* Template Selection Styles */
.template-selection-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.template-info {
  margin-top: 4px;
  color: #6c757d;
  font-style: italic;
}

/* Template Questions Styles */
.template-description {
  color: #6c757d;
  font-size: 14px;
  margin-bottom: 16px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #0d6efd;
}

.template-questions {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 20px;
}

.question-item {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  background: #fafbfc;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.question-text {
  font-weight: 600;
  color: #2c3e50;
  font-size: 15px;
}

.required-indicator {
  color: #dc3545;
  font-weight: bold;
  font-size: 16px;
}

.question-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 0;
}

.radio-option input[type="radio"] {
  accent-color: #0d6efd;
  margin: 0;
}

.radio-option span {
  color: #495057;
  font-size: 14px;
}

.question-input {
  margin-top: 8px;
}

.question-input input,
.question-input textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.question-input input:focus,
.question-input textarea:focus {
  outline: none;
  border-color: #0d6efd;
  box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.25);
}

.question-input textarea {
  min-height: 80px;
  resize: vertical;
  font-family: inherit;
}

.help-text {
  color: #6c757d;
  font-size: 12px;
  margin-top: 4px;
  font-style: italic;
}

/* Template Response Status */
.template-response-status {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  margin-left: 8px;
}

.template-response-status.pending {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeeba;
}

.template-response-status.approved {
  background: #e6f4ea;
  color: #18794e;
  border: 1px solid #c7eed8;
}

.template-response-status.rejected {
  background: #fde2e2;
  color: #a61b1b;
  border: 1px solid #f5b5b5;
}

/* Template Responses Review Styles for Supervisors */
.template-responses-review {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.template-response-item {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  background: #fafbfc;
}

.template-response-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #dee2e6;
}

.template-response-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
}

.template-response-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #6c757d;
}

.template-questions-review {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-review-item {
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 12px;
  background: #ffffff;
}

.question-review-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.question-response {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.response-value {
  color: #495057;
  font-weight: 500;
  padding: 6px 10px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #0d6efd;
  margin-top: 4px;
}

.rejection-reason {
  margin-top: 12px;
  padding: 8px 12px;
  background: #fde2e2;
  border: 1px solid #f5b5b5;
  border-radius: 4px;
  color: #721c24;
  font-size: 13px;
}



/* Approved Response Styling for Risk Officers */
.template-response-item.approved-response {
  border-left: 4px solid #28a745;
  background: #f8fff9;
}

.template-response-item.approved-response .template-response-header h4 {
  color: #155724;
}

.template-response-item.approved-response .template-response-status.approved {
  background: #d4edda;
  color: #155724;
  border-color: #c3e6cb;
}

/* Approved Responses Summary Section */
.approved-responses-summary {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  border: 1px solid #28a745;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.15);
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.summary-icon {
  font-size: 20px;
  color: #155724;
}

.summary-header h4 {
  margin: 0;
  color: #155724;
  font-size: 16px;
  font-weight: 600;
}

.summary-content p {
  margin: 0 0 12px 0;
  color: #155724;
  font-size: 14px;
}

.template-summary-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.7);
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid rgba(40, 167, 69, 0.2);
}

.template-name {
  font-weight: 600;
  color: #155724;
  font-size: 14px;
}

.template-meta {
  color: #28a745;
  font-size: 12px;
  font-weight: 500;
}

/* Latest Changes Summary Section */
.latest-changes-summary {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border: 1px solid #2196f3;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.15);
}

.latest-changes-summary .summary-header h4 {
  color: #1565c0;
}

.latest-changes-summary .summary-content p {
  color: #1565c0;
}

.department-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.department-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.7);
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid rgba(33, 150, 243, 0.2);
}

.dept-name {
  font-weight: 600;
  color: #1565c0;
  font-size: 14px;
}

.dept-status {
  color: #2196f3;
  font-size: 12px;
  font-weight: 500;
}

/* Supervisor Info Box Styles */
.supervisor-info-box {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #e3f2fd;
  border: 1px solid #2196f3;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.supervisor-actions {
  margin-top: 12px;
}

.btn-template-review {
  display: inline-block;
  background: #2196f3;
  color: white;
  text-decoration: none;
  padding: 10px 16px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
}

.btn-template-review:hover {
  background: #1976d2;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
}

.info-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

.info-content {
  flex: 1;
}

.info-content strong {
  display: block;
  color: #1565c0;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.info-content p {
  margin: 4px 0;
  color: #1976d2;
  font-size: 14px;
  line-height: 1.4;
}

/* Template Files Preview Styling */
.template-files-preview {
  margin-top: 12px;
  padding: 12px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
}

.template-files-header {
  font-size: 12px;
  font-weight: 600;
  color: #495057;
  margin-bottom: 8px;
}

.template-files-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.template-file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 12px;
}

.template-file-item .file-icon {
  font-size: 14px;
}

.template-file-item .file-name {
  flex: 1;
  color: #495057;
  font-weight: 500;
}

.template-file-item .file-size {
  color: #6c757d;
  font-size: 11px;
}

/* Responsive adjustments for template questions */
@media (max-width: 768px) {
  .template-questions {
    gap: 16px;
  }
  
  .question-item {
    padding: 12px;
  }
  
  .question-text {
    font-size: 14px;
  }
  
  .radio-option {
    font-size: 13px;
  }
  
  .template-response-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .template-response-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .supervisor-info-box {
    flex-direction: column;
    gap: 8px;
  }
  
  .approved-responses-summary {
    padding: 12px;
  }
  
  .template-summary-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .latest-changes-summary {
    padding: 12px;
  }
  
  .department-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

/* Progressive loading styles */
.section-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  margin: 16px 0;
  color: #6c757d;
  font-size: 14px;
  font-weight: 500;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e9ecef;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>