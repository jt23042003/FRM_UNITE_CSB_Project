<template>
  <div class="dashboard-wrapper">
    <div class="dashboard-container">
      <!-- Header -->
      <header class="dashboard-header">
        <div class="header-content">
          <h2>Unite Hub Analytics Dashboard</h2>
          <div class="header-actions">
            <div class="refresh-info"><br></br>
              <span v-if="lastRefresh" class="last-refresh">
                Last updated: {{ formatTime(lastRefresh) }}
              </span>
              <button @click="refreshDashboard" class="refresh-btn" :disabled="loading">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'rotating': loading }">
                  <polyline points="23 4 23 10 17 10"></polyline>
                  <polyline points="1 20 1 14 7 14"></polyline>
                  <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
                </svg>
                {{ loading ? 'Refreshing...' : 'Refresh' }}
              </button>
            </div>
                      <div class="user-info">
              <span class="user-name">{{ userName }}</span>
              <span v-if="userType" class="user-type">{{ userType }}</span>
              <div class="user-avatar">
                <img src="@/assets/unite_hub_tech_logo.png" alt="Profile" />
              </div>
            </div>
          </div>
        </div>
      </header>

      <!-- Main Content -->
      <main class="dashboard-content" v-if="!loading">
        <!-- Enhanced Stats Grid -->
        <div class="stats-grid">
          <div class="stat-card funds-saved">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
                <text x="12" y="17" text-anchor="middle" font-size="16" font-weight="700" fill="currentColor">₹</text>
              </svg>
            </div>
            <div class="stat-info">
              <h3>₹{{ (analytics?.overview?.funds_saved_total || 0).toLocaleString('en-IN') }}</h3>
              <p>Funds Saved</p>
              <div class="stat-trend positive">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline points="17 6 23 6 23 12"/>
                </svg>
                <span>Aggregate</span>
              </div>
            </div>
          </div>
          <div class="stat-card total-cases">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
            </div>
            <div class="stat-info">
              <h3>{{ analytics?.overview?.total_cases || 0 }}</h3>
              <p>Total Cases</p>
              <div class="stat-trend positive">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline points="17 6 23 6 23 12"/>
                </svg>
                <span>+12% from last month</span>
              </div>
            </div>
          </div>

          <div class="stat-card new-cases">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="16"/>
                <line x1="8" y1="12" x2="16" y2="12"/>
              </svg>
            </div>
            <div class="stat-info">
              <h3>{{ analytics?.overview?.new_cases || 0 }}</h3>
              <p>New Cases</p>
              <div class="stat-trend neutral">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                <span>No change</span>
              </div>
            </div>
          </div>

          <div class="stat-card closed-cases">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </div>
            <div class="stat-info">
              <h3>{{ analytics?.overview?.closed_cases || 0 }}</h3>
              <p>Closed Cases</p>
              <div class="stat-trend positive">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline points="17 6 23 6 23 12"/>
                </svg>
                <span>+8% from last month</span>
              </div>
            </div>
          </div>

          <div class="stat-card assigned-cases">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div class="stat-info">
              <h3>{{ analytics?.overview?.assigned_cases || 0 }}</h3>
              <p>Assigned Cases</p>
              <div class="stat-trend positive">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline points="17 6 23 6 23 12"/>
                </svg>
                <span>+15% efficiency</span>
              </div>
            </div>
          </div>

          <div class="stat-card operational-cases">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
            </div>
            <div class="stat-info">
              <h3>{{ analytics?.overview?.operational_cases || 0 }}</h3>
              <p>Operational Cases</p>
              <div class="stat-percentage">
                {{ getOperationalPercentage() }}% of total
              </div>
            </div>
          </div>

          <div class="stat-card resolution-time">
            <div class="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <div class="stat-info">
              <h3>{{ averageResolutionTime }}</h3>
              <p>Avg Resolution Time</p>
              <div class="stat-trend positive">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <polyline points="1 18 8.5 10.5 13.5 15.5 23 6"/>
                  <polyline points="17 6 23 6 23 12"/>
                </svg>
                <span>-2 days improved</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Real-time Metrics -->
        <div class="real-time-section" v-if="realTimeMetrics">
          <div class="section-header">
            <h3>Real-time Metrics</h3>
            <span class="last-updated">Last updated: {{ formatTime(realTimeMetrics.timestamp) }}</span>
          </div>
          <div class="real-time-grid">
            <div class="real-time-card">
              <div class="real-time-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="16"/>
                  <line x1="8" y1="12" x2="16" y2="12"/>
                </svg>
              </div>
              <div class="real-time-info">
                <h4>{{ realTimeMetrics.cases_last_24h }}</h4>
                <p>Cases Created (24h)</p>
              </div>
            </div>
            <div class="real-time-card">
              <div class="real-time-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
              </div>
              <div class="real-time-info">
                <h4>{{ realTimeMetrics.cases_closed_last_24h }}</h4>
                <p>Cases Closed (24h)</p>
              </div>
            </div>
            <div class="real-time-card">
              <div class="real-time-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <div class="real-time-info">
                <h4>{{ realTimeMetrics.active_cases }}</h4>
                <p>Active Cases</p>
              </div>
            </div>
            <div class="real-time-card">
              <div class="real-time-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <div class="real-time-info">
                <h4>{{ realTimeMetrics.cases_assigned_last_hour }}</h4>
                <p>Assigned (1h)</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Fraud Pattern Detection -->
        <FraudPatternDetector 
          @patternDetected="handleFraudPatternDetected"
          @alertTriggered="handleFraudAlert"
        />

        <!-- Network Visualization Section -->
        <div class="network-section">
          <div class="section-header">
            <h3>Entity Relationship Network</h3>
            <p>Interactive visualization of fraud patterns and entity connections</p>
          </div>
          <NetworkVisualization 
            :height="600" 
            @nodeClick="handleNodeClick"
            @dataLoaded="handleNetworkDataLoaded"
          />
        </div>

        <!-- Performance Metrics -->
        <div class="performance-section">
          <div class="section-header">
            <h3>Performance Insights</h3>
            <p>Key performance indicators and trends</p>
          </div>
          <div class="performance-grid">
            <div class="performance-card">
              <div class="performance-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                </svg>
              </div>
              <div class="performance-info">
                <h4>{{ getClosureRate() }}%</h4>
                <p>Case Closure Rate</p>
                <div class="performance-trend positive">+5% this month</div>
              </div>
            </div>
            
            <div class="performance-card">
              <div class="performance-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
              </div>
              <div class="performance-info">
                <h4>{{ averageResolutionTime }}</h4>
                <p>Avg Resolution Time</p>
                <div class="performance-trend positive">-8% improvement</div>
              </div>
            </div>
            
            <div class="performance-card">
              <div class="performance-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <div class="performance-info">
                <h4>{{ getActiveUsers() }}</h4>
                <p>Active Investigators</p>
                <div class="performance-trend neutral">Same as last week</div>
              </div>
            </div>
            
            <div class="performance-card">
              <div class="performance-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              </div>
              <div class="performance-info">
                <h4>{{ getWorkloadBalance() }}%</h4>
                <p>Workload Balance</p>
                <div class="performance-trend positive">Well distributed</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Advanced Analytics Section -->
        <div class="advanced-analytics-section" v-if="advancedAnalytics">
          <div class="section-header">
            <h3>Advanced Analytics</h3>
          </div>
          
          <div class="advanced-grid">
            <!-- Department Performance -->
            <div class="panel chart-panel">
              <div class="panel-header">
                <h4>Department Performance</h4>
              </div>
              <div class="chart-container">
                <div class="department-performance">
                  <div v-for="dept in advancedAnalytics.department_performance" :key="dept.dept" class="dept-row">
                    <div class="dept-info">
                      <span class="dept-name">{{ dept.dept || 'Unknown' }}</span>
                      <span class="dept-cases">{{ dept.total_cases }} cases</span>
                    </div>
                    <div class="dept-metrics">
                      <div class="metric">
                        <span class="metric-label">Closure Rate</span>
                        <span class="metric-value">{{ dept.closure_rate }}%</span>
                      </div>
                      <div class="metric">
                        <span class="metric-label">Avg Resolution</span>
                        <span class="metric-value">{{ dept.avg_resolution_days || 0 }} days</span>
                      </div>
                    </div>
                    <div class="dept-progress">
                      <div class="progress-bar">
                        <div class="progress-fill" :style="{ width: dept.closure_rate + '%' }"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Case Aging Analysis -->
            <div class="panel chart-panel">
              <div class="panel-header">
                <h4>Case Aging Analysis</h4>
              </div>
              <div class="chart-container">
                <div class="aging-chart">
                  <div v-for="age in advancedAnalytics.case_aging" :key="age.age_bucket" class="age-row">
                    <div class="age-info">
                      <span class="age-bucket">{{ age.age_bucket }}</span>
                      <span class="age-count">{{ age.case_count }} cases</span>
                    </div>
                    <div class="age-progress">
                      <div class="progress-bar">
                        <div class="progress-fill aging" :style="{ width: getAgingPercentage(age.case_count) + '%' }"></div>
                      </div>
                    </div>
                    <div class="age-closure">
                      <span class="closure-rate">{{ age.closure_rate }}% closed</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Top Performers -->
            <div class="panel chart-panel">
              <div class="panel-header">
                <h4>Top Performers (Last 30 Days)</h4>
              </div>
              <div class="chart-container">
                <div class="top-performers">
                  <div v-for="(performer, index) in advancedAnalytics.top_performers" :key="performer.assigned_to" class="performer-row">
                    <div class="performer-rank">#{{ index + 1 }}</div>
                    <div class="performer-info">
                      <span class="performer-name">{{ performer.assigned_to }}</span>
                      <span class="performer-dept">{{ performer.dept }}</span>
                    </div>
                    <div class="performer-metrics">
                      <div class="metric">
                        <span class="metric-value">{{ performer.cases_closed }}</span>
                        <span class="metric-label">Closed</span>
                      </div>
                      <div class="metric">
                        <span class="metric-value">{{ performer.success_rate }}%</span>
                        <span class="metric-label">Success</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Workload Distribution -->
            <div class="panel chart-panel wide">
              <div class="panel-header">
                <h4>Current Workload Distribution</h4>
              </div>
              <div class="chart-container">
                <div class="workload-chart">
                  <div v-for="workload in advancedAnalytics.workload_distribution.slice(0, 10)" :key="workload.assigned_to" class="workload-row">
                    <div class="workload-user">
                      <span class="user-name">{{ workload.assigned_to }}</span>
                      <span class="user-dept">{{ workload.dept }}</span>
                    </div>
                    <div class="workload-bars">
                      <div class="bar-group">
                        <div class="bar-label">Active</div>
                        <div class="bar">
                          <div class="bar-fill active" :style="{ width: getWorkloadPercentage(workload.active_cases) + '%' }"></div>
                        </div>
                        <span class="bar-value">{{ workload.active_cases }}</span>
                      </div>
                      <div class="bar-group">
                        <div class="bar-label">Closed</div>
                        <div class="bar">
                          <div class="bar-fill closed" :style="{ width: getWorkloadPercentage(workload.closed_cases) + '%' }"></div>
                        </div>
                        <span class="bar-value">{{ workload.closed_cases }}</span>
                      </div>
                    </div>
                    <div class="workload-success">
                      <span class="success-rate">{{ workload.success_rate }}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Analytics Grid -->
        <div class="analytics-grid">
          <!-- Case Status Distribution Chart -->
          <div class="panel chart-panel">
            <div class="panel-header">
              <h3>Case Status Distribution</h3>
              <div class="panel-actions">
                <div class="chart-legend">
                  <div v-for="(count, status) in analytics?.status_distribution" :key="status" class="legend-item">
                    <div class="legend-color" :class="getStatusColorClass(status)"></div>
                    <span>{{ status }} ({{ count }})</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="chart-container">
              <div class="donut-chart">
                <svg viewBox="0 0 200 200" class="donut-svg">
                  <circle cx="100" cy="100" r="80" fill="none" stroke="#f1f3f4" stroke-width="20"/>
                  <circle 
                    v-for="(segment, index) in statusChartData" 
                    :key="index"
                    cx="100" 
                    cy="100" 
                    r="80" 
                    fill="none" 
                    :stroke="segment.color"
                    stroke-width="20"
                    :stroke-dasharray="segment.dashArray"
                    :stroke-dashoffset="segment.dashOffset"
                    :transform="segment.transform"
                    class="chart-segment"
                    :class="{ active: segment.active }"
                    @click="toggleChartSegment(index)"
                    @mouseover="highlightSegment(index)"
                    @mouseout="unhighlightSegment(index)"
                  />
                </svg>
                <div class="chart-center">
                  <div class="center-value">{{ analytics?.overview?.total_cases || 0 }}</div>
                  <div class="center-label">Total Cases</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Case Type Distribution -->
          <div class="panel chart-panel">
            <div class="panel-header">
              <h3>Case Type Breakdown</h3>
              <div class="panel-actions">
                <select v-model="typeFilter" class="filter-select">
                  <option value="all">All Types</option>
                  <option value="operational">Operational Only</option>
                  <option value="non-operational">Non-Operational Only</option>
                </select>
              </div>
            </div>
            <div class="chart-container">
              <div class="bar-chart">
                <div v-for="(count, type) in filteredCaseTypes" :key="type" class="bar-item">
                  <div class="bar-info">
                    <span class="bar-label">{{ type || 'Unknown' }}</span>
                    <span class="bar-value">{{ count }}</span>
                  </div>
                  <div class="bar-track">
                    <div 
                      class="bar-fill" 
                      :class="getCaseTypeColorClass(type)"
                      :style="{ width: getTypePercentage(count) + '%' }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Daily Activity Trend -->
          <div class="panel chart-panel wide">
            <div class="panel-header">
              <h3>Daily Activity Trend (Last 30 Days)</h3>
              <div class="panel-actions">
                <div class="activity-stats">
                  <span class="activity-stat">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                    </svg>
                    Peak: {{ getPeakActivity() }}
                  </span>
                  <span class="activity-stat">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <line x1="18" y1="20" x2="18" y2="10"/>
                      <line x1="12" y1="20" x2="12" y2="4"/>
                      <line x1="6" y1="20" x2="6" y2="14"/>
                    </svg>
                    Avg: {{ getAverageActivity() }}
                  </span>
                </div>
              </div>
            </div>
            <div class="chart-container">
              <div class="line-chart">
                <svg viewBox="0 0 800 200" class="line-svg">
                  <defs>
                    <linearGradient id="activityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" style="stop-color:#4f46e5;stop-opacity:0.3"/>
                      <stop offset="100%" style="stop-color:#4f46e5;stop-opacity:0.05"/>
                    </linearGradient>
                  </defs>
                  
                  <!-- Grid lines -->
                  <g class="grid-lines">
                    <line v-for="i in 5" :key="'h-' + i" x1="50" :y1="40 + (i-1) * 32" x2="750" :y2="40 + (i-1) * 32" stroke="#f1f3f4" stroke-width="1"/>
                    <line v-for="i in 8" :key="'v-' + i" :x1="50 + (i-1) * 100" y1="40" :x2="50 + (i-1) * 100" y2="168" stroke="#f1f3f4" stroke-width="1"/>
                  </g>
                  
                  <!-- Activity area -->
                  <path v-if="activityPath" :d="activityPath" fill="url(#activityGradient)" stroke="none"/>
                  
                  <!-- Activity line -->
                  <path v-if="activityPath" :d="activityPath" fill="none" stroke="#4f46e5" stroke-width="2"/>
                  
                  <!-- Data points -->
                  <circle 
                    v-for="(point, index) in activityPoints" 
                    :key="index"
                    :cx="point.x" 
                    :cy="point.y" 
                    r="4" 
                    fill="#4f46e5"
                    class="activity-point"
                    @mouseover="showTooltip(point, $event)"
                    @mouseout="hideTooltip"
                  />
                  
                  <!-- Date labels -->
                  <g class="date-labels">
                    <text 
                      v-for="(point, index) in dateLabels" 
                      :key="'date-' + index"
                      :x="point.x" 
                      y="190" 
                      text-anchor="middle" 
                      font-size="10" 
                      fill="#64748b"
                      transform="rotate(0)"
                    >
                      {{ point.label }}
                    </text>
                  </g>
                  
                  <!-- Value labels -->
                  <g class="value-labels">
                    <text 
                      v-for="i in 5" 
                      :key="'value-' + i"
                      x="40" 
                      :y="44 + (i-1) * 32" 
                      text-anchor="end" 
                      font-size="10" 
                      fill="#64748b"
                    >
                      {{ getYAxisLabel(i-1) }}
                    </text>
                  </g>
                  
                  <!-- Tooltip -->
                  <div v-if="tooltip.visible" class="chart-tooltip" :style="tooltipStyle">
                    <div class="tooltip-content">
                      <div class="tooltip-date">{{ tooltip.date }}</div>
                      <div class="tooltip-value">{{ tooltip.count }} cases</div>
                    </div>
                  </div>
                </svg>
              </div>
            </div>
          </div>

          <!-- Recent Cases Table -->
          <div class="panel table-panel">
            <div class="panel-header">
              <h3>Recent Cases</h3>
              <div class="panel-actions">
                <router-link to="/review-assigned-cases" class="view-all-link">
                  View All Cases
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M7 17L17 7M17 7H7M17 7V17"/>
                  </svg>
                </router-link>
              </div>
            </div>
            <div class="table-container">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Case ID</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Assigned To</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="caseItem in recentCases.slice(0, 10)" :key="caseItem.case_id">
                    <td>
                      <router-link :to="getCaseRoute(caseItem.case_type, caseItem.case_id)" class="case-link">
                        #{{ caseItem.case_id }}
                      </router-link>
                    </td>
                    <td>
                      <span class="case-type-badge" :class="getCaseTypeColorClass(caseItem.case_type)">
                        {{ caseItem.case_type || 'Unknown' }}
                      </span>
                    </td>
                    <td>
                      <span :class="['status-badge', getStatusColorClass(caseItem.status)]">
                        {{ caseItem.status || 'New' }}
                      </span>
                    </td>
                    <td>{{ caseItem.assigned_to || 'Unassigned' }}</td>
                    <td>{{ formatDate(caseItem.creation_date) }}</td>
                  </tr>
                  <tr v-if="recentCases.length === 0">
                    <td colspan="5" style="padding: 12px;">
                      <div class="empty-state">
                        <div class="icon">🗂️</div>
                        <div class="title">No recent cases</div>
                        <div class="hint">New cases will appear here as they are created.</div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>

      <!-- Loading State -->
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner">
          <div class="spinner"></div>
          <p>Loading analytics data...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { API_ENDPOINTS } from '../config/api.js';
