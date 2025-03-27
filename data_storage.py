import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import hashlib

# Define the file path for storing data
DATA_DIR = "data"

def get_user_data_file(email_address=None):
    """
    Get the data file path for a specific user, or the default path if no user is specified
    
    Args:
        email_address: User's email address, or None for the default file
        
    Returns:
        Path to the user-specific charging data file
    """
    if email_address:
        # Create a safe filename from the email address
        safe_email = email_address.replace("@", "_at_").replace(".", "_dot_")
        return os.path.join(DATA_DIR, f"charging_data_{safe_email}.json")
    else:
        # Default file for backward compatibility
        return os.path.join(DATA_DIR, "charging_data.json")

# Default file path (for backward compatibility)
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
            id_fields.append(record['date'].strftime('%Y-%m-%d %H:%M:%S'))
        else:
            id_fields.append(str(record['date']))
    
    # For EVCC data, include time field if available to make it more unique
    if record.get('source') == 'EVCC CSV' and record.get('time'):
        id_fields.append(str(record['time']))
    
    # Add identifying fields - for EVCC use all numeric fields to ensure uniqueness
    if record.get('source') == 'EVCC CSV':
        for field in ['provider', 'location', 'total_kwh', 'duration', 'vehicle', 'cost_per_kwh', 'total_cost']:
            if record.get(field):
                id_fields.append(str(record[field]))
    else:
        # For other sources, use standard fields
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
    
    # For EVCC, also include finished timestamp if available for more uniqueness
    if record.get('source') == 'EVCC CSV' and record.get('end_date'):
        id_fields.append(str(record['end_date']))
        
    # Create a hash from these fields
    record_str = '|'.join(id_fields)
    return hashlib.md5(record_str.encode('utf-8')).hexdigest()

def save_charging_data(data_list, email_address=None):
    """
    Save charging data to persistent storage
    
    Args:
        data_list: List of dictionaries containing charging data
        email_address: Optional email address to save data for a specific user
    """
    ensure_data_directory()
    
    # Get the appropriate file path for this user
    file_path = get_user_data_file(email_address)
    
    # Convert any datetime objects to strings
    serializable_data = []
    for record in data_list:
        # Create a copy so we don't modify the original
        record_copy = record.copy()
        
        # Convert date to string if it's a datetime or date object
        if 'date' in record_copy:
            # Check for datetime.date or datetime.datetime types
            if isinstance(record_copy['date'], datetime):
                record_copy['date'] = record_copy['date'].isoformat()
            elif hasattr(record_copy['date'], 'isoformat'):  # covers both date and datetime
                record_copy['date'] = record_copy['date'].isoformat()
            elif not isinstance(record_copy['date'], str):
                # Last resort, convert to string
                record_copy['date'] = str(record_copy['date'])
        
        # Convert time to string if it's a time object
        if 'time' in record_copy and hasattr(record_copy['time'], 'strftime'):
            record_copy['time'] = record_copy['time'].strftime('%H:%M:%S')
        
        # Also handle other non-serializable objects 
        for key, value in record_copy.items():
            if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                # Convert to string for any other non-serializable types
                record_copy[key] = str(value)
        
        # Generate record ID if not present
        if 'id' not in record_copy:
            record_copy['id'] = generate_record_id(record)
            
        serializable_data.append(record_copy)
    
    # Write to file using a custom JSON encoder for any remaining datetime objects
    with open(file_path, 'w') as f:
        json.dump(serializable_data, f, indent=2, default=str)

