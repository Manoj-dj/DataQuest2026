"""
NASA EONET (Earth Observing Natural Event Tracker) connector.
Fetches real-time natural disaster events with satellite imagery links.
Provides structured wildfire, volcano, storm, and other event data.
"""

import requests
import time
from typing import Iterator, Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.connectors.base_connector import BaseDisasterConnector
from src.utils.schemas import DisasterType, SeverityLevel
from src.utils.logger import app_logger


class NASAEONETConnector(BaseDisasterConnector):
    def __init__(
        self,
        api_url: str = "https://eonet.gsfc.nasa.gov/api/v3/events",
        polling_interval: int = 300,
        max_images_per_event: int = 3
    ):
        super().__init__(polling_interval)
        self.api_url = api_url
        self.max_images_per_event = max_images_per_event
        self.seen_events = set()
        self.logger = app_logger
    
    def fetch_events(self) -> Iterator[Dict[str, Any]]:
        """
        Poll NASA EONET API and yield new disaster events with imagery.
        """
        self.logger.logger.info(f"NASA EONET Connector started. Polling every {self.polling_interval}s")
        
        while True:
            try:
                start_time = time.time()
                
                # Fetch events from last 7 days
                params = {
                    'days': 7,
                    'status': 'open',
                    'limit': 50
                }
                
                response = requests.get(self.api_url, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                events = data.get('events', [])
                new_events = 0
                
                for raw_event in events:
                    event = self.parse_event(raw_event)
                    
                    if event and event['event_id'] not in self.seen_events:
                        self.seen_events.add(event['event_id'])
                        new_events += 1
                        
                        latency_ms = (time.time() - start_time) * 1000
                        self.logger.log_ingestion(
                            event['event_id'],
                            'NASA_EONET',
                            latency_ms
                        )
                        
                        yield event
                
                self.logger.logger.info(f"NASA EONET: Fetched {new_events} new events")
                time.sleep(self.polling_interval)
                
            except Exception as e:
                self.logger.log_error("NASAEONETConnector", e)
                time.sleep(self.polling_interval)
    
    def parse_event(self, raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse NASA EONET event into standardized format with imagery.
        """
        try:
            event_id = f"EONET-{raw_event.get('id', '')}"
            title = raw_event.get('title', 'Unknown Event')
            
            # Extract disaster type from categories
            categories = raw_event.get('categories', [])
            disaster_type = self._extract_disaster_type(categories)
            
            # Skip if not a disaster type we care about
            if disaster_type == DisasterType.UNKNOWN:
                return None
            
            # Extract geometry (coordinates)
            geometries = raw_event.get('geometry', [])
            coords = self._extract_coordinates(geometries)
            
            # Extract dates
            dates = raw_event.get('geometry', [])
            event_time = self._extract_event_time(dates)
            
            # Extract imagery links
            imagery_urls = self._extract_imagery_urls(raw_event)
            
            # Generate severity (NASA doesn't provide this, estimate from event type)
            severity = self._estimate_severity(disaster_type, raw_event)
            
            # Extract location name
            location_name = self._extract_location_name(title, coords)
            
            description = self._build_description(raw_event, disaster_type, location_name)
            
            return {
                'event_id': event_id,
                'disaster_type': disaster_type.value,
                'severity': severity.value,
                'latitude': coords[0],
                'longitude': coords[1],
                'location_name': location_name,
                'population_affected': 0,  # NASA EONET doesn't provide this
                'description': description,
                'magnitude': None,
                'event_time': event_time.isoformat(),
                'source': 'NASA_EONET',
                'url': raw_event.get('link', ''),
                'imagery_urls': imagery_urls,
                'categories': [cat.get('title', '') for cat in categories]
            }
        
        except Exception as e:
            self.logger.log_error("NASAEONETConnector.parse_event", e)
            return None
    
    def _extract_disaster_type(self, categories: List[Dict[str, Any]]) -> DisasterType:
        """Map NASA EONET categories to disaster types."""
        if not categories:
            return DisasterType.UNKNOWN
        
        # Check category IDs (more reliable than titles)
        category_ids = [cat.get('id', 0) for cat in categories]
        
        # NASA EONET category IDs
        # 8: Wildfires, 12: Volcanoes, 10: Dust and Haze, 14: Severe Storms
        # 15: Snow, 16: Floods, 17: Landslides, 18: Earthquakes
        if 8 in category_ids:
            return DisasterType.WILDFIRE
        elif 12 in category_ids:
            return DisasterType.VOLCANO
        elif 18 in category_ids:
            return DisasterType.EARTHQUAKE
        elif 16 in category_ids:
            return DisasterType.FLOOD
        elif 14 in category_ids:
            return DisasterType.CYCLONE
        
        # Fallback to category titles
        for cat in categories:
            title_lower = cat.get('title', '').lower()
            if 'wildfire' in title_lower or 'fire' in title_lower:
                return DisasterType.WILDFIRE
            elif 'volcano' in title_lower:
                return DisasterType.VOLCANO
            elif 'earthquake' in title_lower or 'quake' in title_lower:
                return DisasterType.EARTHQUAKE
            elif 'flood' in title_lower:
                return DisasterType.FLOOD
            elif 'storm' in title_lower or 'hurricane' in title_lower or 'cyclone' in title_lower:
                return DisasterType.CYCLONE
        
        return DisasterType.UNKNOWN
    
    def _extract_coordinates(self, geometries: List[Dict[str, Any]]) -> tuple:
        """Extract centroid coordinates from geometry."""
        if not geometries:
            return (0.0, 0.0)
        
        # Use the first geometry point
        first_geom = geometries[0]
        coords = first_geom.get('coordinates', [0.0, 0.0])
        
        # Handle both [lon, lat] and [[lon, lat]] formats
        if isinstance(coords[0], list):
            coords = coords[0]
        
        # NASA provides [longitude, latitude]
        longitude = float(coords[0]) if len(coords) > 0 else 0.0
        latitude = float(coords[1]) if len(coords) > 1 else 0.0
        
        return (latitude, longitude)
    
    def _extract_event_time(self, geometries: List[Dict[str, Any]]) -> datetime:
        """Extract event time from geometry date."""
        if geometries:
            first_geom = geometries[0]
            date_str = first_geom.get('date', '')
            if date_str:
                try:
                    # NASA EONET dates are in ISO format
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    pass
        
        return datetime.now()
    
    def _extract_imagery_urls(self, raw_event: Dict[str, Any]) -> List[str]:
        """
        Extract imagery URLs from EONET event.
        EONET provides links to sources, but we'll use Worldview URL generation
        based on coordinates for satellite imagery.
        """
        imagery_urls = []
        
        # Check for direct image links in event
        if 'sources' in raw_event:
            for source in raw_event['sources']:
                source_url = source.get('url', '')
                if source_url and any(ext in source_url.lower() for ext in ['.jpg', '.png', '.jpeg', 'imagery']):
                    imagery_urls.append(source_url)
        
        # Will be supplemented with Worldview URLs in pipeline
        return imagery_urls[:self.max_images_per_event]
    
    def _estimate_severity(self, disaster_type: DisasterType, raw_event: Dict[str, Any]) -> SeverityLevel:
        """Estimate severity based on disaster type and event data."""
        # For now, default to Orange for most events
        # Could be enhanced with more sophisticated logic
        return SeverityLevel.ORANGE
    
    def _extract_location_name(self, title: str, coords: tuple) -> str:
        """Extract location name from title."""
        # EONET titles often have format "Event Name, Location"
        if ',' in title:
            parts = title.split(',')
            if len(parts) > 1:
                return parts[-1].strip()
        return title.strip() if title else "Unknown Location"
    
    def _build_description(self, raw_event: Dict[str, Any], disaster_type: DisasterType, location: str) -> str:
        """Build description for the event."""
        title = raw_event.get('title', '')
        categories = [cat.get('title', '') for cat in raw_event.get('categories', [])]
        
        desc_parts = [
            f"{disaster_type.value.replace('_', ' ').title()} event detected",
            f"Location: {location}",
            f"Categories: {', '.join(categories)}" if categories else ""
        ]
        
        return ". ".join(filter(None, desc_parts))[:500]