import axios from 'axios';
import NetworkVisualization from '@/components/NetworkVisualization.vue';
import FraudPatternDetector from '@/components/FraudPatternDetector.vue';
import '../assets/Dashboard.css';

const router = useRouter();

// Get the appropriate route for each case type
const getCaseRoute = (caseType, caseId) => {
  const routeMap = {
    'VM': 'OperationalAction',
    'BM': 'BeneficiaryAction', 
    'PMA': 'PMAAction',
    'PVA': 'PVAAction',
    'PSA': 'PSAAction',
    'ECBT': 'ECBTAction',
    'ECBNT': 'ECBNTAction',
    'NAB': 'NABAction',
    'MM': 'MobileMatchingAction'
  };

  return {
    name: routeMap[caseType] || 'CaseRiskReview',
    params: { case_id: caseId }
  };
};

// State
const userName = ref('');
const userType = ref('');
const typeFilter = ref('all');
const loading = ref(true);
const error = ref(null);
const lastRefresh = ref(null);
const analytics = ref(null);
const recentCases = ref([]);
const advancedAnalytics = ref(null);
const realTimeMetrics = ref(null);
const predictiveAnalytics = ref(null);
const networkData = ref(null);

// Chart data
const statusChartData = ref([]);
const activityPath = ref('');
const activityPoints = ref([]);
const dateLabels = ref([]);

