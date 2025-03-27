from datetime import datetime, timedelta
import pandas as pd
import io
import re
import os
import json

# Paths for saving credentials
CREDENTIALS_FILE = "credentials.json"

def save_credentials(email_address):
    """
    Save email address to a file for future use
    
    Args:
        email_address: User's Gmail address to save
    """
    try:
        data = {"email_address": email_address}
        
        # Save to file
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(data, f)
            
        return True
    except Exception as e:
        print(f"Error saving credentials: {str(e)}")
        return False

def load_credentials():
    """
    Load saved email address from file
    
    Returns:
        Dictionary with email_address key or None if not found
    """
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Error loading credentials: {str(e)}")
        return None

def get_date_range(start_date, end_date):
    """
    Format a date range for Gmail search
    This function now supports both Gmail API and IMAP search formats
    
    Args:
        start_date: Start date as datetime object
        end_date: End date as datetime object
        
    Returns:
        Search query string for date range
    """
    # IMAP and Gmail API use slightly different formats,
    # but both understand this format
    start_str = start_date.strftime('%Y/%m/%d')
    end_str = end_date.strftime('%Y/%m/%d')
    
    # Format that works for both IMAP and Gmail API
    return f"SINCE {start_str} BEFORE {end_str}"

def format_duration(seconds):
    """
    Format duration in seconds to a readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "1h 30m")
    """
    if seconds is None:
        return "Unknown"
    
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if hours > 0:
        return f"{int(hours)}h {int(minutes)}m"
    else:
        return f"{int(minutes)}m"

def parse_duration_str(duration_str):
    """
    Parse a duration string into seconds
    
    Args:
        duration_str: Duration string (e.g., "1h 30m", "45 minutes")
        
    Returns:
        Duration in seconds
    """
    if not duration_str:
        return None
    
    duration_str = duration_str.lower()
    total_seconds = 0
    
    # Extract hours
    hours_match = re.search(r'(\d+)\s*h', duration_str)
    if hours_match:
        hours = int(hours_match.group(1))
        total_seconds += hours * 3600
    
    # Extract minutes
    minutes_match = re.search(r'(\d+)\s*m', duration_str)
    if minutes_match:
        minutes = int(minutes_match.group(1))
        total_seconds += minutes * 60
    
    # Extract seconds
    seconds_match = re.search(r'(\d+)\s*s', duration_str)
    if seconds_match:
        seconds = int(seconds_match.group(1))
        total_seconds += seconds
    
    # If no pattern matched, try to convert directly to minutes
    if total_seconds == 0:
        minutes_match = re.search(r'(\d+)\s*min', duration_str)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            total_seconds = minutes * 60
    
    return total_seconds if total_seconds > 0 else None

def export_data_as_csv(data):
    """
    Export charging data as CSV
    
    Args:
        data: DataFrame containing charging data
        
    Returns:
        CSV data as string
    """
    csv_buffer = io.StringIO()
    data.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    return csv_buffer.getvalue()

def get_plugshare_link(location, latitude=None, longitude=None):
    """
    Generate a PlugShare URL for a specific location
    
    Args:
        location: Name of the location
        latitude: Latitude coordinate (optional)
        longitude: Longitude coordinate (optional)
        
    Returns:
        URL to the PlugShare search for this location
    """
    import urllib.parse
    
    # If we have coordinates, use them for a more precise search
    if latitude is not None and longitude is not None:
        # PlugShare uses the format: https://www.plugshare.com/map#/location/latitude,longitude
        return f"https://www.plugshare.com/map#/location/{latitude},{longitude}"
    else:
        # Otherwise, use the location name for a general search
        encoded_location = urllib.parse.quote(location)
        return f"https://www.plugshare.com/map#/location?address={encoded_location}"

def calculate_statistics(data):
    """
    Calculate summary statistics from charging data
    
    Args:
        data: DataFrame containing charging data
        
    Returns:
        Dictionary of statistics
    """
    stats = {}
    
    # Basic counts
    stats['total_sessions'] = len(data)
    stats['unique_locations'] = data['location'].nunique()
    
    # Energy statistics
    # Handle both energy_kwh and total_kwh column names for backward compatibility
    energy_col = 'energy_kwh' if 'energy_kwh' in data.columns else 'total_kwh'
    stats['total_kwh'] = data[energy_col].sum()
    stats['avg_kwh_per_session'] = data[energy_col].mean()
    stats['max_kwh_session'] = data[energy_col].max()
    
    # Cost statistics
    cost_col = 'cost' if 'cost' in data.columns else 'total_cost'  
    stats['total_cost'] = data[cost_col].sum()
    stats['avg_cost_per_session'] = data[cost_col].mean()
    stats['avg_cost_per_kwh'] = stats['total_cost'] / stats['total_kwh'] if stats['total_kwh'] > 0 else 0
    
    # Power statistics if available
    if 'peak_kw' in data.columns:
        stats['avg_peak_kw'] = data['peak_kw'].mean()
        stats['max_peak_kw'] = data['peak_kw'].max()
    else:
        stats['avg_peak_kw'] = 0
        stats['max_peak_kw'] = 0
    
    # Time statistics
    if 'date' in data.columns:
        stats['first_session'] = data['date'].min()
        stats['last_session'] = data['date'].max()
        stats['days_span'] = (stats['last_session'] - stats['first_session']).days
        
        # Monthly aggregates
        monthly_data = data.copy()
        monthly_data['month'] = monthly_data['date'].dt.to_period('M')
        
        # Use the same column names for aggregation
        monthly_agg = monthly_data.groupby('month').agg({
            cost_col: 'sum',
            energy_col: 'sum'
        })
        
        # Rename columns for consistency with the rest of the stats
        monthly_agg.columns = ['total_cost', 'total_kwh']
        
        stats['monthly_avg_cost'] = monthly_agg['total_cost'].mean()
        stats['monthly_avg_kwh'] = monthly_agg['total_kwh'].mean()
    
    return stats
