<template>
  <div class="network-visualization">
    <div class="network-header">
      <h3>Entity Relationship Network</h3>
      <div class="network-controls">
        <div class="control-group">
          <label>Filter by Risk:</label>
          <select v-model="riskFilter" @change="updateVisualization">
            <option value="all">All Nodes</option>
            <option value="high">High Risk Only</option>
            <option value="medium">Medium+ Risk</option>
          </select>
        </div>
        <div class="control-group">
          <label>Node Type:</label>
          <select v-model="nodeTypeFilter" @change="updateVisualization">
            <option value="all">All Types</option>
            <option value="account">Account Numbers</option>
            <option value="customer">Customers</option>
            <option value="ack_no">Source ACK Numbers</option>
            <option value="case">Cases</option>
          </select>
        </div>
        <button @click="resetZoom" class="control-btn">Reset View</button>
        <button @click="refreshData" class="control-btn" :disabled="loading">
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
    </div>
    
    <div class="network-stats" v-if="networkData">
      <div class="stat-item">
        <span class="stat-label">Total Nodes:</span>
        <span class="stat-value">{{ networkData.stats.total_nodes }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Connections:</span>
        <span class="stat-value">{{ networkData.stats.total_edges }}</span>
      </div>
      <div class="stat-item high-risk">
        <span class="stat-label">High Risk:</span>
        <span class="stat-value">{{ networkData.stats.high_risk_nodes }}</span>
      </div>
      <div class="stat-item medium-risk">
        <span class="stat-label">Medium Risk:</span>
        <span class="stat-value">{{ networkData.stats.medium_risk_nodes }}</span>
      </div>
    </div>
    
    <div class="network-container">
      <div ref="networkSvg" class="network-svg-container"></div>
      
      <div class="network-legend">
        <h4>Legend</h4>
        <div class="legend-items">
          <div class="legend-item">
            <div class="legend-node case"></div>
            <span>Cases</span>
          </div>
          <div class="legend-item">
            <div class="legend-node account"></div>
            <span>Account Numbers</span>
          </div>
          <div class="legend-item">
            <div class="legend-node customer"></div>
            <span>Customers</span>
          </div>
          <div class="legend-item">
            <div class="legend-node ack-no"></div>
            <span>Source ACK Numbers</span>
          </div>
          <div class="legend-item">
            <div class="legend-node high-risk"></div>
            <span>High Risk (5+ connections)</span>
          </div>
          <div class="legend-item">
            <div class="legend-node medium-risk"></div>
            <span>Medium Risk (3-4 connections)</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="fraud-patterns" v-if="networkData && networkData.fraud_patterns">
      <h4>Fraud Patterns (Last 30 Days)</h4>
      <div class="pattern-grid">
        <div v-for="pattern in networkData.fraud_patterns" :key="pattern.case_type" class="pattern-card">
          <div class="pattern-type">{{ pattern.case_type }}</div>
          <div class="pattern-stats">
            <div class="pattern-count">{{ pattern.count }} cases</div>
            <div class="pattern-amount">₹{{ formatAmount(pattern.avg_amount) }} avg</div>
            <div class="pattern-closure">{{ Math.round((pattern.closed_count / pattern.count) * 100) }}% closed</div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="repeated-entities" v-if="networkData && networkData.repeated_entities">
      <h4>Highly Repeated Entities</h4>
      <div class="entity-list">
        <div v-for="entity in networkData.repeated_entities.slice(0, 10)" :key="entity.entity" class="entity-item">
          <div class="entity-info">
            <span class="entity-type">{{ entity.entity_type.replace('_', ' ') }}:</span>
            <span class="entity-value">{{ entity.entity }}</span>
          </div>
          <div class="entity-count">{{ entity.case_count }} cases</div>
        </div>
      </div>
    </div>
    
    <!-- Node Details Modal -->
    <div v-if="selectedNode" class="node-modal-overlay" @click="closeNodeModal">
      <div class="node-modal" @click.stop>
        <div class="node-modal-header">
          <h3>{{ selectedNode.label }}</h3>
          <button @click="closeNodeModal" class="close-btn">&times;</button>
        </div>
        <div class="node-modal-content">
          <div class="node-detail">
            <strong>Type:</strong> {{ selectedNode.type }}
          </div>
          <div class="node-detail">
            <strong>Risk Level:</strong> 
            <span :class="'risk-' + selectedNode.risk_level">{{ selectedNode.risk_level }}</span>
          </div>
          <div class="node-detail">
            <strong>Connections:</strong> {{ selectedNode.connections }}
          </div>
          <div v-if="selectedNode.cases && selectedNode.cases.length > 0" class="node-detail">
            <strong>Related Cases:</strong>
            <div class="case-list">
              <span v-for="caseId in selectedNode.cases.slice(0, 10)" :key="caseId" class="case-tag">
                {{ caseId }}
              </span>
              <span v-if="selectedNode.cases.length > 10" class="case-more">
                +{{ selectedNode.cases.length - 10 }} more
              </span>
            </div>
          </div>
          <div v-if="selectedNode.amount" class="node-detail">
            <strong>Amount:</strong> ₹{{ formatAmount(selectedNode.amount) }}
          </div>
          <div v-if="selectedNode.creation_date" class="node-detail">
            <strong>Created:</strong> {{ formatDate(selectedNode.creation_date) }}
          </div>
          <div v-if="selectedNode.assigned_to" class="node-detail">
            <strong>Assigned to:</strong> {{ selectedNode.assigned_to }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import axios from 'axios'

const networkSvg = ref(null)
const networkData = ref(null)
const loading = ref(false)
const selectedNode = ref(null)
const riskFilter = ref('all')
const nodeTypeFilter = ref('all')

let svg, simulation, nodes, links, nodeElements, linkElements, zoom

const props = defineProps({
  height: {
    type: Number,
    default: 600
  },
  width: {
    type: Number,
    default: 1000
  }
})

const emit = defineEmits(['nodeClick', 'dataLoaded'])

// Fetch network data from API
const fetchNetworkData = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('jwt')
    if (!token) return

    const response = await axios.get('/api/dashboard/network-data', {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (response.data.success) {
      networkData.value = response.data.data
      emit('dataLoaded', networkData.value)
      await nextTick()
      initializeVisualization()
    }
  } catch (err) {
    console.error('Failed to fetch network data:', err)
  } finally {
    loading.value = false
  }
}

// Initialize D3 visualization
const initializeVisualization = () => {
  if (!networkData.value || !networkSvg.value) return

  // Clear previous visualization
  d3.select(networkSvg.value).selectAll('*').remove()

  const container = networkSvg.value
  const rect = container.getBoundingClientRect()
  const width = rect.width || props.width
  const height = props.height

  // Create SVG
  svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  // Add zoom behavior
  zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      svg.select('.network-group').attr('transform', event.transform)
    })

  svg.call(zoom)

  // Create main group for network elements
  const networkGroup = svg.append('g').attr('class', 'network-group')

  // Filter data based on current filters
  const filteredData = getFilteredData()
  nodes = [...filteredData.nodes]
  links = [...filteredData.edges]

  // Create force simulation
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(80))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => getNodeRadius(d) + 5))

  // Create links
  linkElements = networkGroup.selectAll('.link')
    .data(links)
    .enter()
    .append('line')
    .attr('class', 'link')
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
    .attr('stroke-width', d => Math.sqrt(d.strength))

  // Create nodes
  nodeElements = networkGroup.selectAll('.node')
    .data(nodes)
    .enter()
    .append('circle')
    .attr('class', 'node')
    .attr('r', getNodeRadius)
    .attr('fill', getNodeColor)
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .style('cursor', 'pointer')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))
    .on('click', (event, d) => {
      selectedNode.value = d
      emit('nodeClick', d)
    })
    .on('mouseover', (event, d) => {
      // Highlight connected nodes
      const connectedNodeIds = new Set()
      links.forEach(link => {
        if (link.source.id === d.id) connectedNodeIds.add(link.target.id)
        if (link.target.id === d.id) connectedNodeIds.add(link.source.id)
      })

      nodeElements
        .style('opacity', node => connectedNodeIds.has(node.id) || node.id === d.id ? 1 : 0.3)
      
      linkElements
        .style('opacity', link => link.source.id === d.id || link.target.id === d.id ? 1 : 0.1)
    })
    .on('mouseout', () => {
      nodeElements.style('opacity', 1)
      linkElements.style('opacity', 0.6)
    })

  // Add labels
  const labels = networkGroup.selectAll('.label')
    .data(nodes.filter(d => d.connections > 2)) // Only show labels for highly connected nodes
    .enter()
    .append('text')
    .attr('class', 'label')
    .attr('text-anchor', 'middle')
    .attr('dy', '.35em')
    .style('font-size', '10px')
    .style('fill', '#333')
    .style('pointer-events', 'none')
    .text(d => d.type === 'case' ? `C${d.label.split(' ')[1]}` : d.label.slice(0, 8))

  // Update positions on simulation tick
  simulation.on('tick', () => {
    linkElements
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    nodeElements
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)

    labels
      .attr('x', d => d.x)
      .attr('y', d => d.y)
  })
}