// Tooltip state
const tooltip = ref({
  visible: false,
  date: '',
  count: 0,
  x: 0,
  y: 0
});

const tooltipStyle = computed(() => ({
  position: 'absolute',
  left: tooltip.value.x + 'px',
  top: tooltip.value.y + 'px',
  transform: 'translate(-50%, -100%)'
}));

// Computed properties
const averageResolutionTime = computed(() => {
  if (!analytics.value?.overview?.average_resolution_days) return '0 days';
  const days = analytics.value.overview.average_resolution_days;
  return `${days} days`;
});

const filteredCaseTypes = computed(() => {
  if (!analytics.value?.case_types) return {};
  
  const types = analytics.value.case_types;
  const operationalTypes = ['VM', 'BM']; // Define which types are operational
  
  if (typeFilter.value === 'operational') {
    return Object.fromEntries(
      Object.entries(types).filter(([type]) => operationalTypes.includes(type))
    );
  } else if (typeFilter.value === 'non-operational') {
    return Object.fromEntries(
      Object.entries(types).filter(([type]) => !operationalTypes.includes(type))
    );
  }
  
  return types;
});

const getOperationalPercentage = () => {
  if (!analytics.value?.overview) return 0;
  const total = analytics.value.overview.total_cases;
  const operational = analytics.value.overview.operational_cases;
  return total > 0 ? Math.round((operational / total) * 100) : 0;
};

