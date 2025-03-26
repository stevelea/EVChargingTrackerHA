import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import hashlib

# Define the file path for storing data
DATA_DIR = "data"
CHARGING_DATA_FILE = os.path.join(DATA_DIR, "charging_data.json")

def ensure_data_directory():
    """
    Ensure the data directory exists
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def generate_record_id(record):
    """
    Generate a unique ID for a charging record based on its content
    
    Args:
        record: Dictionary containing charging data
        
    Returns:
        A string hash that uniquely identifies the record
    """
    # Create a string containing the key identifying fields
    id_fields = []
    
    # Date - convert to string if it's a datetime
    if record.get('date'):
        if isinstance(record['date'], datetime):
            id_fields.append(record['date'].strftime('%Y-%m-%d'))
        else:
            id_fields.append(str(record['date']))
    
    # Add other identifying fields
    for field in ['provider', 'location', 'total_kwh', 'total_cost']:
        if record.get(field):
            id_fields.append(str(record[field]))
    
    # Include source if available
    if record.get('source'):
        id_fields.append(str(record['source']))
    
    # If we have email_id or pdf_filename, use that too
    if record.get('email_id'):
        id_fields.append(str(record['email_id']))
    elif record.get('pdf_filename'):
        id_fields.append(str(record['pdf_filename']))
    
    # Create a hash from these fields
    record_str = '|'.join(id_fields)
    return hashlib.md5(record_str.encode('utf-8')).hexdigest()

def save_charging_data(data_list):
    """
    Save charging data to persistent storage
    
    Args:
        data_list: List of dictionaries containing charging data
    """
    ensure_data_directory()
    
    # Convert any datetime objects to strings
    serializable_data = []
    for record in data_list:
        # Create a copy so we don't modify the original
        record_copy = record.copy()
        
        # Convert date to string if it's a datetime
        if 'date' in record_copy and isinstance(record_copy['date'], datetime):
            record_copy['date'] = record_copy['date'].isoformat()
        
        # Convert time to string if it's a time object
        if 'time' in record_copy and hasattr(record_copy['time'], 'strftime'):
            record_copy['time'] = record_copy['time'].strftime('%H:%M:%S')
        
        # Generate record ID if not present
        if 'id' not in record_copy:
            record_copy['id'] = generate_record_id(record)
            
        serializable_data.append(record_copy)
    
    # Write to file
    with open(CHARGING_DATA_FILE, 'w') as f:
        json.dump(serializable_data, f, indent=2)

def load_charging_data():
    """
    Load charging data from persistent storage
    
    Returns:
        List of dictionaries containing charging data, or empty list if none found
    """
    ensure_data_directory()
    
    if not os.path.exists(CHARGING_DATA_FILE):
        return []
    
    try:
        with open(CHARGING_DATA_FILE, 'r') as f:
            data = json.load(f)
            
        # Convert string dates back to datetime objects
        for record in data:
            if 'date' in record and isinstance(record['date'], str):
                try:
                    record['date'] = datetime.fromisoformat(record['date'])
                except ValueError:
                    # If conversion fails, leave as string
                    pass
        
        return data
    except Exception as e:
        st.error(f"Error loading charging data: {str(e)}")
        return []

def merge_charging_data(existing_data, new_data):
    """
    Merge new charging data with existing data, avoiding duplicates
    
    Args:
        existing_data: List of existing charging data records
        new_data: List of new charging data records to merge
        
    Returns:
        Combined list of charging data with duplicates removed
    """
    # Build lookup of existing record IDs
    existing_ids = set()
    for record in existing_data:
        # Generate ID if not present
        if 'id' not in record:
            record['id'] = generate_record_id(record)
        existing_ids.add(record['id'])
    
    # Add new records if they don't already exist
    for record in new_data:
        # Generate ID if not present
        if 'id' not in record:
            record['id'] = generate_record_id(record)
            
        # Check if this record already exists
        if record['id'] not in existing_ids:
            existing_data.append(record)
            existing_ids.add(record['id'])
    
    return existing_data

def convert_to_dataframe(charging_data):
    """
    Convert charging data to a pandas DataFrame
    
    Args:
        charging_data: List of charging data dictionaries
        
    Returns:
        Pandas DataFrame with charging data
    """
    return pd.DataFrame(charging_data)

def filter_data_by_date_range(data, start_date, end_date):
    """
    Filter charging data by date range
    
    Args:
        data: DataFrame or list of dictionaries with charging data
        start_date: Start date for filtering
        end_date: End date for filtering
        
    Returns:
        Filtered data containing only records within the date range
    """
    if isinstance(data, pd.DataFrame):
        # If data is already a DataFrame
        if 'date' in data.columns:
            # Ensure date column is datetime type
            data['date'] = pd.to_datetime(data['date'], errors='coerce')
            
            # Filter by date range
            mask = (data['date'] >= start_date) & (data['date'] <= end_date)
            return data[mask]
        else:
            return data
    else:
        # If data is a list of dictionaries
        filtered_data = []
        for record in data:
            if 'date' in record:
                record_date = record['date']
                # Convert to datetime if it's a string
                if isinstance(record_date, str):
                    try:
                        record_date = datetime.fromisoformat(record_date)
                    except ValueError:
                        # Skip this record if date can't be parsed
                        continue
                
                # Check if date is within range
                if start_date <= record_date <= end_date:
                    filtered_data.append(record)
        
        return filtered_data

def delete_charging_data():
    """
    Delete all stored charging data
    """
    ensure_data_directory()
    
    if os.path.exists(CHARGING_DATA_FILE):
        os.remove(CHARGING_DATA_FILE)
        return True
    return False