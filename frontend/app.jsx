const { useState, useEffect, useRef, useCallback } = React;

// API Configuration
const API_BASE_URL = window.location.origin;
const WS_URL = `ws://${window.location.host}/ws`;

// Main App Component
function App() {
    const [wsConnected, setWsConnected] = useState(false);
    const [activeEvents, setActiveEvents] = useState(0);
    const [query, setQuery] = useState('');
    const [queryResponse, setQueryResponse] = useState(null);
    const [loading, setLoading] = useState(false);
    const [events, setEvents] = useState([]);
    const [filteredEvents, setFilteredEvents] = useState([]);
    const [stats, setStats] = useState(null);
    const [typeFilter, setTypeFilter] = useState('');
    const [severityFilter, setSeverityFilter] = useState('');
    const wsRef = useRef(null);
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const markersRef = useRef([]);
    const typeChartRef = useRef(null);
    const severityChartRef = useRef(null);
    const reconnectAttemptsRef = useRef(0);

    // Initialize Map
    useEffect(() => {
        if (!mapInstanceRef.current) {
            mapInstanceRef.current = L.map('map').setView([20, 0], 2);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors',
                maxZoom: 18
            }).addTo(mapInstanceRef.current);
        }
        return () => {
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }
        };
    }, []);

    // WebSocket Connection
    useEffect(() => {
        const connectWebSocket = () => {
            try {
                const ws = new WebSocket(WS_URL);
                wsRef.current = ws;

                ws.onopen = () => {
                    console.log('WebSocket connected');
                    reconnectAttemptsRef.current = 0;
                    setWsConnected(true);
                    showNotification('Connected to real-time stream', 'success');
                };

                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.type === 'new_event') {
                        showNotification(`New ${data.event.disaster_type} detected`, 'warning');
                        loadEvents();
                        loadStatistics();
                    }
                };

                ws.onerror = () => {
                    setWsConnected(false);
                };

                ws.onclose = () => {
                    setWsConnected(false);
                    if (reconnectAttemptsRef.current < 5) {
                        reconnectAttemptsRef.current++;
                        setTimeout(connectWebSocket, 3000 * reconnectAttemptsRef.current);
                    }
                };
            } catch (error) {
                console.error('WebSocket error:', error);
                setWsConnected(false);
            }
        };

        connectWebSocket();
        return () => {
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    // Load Events
    const loadEvents = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/events/latest?limit=50`);
            const data = await response.json();
            setEvents(data.events || []);
            setFilteredEvents(data.events || []);
            updateMap(data.events || []);
        } catch (error) {
            console.error('Failed to load events:', error);
        }
    }, []);

    // Load Statistics
    const loadStatistics = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/stats`);
            const data = await response.json();
            setStats(data);
            updateCharts(data);
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }, []);

    // Update Map
    const updateMap = (eventsList) => {
        if (!mapInstanceRef.current) return;
        markersRef.current.forEach(marker => mapInstanceRef.current.removeLayer(marker));
        markersRef.current = [];

        eventsList.forEach(event => {
            if (event.latitude !== 0 || event.longitude !== 0) {
                const color = getSeverityColor(event.severity);
                const marker = L.circleMarker([event.latitude, event.longitude], {
                    radius: 10,
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(mapInstanceRef.current);

                marker.bindPopup(`
                    <strong>${event.disaster_type?.toUpperCase()}</strong><br>
                    <em>${event.severity} Alert</em><br>
                    ${event.location || 'Unknown'}<br>
                    Risk: ${event.risk_score ? parseFloat(event.risk_score).toFixed(1) : 'N/A'}/10
                `);
                markersRef.current.push(marker);
            }
        });
    };

    const getSeverityColor = (severity) => {
        const colors = { 'Red': '#dc2626', 'Orange': '#f59e0b', 'Green': '#10b981', 'Unknown': '#6b7280' };
        return colors[severity] || colors['Unknown'];
    };

    // Update Charts
    const updateCharts = (statsData) => {
        if (typeChartRef.current && statsData.by_type) {
            const ctx = document.getElementById('type-chart');
            if (window.typeChart) window.typeChart.destroy();
            window.typeChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(statsData.by_type).map(k => k.charAt(0).toUpperCase() + k.slice(1)),
                    datasets: [{
                        data: Object.values(statsData.by_type),
                        backgroundColor: ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6']
                    }]
                },
                options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
            });
        }

        if (severityChartRef.current && statsData.by_severity) {
            const ctx = document.getElementById('severity-chart');
            if (window.severityChart) window.severityChart.destroy();
            window.severityChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(statsData.by_severity),
                    datasets: [{
                        label: 'Events',
                        data: Object.values(statsData.by_severity),
                        backgroundColor: ['#dc2626', '#f59e0b', '#10b981', '#6b7280']
                    }]
                },
                options: { responsive: true, plugins: { legend: { display: false } } }
            });
        }
    };

    // Handle Query Submission
    const handleQuery = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        try {
            const startTime = performance.now();
            const response = await fetch(`${API_BASE_URL}/api/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, top_k: 5 })
            });
            const data = await response.json();
            const latency = performance.now() - startTime;
            setQueryResponse({ ...data, clientLatency: latency });
        } catch (error) {
            console.error('Query failed:', error);
        } finally {
            setLoading(false);
        }
    };

    // Filter Events
    useEffect(() => {
        let filtered = events;
        if (typeFilter) filtered = filtered.filter(e => e.disaster_type === typeFilter);
        if (severityFilter) filtered = filtered.filter(e => e.severity === severityFilter);
        setFilteredEvents(filtered);
        updateMap(filtered);
    }, [typeFilter, severityFilter, events]);

    // Initial Load
    useEffect(() => {
        loadEvents();
        loadStatistics();
        const interval1 = setInterval(loadEvents, 120000);
        const interval2 = setInterval(loadStatistics, 120000);
        return () => { clearInterval(interval1); clearInterval(interval2); };
    }, [loadEvents, loadStatistics]);

    // Notification
    const showNotification = (message, type) => {
        const container = document.getElementById('notification-container');
        const notif = document.createElement('div');
        notif.className = `notification ${type}`;
        notif.textContent = message;
        container.appendChild(notif);
        setTimeout(() => notif.remove(), 5000);
    };

    return (
        <div className="app-container">
            <Header wsConnected={wsConnected} activeEvents={stats?.total_events || 0} />
            <main className="main-content">
                <QueryPanel query={query} setQuery={setQuery} handleQuery={handleQuery} loading={loading} 
                           response={queryResponse} />
                <MapSection mapRef={mapRef} />
                <EventsSection events={filteredEvents} typeFilter={typeFilter} setTypeFilter={setTypeFilter}
                              severityFilter={severityFilter} setSeverityFilter={setSeverityFilter}
                              onRefresh={loadEvents} />
                <StatisticsSection stats={stats} />
            </main>
            <div id="notification-container"></div>
        </div>
    );
}

// Header Component
function Header({ wsConnected, activeEvents }) {
    return (
        <header className="app-header">
            <div className="header-left">
                <h1 className="logo-title">
                    <span className="logo-icon">🌍</span>
                    DisasterLens AI
                </h1>
                <p className="tagline">Real-Time Climate Emergency Intelligence System</p>
            </div>
            <div className="header-right">
                <div className={`status-badge ${wsConnected ? 'connected' : 'disconnected'}`}>
                    <span className="status-dot"></span>
                    <span>{wsConnected ? 'Connected' : 'Disconnected'}</span>
                </div>
                <div className="active-events-badge">
                    <span className="events-count">{activeEvents}</span>
                    <span>Active Events</span>
                </div>
            </div>
        </header>
    );
}

// Query Panel Component
function QueryPanel({ query, setQuery, handleQuery, loading, response }) {
    const quickQueries = [
        "What are the most severe disasters right now?",
        "Show me all earthquakes in the last 48 hours",
        "Which wildfires are currently active?",
        "What disasters affect populated areas?"
    ];

    return (
        <section className="query-section">
            <div className="query-panel">
                <h2 className="section-title">Ask About Current Disasters</h2>
                <form onSubmit={handleQuery} className="query-form">
                    <div className="input-group">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="e.g., What earthquakes happened in the last 24 hours?"
                            className="query-input"
                        />
                        <button type="submit" className="query-button" disabled={loading}>
                            {loading ? <span className="spinner"></span> : 'Query'}
                        </button>
                    </div>
                    <div className="quick-queries">
                        <span className="quick-label">Quick queries:</span>
                        {quickQueries.map((q, i) => (
                            <button key={i} type="button" className="quick-btn" onClick={() => setQuery(q)}>
                                {q.split(' ').slice(0, 2).join(' ')}
                            </button>
                        ))}
                    </div>
                </form>

                {response && (
                    <div className="response-panel">
                        <div className="response-header">
                            <h3>Response</h3>
                            <div className="response-meta">
                                <span>{response.latency_ms?.toFixed(0)}ms</span>
                                <span>{new Date(response.timestamp).toLocaleTimeString()}</span>
                            </div>
                        </div>
                        <div className="response-content">{response.answer}</div>
                        {response.risk_assessment && (
                            <div className="risk-badge">{response.risk_assessment}</div>
                        )}
                        {response.sources?.length > 0 && (
                            <div className="sources-list">
                                <h4>Sources</h4>
                                {response.sources.map((src, i) => (
                                    <div key={i} className="source-item">
                                        <span className={`severity-chip ${src.severity}`}>{src.severity}</span>
                                        <span>{src.disaster_type} - {src.location}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </section>
    );
}

// Map Section Component
function MapSection() {
    return (
        <section className="map-section">
            <div className="map-panel">
                <h2 className="section-title">Live Disaster Map</h2>
                <div id="map" className="map-container"></div>
                <div className="map-legend">
                    <div className="legend-item"><span className="legend-dot red"></span>Red Alert</div>
                    <div className="legend-item"><span className="legend-dot orange"></span>Orange Alert</div>
                    <div className="legend-item"><span className="legend-dot green"></span>Green Alert</div>
                </div>
            </div>
        </section>
    );
}

// Events Section Component
function EventsSection({ events, typeFilter, setTypeFilter, severityFilter, setSeverityFilter, onRefresh }) {
    const getSeverityColor = (severity) => {
        const colors = { 'Red': '#dc2626', 'Orange': '#f59e0b', 'Green': '#10b981', 'Unknown': '#6b7280' };
        return colors[severity] || '#6b7280';
    };

    return (
        <section className="events-section">
            <div className="events-panel">
                <div className="events-header">
                    <h2 className="section-title">Recent Disaster Events</h2>
                    <button onClick={onRefresh} className="refresh-button">↻ Refresh</button>
                </div>
                <div className="filter-bar">
                    <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                        <option value="">All Types</option>
                        <option value="earthquake">Earthquake</option>
                        <option value="wildfire">Wildfire</option>
                        <option value="flood">Flood</option>
                        <option value="cyclone">Cyclone</option>
                        <option value="tsunami">Tsunami</option>
                        <option value="volcano">Volcano</option>
                    </select>
                    <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
                        <option value="">All Severities</option>
                        <option value="Red">Red Alert</option>
                        <option value="Orange">Orange Alert</option>
                        <option value="Green">Green Alert</option>
                    </select>
                </div>
                <div className="events-grid">
                    {events.length === 0 ? (
                        <div className="empty-state">Loading events...</div>
                    ) : (
                        events.map((event, i) => (
                            <div key={i} className="event-card">
                                <div className="event-header">
                                    <span className={`severity-badge ${event.severity}`}>{event.severity}</span>
                                    <span className="event-type">{event.disaster_type}</span>
                                </div>
                                <div className="event-location">{event.location}</div>
                                <div className="event-meta">
                                    <span>Risk: {event.risk_score ? parseFloat(event.risk_score).toFixed(1) : 'N/A'}/10</span>
                                    <span>{new Date(event.event_time).toLocaleDateString()}</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </section>
    );
}

// Statistics Section Component
function StatisticsSection({ stats }) {
    return (
        <section className="statistics-section">
            <div className="stats-panel">
                <h2 className="section-title">Global Statistics</h2>
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-value">{stats?.total_events || 0}</div>
                        <div className="stat-label">Total Events</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{stats?.avg_risk_score?.toFixed(1) || '0.0'}</div>
                        <div className="stat-label">Avg Risk Score</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{stats?.high_risk_count || 0}</div>
                        <div className="stat-label">High Risk Events</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{stats?.by_severity?.Red || 0}</div>
                        <div className="stat-label">Red Alerts</div>
                    </div>
                </div>
                <div className="charts-grid">
                    <div className="chart-container">
                        <h3>Events by Type</h3>
                        <canvas id="type-chart"></canvas>
                    </div>
                    <div className="chart-container">
                        <h3>Events by Severity</h3>
                        <canvas id="severity-chart"></canvas>
                    </div>
                </div>
            </div>
        </section>
    );
}

// Render App
ReactDOM.render(<App />, document.getElementById('root'));
