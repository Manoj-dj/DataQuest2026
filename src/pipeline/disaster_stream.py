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
from src.pipeline.risk_scoring import RiskScoringEngine
from src.utils.logger import app_logger
from src.utils.schemas import DisasterEvent
import os

class DisasterConnectorSubject(ConnectorSubject):
    def __init__(self, connector):
        super().__init__()
        self.connector = connector
    
    def run(self):
        for event in self.connector._safe_fetch():
            if event:
                self.next(
                    event_id=event.get('event_id', ''),
                    disaster_type=event.get('disaster_type', ''),
                    severity=event.get('severity', ''),
                    latitude=event.get('latitude', 0.0),
                    longitude=event.get('longitude', 0.0),
                    location_name=event.get('location_name', ''),
                    population_affected=event.get('population_affected', 0),
                    description=event.get('description', ''),
                    magnitude=event.get('magnitude'),
                    event_time=event.get('event_time', ''),
                    source=event.get('source', ''),
                    url=event.get('url', '')
                )
    
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
            schema=gdacs_schema,
            mode="streaming"
        )
        
        news_subject = DisasterConnectorSubject(self.news_connector)
        news_stream = pw.io.python.read(
            news_subject,
            schema=gdacs_schema,
            mode="streaming"
        )
        
        combined_stream = pw.Table.concat(gdacs_stream, news_stream)
        
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
            return self.risk_engine.calculate_risk_score(
                severity, population, disaster_type, magnitude
            )
        
        @pw.udf
        def add_ingestion_timestamp() -> str:
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
            risk_score=calculate_risk(
                pw.this.severity,
                pw.this.population_affected,
                pw.this.disaster_type,
                pw.this.magnitude
            ),
            ingested_at=add_ingestion_timestamp()
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
            mag_str = f" Magnitude: {magnitude}" if magnitude else ""
            
            text = f"""
DISASTER TYPE: {disaster_type.upper()}
SEVERITY: {severity}
LOCATION: {location}
POPULATION AFFECTED: {population:,} people
EVENT TIME: {event_time}
{mag_str}
SOURCE: {source}

DESCRIPTION:
{description}
""".strip()
            return text
        
        rag_ready = stream.select(
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
            metadata_json=pw.apply(
                lambda **kwargs: str(kwargs),
                disaster_type=pw.this.disaster_type,
                severity=pw.this.severity,
                risk_score=pw.this.risk_score,
                location=pw.this.location_name,
                source=pw.this.source,
                url=pw.this.url,
                event_time=pw.this.event_time
            )
        )
        
        return rag_ready
