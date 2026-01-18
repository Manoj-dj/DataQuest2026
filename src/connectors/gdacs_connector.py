"""
GDACS (Global Disaster Alert and Coordination System) connector.
Fetches real-time disaster alerts from GDACS RSS feed.
Provides structured earthquake, flood, cyclone, and wildfire data.
"""

import requests
import feedparser
import time
from typing import Iterator, Dict, Any
from datetime import datetime
from src.connectors.base_connector import BaseDisasterConnector
from src.utils.schemas import DisasterType, SeverityLevel

class GDACSConnector(BaseDisasterConnector):
    def __init__(self, rss_url: str, polling_interval: int = 120):
        super().__init__(polling_interval)
        self.rss_url = rss_url
        self.seen_events = set()
    
    def fetch_events(self) -> Iterator[Dict[str, Any]]:
        """
        Poll GDACS RSS feed and yield new disaster events.
        """
        self.logger.logger.info(f"GDACS Connector started. Polling every {self.polling_interval}s")
        
        while True:
            try:
                start_time = time.time()
                response = requests.get(self.rss_url, timeout=10)
                response.raise_for_status()
                
                feed = feedparser.parse(response.content)
                new_events = 0
                
                # DEBUG: Log first event schema for Pathway debugging
                if feed.entries and len(self.seen_events) == 0:
                    first_event = self.parse_event(feed.entries[0]) if feed.entries else None
                    if first_event:
                        self.logger.logger.info(f"=== GDACS EVENT SCHEMA DEBUG ===")
                        self.logger.logger.info(f"Sample event keys: {list(first_event.keys())}")
                        self.logger.logger.info(f"Sample event (first 500 chars): {str(first_event)[:500]}")
                        self.logger.logger.info(f"================================")
                
                for entry in feed.entries:
                    event = self.parse_event(entry)
                    
                    if event and event['event_id'] not in self.seen_events:
                        self.seen_events.add(event['event_id'])
                        new_events += 1
                        
                        latency_ms = (time.time() - start_time) * 1000
                        self.logger.log_ingestion(
                            event['event_id'],
                            'GDACS',
                            latency_ms
                        )
                        
                        yield event
                
                self.logger.logger.info(f"GDACS: Fetched {new_events} new events")
                time.sleep(self.polling_interval)
                
            except Exception as e:
                self.logger.log_error("GDACSConnector", e)
                time.sleep(self.polling_interval)
    
    def parse_event(self, entry: Any) -> Dict[str, Any]:
        """
        Parse GDACS RSS entry into standardized event format.
        """
        try:
            title = entry.get('title', '')
            description = entry.get('description', '')
            link = entry.get('link', '')
            
            disaster_type = self._extract_disaster_type(title)
            severity = self._extract_severity(title, description)
            
            event_id = entry.get('id', f"GDACS-{hash(title)}")
            
            coords = self._extract_coordinates(entry)
            location = self._extract_location(title, description)
            
            magnitude = self._extract_magnitude(description)
            pop_affected = self._extract_population(description)
            
            event_time_str = entry.get('published', entry.get('updated'))
            event_time = datetime.now()
            if event_time_str:
                try:
                    from email.utils import parsedate_to_datetime
                    event_time = parsedate_to_datetime(event_time_str)
                except:
                    pass
            
            return {
                'event_id': event_id,
                'disaster_type': disaster_type.value,
                'severity': severity.value,
                'latitude': coords[0],
                'longitude': coords[1],
                'location_name': location,
                'population_affected': pop_affected,
                'description': description[:500],
                'magnitude': magnitude,
                'event_time': event_time.isoformat(),
                'source': 'GDACS',
                'url': link
            }
        
        except Exception as e:
            self.logger.log_error("GDACSConnector.parse_event", e)
            return None
    
    def _extract_disaster_type(self, title: str) -> DisasterType:
        title_lower = title.lower()
        if 'earthquake' in title_lower or 'quake' in title_lower:
            return DisasterType.EARTHQUAKE
        elif 'flood' in title_lower:
            return DisasterType.FLOOD
        elif 'fire' in title_lower:
            return DisasterType.WILDFIRE
        elif 'cyclone' in title_lower or 'hurricane' in title_lower or 'typhoon' in title_lower:
            return DisasterType.CYCLONE
        elif 'tsunami' in title_lower:
            return DisasterType.TSUNAMI
        elif 'volcano' in title_lower:
            return DisasterType.VOLCANO
        else:
            return DisasterType.UNKNOWN
    
    def _extract_severity(self, title: str, description: str) -> SeverityLevel:
        combined = (title + " " + description).lower()
        if 'red' in combined or 'severe' in combined or 'major' in combined:
            return SeverityLevel.RED
        elif 'orange' in combined or 'moderate' in combined:
            return SeverityLevel.ORANGE
        elif 'green' in combined or 'minor' in combined:
            return SeverityLevel.GREEN
        else:
            return SeverityLevel.UNKNOWN
    
    def _extract_coordinates(self, entry: Any) -> tuple:
        """Extract latitude and longitude from entry."""
        if hasattr(entry, 'geo_lat') and hasattr(entry, 'geo_long'):
            return (float(entry.geo_lat), float(entry.geo_long))
        
        if 'georss_point' in entry:
            try:
                coords = entry.georss_point.split()
                return (float(coords[0]), float(coords[1]))
            except:
                pass
        
        return (0.0, 0.0)
    
    def _extract_location(self, title: str, description: str) -> str:
        parts = title.split(',')
        if len(parts) > 1:
            return parts[-1].strip()
        return "Unknown Location"
    
    def _extract_magnitude(self, description: str) -> float:
        import re
        match = re.search(r'magnitude[:\s]+(\d+\.?\d*)', description.lower())
        if match:
            return float(match.group(1))
        return None
    
    def _extract_population(self, description: str) -> int:
        import re
        match = re.search(r'(\d+(?:,\d+)*)\s*(?:people|population|affected)', description.lower())
        if match:
            return int(match.group(1).replace(',', ''))
        return 0
