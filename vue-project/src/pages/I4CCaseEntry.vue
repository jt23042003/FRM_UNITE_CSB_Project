<template>
  <div class="form-bg">
    <form class="entry-card grouped-form" @submit.prevent="onSubmit">
      <h2 class="form-title">I4C Fraud Complaint Entry</h2>
      <div class="section-grid">
        <label>
          Acknowledgement No.
          <input v-model="form.ackNo" type="text" required />
        </label>
        <label>
          Sub Category of Complaint
          <input v-model="form.subCategory" type="text" required />
        </label>
        <label>
          Transaction Date
          <input v-model="form.transactionDate" type="date" required />
        </label>
        <label>
          Complaint Date
          <input v-model="form.complaintDate" type="date" required />
        </label>
        <label>
          Date & Time of Reporting / Escalation
          <input v-model="form.reportDateTime" type="datetime-local" required />
        </label>
        <label>
          State
          <input v-model="form.state" type="text" required />
        </label>
        <label>
          District
          <input v-model="form.district" type="text" required />
        </label>
        <label>
          Policestation
          <input v-model="form.policestation" type="text" required />
        </label>
        <label>
          Mode of Payment
          <input v-model="form.paymentMode" type="text" required />
        </label>
        <label>
          Account Number
          <input v-model="form.accountNumber" type="number" required />
        </label>
        <label>
          Card Number
          <input v-model="form.cardNumber" type="number" />
        </label>
        <label>
          Transaction Id / UTR Number
          <input v-model="form.transactionId" type="number" required />
        </label>
        <label>
          Layers
          <select v-model="form.layers" required>
            <option value="">Select Layer</option>
            <option v-for="n in 30" :key="n" :value="`Layer ${n}`">Layer {{ n }}</option>
          </select>
        </label>
        <label>
          Transaction Amount
          <input v-model.number="form.transactionAmount" type="number" min="0" step="1" required />
        </label>
        <label>
          Disputed Amount
          <input v-model.number="form.disputedAmount" type="number" min="0" step="1" required />
        </label>
        <label>
          Action
          <input v-model="form.action" type="text" />
        </label>
        <label>
          Money transfer TO Bank
          <input v-model="form.toBank" type="number" />
        </label>
        <label>
          Money transfer TO Account
          <input v-model="form.toAccount" type="number" />
        </label>
        <label>
          IFSC Code (Non Mandatory)
          <input v-model="form.ifsc" type="text" />
        </label>
        <label>
          Money transfer TO Transaction Id / UTR Number
          <input v-model="form.toTransactionId" type="number" />
        </label>
        <label>
          Money transfer TO Amount
          <input v-model.number="form.toAmount" type="number" min="0" step="1" />
        </label>
        <label>
          Action Taken Date
          <input v-model="form.actionTakenDate" type="date" />
        </label>
        <label>
          Lien Amount (Non Mandatory)
          <input v-model.number="form.lienAmount" type="number" min="0" step="1" />
        </label>
        <label>
          Evidence Provided (Non Mandatory)
          <input type="file" @change="onFileChange" />
          <span v-if="form.evidenceName" style="display:block;margin-top:0.3rem;color:#2563eb;">Selected: {{ form.evidenceName }}</span>
        </label>
        <label class="span-all">
      Additional Information
      <textarea v-model="form.additionalInfo" placeholder="I was added in a WhatsApp group and..."></textarea>
    </label>
      </div>
      <div class="action-buttons span-all">
        <button class="submit-btn" type="submit">Submit/Save</button>
        <button class="reset-btn" type="button" @click="onReset">Reset/Clear</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import axios from 'axios'

const form = reactive({
  ackNo: '',
  subCategory: '',
  transactionDate: '',
  complaintDate: '',
  reportDateTime: '',
  state: '',
  district: '',
  policestation: '',
  paymentMode: '',
  accountNumber: '',
  cardNumber: '',
  transactionId: '',
  layers: '',
  transactionAmount: null,
  disputedAmount: null,
  action: '',
  toBank: '',
  toAccount: '',
  ifsc: '',
  toTransactionId: '',
  toAmount: null,
  actionTakenDate: '',
  lienAmount: null,
  evidence: null,      // will hold the file object
  evidenceName: '',    // for display only
  additionalInfo: ''
})

function onFileChange(e) {
  const file = e.target.files[0]
  form.evidence = file || null
  form.evidenceName = file ? file.name : ''
}

const onSubmit = async () => {
  try {
    await axios.post(
  'http://34.47.219.225:9000/api/match-i4c-data',
  { ...form },
  { headers: { 'Content-Type': 'application/json' } }
)
    alert('Case submitted successfully.')
    onReset()
  } catch (error) {
    alert('Failed to submit case. Check console.')
    console.error(error)
  }
}

const onReset = () => {
  for (const key in form) {
    form[key] = (typeof form[key] === 'number') ? null : ''
  }
  form.evidence = null
  form.evidenceName = ''
}
</script>