const getTypePercentage = (count) => {
  const total = Object.values(filteredCaseTypes.value).reduce((sum, curr) => sum + curr, 0);
  return total > 0 ? Math.round((count / total) * 100) : 0;
};

const getPeakActivity = () => {
  if (!analytics.value?.daily_activity?.length) return 0;
  return Math.max(...analytics.value.daily_activity.map(d => d.count));
};

const getAverageActivity = () => {
  if (!analytics.value?.daily_activity?.length) return 0;
  const total = analytics.value.daily_activity.reduce((sum, d) => sum + d.count, 0);
  return Math.round(total / analytics.value.daily_activity.length);
};

const getClosureRate = () => {
  if (!analytics.value?.overview) return 0;
  const total = analytics.value.overview.total_cases;
  const closed = analytics.value.overview.closed_cases;
  return total > 0 ? Math.round((closed / total) * 100) : 0;
};

const getActiveUsers = () => {
  const uniqueAssigned = new Set(
    recentCases.value
      .filter(c => c.assigned_to && c.assigned_to !== 'Unassigned')
      .map(c => c.assigned_to)
  );
  return uniqueAssigned.size;
};

const getWorkloadBalance = () => {
  // Calculate workload distribution balance (simplified)
  const assignedCases = recentCases.value.filter(c => c.assigned_to && c.assigned_to !== 'Unassigned');
  if (assignedCases.length === 0) return 100;
  
  const userCounts = {};
  assignedCases.forEach(c => {
    userCounts[c.assigned_to] = (userCounts[c.assigned_to] || 0) + 1;
  });
  
  const counts = Object.values(userCounts);
  const avg = counts.reduce((sum, count) => sum + count, 0) / counts.length;
  const variance = counts.reduce((sum, count) => sum + Math.pow(count - avg, 2), 0) / counts.length;
  
  // Convert to balance percentage (lower variance = better balance)
  return Math.max(0, Math.round(100 - (variance / avg) * 20));
};

