"""
Module for fetching and processing real-time charging station data.
This module interacts with public EV charging APIs to retrieve station information.
"""

import os
import requests
import json
import time
from datetime import datetime
import pandas as pd
import streamlit as st

# Cache timeout in seconds (10 minutes)
CACHE_TIMEOUT = 600

def get_charging_stations(latitude, longitude, radius=10, filters=None):
    """
    Fetch charging stations near a specific location.
    
    Args:
        latitude (float): Latitude of the center point
        longitude (float): Longitude of the center point
        radius (int): Radius in kilometers to search
        filters (dict): Optional filters like connector types, networks, etc.
        
    Returns:
        DataFrame: Charging stations with their details
    """
    # Check if we have cached data that's still valid
    if 'charging_stations_cache' in st.session_state and 'cache_time' in st.session_state:
        cache_age = time.time() - st.session_state.cache_time
        if cache_age < CACHE_TIMEOUT:
            # Cache is still valid, use it
            return st.session_state.charging_stations_cache
    
    # OpenChargeMap API endpoint
    api_key = os.environ.get('OCMAP_API_KEY')
    if not api_key:
        st.warning("OpenChargeMap API key not found. Using limited data mode.")
        return fetch_limited_station_data(latitude, longitude, radius)
    
    # API base URL
    base_url = "https://api.openchargemap.io/v3/poi"
    
    # Build query parameters
    params = {
        'key': api_key,
        'latitude': latitude,
        'longitude': longitude,
        'distance': radius,
        'distanceunit': 'km',
        'maxresults': 100,
        'includecomments': True,
        'verbose': False,
        'output': 'json'
    }
    
    # Add filters if provided
    if filters:
        if 'connectors' in filters and filters['connectors']:
            params['connectiontypeid'] = ','.join(map(str, filters['connectors']))
        if 'networks' in filters and filters['networks']:
            params['operatorid'] = ','.join(map(str, filters['networks']))
        if 'status' in filters and filters['status']:
            params['statustypeid'] = ','.join(map(str, filters['status']))
        if 'power' in filters and filters['power']:
            params['minpowerkw'] = filters['power']
    
    try:
        # Make API request
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse response
        stations = response.json()
        
        # Convert to DataFrame
        stations_df = process_charging_stations(stations)
        
        # Cache the results
        st.session_state.charging_stations_cache = stations_df
        st.session_state.cache_time = time.time()
        
        return stations_df
        
    except Exception as e:
        st.error(f"Error fetching charging station data: {str(e)}")
        return fetch_limited_station_data(latitude, longitude, radius)

def fetch_limited_station_data(latitude, longitude, radius):
    """
    Fetch limited charging station data from local database when API key is not available.
    
    Args:
        latitude (float): Latitude of the center point
        longitude (float): Longitude of the center point
        radius (int): Radius in kilometers to search
        
    Returns:
        DataFrame: Limited charging station data
    """
    # Check if local data file exists
    local_data_path = os.path.join("data", "local_charging_stations.json")
    
    if os.path.exists(local_data_path):
        try:
            with open(local_data_path, 'r') as f:
                stations = json.load(f)
                
            # Filter stations by distance
            # Note: This is a simplified distance calculation
            filtered_stations = []
            for station in stations:
                # Simple distance calculation using Euclidean distance (not ideal for geo coords but simple)
                station_lat = station.get('AddressInfo', {}).get('Latitude')
                station_lon = station.get('AddressInfo', {}).get('Longitude')
                
                if station_lat and station_lon:
                    # Simple approximation of distance for filtering
                    dlat = abs(station_lat - latitude)
                    dlon = abs(station_lon - longitude)
                    dist_approx = ((dlat**2 + dlon**2) ** 0.5) * 111  # Rough km conversion
                    
                    if dist_approx <= radius:
                        filtered_stations.append(station)
            
            return process_charging_stations(filtered_stations)
            
        except Exception as e:
            st.error(f"Error loading local charging station data: {str(e)}")
    
    # If local data doesn't exist or can't be loaded, return sample data
    sample_stations = generate_sample_stations(latitude, longitude, radius)
    return process_charging_stations(sample_stations)

def process_charging_stations(stations):
    """
    Process raw charging station data into a DataFrame.
    
    Args:
        stations (list): List of station dictionaries from API
        
    Returns:
        DataFrame: Processed charging station data
    """
    processed_stations = []
    
    for station in stations:
        # Extract basic information
        address_info = station.get('AddressInfo', {})
        
        # Process each connection
        connections = station.get('Connections', [])
        for conn in connections:
            # Extract connection info
            connection_type = conn.get('ConnectionType', {}).get('Title', 'Unknown')
            power_kw = conn.get('PowerKW')
            status = conn.get('StatusType', {}).get('Title', 'Unknown')
            
            # Check if amps and voltage are available, compute power if needed
            if not power_kw and 'Amps' in conn and 'Voltage' in conn:
                amps = conn.get('Amps', 0)
                voltage = conn.get('Voltage', 0)
                power_kw = (amps * voltage / 1000) if amps and voltage else None
            
            # Format charging cost
            cost_description = conn.get('Cost', "Unknown")
            
            # Add to processed stations
            processed_stations.append({
                'name': station.get('AddressInfo', {}).get('Title', 'Unknown Station'),
                'operator': station.get('OperatorInfo', {}).get('Title', 'Unknown'),
                'address': f"{address_info.get('AddressLine1', '')}, {address_info.get('Town', '')}, {address_info.get('StateOrProvince', '')}",
                'latitude': address_info.get('Latitude'),
                'longitude': address_info.get('Longitude'),
                'connector_type': connection_type,
                'power_kw': power_kw,
                'status': status,
                'cost': cost_description,
                'last_verified': station.get('DateLastVerified'),
                'usage_type': station.get('UsageType', {}).get('Title', 'Unknown'),
                'access_comments': station.get('GeneralComments', ''),
                'station_id': station.get('ID')
            })
    
    # Convert to DataFrame
    if processed_stations:
        df = pd.DataFrame(processed_stations)
        
        # Convert datetime strings to datetime objects
        if 'last_verified' in df.columns:
            df['last_verified'] = pd.to_datetime(df['last_verified'], errors='coerce')
        
        return df
    else:
        # Return empty DataFrame with the correct columns
        return pd.DataFrame(columns=[
            'name', 'operator', 'address', 'latitude', 'longitude',
            'connector_type', 'power_kw', 'status', 'cost', 'last_verified',
            'usage_type', 'access_comments', 'station_id'
        ])

