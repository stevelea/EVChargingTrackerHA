"""
Patch module to override data_storage functions with Azure-specific versions.
This module should be imported in the run_proxy_azure.py or application.py file.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_azure_storage_patch():
    """
    Apply patches to use Azure storage instead of Replit DB
    """
    logger.info("Applying Azure storage patches...")
    
    # Check if we're running in Azure
    if "WEBSITE_HOSTNAME" in os.environ:
        logger.info("Running in Azure environment, applying storage patches")
        
        # Check if azure_storage module exists
        try:
            # Import the azure_storage module from the same directory
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from azure_storage import (
                get_azure_status,
                get_user_data_path,
                save_charging_data,
                load_charging_data,
                delete_charging_data
            )
            
            # Patch functions in data_storage module
            import data_storage
            
            # Backup original functions
            original_get_replit_status = data_storage.get_replit_status
            original_get_user_data_key = data_storage.get_user_data_key
            original_save_charging_data = data_storage.save_charging_data
            original_load_charging_data = data_storage.load_charging_data
            original_delete_charging_data = data_storage.delete_charging_data
            
            # Replace with Azure functions
            data_storage.get_replit_status = get_azure_status
            data_storage.get_user_data_key = get_user_data_path
            data_storage.save_charging_data = save_charging_data
            data_storage.load_charging_data = load_charging_data
            data_storage.delete_charging_data = delete_charging_data
            
            logger.info("Successfully patched data_storage module with Azure storage functions")
            return True
        except ImportError as e:
            logger.error(f"Failed to import azure_storage module: {e}")
        except Exception as e:
            logger.error(f"Error applying Azure storage patches: {e}")
    else:
        logger.info("Not running in Azure environment, skipping storage patches")
    
    return False