// Get filtered data based on current filters
const getFilteredData = () => {
  if (!networkData.value) return { nodes: [], edges: [] }

  let filteredNodes = networkData.value.nodes

  // Apply risk filter
  if (riskFilter.value === 'high') {
    filteredNodes = filteredNodes.filter(n => n.risk_level === 'high')
  } else if (riskFilter.value === 'medium') {
    filteredNodes = filteredNodes.filter(n => n.risk_level === 'high' || n.risk_level === 'medium')
  }

  // Apply node type filter
  if (nodeTypeFilter.value !== 'all') {
    filteredNodes = filteredNodes.filter(n => n.type === nodeTypeFilter.value)
  }

  const nodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredEdges = networkData.value.edges.filter(e => 
    nodeIds.has(e.source) && nodeIds.has(e.target)
  )

  return { nodes: filteredNodes, edges: filteredEdges }
}

// Get node radius based on connections
const getNodeRadius = (d) => {
  const baseRadius = 6
  const connectionMultiplier = Math.sqrt(d.connections || 1)
  return Math.min(baseRadius + connectionMultiplier * 2, 20)
}

// Get node color based on type and risk level
const getNodeColor = (d) => {
  if (d.risk_level === 'high') return '#ef4444'
  if (d.risk_level === 'medium') return '#f97316'
  
  switch (d.type) {
    case 'case': return '#3b82f6'
    case 'account': return '#8b5cf6'
    case 'customer': return '#10b981'
    case 'ack_no': return '#f59e0b'
    default: return '#6b7280'
  }
}

