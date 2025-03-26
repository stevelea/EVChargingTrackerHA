from datetime import datetime, timedelta
import pandas as pd
import io

def get_date_range(start_date, end_date):
    """
    Format a date range for Gmail API query
    
    Args:
        start_date: Start date as datetime object
        end_date: End date as datetime object
        
    Returns:
        Gmail query string for date range
    """
    start_str = start_date.strftime('%Y/%m/%d')
    end_str = end_date.strftime('%Y/%m/%d')
    return f"after:{start_str} before:{end_str}"

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
    stats['total_kwh'] = data['total_kwh'].sum()
    stats['avg_kwh_per_session'] = data['total_kwh'].mean()
    stats['max_kwh_session'] = data['total_kwh'].max()
    
    # Cost statistics
    stats['total_cost'] = data['total_cost'].sum()
    stats['avg_cost_per_session'] = data['total_cost'].mean()
    stats['avg_cost_per_kwh'] = stats['total_cost'] / stats['total_kwh'] if stats['total_kwh'] > 0 else 0
    
    # Power statistics
    stats['avg_peak_kw'] = data['peak_kw'].mean()
    stats['max_peak_kw'] = data['peak_kw'].max()
    
    # Time statistics
    if 'date' in data.columns:
        stats['first_session'] = data['date'].min()
        stats['last_session'] = data['date'].max()
        stats['days_span'] = (stats['last_session'] - stats['first_session']).days
        
        # Monthly aggregates
        monthly_data = data.copy()
        monthly_data['month'] = monthly_data['date'].dt.to_period('M')
        monthly_agg = monthly_data.groupby('month').agg({
            'total_cost': 'sum',
            'total_kwh': 'sum'
        })
        
        stats['monthly_avg_cost'] = monthly_agg['total_cost'].mean()
        stats['monthly_avg_kwh'] = monthly_agg['total_kwh'].mean()
    
    return stats
