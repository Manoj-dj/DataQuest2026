"""
Core Pathway streaming pipeline for disaster event processing.
Handles real-time ingestion, transformation, enrichment, and indexing.
"""

from typing import Dict
import pathway as pw
from pathway.io.python import ConnectorSubject
from datetime import datetime
from src.connectors.gdacs_connector import GDACSConnector
from src.connectors.newsapi_connector import NewsAPIConnector
from src.connectors.nasa_eonet_connector import NASAEONETConnector
from src.pipeline.risk_scoring import RiskScoringEngine
from src.utils.logger import app_logger
from src.utils.schemas import DisasterEvent
from src.utils.imagery_utils import get_imagery_urls_for_event
from datetime import datetime
import os

class DisasterConnectorSubject(ConnectorSubject):
    def __init__(self, connector, include_imagery=False):
        super().__init__()
        self.connector = connector
        self.include_imagery = include_imagery
    
    def run(self):
        import json
        for event in self.connector._safe_fetch():
            if event:
                # Convert None magnitude to 0.0 for Pathway schema compatibility
                magnitude = event.get('magnitude')
                if magnitude is None:
                    magnitude = 0.0
                
                data = {
                    'event_id': event.get('event_id', ''),
                    'disaster_type': event.get('disaster_type', ''),
                    'severity': event.get('severity', ''),
                    'latitude': event.get('latitude', 0.0),
                    'longitude': event.get('longitude', 0.0),
                    'location_name': event.get('location_name', ''),
                    'population_affected': event.get('population_affected', 0),
                    'description': event.get('description', ''),
                    'magnitude': magnitude,
                    'event_time': event.get('event_time', ''),
                    'source': event.get('source', ''),
                    'url': event.get('url', '')
                }
                
                # Include imagery URLs if present
                if self.include_imagery and 'imagery_urls' in event:
                    imagery_urls = event.get('imagery_urls', [])
                    if imagery_urls:
                        data['imagery_urls'] = json.dumps(imagery_urls) if isinstance(imagery_urls, list) else str(imagery_urls)
                    else:
                        data['imagery_urls'] = '[]'
                
                self.next(**data)
    
    @property
    def _deletions_enabled(self):
        return False

