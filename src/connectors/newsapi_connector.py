"""
NewsAPI connector for real-time disaster news articles.
Augments structured disaster data with contextual news coverage.
"""

import requests
import time
from typing import Iterator, Dict, Any
from datetime import datetime, timedelta
from src.connectors.base_connector import BaseDisasterConnector
from src.utils.schemas import DisasterType, SeverityLevel

class NewsAPIConnector(BaseDisasterConnector):
    def __init__(self, api_key: str, query: str, polling_interval: int = 180):
        super().__init__(polling_interval)
        self.api_key = api_key
        self.query = query
        self.base_url = "https://newsapi.org/v2/everything"
        self.seen_articles = set()
    
    def fetch_events(self) -> Iterator[Dict[str, Any]]:
        """
        Poll NewsAPI for disaster-related articles.
        """
        self.logger.logger.info(f"NewsAPI Connector started. Query: {self.query}")
        
        while True:
            try:
                start_time = time.time()
                
                params = {
                    'q': self.query,
                    'apiKey': self.api_key,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': 10,
                    'from': (datetime.now() - timedelta(hours=24)).isoformat()
                }
                
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                new_articles = 0
                
                if data.get('status') == 'ok':
                    for article in data.get('articles', []):
                        event = self.parse_event(article)
                        
                        if event and event['event_id'] not in self.seen_articles:
                            self.seen_articles.add(event['event_id'])
                            new_articles += 1
                            
                            latency_ms = (time.time() - start_time) * 1000
                            self.logger.log_ingestion(
                                event['event_id'],
                                'NewsAPI',
                                latency_ms
                            )
                            
                            yield event
                
                self.logger.logger.info(f"NewsAPI: Fetched {new_articles} new articles")
                time.sleep(self.polling_interval)
                
            except Exception as e:
                self.logger.log_error("NewsAPIConnector", e)
                time.sleep(self.polling_interval)
    
    def parse_event(self, article: Dict) -> Dict[str, Any]:
        """
        Parse NewsAPI article into disaster event format.
        """
        try:
            title = article.get('title', '')
            description = article.get('description', '') or ''
            content = article.get('content', '') or ''
            url = article.get('url', '')
            
            combined_text = f"{title} {description} {content}"
            
            disaster_type = self._classify_disaster_type(combined_text)
            severity = self._estimate_severity(combined_text)
            
            event_id = f"NEWS-{hash(url)}"
            
            published_at = article.get('publishedAt')
            event_time = datetime.now()
            if published_at:
                try:
                    event_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                except:
                    pass
            
            return {
                'event_id': event_id,
                'disaster_type': disaster_type.value,
                'severity': severity.value,
                'latitude': 0.0,
                'longitude': 0.0,
                'location_name': self._extract_location(combined_text),
                'population_affected': self._estimate_impact(combined_text),
                'description': (description or content)[:500],
                'magnitude': None,
                'event_time': event_time.isoformat(),
                'source': 'NewsAPI',
                'url': url
            }
        
        except Exception as e:
            self.logger.log_error("NewsAPIConnector.parse_event", e)
            return None
    
    def _classify_disaster_type(self, text: str) -> DisasterType:
        text_lower = text.lower()
        
        type_keywords = {
            DisasterType.EARTHQUAKE: ['earthquake', 'quake', 'seismic', 'tremor'],
            DisasterType.WILDFIRE: ['wildfire', 'forest fire', 'bushfire', 'blaze'],
            DisasterType.FLOOD: ['flood', 'flooding', 'deluge', 'inundation'],
            DisasterType.CYCLONE: ['cyclone', 'hurricane', 'typhoon', 'tropical storm'],
            DisasterType.TSUNAMI: ['tsunami', 'tidal wave'],
            DisasterType.VOLCANO: ['volcano', 'volcanic', 'eruption'],
            DisasterType.DROUGHT: ['drought', 'water shortage']
        }
        
        for disaster_type, keywords in type_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return disaster_type
        
        return DisasterType.UNKNOWN
    
    def _estimate_severity(self, text: str) -> SeverityLevel:
        text_lower = text.lower()
        
        red_keywords = ['catastrophic', 'devastating', 'severe', 'major', 'deadly', 'fatal']
        orange_keywords = ['significant', 'moderate', 'considerable', 'substantial']
        
        if any(keyword in text_lower for keyword in red_keywords):
            return SeverityLevel.RED
        elif any(keyword in text_lower for keyword in orange_keywords):
            return SeverityLevel.ORANGE
        else:
            return SeverityLevel.GREEN
    
    def _extract_location(self, text: str) -> str:
        import re
        
        location_patterns = [
            r'in ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'near ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'at ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return "Unknown Location"
    
    def _estimate_impact(self, text: str) -> int:
        import re
        
        patterns = [
            r'(\d+(?:,\d+)*)\s*(?:people|victims|casualties|affected)',
            r'(\d+(?:,\d+)*)\s*(?:dead|killed|deaths)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1).replace(',', ''))
        
        severity_estimates = {
            'catastrophic': 10000,
            'devastating': 5000,
            'severe': 1000,
            'major': 500
        }
        
        for keyword, estimate in severity_estimates.items():
            if keyword in text.lower():
                return estimate
        
        return 100
