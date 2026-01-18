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
            allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],
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
        
        @self.app.get("/api/health")
        async def api_health_check():
            """API health check endpoint (alternative path)."""
            try:
                uptime = time.time() - self.start_time
                uptime_str = f"{int(uptime)}s"
                if uptime > 60:
                    uptime_str = f"{int(uptime) // 60}m {int(uptime) % 60}s"
                
                # Get event count
                all_events = self.vector_store.get_all_events(limit=10)
                event_count = len(all_events)
                
                return {
                    "status": "healthy",
                    "events_count": event_count,
                    "uptime": uptime_str,
                    "timestamp": datetime.now().isoformat(),
                    "components": {
                        "pathway": "running",
                        "vector_store": "connected",
                        "llm": "ready",
                        "api": "operational"
                    }
                }
            except Exception as e:
                self.logger.log_error("api_health_check", e)
                return {
                    "status": "degraded",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.get("/api/debug/events")
        async def debug_events():
            """Debug endpoint to see what's in the vector store."""
            try:
                # Get all events (no search, just list)
                all_events = self.vector_store.get_all_events(limit=20)
                
                # Try a simple search
                search_results = self.vector_store.search(
                    query="wildfire earthquake disaster",
                    top_k=10,
                    filters=None
                )
                
                return {
                    "total_events_count": len(all_events),
                    "sample_event_ids": [e.get('id', 'unknown') for e in all_events[:5]],
                    "sample_event_metadata": [e.get('metadata', {}) for e in all_events[:3]],
                    "search_results_count": len(search_results) if search_results else 0,
                    "search_sample": search_results[:3] if search_results else []
                }
            except Exception as e:
                self.logger.log_error("debug_events", e)
                return {"error": str(e)}
        
        @self.app.post("/api/query", response_model=QueryResponse)
        async def query_disasters(request: QueryRequest):
            """
            Main RAG query endpoint - answer questions about disasters.
            """
            try:
                self.logger.logger.info(f"RAG query received: {request.query}")
                start_time = time.time()
                
                filters = None
                if request.filters:
                    filters = request.filters
                
                # Search vector store
                retrieved_contexts = self.vector_store.search(
                    query=request.query,
                    top_k=request.top_k,
                    filters=filters
                )
                
                self.logger.logger.info(f"Vector search returned {len(retrieved_contexts) if retrieved_contexts else 0} results")
                
                # If no results, try a broader search without filters
                if not retrieved_contexts or len(retrieved_contexts) == 0:
                    self.logger.logger.warning("No results from vector search, trying broader search...")
                    retrieved_contexts = self.vector_store.search(
                        query="disaster earthquake wildfire flood hurricane",
                        top_k=10,
                        filters=None  # Remove all filters
                    )
                    self.logger.logger.info(f"Broader search returned {len(retrieved_contexts) if retrieved_contexts else 0} results")
                
                # If still no results, return helpful message
                if not retrieved_contexts or len(retrieved_contexts) == 0:
                    self.logger.logger.warning("Still no results after broader search")
                    return QueryResponse(
                        query=request.query,
                        answer="The system has indexed events but couldn't find matches for your specific query. Try broader terms like 'recent earthquakes' or 'active wildfires'.",
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
                import json
                events_with_coords = 0
                events_without_coords = 0
                
                for event in all_events:
                    metadata = event.get('metadata', {})
                    
                    # Extract coordinates - try multiple field names
                    lat = metadata.get('latitude') or metadata.get('lat')
                    lon = metadata.get('longitude') or metadata.get('lon') or metadata.get('lng')
                    
                    # For map display, we need coordinates - skip if missing
                    # But log to see how many have coordinates
                    if lat is None or lon is None:
                        events_without_coords += 1
                        continue
                    
                    try:
                        lat = float(lat)
                        lon = float(lon)
                    except (ValueError, TypeError):
                        events_without_coords += 1
                        continue
                    
                    # Skip (0,0) coordinates which are likely invalid
                    if lat == 0.0 and lon == 0.0:
                        events_without_coords += 1
                        continue
                    
                    events_with_coords += 1
                    
                    # Extract imagery URLs
                    imagery_urls = metadata.get('imagery_urls', [])
                    if isinstance(imagery_urls, str):
                        try:
                            imagery_urls = json.loads(imagery_urls)
                        except:
                            imagery_urls = []
                    
                    formatted_events.append({
                        'event_id': event.get('id'),
                        'disaster_type': metadata.get('disaster_type', 'Unknown'),
                        'severity': metadata.get('severity', 'Unknown'),
                        'location': metadata.get('location_name') or metadata.get('location', 'Unknown Location'),
                        'latitude': lat,
                        'longitude': lon,
                        'risk_score': metadata.get('risk_score'),
                        'event_time': metadata.get('event_time', ''),
                        'source': metadata.get('source', 'Unknown'),
                        'url': metadata.get('url', ''),
                        'description': metadata.get('description', ''),
                        'population_affected': metadata.get('population_affected', 0),
                        'magnitude': metadata.get('magnitude'),
                        'imagery_urls': imagery_urls if isinstance(imagery_urls, list) else [],
                        'has_imagery': metadata.get('has_imagery', False) or len(imagery_urls) > 0
                    })
                
                self.logger.logger.info(f"Returning {len(formatted_events)} events with coordinates (from {len(all_events)} total: {events_with_coords} with coords, {events_without_coords} without)")
                
                return {
                    'events': formatted_events,
                    'count': len(formatted_events),
                    'timestamp': datetime.now().isoformat()
                }
            
            except Exception as e:
                self.logger.log_error("get_latest_events", e)
                # Return empty events array instead of error to prevent frontend crashes
                import traceback
                self.logger.logger.error(f"Full traceback: {traceback.format_exc()}")
                return {
                    'events': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)[:200]  # Include error for debugging
                }
        
        @self.app.get("/api/events/{event_id}")
        async def get_event_details(event_id: str):
            """
            Get detailed information about specific event.
            """
            try:
                event = self.vector_store.get_event_by_id(event_id)
                
                if not event:
                    raise HTTPException(status_code=404, detail="Event not found")
                
                import json
                metadata = event.get('metadata', {})
                
                # Extract imagery URLs from metadata
                imagery_urls = metadata.get('imagery_urls', [])
                if isinstance(imagery_urls, str):
                    try:
                        imagery_urls = json.loads(imagery_urls)
                    except:
                        imagery_urls = []
                
                return {
                    'event_id': event.get('id'),
                    'text': event.get('text'),
                    'metadata': metadata,
                    'imagery_urls': imagery_urls if isinstance(imagery_urls, list) else [],
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
        
        @self.app.get("/api/events/{event_id}/imagery")
        async def get_event_imagery(event_id: str):
            """
            Get imagery URLs for a specific event.
            """
            try:
                import json
                event = self.vector_store.get_event_by_id(event_id)
                
                if not event:
                    raise HTTPException(status_code=404, detail="Event not found")
                
                metadata = event.get('metadata', {})
                imagery_urls = metadata.get('imagery_urls', [])
                
                # Handle both list and JSON string formats
                if isinstance(imagery_urls, str):
                    try:
                        imagery_urls = json.loads(imagery_urls)
                    except:
                        imagery_urls = []
                
                return {
                    'event_id': event_id,
                    'imagery_urls': imagery_urls if isinstance(imagery_urls, list) else [],
                    'count': len(imagery_urls) if isinstance(imagery_urls, list) else 0,
                    'timestamp': datetime.now().isoformat()
                }
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.log_error("get_event_imagery", e)
                raise HTTPException(status_code=500, detail="Failed to retrieve imagery")
        
        @self.app.post("/api/imagery/analyze")
        async def analyze_imagery(request: Dict):
            """
            Analyze disaster imagery using GPT-4 Vision.
            """
            try:
                image_url = request.get('image_url')
                event_context = request.get('context') or request.get('event_context')
                
                if not image_url:
                    raise HTTPException(status_code=400, detail="image_url is required")
                
                analysis = self.llm.analyze_disaster_image(
                    image_url=image_url,
                    event_context=event_context
                )
                
                return {
                    'analysis': analysis,
                    'timestamp': datetime.now().isoformat()
                }
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.log_error("analyze_imagery", e)
                raise HTTPException(status_code=500, detail="Failed to analyze imagery")

def create_app(vector_store: DisasterVectorStore, llm: OpenAILLM) -> FastAPI:
    """
    Factory function to create FastAPI application.
    """
    api = DisasterLensAPI(vector_store, llm)
    return api.app
