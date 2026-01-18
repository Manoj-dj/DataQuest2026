"""
FastAPI REST API server for DisasterLens AI.
Provides endpoints for querying disasters, retrieving events, and system health.
Integrates Pathway pipeline with vector store and LLM for real-time RAG.
"""

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
import time
import os
from typing import Optional, Dict, List
import threading

from src.rag.vector_store import DisasterVectorStore
from src.rag.llm_interface import OpenAILLM
from src.utils.logger import app_logger
from src.utils.schemas import QueryRequest, QueryResponse, EventListResponse, HealthResponse

class DisasterLensAPI:
    def __init__(self, vector_store: DisasterVectorStore, llm: OpenAILLM):
        self.app = FastAPI(
            title="DisasterLens AI",
            description="Real-Time Climate Emergency Intelligence System",
            version="1.0.0"
        )
        
        self.vector_store = vector_store
        self.llm = llm
        self.logger = app_logger
        self.start_time = time.time()
        
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """
        Configure CORS and other middleware.
        """
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """
        Define API endpoints.
        """
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Serve frontend HTML."""
            html_path = "frontend/index.html"
            if os.path.exists(html_path):
                with open(html_path, 'r') as f:
                    return f.read()
            return "<h1>DisasterLens AI</h1><p>Frontend not found. API is running at /docs</p>"
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """System health and status check."""
            try:
                uptime = time.time() - self.start_time
                active_events = self.vector_store.count()
                
                return HealthResponse(
                    status="healthy",
                    version="1.0.0",
                    uptime_seconds=uptime,
                    active_events=active_events,
                    last_update=datetime.now()
                )
            except Exception as e:
                self.logger.log_error("health_check", e)
                raise HTTPException(status_code=500, detail="Health check failed")
        
        @self.app.post("/api/query", response_model=QueryResponse)
        async def query_disasters(request: QueryRequest):
            """
            Main RAG query endpoint - answer questions about disasters.
            """
            try:
                start_time = time.time()
                
                filters = None
                if request.filters:
                    filters = request.filters
                
                retrieved_contexts = self.vector_store.search(
                    query=request.query,
                    top_k=request.top_k,
                    filters=filters
                )
                
                if not retrieved_contexts:
                    return QueryResponse(
                        query=request.query,
                        answer="I couldn't find any relevant disaster events matching your query. The database may not have recent events, or try rephrasing your question.",
                        sources=[],
                        risk_assessment=None,
                        timestamp=datetime.now(),
                        latency_ms=0
                    )
                
                llm_response = self.llm.generate_rag_response(
                    query=request.query,
                    retrieved_contexts=retrieved_contexts,
                    include_risk_assessment=True
                )
                
                total_latency = (time.time() - start_time) * 1000
                
                return QueryResponse(
                    query=request.query,
                    answer=llm_response['answer'],
                    sources=llm_response['sources'],
                    risk_assessment=llm_response.get('risk_assessment'),
                    timestamp=datetime.now(),
                    latency_ms=total_latency
                )
            
            except Exception as e:
                self.logger.log_error("query_disasters", e)
                raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")
        
        @self.app.get("/api/events/latest")
        async def get_latest_events(
            limit: int = Query(default=20, ge=1, le=100),
            disaster_type: Optional[str] = None
        ):
            """
            Retrieve latest disaster events from vector store.
            """
            try:
                all_events = self.vector_store.get_all_events(limit=limit)
                
                if disaster_type:
                    all_events = [
                        e for e in all_events 
                        if e.get('metadata', {}).get('disaster_type') == disaster_type
                    ]
                
                formatted_events = []
                for event in all_events:
                    metadata = event.get('metadata', {})
                    formatted_events.append({
                        'event_id': event.get('id'),
                        'disaster_type': metadata.get('disaster_type'),
                        'severity': metadata.get('severity'),
                        'location': metadata.get('location'),
                        'risk_score': metadata.get('risk_score'),
                        'event_time': metadata.get('event_time'),
                        'source': metadata.get('source'),
                        'url': metadata.get('url', '')
                    })
                
                return {
                    'events': formatted_events,
                    'count': len(formatted_events),
                    'timestamp': datetime.now().isoformat()
                }
            
            except Exception as e:
                self.logger.log_error("get_latest_events", e)
                raise HTTPException(status_code=500, detail="Failed to retrieve events")
        
        @self.app.get("/api/events/{event_id}")
        async def get_event_details(event_id: str):
            """
            Get detailed information about specific event.
            """
            try:
                event = self.vector_store.get_event_by_id(event_id)
                
                if not event:
                    raise HTTPException(status_code=404, detail="Event not found")
                
                return {
                    'event_id': event.get('id'),
                    'text': event.get('text'),
                    'metadata': event.get('metadata'),
                    'timestamp': datetime.now().isoformat()
                }
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.log_error("get_event_details", e)
                raise HTTPException(status_code=500, detail="Failed to retrieve event")
        
        @self.app.get("/api/stats")
        async def get_statistics():
            """
            Get aggregated statistics about disasters.
            """
            try:
                all_events = self.vector_store.get_all_events(limit=1000)
                
                stats = {
                    'total_events': len(all_events),
                    'by_type': {},
                    'by_severity': {},
                    'avg_risk_score': 0,
                    'high_risk_count': 0
                }
                
                risk_scores = []
                
                for event in all_events:
                    metadata = event.get('metadata', {})
                    
                    d_type = metadata.get('disaster_type', 'unknown')
                    stats['by_type'][d_type] = stats['by_type'].get(d_type, 0) + 1
                    
                    severity = metadata.get('severity', 'Unknown')
                    stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
                    
                    risk_score = metadata.get('risk_score')
                    if risk_score:
                        try:
                            risk_val = float(risk_score)
                            risk_scores.append(risk_val)
                            if risk_val >= 7.0:
                                stats['high_risk_count'] += 1
                        except:
                            pass
                
                if risk_scores:
                    stats['avg_risk_score'] = round(sum(risk_scores) / len(risk_scores), 2)
                
                return stats
            
            except Exception as e:
                self.logger.log_error("get_statistics", e)
                raise HTTPException(status_code=500, detail="Failed to compute statistics")

def create_app(vector_store: DisasterVectorStore, llm: OpenAILLM) -> FastAPI:
    """
    Factory function to create FastAPI application.
    """
    api = DisasterLensAPI(vector_store, llm)
    return api.app