def load_charging_data(email_address=None):
    """
    Load charging data from persistent storage
    
    Args:
        email_address: Optional email address to load data for a specific user
    
    Returns:
        List of dictionaries containing charging data, or empty list if none found
    """
    ensure_data_directory()
    
    # Get the appropriate file path for this user
    file_path = get_user_data_file(email_address)
    
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Convert string dates back to datetime objects
        for record in data:
            if 'date' in record and isinstance(record['date'], str):
                # Try different date formats for parsing
                date_formats = [
                    # ISO format with various separators
                    '%Y-%m-%dT%H:%M:%S',      # ISO format with time
                    '%Y-%m-%dT%H:%M:%S.%f',   # ISO format with milliseconds
                    '%Y-%m-%d',               # ISO date only
                    
                    # Other common formats
                    '%m/%d/%Y',               # US format
                    '%d/%m/%Y',               # UK/AU format
                    '%B %d, %Y',              # Month name format
                    '%d-%m-%Y',               # Dash-separated format
                    '%d-%m-%y',               # Two-digit year format
                ]
                
                parsed_date = None
                for fmt in date_formats:
                    try:
                        if 'T' in record['date'] and 'T' not in fmt:
                            # Skip non-ISO formats for ISO strings
                            continue
                        
                        # For ISO datetime format, try parsing just with fromisoformat
                        if fmt == '%Y-%m-%dT%H:%M:%S' or fmt == '%Y-%m-%dT%H:%M:%S.%f':
                            try:
                                parsed_date = datetime.fromisoformat(record['date'])
                                break
                            except ValueError:
                                continue
                        
                        # Otherwise use strptime
                        parsed_date = datetime.strptime(record['date'], fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_date:
                    record['date'] = parsed_date
                # If parsing fails, leave as string - don't discard the data
        
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
        
        # Function to parse date strings in multiple formats
        def parse_date_string(date_str):
            # Try different date formats for parsing
            date_formats = [
                # ISO format with various separators
                '%Y-%m-%dT%H:%M:%S',      # ISO format with time
                '%Y-%m-%dT%H:%M:%S.%f',   # ISO format with milliseconds
                '%Y-%m-%d',               # ISO date only
                
                # Other common formats
                '%m/%d/%Y',               # US format
                '%d/%m/%Y',               # UK/AU format
                '%B %d, %Y',              # Month name format
                '%d-%m-%Y',               # Dash-separated format
                '%d-%m-%y',               # Two-digit year format
            ]
            
            # First try fromisoformat for ISO strings
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                pass
                
            # Then try other formats
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
                    
            # Return None if parsing fails
            return None
            
        for record in data:
            if 'date' in record:
                record_date = record['date']
                
                # Convert to datetime if it's a string
                if isinstance(record_date, str):
                    parsed_date = parse_date_string(record_date)
                    if parsed_date is None:
                        # Skip this record if date can't be parsed
                        continue
                    record_date = parsed_date
                
                # Handle date type
                if hasattr(record_date, 'date') and callable(getattr(record_date, 'date')):
                    # If it's a datetime, get just the date part for comparison
                    record_date = record_date.date()
                    
                    # Convert start_date and end_date to date objects if they're datetimes
                    start_date_obj = start_date.date() if hasattr(start_date, 'date') else start_date
                    end_date_obj = end_date.date() if hasattr(end_date, 'date') else end_date
                    
                    # Check if date is within range
                    if start_date_obj <= record_date <= end_date_obj:
                        filtered_data.append(record)
                else:
                    # If it's already a date or another type
                    try:
                        if start_date <= record_date <= end_date:
                            filtered_data.append(record)
                    except TypeError:
                        # If comparison fails, try to compare strings
                        continue
        
        return filtered_data

def delete_charging_data(email_address=None):
    """
    Delete all stored charging data for a specific user or the default data
    
    Args:
        email_address: Optional email address to delete data for a specific user
    """
    ensure_data_directory()
    
    # Get the appropriate file path for this user
    file_path = get_user_data_file(email_address)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def delete_selected_records(record_ids, email_address=None):
    """
    Delete selected records by their IDs
    
    Args:
        record_ids: List of record IDs to delete
        email_address: Optional email address to delete data for a specific user
        
    Returns:
        Tuple of (success, count) indicating if operation succeeded and how many records were deleted
    """
    ensure_data_directory()
    
    # Get the appropriate file path for this user
    file_path = get_user_data_file(email_address)
    
    if not os.path.exists(file_path):
        return False, 0
    
    try:
        # Load existing data
        existing_data = load_charging_data(email_address)
        
        # Create a set of IDs to delete for faster lookup
        ids_to_delete = set(record_ids)
        
        # Filter out records with matching IDs
        new_data = [record for record in existing_data if record.get('id') not in ids_to_delete]
        
        # Calculate how many records were deleted
        records_deleted = len(existing_data) - len(new_data)
        
        # Save the updated data
        save_charging_data(new_data, email_address)
        
        return True, records_deleted
    except Exception as e:
        st.error(f"Error deleting selected records: {str(e)}")
        return False, 0

def filter_records_by_criteria(criteria, email_address=None):
    """
    Filter records by multiple criteria
    
    Args:
        criteria: Dictionary of field-value pairs to filter on
        email_address: Optional email address to filter data for a specific user
        
    Returns:
        List of records matching all criteria
    """
    data = load_charging_data(email_address)
    
    if not data:
        return []
    
    filtered_data = data.copy()
    
    # Apply each criteria as a filter
    for field, value in criteria.items():
        if field == 'date_range':
            # Special case for date range
            start_date, end_date = value
            filtered_data = filter_data_by_date_range(filtered_data, start_date, end_date)
        elif field == 'provider':
            # Filter by provider
            if value != "All":  # Skip if "All" is selected
                filtered_data = [record for record in filtered_data if record.get('provider') == value]
        elif field == 'location':
            # Filter by location (partial match)
            filtered_data = [record for record in filtered_data 
                            if record.get('location') and value.lower() in record.get('location', '').lower()]
        elif field == 'source':
            # Filter by data source
            filtered_data = [record for record in filtered_data if record.get('source') == value]
        elif field == 'min_cost':
            # Filter by minimum cost
            filtered_data = [record for record in filtered_data 
                            if record.get('total_cost') is not None and float(record.get('total_cost', 0)) >= float(value)]
        elif field == 'max_cost':
            # Filter by maximum cost
            filtered_data = [record for record in filtered_data 
                            if record.get('total_cost') is not None and float(record.get('total_cost', 0)) <= float(value)]
        elif field == 'min_kwh':
            # Filter by minimum kWh
            filtered_data = [record for record in filtered_data 
                            if record.get('total_kwh') is not None and float(record.get('total_kwh', 0)) >= float(value)]
        elif field == 'max_kwh':
            # Filter by maximum kWh
            filtered_data = [record for record in filtered_data 
                            if record.get('total_kwh') is not None and float(record.get('total_kwh', 0)) <= float(value)]
    
    return filtered_data