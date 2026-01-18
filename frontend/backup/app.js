/**
 * DisasterLens AI - Frontend Application
 * Handles real-time updates, map visualization, and user interactions
 */

const API_BASE_URL = window.location.origin;
const WS_URL = `ws://${window.location.host}/ws`;

let map;
let markers = [];
let eventsData = [];
let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    initializeWebSocket();
    loadEvents();
    loadStatistics();
    setupEventListeners();
    
    // Auto-refresh every 2 minutes
    setInterval(loadEvents, 120000);
    setInterval(loadStatistics, 120000);
});

// Initialize Leaflet map
function initializeMap() {
    map = L.map('map').setView([20, 0], 2);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
    
    console.log('Map initialized');
}

// Initialize WebSocket connection
function initializeWebSocket() {
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            reconnectAttempts = 0;
            updateConnectionStatus(true);
            showNotification('Connected to real-time stream', 'success');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateConnectionStatus(false);
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus(false);
            attemptReconnect();
        };
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        updateConnectionStatus(false);
    }
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    console.log('WebSocket message:', data);
    
    if (data.type === 'new_event') {
        showNotification(`New ${data.event.disaster_type} detected in ${data.event.location}`, 'warning');
        loadEvents();
        loadStatistics();
    } else if (data.type === 'connection') {
        console.log(data.message);
    }
}

// Attempt WebSocket reconnection
function attemptReconnect() {
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        console.log(`Reconnection attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
        setTimeout(initializeWebSocket, 3000 * reconnectAttempts);
    } else {
        showNotification('Failed to connect to real-time stream', 'error');
    }
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    const statusBadge = document.getElementById('connection-status');
    if (connected) {
        statusBadge.classList.remove('disconnected');
        statusBadge.classList.add('connected');
        statusBadge.querySelector('.status-text').textContent = 'Connected';
    } else {
        statusBadge.classList.remove('connected');
        statusBadge.classList.add('disconnected');
        statusBadge.querySelector('.status-text').textContent = 'Disconnected';
    }
}

// Setup event listeners
function setupEventListeners() {
    // Query form submission
    document.getElementById('query-form').addEventListener('submit', handleQuerySubmit);
    
    // Quick query buttons
    document.querySelectorAll('.quick-query-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.getAttribute('data-query');
            document.getElementById('query-input').value = query;
            handleQuerySubmit(new Event('submit'));
        });
    });
    
    // Refresh events button
    document.getElementById('refresh-events').addEventListener('click', loadEvents);
    
    // Filter dropdowns
    document.getElementById('type-filter').addEventListener('change', filterEvents);
    document.getElementById('severity-filter').addEventListener('change', filterEvents);
}

// Handle query form submission
async function handleQuerySubmit(e) {
    e.preventDefault();
    
    const queryInput = document.getElementById('query-input');
    const submitBtn = document.getElementById('query-submit');
    const query = queryInput.value.trim();
    
    if (!query) return;
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.querySelector('.button-text').style.display = 'none';
    submitBtn.querySelector('.loader').style.display = 'inline-block';
    
    try {
        const startTime = performance.now();
        
        const response = await fetch(`${API_BASE_URL}/api/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                top_k: 5
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const endTime = performance.now();
        
        displayQueryResponse(data, endTime - startTime);
        
    } catch (error) {
        console.error('Query error:', error);
        showNotification('Failed to process query. Please try again.', 'error');
    } finally {
        // Reset button state
        submitBtn.disabled = false;
        submitBtn.querySelector('.button-text').style.display = 'inline';
        submitBtn.querySelector('.loader').style.display = 'none';
    }
}

