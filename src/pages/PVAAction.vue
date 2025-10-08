<template>
    <div class="pva-container">
      <!-- Progress Steps -->
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
  
      <!-- Step Content -->
      <div class="step-content">
        <!-- Step 1: Alert & Customer Details -->
        <div v-if="currentStep === 1" class="step-panel">
          <h3>Alert - Potential Victim Account - Amount Transferred to Suspect Beneficiaries</h3>
          <div class="comparison-grid">
            <!-- I4C Details -->
            <div class="details-section">
              <h4>Customer Details - I4C</h4>
              <div class="details-row">
                <div class="field-group">
                  <label>Name</label>
                  <input type="text" v-model="i4cDetails.name" readonly />
                </div>
                <div class="field-group">
                  <label>Mobile Number</label>
                  <input type="text" v-model="i4cDetails.mobile" readonly />
                </div>
                <div class="field-group">
                  <label>Email</label>
                  <input type="text" v-model="i4cDetails.email" readonly />
                </div>
                <div class="field-group">
                  <label>IFSC Code</label>
                  <input type="text" v-model="i4cDetails.ifsc" readonly />
                </div>
              </div>
              <div class="details-row">
                <div class="field-group">
                  <label>Beneficiary Account Number</label>
                  <input type="text" v-model="i4cDetails.beneficiaryAccount" readonly />
                </div>
                <div class="field-group">
                  <label>Bank Name</label>
                  <input type="text" v-model="i4cDetails.bankName" readonly />
                </div>
              </div>
            </div>
  
            <!-- Bank Details -->
            <div class="details-section">
              <h4>Customer Details - Bank</h4>
              <div class="highlight-note">Matched information to be highlighted/coloured</div>
              <div class="details-row">
                <div class="field-group highlight">
                  <label>Name</label>
                  <input type="text" v-model="bankDetails.name" readonly />
                </div>
                <div class="field-group highlight">
                  <label>Mobile Number</label>
                  <input type="text" v-model="bankDetails.mobile" readonly />
                </div>
                <div class="field-group highlight">
                  <label>Email</label>
                  <input type="text" v-model="bankDetails.email" readonly />
                </div>
                <div class="field-group highlight">
                  <label>IFSC Code</label>
                  <input type="text" v-model="bankDetails.ifsc" readonly />
                </div>
              </div>
              <div class="details-row">
                <div class="field-group">
                  <label>Beneficiary Account Number</label>
                  <input type="text" v-model="bankDetails.beneficiaryAccount" readonly />
                </div>
                <div class="field-group">
                  <label>Bank Name</label>
                  <input type="text" v-model="bankDetails.bankName" readonly />
                </div>
              </div>
              <div class="details-row">
                <div class="field-group">
                  <label>Customer ID</label>
                  <input type="text" v-model="bankDetails.customerId" readonly />
                </div>
                <div class="field-group">
                  <label>AQB</label>
                  <input type="text" v-model="bankDetails.aqb" readonly />
                </div>
                <div class="field-group">
                  <label>Avail. Bal.</label>
                  <input type="text" v-model="bankDetails.availBal" readonly />
                </div>
                <div class="field-group">
                  <label>Product Code</label>
                  <input type="text" v-model="bankDetails.productCode" readonly />
                </div>
              </div>
              <div class="details-row">
                <div class="field-group">
                  <label>Rel. Value</label>
                  <input type="text" v-model="bankDetails.relValue" readonly />
                </div>
                <div class="field-group">
                  <label>MOB / Vintage</label>
                  <input type="text" v-model="bankDetails.mob" readonly />
                </div>
                <div class="field-group">
                  <label>A/c Status</label>
                  <input type="text" v-model="bankDetails.accountStatus" readonly />
                </div>
              </div>
              <div class="details-row">
                <div class="field-group">
                  <label>Addl field1</label>
                  <input type="text" v-model="bankDetails.addlField1" readonly />
                </div>
                <div class="field-group">
                  <label>Addl field2</label>
                  <input type="text" v-model="bankDetails.addlField2" readonly />
                </div>
                <div class="field-group">
                  <label>Addl field4</label>
                  <input type="text" v-model="bankDetails.addlField4" readonly />
                </div>
              </div>
            </div>
          </div>
  
          <!-- Transaction Details -->
          <div class="transaction-section">
            <h4>Transaction details :</h4>
            <div class="transaction-table">
              <div class="table-header">
                <div>Date</div>
                <div>Time</div>
                <div>Beneficiary</div>
                <div>Amount</div>
                <div>Mode</div>
                <div>Txn. Ref #</div>
                <div>Txn Description</div>
              </div>
              <div v-for="(txn, index) in transactions" :key="index" class="table-row">
                <div>{{ txn.date }}</div>
                <div>{{ txn.time }}</div>
                <div>{{ txn.beneficiary }}</div>
                <div>{{ txn.amount }}</div>
                <div>{{ txn.mode }}</div>
                <div>{{ txn.refNumber }}</div>
                <div>{{ txn.description }}</div>
              </div>
              <div class="total-row">
                <div></div>
                <div></div>
                <div><strong>Total Value @ Risk</strong></div>
                <div><strong>{{ totalAtRisk }}</strong></div>
                <div></div>
                <div></div>
                <div></div>
              </div>
            </div>
          </div>
        </div>
  
        <!-- Step 2: Analysis & Investigation -->
        <div v-if="currentStep === 2" class="step-panel">
          <h3>Analysis & Investigation</h3>
          <div class="action-grid">
            <div class="action-section">
              <div class="field-group">
                <label>Analysis / Investigation Update</label>
                <div class="input-row">
                  <select v-model="action.analysisLOV" class="compact-select">
                    <option value="">LOV</option>
                    <option value="under-review">Under Review</option>
                    <option value="suspicious">Suspicious Activity</option>
                    <option value="cleared">Cleared</option>
                  </select>
                  <textarea v-model="action.analysisUpdate" placeholder="Update" class="compact-textarea"></textarea>
                </div>
              </div>
  
              <div class="field-group">
                <label>Alert Initial review feedback</label>
                <div class="input-row">
                  <select v-model="action.initialReviewLOV" class="compact-select">
                    <option value="">Drop Down</option>
                    <option value="immediate">Immediate</option>
                    <option value="escalate">Escalate</option>
                    <option value="hold">Hold</option>
                  </select>
                  <textarea v-model="action.initialReview" placeholder="Text box with free flow text" class="compact-textarea"></textarea>
                </div>
              </div>
  
              <div class="field-group">
                <label>Reassignment if required :</label>
                <div class="reassign-header">
                  <span>User ID</span>
                  <span>Dept</span>
                  <span>Date/Time</span>
                </div>
                <div v-for="(item, index) in action.reassignments" :key="index" class="reassign-row">
                  <span class="forward-label" v-if="index === 0">Forward to</span>
                  <span class="forward-label" v-else>Forward to</span>
                  <input type="text" v-model="item.userId" placeholder="User ID" class="compact-input" />
                  <select v-model="item.dept" class="compact-select">
                    <option value="LOV">LOV</option>
                  </select>
                  <input type="text" v-model="item.timestamp" value="Stamp" readonly class="compact-input" />
                </div>
              </div>
            </div>
  
            <div class="action-section">
              <div class="field-group">
                <label>Review / Feedback from other functions</label>
                <div class="review-header">
                  <span>User ID / Dept</span>
                  <span>Update - LOV</span>
                  <span>Update - Text box</span>
                  <span>Date/Time</span>
                </div>
                <div v-for="(review, index) in action.reviews" :key="index" class="review-row">
                  <input type="text" v-model="review.userId" placeholder="User ID" class="compact-input" />
                  <select v-model="review.lov" class="compact-select">
                    <option value="LOV">LOV</option>
                  </select>
                  <textarea v-model="review.text" placeholder="Free flow" class="compact-textarea-small"></textarea>
                  <input type="text" v-model="review.timestamp" value="Stamp" readonly class="compact-input" />
                </div>
              </div>
            </div>
          </div>
        </div>
  
        <!-- Step 3: Final Closure -->
        <div v-if="currentStep === 3" class="step-panel">
          <h3>Final Closure</h3>
          <div class="form-grid">
            <div class="form-section">
              <div class="field-group">
                <label>Alert Final Closure remarks</label>
                <div class="input-row">
                  <select v-model="action.closureLOV" class="compact-select">
                    <option value="">Drop Down</option>
                    <option value="genuine">Genuine Transaction</option>
                    <option value="victim-confirmed">Victim Confirmed</option>
                    <option value="needs-investigation">Needs Further Investigation</option>
                  </select>
                  <textarea v-model="action.closureRemarks" placeholder="Text box with free flow text" class="compact-textarea"></textarea>
                </div>
              </div>
            </div>
          </div>
        </div>
  
        <!-- Step 4: Confirmation -->
        <div v-if="currentStep === 4" class="step-panel">
          <h3>Confirmation</h3>
          <div class="confirmation-grid">
            <div class="confirm-section">
              <div class="confirm-row">
                <label>Confirm / Final Closure</label>
                <select v-model="action.confirmClosure" class="compact-select">
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                </select>
              </div>
              <div class="confirm-row">
                <label>Confirmed Victim</label>
                <select v-model="action.confirmedVictim" class="compact-select">
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                </select>
              </div>
              <div class="confirm-row">
                <label>Funds Saved</label>
                <input 
                  type="number" 
                  v-model="action.fundsSaved" 
                  :disabled="isReadOnly" 
                  class="compact-input"
                  placeholder="Amount (INR)"
                  min="0"
                  step="0.01"
                />
              </div>
            </div>
            <div class="confirm-section">
              <div class="confirm-row">
                <label>Digital Channel blocked</label>
                <select v-model="action.digitalBlocked" class="compact-select">
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                </select>
              </div>
              <div class="confirm-row">
                <label>A/c fully blocked and closed</label>
                <select v-model="action.accountBlocked" class="compact-select">
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                </select>
              </div>
              <div class="confirm-row">
                <label>Date & Time</label>
                <div class="datetime-row">
                  <input 
                    type="date" 
                    v-model="action.closureDate" 
                    :disabled="action.confirmClosure !== 'Yes'" 
                    class="compact-input"
                  />
                  <input 
                    type="time" 
                    v-model="action.closureTime" 
                    :disabled="action.confirmClosure !== 'Yes'" 
                    class="compact-input"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
  
      <!-- Navigation & Action Buttons -->
      <div class="bottom-navigation">
        <div class="nav-buttons">
          <button 
            @click="previousStep" 
            :disabled="currentStep === 1"
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
          <button @click="saveAction" class="btn-save">Save</button>
          <button @click="submitAction" class="btn-submit">Submit</button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import axios from 'axios';
  import { API_ENDPOINTS } from '../config/api.js';
  
  const route = useRoute();
  
  // Multi-step form state
  const currentStep = ref(1);
  const steps = ref([
    { title: 'Victim Details', icon: 'alert' },
    { title: 'Analysis', icon: 'analysis' },
    { title: 'Closure', icon: 'closure' },
    { title: 'Confirmation', icon: 'confirm' }
  ]);
  
  // Navigation methods
  const goToStep = (step) => {
    currentStep.value = step;
  };
  
  const nextStep = () => {
    if (currentStep.value < steps.value.length) {
      currentStep.value++;
    }
  };
  
  const previousStep = () => {
    if (currentStep.value > 1) {
      currentStep.value--;
    }
  };
  
  // Data structure for I4C details
  const i4cDetails = ref({
    name: 'John Doe',
    mobile: '+91-9876543210',
    email: 'john.doe@email.com',
    ifsc: 'HDFC0001234',
    beneficiaryAccount: '1234567890123456',
    bankName: 'HDFC Bank'
  });
  
  // Data structure for Bank details
  const bankDetails = ref({
    name: 'John Doe',
    mobile: '+91-9876543210',
    email: 'john.doe@email.com',
    ifsc: 'HDFC0001234',
    beneficiaryAccount: '1234567890123456',
    bankName: 'HDFC Bank',
    customerId: 'CUST001234',
    aqb: '99999999.99',
    availBal: '99999999.99',
    productCode: 'ALPHA123',
    relValue: '99999999.99',
    mob: 'ALPHA123',
    accountStatus: 'Open',
    addlField1: '',
    addlField2: '',
    addlField4: ''
  });
  
  // Transaction details
  const transactions = ref([
    {
      date: '2024-01-15',
      time: '14:30',
      beneficiary: 'SUSPECT_ACCT_001',
      amount: '₹50,000.00',
      mode: 'NEFT',
      refNumber: 'TXN123456789',
      description: 'Fund Transfer to Suspect'
    },
    {
      date: '2024-01-16',
      time: '09:15',
      beneficiary: 'SUSPECT_ACCT_002',
      amount: '₹75,000.00',
      mode: 'IMPS',
      refNumber: 'TXN987654321',
      description: 'Online Transfer to Suspect'
    }
  ]);
  
  const totalAtRisk = computed(() => {
    return '₹1,25,000.00';
  });
  
  // Action section data
  const action = ref({
    analysisLOV: '',
    analysisUpdate: '',
    initialReviewLOV: '',
    initialReview: '',
    reassignments: [
      { userId: '', dept: 'LOV', timestamp: 'Stamp' },
      { userId: '', dept: 'LOV', timestamp: 'Stamp' },
      { userId: '', dept: 'LOV', timestamp: 'Stamp' }
    ],
    reviews: [
      { userId: '', lov: 'LOV', text: '', timestamp: 'Stamp' },
      { userId: '', lov: 'LOV', text: '', timestamp: 'Stamp' },
      { userId: '', lov: 'LOV', text: '', timestamp: 'Stamp' }
    ],
    closureLOV: '',
    closureRemarks: '',
    confirmClosure: 'No',
    confirmedVictim: 'No',
    fundsSaved: null,
    digitalBlocked: 'No',
    accountBlocked: 'No',
    closureDate: '',
    closureTime: ''
  });
  
  // Fetch case details on component mount
  onMounted(async () => {
    try {
      const caseId = route.params.case_id;
      const token = localStorage.getItem('jwt');
      
      if (!token) {
        throw new Error('No authentication token found');
      }
  
      // Uncomment when API is ready
      // const response = await axios.get(`${API_ENDPOINTS.CASE_DETAILS}/${caseId}`, {
      //   headers: { 'Authorization': `Bearer ${token}` }
      // });
  
      // if (response.data) {
      //   const data = response.data;
      //   Object.assign(i4cDetails.value, data.i4c_details || {});
      //   Object.assign(bankDetails.value, data.bank_details || {});
      //   if (data.action_details) {
      //     Object.assign(action.value, data.action_details);
      //   }
      //   if (data.transactions) {
      //     transactions.value = data.transactions;
      //   }
      // }
    } catch (error) {
      console.error('Error fetching case details:', error);
    }
  });
  
  // Save action details
  const saveAction = async () => {
    try {
      const token = localStorage.getItem('jwt');
      const caseId = route.params.case_id;
      
      console.log('Saving action:', action.value);
      // Uncomment when API is ready
      // await axios.post(`${API_ENDPOINTS.SAVE_ACTION}/${caseId}`, {
      //   action_details: action.value
      // }, {
      //   headers: { 'Authorization': `Bearer ${token}` }
      // });
    } catch (error) {
      console.error('Error saving action:', error);
    }
  };
  
  // Submit final action
  const submitAction = async () => {
    try {
      const token = localStorage.getItem('jwt');
      const caseId = route.params.case_id;
      
      console.log('Submitting action:', action.value);
      // Uncomment when API is ready
      // await axios.post(`${API_ENDPOINTS.SUBMIT_ACTION}/${caseId}`, {
      //   action_details: action.value
      // }, {
      //   headers: { 'Authorization': `Bearer ${token}` }
      // });
    } catch (error) {
      console.error('Error submitting action:', error);
    }
  };
  </script>
  
  <style scoped>
  .pva-container {
    height: 100vh;
    overflow: hidden;
    margin-left: 0px;
    padding: 16px;
    background: #f8f9fa;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
  }
  
  /* Progress Steps */
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
  
  .step.active .step-number,
  .step.completed .step-number {
    background: rgba(255,255,255,0.3);
  }
  
  .step-title {
    font-size: 14px;
    font-weight: 500;
  }
  
  /* Step Content */
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
    font-size: 18px;
    font-weight: 600;
    padding-bottom: 12px;
    border-bottom: 2px solid #e9ecef;
  }
  
  /* Comparison Grid - Step 1 */
  .comparison-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
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
  
  .highlight-note {
    background: #fff3cd;
    color: #856404;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 12px;
    margin-bottom: 12px;
    border: 1px solid #ffc107;
  }
  
  .details-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
    margin-bottom: 12px;
  }
  
  .field-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .field-group label {
    font-size: 12px;
    font-weight: 500;
    color: #6c757d;
    margin-bottom: 2px;
  }
  
  .field-group input {
    padding: 6px 8px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 13px;
    background: #fff;
    height: 32px;
    box-sizing: border-box;
  }
  
  .field-group.highlight input {
    background: #fff3cd;
    border-color: #ffc107;
    font-weight: 500;
  }
  
  /* Transaction Table */
  .transaction-section {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #e9ecef;
  }
  
  .transaction-section h4 {
    margin: 0 0 12px 0;
    color: #495057;
    font-size: 16px;
    font-weight: 600;
  }
  
  .transaction-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
  }
  
  .table-header, .table-row {
    display: grid;
    grid-template-columns: 100px 80px 150px 120px 80px 120px 1fr;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid #dee2e6;
    font-size: 13px;
    color: #495057;
  }
  
  .table-header {
    font-weight: 600;
    background: #f8f9fa;
    border-bottom: 2px solid #dee2e6;
  }
  
  .table-row {
    padding: 8px 0;
    border-bottom: 1px solid #f1f3f5;
  }
  
  .table-row:last-child {
    border-bottom: none;
  }
  
  .total-row {
    display: grid;
    grid-template-columns: 100px 80px 150px 120px 80px 120px 1fr;
    gap: 8px;
    padding: 8px 0;
    font-size: 14px;
    font-weight: 600;
    color: #dc3545;
    border-top: 2px solid #dc3545;
    margin-top: 8px;
  }
  
  /* Action Grid - Step 2 */
  .action-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }
  
  .action-section {
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
    grid-template-columns: 150px 1fr;
    gap: 12px;
    align-items: start;
  }
  
  .reassign-header, .review-header {
    display: grid;
    grid-template-columns: 80px 120px 80px 80px;
    gap: 8px;
    margin-bottom: 8px;
    font-weight: 500;
    color: #495057;
    font-size: 12px;
    padding: 8px;
    background: #f8f9fa;
    border-radius: 4px;
  }
  
  .reassign-row {
    display: grid;
    grid-template-columns: 80px 120px 80px 80px;
    gap: 8px;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .review-row {
    display: grid;
    grid-template-columns: 120px 80px 1fr 80px;
    gap: 8px;
    align-items: start;
    margin-bottom: 8px;
  }
  
  .forward-label {
    font-size: 12px;
    color: #6c757d;
    padding: 6px 0;
  }
  
  /* Form Grid - Step 3 */
  .form-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .form-section {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  /* Confirmation Grid - Step 4 */
  .confirmation-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }
  
  .confirm-section {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .confirm-row {
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 12px;
    align-items: center;
  }
  
  .confirm-row label {
    font-size: 14px;
    font-weight: 500;
    color: #495057;
  }
  
  .datetime-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  
  /* Compact Form Elements */
  .compact-select {
    padding: 6px 8px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 13px;
    background: #fff;
    height: 32px;
    box-sizing: border-box;
  }
  
  .compact-input {
    padding: 6px 8px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 13px;
    background: #fff;
    height: 32px;
    box-sizing: border-box;
  }
  
  .compact-textarea {
    padding: 8px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 13px;
    background: #fff;
    min-height: 60px;
    max-height: 80px;
    resize: vertical;
    font-family: inherit;
    box-sizing: border-box;
  }
  
  .compact-textarea-small {
    padding: 6px 8px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 12px;
    background: #fff;
    min-height: 40px;
    max-height: 60px;
    resize: vertical;
    font-family: inherit;
    box-sizing: border-box;
  }
  
  /* Bottom Navigation */
  .bottom-navigation {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #fff;
    padding: 16px 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .nav-buttons {
    display: flex;
    gap: 12px;
  }
  
  .btn-nav {
    padding: 8px 16px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    background: #fff;
    color: #495057;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-nav:hover:not(:disabled) {
    background: #e9ecef;
    border-color: #adb5bd;
  }
  
  .btn-nav:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .btn-next {
    background: #0d6efd;
    color: #fff;
    border-color: #0d6efd;
  }
  
  .btn-next:hover {
    background: #0b5ed7;
    border-color: #0b5ed7;
  }
  
  .action-buttons {
    display: flex;
    gap: 12px;
  }
  
  .btn-save,
  .btn-submit {
    padding: 8px 20px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
  }
  
  .btn-save {
    background: #6c757d;
    color: #fff;
  }
  
  .btn-save:hover {
    background: #5c636a;
  }
  
  .btn-submit {
    background: #28a745;
    color: #fff;
  }
  
  .btn-submit:hover {
    background: #218838;
  }
  
  /* Responsive Design */
  @media (max-width: 1200px) {
    .comparison-grid,
    .action-grid,
    .confirmation-grid {
      grid-template-columns: 1fr;
      gap: 16px;
    }
    
    .details-row {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .input-row {
      grid-template-columns: 1fr;
      gap: 8px;
    }
    
    .table-header, .table-row, .total-row {
      grid-template-columns: repeat(3, 1fr);
      gap: 4px;
    }
  }
  
  @media (max-width: 768px) {
    .pva-container {
      padding: 12px;
    }
    
    .steps-container {
      flex-direction: column;
      gap: 8px;
    }
    
    .step {
      justify-content: flex-start;
    }
    
    .details-row {
      grid-template-columns: 1fr;
    }
    
    .confirm-row {
      grid-template-columns: 1fr;
      gap: 4px;
    }
    
    .bottom-navigation {
      flex-direction: column;
      gap: 12px;
    }
    
    .nav-buttons,
    .action-buttons {
      width: 100%;
      justify-content: center;
    }
  }
  
  /* Custom Scrollbar */
  .step-content::-webkit-scrollbar {
    width: 6px;
  }
  
  .step-content::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }
  
  .step-content::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
  }
  
  .step-content::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
  }
  </style> 