// Advanced analytics helper functions
const getAgingPercentage = (count) => {
  if (!advancedAnalytics.value?.case_aging) return 0;
  const maxCount = Math.max(...advancedAnalytics.value.case_aging.map(a => a.case_count));
  return maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;
};

const getWorkloadPercentage = (count) => {
  if (!advancedAnalytics.value?.workload_distribution) return 0;
  const maxCount = Math.max(...advancedAnalytics.value.workload_distribution.map(w => Math.max(w.active_cases, w.closed_cases)));
  return maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;
};

const getYAxisLabel = (index) => {
  if (!analytics.value?.daily_activity?.length) return '0';
  const data = analytics.value.daily_activity.slice(0, 30);
  const maxValue = Math.max(...data.map(d => d.count));
  return Math.round(maxValue - (index * maxValue / 4));
};

// Color and styling helpers
const getStatusColorClass = (status) => {
  const statusMap = {
    'New': 'status-new',
    'Assigned': 'status-assigned', 
    'Closed': 'status-closed',
    'Pending': 'status-pending'
  };
  return statusMap[status] || 'status-default';
};

const getCaseTypeColorClass = (type) => {
  const typeMap = {
    'VM': 'type-vm',
    'BM': 'type-bm',
    'PMA': 'type-pma',
    'PSA': 'type-psa',
    'NAB': 'type-nab',
    'ECBT': 'type-ecbt',
    'ECBNT': 'type-ecbnt'
  };
  return typeMap[type] || 'type-default';
};

