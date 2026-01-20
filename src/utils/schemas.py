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
    answer: str  # Keep for backward compatibility, but will be deprecated
    sources: List[Dict[str, str]]
    risk_assessment: Optional[str] = None  # Keep for backward compatibility
    timestamp: datetime
    latency_ms: float
    # New structured fields
    key_events: List[str] = []
    risk_assessment_items: List[str] = []
    recommendations: List[str] = []
    actionable_insight: Optional[str] = None

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

# Explainable Alert Schemas
class AlertSignal(BaseModel):
    signal_name: str
    weight: float = Field(ge=0.0, le=1.0)
    value: Optional[float] = None
    description: str

class ExplainableAlert(BaseModel):
    alert_id: str
    title: str
    location: str
    severity: SeverityLevel
    risk_score: float = Field(ge=0.0, le=10.0)
    signals: List[AlertSignal]
    summary: str  # Plain text, no markdown
    event_id: Optional[str] = None
    timestamp: datetime
    # Post-event impact fields
    actual_impact: Optional[str] = None
    actual_people_affected: Optional[int] = None
    was_false_alarm: Optional[bool] = None
    prediction_error: Optional[float] = None  # Difference between predicted and actual

class AlertListResponse(BaseModel):
    alerts: List[ExplainableAlert]
    count: int
    timestamp: datetime

# Scenario Simulator Schemas
class SimulationRequest(BaseModel):
    hazard_type: str
    magnitude: Optional[float] = None
    location: str
    latitude: float
    longitude: float
    population_density: float = Field(ge=0.0)
    infrastructure_score: float = Field(ge=0.0, le=10.0)

class SimulationResponse(BaseModel):
    predicted_risk_score: float = Field(ge=0.0, le=10.0)
    predicted_impacts: List[str]
    explanation: str  # Plain text, no markdown
    timestamp: datetime

# Alert Settings Schemas
class AlertChannel(str, Enum):
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SMS = "sms"

class AlertSettings(BaseModel):
    role: str  # citizen, responder, admin
    min_severity: SeverityLevel
    channels: List[AlertChannel]
    show_predictions: bool = True
    show_confirmed_only: bool = False

class AlertSettingsResponse(BaseModel):
    settings: AlertSettings
    timestamp: datetime

# Post-Event Impact Schema
class ImpactUpdateRequest(BaseModel):
    actual_impact: Optional[str] = None
    actual_people_affected: Optional[int] = None
    was_false_alarm: Optional[bool] = None
