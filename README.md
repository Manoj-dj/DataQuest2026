# 🌍 DisasterLens AI - Real-Time Climate Emergency Intelligence System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pathway](https://img.shields.io/badge/Pathway-0.13.1-green.svg)](https://pathway.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **A production-ready Live AI system that reduces disaster response time from 8–12 hours to under 5 seconds through real-time RAG-powered intelligence.**

Built for **DataQuest 2026 Hackathon** at IIT Kharagpur, demonstrating Pathway’s streaming engine for dynamic, always-up-to-date climate/disaster intelligence.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Real-Time Demonstration](#real-time-demonstration)
- [Future Enhancements](#future-enhancements)
- [Acknowledgments](#acknowledgments)
- [License](#license)

---

## 🎯 Overview

DisasterLens AI is a **Live AI** application for real-time climate and disaster intelligence. Instead of stale, batch-updated systems, it maintains a continuously updated knowledge base that reacts within seconds when new events appear or existing information changes.

Traditional disaster dashboards suffer from:
- **Static knowledge**: Manual or batch re-indexing every few hours.
- **Delayed insight**: Critical changes can take hours to propagate.
- **Fragmented data**: Multiple feeds, no unified reasoning layer.

DisasterLens AI solves this by coupling **Pathway** for streaming ETL with a **dynamic RAG pipeline** (MiniLM embeddings + ChromaDB + Gemini 2.x Flash) and a **professional web dashboard** for emergency managers.

---

## 🚨 Problem Statement

**Hackathon Goal:** Build a RAG application on top of Pathway that connects to a **dynamic, continuously changing data source** and proves that answers update in real time without manual restarts or batch re-indexing.

**Our Use Case:** A climate & disaster intelligence assistant that:
- Ingests **live disaster alerts and news**.
- Maintains an **incrementally updated** semantic index.
- Answers questions like “What severe events are ongoing right now?” using the latest data.
- Visually shows **live map updates** and **risk scores** when new events are ingested.

### Judging Criteria Alignment (Short)

| Criterion                          | Weight | How We Address It                                                |
|------------------------------------|--------|------------------------------------------------------------------|
| Real-Time Capability & Dynamism    | 35%    | Streaming ingestion, incremental vector updates, live demo       |
| Technical Implementation & Elegance| 30%    | Modular, Pathway-centric design, logging, typed models           |
| Innovation & UX                    | 20%    | Risk scoring, interactive map, charts, live notifications        |
| Impact & Feasibility               | 15%    | Disaster-response use case, cloud-ready architecture            |

---

## ✨ Key Features

### Core MVP (Implemented)

#### 1. Real-Time Data Ingestion

- **GDACS Connector**
  - Streams alerts from the GDACS RSS feed (earthquakes, floods, cyclones, tsunamis, volcanoes).
  - Parses severity (Red/Orange/Green), location, magnitude, population impact.
  - Polling interval configurable (default ~120 seconds).

- **NewsAPI Connector**
  - Pulls breaking disaster-related news (earthquake, wildfire, flood, cyclone, etc.).
  - Enriches structured alerts with human-readable context.
  - Classifies disaster type and severity heuristically from article text.

#### 2. Pathway Streaming Pipeline

- Unifies GDACS + NewsAPI into a **single streaming table**.
- Performs:
  - Incremental event ingestion and deduplication.
  - Enrichment with standardized schema (type, severity, geo, description, sources).
  - **Risk scoring** combining severity, magnitude, disaster type multipliers, and population affected.
- Exposes a live “event stream” that is used to update the vector store without restarts.

#### 3. Dynamic RAG Pipeline

- **Embeddings**: `all-MiniLM-L6-v2` via sentence-transformers (fast, 384-dim).
- **Vector DB**: ChromaDB persistent collection (`disaster_events`) with cosine similarity.
- **RAG Flow**:
  - New/updated events are embedded and upserted into Chroma incrementally.
  - Queries embed the text and retrieve top‑k relevant events (with optional filters).
  - Retrieved contexts are injected into a custom, safety-focused prompt for Gemini.

#### 4. Gemini LLM Integration

- Model: **Gemini 2.x Flash** (configurable), tuned for:
  - Low temperature (0.2) for factual responses.
  - Clear citation and source referencing.
- RAG prompt includes:
  - System instructions for disaster domain.
  - Structured event snippets (type, severity, risk, time, source).
- Returns:
  - Natural language **answer**.
  - **Structured source list** with event IDs, locations, timestamps, URLs.
  - Short **risk-assessment summary** (Low/Moderate/High/Critical).

#### 5. FastAPI Backend & WebSocket

- REST endpoints:
  - `POST /api/query` – RAG Q&A.
  - `GET /api/events/latest` – latest events (with filters).
  - `GET /api/events/{event_id}` – details for a single event.
  - `GET /api/stats` – aggregated stats (per type, per severity, avg risk).
  - `GET /health` – health and uptime.
- WebSocket:
  - `GET /ws` – pushes `new_event` messages to the frontend when the pipeline ingests new data.
  - Used for **real-time notifications** and live dashboard updates.

#### 6. Professional Frontend (HTML/CSS/JS)

- **Query Panel**
  - Text box + quick query buttons (“Most severe”, “Earthquakes”, “Wildfires”, “High impact”).
  - Shows LLM answer, latency, timestamp.
  - Displays risk assessment banner and list of sources with severity chips and links.

- **Live Map**
  - Built with Leaflet.js.
  - Color-coded markers (Red / Orange / Green) by severity.
  - Popups show type, location, risk score, time.

- **Events List**
  - Card-based list of recent events.
  - Filters by disaster type and severity.
  - Risk score badges.

- **Statistics**
  - High-level KPIs (total events, avg risk, high-risk count, Red alerts).
  - Chart.js bar/doughnut charts (by type, by severity).

- **Real-Time UX**
  - WebSocket connection indicator (connected/disconnected).
  - Toast notifications when new events arrive.

#### 7. Advanced Feature: Risk Scoring with Explainability

We add a **domain-inspired risk score** per event:
```text
Risk ≈ base(severity) × type_multiplier × magnitude_factor × population_factor
Used to:

Rank events in answers.

Drive “High / Critical” risk labels.

Power stats (avg risk, high-risk count).

Display risk score on cards and map popups.

```

#### 🏗️ Architecture
***High-level layers:***

**1.Connectors**

GDACS RSS

NewsAPI JSON

Easily extendable to more sources (S3, DB CDC, social streams).

**2.Pathway Pipeline**

Ingests connector streams.

Cleans, normalizes, and enriches events.

Computes risk scores.

Publishes a unified streaming table of events.

**3.Vector & LLM Layer**

Embedding service (MiniLM).

ChromaDB persistent collection.

Gemini LLM wrapper for RAG answers and risk summaries.

**4.API & Realtime Layer**

FastAPI for REST.

WebSocket for live updates to the UI.

**5.Frontend**

SPA-like HTML/CSS/JS dashboard.

Map, charts, query panel, filters.

**🧰 Technology Stack**

    -Core Engine: Pathway (Python API, Rust engine)

    -ML / RAG: sentence-transformers, ChromaDB, Gemini 2.x Flash

    -Backend: FastAPI, Uvicorn

    -Frontend: HTML, CSS, vanilla JS, Leaflet, Chart.js

    -Utilities: Loguru for logging, Pydantic for models, dotenv/YAML for config

    -Containerization: Docker + docker-compose (optional)


**📦 Installation**
Prerequisites
Python 3.11+

pip

(Optional) Docker & docker-compose

API keys:

Gemini API key

NewsAPI key

**Steps**
git clone https://github.com/your-org/disasterlens-ai.git
cd disasterlens-ai

python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env to add GEMINI_API_KEY and NEWSAPI_KEY

mkdir -p data/live_events logs

python src/main.py

**Open: http://localhost:8080**

**For Docker:**
cp .env.example .env
# Edit .env

docker-compose up --build
# Then visit http://localhost:8080

---

**⚙️ Configuration**
.env (key variables):

GEMINI_API_KEY=your_gemini_key
NEWSAPI_KEY=your_newsapi_key

APP_HOST=0.0.0.0
APP_PORT=8080

CHROMA_PERSIST_DIRECTORY=./chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
GEMINI_MODEL=gemini-2.0-flash-exp

GDACS_RSS_URL=https://www.gdacs.org/xml/rss.xml
NEWSAPI_QUERY=disaster OR earthquake OR wildfire OR flood OR hurricane

**📁 Project Structure**

disasterlens-ai/
├── README.md
├── requirements.txt
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── config/
│   └── config.yaml
├── src/
│   ├── main.py                  # Orchestration: Pathway + API
│   ├── connectors/              # GDACS, NewsAPI, base connector
│   ├── pipeline/                # Pathway pipeline + risk scoring
│   ├── rag/                     # Embeddings, vector store, LLM
│   ├── api/                     # FastAPI + WebSocket handlers
│   └── utils/                   # Logger, Pydantic schemas
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── tests/
    └── test_connectors.py



#### 🔭 Future Enhancements
Short/medium-term roadmap:

More Data Sources

USGS earthquakes, NASA FIRMS wildfires, weather APIs, social feeds.

Richer Pathway Logic

Time-window aggregations, trend detection, compound event detection.

Better Risk Modeling

Integrate population density, infrastructure, vulnerability indices.

User & Org Features

Authentication, roles (public vs. responder vs. admin), org-based views.

Evaluation & MLOps

RAG evaluation (RAGAS), CI/CD, monitoring dashboards.