// Format helpers
const formatDate = (date) => {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
};

const formatTime = (date) => {
  if (!date) return '';
  return new Date(date).toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

const formatDateShort = (date) => {
  if (!date) return '';
  return new Date(date).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short'
  });
};

// Chart generation functions
const generateStatusChart = () => {
  if (!analytics.value?.status_distribution) return;
  
  const total = Object.values(analytics.value.status_distribution).reduce((sum, count) => sum + count, 0);
  let cumulativePercentage = 0;
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  
  const colors = {
    'New': '#3b82f6',
    'Assigned': '#f59e0b', 
    'Closed': '#10b981',
    'Pending': '#ef4444'
  };
  
  statusChartData.value = Object.entries(analytics.value.status_distribution).map(([status, count]) => {
    const percentage = count / total;
    const dashArray = `${percentage * circumference} ${circumference}`;
    const dashOffset = -cumulativePercentage * circumference;
    const transform = `rotate(-90 100 100)`;
    
    cumulativePercentage += percentage;
    
    return {
      color: colors[status] || '#6b7280',
      dashArray,
      dashOffset,
      transform,
      active: false,
      highlighted: false,
      status: status
    };
  });
};

const generateActivityChart = () => {
  if (!analytics.value?.daily_activity?.length) return;
  
  const data = analytics.value.daily_activity.slice(0, 30).reverse(); // Last 30 days
  const maxValue = Math.max(...data.map(d => d.count));
  const padding = 50;
  const chartWidth = 800 - 2 * padding;
  const chartHeight = 200 - 80; // Leave space for padding
  
  // Generate path and points
  const points = data.map((d, i) => {
    const x = padding + (i * chartWidth) / (data.length - 1);
    const y = 40 + chartHeight - (d.count / maxValue) * chartHeight;
    return { x, y, count: d.count, date: d.date };
  });
  
  activityPoints.value = points;
  
  // Generate date labels (show every 5th date to avoid crowding)
  dateLabels.value = points
    .filter((_, i) => i % Math.max(1, Math.floor(points.length / 6)) === 0)
    .map(point => ({
      x: point.x,
      label: formatDateShort(point.date)
    }));
  
  // Generate SVG path
  if (points.length > 0) {
    let path = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      path += ` L ${points[i].x} ${points[i].y}`;
    }
    // Add area fill path
    path += ` L ${points[points.length - 1].x} ${40 + chartHeight}`;
    path += ` L ${points[0].x} ${40 + chartHeight} Z`;
    
    activityPath.value = path;
  }
};

