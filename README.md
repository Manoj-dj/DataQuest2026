# 🌍 DisasterLens AI - Real-Time Climate Emergency Intelligence System

<div align="center">

![DisasterLens AI](https://img.shields.io/badge/DisasterLens-AI-blue?style=for-the-badge)
![Pathway](https://img.shields.io/badge/Pathway-Streaming-green?style=for-the-badge)
![React](https://img.shields.io/badge/React-18.2-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal?style=for-the-badge)

**Real-time disaster intelligence with Pathway streaming, RAG, and multi-modal analysis**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Real-Time Streaming](#-real-time--streaming-functionality) • [API Documentation](#-api-endpoints)

</div>

---

## 📋 Project Title and Brief Description

### Project Title
**DisasterLens AI - Real-Time Climate Emergency Intelligence System**

### Brief Description
DisasterLens AI is an intelligent disaster monitoring and early-warning system that aggregates real-time disaster data from multiple sources (GDACS, NewsAPI, NASA EONET), processes it through Pathway's high-performance streaming engine, and provides interactive RAG-powered queries with multi-modal analysis. The system enables emergency responders, government agencies, and citizens to make informed decisions during climate emergencies through real-time alerts, predictive analytics, and explainable AI insights.

### Key Highlights
- ⚡ **Real-Time Streaming**: Pathway-based event ingestion with sub-second latency
- 🤖 **Advanced RAG**: GPT-4 powered intelligent queries with historical disaster correlation
- 🔮 **Predictive Intelligence**: AI-powered disaster impact predictions using historical patterns
- 📊 **Explainable Alerts**: Transparent risk assessment with contributing signal analysis
- 🗺️ **Interactive Visualization**: Live disaster maps with real-time updates
- 🎯 **Multi-Role Support**: Customizable alert settings for citizens, responders, and administrators

---

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Sources Layer                            │
├──────────────┬──────────────┬──────────────────────────────────┤
│  GDACS RSS   │  NewsAPI     │   NASA EONET                     │
│   (Python)   │   (REST)     │    (REST)                        │
│  Polling:    │  Polling:    │   Polling:                       │
│  120s        │  180s        │   3600s                          │
└──────┬───────┴──────┬───────┴──────┬───────────────────────────┘
       │              │              │
       └──────────────┼──────────────┘
                      │
            ┌─────────▼─────────┐
            │  Pathway Stream    │
            │   Engine (Rust)   │
            │  ───────────────── │
            │  • Transformations │
            │  • Risk Scoring    │
            │  • Deduplication   │
            │  • Pattern Detect  │
            │  • Real-time Proc  │
            └─────────┬─────────┘
                      │
       ┌──────────────┼──────────────┐
       │              │              │
┌──────▼──────┐ ┌─────▼──────┐ ┌────▼───────┐
│  ChromaDB   │ │  Embedder  │ │  LLM (GPT) │
│ Vector Store│ │  (CLIP)    │ │   Interface│
│             │ │            │ │            │
│ • Text      │ │ • Sentence │ │ • GPT-4o   │
│   Embeddings│ │   Transform│ │ • Vision   │
│ • Metadata  │ │ • CLIP     │ │ • RAG      │
│ • Indexing  │ │            │ │            │
└──────┬──────┘ └────────────┘ └────┬───────┘
       │                             │
       └─────────────┬───────────────┘
                     │
            ┌────────▼────────┐
            │   FastAPI       │
            │   REST + WS     │
            │  ────────────── │
            │  • REST API     │
            │  • WebSocket    │
            │  • Real-time    │
            │    Streaming    │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │  React Frontend │
            │  + Leaflet Map  │
            │  ────────────── │
            │  • Dashboard    │
            │  • Predictions  │
            │  • Alerts       │
            │  • Simulator    │
            └─────────────────┘
```

### Component Breakdown

#### 1. **Data Ingestion Layer**
- **GDACS Connector**: Fetches disaster alerts from Global Disaster Alert and Coordination System RSS feed
- **NewsAPI Connector**: Retrieves disaster-related news articles via REST API
- **NASA EONET Connector**: Pulls natural event data from NASA's Earth Observatory Natural Event Tracker

#### 2. **Pathway Streaming Engine**
- **Real-Time Processing**: Rust-based engine for high-performance streaming
- **Transformations**: Event normalization, enrichment, and risk scoring
- **Pattern Detection**: Spatial clustering, cascading disaster detection, severity escalation
- **Deduplication**: Automatic event deduplication across sources
- **Incremental Updates**: Only processes new/changed events

#### 3. **Vector Store & RAG System**
- **ChromaDB**: Persistent vector database for semantic search
- **Embedding Service**: Sentence-Transformers for text, CLIP for images
- **LLM Interface**: OpenAI GPT-4o for intelligent query responses
- **Historical Correlation**: Vector similarity search for pattern matching

#### 4. **API Layer**
- **FastAPI**: RESTful API with automatic OpenAPI documentation
- **WebSocket**: Real-time event streaming to frontend
- **Endpoints**: Query, events, predictions, alerts, settings, simulation

#### 5. **Frontend**
- **React 18**: Modern UI framework with hooks
- **Vite**: Fast build tool with HMR
- **Leaflet**: Interactive map visualization
- **Tailwind CSS**: Utility-first styling
- **Recharts**: Data visualization

---

## 🚀 Step-by-Step Setup and Execution Instructions

### Prerequisites

- **Python 3.11+** (3.12 recommended)
- **Node.js 18+** (for frontend)
- **`uv` package manager** (recommended) or `pip`
- **WSL/Unix environment** (Linux recommended, Windows WSL works)
- **OpenAI API Key** (required for RAG functionality)
- **NewsAPI Key** (optional, for NewsAPI connector)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd DataQuest2026
```

### Step 2: Install Python Dependencies

#### Option A: Using `uv` (Recommended)
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/Mac/WSL
# OR
.venv\Scripts\activate  # On Windows

# Install dependencies
uv pip install -r requirements.txt --index-strategy unsafe-best-match
```

#### Option B: Using `pip`
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/Mac/WSL
# OR
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (but recommended)
NEWSAPI_KEY=your_newsapi_key_here  # For NewsAPI connector

# Optional Configuration
GDACS_RSS_URL=https://www.gdacs.org/xml/rss.xml
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
OPENAI_MODEL=gpt-4o-mini
APP_HOST=0.0.0.0
APP_PORT=8080
```

**Note**: You can get an OpenAI API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### Step 5: Start Backend Server

#### Using the provided script:
```bash
chmod +x run_backend.sh
./run_backend.sh
```

#### Or manually:
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run the backend
python3 src/main.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     Pathway streaming mode: ENABLED
INFO:     Using Pathway version: 0.13.1
```

The backend will:
- Initialize ChromaDB vector store (creates `chroma_db/` directory)
- Start Pathway streaming pipeline (GDACS, NewsAPI, NASA EONET)
- Load embedding models (text + CLIP image embeddings)
- Start FastAPI server on port 8080
- Begin ingesting disaster events in real-time

### Step 6: Start Frontend (Separate Terminal)

```bash
# Navigate to frontend directory
cd frontend

# Start development server
npm run dev
```

**Expected Output:**
```
  VITE v5.0.11  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

Frontend runs on `http://localhost:3000`

### Step 7: Access the Application

1. **Open Browser**: Navigate to `http://localhost:3000`
2. **Wait for Data**: The system will start ingesting events (may take 1-2 minutes for initial data)
3. **Explore Features**:
   - **Dashboard**: View global statistics and charts
   - **Events**: Browse recent disaster events
   - **Map**: Interactive map with live event markers
   - **Query**: Ask natural language questions about disasters
   - **Predictions**: View AI-powered disaster predictions
   - **Explainable Alerts**: See alerts with contributing signals
   - **Scenario Simulator**: Test "what-if" disaster scenarios
   - **Past Events**: Review prediction accuracy
   - **Alert Settings**: Configure role-based alert preferences

### Step 8: Verify System is Working

#### Check Backend Health:
```bash
curl http://localhost:8080/api/health
```

Should return:
```json
{
  "status": "healthy",
  "events_count": <number>,
  "uptime": "<time>",
  "components": {
    "pathway": "running",
    "vector_store": "connected",
    "llm": "ready",
    "api": "operational"
  }
}
```

#### Check Frontend:
- Open `http://localhost:3000` in browser
- You should see the DisasterLens AI interface
- Check browser console (F12) for any errors

---

## ⚡ Real-Time / Streaming Functionality

### Pathway Streaming Engine

DisasterLens AI leverages **Pathway 0.13.1** for real-time data processing. Pathway is a Rust-based streaming engine that provides:

- **Sub-second latency**: Events are processed as they arrive
- **Incremental updates**: Only new/changed events trigger processing
- **Automatic deduplication**: Prevents duplicate events across sources
- **Transformations**: Real-time risk scoring, enrichment, and pattern detection

### Streaming Architecture

#### 1. **Data Source Connectors**

Each connector implements a polling mechanism that feeds data into Pathway:

```python
# GDACS Connector (src/connectors/gdacs_connector.py)
- Polls GDACS RSS feed every 120 seconds
- Parses XML/RSS format
- Extracts: disaster type, severity, location, magnitude, population affected

# NewsAPI Connector (src/connectors/newsapi_connector.py)
- Polls NewsAPI REST endpoint every 180 seconds
- Searches for disaster-related keywords
- Extracts: article text, location, sentiment

# NASA EONET Connector (src/connectors/nasa_eonet_connector.py)
- Polls NASA EONET API every 3600 seconds (1 hour)
- Retrieves natural event data
- Extracts: event type, coordinates, imagery URLs
```

#### 2. **Pathway Pipeline Construction**

The streaming pipeline is built in `src/pipeline/disaster_stream.py`:

```python
def build_pipeline(self) -> pw.Table:
    # Create Pathway schema
    schema = pw.schema_builder({
        'event_id': pw.column_definition(dtype=str),
        'disaster_type': pw.column_definition(dtype=str),
        'severity': pw.column_definition(dtype=str),
        # ... more fields
    })
    
    # Create connector subjects (data sources)
    gdacs_subject = DisasterConnectorSubject(self.gdacs_connector)
    news_subject = DisasterConnectorSubject(self.news_connector)
    nasa_subject = DisasterConnectorSubject(self.nasa_eonet_connector)
    
    # Create Pathway streams
    gdacs_stream = pw.io.python.read(gdacs_subject, schema=schema)
    news_stream = pw.io.python.read(news_subject, schema=schema)
    nasa_stream = pw.io.python.read(nasa_subject, schema=schema)
    
    # Combine all streams
    all_events = gdacs_stream.concat(news_stream).concat(nasa_stream)
    
    # Apply transformations
    enriched_events = all_events.select(
        *[pw.this[col] for col in all_events.column_names()],
        risk_score=calculate_risk_score(...),
        imagery_urls_json=generate_imagery_urls(...)
    )
    
    return enriched_events
```

#### 3. **Real-Time Processing Flow**

```
New Event Arrives
      ↓
Pathway Stream Engine (Rust)
      ↓
Transformations Applied:
  • Risk Scoring
  • Imagery URL Generation
  • Metadata Enrichment
  • Pattern Detection
      ↓
on_change() Callback Triggered
      ↓
Parallel Processing:
  ├─→ ChromaDB Indexing (Vector Store)
  ├─→ Embedding Generation (Text + Image)
  └─→ WebSocket Broadcast (Frontend)
      ↓
Frontend Receives Update (Real-Time)
```

#### 4. **WebSocket Real-Time Updates**

The system uses WebSocket for live event streaming:

**Backend** (`src/api/websocket_handler.py`):
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Send events as they arrive
    await websocket.send_json({
        "type": "new_event",
        "event": event_data,
        "timestamp": datetime.now().isoformat()
    })
```

**Frontend** (`frontend/src/hooks/useWebSocket.js`):
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'new_event') {
        // Update UI in real-time
        updateEventsList(data.event);
        updateMapMarker(data.event);
    }
};
```

#### 5. **Pattern Detection (Real-Time)**

Pathway's streaming capabilities enable real-time pattern detection:

**Spatial Clustering** (`src/pipeline/pattern_detection.py`):
```python
# Detect multiple disasters in same region
windowed_events = events.windowby(
    pw.this.timestamp,
    window=pw.temporal.sliding(
        hop=timedelta(minutes=5),
        duration=timedelta(hours=24)
    )
)

# Group by geographic region
clusters = windowed_events.reduce(
    event_count=pw.reducers.count(),
    locations=pw.reducers.unique(pw.this.location)
)
```

**Cascading Disaster Detection**:
- Detects earthquake → tsunami risk
- Detects wildfire → smoke pollution risk
- Detects multiple disasters in proximity

**Severity Escalation**:
- Tracks increasing severity over time windows
- Alerts when disaster conditions worsen

#### 6. **Real-Time Metrics**

The system provides real-time metrics:

- **Event Count**: Updated as new events arrive
- **Risk Score Distribution**: Calculated in real-time
- **Severity Breakdown**: Red/Orange/Green alerts
- **Geographic Distribution**: Heat maps update live

### Streaming Performance

- **Latency**: < 1 second from event arrival to frontend display
- **Throughput**: Handles 100+ events/minute
- **Memory Efficiency**: Pathway's incremental processing minimizes memory usage
- **Fault Tolerance**: Automatic reconnection and error recovery

### Monitoring Real-Time Streams

Check Pathway streaming status:
```bash
# View backend logs
tail -f logs/disasterlens_*.log

# Look for:
# "Pathway streaming mode: ENABLED"
# "New event received from GDACS"
# "Event indexed in vector store"
```

---

## 📡 API Endpoints

### REST API (Port 8080)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System health check |
| `/api/query` | POST | RAG query endpoint |
| `/api/events/latest` | GET | Get latest events (for map) |
| `/api/events/{event_id}` | GET | Get specific event details |
| `/api/stats` | GET | Statistics dashboard data |
| `/api/predictions` | GET | Get disaster predictions |
| `/api/alerts/recent` | GET | Get explainable alerts |
| `/api/alerts/{id}/impact` | POST | Update post-event impact |
| `/api/simulate` | POST | Scenario simulator |
| `/api/alert-settings/{role}` | GET/PUT | Alert settings management |

### WebSocket (Port 8080)

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/ws` | WebSocket | Real-time event streaming |
| `/ws/predictions` | WebSocket | Live prediction alerts |

### API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

---

## 📁 Project Structure

```
DataQuest2026/
├── src/                          # Backend source code
│   ├── api/                      # FastAPI endpoints
│   │   ├── server.py            # REST API routes
│   │   └── websocket_handler.py # WebSocket for real-time updates
│   ├── connectors/              # Data source connectors
│   │   ├── base_connector.py
│   │   ├── gdacs_connector.py   # GDACS RSS feed
│   │   ├── newsapi_connector.py # NewsAPI articles
│   │   └── nasa_eonet_connector.py # NASA EONET events
│   ├── pipeline/                # Pathway streaming pipeline
│   │   ├── disaster_stream.py   # Main pipeline logic
│   │   ├── pattern_detection.py # Pattern detection
│   │   └── risk_scoring.py      # Risk calculation engine
│   ├── rag/                     # RAG components
│   │   ├── embedder.py          # Text + image embeddings
│   │   ├── llm_interface.py     # OpenAI GPT-4 interface
│   │   └── vector_store.py      # ChromaDB vector store
│   ├── utils/                   # Utilities
│   │   ├── logger.py            # Logging system
│   │   ├── schemas.py           # Data schemas
│   │   └── imagery_utils.py     # Image URL generation
│   └── main.py                  # Application entry point
│
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── Dashboard/      # Statistics dashboard
│   │   │   ├── Events/         # Event list/cards
│   │   │   ├── Map/            # Leaflet map component
│   │   │   ├── Query/          # RAG query panel
│   │   │   ├── Predictions/    # Predictions dashboard
│   │   │   ├── Alerts/         # Explainable alerts
│   │   │   ├── Simulator/      # Scenario simulator
│   │   │   ├── Settings/       # Alert settings
│   │   │   ├── Imagery/        # Image gallery/modal
│   │   │   ├── Header/         # App header
│   │   │   └── Sidebar/        # Navigation sidebar
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # API services
│   │   └── utils/               # Frontend utilities
│   ├── public/                  # Static assets
│   └── package.json
│
├── config/                       # Configuration files
│   └── config.yaml              # Application configuration
│
├── requirements.txt              # Python dependencies
├── run_backend.sh               # Backend startup script
└── README.md                     # This file
```

---

## 🧪 Testing

### Run Backend Tests
```bash
# Test all endpoints
python3 test_backend.py

# Test specific features
python3 test_simulate.py
```

### Manual Testing
```bash
# Test API health
curl http://localhost:8080/api/health

# Test RAG query
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me recent earthquakes"}'

# Test events endpoint
curl http://localhost:8080/api/events/latest?limit=10
```

---

## 🛠️ Technology Stack

### Backend
- **Pathway 0.13.1**: Real-time streaming engine (Rust-based)
- **FastAPI 0.109**: REST API framework
- **ChromaDB 0.5.15+**: Vector database
- **OpenAI GPT-4o**: LLM for RAG
- **Sentence-Transformers**: Text embeddings
- **CLIP**: Image embeddings
- **Uvicorn**: ASGI server

### Frontend
- **React 18.2**: UI framework
- **Vite 5**: Build tool
- **Tailwind CSS**: Styling
- **React Leaflet**: Map component
- **Recharts**: Data visualization
- **Axios**: HTTP client

---

## 🐛 Troubleshooting

### Backend Issues

**ChromaDB Errors:**
```bash
# Reset ChromaDB database
rm -rf chroma_db
# Restart backend - it will recreate
```

**Pathway Errors:**
```bash
# Check Pathway version
python3 -c "import pathway as pw; print(pw.__version__)"
# Should output: 0.13.1
```

**Port Already in Use:**
```bash
# Find process using port 8080
lsof -i :8080  # Linux/Mac
netstat -ano | findstr :8080  # Windows

# Kill process
kill -9 <PID>
```

### Frontend Issues

**Connection Errors:**
- Ensure backend is running on port 8080
- Check CORS settings in `src/api/server.py`
- Verify WebSocket endpoint is accessible

**Build Errors:**
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

---

## 📝 License

This project is developed for DataQuest 2026 hackathon.

---

## 🙏 Acknowledgments

- **GDACS**: Global Disaster Alert and Coordination System
- **NASA EONET**: Earth Observatory Natural Event Tracker
- **Pathway**: Real-time data processing engine
- **OpenAI**: GPT-4 Vision API

---

<div align="center">

**Built with ❤️ for real-time disaster intelligence**

[Report Issues](https://github.com/your-repo/issues) • [Documentation](./docs/) • [Contributing](./CONTRIBUTING.md)

</div>
