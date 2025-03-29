"""
Entry point for the Home Assistant add-on.
This script initializes the environment and starts the combined app.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ha_addon")

# Import the HA add-on adapter
try:
    from ha_addon_adapter import setup_environment, log_addon_info, log_addon_error
    
    # Set up the Home Assistant environment
    logger.info("Setting up Home Assistant add-on environment...")
    if not setup_environment():
        logger.error("Failed to set up Home Assistant environment. Exiting.")
        sys.exit(1)
        
    # Log successful initialization
    logger.info("Home Assistant add-on environment initialized successfully.")
    
    # Import and run the proxy app (which combines Streamlit and API)
    logger.info("Starting the combined EV Charging Tracker application...")
    
    # Change directory to ensure relative imports work
    os.chdir(Path(__file__).parent)
    
    # Check if run_proxy.py exists
    if not Path("run_proxy.py").exists():
        log_addon_error("run_proxy.py not found. Checking for run_combined.py...")
        
        if Path("run_combined.py").exists():
            log_addon_info("Using run_combined.py instead.")
            import run_combined
        else:
            log_addon_error("Neither run_proxy.py nor run_combined.py found. Cannot start application.")
            sys.exit(1)
    else:
        # Import and run the proxy app
        import run_proxy
        
except Exception as e:
    logger.error(f"Error starting Home Assistant add-on: {e}")
    sys.exit(1)