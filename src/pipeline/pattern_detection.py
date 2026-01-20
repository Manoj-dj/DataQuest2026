"""
Pathway-based pattern detection for predictive disaster intelligence.
Detects cascading disasters, spatial clusters, and severity escalation patterns.
"""

import pathway as pw
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math
from src.utils.logger import app_logger


class DisasterPatternDetector:
    """Detect patterns in disaster events using Pathway transformations."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = app_logger
        self.cluster_radius_km = config.get('pattern_detection', {}).get('cluster_radius_km', 500)
        self.time_window_hours = config.get('pattern_detection', {}).get('time_window_hours', 24)
        self.min_cluster_size = config.get('pattern_detection', {}).get('min_cluster_size', 3)
    
    def build_prediction_pipeline(self, event_stream: pw.Table) -> pw.Table:
        """
        Build Pathway pipeline with pattern detection and predictions.
        """
        self.logger.logger.info("Building prediction pipeline with pattern detection...")
        
        # Add timestamp column for temporal analysis
        @pw.udf
        def parse_timestamp(event_time: str) -> float:
            """Parse event time to timestamp for temporal operations."""
            try:
                if event_time:
                    dt = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                    return dt.timestamp()
            except:
                pass
            return datetime.now().timestamp()
        
        events_with_timestamp = event_stream.select(
            *[pw.this[col] for col in event_stream.column_names()],
            timestamp_float=parse_timestamp(pw.this.event_time)
        )
        
        # Detect patterns using Pathway transformations
        patterns = self._detect_patterns(events_with_timestamp)
        
        # Generate predictions
        predictions = patterns.select(
            prediction_type=pw.this.pattern_type,
            prediction_severity=pw.this.pattern_severity,
            prediction_message=pw.this.pattern_message,
            prediction_recommendation=pw.this.pattern_recommendation,
            event_ids=pw.this.event_ids,
            event_data=pw.this.event_data
        )
        
        return predictions
    
    def _detect_patterns(self, events: pw.Table) -> pw.Table:
        """Detect various disaster patterns."""
        
        # Pattern 1: Spatial clustering
        clusters = self._detect_spatial_clusters(events)
        
        # Pattern 2: Cascading disaster risk
        cascading = self._detect_cascading_risks(events)
        
        # Pattern 3: Severity escalation
        escalation = self._detect_severity_escalation(events)
        
        # Combine all patterns
        all_patterns = pw.Table.concat(clusters, cascading, escalation)
        
        return all_patterns
    
    def _detect_spatial_clusters(self, events: pw.Table) -> pw.Table:
        """Detect spatial clusters of events (multiple disasters in same region)."""
        
        @pw.udf
        def check_cluster(
            lat: float, lon: float, event_type: str, 
            severity: str, event_id: str, timestamp: float
        ) -> Optional[Dict]:
            """Check if event is part of a spatial cluster."""
            # This is a simplified check - in production, use proper spatial indexing
            # For now, we'll use Pathway's windowing capabilities
            
            # Return cluster indicator
            if lat != 0.0 and lon != 0.0:
                return {
                    'type': 'SPATIAL_CLUSTER',
                    'lat': lat,
                    'lon': lon,
                    'event_type': event_type,
                    'severity': severity,
                    'event_id': event_id
                }
            return None
        
        # Add cluster check
        with_cluster = events.select(
            *[pw.this[col] for col in events.column_names()],
            cluster_data=check_cluster(
                pw.this.latitude,
                pw.this.longitude,
                pw.this.disaster_type,
                pw.this.severity,
                pw.this.event_id,
                pw.this.timestamp_float
            )
        )
        
        # Filter for events with cluster data
        cluster_events = with_cluster.filter(pw.this.cluster_data.is_not_none())
        
        # Group by region (simplified - using rounded coordinates)
        @pw.udf
        def get_region_key(lat: float, lon: float) -> str:
            """Create region key from coordinates."""
            # Round to ~100km grid
            lat_rounded = round(lat, 1)
            lon_rounded = round(lon, 1)
            return f"{lat_rounded:.1f},{lon_rounded:.1f}"
        
        region_keyed = cluster_events.select(
            *[pw.this[col] for col in cluster_events.column_names()],
            region_key=get_region_key(pw.this.latitude, pw.this.longitude)
        )
        
        # Count events per region in time window
        region_counts = region_keyed.groupby(pw.this.region_key).reduce(
            region_key=pw.this.region_key,
            event_count=pw.reducers.count(),
            event_ids=pw.reducers.unique(pw.this.event_id),
            event_types=pw.reducers.unique(pw.this.disaster_type),
            avg_severity=pw.reducers.avg(pw.this.risk_score if 'risk_score' in cluster_events.column_names() else pw.cast(float, 5.0))
        )
        
        # Filter for clusters (3+ events)
        clusters = region_counts.filter(pw.this.event_count >= self.min_cluster_size)
        
        # Generate cluster alerts
        @pw.udf
        def generate_cluster_alert(
            region_key: str, event_count: int, 
            event_ids: List[str], event_types: List[str]
        ) -> Dict:
            """Generate cluster alert."""
            return {
                'pattern_type': 'CLUSTER_ALERT',
                'pattern_severity': 'HIGH',
                'pattern_message': f'Multiple disasters ({event_count}) detected in close proximity',
                'pattern_recommendation': 'Activate regional emergency coordination',
                'event_ids': event_ids,
                'event_data': {
                    'region': region_key,
                    'count': event_count,
                    'types': event_types
                }
            }
        
        return clusters.select(
            pattern_type=pw.cast(str, 'CLUSTER_ALERT'),
            pattern_severity=pw.cast(str, 'HIGH'),
            pattern_message=pw.cast(str, 'Multiple disasters detected in close proximity'),
            pattern_recommendation=pw.cast(str, 'Activate regional emergency coordination'),
            event_ids=pw.this.event_ids,
            event_data=pw.cast(str, '{}')
        )
    
    def _detect_cascading_risks(self, events: pw.Table) -> pw.Table:
        """Detect risk of cascading disasters (e.g., earthquake → tsunami)."""
        
        @pw.udf
        def check_cascading_risk(
            disaster_type: str, lat: float, lon: float, 
            magnitude: float, severity: str, event_id: str
        ) -> Optional[Dict]:
            """Check for cascading disaster risk patterns."""
            
            # Pattern: Earthquake near coast → tsunami risk
            if disaster_type.lower() in ['earthquake', 'quake']:
                # Check if near coast (simplified: check if lat/lon in coastal regions)
                # In production, use proper geographic data
                if magnitude and magnitude >= 5.0:
                    return {
                        'pattern_type': 'CASCADING_RISK',
                        'pattern_severity': 'CRITICAL',
                        'pattern_message': 'Earthquake detected near coastal area - tsunami risk possible',
                        'pattern_recommendation': 'Issue early warning for coastal areas',
                        'event_ids': [event_id],
                        'event_data': {
                            'primary': 'earthquake',
                            'secondary_risk': 'tsunami',
                            'magnitude': magnitude
                        }
                    }
            
            # Pattern: Wildfire + drought conditions → rapid spread
            if disaster_type.lower() in ['wildfire', 'fire']:
                if severity and severity.upper() in ['RED', 'ORANGE']:
                    return {
                        'pattern_type': 'CASCADING_RISK',
                        'pattern_severity': 'HIGH',
                        'pattern_message': 'High-severity wildfire detected - rapid spread risk',
                        'pattern_recommendation': 'Monitor wind conditions and prepare evacuation routes',
                        'event_ids': [event_id],
                        'event_data': {
                            'primary': 'wildfire',
                            'secondary_risk': 'rapid_spread',
                            'severity': severity
                        }
                    }
            
            return None
        
        cascading_events = events.select(
            *[pw.this[col] for col in events.column_names()],
            cascading_data=check_cascading_risk(
                pw.this.disaster_type,
                pw.this.latitude,
                pw.this.longitude,
                pw.this.magnitude if 'magnitude' in events.column_names() else pw.cast(float, 0.0),
                pw.this.severity,
                pw.this.event_id
            )
        )
        
        cascading_filtered = cascading_events.filter(pw.this.cascading_data.is_not_none())
        
        # Extract cascading risk data
        @pw.udf
        def extract_cascading_info(cascading_data: Dict) -> str:
            """Extract cascading risk information."""
            if cascading_data:
                return str(cascading_data)
            return '{}'
        
        return cascading_filtered.select(
            pattern_type=pw.cast(str, 'CASCADING_RISK'),
            pattern_severity=pw.cast(str, 'HIGH'),
            pattern_message=pw.cast(str, 'Secondary disaster risk detected'),
            pattern_recommendation=pw.cast(str, 'Issue early warning'),
            event_ids=pw.this.event_id,
            event_data=extract_cascading_info(pw.this.cascading_data)
        )
    
    def _detect_severity_escalation(self, events: pw.Table) -> pw.Table:
        """Detect if disaster severity is escalating over time."""
        
        # Group by disaster type and location to track severity over time
        severity_tracking = events.groupby(
            pw.this.disaster_type,
            pw.this.location_name
        ).reduce(
            disaster_type=pw.this.disaster_type,
            location_name=pw.this.location_name,
            event_count=pw.reducers.count(),
            max_severity=pw.reducers.max(pw.this.severity),
            avg_risk_score=pw.reducers.avg(pw.this.risk_score if 'risk_score' in events.column_names() else pw.cast(float, 5.0))
        )
        
        # Filter for escalating patterns (multiple events with increasing severity)
        @pw.udf
        def check_escalation(
            event_count: int, max_severity: str, avg_risk: float
        ) -> Optional[Dict]:
            """Check if severity is escalating."""
            if event_count >= 2:
                if max_severity and max_severity.upper() in ['RED', 'ORANGE']:
                    if avg_risk and avg_risk >= 6.0:
                        return {
                            'pattern_type': 'ESCALATION',
                            'pattern_severity': 'MEDIUM',
                            'pattern_message': 'Disaster severity increasing over time',
                            'pattern_recommendation': 'Monitor situation closely and prepare response',
                            'event_data': {
                                'count': event_count,
                                'max_severity': max_severity,
                                'avg_risk': avg_risk
                            }
                        }
            return None
        
        escalation_data = severity_tracking.select(
            *[pw.this[col] for col in severity_tracking.column_names()],
            escalation=check_escalation(
                pw.this.event_count,
                pw.this.max_severity,
                pw.this.avg_risk_score
            )
        )
        
        escalation_filtered = escalation_data.filter(pw.this.escalation.is_not_none())
        
        return escalation_filtered.select(
            pattern_type=pw.cast(str, 'ESCALATION'),
            pattern_severity=pw.this.escalation['pattern_severity'],
            pattern_message=pw.this.escalation['pattern_message'],
            pattern_recommendation=pw.this.escalation['pattern_recommendation'],
            event_ids=pw.cast(List[str], []),
            event_data=pw.cast(str, '{}')
        )
