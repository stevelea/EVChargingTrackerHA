"""
Home Assistant-specific data persistence module for EV Charging Tracker.
This provides methods for storing data within the Home Assistant add-on environment.
"""

import json
import os
import datetime
from pathlib import Path

# We don't actually need pandas in this module
# All DataFrame conversions are handled in other modules
# Let's remove the import to avoid dependency issues
pd = None

# Default path for data storage in Home Assistant add-on
HA_DATA_DIR = os.environ.get('EVCT_DATA_DIR', '/data')

def get_data_dir():
    """
    Get the data directory for the Home Assistant add-on
    
    Returns:
        Path object for the data directory
    """
    data_dir = Path(HA_DATA_DIR)
    data_dir.mkdir(exist_ok=True)
    return data_dir

def get_user_data_file(email_address=None):
    """
    Get the path to the user data file
    
    Args:
        email_address: User's email address, or None for the default file
        
    Returns:
        Path object for the user data file
    """
    data_dir = get_data_dir()
    
    if email_address:
        # Create a safe filename from the email address
        filename = email_address.replace('@', '_at_').replace('.', '_dot_') + '.json'
    else:
        filename = 'charging_data.json'
        
    return data_dir / filename

def save_charging_data(data_list, email_address=None):
    """
    Save charging data to persistent storage
    
    Args:
        data_list: List of dictionaries containing charging data
        email_address: Optional email address to save data for a specific user
    """
    # Convert datetime objects to strings for JSON serialization
    serializable_data = []
    for record in data_list:
        record_copy = record.copy()
        for key, value in record_copy.items():
            if isinstance(value, (datetime.datetime, datetime.date)):
                record_copy[key] = value.isoformat()
        serializable_data.append(record_copy)
    
    # Save to file
    file_path = get_user_data_file(email_address)
    with open(file_path, 'w') as f:
        json.dump(serializable_data, f, indent=2)

def load_charging_data(email_address=None):
    """
    Load charging data from persistent storage
    
    Args:
        email_address: Optional email address to load data for a specific user
    
    Returns:
        List of dictionaries containing charging data, or empty list if none found
    """
    file_path = get_user_data_file(email_address)
    
    if not file_path.exists():
        return []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Convert string dates back to datetime objects
        for record in data:
            for date_field in ['date', 'start_time', 'end_time']:
                if date_field in record and isinstance(record[date_field], str):
                    try:
                        record[date_field] = datetime.datetime.fromisoformat(record[date_field])
                    except ValueError:
                        # If parsing fails, leave as string
                        pass
                        
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return []

def delete_charging_data(email_address=None):
    """
    Delete all stored charging data for a specific user or the default data
    
    Args:
        email_address: Optional email address to delete data for a specific user
    """
    file_path = get_user_data_file(email_address)
    
    if file_path.exists():
        file_path.unlink()

def save_credentials(email, password):
    """
    Save user credentials securely
    
    Args:
        email: User's email address
        password: User's password or app password
        
    Returns:
        Boolean indicating if save was successful
    """
    try:
        credentials_file = get_data_dir() / 'credentials.json'
        with open(credentials_file, 'w') as f:
            json.dump({'email': email, 'password': password}, f)
        return True
    except Exception as e:
        print(f"Error saving credentials: {e}")
        return False

def load_credentials():
    """
    Load user credentials
    
    Returns:
        Tuple of (email, password) or (None, None) if not found
    """
    try:
        credentials_file = get_data_dir() / 'credentials.json'
        if not credentials_file.exists():
            return None, None
            
        with open(credentials_file, 'r') as f:
            creds = json.load(f)
            return creds.get('email'), creds.get('password')
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None, None