// API calls
const fetchAnalytics = async () => {
  try {
    const token = localStorage.getItem('jwt');
    if (!token) throw new Error('No authentication token found');

    const response = await axios.get('/api/dashboard/analytics', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.data.success) {
      analytics.value = response.data.data;
      generateStatusChart();
      generateActivityChart();
      lastRefresh.value = new Date();
    }
  } catch (err) {
    console.error('Failed to fetch analytics:', err);
    error.value = err.message;
    if (err.response?.status === 401) {
      router.push('/login');
    }
  }
};

const fetchRecentCases = async () => {
  try {
    const token = localStorage.getItem('jwt');
    if (!token) return;

    const response = await axios.get(API_ENDPOINTS.NEW_CASE_LIST, {
      headers: { 'Authorization': `Bearer ${token}` },
      params: { limit: 20 }
    });

    if (response.data && Array.isArray(response.data.cases)) {
      recentCases.value = response.data.cases;
    }
  } catch (err) {
    console.error('Failed to fetch recent cases:', err);
  }
};

const fetchAdvancedAnalytics = async () => {
  try {
    const token = localStorage.getItem('jwt');
    if (!token) return;

    const response = await axios.get('/api/dashboard/advanced-analytics', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.data.success) {
      advancedAnalytics.value = response.data.data;
    }
  } catch (err) {
    console.error('Failed to fetch advanced analytics:', err);
  }
};

const fetchRealTimeMetrics = async () => {
  try {
    const token = localStorage.getItem('jwt');
    if (!token) return;

    const response = await axios.get('/api/dashboard/real-time-metrics', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.data.success) {
      realTimeMetrics.value = response.data.data;
    }
  } catch (err) {
    console.error('Failed to fetch real-time metrics:', err);
  }
};

const fetchPredictiveAnalytics = async () => {
  try {
    const token = localStorage.getItem('jwt');
    if (!token) return;

    const response = await axios.get('/api/dashboard/predictive-analytics', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.data.success) {
      predictiveAnalytics.value = response.data.data;
    }
  } catch (err) {
    console.error('Failed to fetch predictive analytics:', err);
  }
};