// Display query response
function displayQueryResponse(data, clientLatency) {
    const responseContainer = document.getElementById('response-container');
    const responseContent = document.getElementById('response-content');
    const responseLatency = document.getElementById('response-latency');
    const responseTimestamp = document.getElementById('response-timestamp');
    
    responseContent.textContent = data.answer;
    responseLatency.textContent = `Latency: ${Math.round(data.latency_ms)}ms (client: ${Math.round(clientLatency)}ms)`;
    responseTimestamp.textContent = `Retrieved at ${new Date(data.timestamp).toLocaleTimeString()}`;
    
    // Show risk assessment if available
    if (data.risk_assessment) {
        document.getElementById('risk-assessment-container').style.display = 'block';
        document.getElementById('risk-assessment-content').textContent = data.risk_assessment;
    } else {
        document.getElementById('risk-assessment-container').style.display = 'none';
    }
    
    // Display sources
    if (data.sources && data.sources.length > 0) {
        displaySources(data.sources);
    } else {
        document.getElementById('sources-container').style.display = 'none';
    }
    
    responseContainer.style.display = 'block';
    responseContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Display source citations
function displaySources(sources) {
    const sourcesContainer = document.getElementById('sources-container');
    const sourcesList = document.getElementById('sources-list');
    
    sourcesList.innerHTML = '';
    
    sources.forEach(source => {
        const sourceItem = document.createElement('div');
        sourceItem.className = 'source-item';
        
        const severityClass = `severity-${source.severity}`;
        
        sourceItem.innerHTML = `
            <h5>
                ${source.disaster_type.charAt(0).toUpperCase() + source.disaster_type.slice(1)}
                <span class="severity-badge ${severityClass}">${source.severity}</span>
            </h5>
            <p><strong>Location:</strong> ${source.location}</p>
            <p><strong>Time:</strong> ${new Date(source.event_time).toLocaleString()}</p>
            <p><strong>Source:</strong> ${source.source}</p>
            ${source.url ? `<a href="${source.url}" target="_blank" rel="noopener">View Source ↗</a>` : ''}
        `;
        
        sourcesList.appendChild(sourceItem);
    });
    
    sourcesContainer.style.display = 'block';
}

// Load disaster events
async function loadEvents() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/events/latest?limit=50`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        eventsData = data.events;
        
        displayEvents(eventsData);
        updateMap(eventsData);
        updateEventCount(eventsData.length);
        
    } catch (error) {
        console.error('Failed to load events:', error);
        document.getElementById('events-list').innerHTML = 
            '<div class="loading-spinner">Failed to load events. Retrying...</div>';
        setTimeout(loadEvents, 5000);
    }
}

// Display events in grid
function displayEvents(events) {
    const eventsList = document.getElementById('events-list');
    
    if (!events || events.length === 0) {
        eventsList.innerHTML = '<div class="loading-spinner">No disaster events found</div>';
        return;
    }
    
    eventsList.innerHTML = '';
    
    events.forEach(event => {
        const eventCard = createEventCard(event);
        eventsList.appendChild(eventCard);
    });
}

// Create event card element
function createEventCard(event) {
    const card = document.createElement('div');
    card.className = `event-card severity-${event.severity}`;
    
    card.innerHTML = `
        <div class="event-header">
            <div class="event-type">${event.disaster_type}</div>
            <span class="severity-badge severity-${event.severity}">${event.severity}</span>
        </div>
        <div class="event-details">
            <p><strong>Location:</strong> ${event.location}</p>
            <p><strong>Time:</strong> ${new Date(event.event_time).toLocaleString()}</p>
            <p><strong>Source:</strong> ${event.source}</p>
            ${event.risk_score ? `<div class="risk-score">Risk: ${parseFloat(event.risk_score).toFixed(1)}/10</div>` : ''}
        </div>
    `;
    
    return card;
}

// Update map with event markers
function updateMap(events) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    
    events.forEach(event => {
        if (event.latitude !== 0 || event.longitude !== 0) {
            const markerColor = getSeverityColor(event.severity);
            
            const marker = L.circleMarker([event.latitude, event.longitude], {
                radius: 8,
                fillColor: markerColor,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map);
            
            marker.bindPopup(`
                <strong>${event.disaster_type.toUpperCase()}</strong><br>
                <em>${event.severity} Alert</em><br>
                ${event.location}<br>
                Risk Score: ${event.risk_score ? parseFloat(event.risk_score).toFixed(1) : 'N/A'}/10<br>
                <small>${new Date(event.event_time).toLocaleString()}</small>
            `);
            
            markers.push(marker);
        }
    });
}

// Get color based on severity
function getSeverityColor(severity) {
    const colors = {
        'Red': '#dc2626',
        'Orange': '#f59e0b',
        'Green': '#10b981',
        'Unknown': '#6b7280'
    };
    return colors[severity] || colors['Unknown'];
}

// Filter events by type and severity
function filterEvents() {
    const typeFilter = document.getElementById('type-filter').value;
    const severityFilter = document.getElementById('severity-filter').value;
    
    let filteredEvents = eventsData;
    
    if (typeFilter) {
        filteredEvents = filteredEvents.filter(e => e.disaster_type === typeFilter);
    }
    
    if (severityFilter) {
        filteredEvents = filteredEvents.filter(e => e.severity === severityFilter);
    }
    
    displayEvents(filteredEvents);
    updateMap(filteredEvents);
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const stats = await response.json();
        displayStatistics(stats);
        
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
}

// Display statistics
function displayStatistics(stats) {
    document.getElementById('stat-total').textContent = stats.total_events || 0;
    document.getElementById('stat-avg-risk').textContent = stats.avg_risk_score ? 
        stats.avg_risk_score.toFixed(1) : '0.0';
    document.getElementById('stat-high-risk').textContent = stats.high_risk_count || 0;
    document.getElementById('stat-red-alerts').textContent = stats.by_severity?.Red || 0;
    
    // Update charts
    updateTypeChart(stats.by_type || {});
    updateSeverityChart(stats.by_severity || {});
}

// Update disaster type chart
function updateTypeChart(byType) {
    const ctx = document.getElementById('type-chart');
    
    if (window.typeChart) {
        window.typeChart.destroy();
    }
    
    window.typeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(byType).map(k => k.charAt(0).toUpperCase() + k.slice(1)),
            datasets: [{
                data: Object.values(byType),
                backgroundColor: [
                    '#ef4444', '#f59e0b', '#10b981', '#3b82f6', 
                    '#8b5cf6', '#ec4899', '#14b8a6'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#cbd5e1'
                    }
                }
            }
        }
    });
}

// Update severity chart
function updateSeverityChart(bySeverity) {
    const ctx = document.getElementById('severity-chart');
    
    if (window.severityChart) {
        window.severityChart.destroy();
    }
    
    window.severityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(bySeverity),
            datasets: [{
                label: 'Events by Severity',
                data: Object.values(bySeverity),
                backgroundColor: ['#dc2626', '#f59e0b', '#10b981', '#6b7280']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#cbd5e1'
                    },
                    grid: {
                        color: '#334155'
                    }
                },
                x: {
                    ticks: {
                        color: '#cbd5e1'
                    },
                    grid: {
                        color: '#334155'
                    }
                }
            }
        }
    });
}

// Update event count display
function updateEventCount(count) {
    document.getElementById('active-events-count').textContent = count;
}

// Show notification
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Expose functions for debugging
window.DisasterLensDebug = {
    loadEvents,
    loadStatistics,
    reconnectWebSocket: initializeWebSocket
};