class DisasterStreamPipeline:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = app_logger
        self.risk_engine = RiskScoringEngine(config['risk_scoring'])
        
        self.gdacs_connector = GDACSConnector(
            rss_url=config['data_sources']['gdacs']['url'],
            polling_interval=config['data_sources']['gdacs']['polling_interval']
        )
        
        newsapi_key = os.getenv('NEWSAPI_KEY')
        self.news_connector = NewsAPIConnector(
            api_key=newsapi_key,
            query=config['data_sources']['newsapi']['query'],
            polling_interval=config['data_sources']['newsapi']['polling_interval']
        )
        
        # Initialize NASA EONET connector if enabled
        if config.get('data_sources', {}).get('nasa_eonet', {}).get('enabled', True):
            self.nasa_eonet_connector = NASAEONETConnector(
                api_url=config['data_sources']['nasa_eonet']['api_url'],
                polling_interval=config['data_sources']['nasa_eonet']['polling_interval'],
                max_images_per_event=config['data_sources']['nasa_eonet'].get('max_images_per_event', 3)
            )
        else:
            self.nasa_eonet_connector = None
    
    def build_pipeline(self) -> pw.Table:
        """
        Construct the complete Pathway streaming pipeline.
        """
        self.logger.logger.info("Building Pathway streaming pipeline...")
        
        gdacs_schema = pw.schema_builder({
            'event_id': pw.column_definition(dtype=str),
            'disaster_type': pw.column_definition(dtype=str),
            'severity': pw.column_definition(dtype=str),
            'latitude': pw.column_definition(dtype=float),
            'longitude': pw.column_definition(dtype=float),
            'location_name': pw.column_definition(dtype=str),
            'population_affected': pw.column_definition(dtype=int),
            'description': pw.column_definition(dtype=str),
            'magnitude': pw.column_definition(dtype=float, default_value=None),
            'event_time': pw.column_definition(dtype=str),
            'source': pw.column_definition(dtype=str),
            'url': pw.column_definition(dtype=str, default_value='')
        })
        
        gdacs_subject = DisasterConnectorSubject(self.gdacs_connector)
        gdacs_stream = pw.io.python.read(
            gdacs_subject,
            schema=gdacs_schema
        )
        
        news_subject = DisasterConnectorSubject(self.news_connector)
        news_stream = pw.io.python.read(
            news_subject,
            schema=gdacs_schema
        )
        
        # Streams will be combined later after adding imagery_urls_json column
        
        # UDF to prefix event IDs with source to ensure disjointness
        @pw.udf
        def prefix_event_id(source: str, event_id: str) -> str:
            return f"{source.lower()}:{event_id}"
        
        if self.nasa_eonet_connector:
            nasa_schema = pw.schema_builder({
                'event_id': pw.column_definition(dtype=str),
                'disaster_type': pw.column_definition(dtype=str),
                'severity': pw.column_definition(dtype=str),
                'latitude': pw.column_definition(dtype=float),
                'longitude': pw.column_definition(dtype=float),
                'location_name': pw.column_definition(dtype=str),
                'population_affected': pw.column_definition(dtype=int),
                'description': pw.column_definition(dtype=str),
                'magnitude': pw.column_definition(dtype=float, default_value=0.0),
                'event_time': pw.column_definition(dtype=str),
                'source': pw.column_definition(dtype=str),
                'url': pw.column_definition(dtype=str, default_value=''),
                'imagery_urls': pw.column_definition(dtype=str, default_value='')  # JSON string
            })
            
            nasa_subject = DisasterConnectorSubject(self.nasa_eonet_connector, include_imagery=True)
            nasa_stream = pw.io.python.read(
                nasa_subject,
                schema=nasa_schema
            )
            
            # Convert NASA stream to match standard schema (extract imagery_urls)
            @pw.udf
            def extract_imagery_json(imagery_field: str) -> str:
                """Extract imagery URLs as JSON string."""
                import json
                try:
                    if imagery_field:
                        urls = json.loads(imagery_field) if isinstance(imagery_field, str) else imagery_field
                        return json.dumps(urls if isinstance(urls, list) else [])
                except:
                    pass
                return '[]'
            
            # Normalize NASA stream to standard format with imagery_urls_json
            # Use with_id_from to set row IDs based on prefixed event_id
            nasa_normalized = nasa_stream.select(
                event_id=prefix_event_id(pw.this.source, pw.this.event_id),
                disaster_type=pw.this.disaster_type,
                severity=pw.this.severity,
                latitude=pw.this.latitude,
                longitude=pw.this.longitude,
                location_name=pw.this.location_name,
                population_affected=pw.this.population_affected,
                description=pw.this.description,
                magnitude=pw.this.magnitude,
                event_time=pw.this.event_time,
                source=pw.this.source,
                url=pw.this.url,
                imagery_urls_json=pw.this.imagery_urls if 'imagery_urls' in nasa_stream.column_names() else pw.cast(str, '[]')
            ).with_id_from(pw.this.event_id)
            
            # Add imagery_urls_json column to other streams (empty array)
            # Prefix event_ids and set row IDs to ensure disjointness across sources
            gdacs_with_imagery = gdacs_stream.select(
                event_id=prefix_event_id(pw.this.source, pw.this.event_id),
                disaster_type=pw.this.disaster_type,
                severity=pw.this.severity,
                latitude=pw.this.latitude,
                longitude=pw.this.longitude,
                location_name=pw.this.location_name,
                population_affected=pw.this.population_affected,
                description=pw.this.description,
                magnitude=pw.this.magnitude,
                event_time=pw.this.event_time,
                source=pw.this.source,
                url=pw.this.url,
                imagery_urls_json=pw.cast(str, '[]')
            ).with_id_from(pw.this.event_id)
            
            news_with_imagery = news_stream.select(
                event_id=prefix_event_id(pw.this.source, pw.this.event_id),
                disaster_type=pw.this.disaster_type,
                severity=pw.this.severity,
                latitude=pw.this.latitude,
                longitude=pw.this.longitude,
                location_name=pw.this.location_name,
                population_affected=pw.this.population_affected,
                description=pw.this.description,
                magnitude=pw.this.magnitude,
                event_time=pw.this.event_time,
                source=pw.this.source,
                url=pw.this.url,
                imagery_urls_json=pw.cast(str, '[]')
            ).with_id_from(pw.this.event_id)
            
            # Promise universes are disjoint and concat streams
            pw.universes.promise_are_pairwise_disjoint(gdacs_with_imagery, news_with_imagery)
            temp_combined = pw.Table.concat(gdacs_with_imagery, news_with_imagery)
            # Then add NASA if available
            if nasa_normalized is not None:
                pw.universes.promise_are_pairwise_disjoint(temp_combined, nasa_normalized)
                combined_stream = pw.Table.concat(temp_combined, nasa_normalized)
            else:
                combined_stream = temp_combined
        else:
            # No NASA connector - just combine GDACS and News
            # Add imagery_urls_json column to both streams (empty array)
            # Prefix event_ids and set row IDs to ensure disjointness
            gdacs_with_imagery = gdacs_stream.select(
                event_id=prefix_event_id(pw.this.source, pw.this.event_id),
                disaster_type=pw.this.disaster_type,
                severity=pw.this.severity,
                latitude=pw.this.latitude,
                longitude=pw.this.longitude,
                location_name=pw.this.location_name,
                population_affected=pw.this.population_affected,
                description=pw.this.description,
                magnitude=pw.this.magnitude,
                event_time=pw.this.event_time,
                source=pw.this.source,
                url=pw.this.url,
                imagery_urls_json=pw.cast(str, '[]')
            ).with_id_from(pw.this.event_id)
            
            news_with_imagery = news_stream.select(
                event_id=prefix_event_id(pw.this.source, pw.this.event_id),
                disaster_type=pw.this.disaster_type,
                severity=pw.this.severity,
                latitude=pw.this.latitude,
                longitude=pw.this.longitude,
                location_name=pw.this.location_name,
                population_affected=pw.this.population_affected,
                description=pw.this.description,
                magnitude=pw.this.magnitude,
                event_time=pw.this.event_time,
                source=pw.this.source,
                url=pw.this.url,
                imagery_urls_json=pw.cast(str, '[]')
            ).with_id_from(pw.this.event_id)
            
            # Promise universes are disjoint and concat
            pw.universes.promise_are_pairwise_disjoint(gdacs_with_imagery, news_with_imagery)
            combined_stream = pw.Table.concat(gdacs_with_imagery, news_with_imagery)
        
        enriched_stream = self._enrich_events(combined_stream)
        
        output_stream = self._prepare_for_rag(enriched_stream)
        
        self.logger.logger.info("Pathway pipeline built successfully")
        
        return output_stream
    
    def _enrich_events(self, stream: pw.Table) -> pw.Table:
        """
        Apply transformations: risk scoring, timestamp, deduplication.
        """
        
        @pw.udf
        def calculate_risk(
            severity: str,
            population: int,
            disaster_type: str,
            magnitude: float
        ) -> float:
            try:
                # Ensure safe type conversions
                pop = int(population) if population else 0
                mag = float(magnitude) if magnitude else 0.0
                sev = str(severity) if severity else 'Unknown'
                dtype = str(disaster_type) if disaster_type else 'unknown'
                
                return self.risk_engine.calculate_risk_score(
                    sev, pop, dtype, mag
                )
            except Exception as e:
                # Return default risk score on error
                return 5.0
        
        @pw.udf
        def add_ingestion_timestamp(_dummy: str) -> str:
            """Add ingestion timestamp. _dummy parameter required for Pathway UDFs."""
            return datetime.now().isoformat()
        
        enriched = stream.select(
            event_id=pw.this.event_id,
            disaster_type=pw.this.disaster_type,
            severity=pw.this.severity,
            latitude=pw.this.latitude,
            longitude=pw.this.longitude,
            location_name=pw.this.location_name,
            population_affected=pw.this.population_affected,
            description=pw.this.description,
            magnitude=pw.this.magnitude,
            event_time=pw.this.event_time,
            source=pw.this.source,
            url=pw.this.url,
            imagery_urls_json=pw.this.imagery_urls_json if 'imagery_urls_json' in stream.column_names() else pw.cast(str, '[]'),
            risk_score=calculate_risk(
                pw.this.severity,
                pw.this.population_affected,
                pw.this.disaster_type,
                pw.this.magnitude
            ),
            ingested_at=add_ingestion_timestamp(pw.this.event_id)
        )
        
        return enriched
    
    def _prepare_for_rag(self, stream: pw.Table) -> pw.Table:
        """
        Format events for vector database ingestion.
        Create text representation for embedding.
        """
        
        @pw.udf
        def format_text_content(
            disaster_type: str,
            severity: str,
            location: str,
            population: int,
            description: str,
            magnitude: float,
            event_time: str,
            source: str
        ) -> str:
            try:
                # Safe string conversions
                dtype = str(disaster_type) if disaster_type else 'Unknown'
                sev = str(severity) if severity else 'Unknown'
                loc = str(location) if location else 'Unknown Location'
                pop = int(population) if population else 0
                desc = str(description) if description else ''
                mag = float(magnitude) if magnitude and magnitude > 0 else None
                etime = str(event_time) if event_time else ''
                src = str(source) if source else 'Unknown'
                
                mag_str = f" Magnitude: {mag}" if mag else ""
                
                text = f"""
DISASTER TYPE: {dtype.upper()}
SEVERITY: {sev}
LOCATION: {loc}
POPULATION AFFECTED: {pop:,} people
EVENT TIME: {etime}
{mag_str}
SOURCE: {src}

DESCRIPTION:
{desc}
""".strip()
                return text
            except Exception as e:
                # Return minimal text on error
                return f"Disaster event: {str(disaster_type or 'Unknown')} at {str(location or 'Unknown')}"
        
        @pw.udf
        def enhance_imagery_urls(
            latitude: float,
            longitude: float,
            disaster_type: str,
            event_time: str,
            existing_urls_json: str
        ) -> str:
            """Enhance imagery URLs with Worldview URLs."""
            import json
            from datetime import datetime
            
            try:
                # Parse existing URLs
                existing_urls = []
                if existing_urls_json and existing_urls_json != '[]':
                    existing_urls = json.loads(existing_urls_json) if isinstance(existing_urls_json, str) else existing_urls_json
                
                # Parse event time
                event_dt = None
                if event_time:
                    try:
                        event_dt = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                    except:
                        pass
                
                # Get enhanced imagery URLs
                enhanced_urls = get_imagery_urls_for_event(
                    disaster_type=disaster_type,
                    latitude=float(latitude),
                    longitude=float(longitude),
                    event_time=event_dt,
                    existing_urls=existing_urls if isinstance(existing_urls, list) else []
                )
                
                return json.dumps(enhanced_urls)
            except Exception as e:
                return existing_urls_json if existing_urls_json else '[]'
        
        # Check if imagery_urls_json column exists (from NASA EONET)
        try:
            imagery_enhanced = stream.select(
                event_id=pw.this.event_id,
                text_content=format_text_content(
                    pw.this.disaster_type,
                    pw.this.severity,
                    pw.this.location_name,
                    pw.this.population_affected,
                    pw.this.description,
                    pw.this.magnitude,
                    pw.this.event_time,
                    pw.this.source
                ),
                imagery_urls_json=enhance_imagery_urls(
                    pw.this.latitude,
                    pw.this.longitude,
                    pw.this.disaster_type,
                    pw.this.event_time,
                    getattr(pw.this, 'imagery_urls_json', pw.cast(str, '[]'))
                ),
                metadata_json=pw.apply(
                    lambda **kwargs: str(kwargs),
                    disaster_type=pw.this.disaster_type,
                    severity=pw.this.severity,
                    risk_score=pw.this.risk_score,
                    location=pw.this.location_name,
                    location_name=pw.this.location_name,
                    latitude=pw.this.latitude,
                    longitude=pw.this.longitude,
                    source=pw.this.source,
                    url=pw.this.url,
                    event_time=pw.this.event_time,
                    population_affected=pw.this.population_affected,
                    magnitude=pw.this.magnitude
                )
            )
        except:
            # Fallback if imagery_urls_json column doesn't exist
            imagery_enhanced = stream.select(
                event_id=pw.this.event_id,
                text_content=format_text_content(
                    pw.this.disaster_type,
                    pw.this.severity,
                    pw.this.location_name,
                    pw.this.population_affected,
                    pw.this.description,
                    pw.this.magnitude,
                    pw.this.event_time,
                    pw.this.source
                ),
                imagery_urls_json=enhance_imagery_urls(
                    pw.this.latitude,
                    pw.this.longitude,
                    pw.this.disaster_type,
                    pw.this.event_time,
                    '[]'
                ),
                metadata_json=pw.apply(
                    lambda **kwargs: str(kwargs),
                    disaster_type=pw.this.disaster_type,
                    severity=pw.this.severity,
                    risk_score=pw.this.risk_score,
                    location=pw.this.location_name,
                    location_name=pw.this.location_name,
                    latitude=pw.this.latitude,
                    longitude=pw.this.longitude,
                    source=pw.this.source,
                    url=pw.this.url,
                    event_time=pw.this.event_time,
                    population_affected=pw.this.population_affected,
                    magnitude=pw.this.magnitude
                )
            )
        
        return imagery_enhanced
