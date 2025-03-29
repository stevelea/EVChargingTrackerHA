"""
Background task handler for the EV Charging Tracker app.
This module provides functions for automated data refresh.
"""
import threading
import time
from datetime import datetime
import traceback

from gmail_api import GmailClient
from data_parser import parse_charging_emails
from data_storage import load_charging_data, save_charging_data, merge_charging_data
from utils import load_credentials

# Global variables to track background task state
_background_thread = None
_stop_background = False
_background_running = False
_last_refresh_time = None
_refresh_interval = 10  # Default interval in minutes

def refresh_data(email_address=None, password=None, search_terms=None):
    """
    Refresh charging data by retrieving new emails from Gmail
    
    Args:
        email_address: Gmail address to use (if None, will try to load from credentials)
        password: App password for Gmail (if None, will try to load from credentials)
        search_terms: Optional search terms for filtering emails
        
    Returns:
        Tuple of (success, message, count) indicating if refresh was successful,
        a message describing the outcome, and the count of new records found
    """
    global _last_refresh_time
    
    try:
        # If email or password not provided, try to load from credentials
        if not email_address or not password:
            credentials = load_credentials()
            if credentials and 'email_address' in credentials:
                email_address = credentials['email_address']
                
                if 'password' in credentials:
                    password = credentials['password']
                else:
                    return (False, "No password saved for automatic refresh", 0)
            else:
                return (False, "No credentials found for automatic refresh", 0)
        
        # Default search terms if none provided
        if not search_terms:
            search_terms = "EV charging receipt OR Ampol AmpCharge OR charging session"
        
        # Initialize Gmail client and authenticate
        client = GmailClient()
        if not client.authenticate(email_address, password):
            return (False, "Gmail authentication failed", 0)
        
        # Search for charging emails
        try:
            # Get charging emails from the last 30 days
            from datetime import datetime, timedelta
            
            # Calculate date range for the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Get date range string for the query
            date_range = utils.get_date_range(start_date, end_date)
            
            # Construct IMAP query with search terms and date range
            query = f"({search_terms}) {date_range}"
            
            # Get charging emails from the query
            charging_emails = client.get_emails(query=query, max_results=100)
            
            if not charging_emails:
                _last_refresh_time = datetime.now()
                return (True, "No new charging emails found", 0)
            
            # Parse the charging data from emails
            charging_data = parse_charging_emails(charging_emails)
            
            if not charging_data:
                _last_refresh_time = datetime.now()
                return (True, "No charging data could be extracted from emails", 0)
            
            # Get existing data
            existing_data = load_charging_data(email_address)
            
            # Merge with existing data (avoiding duplicates)
            merged_data = merge_charging_data(existing_data, charging_data)
            
            # Save the merged data
            save_charging_data(merged_data, email_address)
            
            # Calculate how many new records were added
            new_records_count = len(merged_data) - len(existing_data) if existing_data else len(merged_data)
            
            # Update last refresh time
            _last_refresh_time = datetime.now()
            
            return (True, "Successfully refreshed charging data", new_records_count)
        
        except Exception as e:
            error_msg = f"Error searching or parsing emails: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return (False, error_msg, 0)
    
    except Exception as e:
        error_msg = f"Error in refresh_data: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return (False, error_msg, 0)

def background_refresh_task(interval_minutes=10):
    """
    Background task that refreshes data at regular intervals
    
    Args:
        interval_minutes: Minutes between refresh attempts
    """
    global _stop_background, _background_running, _refresh_interval
    
    _refresh_interval = interval_minutes
    _background_running = True
    
    print(f"Starting background refresh task with {interval_minutes} minute interval")
    
    try:
        while not _stop_background:
            try:
                # Load credentials
                credentials = load_credentials()
                if credentials and 'email_address' in credentials and 'password' in credentials:
                    # Perform refresh
                    print(f"Background refresh at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    refresh_data(
                        credentials['email_address'], 
                        credentials['password']
                    )
                else:
                    print("No valid credentials found for background refresh")
            except Exception as e:
                print(f"Error in background refresh: {str(e)}")
                print(traceback.format_exc())
            
            # Wait for the next interval
            # We check _stop_background every second to allow for faster shutdown
            for _ in range(interval_minutes * 60):
                if _stop_background:
                    break
                time.sleep(1)
    finally:
        _background_running = False
        print("Background refresh task stopped")

def start_background_refresh(interval_minutes=10):
    """
    Start the background refresh task if not already running
    
    Args:
        interval_minutes: Minutes between refresh attempts
        
    Returns:
        Boolean indicating if task was started
    """
    global _background_thread, _stop_background, _background_running
    
    # Don't start if already running
    if _background_running and _background_thread and _background_thread.is_alive():
        return False
    
    # Reset the stop flag
    _stop_background = False
    
    # Create and start the thread
    _background_thread = threading.Thread(
        target=background_refresh_task,
        args=(interval_minutes,),
        daemon=True  # Make it a daemon so it exits when the main program exits
    )
    _background_thread.start()
    
    return True

def stop_background_refresh():
    """
    Stop the background refresh task if running
    
    Returns:
        Boolean indicating if task was stopped
    """
    global _background_thread, _stop_background, _background_running
    
    # If not running, return False
    if not _background_running or not _background_thread or not _background_thread.is_alive():
        return False
    
    # Set the stop flag
    _stop_background = True
    
    # Wait for the thread to exit (with timeout)
    _background_thread.join(timeout=5)
    
    # Reset the thread variable
    _background_thread = None
    
    return not _background_running  # Return True if successfully stopped

def get_background_status():
    """
    Get the status of the background refresh task
    
    Returns:
        Dictionary with status information
    """
    global _background_running, _last_refresh_time, _refresh_interval
    
    return {
        "running": _background_running,
        "last_refresh": _last_refresh_time.strftime('%Y-%m-%d %H:%M:%S') if _last_refresh_time else None,
        "interval_minutes": _refresh_interval
    }