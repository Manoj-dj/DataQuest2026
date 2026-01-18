"""
Centralized logging configuration for DisasterLens AI.
Provides structured logging with timestamps, levels, and performance tracking.
"""

import sys
from pathlib import Path
from loguru import logger
from datetime import datetime
import json

class DisasterLogger:
    def __init__(self, log_level: str = "INFO"):
        self.logger = logger
        self.log_level = log_level
        self._setup_logger()
    
    def _setup_logger(self):
        logger.remove()
        
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.add(
            sys.stdout,
            format=log_format,
            level=self.log_level,
            colorize=True
        )
        
        logger.add(
            "logs/disasterlens_{time:YYYY-MM-DD}.log",
            format=log_format,
            level="DEBUG",
            rotation="00:00",
            retention="7 days",
            compression="zip"
        )
    
    def log_ingestion(self, event_id: str, source: str, latency_ms: float):
        logger.info(
            f"DATA_INGESTION | EventID={event_id} | Source={source} | "
            f"Latency={latency_ms:.2f}ms | Timestamp={datetime.now().isoformat()}"
        )
    
    def log_query(self, query: str, response_time_ms: float, source_count: int):
        logger.info(
            f"QUERY_PROCESSED | Query='{query[:50]}...' | "
            f"ResponseTime={response_time_ms:.2f}ms | SourcesRetrieved={source_count}"
        )
    
    def log_error(self, component: str, error: Exception):
        logger.error(
            f"ERROR | Component={component} | "
            f"Error={type(error).__name__} | Message={str(error)}"
        )
    
    def log_pipeline_update(self, event_count: int, processing_time_ms: float):
        logger.info(
            f"PIPELINE_UPDATE | EventsProcessed={event_count} | "
            f"ProcessingTime={processing_time_ms:.2f}ms"
        )

app_logger = DisasterLogger()
