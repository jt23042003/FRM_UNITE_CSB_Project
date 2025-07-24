<template>
  <div class="dashboard-wrapper">
    <div class="dashboard-container">
      <!-- Header -->
      <header class="dashboard-header">
        <div class="header-content">
          <h2>Dashboard</h2>
          <div class="user-info">
            <span class="user-name">{{ userName }}</span>
            <div class="user-avatar">
              <img src="@/assets/unite_hub_tech_logo.png" alt="Profile" />
            </div>
          </div>
        </div>
      </header>

      <!-- Main Content -->
      <main class="dashboard-content">
        <!-- Stats Cards -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
              </svg>
            </div>
            <div class="stat-info">
              <h3>{{ metrics.totalCases || 0 }}</h3>
              <p>Total Cases</p>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2v20M2 12h20" />
              </svg>
            </div>
            <div class="stat-info">
              <h3>{{ metrics.newCases || 0 }}</h3>
              <p>New Cases</p>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <div class="stat-info">
              <h3>{{ metrics.completedCases || 0 }}</h3>
              <p>Completed</p>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon warning">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 12h3v8h6v-6h2v6h6v-8h3L12 2z" />
              </svg>
            </div>
            <div class="stat-info">
              <h3>{{ metrics.highRiskCases || 0 }}</h3>
              <p>High Risk</p>
            </div>
          </div>
        </div>

        <!-- Main Grid -->
        <div class="main-grid">
          <!-- Recent Cases -->
          <div class="panel cases-panel">
            <div class="panel-header">
              <h3>Recent Cases</h3>
              <div class="panel-actions">
                <select v-model="caseFilter" class="filter-select">
                  <option value="all">All Cases</option>
                  <option value="high">High Risk</option>
                  <option value="medium">Medium Risk</option>
                  <option value="low">Low Risk</option>
                </select>
              </div>
            </div>
            <div class="table-container">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Case ID</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Risk Level</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="caseItem in filteredCases" :key="caseItem.case_id">
                    <td>
                      <router-link :to="getCaseRoute(caseItem.case_type, caseItem.case_id)" class="case-link">
                        {{ caseItem.case_id }}
                      </router-link>
                    </td>
                    <td>{{ caseItem.case_type || '-' }}</td>
                    <td>
                      <span :class="['status-badge', caseItem.status ? caseItem.status.toLowerCase().replace(/ /g,'-') : '']">
                        {{ caseItem.status || '-' }}
                      </span>
                    </td>
                    <td>
                      <span :class="['risk-badge', caseItem.risk_level ? caseItem.risk_level.toLowerCase() : '']">
                        {{ caseItem.risk_level || '-' }}
                      </span>
                    </td>
                    <td>{{ caseItem.date_created ? formatDate(caseItem.date_created) : '-' }}</td>
                  </tr>
                  <tr v-if="filteredCases.length === 0">
                    <td colspan="5" style="text-align:center; padding: 20px;">No cases found.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Case Distribution -->
          <div class="panel distribution-panel">
            <div class="panel-header">
              <h3>Case Distribution</h3>
              <div class="panel-actions">
                <select v-model="timeRange" class="filter-select">
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                  <option value="quarter">This Quarter</option>
                </select>
              </div>
            </div>
            <div class="distribution-list">
              <div v-for="(count, type) in caseTypes" :key="type" class="distribution-item">
                <div class="item-header">
                  <span class="type-label">{{ type }}</span>
                  <span class="type-count">{{ count }}</span>
                </div>
                <div class="progress-bar">
                  <div class="progress" :style="{ width: getPercentage(count) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { API_ENDPOINTS } from '../config/api.js';
import axios from 'axios';
import '../assets/Dashboard.css';

const router = useRouter();

// Get the appropriate route for each case type
const getCaseRoute = (caseType, caseId) => {
  const routeMap = {
    'VM': 'operational-action',
    'BM': 'beneficiary-action',
    'PMA': 'pma-action',
    'PVA': 'pva-action',
    'PSA': 'psa-action',
    'ECBT': 'ecbt-action',
    'ECBNT': 'ecbnt-action',
    'NAB': 'nab-action'
  };

  return `/${routeMap[caseType] || 'case-details'}/${caseId}`;
};

// State
const userName = ref('Admin User');
const timeRange = ref('month');
const caseFilter = ref('all');
const loading = ref(false);
const error = ref(null);

// Mock data - Replace with API calls
const metrics = ref({
  totalCases: 0,
  newCases: 0,
  completedCases: 0,
  highRiskCases: 0
});

const caseTypes = ref({
  'VM': 0,
  'BM': 0,
  'PMA': 0,
  'NAB': 0,
  'PSA': 0,
  'ECBT': 0,
  'ECBNT': 0
});

const recentCases = ref([]);

// Computed
const getPercentage = (count) => {
  const total = Object.values(caseTypes.value).reduce((sum, curr) => sum + curr, 0);
  return total > 0 ? (count / total) * 100 : 0;
};

const filteredCases = computed(() => {
  if (caseFilter.value === 'all') return recentCases.value;
  return recentCases.value.filter(c => 
    c.riskLevel.toLowerCase() === caseFilter.value
  );
});

// Format date helper
const formatDate = (date) => {
  return new Date(date).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
};

// Fetch dashboard data
const fetchDashboardData = async () => {
  loading.value = true;
  error.value = null;
  
  try {
    const token = localStorage.getItem('jwt');
    if (!token) throw new Error('No authentication token found');

    const response = await axios.get(API_ENDPOINTS.NEW_CASE_LIST, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.data && Array.isArray(response.data.cases)) {
      const cases = response.data.cases;
      
      // Update metrics
      metrics.value = {
        totalCases: cases.length,
        newCases: cases.filter(c => c.status === 'New').length,
        completedCases: cases.filter(c => c.status === 'Closed').length,
        highRiskCases: cases.filter(c => c.risk_level === 'High').length
      };

      // Update case types distribution
      Object.keys(caseTypes.value).forEach(type => {
        caseTypes.value[type] = cases.filter(c => c.case_type === type).length;
      });

      // Update recent cases
      recentCases.value = cases
        .slice(0, 10)
        .map(c => ({
          id: c.case_id,
          type: c.case_type,
          status: c.status,
          date: c.created_at,
          riskLevel: c.risk_level || 'Medium'
        }));
    }
  } catch (err) {
    error.value = err.message;
    if (err.response?.status === 401) {
      router.push('/login');
    }
  } finally {
    loading.value = false;
  }
};

// Initialize dashboard
onMounted(fetchDashboardData);
</script>

<style>
.dashboard-wrapper {
  height: 100%;
  width: 100%;
  overflow-y: auto;
}

@import '../assets/Dashboard.css';
</style>
  