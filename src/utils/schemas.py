"""
Data schemas and models for DisasterLens AI.
Defines structure for disaster events, API requests/responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class SeverityLevel(str, Enum):
    RED = "Red"
    ORANGE = "Orange"
    GREEN = "Green"
    UNKNOWN = "Unknown"

class DisasterType(str, Enum):
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    WILDFIRE = "wildfire"
    CYCLONE = "cyclone"
    TSUNAMI = "tsunami"
    VOLCANO = "volcano"
    DROUGHT = "drought"
    UNKNOWN = "unknown"

class DisasterEvent(BaseModel):
    event_id: str
    disaster_type: DisasterType
    severity: SeverityLevel
    latitude: float
    longitude: float
    location_name: str
    population_affected: int = 0
    description: str
    magnitude: Optional[float] = None
    event_time: datetime
    source: str
    url: Optional[str] = None
    risk_score: float = 0.0
    ingested_at: Optional[datetime] = None

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    filters: Optional[Dict[str, str]] = None
    top_k: int = Field(default=5, ge=1, le=20)

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, str]]
    risk_assessment: Optional[str] = None
    timestamp: datetime
    latency_ms: float

class EventListResponse(BaseModel):
    events: List[DisasterEvent]
    count: int
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    active_events: int
    last_update: Optional[datetime]
