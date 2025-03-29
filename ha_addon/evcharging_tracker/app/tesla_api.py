import os
import requests
import time
import json
import streamlit as st
from datetime import datetime, timedelta

class TeslaApiClient:
    """
    Client for interacting with the Tesla API to retrieve vehicle and charging data.
    This implementation focuses on retrieving charging data for non-Tesla vehicles
    that use Tesla Superchargers or other Tesla charging networks.
    """
    
    # Tesla API endpoints
    BASE_URL = "https://owner-api.teslamotors.com/api/1"
    AUTH_URL = "https://auth.tesla.com/oauth2/v3/token"
    
    def __init__(self):
        """Initialize the Tesla API client"""
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
        self.vehicle_id = None
        self.vehicles = []
        
        # Try to load saved tokens
        self._load_tokens()
    
    def _load_tokens(self):
        """Load authentication tokens from secure storage if available"""
        try:
            if os.path.exists('.tesla_tokens.json'):
                with open('.tesla_tokens.json', 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get('access_token')
                    self.refresh_token = tokens.get('refresh_token')
                    self.token_expires_at = tokens.get('expires_at', 0)
        except Exception as e:
            st.warning(f"Error loading Tesla tokens: {str(e)}")
    
    def _save_tokens(self):
        """Save authentication tokens to secure storage"""
        try:
            tokens = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_at': self.token_expires_at
            }
            with open('.tesla_tokens.json', 'w') as f:
                json.dump(tokens, f)
        except Exception as e:
            st.warning(f"Error saving Tesla tokens: {str(e)}")
    
    def authenticate(self, email, password):
        """
        Authenticate with Tesla API using email and password.
        
        Args:
            email (str): Tesla account email
            password (str): Tesla account password
            
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            # For security reasons, implement OAuth authentication flow
            # This is a placeholder - actual implementation would use Tesla's OAuth flow
            st.warning("Tesla API authentication requires OAuth implementation")
            st.info("Please provide your Tesla API access token and refresh token directly")
            return False
        except Exception as e:
            st.error(f"Tesla authentication failed: {str(e)}")
            return False
    
    def set_tokens(self, access_token, refresh_token, expires_in=3600):
        """
        Set authentication tokens directly.
        
        Args:
            access_token (str): Tesla API access token
            refresh_token (str): Tesla API refresh token
            expires_in (int): Token expiration time in seconds
            
        Returns:
            bool: True if tokens were set successfully
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = time.time() + expires_in
        self._save_tokens()
        return True
    
    def _refresh_access_token(self):
        """Refresh the access token using the refresh token"""
        if not self.refresh_token:
            return False
            
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "grant_type": "refresh_token",
                "client_id": "ownerapi",
                "refresh_token": self.refresh_token,
                "scope": "openid email offline_access"
            }
            
            response = requests.post(self.AUTH_URL, headers=headers, json=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.refresh_token = token_data.get("refresh_token", self.refresh_token)
                self.token_expires_at = time.time() + token_data.get("expires_in", 3600)
                self._save_tokens()
                return True
            else:
                st.error(f"Failed to refresh Tesla API token: {response.status_code} {response.text}")
                return False
        except Exception as e:
            st.error(f"Error refreshing Tesla API token: {str(e)}")
            return False
    
    def _ensure_authenticated(self):
        """Ensure the client is authenticated, refreshing token if needed"""
        if not self.access_token:
            st.error("Not authenticated with Tesla API")
            return False
            
        # If token is expired or about to expire, refresh it
        if time.time() >= self.token_expires_at - 300:  # 5 minutes buffer
            return self._refresh_access_token()
            
        return True
    
    def get_vehicles(self):
        """
        Get list of vehicles associated with the account.
        
        Returns:
            list: List of vehicles with their details
        """
        if not self._ensure_authenticated():
            return []
            
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(f"{self.BASE_URL}/vehicles", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                self.vehicles = result.get("response", [])
                return self.vehicles
            else:
                st.error(f"Failed to get vehicles: {response.status_code} {response.text}")
                return []
        except Exception as e:
            st.error(f"Error getting vehicles: {str(e)}")
            return []
    
    def select_vehicle(self, vehicle_id=None):
        """
        Select a vehicle to work with.
        
        Args:
            vehicle_id (str, optional): ID of the vehicle to select. If None, selects the first vehicle.
            
        Returns:
            bool: True if a vehicle was selected successfully
        """
        if not self.vehicles:
            vehicles = self.get_vehicles()
            if not vehicles:
                return False
        
        if vehicle_id:
            for vehicle in self.vehicles:
                if str(vehicle.get("id")) == str(vehicle_id):
                    self.vehicle_id = vehicle_id
                    return True
            st.error(f"Vehicle with ID {vehicle_id} not found")
            return False
        else:
            # Select the first vehicle if no ID specified
            if self.vehicles:
                self.vehicle_id = self.vehicles[0].get("id")
                return True
            return False
    
    def get_charging_history(self, start_date=None, end_date=None):
        """
        Get charging history for the selected vehicle.
        
        Args:
            start_date (datetime, optional): Start date for history query
            end_date (datetime, optional): End date for history query
            
        Returns:
            list: List of charging sessions
        """
        if not self._ensure_authenticated() or not self.vehicle_id:
            return []
            
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)  # Default: last 30 days
        if not end_date:
            end_date = datetime.now()
            
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Format dates for Tesla API
            start_ts = int(start_date.timestamp() * 1000)
            end_ts = int(end_date.timestamp() * 1000)
            
            # Endpoint for charge history differs based on API version
            # This is the current endpoint as of March 2025
            response = requests.get(
                f"{self.BASE_URL}/vehicles/{self.vehicle_id}/charge_history?start_time={start_ts}&end_time={end_ts}",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", [])
            else:
                st.error(f"Failed to get charging history: {response.status_code} {response.text}")
                return []
        except Exception as e:
            st.error(f"Error getting charging history: {str(e)}")
            return []
    
    def format_charging_data(self, charging_history):
        """
        Format Tesla API charging history into the app's standardized format.
        
        Args:
            charging_history (list): Raw charging history from Tesla API
            
        Returns:
            list: Charging data in the app's standardized format
        """
        formatted_data = []
        
        for session in charging_history:
            try:
                # Extract session data - field names depend on Tesla API version
                # Adapt these based on the actual response
                start_time = session.get("start_time") or session.get("timestamp")
                if isinstance(start_time, int):  # Convert from milliseconds timestamp
                    start_date = datetime.fromtimestamp(start_time / 1000)
                else:
                    start_date = datetime.now()  # Fallback to current date
                
                # Create a data entry in our app's format
                data = {
                    'date': start_date.replace(hour=0, minute=0, second=0, microsecond=0),
                    'time': start_date.time(),
                    'location': session.get("site_name") or session.get("location", "Unknown"),
                    'provider': "Tesla",  # Provider is always Tesla for this API
                    'connector_type': session.get("connector_type", "Tesla"),
                    'total_kwh': session.get("energy_added") or session.get("charge_energy_added", 0),
                    'peak_kw': session.get("max_power") or session.get("charger_power", 0),
                    'duration': self._format_duration(session.get("duration_seconds", 0)),
                    'cost_per_kwh': session.get("fee_per_kwh", 0),
                    'total_cost': session.get("total_fee") or session.get("charge_cost", 0)
                }
                
                formatted_data.append(data)
            except Exception as e:
                st.warning(f"Error formatting Tesla charging session: {str(e)}")
                continue
                
        return formatted_data
    
    def _format_duration(self, seconds):
        """
        Format duration in seconds to a readable string.
        
        Args:
            seconds (int): Duration in seconds
            
        Returns:
            str: Formatted duration string (e.g., "1h 30m")
        """
        if not seconds:
            return "0m"
            
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"