// Drag functions
const dragstarted = (event, d) => {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

const dragged = (event, d) => {
  d.fx = event.x
  d.fy = event.y
}

const dragended = (event, d) => {
  if (!event.active) simulation.alphaTarget(0)
  d.fx = null
  d.fy = null
}

// Update visualization when filters change
const updateVisualization = () => {
  if (simulation) {
    simulation.stop()
  }
  initializeVisualization()
}

// Reset zoom
const resetZoom = () => {
  if (svg && zoom) {
    svg.transition().duration(750).call(
      zoom.transform,
      d3.zoomIdentity
    )
  }
}

// Refresh data
const refreshData = () => {
  fetchNetworkData()
}

// Close node modal
const closeNodeModal = () => {
  selectedNode.value = null
}

// Format amount for display
const formatAmount = (amount) => {
  if (!amount) return '0'
  return new Intl.NumberFormat('en-IN').format(Math.round(amount))
}

// Format date for display
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-IN')
}

// Lifecycle hooks
onMounted(() => {
  fetchNetworkData()
})

onUnmounted(() => {
  if (simulation) {
    simulation.stop()
  }
})

// Expose methods for parent component
defineExpose({
  refreshData,
  resetZoom,
  updateVisualization
})
</script>

<style scoped>
.network-visualization {
  width: 100%;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.network-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.network-header h3 {
  margin: 0;
  color: #111827;
  font-size: 1.25rem;
  font-weight: 600;
}

.network-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.control-group label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.control-group select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  background: white;
}

