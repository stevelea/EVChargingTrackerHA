"""
Home Assistant add-on adapter for EV Charging Tracker.
This module provides functions to interface with the Home Assistant add-on environment.
"""

import os
import logging
import json
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ha_addon")

# Constants
HA_DATA_DIR = os.environ.get('EVCT_DATA_DIR', '/data')
DEFAULT_GUEST_MODE = os.environ.get('EVCT_GUEST_MODE', 'true').lower() == 'true'
DEFAULT_GUEST_PASSWORD = os.environ.get('EVCT_GUEST_PASSWORD', 'evdata2023')
DEFAULT_REFRESH_INTERVAL = int(os.environ.get('EVCT_REFRESH_INTERVAL', '10'))

def get_addon_config():
    """
    Get the current add-on configuration from the environment
    
    Returns:
        Dictionary with the add-on configuration
    """
    return {
        "use_guest_mode": DEFAULT_GUEST_MODE,
        "guest_password": DEFAULT_GUEST_PASSWORD,
        "background_refresh_interval": DEFAULT_REFRESH_INTERVAL
    }

def init_addon():
    """
    Initialize the add-on environment
    
    Returns:
        Boolean indicating if initialization was successful
    """
    try:
        # Ensure data directory exists
        data_dir = Path(HA_DATA_DIR)
        data_dir.mkdir(exist_ok=True)
        
        # Log status
        config = get_addon_config()
        logger.info(f"EV Charging Tracker add-on initialized with config: {json.dumps(config)}")
        
        # Create .streamlit directory if needed to ensure configuration
        streamlit_dir = Path('.streamlit')
        streamlit_dir.mkdir(exist_ok=True)
        
        # Create Streamlit config if it doesn't exist
        streamlit_config = streamlit_dir / 'config.toml'
        if not streamlit_config.exists():
            with open(streamlit_config, 'w') as f:
                f.write("""
[server]
headless = true
enableCORS = false
enableXsrfProtection = false
address = "0.0.0.0"
port = 5000

[browser]
gatherUsageStats = false
                """)
                
        return True
    except Exception as e:
        logger.error(f"Failed to initialize add-on: {e}")
        return False

def log_addon_info(message):
    """
    Log information to the add-on log
    
    Args:
        message: Message to log
    """
    logger.info(message)

def log_addon_error(message):
    """
    Log error to the add-on log
    
    Args:
        message: Error message to log
    """
    logger.error(message)

def get_data_path():
    """
    Get the path to the data directory
    
    Returns:
        Path object for the data directory
    """
    return Path(HA_DATA_DIR)

def setup_environment():
    """
    Setup the environment for the add-on
    
    This function should be called during application startup
    to configure the application for the Home Assistant environment.
    """
    # Initialize the add-on
    if not init_addon():
        logger.error("Failed to initialize add-on environment")
        return False
        
    # Log startup
    logger.info("EV Charging Tracker add-on starting up")
    
    # Set default values as environment variables for the rest of the application
    os.environ['GUEST_MODE_ENABLED'] = str(DEFAULT_GUEST_MODE).lower()
    os.environ['GUEST_PASSWORD'] = DEFAULT_GUEST_PASSWORD
    os.environ['BACKGROUND_REFRESH_INTERVAL'] = str(DEFAULT_REFRESH_INTERVAL)
    
    return True