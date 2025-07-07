<template>
    <div class="page-container">
      <h1 class="screen-header">Bulk Complaint Processing</h1>
      
      <div class="upload-card">
        <h2 class="card-title">Upload JSON File</h2>
        <p class="card-subtitle">
          Select a .json file containing an array of complaint records. The system will process each record individually.
        </p>
  
        <div class="file-input-area">
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
  
        <button @click="startProcessing" :disabled="!file || isLoading" class="process-btn">
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
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  import axios from 'axios';
  import '../assets/BulkFileUpload.css' // Keep this line if it's correct for your project
  
  const file = ref(null);
  const isLoading = ref(false);
  const result = ref(null); // Initialize with null (JavaScript)
  
  function handleFileSelect(event) {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.type === 'application/json') {
      file.value = selectedFile;
      result.value = null; // Clear previous results using null
    } else {
      alert('Please select a valid .json file.');
      file.value = null;
      event.target.value = ''; // Reset file input
    }
  }
  
  async function startProcessing() {
    if (!file.value) return;
  
    isLoading.value = true;
    result.value = null; // Corrected to use null
    
    const formData = new FormData();
    formData.append('file', file.value);
  
    try {
      const res = await axios.post('http://34.47.219.225:9000/api/process-bulk-file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      result.value = res.data; // Assign the API response to result.value first
  
      // IMPORTANT: Move this block HERE, AFTER result.value has been assigned
      if (result.value.error_file_path) {
          result.value.download_url = `http://34.47.219.225:9000/api/download-error-log/${result.value.error_file_path}`;
      }
      // END IMPORTANT MOVE
  
    } catch (error) {
      console.error("Failed to process file:", error.response?.data || error.message);
      alert(`An error occurred: ${error.response?.data?.detail || 'Please check the console.'}`);
      result.value = { // Corrected to use null
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