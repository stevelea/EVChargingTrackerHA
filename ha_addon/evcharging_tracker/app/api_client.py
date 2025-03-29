"""
API client library for the EV Charging Data API.
This module provides a Python client for interacting with the API.
"""

import requests
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union


class EVChargingAPIClient:
    """
    Client for the EV Charging Data API.
    
    This client provides methods to interact with the API endpoints
    for retrieving and querying charging data.
    """
    
    def __init__(self, base_url: str, api_key: str = None):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API (e.g., 'http://localhost:5001')
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        # Set default headers
        if api_key:
            self.session.headers.update({'X-API-Key': api_key})
    
    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make a GET request to the API.
        
        Args:
            endpoint: API endpoint (without leading slash)
            params: Query parameters
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            requests.RequestException: If the request fails
            ValueError: If the response is not valid JSON
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to params if not in headers
        if self.api_key and 'X-API-Key' not in self.session.headers:
            params = params or {}
            params['api_key'] = self.api_key
        
        response = self.session.get(url, params=params)
        response.raise_for_status()  # Raise exception for 4XX/5XX status codes
        
        return response.json()
    
    def health_check(self) -> Dict:
        """
        Check if the API is running.
        
        Returns:
            Dictionary with API status information
        """
        return self._get('api/health')
    
    def get_charging_data(
        self, 
        email: str = None, 
        start_date: Union[str, date, datetime] = None,
        end_date: Union[str, date, datetime] = None,
        provider: str = None,
        location: str = None
    ) -> Dict:
        """
        Get charging data with optional filtering.
        
        Args:
            email: User email to retrieve data for
            start_date: Filter by date range (start)
            end_date: Filter by date range (end)
            provider: Filter by charging provider
            location: Filter by charging location
            
        Returns:
            Dictionary with charging data records
        """
        params = {}
        
        # Add parameters if they're provided
        if email:
            params['email'] = email
        
        # Format dates if needed
        if start_date:
            if isinstance(start_date, (date, datetime)):
                params['start_date'] = start_date.strftime('%Y-%m-%d')
            else:
                params['start_date'] = start_date
                
        if end_date:
            if isinstance(end_date, (date, datetime)):
                params['end_date'] = end_date.strftime('%Y-%m-%d')
            else:
                params['end_date'] = end_date
        
        if provider:
            params['provider'] = provider
            
        if location:
            params['location'] = location
        
        return self._get('api/charging-data', params=params)
    
    def get_charging_record(self, record_id: str, email: str = None) -> Dict:
        """
        Get a specific charging record by ID.
        
        Args:
            record_id: ID of the charging record
            email: User email to retrieve data for
            
        Returns:
            Dictionary with the charging record details
        """
        params = {}
        if email:
            params['email'] = email
            
        return self._get(f'api/charging-data/{record_id}', params=params)
    
    def get_charging_summary(self, email: str = None) -> Dict:
        """
        Get a summary of charging data statistics.
        
        Args:
            email: User email to retrieve data for
            
        Returns:
            Dictionary with summary statistics
        """
        params = {}
        if email:
            params['email'] = email
            
        return self._get('api/summary', params=params)
    
    def get_users(self, admin_key: str) -> Dict:
        """
        Get list of users with data in the system.
        
        Args:
            admin_key: Administrator key for authentication
            
        Returns:
            Dictionary with list of users
            
        Note:
            This endpoint requires administrator access.
        """
        # Save original headers
        original_headers = self.session.headers.copy()
        
        try:
            # Add admin key to headers
            self.session.headers.update({'X-Admin-Key': admin_key})
            
            return self._get('api/users')
        finally:
            # Restore original headers
            self.session.headers = original_headers


# Example usage
if __name__ == "__main__":
    # Create a client instance
    client = EVChargingAPIClient(
        base_url="http://localhost:8000",
        api_key="ev-charging-api-key"  # Default API key
    )
    
    try:
        # Check if the API is running
        health = client.health_check()
        print("API Status:", health)
        
        # Get charging data
        data = client.get_charging_data()
        print(f"Retrieved {data.get('count', 0)} charging records")
        
        # Get summary statistics
        summary = client.get_charging_summary()
        print("Summary:", json.dumps(summary, indent=2))
        
    except requests.RequestException as e:
        print(f"API request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")