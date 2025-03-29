"""
Main entry point for Azure App Service.
This file is used by Azure App Service to start the application.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to sys.path to import modules from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Apply Azure-specific patches for storage
try:
    from azure_data_storage_patch import apply_azure_storage_patch
    apply_azure_storage_patch()
    logger.info("Azure storage patches applied")
except Exception as e:
    logger.error(f"Failed to apply Azure storage patches: {e}")

# Import the application from run_proxy_azure.py
from run_proxy_azure import app

# Azure Web Apps expects an app named 'application'
application = app

if __name__ == "__main__":
    # This block is executed when running locally
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting application on port {port}")
    application.run(host="0.0.0.0", port=port)