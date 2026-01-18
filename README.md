# 🌍 DisasterLens AI - Real-Time Climate Emergency Intelligence System

<div align="center">

![DisasterLens AI](https://img.shields.io/badge/DisasterLens-AI-blue?style=for-the-badge)
![Pathway](https://img.shields.io/badge/Pathway-Streaming-green?style=for-the-badge)
![React](https://img.shields.io/badge/React-18.2-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal?style=for-the-badge)

**Real-time disaster intelligence with Pathway streaming, RAG, and multi-modal analysis**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Documentation](#-documentation)

</div>

---

## 🎯 Overview

DisasterLens AI is an intelligent disaster monitoring system that aggregates real-time disaster data from multiple sources (GDACS, NewsAPI, NASA EONET), processes it through Pathway's streaming engine, and provides interactive RAG-powered queries with multi-modal analysis.

### Key Capabilities

- 🔄 **Real-Time Streaming**: Pathway-based event ingestion from 3+ data sources
- 🤖 **RAG System**: OpenAI GPT-4 powered intelligent queries with semantic search
- 🗺️ **Interactive Maps**: Live disaster event visualization with Leaflet
- 📊 **Analytics Dashboard**: Real-time statistics and risk assessment
- 🖼️ **Multi-Modal Analysis**: GPT-4 Vision for satellite imagery analysis
- ⚡ **Sub-Second Latency**: Pathway's Rust engine for high-performance streaming

---

## ✨ Features

### 🔍 Intelligent Query System
- Natural language disaster queries
- Semantic search with ChromaDB vector store
- Contextual responses with source citations
- Risk assessment and severity analysis

### 🗺️ Live Disaster Map
- Real-time event visualization
- Color-coded severity indicators (Red/Orange/Green)
- Interactive markers with detailed popups
- Geographic clustering and filtering

### 📈 Analytics Dashboard
- Event statistics by type and severity
- Risk score distribution
- Temporal analysis charts
- Population impact metrics

### 🖼️ Multi-Modal Analysis
- Satellite imagery integration (NASA Worldview)
- GPT-4 Vision for image analysis
- Enhanced event context with visual data
- CLIP embeddings for image similarity search

### ⚡ Real-Time Updates
- WebSocket live event streaming
- Automatic data refresh every 2 minutes
- Pathway incremental processing
- Zero-downtime updates

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- `uv` package manager (recommended) or `pip`
- WSL/Unix environment (Linux recommended)

### Installation

#### 1. Clone Repository
```bash
git clone <repository-url>
cd DataQuest2026
```

#### 2. Install Python Dependencies
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt --index-strategy unsafe-best-match

# OR using pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

#### 4. Configure Environment Variables
Create a `.env` file in the project root:
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
NEWSAPI_KEY=your_newsapi_key_here  # For NewsAPI connector
GDACS_RSS_URL=https://www.gdacs.org/xml/rss.xml
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
OPENAI_MODEL=gpt-4o-mini
APP_HOST=0.0.0.0
APP_PORT=8080
```

#### 5. Start Backend
```bash
chmod +x run_backend.sh
./run_backend.sh
```

The backend will:
- Initialize ChromaDB vector store
- Start Pathway streaming pipeline (GDACS, NewsAPI, NASA EONET)
- Load embedding models (text + CLIP image embeddings)
- Start FastAPI server on port 8080

#### 6. Start Frontend (Separate Terminal)
```bash
cd frontend
npm run dev
```

Frontend runs on `http://localhost:3000`

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
│   │   │   ├── Imagery/        # Image gallery/modal
│   │   │   ├── Header/         # App header
│   │   │   └── Sidebar/        # Navigation sidebar
│   │   ├── hooks/               # Custom React hooks
│   │   │   ├── useDisasterEvents.js
│   │   │   ├── useImagery.js
│   │   │   ├── useStatistics.js
│   │   │   └── useWebSocket.js
│   │   ├── services/            # API services
│   │   │   ├── api.js           # Axios HTTP client
│   │   │   └── websocket.js     # WebSocket client
│   │   └── utils/               # Frontend utilities
│   │       ├── constants.js
│   │       └── formatters.js
│   ├── public/                  # Static assets
│   └── package.json
│
├── config/                       # Configuration files
│   └── config.yaml              # Application configuration
│
├── logs/                         # Application logs
│   └── disasterlens_*.log
│
├── chroma_db/                    # ChromaDB persistence
│
├── tests/                        # Test files
│   └── test_connectors.py
│
├── requirements.txt              # Python dependencies
├── run_backend.sh               # Backend startup script
├── start_frontend.sh            # Frontend startup script
└── README.md                     # This file
```

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Data Sources                          │
├──────────────┬──────────────┬──────────────────────────┤
│  GDACS RSS   │  NewsAPI     │   NASA EONET             │
│   (Python)   │   (REST)     │    (REST)                │
└──────┬───────┴──────┬───────┴──────┬───────────────────┘
       │              │              │
       └──────────────┼──────────────┘
                      │
            ┌─────────▼─────────┐
            │  Pathway Stream   │
            │   Engine (Rust)   │
            │  - Transformations│
            │  - Risk Scoring   │
            │  - Deduplication  │
            └─────────┬─────────┘
                      │
       ┌──────────────┼──────────────┐
       │              │              │
┌──────▼──────┐ ┌─────▼──────┐ ┌────▼───────┐
│  ChromaDB   │ │  Embedder  │ │  LLM (GPT) │
│ Vector Store│ │  (CLIP)    │ │   Interface│
└──────┬──────┘ └────────────┘ └────┬───────┘
       │                             │
       └─────────────┬───────────────┘
                     │
            ┌────────▼────────┐
            │   FastAPI       │
            │   REST + WS     │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │  React Frontend │
            │  + Leaflet Map  │
            └─────────────────┘
```

### Data Flow

1. **Ingestion**: Connectors fetch events from GDACS, NewsAPI, NASA EONET
2. **Streaming**: Pathway processes events in real-time (transformations, risk scoring)
3. **Embedding**: Text and image embeddings generated for vector search
4. **Storage**: Events indexed in ChromaDB with metadata and embeddings
5. **Query**: RAG system retrieves relevant events and generates GPT-4 responses
6. **Display**: Frontend visualizes events on map, dashboard, and query results

---

## 🔧 Configuration

### Backend Configuration (`config/config.yaml`)

```yaml
data_sources:
  gdacs:
    enabled: true
    url: https://www.gdacs.org/xml/rss.xml
    polling_interval: 120
  
  newsapi:
    enabled: true
    query: "disaster earthquake wildfire flood"
    polling_interval: 180
  
  nasa_eonet:
    enabled: true
    api_url: https://eonet.gsfc.nasa.gov/api/v3/events
    polling_interval: 3600

vector_store:
  collection_name: disaster_events

llm:
  temperature: 0.2
  max_tokens: 1000

risk_scoring:
  severity_weights:
    Red: 10
    Orange: 7
    Green: 3
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
| `/api/debug/events` | GET | Debug endpoint (dev only) |

### WebSocket (Port 8080)

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/ws` | WebSocket | Real-time event streaming |

---

## 🧪 Testing

### Run Tests
```bash
# Backend tests
pytest tests/

# Frontend tests (if configured)
cd frontend
npm test
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

## 🛠️ Development

### Backend Development
```bash
# Activate virtual environment
source .venv/bin/activate

# Run in debug mode
python src/main.py

# Check logs
tail -f logs/disasterlens_*.log
```

### Frontend Development
```bash
cd frontend
npm run dev  # Starts Vite dev server with HMR
```

### Adding New Data Sources

1. Create connector in `src/connectors/` extending `BaseDisasterConnector`
2. Add to `src/pipeline/disaster_stream.py` `build_pipeline()`
3. Update `config/config.yaml` with connector settings

---

## 📊 Technology Stack

### Backend
- **Pathway 0.13.1**: Real-time streaming engine
- **FastAPI 0.109**: REST API framework
- **ChromaDB 0.5.0+**: Vector database
- **OpenAI GPT-4**: LLM for RAG
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
- **Marked**: Markdown parser

---

## 🐛 Troubleshooting

### ChromaDB Issues
```bash
# Reset ChromaDB database
rm -rf chroma_db
# Restart backend - it will recreate
```

### Pathway Errors
```bash
# Check Pathway version
python -c "import pathway as pw; print(pw.__version__)"

# Verify Pathway installation
python check_pathway_installation.py
```

### Frontend Connection Issues
- Ensure backend is running on port 8080
- Check CORS settings in `src/api/server.py`
- Verify WebSocket endpoint is accessible

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