.control-btn {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.control-btn:hover:not(:disabled) {
  background: #2563eb;
}

.control-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.network-stats {
  padding: 1rem 1.5rem;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.stat-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

.stat-item.high-risk .stat-value {
  color: #ef4444;
}

.stat-item.medium-risk .stat-value {
  color: #f97316;
}

.network-container {
  position: relative;
  display: flex;
}

.network-svg-container {
  flex: 1;
  min-height: 600px;
  background: #fafafa;
}

.network-legend {
  width: 200px;
  padding: 1.5rem;
  background: #fff;
  border-left: 1px solid #e5e7eb;
}

.network-legend h4 {
  margin: 0 0 1rem 0;
  color: #111827;
  font-size: 1rem;
  font-weight: 600;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-node {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid #fff;
}

.legend-node.case { background: #3b82f6; }
.legend-node.account { background: #8b5cf6; }
.legend-node.customer { background: #10b981; }
.legend-node.ack-no { background: #f59e0b; }
.legend-node.high-risk { background: #ef4444; }
.legend-node.medium-risk { background: #f97316; }

.legend-item span {
  font-size: 0.875rem;
  color: #6b7280;
}

.fraud-patterns {
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.fraud-patterns h4 {
  margin: 0 0 1rem 0;
  color: #111827;
  font-size: 1rem;
  font-weight: 600;
}

.pattern-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.pattern-card {
  padding: 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.pattern-type {
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.5rem;
}

.pattern-stats {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.pattern-count, .pattern-amount, .pattern-closure {
  font-size: 0.875rem;
  color: #6b7280;
}

.repeated-entities {
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.repeated-entities h4 {
  margin: 0 0 1rem 0;
  color: #111827;
  font-size: 1rem;
  font-weight: 600;
}

.entity-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.entity-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.entity-info {
  display: flex;
  gap: 0.5rem;
}

.entity-type {
  font-weight: 500;
  color: #6b7280;
  text-transform: capitalize;
}

.entity-value {
  font-weight: 600;
  color: #111827;
}

.entity-count {
  font-size: 0.875rem;
  font-weight: 600;
  color: #ef4444;
}

/* Node Modal */
.node-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.node-modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.node-modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.node-modal-header h3 {
  margin: 0;
  color: #111827;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #111827;
}

.node-modal-content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.node-detail {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.node-detail strong {
  color: #111827;
  font-weight: 600;
}

.risk-high { color: #ef4444; font-weight: 600; }
.risk-medium { color: #f97316; font-weight: 600; }
.risk-low { color: #10b981; font-weight: 600; }

.case-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.case-tag {
  padding: 0.25rem 0.5rem;
  background: #e5e7eb;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.case-more {
  padding: 0.25rem 0.5rem;
  background: #3b82f6;
  color: white;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Responsive */
@media (max-width: 1024px) {
  .network-container {
    flex-direction: column;
  }
  
  .network-legend {
    width: 100%;
    border-left: none;
    border-top: 1px solid #e5e7eb;
  }
  
  .legend-items {
    flex-direction: row;
    flex-wrap: wrap;
  }
  
  .pattern-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .network-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .network-controls {
    justify-content: space-between;
  }
  
  .network-stats {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .network-svg-container {
    min-height: 400px;
  }
}
</style>