const refreshDashboard = async () => {
  loading.value = true;
  error.value = null;
  
  try {
    await Promise.all([
      fetchAnalytics(),
      fetchRecentCases(),
      fetchAdvancedAnalytics(),
      fetchRealTimeMetrics(),
      fetchPredictiveAnalytics()
    ]);
  } catch (err) {
    error.value = 'Failed to refresh dashboard data';
  } finally {
    loading.value = false;
  }
};

// Tooltip functions
const showTooltip = (point, event) => {
  tooltip.value = {
    visible: true,
    date: formatDate(point.date),
    count: point.count,
    x: event.clientX,
    y: event.clientY - 10
  };
};

const hideTooltip = () => {
  tooltip.value.visible = false;
};

// Chart interaction functions
const toggleChartSegment = (index) => {
  statusChartData.value[index].active = !statusChartData.value[index].active;
};

const highlightSegment = (index) => {
  statusChartData.value.forEach((segment, i) => {
    segment.highlighted = i === index;
  });
};

const unhighlightSegment = () => {
  statusChartData.value.forEach(segment => {
    segment.highlighted = false;
  });
};

// Network visualization event handlers
const handleNodeClick = (node) => {
  console.log('Node clicked:', node);
  // Navigate to case details when clicking on nodes
  if (node.type === 'case') {
    const caseId = node.label.split(' ')[1];
    if (caseId && !isNaN(caseId)) {
      // Navigate to case details based on case type
      const route = getCaseRoute(node.case_type, caseId);
      router.push(route);
    }
  } else if (node.cases && node.cases.length > 0) {
    // For entity nodes, navigate to the first related case
    const firstCaseId = node.cases[0];
    if (firstCaseId && !isNaN(firstCaseId)) {
      router.push({
        name: 'CaseRiskReview',
        params: { case_id: firstCaseId }
      });
    }
  }
};

const handleNetworkDataLoaded = (data) => {
  networkData.value = data;
  console.log('Network data loaded:', data);
};

// Fraud pattern detection event handlers
const handleFraudPatternDetected = (fraudData) => {
  console.log('Fraud patterns detected:', fraudData);
  // You can add custom logic here, like triggering notifications
  if (fraudData.critical_alerts && fraudData.critical_alerts.length > 0) {
    // Show notification for critical alerts
    fraudData.critical_alerts.forEach(alert => {
      if (alert.risk_score > 90) {
        console.warn('Critical fraud alert:', alert.title);
        // You could integrate with a notification system here
      }
    });
  }
};

const handleFraudAlert = (alertData) => {
  console.log('Fraud alert triggered:', alertData);
  // Handle different types of fraud alerts
  if (alertData.type === 'investigate') {
    // Could navigate to investigation page or open modal
    console.log('Investigation requested for pattern:', alertData.pattern);
  }
};

// Load user information
const loadUserInfo = () => {
  const storedUsername = localStorage.getItem('username');
  const storedUserType = localStorage.getItem('user_type');
  
  if (storedUsername) {
    userName.value = storedUsername;
  } else {
    userName.value = 'Unknown User';
  }
  
  if (storedUserType) {
    userType.value = storedUserType;
  }
};

// Initialize dashboard
onMounted(async () => {
  loadUserInfo();
  
  // Redirect users with type "others" to simple dashboard
  if (userType.value === 'others') {
    router.push('/simple-dashboard');
    return;
  }
  
  await refreshDashboard();
});

// Auto-refresh when component becomes visible
const handleVisibilityChange = () => {
  if (!document.hidden) {
    refreshDashboard();
  }
};

// Periodic refresh every 5 minutes
let refreshInterval = null;
let realTimeInterval = null;

onMounted(() => {
  document.addEventListener('visibilitychange', handleVisibilityChange);
  
  // Set up periodic refresh every 5 minutes
  refreshInterval = setInterval(() => {
    if (!document.hidden) {
      refreshDashboard();
    }
  }, 5 * 60 * 1000); // 5 minutes
  
  // Set up real-time metrics refresh every 2 minutes (reduced frequency)
  realTimeInterval = setInterval(() => {
    if (!document.hidden) {
      fetchRealTimeMetrics();
    }
  }, 2 * 60 * 1000); // 2 minutes
});

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange);
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
  if (realTimeInterval) {
    clearInterval(realTimeInterval);
  }
});
</script>

<style>
@import '../assets/Dashboard.css';

.dashboard-wrapper {
  height: 100%;
  width: 100%;
  overflow-y: auto;
}
</style>
  