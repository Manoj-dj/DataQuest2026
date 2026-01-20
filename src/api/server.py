"""
FastAPI REST API server for DisasterLens AI.
Provides endpoints for querying disasters, retrieving events, and system health.
Integrates Pathway pipeline with vector store and LLM for real-time RAG.
"""

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
import time
import os
from typing import Optional, Dict, List
import threading
import asyncio
import json

from src.rag.vector_store import DisasterVectorStore
from src.rag.llm_interface import OpenAILLM
from src.utils.logger import app_logger
from src.utils.schemas import (
    QueryRequest, QueryResponse, EventListResponse, HealthResponse,
    ExplainableAlert, AlertListResponse, AlertSignal,
    SimulationRequest, SimulationResponse,
    AlertSettings, AlertSettingsResponse,
    ImpactUpdateRequest, SeverityLevel, AlertChannel
)

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
        self.prediction_connections: List[WebSocket] = []
        
        # Alert storage (in-memory for now, can be persisted later)
        self.alerts: Dict[str, ExplainableAlert] = {}
        self.alert_settings: Dict[str, AlertSettings] = {
            "citizen": AlertSettings(
                role="citizen",
                min_severity=SeverityLevel.RED,
                channels=[AlertChannel.WEBSOCKET],
                show_predictions=True,
                show_confirmed_only=False
            ),
            "responder": AlertSettings(
                role="responder",
                min_severity=SeverityLevel.ORANGE,
                channels=[AlertChannel.WEBSOCKET],
                show_predictions=True,
                show_confirmed_only=False
            ),
            "admin": AlertSettings(
                role="admin",
                min_severity=SeverityLevel.GREEN,
                channels=[AlertChannel.WEBSOCKET],
                show_predictions=True,
                show_confirmed_only=False
            )
        }
        
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
                        latency_ms=0,
                        key_events=[],
                        risk_assessment_items=[],
                        recommendations=[],
                        actionable_insight="The system has indexed events but couldn't find matches for your specific query. Try broader terms like 'recent earthquakes' or 'active wildfires'."
                    )
                
                llm_response = self.llm.generate_rag_response(
                    query=request.query,
                    retrieved_contexts=retrieved_contexts,
                    include_risk_assessment=True
                )
                
                total_latency = (time.time() - start_time) * 1000
                
                return QueryResponse(
                    query=request.query,
                    answer=llm_response.get('answer', ''),
                    sources=llm_response['sources'],
                    risk_assessment=llm_response.get('risk_assessment'),
                    timestamp=datetime.now(),
                    latency_ms=total_latency,
                    key_events=llm_response.get('key_events', []),
                    risk_assessment_items=llm_response.get('risk_assessment_items', []),
                    recommendations=llm_response.get('recommendations', []),
                    actionable_insight=llm_response.get('actionable_insight')
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
        
        @self.app.get("/api/predictions")
        async def get_disaster_predictions():
            """
            Get real-time disaster predictions and alerts.
            Uses Pathway pattern detection + RAG historical analysis.
            """
            try:
                # Get recent events from last 24 hours
                hours = 24
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                # Get all events from vector store
                all_events = self.vector_store.get_all_events()
                
                # Filter recent events
                recent_events = []
                for event in all_events:
                    try:
                        event_time_str = event.get('metadata', {}).get('event_time', '')
                        if event_time_str:
                            event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00'))
                            if event_time >= cutoff_time:
                                recent_events.append(event)
                    except:
                        # Include event if time parsing fails
                        recent_events.append(event)
                
                predictions = []
                
                for event in recent_events[:10]:  # Limit to 10 events for performance
                    try:
                        metadata = event.get('metadata', {})
                        
                        # Find similar historical events using RAG
                        query_text = f"{metadata.get('disaster_type', '')} {metadata.get('location_name') or metadata.get('location', '')}"
                        similar_events = self.vector_store.search(
                            query_text=query_text,
                            top_k=5
                        )
                        
                        # Generate prediction using RAG
                        prediction_text = self.llm.predict_disaster_impact(
                            current_event=event,
                            similar_events=similar_events
                        )
                        
                        # Calculate confidence based on similar events
                        confidence = 'HIGH' if len(similar_events) >= 3 else 'MEDIUM' if len(similar_events) >= 1 else 'LOW'
                        
                        risk_score = float(metadata.get('risk_score', 0))
                        
                        # Create explainable alert
                        signals = [
                            {
                                'name': 'GDACS Score',
                                'weight': 0.4,
                                'value': risk_score,
                                'description': f'GDACS risk score: {risk_score}/10'
                            },
                            {
                                'name': 'Historical Pattern Match',
                                'weight': 0.3,
                                'value': len(similar_events),
                                'description': f'Found {len(similar_events)} similar historical events'
                            },
                            {
                                'name': 'News Sentiment',
                                'weight': 0.2,
                                'value': 1.0 if metadata.get('severity') == 'Red' else 0.5,
                                'description': 'News coverage indicates high severity'
                            },
                            {
                                'name': 'Population Density',
                                'weight': 0.1,
                                'value': metadata.get('population_affected', 0) / 100000.0 if metadata.get('population_affected') else 0.0,
                                'description': f"Affected population: {metadata.get('population_affected', 0)}"
                            }
                        ]
                        
                        summary = f"A {metadata.get('disaster_type', 'disaster')} has been detected at {metadata.get('location_name') or metadata.get('location', 'Unknown')}. "
                        summary += f"Risk score: {risk_score}/10. "
                        summary += f"Based on {len(similar_events)} similar historical events, this situation requires monitoring."
                        
                        explainable_alert = self._create_explainable_alert(
                            event=event,
                            signals=signals,
                            risk_score=risk_score,
                            summary=summary
                        )
                        
                        predictions.append({
                            'event_id': event.get('id', 'unknown'),
                            'event_title': f"{metadata.get('disaster_type', 'Disaster')} - {metadata.get('location_name') or metadata.get('location', 'Unknown')}",
                            'prediction': prediction_text,
                            'confidence': confidence,
                            'severity': metadata.get('severity', 'Unknown'),
                            'risk_score': risk_score,
                            'timestamp': datetime.now().isoformat(),
                            'alert_id': explainable_alert.alert_id
                        })
                    except Exception as e:
                        self.logger.log_error("get_disaster_predictions", e)
                        continue
                
                return {
                    'predictions': predictions,
                    'total': len(predictions),
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.log_error("get_disaster_predictions", e)
                return {'predictions': [], 'total': 0, 'error': str(e)}
        
        @self.app.websocket("/ws/predictions")
        async def prediction_websocket(websocket: WebSocket):
            """WebSocket endpoint for live prediction alerts."""
            await websocket.accept()
            self.prediction_connections.append(websocket)
            self.logger.logger.info(f"Prediction WebSocket connected. Total connections: {len(self.prediction_connections)}")
            
            try:
                # Send initial connection confirmation
                await websocket.send_json({
                    "type": "connected",
                    "message": "Prediction WebSocket connected",
                    "timestamp": datetime.now().isoformat()
                })
                
                while True:
                    # Keep connection alive - wait for messages or timeout
                    try:
                        # Use receive with timeout to keep connection alive
                        data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                        # Echo back or handle client messages if needed
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        })
                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        await websocket.send_json({
                            "type": "ping",
                            "timestamp": datetime.now().isoformat()
                        })
            except WebSocketDisconnect:
                if websocket in self.prediction_connections:
                    self.prediction_connections.remove(websocket)
                self.logger.logger.info(f"Prediction WebSocket disconnected. Remaining connections: {len(self.prediction_connections)}")
            except Exception as e:
                self.logger.log_error("prediction_websocket", e)
                if websocket in self.prediction_connections:
                    self.prediction_connections.remove(websocket)
        
        # Explainable Alerts Endpoints
        @self.app.get("/api/alerts/recent", response_model=AlertListResponse)
        async def get_recent_alerts(limit: int = Query(default=20, ge=1, le=100)):
            """Get recent explainable alerts with signals and risk scores."""
            try:
                # Get alerts sorted by timestamp (most recent first)
                sorted_alerts = sorted(
                    self.alerts.values(),
                    key=lambda a: a.timestamp,
                    reverse=True
                )[:limit]
                
                return AlertListResponse(
                    alerts=sorted_alerts,
                    count=len(sorted_alerts),
                    timestamp=datetime.now()
                )
            except Exception as e:
                self.logger.log_error("get_recent_alerts", e)
                return AlertListResponse(alerts=[], count=0, timestamp=datetime.now())
        
        @self.app.post("/api/alerts/{alert_id}/impact")
        async def update_alert_impact(alert_id: str, impact: ImpactUpdateRequest):
            """Update post-event impact data for an alert."""
            try:
                if alert_id not in self.alerts:
                    raise HTTPException(status_code=404, detail="Alert not found")
                
                alert = self.alerts[alert_id]
                
                # Update impact fields
                if impact.actual_impact is not None:
                    alert.actual_impact = impact.actual_impact
                if impact.actual_people_affected is not None:
                    alert.actual_people_affected = impact.actual_people_affected
                if impact.was_false_alarm is not None:
                    alert.was_false_alarm = impact.was_false_alarm
                
                # Calculate prediction error
                if alert.actual_people_affected is not None and alert.risk_score is not None:
                    # Map risk_score (0-10) to severity bucket
                    predicted_severity_bucket = 0
                    if alert.risk_score >= 7.5:
                        predicted_severity_bucket = 3  # High
                    elif alert.risk_score >= 5.0:
                        predicted_severity_bucket = 2  # Medium
                    else:
                        predicted_severity_bucket = 1  # Low
                    
                    # Map actual_people_affected to severity bucket
                    actual_severity_bucket = 0
                    if alert.actual_people_affected >= 100000:
                        actual_severity_bucket = 3
                    elif alert.actual_people_affected >= 10000:
                        actual_severity_bucket = 2
                    else:
                        actual_severity_bucket = 1
                    
                    alert.prediction_error = abs(predicted_severity_bucket - actual_severity_bucket)
                
                self.alerts[alert_id] = alert
                
                return {"success": True, "alert_id": alert_id, "timestamp": datetime.now().isoformat()}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.log_error("update_alert_impact", e)
                raise HTTPException(status_code=500, detail="Failed to update alert impact")
        
        # Scenario Simulator Endpoint
        @self.app.post("/api/simulate", response_model=SimulationResponse)
        async def simulate_scenario(request: SimulationRequest):
            """Simulate a disaster scenario and predict impact using RAG."""
            try:
                # Create a mock event from the simulation request
                mock_event = {
                    'id': f"sim_{int(time.time())}",
                    'metadata': {
                        'disaster_type': request.hazard_type,
                        'location_name': request.location,
                        'latitude': request.latitude,
                        'longitude': request.longitude,
                        'magnitude': request.magnitude,
                        'population_affected': int(request.population_density * 1000),  # Rough estimate
                        'severity': 'Unknown',
                        'risk_score': 0.0
                    },
                    'text': f"Simulated {request.hazard_type} at {request.location}"
                }
                
                # Find similar historical events
                query_text = f"{request.hazard_type} {request.location}"
                similar_events = self.vector_store.search(
                    query_text=query_text,
                    top_k=5
                )
                
                # Generate prediction using RAG
                prediction_json = self.llm.predict_disaster_impact(
                    current_event=mock_event,
                    similar_events=similar_events
                )
                
                # Parse prediction JSON
                try:
                    prediction_data = json.loads(prediction_json)
                    predicted_impacts = prediction_data.get('recommended_actions', [])
                    if not predicted_impacts:
                        predicted_impacts = prediction_data.get('secondary_risks', [])
                    
                    explanation = prediction_data.get('expected_impact_scale', '') + ' ' + prediction_data.get('timeline', '')
                    explanation = explanation.strip()
                except:
                    predicted_impacts = ["Unable to generate detailed predictions"]
                    explanation = "Historical data analysis completed but detailed prediction unavailable."
                
                # Calculate risk score based on magnitude, population density, infrastructure
                base_risk = 5.0
                if request.magnitude:
                    base_risk += min(request.magnitude / 2.0, 3.0)
                if request.population_density > 1000:
                    base_risk += 1.5
                elif request.population_density > 100:
                    base_risk += 0.5
                base_risk -= (10.0 - request.infrastructure_score) * 0.2
                predicted_risk_score = max(0.0, min(10.0, base_risk))
                
                return SimulationResponse(
                    predicted_risk_score=predicted_risk_score,
                    predicted_impacts=predicted_impacts if isinstance(predicted_impacts, list) else [str(predicted_impacts)],
                    explanation=explanation,
                    timestamp=datetime.now()
                )
            except Exception as e:
                self.logger.log_error("simulate_scenario", e)
                raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")
        
        # Alert Settings Endpoints
        @self.app.get("/api/alert-settings/{role}", response_model=AlertSettingsResponse)
        async def get_alert_settings(role: str):
            """Get alert settings for a specific role."""
            try:
                if role not in self.alert_settings:
                    raise HTTPException(status_code=404, detail=f"Role '{role}' not found. Available: citizen, responder, admin")
                
                return AlertSettingsResponse(
                    settings=self.alert_settings[role],
                    timestamp=datetime.now()
                )
            except HTTPException:
                raise
            except Exception as e:
                self.logger.log_error("get_alert_settings", e)
                raise HTTPException(status_code=500, detail="Failed to retrieve alert settings")
        
        @self.app.put("/api/alert-settings/{role}", response_model=AlertSettingsResponse)
        async def update_alert_settings(role: str, settings: AlertSettings):
            """Update alert settings for a specific role."""
            try:
                if role not in self.alert_settings:
                    raise HTTPException(status_code=404, detail=f"Role '{role}' not found")
                
                # Ensure role matches
                settings.role = role
                self.alert_settings[role] = settings
                
                return AlertSettingsResponse(
                    settings=settings,
                    timestamp=datetime.now()
                )
            except HTTPException:
                raise
            except Exception as e:
                self.logger.log_error("update_alert_settings", e)
                raise HTTPException(status_code=500, detail="Failed to update alert settings")
        
    def _create_explainable_alert(
        self,
        event: Dict,
        signals: List[Dict],
        risk_score: float,
        summary: str
    ) -> ExplainableAlert:
        """Create an explainable alert from an event."""
        metadata = event.get('metadata', {})
        alert_id = f"alert_{event.get('id', 'unknown')}_{int(time.time())}"
        
        alert_signals = [
            AlertSignal(
                signal_name=s.get('name', 'Unknown'),
                weight=s.get('weight', 0.0),
                value=s.get('value'),
                description=s.get('description', '')
            )
            for s in signals
        ]
        
        alert = ExplainableAlert(
            alert_id=alert_id,
            title=f"{metadata.get('disaster_type', 'Disaster')} - {metadata.get('location_name') or metadata.get('location', 'Unknown')}",
            location=metadata.get('location_name') or metadata.get('location', 'Unknown'),
            severity=SeverityLevel(metadata.get('severity', 'Unknown')),
            risk_score=risk_score,
            signals=alert_signals,
            summary=summary,
            event_id=event.get('id'),
            timestamp=datetime.now()
        )
        
        self.alerts[alert_id] = alert
        return alert
    
    async def broadcast_prediction_alert(self, alert: Dict):
        """Broadcast prediction alert to all connected WebSocket clients."""
        if not self.prediction_connections:
            return
        
        disconnected = []
        for connection in self.prediction_connections:
            try:
                await connection.send_json(alert)
            except Exception as e:
                self.logger.logger.warning(f"Failed to send alert to WebSocket client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.prediction_connections:
                self.prediction_connections.remove(conn)

def create_app(vector_store: DisasterVectorStore, llm: OpenAILLM) -> FastAPI:
    """
    Factory function to create FastAPI application.
    """
    api = DisasterLensAPI(vector_store, llm)
    return api.app