def generate_sample_stations(center_lat, center_lon, radius):
    """
    Generate sample charging station data for demonstration purposes.
    
    Args:
        center_lat (float): Center latitude
        center_lon (float): Center longitude
        radius (int): Radius in kilometers
        
    Returns:
        list: Sample charging station data
    """
    # Australian charging network operators
    aus_operators = [
        "ChargeFox", "Evie Networks", "AmpCharge", "Tesla", 
        "NRMA", "RAC", "Jolt", "Chargepod", "Everty"
    ]
    
    # Sample stations with different connector types and statuses
    import random
    
    # Generate sample locations around the center point
    stations = []
    for i in range(10):
        # Generate random coordinates within the radius
        # This is a simplified approach that doesn't account for Earth's curvature
        lat_offset = (random.random() * 2 - 1) * radius / 111.0
        lon_offset = (random.random() * 2 - 1) * radius / (111.0 * abs(abs(center_lat) - 90) / 90)
        
        lat = center_lat + lat_offset
        lon = center_lon + lon_offset
        
        # Random operator
        operator = random.choice(aus_operators)
        
        # Generate a station
        station = {
            "ID": i + 1,
            "OperatorInfo": {
                "Title": operator,
                "WebsiteURL": f"https://{operator.lower().replace(' ', '')}.com.au"
            },
            "AddressInfo": {
                "Title": f"{operator} Charging Station #{i+1}",
                "AddressLine1": f"{random.randint(1, 100)} Sample Street",
                "Town": "Sample City",
                "StateOrProvince": "Sample State",
                "Postcode": f"{random.randint(1000, 9999)}",
                "CountryID": 13,  # Australia
                "Country": {
                    "Title": "Australia"
                },
                "Latitude": lat,
                "Longitude": lon
            },
            "Connections": [
                {
                    "ConnectionType": {
                        "ID": 33,
                        "Title": "CCS (Type 2)"
                    },
                    "StatusType": {
                        "ID": random.choice([0, 10, 50, 75, 100]),
                        "Title": random.choice(["Available", "Occupied", "Unknown", "Offline", "Operational"])
                    },
                    "PowerKW": round(random.choice([7.4, 11, 22, 50, 150, 350]), 1),
                    "Cost": "$0.40 per kWh"
                }
            ],
            "DateLastVerified": datetime.now().isoformat(),
            "UsageType": {
                "Title": random.choice(["Public", "Private", "Restricted Access"])
            },
            "GeneralComments": "Sample charging station for demonstration purposes."
        }
        
        # Add a second connector to some stations
        if random.random() > 0.5:
            station["Connections"].append({
                "ConnectionType": {
                    "ID": 25,
                    "Title": "Type 2 (Socket Only)"
                },
                "StatusType": {
                    "ID": random.choice([0, 10, 50, 75, 100]),
                    "Title": random.choice(["Available", "Occupied", "Unknown", "Offline", "Operational"])
                },
                "PowerKW": round(random.choice([7.4, 11, 22]), 1),
                "Cost": "$0.35 per kWh"
            })
        
        stations.append(station)
    
    return stations

def update_station_status(station_id, new_status):
    """
    Update the status of a charging station.
    
    Args:
        station_id (int): ID of the station to update
        new_status (str): New status for the station
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    # This would typically call an API to update the station status
    # For now, just update the cached data
    if 'charging_stations_cache' in st.session_state:
        stations_df = st.session_state.charging_stations_cache
        stations_df.loc[stations_df['station_id'] == station_id, 'status'] = new_status
        st.session_state.charging_stations_cache = stations_df
        return True
    return False

def get_connector_types():
    """
    Get a list of available connector types.
    
    Returns:
        list: Connector types with IDs and names
    """
    return [
        {"id": 1, "name": "Type 1 (J1772)"},
        {"id": 2, "name": "Type 2 (Mennekes)"},
        {"id": 25, "name": "Type 2 (Socket Only)"},
        {"id": 33, "name": "CCS (Type 2)"},
        {"id": 32, "name": "CCS (Type 1)"},
        {"id": 27, "name": "CHAdeMO"},
        {"id": 3, "name": "Tesla (Proprietary)"},
        {"id": 8, "name": "Tesla (Supercharger)"},
        {"id": 10, "name": "Tesla (Destination Charger)"},
    ]

def get_networks():
    """
    Get a list of available charging networks.
    
    Returns:
        list: Charging networks with IDs and names
    """
    return [
        {"id": 23, "name": "ChargeFox"},
        {"id": 3534, "name": "Evie Networks"},
        {"id": 299, "name": "Tesla"},
        {"id": 2, "name": "ChargePoint"},
        {"id": 3423, "name": "AmpCharge"},
        {"id": 3514, "name": "NRMA"},
        {"id": 3654, "name": "Jolt"},
        {"id": 3542, "name": "Chargepod"},
    ]