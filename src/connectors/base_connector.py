"""
Abstract base class for disaster data connectors.
Defines interface for streaming data sources in Pathway pipeline.
"""

from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any
import time
from src.utils.logger import app_logger

class BaseDisasterConnector(ABC):
    def __init__(self, polling_interval: int = 120):
        self.polling_interval = polling_interval
        self.logger = app_logger
    
    @abstractmethod
    def fetch_events(self) -> Iterator[Dict[str, Any]]:
        """
        Continuously fetch disaster events from source.
        Must yield dictionaries matching DisasterEvent schema.
        """
        pass
    
    def _safe_fetch(self) -> Iterator[Dict[str, Any]]:
        """
        Wrapper with error handling and logging.
        """
        while True:
            try:
                for event in self.fetch_events():
                    yield event
            except Exception as e:
                self.logger.log_error(self.__class__.__name__, e)
                time.sleep(self.polling_interval)
    
    @abstractmethod
    def parse_event(self, raw_data: Any) -> Dict[str, Any]:
        """
        Parse raw data from source into standardized event dict.
        """
        pass
