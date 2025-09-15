<template>
  <div class="fraud-detector">
    <div class="fraud-header">
      <h3>🔍 Fraud Pattern Detection</h3>
      <div class="fraud-controls">
        <select v-model="timeRange" @change="refreshData" class="time-selector">
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
        <button @click="refreshData" class="refresh-btn" :disabled="loading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"></polyline>
            <polyline points="1 20 1 14 7 14"></polyline>
            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
          </svg>
          {{ loading ? 'Updating...' : 'Refresh' }}
        </button>
      </div>
    </div>

    <div class="fraud-content" v-if="fraudData">
      <!-- Critical Alerts -->
      <div class="critical-alerts" v-if="fraudData.critical_alerts && fraudData.critical_alerts.length > 0">
        <h4>🚨 Critical Fraud Alerts</h4>
        <div class="alert-list">
          <div v-for="alert in fraudData.critical_alerts" :key="alert.id" class="alert-item critical">
            <div class="alert-icon">⚠️</div>
            <div class="alert-content">
              <div class="alert-title">{{ alert.title }}</div>
              <div class="alert-description">{{ alert.description }}</div>
              <div class="alert-meta">
                <span class="alert-count">{{ alert.case_count }} cases</span>
                <span class="alert-amount">₹{{ formatAmount(alert.total_amount) }}</span>
                <span class="alert-time">{{ formatTimeAgo(alert.first_seen) }}</span>
              </div>
            </div>
            <div class="alert-risk">
              <div class="risk-score high">{{ alert.risk_score }}/100</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Real-time Fraud Stats -->
      <div class="fraud-stats">
        <h4>📊 Real-time Fraud Statistics</h4>
        <div class="stats-grid">
          <div class="stat-card suspicious">
            <div class="stat-icon">🔴</div>
            <div class="stat-info">
              <div class="stat-value">{{ fraudData.stats?.suspicious_entities || 0 }}</div>
              <div class="stat-label">Suspicious Entities</div>
              <div class="stat-change">+{{ fraudData.stats?.new_suspicious || 0 }} new</div>
            </div>
          </div>
          
          <div class="stat-card repeated">
            <div class="stat-icon">🔄</div>
            <div class="stat-info">
              <div class="stat-value">{{ fraudData.stats?.repeated_patterns || 0 }}</div>
              <div class="stat-label">Repeated Patterns</div>
              <div class="stat-change">{{ fraudData.stats?.pattern_growth || 0 }}% growth</div>
            </div>
          </div>
          
          <div class="stat-card networks">
            <div class="stat-icon">🕸️</div>
            <div class="stat-info">
              <div class="stat-value">{{ fraudData.stats?.fraud_networks || 0 }}</div>
              <div class="stat-label">Fraud Networks</div>
              <div class="stat-change">{{ fraudData.stats?.network_size || 0 }} avg size</div>
            </div>
          </div>
          
          <div class="stat-card velocity">
            <div class="stat-icon">⚡</div>
            <div class="stat-info">
              <div class="stat-value">{{ fraudData.stats?.high_velocity || 0 }}</div>
              <div class="stat-label">High Velocity Cases</div>
              <div class="stat-change">{{ fraudData.stats?.velocity_increase || 0 }}% faster</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Top Repeated Cases -->
      <div class="repeated-cases">
        <h4>🔁 Highly Repeated Case Patterns</h4>
        <div class="case-patterns">
          <div v-for="pattern in fraudData.repeated_cases?.slice(0, 8)" :key="pattern.pattern_id" 
               class="pattern-card" :class="getRiskClass(pattern.risk_level)">
            <div class="pattern-header">
              <div class="pattern-type">{{ pattern.pattern_type }}</div>
              <div class="pattern-risk">{{ pattern.risk_level }}</div>
            </div>
            <div class="pattern-details">
              <div class="pattern-entity">
                <strong>{{ pattern.entity_type }}:</strong> 
                <span class="entity-value">{{ pattern.entity_value }}</span>
              </div>
              <div class="pattern-stats">
                <span class="case-count">{{ pattern.case_count }} cases</span>
                <span class="time-span">{{ pattern.time_span }}</span>
                <span class="total-amount">₹{{ formatAmount(pattern.total_amount) }}</span>
              </div>
              <div class="pattern-locations" v-if="pattern.locations">
                <strong>Locations:</strong> {{ pattern.locations.slice(0, 3).join(', ') }}
                <span v-if="pattern.locations.length > 3">+{{ pattern.locations.length - 3 }} more</span>
              </div>
            </div>
            <div class="pattern-actions">
              <button @click="investigatePattern(pattern)" class="investigate-btn">
                🔍 Investigate
              </button>
              <button @click="viewCases(pattern)" class="view-cases-btn">
                📋 View Cases
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Fraud Velocity Chart -->
      <div class="fraud-velocity" v-if="fraudData.velocity_data">
        <h4>📈 Fraud Case Velocity ({{ timeRange }})</h4>
        <div class="velocity-chart">
          <div class="chart-container">
            <canvas ref="velocityChart" width="800" height="200"></canvas>
          </div>
          <div class="velocity-insights">
            <div class="insight-item">
              <div class="insight-label">Peak Hour:</div>
              <div class="insight-value">{{ fraudData.velocity_data.peak_hour || 'N/A' }}</div>
            </div>
            <div class="insight-item">
              <div class="insight-label">Avg Cases/Hour:</div>
              <div class="insight-value">{{ fraudData.velocity_data.avg_per_hour || 0 }}</div>
            </div>
            <div class="insight-item">
              <div class="insight-label">Trend:</div>
              <div class="insight-value" :class="getTrendClass(fraudData.velocity_data.trend)">
                {{ fraudData.velocity_data.trend || 'Stable' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Geographic Hotspots -->
      <div class="geo-hotspots" v-if="fraudData.geographic_patterns">
        <h4>🗺️ Geographic Fraud Hotspots</h4>
        <div class="hotspot-grid">
          <div v-for="hotspot in fraudData.geographic_patterns.slice(0, 6)" 
               :key="hotspot.location" class="hotspot-card">
            <div class="hotspot-location">{{ hotspot.location }}</div>
            <div class="hotspot-stats">
              <div class="hotspot-cases">{{ hotspot.case_count }} cases</div>
              <div class="hotspot-amount">₹{{ formatAmount(hotspot.total_amount) }}</div>
              <div class="hotspot-trend" :class="getTrendClass(hotspot.trend)">
                {{ hotspot.trend }}
              </div>
            </div>
            <div class="hotspot-risk">
              <div class="risk-indicator" :class="getRiskClass(hotspot.risk_level)"></div>
              <span>{{ hotspot.risk_level }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="fraud-loading">
      <div class="loading-spinner"></div>
      <p>Analyzing fraud patterns...</p>
    </div>

    <div v-if="error" class="fraud-error">
      <div class="error-icon">❌</div>
      <p>{{ error }}</p>
      <button @click="refreshData" class="retry-btn">Retry</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const fraudData = ref(null)
const loading = ref(false)
const error = ref(null)
const timeRange = ref('24h')
const velocityChart = ref(null)
const router = useRouter()

let refreshInterval = null

const emit = defineEmits(['patternDetected', 'alertTriggered'])

// Fetch fraud detection data
const fetchFraudData = async () => {
  loading.value = true
  error.value = null
  
  try {
    const token = localStorage.getItem('jwt')
    if (!token) return

    // Call the real fraud patterns API
    const response = await axios.get('/api/dashboard/fraud-patterns', {
      headers: { 'Authorization': `Bearer ${token}` },
      params: { time_range: timeRange.value }
    })

    if (response.data.success) {
      fraudData.value = response.data.data
      emit('patternDetected', response.data.data)
      
      // Draw velocity chart after data is loaded
      await nextTick()
      drawVelocityChart()
    }
    
  } catch (err) {
    error.value = 'Failed to load fraud detection data'
    console.error('Fraud detection error:', err)
    
    // Fallback to mock data if API fails
    const mockData = generateMockFraudData()
    fraudData.value = mockData
    emit('patternDetected', mockData)
    
    await nextTick()
    drawVelocityChart()
  } finally {
    loading.value = false
  }
}

// Generate mock fraud data for demonstration
const generateMockFraudData = () => {
  const timeMultiplier = timeRange.value === '24h' ? 1 : timeRange.value === '7d' ? 7 : 30
  
  return {
    critical_alerts: [
      {
        id: 1,
        title: 'Suspicious Mobile Number Pattern',
        description: 'Mobile number +91-9876543210 linked to 15+ cases across multiple states',
        case_count: 15,
        total_amount: 2500000,
        first_seen: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        risk_score: 95
      },
      {
        id: 2,
        title: 'Account Number Reuse',
        description: 'Beneficiary account 1234567890 receiving funds from 8 different victims',
        case_count: 8,
        total_amount: 1200000,
        first_seen: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
        risk_score: 88
      },
      {
        id: 3,
        title: 'Geographic Clustering',
        description: 'Unusual spike in fraud cases from Mumbai region',
        case_count: 23,
        total_amount: 4500000,
        first_seen: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
        risk_score: 82
      }
    ],
    stats: {
      suspicious_entities: Math.floor(45 * timeMultiplier),
      new_suspicious: Math.floor(8 * timeMultiplier),
      repeated_patterns: Math.floor(12 * timeMultiplier),
      pattern_growth: Math.floor(15 + Math.random() * 20),
      fraud_networks: Math.floor(6 * timeMultiplier),
      network_size: Math.floor(8 + Math.random() * 12),
      high_velocity: Math.floor(18 * timeMultiplier),
      velocity_increase: Math.floor(25 + Math.random() * 30)
    },
    repeated_cases: [
      {
        pattern_id: 'p1',
        pattern_type: 'Mobile Reuse',
        entity_type: 'Mobile Number',
        entity_value: '+91-9876543210',
        case_count: 15,
        time_span: '3 days',
        total_amount: 2500000,
        risk_level: 'high',
        locations: ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata']
      },
      {
        pattern_id: 'p2',
        pattern_type: 'Account Clustering',
        entity_type: 'Account Number',
        entity_value: '1234567890',
        case_count: 8,
        time_span: '2 days',
        total_amount: 1200000,
        risk_level: 'high',
        locations: ['Mumbai', 'Pune']
      },
      {
        pattern_id: 'p3',
        pattern_type: 'Name Similarity',
        entity_type: 'Beneficiary Name',
        entity_value: 'Raj Kumar*',
        case_count: 12,
        time_span: '5 days',
        total_amount: 1800000,
        risk_level: 'medium',
        locations: ['Delhi', 'Gurgaon', 'Noida']
      },
      {
        pattern_id: 'p4',
        pattern_type: 'Location Hotspot',
        entity_type: 'Location',
        entity_value: 'Mumbai Central',
        case_count: 23,
        time_span: '1 day',
        total_amount: 4500000,
        risk_level: 'high',
        locations: ['Mumbai']
      }
    ],
    velocity_data: {
      peak_hour: '14:00-15:00',
      avg_per_hour: Math.floor(5 * timeMultiplier),
      trend: Math.random() > 0.5 ? 'Increasing' : 'Stable',
      hourly_data: Array.from({length: 24}, (_, i) => ({
        hour: i,
        cases: Math.floor(Math.random() * 10 * timeMultiplier) + 1
      }))
    },
    geographic_patterns: [
      {
        location: 'Mumbai',
        case_count: 45,
        total_amount: 8500000,
        risk_level: 'high',
        trend: 'Increasing'
      },
      {
        location: 'Delhi',
        case_count: 32,
        total_amount: 6200000,
        risk_level: 'high',
        trend: 'Stable'
      },
      {
        location: 'Bangalore',
        case_count: 28,
        total_amount: 4800000,
        risk_level: 'medium',
        trend: 'Decreasing'
      },
      {
        location: 'Chennai',
        case_count: 21,
        total_amount: 3200000,
        risk_level: 'medium',
        trend: 'Stable'
      }
    ]
  }
}

// Draw velocity chart using Canvas
const drawVelocityChart = () => {
  if (!velocityChart.value || !fraudData.value?.velocity_data) return
  
  const canvas = velocityChart.value
  const ctx = canvas.getContext('2d')
  const data = fraudData.value.velocity_data.hourly_data
  
  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  const padding = 40
  const chartWidth = canvas.width - 2 * padding
  const chartHeight = canvas.height - 2 * padding
  const maxValue = Math.max(...data.map(d => d.cases))
  
  // Draw grid
  ctx.strokeStyle = '#e5e7eb'
  ctx.lineWidth = 1
  
  for (let i = 0; i <= 5; i++) {
    const y = padding + (chartHeight / 5) * i
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(canvas.width - padding, y)
    ctx.stroke()
  }
  
  // Draw chart line
  ctx.strokeStyle = '#ef4444'
  ctx.lineWidth = 3
  ctx.fillStyle = 'rgba(239, 68, 68, 0.1)'
  
  ctx.beginPath()
  data.forEach((point, index) => {
    const x = padding + (chartWidth / (data.length - 1)) * index
    const y = padding + chartHeight - (point.cases / maxValue) * chartHeight
    
    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  ctx.stroke()
  
  // Fill area under curve
  ctx.lineTo(canvas.width - padding, padding + chartHeight)
  ctx.lineTo(padding, padding + chartHeight)
  ctx.closePath()
  ctx.fill()
  
  // Draw data points
  ctx.fillStyle = '#ef4444'
  data.forEach((point, index) => {
    const x = padding + (chartWidth / (data.length - 1)) * index
    const y = padding + chartHeight - (point.cases / maxValue) * chartHeight
    
    ctx.beginPath()
    ctx.arc(x, y, 4, 0, 2 * Math.PI)
    ctx.fill()
  })
  
  // Draw labels
  ctx.fillStyle = '#6b7280'
  ctx.font = '12px Arial'
  ctx.textAlign = 'center'
  
  for (let i = 0; i < data.length; i += 4) {
    const x = padding + (chartWidth / (data.length - 1)) * i
    ctx.fillText(`${i}:00`, x, canvas.height - 10)
  }
}

// Event handlers
const investigatePattern = (pattern) => {
  console.log('Investigating pattern:', pattern)
  emit('alertTriggered', {
    type: 'investigate',
    pattern: pattern
  })
}

const viewCases = (pattern) => {
  console.log('Viewing cases for pattern:', pattern)
  
  // Navigate to case details page with filter based on pattern
  if (pattern.case_ids && pattern.case_ids.length > 0) {
    // If we have specific case IDs, navigate to the first case
    const firstCaseId = pattern.case_ids[0]
    
    // Navigate to the case risk review page for the specific case
    router.push({
      name: 'CaseRiskReview',
      params: { case_id: firstCaseId }
    })
  } else {
    // Navigate to case list page with search filter
    const searchQuery = pattern.entity_value || pattern.title || 'fraud_pattern'
    router.push({
      name: 'CaseDetails',
      query: { 
        search: searchQuery,
        filter: pattern.entity_type || 'all'
      }
    })
  }
}

const refreshData = () => {
  fetchFraudData()
}

// Utility functions
const formatAmount = (amount) => {
  if (!amount) return '0'
  return new Intl.NumberFormat('en-IN').format(Math.round(amount))
}

const formatTimeAgo = (date) => {
  if (!date) return ''
  const now = new Date()
  const diff = now - new Date(date)
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (hours > 0) return `${hours}h ago`
  return `${minutes}m ago`
}

const getRiskClass = (riskLevel) => {
  switch (riskLevel?.toLowerCase()) {
    case 'high': return 'high-risk'
    case 'medium': return 'medium-risk'
    case 'low': return 'low-risk'
    default: return ''
  }
}

const getTrendClass = (trend) => {
  switch (trend?.toLowerCase()) {
    case 'increasing': return 'trend-up'
    case 'decreasing': return 'trend-down'
    case 'stable': return 'trend-stable'
    default: return ''
  }
}

// Lifecycle
onMounted(() => {
  fetchFraudData()
  
  // Auto-refresh every 2 minutes
  refreshInterval = setInterval(() => {
    fetchFraudData()
  }, 2 * 60 * 1000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

defineExpose({
  refreshData
})
</script>

<style scoped>
.fraud-detector {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.fraud-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #fef2f2 0%, #fff5f5 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.fraud-header h3 {
  margin: 0;
  color: #dc2626;
  font-size: 1.25rem;
  font-weight: 600;
}

.fraud-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.time-selector {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  background: white;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #b91c1c;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.fraud-content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Critical Alerts */
.critical-alerts h4 {
  margin: 0 0 1rem 0;
  color: #dc2626;
  font-size: 1.125rem;
  font-weight: 600;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  border: 2px solid #fee2e2;
  border-radius: 8px;
  background: #fef2f2;
}

.alert-item.critical {
  border-color: #fecaca;
  background: linear-gradient(135deg, #fef2f2 0%, #fef7f7 100%);
}

.alert-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 600;
  color: #dc2626;
  margin-bottom: 0.25rem;
}

.alert-description {
  color: #6b7280;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.alert-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #9ca3af;
}

.alert-count, .alert-amount, .alert-time {
  font-weight: 500;
}

.alert-risk {
  flex-shrink: 0;
}

.risk-score {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
  min-width: 60px;
}

.risk-score.high {
  background: #dc2626;
  color: white;
}

/* Fraud Stats */
.fraud-stats h4 {
  margin: 0 0 1rem 0;
  color: #111827;
  font-size: 1.125rem;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-card.suspicious {
  background: linear-gradient(135deg, #fef2f2 0%, #fff5f5 100%);
  border-color: #fecaca;
}

.stat-card.repeated {
  background: linear-gradient(135deg, #fefbeb 0%, #fffbeb 100%);
  border-color: #fed7aa;
}

.stat-card.networks {
  background: linear-gradient(135deg, #f0f9ff 0%, #f0f9ff 100%);
  border-color: #bae6fd;
}

.stat-card.velocity {
  background: linear-gradient(135deg, #f3f4f6 0%, #f9fafb 100%);
  border-color: #d1d5db;
}

.stat-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.stat-change {
  font-size: 0.75rem;
  color: #dc2626;
  font-weight: 500;
}

/* Repeated Cases */
.repeated-cases h4 {
  margin: 0 0 1rem 0;
  color: #111827;
  font-size: 1.125rem;
  font-weight: 600;
}

.case-patterns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.pattern-card {
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  transition: all 0.2s;
}

.pattern-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.pattern-card.high-risk {
  border-color: #fecaca;
  background: linear-gradient(135deg, #fef2f2 0%, #fff5f5 100%);
}

.pattern-card.medium-risk {
  border-color: #fed7aa;
  background: linear-gradient(135deg, #fefbeb 0%, #fffbeb 100%);
}

.pattern-card.low-risk {
  border-color: #bbf7d0;
  background: linear-gradient(135deg, #f0fdf4 0%, #f7fee7 100%);
}

.pattern-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.pattern-type {
  font-weight: 600;
  color: #111827;
}

.pattern-risk {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.pattern-card.high-risk .pattern-risk {
  background: #dc2626;
  color: white;
}

.pattern-card.medium-risk .pattern-risk {
  background: #d97706;
  color: white;
}

.pattern-card.low-risk .pattern-risk {
  background: #059669;
  color: white;
}

.pattern-details {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pattern-entity {
  font-size: 0.875rem;
  color: #374151;
}

.entity-value {
  font-weight: 600;
  color: #111827;
}

.pattern-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.case-count, .time-span, .total-amount {
  font-weight: 500;
}

.pattern-locations {
  font-size: 0.75rem;
  color: #6b7280;
}

.pattern-actions {
  display: flex;
  gap: 0.5rem;
}

.investigate-btn, .view-cases-btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.investigate-btn {
  background: #dc2626;
  color: white;
}

.investigate-btn:hover {
  background: #b91c1c;
}

.view-cases-btn {
  background: #e5e7eb;
  color: #374151;
}

.view-cases-btn:hover {
  background: #d1d5db;
}

/* Fraud Velocity */
.fraud-velocity h4 {
  margin: 0 0 1rem 0;
  color: #111827;
  font-size: 1.125rem;
  font-weight: 600;
}

.velocity-chart {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
}

.chart-container {
  flex: 1;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
}

.velocity-insights {
  width: 200px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.insight-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.insight-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.insight-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

.trend-up {
  color: #dc2626;
}

.trend-down {
  color: #059669;
}

.trend-stable {
  color: #6b7280;
}

/* Geographic Hotspots */
.geo-hotspots h4 {
  margin: 0 0 1rem 0;
  color: #111827;
  font-size: 1.125rem;
  font-weight: 600;
}

.hotspot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.hotspot-card {
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.hotspot-location {
  font-weight: 600;
  color: #111827;
  font-size: 1rem;
}

.hotspot-stats {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.hotspot-cases, .hotspot-amount {
  font-size: 0.875rem;
  color: #6b7280;
}

.hotspot-trend {
  font-size: 0.75rem;
  font-weight: 500;
}

.hotspot-risk {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
}

.risk-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.risk-indicator.high-risk {
  background: #dc2626;
}

.risk-indicator.medium-risk {
  background: #d97706;
}

.risk-indicator.low-risk {
  background: #059669;
}

/* Loading and Error States */
.fraud-loading, .fraud-error {
  padding: 3rem;
  text-align: center;
  color: #6b7280;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #dc2626;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.retry-btn {
  padding: 0.5rem 1rem;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 1rem;
}

.retry-btn:hover {
  background: #b91c1c;
}

/* Responsive */
@media (max-width: 768px) {
  .fraud-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .fraud-controls {
    justify-content: space-between;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .case-patterns {
    grid-template-columns: 1fr;
  }
  
  .velocity-chart {
    flex-direction: column;
  }
  
  .velocity-insights {
    width: 100%;
  }
  
  .hotspot-grid {
    grid-template-columns: 1fr;
  }
  
  .pattern-actions {
    flex-direction: column;
  }
}
</style>
