<template>
  <div class="simple-dashboard">
    <div class="dashboard-container">
      <header class="dashboard-header">
        <div class="header-content">
          <h2>Welcome</h2>
          <div class="user-info">
            <span class="user-name">{{ userName }}</span>
            <div class="user-avatar">
              <img src="@/assets/unite_hub_tech_logo.png" alt="Profile" />
            </div>
          </div>
        </div>
      </header>
      
      <main class="dashboard-content">
        <div class="welcome-message">
          <h3>Welcome to UNITE Hub Technologies</h3>
          <p>You have access to view case details. Use the navigation to explore cases.</p>
        </div>
        <div v-if="loading" class="skeleton-table" style="margin-bottom: 14px;">
          <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
          <div class="row"><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div><div class="cell skeleton skeleton-line"></div></div>
        </div>

        <div class="analytics-cards" v-if="analytics">
          <div class="card">
            <div class="card-title">My Total Cases</div>
            <div class="card-value">{{ analytics.overview.total_cases }}</div>
          </div>
          <div class="card">
            <div class="card-title">Open</div>
            <div class="card-value">{{ analytics.overview.open_cases }}</div>
          </div>
          <div class="card">
            <div class="card-title">Closed</div>
            <div class="card-value">{{ analytics.overview.closed_cases }}</div>
          </div>
          <div class="card">
            <div class="card-title">This Month</div>
            <div class="card-value">{{ analytics.overview.monthly_created }}</div>
          </div>
          <div class="card">
            <div class="card-title">Avg Resolution</div>
            <div class="card-value">{{ analytics.overview.average_resolution_days }} days</div>
          </div>
          <div class="card">
            <div class="card-title">Funds Saved</div>
            <div class="card-value">₹{{ (analytics.overview.funds_saved_total || 0).toLocaleString('en-IN') }}</div>
          </div>
        </div>

        <div class="recent-cases" v-if="analytics?.recent_cases?.length">
          <h4>My Recent Cases</h4>
          <ul>
            <li v-for="c in analytics.recent_cases" :key="c.case_id">
              <span class="badge">{{ c.status }}</span>
              <span class="case-type">{{ c.case_type }}</span>
              <span class="case-date">{{ formatDate(c.creation_date) }}</span>
            </li>
          </ul>
        </div>
        <div v-else-if="!loading" class="empty-state" style="margin: 12px 0;">
          <div class="icon">🗂️</div>
          <div class="title">No recent cases</div>
          <div class="hint">Your recently viewed or created cases will show up here.</div>
        </div>

        <div class="status-bars" v-if="analytics?.status_distribution">
          <h4>Status Distribution</h4>
          <div v-for="(count, status) in analytics.status_distribution" :key="status" class="bar-row">
            <span class="label">{{ status }}</span>
            <div class="bar">
              <div class="fill" :style="{ width: barWidth(count) }"></div>
            </div>
            <span class="count">{{ count }}</span>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

const userName = ref('');
const analytics = ref(null);
const loading = ref(true);
const error = ref(null);

const fetchUserName = async () => {
  try {
    const token = localStorage.getItem('jwt');
    if (!token) return;
    const response = await axios.get('/api/new-case-list', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (response.data && response.data.logged_in_user_name) {
      userName.value = response.data.logged_in_user_name;
    }
    if (response.data && response.data.logged_in_user_type) {
      localStorage.setItem('user_type', response.data.logged_in_user_type);
    }
  } catch (err) {
    console.error('Failed to fetch user name:', err);
  }
};

const fetchUserAnalytics = async () => {
  loading.value = true;
  error.value = null;
  try {
    const token = localStorage.getItem('jwt');
    if (!token) return;
    const resp = await axios.get('/api/dashboard/user-analytics', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (resp.data && resp.data.success) {
      analytics.value = resp.data.data;
    }
  } catch (err) {
    console.error('Failed to fetch user analytics:', err);
    error.value = err.message || 'Failed to load analytics';
  } finally {
    loading.value = false;
  }
};

const maxStatusCount = computed(() => {
  if (!analytics.value?.status_distribution) return 1;
  return Math.max(...Object.values(analytics.value.status_distribution));
});

const barWidth = (count) => `${Math.round((count / maxStatusCount.value) * 100)}%`;
const formatDate = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: '2-digit' });
};

onMounted(async () => {
  await fetchUserName();
  await fetchUserAnalytics();
});
</script>

<style scoped>
.simple-dashboard {
  min-height: 100vh;
  background: #f8fafc;
}

.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.dashboard-header {
  background: #fff;
  border-radius: 12px;
  padding: 1.5rem 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0;
  color: #1e293b;
  font-size: 1.875rem;
  font-weight: 600;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-name {
  font-size: 1.125rem;
  font-weight: 500;
  color: #475569;
}

.user-avatar img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #e2e8f0;
}

.dashboard-content {
  background: #fff;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.welcome-message {
  text-align: center;
  padding: 1.5rem 1rem 2rem;
}

.analytics-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.card {
  background: #f1f5f9;
  border-radius: 10px;
  padding: 1rem;
}

.card-title {
  font-size: 0.85rem;
  color: #64748b;
}

.card-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #0f172a;
}

.recent-cases h4,
.status-bars h4 {
  margin: 1rem 0;
  color: #1e293b;
}

.recent-cases ul {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem 0;
}

.recent-cases li {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px dashed #e2e8f0;
}

.badge {
  background: #e2e8f0;
  color: #0f172a;
  border-radius: 999px;
  padding: 0.15rem 0.6rem;
  font-size: 0.75rem;
}

.case-type { color: #475569; }
.case-date { color: #64748b; margin-left: auto; }

.status-bars .bar-row {
  display: grid;
  grid-template-columns: 120px 1fr 48px;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.status-bars .bar {
  background: #e2e8f0;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
}

.status-bars .fill {
  background: #3b82f6;
  height: 10px;
}

.status-bars .label { color: #334155; font-size: 0.9rem; }
.status-bars .count { color: #334155; font-weight: 600; text-align: right; }
</style>
