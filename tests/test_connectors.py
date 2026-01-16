"""
Basic unit tests for disaster connectors.
"""

import pytest
from src.connectors.gdacs_connector import GDACSConnector
from src.utils.schemas import DisasterType, SeverityLevel

def test_gdacs_connector_initialization():
    """Test GDACS connector initializes correctly."""
    connector = GDACSConnector(
        rss_url="https://www.gdacs.org/xml/rss.xml",
        polling_interval=60
    )
    assert connector.polling_interval == 60
    assert connector.rss_url == "https://www.gdacs.org/xml/rss.xml"

def test_disaster_type_extraction():
    """Test disaster type classification."""
    connector = GDACSConnector("", 60)
    
    assert connector._extract_disaster_type("Earthquake M6.5") == DisasterType.EARTHQUAKE
    assert connector._extract_disaster_type("Wildfire in California") == DisasterType.WILDFIRE
    assert connector._extract_disaster_type("Flood in Bangladesh") == DisasterType.FLOOD

def test_severity_extraction():
    """Test severity level classification."""
    connector = GDACSConnector("", 60)
    
    assert connector._extract_severity("Red alert major", "") == SeverityLevel.RED
    assert connector._extract_severity("Orange moderate", "") == SeverityLevel.ORANGE
    assert connector._extract_severity("Green minor", "") == SeverityLevel.GREEN

if __name__ == "__main__":
    pytest.main([__file__])
