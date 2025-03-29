"""
Azure Storage adapter for the EV Charging Tracker app.
This module provides functions to store and retrieve data using Azure Storage.
"""

import os
import json
import logging
from datetime import datetime

# Note: For Azure free tier, we'll use local file storage
# When upgrading to a paid tier, this can be changed to use Azure Blob Storage
# by uncommenting the code below and installing the azure-storage-blob package

# from azure.storage.blob import BlobServiceClient, ContentSettings

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure Storage settings
STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING', '')
CONTAINER_NAME = 'evchargingdata'
DATA_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def get_azure_status():
    """
    Return status of Azure Storage
    
    Returns:
        Dictionary with status information
    """
    # For free tier, we're using local file storage
    if not os.path.exists(DATA_DIRECTORY):
        os.makedirs(DATA_DIRECTORY)
        
    return {
        "status": "ok",
        "storage_type": "local_file",
        "data_directory": DATA_DIRECTORY
    }
    
    # When upgrading to a paid tier with Blob Storage:
    """
    try:
        if not STORAGE_CONNECTION_STRING:
            return {
                "status": "error",
                "message": "Azure Storage connection string not configured"
            }
            
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        
        # Get container client
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        
        # Try to create container if it doesn't exist
        if not container_client.exists():
            container_client.create_container()
            
        return {
            "status": "ok",
            "storage_type": "azure_blob",
            "container": CONTAINER_NAME
        }
    except Exception as e:
        logger.error(f"Azure Storage error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
    """


def get_user_data_path(email_address=None):
    """
    Get the path for storing user data in Azure Storage
    
    Args:
        email_address: User's email address, or None for the default path
        
    Returns:
        String path for the user's data in Azure Storage
    """
    if email_address:
        # Sanitize email address to use as a file name
        sanitized_email = email_address.replace('@', '_at_').replace('.', '_dot_')
        return os.path.join(DATA_DIRECTORY, f"charging_data_{sanitized_email}.json")
    else:
        return os.path.join(DATA_DIRECTORY, "charging_data_default.json")


def save_charging_data(data_list, email_address=None):
    """
    Save charging data to Azure Storage
    
    Args:
        data_list: List of dictionaries containing charging data
        email_address: Optional email address to save data for a specific user
    """
    # Prepare data for storage (serialize datetime objects)
    serializable_data = []
    for record in data_list:
        record_copy = record.copy()
        for key, value in record.items():
            if isinstance(value, datetime):
                record_copy[key] = value.isoformat()
        serializable_data.append(record_copy)
        
    # Save to file (for free tier)
    file_path = get_user_data_path(email_address)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(serializable_data, f)
    
    logger.info(f"Saved {len(serializable_data)} records to {file_path}")
    
    # When upgrading to a paid tier with Blob Storage:
    """
    try:
        # Convert data to JSON string
        json_data = json.dumps(serializable_data)
        
        # Get blob path
        blob_path = get_user_data_path(email_address)
        
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        
        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, 
            blob=blob_path
        )
        
        # Upload the data
        blob_client.upload_blob(
            json_data, 
            overwrite=True,
            content_settings=ContentSettings(content_type='application/json')
        )
        
        logger.info(f"Saved {len(serializable_data)} records to Azure blob: {blob_path}")
    except Exception as e:
        logger.error(f"Error saving data to Azure Storage: {str(e)}")
        # Fall back to file storage
        file_path = get_user_data_path(email_address)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(serializable_data, f)
        
        logger.info(f"Saved {len(serializable_data)} records to fallback file: {file_path}")
    """


def load_charging_data(email_address=None):
    """
    Load charging data from Azure Storage
    
    Args:
        email_address: Optional email address to load data for a specific user
    
    Returns:
        List of dictionaries containing charging data, or empty list if none found
    """
    # Load from file (for free tier)
    file_path = get_user_data_path(email_address)
    
    if not os.path.exists(file_path):
        logger.info(f"No data file found at {file_path}")
        return []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert date strings back to datetime objects
        for record in data:
            for key in ['date', 'start_time', 'end_time']:
                if key in record and record[key]:
                    try:
                        record[key] = datetime.fromisoformat(record[key])
                    except (ValueError, TypeError):
                        pass
        
        logger.info(f"Loaded {len(data)} records from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading data from file: {str(e)}")
        return []
    
    # When upgrading to a paid tier with Blob Storage:
    """
    try:
        # Get blob path
        blob_path = get_user_data_path(email_address)
        
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        
        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, 
            blob=blob_path
        )
        
        # Check if blob exists
        if not blob_client.exists():
            logger.info(f"No data found in Azure blob: {blob_path}")
            return []
        
        # Download the data
        download_stream = blob_client.download_blob()
        json_data = download_stream.readall()
        
        # Parse JSON
        data = json.loads(json_data)
        
        # Convert date strings back to datetime objects
        for record in data:
            for key in ['date', 'start_time', 'end_time']:
                if key in record and record[key]:
                    try:
                        record[key] = datetime.fromisoformat(record[key])
                    except (ValueError, TypeError):
                        pass
        
        logger.info(f"Loaded {len(data)} records from Azure blob: {blob_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading data from Azure Storage: {str(e)}")
        
        # Try fallback to file storage
        try:
            file_path = get_user_data_path(email_address)
            
            if not os.path.exists(file_path):
                logger.info(f"No fallback data file found at {file_path}")
                return []
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert date strings back to datetime objects
            for record in data:
                for key in ['date', 'start_time', 'end_time']:
                    if key in record and record[key]:
                        try:
                            record[key] = datetime.fromisoformat(record[key])
                        except (ValueError, TypeError):
                            pass
            
            logger.info(f"Loaded {len(data)} records from fallback file: {file_path}")
            return data
        except Exception as fallback_error:
            logger.error(f"Error loading data from fallback file: {str(fallback_error)}")
            return []
    """


def delete_charging_data(email_address=None):
    """
    Delete all stored charging data for a specific user or the default data
    
    Args:
        email_address: Optional email address to delete data for a specific user
    """
    # Delete from file (for free tier)
    file_path = get_user_data_path(email_address)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Deleted data file at {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting data file: {str(e)}")
            return False
    else:
        logger.info(f"No data file found at {file_path}")
        return False
    
    # When upgrading to a paid tier with Blob Storage:
    """
    try:
        # Get blob path
        blob_path = get_user_data_path(email_address)
        
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        
        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, 
            blob=blob_path
        )
        
        # Check if blob exists
        if blob_client.exists():
            # Delete the blob
            blob_client.delete_blob()
            logger.info(f"Deleted data from Azure blob: {blob_path}")
            
            # Also delete local file if it exists
            file_path = get_user_data_path(email_address)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted fallback data file at {file_path}")
                
            return True
        else:
            logger.info(f"No data found in Azure blob: {blob_path}")
            
            # Check for local file
            file_path = get_user_data_path(email_address)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted fallback data file at {file_path}")
                return True
                
            return False
    except Exception as e:
        logger.error(f"Error deleting data from Azure Storage: {str(e)}")
        return False
    """