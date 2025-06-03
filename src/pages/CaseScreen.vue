<template>
    <div class="case-details-bg">
      <h2 class="case-details-header">Case Details: {{ caseData.ack_no || '-' }}</h2>
      <div v-if="loading" class="case-details-loading">Loading...</div>
      <div v-else-if="error" class="case-details-error">{{ error }}</div>
      <div v-else>
        <table class="case-details-table">
          <tbody>
            <tr><th>Case ID</th><td>{{ caseData.case_id }}</td></tr>
            <tr><th>Acknowledgement No.</th><td>{{ caseData.ack_no }}</td></tr>
            <tr><th>Match Type</th><td>{{ caseData.match_type }}</td></tr>
            <tr><th>Status</th><td>{{ caseData.status }}</td></tr>
            <tr><th>Created On</th><td>{{ caseData.created_on }}</td></tr>
            <tr><th>Closed On</th><td>{{ caseData.closed_on || '-' }}</td></tr>
            <tr><th>Decision</th><td>{{ caseData.decision || '-' }}</td></tr>
            <tr><th>Remarks</th><td>{{ caseData.remarks || '-' }}</td></tr>
            <tr><th>Assigned To</th><td>{{ caseData.assigned_to || '-' }}</td></tr>
            <tr><th>Mobile</th><td>{{ caseData.details?.mobile || '-' }}</td></tr>
            <tr><th>Email</th><td>{{ caseData.details?.email || '-' }}</td></tr>
            <tr><th>PAN</th><td>{{ caseData.details?.pan || '-' }}</td></tr>
            <tr><th>Aadhaar</th><td>{{ caseData.details?.aadhar || '-' }}</td></tr>
            <tr><th>Card</th><td>{{ caseData.details?.card || '-' }}</td></tr>
            <tr><th>Account</th><td>{{ caseData.details?.acct || '-' }}</td></tr>
            <tr><th>Transaction ID</th><td>{{ caseData.details?.txn_id || '-' }}</td></tr>
            <tr><th>Complaint Date</th><td>{{ caseData.details?.comp_date || '-' }}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import { useRoute } from 'vue-router'
  import axios from 'axios'
  import '../assets/CaseScreen.css'
  
  const route = useRoute()
  const ackno = route.params.ackno
  
  const caseData = ref({})
  const loading = ref(true)
  const error = ref('')
  
  onMounted(async () => {
    loading.value = true
    error.value = ''
    try {
      const res = await axios.get(`http://34.47.219.225:9000/api/case/${ackno}`)
      caseData.value = res.data
    } catch (e) {
      error.value = 'Failed to fetch case details.'
    }
    loading.value = false
  })
  </script>
  