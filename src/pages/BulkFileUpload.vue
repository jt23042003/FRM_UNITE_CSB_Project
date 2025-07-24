<template>
  <div class="page-container">
    <h1 class="screen-header">Bulk Complaint Processing</h1>
    
    <div class="upload-card">
      <h2 class="card-title">Upload JSON File</h2>
      <p class="card-subtitle">
        Select a .json file containing an array of complaint records. The system will process each record individually.
      </p>

      <div 
        class="file-input-area"
        :class="{ 'uploading': isLoading }"
        @dragover.prevent
        @drop.prevent="handleFileDrop"
      >
        <label for="json-upload" class="file-upload-label">
          <span class="button-style">{{ file ? 'File Selected' : 'Choose File' }}</span>
          <span class="file-name">{{ file ? file.name : 'No file chosen' }}</span>
        </label>
        <input 
          id="json-upload"
          type="file" 
          @change="handleFileSelect" 
          accept=".json"
          class="visually-hidden"
        />
      </div>

      <button 
        @click="startProcessing" 
        :disabled="!file || isLoading" 
        :class="{ 'processing': isLoading }"
        class="process-btn"
      >
        <span v-if="isLoading">Processing...</span>
        <span v-else>Start Processing</span>
      </button>

      <div v-if="result" class="results-panel">
        <h3 class="results-title">{{ result.message }}</h3>
        <div class="results-grid">
          <div class="result-item success">
            <span class="count">{{ result.success_count }}</span>
            <span class="label">Records Succeeded</span>
          </div>
          <div class="result-item failed">
            <span class="count">{{ result.failed_count }}</span>
            <span class="label">Records Failed</span>
          </div>
        </div>
        <div v-if="result && result.error_file_path" class="error-file-info">
          <p>An error log has been generated for the failed records.</p>
          <strong>Download:</strong> 
          <a :href="result.download_url" target="_blank" class="download-link">
            {{ result.error_file_path }}
          </a>
        </div>
        <!-- New: Show detailed errors for failed records -->
        <div v-if="result.errors && result.errors.length > 0" class="bulk-error-details">
          <h4>Failed Records Details</h4>
          <table class="bulk-error-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Error</th>
                <th>Record Data</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="err in result.errors" :key="err.index">
                <td>{{ err.index + 1 }}</td>
                <td>
                  <div v-if="typeof err.error === 'string'">{{ err.error }}</div>
                  <div v-else-if="err.error && err.error.type === 'validation'">
                    <ul>
                      <li v-for="(v, i) in err.error.detail" :key="i">
                        <span v-if="v.loc && v.loc.length > 1">{{ v.loc[1] }}: </span>{{ v.msg }}
                      </li>
                    </ul>
                  </div>
                  <div v-else-if="err.error && err.error.type === 'db' && (err.error.detail && (err.error.detail.includes('duplicate key value violates unique constraint') || err.error.detail.includes('already exists'))) ">
                    <span>
                      Duplicate Acknowledgement Number detected: <strong>{{ err.record && (err.record.ackNo || err.record.ackno || err.record.ack_no) }}</strong> is already in use.
                    </span>
                  </div>
                  <div v-else-if="err.error && err.error.detail">
                    {{ err.error.detail }}
                  </div>
                  <div v-else>
                    {{ err.error ? JSON.stringify(err.error) : 'Unknown error' }}
                  </div>
                </td>
                <td>
                  <pre class="record-json">{{ JSON.stringify(err.record, null, 2) }}</pre>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- End error details -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import '../assets/BulkFileUpload.css'

const file = ref(null);
const isLoading = ref(false);
const result = ref(null);

function handleFileSelect(event) {
  const selectedFile = event.target.files[0];
  if (selectedFile && selectedFile.type === 'application/json') {
    file.value = selectedFile;
    result.value = null;
  } else {
    alert('Please select a valid .json file.');
    file.value = null;
    event.target.value = '';
  }
}

function handleFileDrop(event) {
  const droppedFile = event.dataTransfer.files[0];
  if (droppedFile && droppedFile.type === 'application/json') {
    file.value = droppedFile;
    result.value = null;
  } else {
    alert('Please drop a valid .json file.');
  }
}

async function startProcessing() {
  if (!file.value) return;

  isLoading.value = true;
  result.value = null;
  
  const formData = new FormData();
  formData.append('file', file.value);

  try {
    const res = await axios.post('http://34.47.219.225:9000/api/process-bulk-file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    result.value = res.data;

    if (result.value.error_file_path) {
      result.value.download_url = `http://34.47.219.225:9000/api/download-error-log/${result.value.error_file_path}`;
    }

  } catch (error) {
    console.error("Failed to process file:", error.response?.data || error.message);
    alert(`An error occurred: ${error.response?.data?.detail || 'Please check the console.'}`);
    result.value = {
      message: 'Processing failed due to a server error.',
      success_count: 'N/A',
      failed_count: 'N/A',
      error_file_path: null
    };
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.bulk-error-details {
  margin-top: 2rem;
  background: #fff3cd;
  border: 1px solid #ffeeba;
  border-radius: 8px;
  padding: 1.5rem;
}
.bulk-error-details h4 {
  color: #856404;
  margin-bottom: 1rem;
}
.bulk-error-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}
.bulk-error-table th, .bulk-error-table td {
  border: 1px solid #ffeeba;
  padding: 0.75rem 1rem;
  text-align: left;
  vertical-align: top;
  font-size: 0.95rem;
}
.bulk-error-table th {
  background: #fff8e1;
  color: #856404;
}
.bulk-error-table tr:nth-child(even) {
  background: #fffdf5;
}
.record-json {
  font-size: 0.85rem;
  background: #f8f9fa;
  border-radius: 4px;
  padding: 0.5rem;
  overflow-x: auto;
  max-width: 400px;
  white-space: pre-wrap;
}
</style>