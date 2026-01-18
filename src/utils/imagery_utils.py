"""
Imagery utilities for generating satellite imagery URLs.
Provides Worldview URL generation for disaster event locations.
"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from src.utils.logger import app_logger


def generate_worldview_url(
    latitude: float,
    longitude: float,
    date: Optional[datetime] = None,
    layers: Optional[List[str]] = None,
    width: int = 800,
    height: int = 600,
    zoom_level: int = 8
) -> str:
    """
    Generate NASA Worldview URL for satellite imagery at given coordinates.
    
    Args:
        latitude: Event latitude
        longitude: Event longitude
        date: Date for imagery (defaults to today)
        layers: List of layer identifiers (e.g., ['MODIS_Terra_CorrectedReflectance_TrueColor'])
        width: Image width in pixels
        height: Image height in pixels
        zoom_level: Map zoom level
        
    Returns:
        Worldview URL string
    """
    if date is None:
        date = datetime.now()
    
    # Default layers for natural disasters
    if layers is None:
        layers = ['MODIS_Terra_CorrectedReflectance_TrueColor']
    
    # Format date for Worldview
    date_str = date.strftime('%Y-%m-%d')
    
    # Build Worldview URL
    base_url = "https://worldview.earthdata.nasa.gov"
    
    # Worldview snapshot API format
    # Using the newer snapshot API
    url = f"{base_url}/snapshot?layers={','.join(layers)}&time={date_str}&lat={latitude}&lon={longitude}&z={zoom_level}&width={width}&height={height}"
    
    return url


def generate_fires_worldview_url(
    latitude: float,
    longitude: float,
    date: Optional[datetime] = None
) -> str:
    """
    Generate Worldview URL optimized for wildfire detection.
    Uses MODIS Active Fires layer.
    """
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime('%Y-%m-%d')
    base_url = "https://worldview.earthdata.nasa.gov"
    
    # Use MODIS Active Fires layer
    layers = ['MODIS_Terra_Active_Fires', 'MODIS_Terra_CorrectedReflectance_TrueColor']
    url = f"{base_url}/snapshot?layers={','.join(layers)}&time={date_str}&lat={latitude}&lon={longitude}&z=10&width=800&height=600"
    
    return url


def generate_storm_worldview_url(
    latitude: float,
    longitude: float,
    date: Optional[datetime] = None
) -> str:
    """
    Generate Worldview URL optimized for storm/cyclone visualization.
    Uses GOES imagery for storms.
    """
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime('%Y-%m-%d')
    base_url = "https://worldview.earthdata.nasa.gov"
    
    # Use GOES imagery for storms
    layers = ['GOES-East_ABI_Band2_Red_Visible', 'MODIS_Terra_CorrectedReflectance_TrueColor']
    url = f"{base_url}/snapshot?layers={','.join(layers)}&time={date_str}&lat={latitude}&lon={longitude}&z=9&width=800&height=600"
    
    return url


def generate_volcano_worldview_url(
    latitude: float,
    longitude: float,
    date: Optional[datetime] = None
) -> str:
    """
    Generate Worldview URL optimized for volcano visualization.
    Uses thermal/sulfur dioxide layers.
    """
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime('%Y-%m-%d')
    base_url = "https://worldview.earthdata.nasa.gov"
    
    # Use MODIS thermal and true color
    layers = ['MODIS_Terra_Thermal_Anomalies_All', 'MODIS_Terra_CorrectedReflectance_TrueColor']
    url = f"{base_url}/snapshot?layers={','.join(layers)}&time={date_str}&lat={latitude}&lon={longitude}&z=10&width=800&height=600"
    
    return url


def get_imagery_urls_for_event(
    disaster_type: str,
    latitude: float,
    longitude: float,
    event_time: Optional[datetime] = None,
    existing_urls: Optional[List[str]] = None
) -> List[str]:
    """
    Get appropriate imagery URLs for a disaster event based on type.
    
    Args:
        disaster_type: Type of disaster (earthquake, wildfire, etc.)
        latitude: Event latitude
        longitude: Event longitude
        event_time: Event timestamp
        existing_urls: Pre-existing imagery URLs to include
        
    Returns:
        List of imagery URLs
    """
    urls = existing_urls or []
    
    # Skip if invalid coordinates
    if latitude == 0.0 and longitude == 0.0:
        return urls
    
    # Generate type-specific Worldview URL
    disaster_lower = disaster_type.lower()
    
    try:
        if 'wildfire' in disaster_lower or 'fire' in disaster_lower:
            worldview_url = generate_fires_worldview_url(latitude, longitude, event_time)
        elif 'storm' in disaster_lower or 'cyclone' in disaster_lower or 'hurricane' in disaster_lower:
            worldview_url = generate_storm_worldview_url(latitude, longitude, event_time)
        elif 'volcano' in disaster_lower:
            worldview_url = generate_volcano_worldview_url(latitude, longitude, event_time)
        else:
            worldview_url = generate_worldview_url(latitude, longitude, event_time)
        
        # Add Worldview URL if not already in list
        if worldview_url not in urls:
            urls.insert(0, worldview_url)  # Prepend Worldview URL
        
        # Limit to 3 URLs max
        return urls[:3]
    
    except Exception as e:
        app_logger.log_error("get_imagery_urls_for_event", e)
        return urls
