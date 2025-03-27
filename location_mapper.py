"""
Module for handling location mapping functionality for EV charging stations.
This module uses geopy for geocoding and folium for creating interactive maps.
"""

import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from streamlit_folium import folium_static
import pandas as pd
import streamlit as st

from utils import get_plugshare_link

# Initialize geocoder with the app name
geocoder = Nominatim(user_agent="ev_charging_analyzer")

def geocode_location(location_name, country="Australia"):
    """
    Convert a location name to geographic coordinates using geocoding.
    
    Args:
        location_name (str): The name of the location to geocode
        country (str): The country to bias the search towards
        
    Returns:
        tuple: (latitude, longitude) or None if geocoding fails
    """
    if not location_name or location_name.lower() in ["unknown", "n/a", ""]:
        return None
    
    try:
        # Add country to improve geocoding accuracy
        search_query = f"{location_name}, {country}"
        location = geocoder.geocode(search_query, timeout=10)
        
        if location:
            return (location.latitude, location.longitude)
        else:
            return None
    except Exception as e:
        st.error(f"Error geocoding location '{location_name}': {str(e)}")
        return None

def get_location_coordinates(df):
    """
    Process a DataFrame to add latitude and longitude for all locations.
    Uses caching for efficiency.
    
    Args:
        df (DataFrame): DataFrame containing charging data with 'location' column
        
    Returns:
        DataFrame: Original DataFrame with 'latitude' and 'longitude' columns added
    """
    # Check if the DataFrame already has coordinates that we can use
    coords_exist = False
    if 'latitude' in df.columns and 'longitude' in df.columns:
        # Count non-null coordinates
        valid_coords = (~df['latitude'].isna() & ~df['longitude'].isna()).sum()
        if valid_coords > 0:
            print(f"Using {valid_coords} existing coordinates from {df.shape[0]} records")
            coords_exist = True
    
    # Create a copy of the DataFrame to avoid modifying the original
    result_df = df.copy()
    
    # Add empty latitude and longitude columns if they don't exist
    if 'latitude' not in result_df.columns:
        result_df['latitude'] = None
    if 'longitude' not in result_df.columns:
        result_df['longitude'] = None
    
    # If we already have coordinates for all records, return early
    if coords_exist and valid_coords == df.shape[0]:
        return result_df
    
    # Create a geocoding cache
    if 'geocoding_cache' not in st.session_state:
        st.session_state.geocoding_cache = {}
    
    # Get unique locations that need geocoding (those without coordinates)
    if coords_exist:
        # Only get locations for rows without valid coordinates
        missing_coords = result_df[result_df['latitude'].isna() | result_df['longitude'].isna()]
        unique_locations = missing_coords['location'].dropna().unique()
        print(f"Need to geocode {len(unique_locations)} locations with missing coordinates")
    else:
        # Get all unique locations
        unique_locations = result_df['location'].dropna().unique()
        print(f"Need to geocode {len(unique_locations)} unique locations")
    
    # Geocode each unique location not already in cache
    for location in unique_locations:
        # Skip empty locations or those already in cache
        if not location or location.lower() in st.session_state.geocoding_cache:
            continue
            
        # Get coordinates
        coords = geocode_location(location)
        
        # Add to cache
        st.session_state.geocoding_cache[location.lower()] = coords
    
    # Apply coordinates from cache to DataFrame
    coords_applied = 0
    for i, row in result_df.iterrows():
        # Skip if row already has valid coordinates
        if coords_exist and pd.notna(row['latitude']) and pd.notna(row['longitude']):
            continue
            
        # Apply coordinates from cache if available
        if pd.notna(row['location']) and row['location'].lower() in st.session_state.geocoding_cache:
            coords = st.session_state.geocoding_cache[row['location'].lower()]
            if coords:
                result_df.at[i, 'latitude'] = coords[0]
                result_df.at[i, 'longitude'] = coords[1]
                coords_applied += 1
    
    print(f"Applied {coords_applied} coordinates from cache")
    
    return result_df

def create_charging_map(df, zoom_start=10):
    """
    Create an interactive map showing all charging locations.
    
    Args:
        df (DataFrame): DataFrame containing charging data with 'latitude', 'longitude', and other columns
        zoom_start (int): Initial zoom level for the map
        
    Returns:
        folium.Map: A folium map object ready to be displayed
    """
    # Add coordinates if needed
    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        df = get_location_coordinates(df)
    
    # Filter out rows with missing coordinates
    map_data = df.dropna(subset=['latitude', 'longitude'])
    
    if map_data.empty:
        st.warning("No location data available for mapping. Try adding specific location names.")
        return None
    
    # Calculate the center of the map (median of available coordinates)
    center_lat = map_data['latitude'].median()
    center_lon = map_data['longitude'].median()
    
    # Create a base map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
    
    # Add marker cluster for better visualization
    marker_cluster = MarkerCluster().add_to(m)
    
    # Add markers for each location
    for _, row in map_data.iterrows():
        # Generate PlugShare link for this location
        plugshare_url = get_plugshare_link(row['location'], row['latitude'], row['longitude'])
        
        # Create popup content with proper HTML formatting
        popup_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 5px;">
            <h4 style="margin: 0 0 5px 0;">{row['location']}</h4>
            <b>Date:</b> {row['date'].strftime('%Y-%m-%d')}<br>
            <b>Provider:</b> {row['provider']}<br>
            <b>Energy:</b> {row['total_kwh']:.2f} kWh<br>
            <b>Cost:</b> ${row['total_cost']:.2f}<br>
            <br>
            <a href="{plugshare_url}" target="_blank" style="background-color: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: inline-block;">View on PlugShare</a>
        </div>
        """
        
        # Create marker
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=row['location'],
            icon=folium.Icon(color='green', icon='bolt', prefix='fa')
        ).add_to(marker_cluster)
    
    return m

def display_charging_map(df):
    """
    Display an interactive map of charging locations in Streamlit.
    
    Args:
        df (DataFrame): DataFrame containing charging data
    """
    st.subheader("Charging Station Map")
    
    # Create location setup container
    setup_container = st.container()
    
    with setup_container:
        st.write("Configure your location settings:")
        col1, col2 = st.columns(2)
        
        with col1:
            # Allow user to set home location and persist it
            if 'home_location' not in st.session_state:
                # Try to load from data storage
                try:
                    # Import get_replit_status function from data_storage module
                    from data_storage import get_replit_status
                    replit_status = get_replit_status()
                    
                    if replit_status.get('available', False):
                        from replit import db
                        home_location_key = f"home_location_{st.session_state.get('current_user_email', 'default')}"
                        if home_location_key in db:
                            st.session_state.home_location = db[home_location_key]
                        else:
                            st.session_state.home_location = "Garage"
                    else:
                        # Try to load from a JSON file
                        import json
                        import os
                        settings_file = os.path.join("data", "user_settings.json")
                        if os.path.exists(settings_file):
                            try:
                                with open(settings_file, 'r') as f:
                                    settings = json.load(f)
                                email_key = st.session_state.get('current_user_email', 'default')
                                if email_key in settings and 'home_location' in settings[email_key]:
                                    st.session_state.home_location = settings[email_key]['home_location']
                                else:
                                    st.session_state.home_location = "Garage"
                            except:
                                st.session_state.home_location = "Garage"
                        else:
                            st.session_state.home_location = "Garage"
                except:
                    st.session_state.home_location = "Garage"
            
            home_location = st.text_input(
                "Home Charger Location Name:", 
                value=st.session_state.home_location
            )
            
            if home_location != st.session_state.home_location:
                st.session_state.home_location = home_location
                
                # Save the home location for persistence
                try:
                    # Get replit status again
                    from data_storage import get_replit_status
                    replit_status = get_replit_status()
                    
                    if replit_status.get('available', False):
                        from replit import db
                        home_location_key = f"home_location_{st.session_state.get('current_user_email', 'default')}"
                        db[home_location_key] = home_location
                    else:
                        # Save to a JSON file
                        import json
                        import os
                        
                        # Ensure data directory exists
                        os.makedirs("data", exist_ok=True)
                        
                        settings_file = os.path.join("data", "user_settings.json")
                        settings = {}
                        
                        # Load existing settings if available
                        if os.path.exists(settings_file):
                            try:
                                with open(settings_file, 'r') as f:
                                    settings = json.load(f)
                            except:
                                settings = {}
                        
                        # Update with new home location
                        email_key = st.session_state.get('current_user_email', 'default')
                        if email_key not in settings:
                            settings[email_key] = {}
                        settings[email_key]['home_location'] = home_location
                        
                        # Save settings
                        with open(settings_file, 'w') as f:
                            json.dump(settings, f)
                except:
                    st.warning("Unable to save home location for future sessions")
                
                # Clear cache for home location
                if 'geocoding_cache' in st.session_state and home_location.lower() in st.session_state.geocoding_cache:
                    del st.session_state.geocoding_cache[home_location.lower()]
        
        with col2:
            # Country for geocoding
            if 'geocoding_country' not in st.session_state:
                st.session_state.geocoding_country = "Australia"
            
            country = st.text_input(
                "Country for Location Search:", 
                value=st.session_state.geocoding_country
            )
            
            if country != st.session_state.geocoding_country:
                st.session_state.geocoding_country = country
                # Clear entire cache when country changes
                st.session_state.geocoding_cache = {}
    
    # Allow manual setting of home charger coordinates
    if st.checkbox("Set Home Charger Coordinates Manually"):
        col1, col2 = st.columns(2)
        
        with col1:
            home_lat = st.number_input("Home Latitude:", value=-33.8688)
        
        with col2:
            home_lon = st.number_input("Home Longitude:", value=151.2093)
        
        # Store home coordinates in cache
        if 'geocoding_cache' not in st.session_state:
            st.session_state.geocoding_cache = {}
        
        st.session_state.geocoding_cache[home_location.lower()] = (home_lat, home_lon)
        
    # Add sample charging locations checkbox 
    show_samples = st.checkbox("Show sample charging locations", value=True,
                      help="Display sample charging locations on the map for demonstration")
    
    # Create and process the data for mapping
    with st.spinner("Processing location data..."):
        # Replace "Garage" with the home location name in the dataset
        df_for_map = df.copy()
        df_for_map.loc[df_for_map['location'] == "Garage", 'location'] = st.session_state.home_location
        
        # If showing samples is checked, add sample charging locations for demonstration
        if show_samples:
            # Create sample location data with pre-defined coordinates
            sample_locations = [
                {"location": "Sydney CBD Tesla Supercharger", "date": pd.Timestamp.now(), 
                 "provider": "Tesla", "total_kwh": 45.5, "total_cost": 22.75,
                 "latitude": -33.8688, "longitude": 151.2093},
                {"location": "Melbourne Central Charging Station", "date": pd.Timestamp.now(),
                 "provider": "Ampol AmpCharge", "total_kwh": 35.2, "total_cost": 18.60,
                 "latitude": -37.8136, "longitude": 144.9631},
                {"location": "Brisbane Airport EV Station", "date": pd.Timestamp.now(),
                 "provider": "Evie Networks", "total_kwh": 28.7, "total_cost": 15.32,
                 "latitude": -27.3942, "longitude": 153.1218},
                {"location": "Adelaide CBD Chargers", "date": pd.Timestamp.now(),
                 "provider": "ChargeFox", "total_kwh": 32.1, "total_cost": 16.05,
                 "latitude": -34.9285, "longitude": 138.6007},
                {"location": "Perth Shopping Centre", "date": pd.Timestamp.now(),
                 "provider": "NRMA", "total_kwh": 40.3, "total_cost": 20.15,
                 "latitude": -31.9505, "longitude": 115.8605}
            ]
            
            # Create sample DataFrame
            sample_df = pd.DataFrame(sample_locations)
            
            # Update geocoding cache with sample locations to ensure they appear
            if 'geocoding_cache' not in st.session_state:
                st.session_state.geocoding_cache = {}
                
            # Add samples to cache
            for _, row in sample_df.iterrows():
                location_key = row['location'].lower()
                st.session_state.geocoding_cache[location_key] = (row['latitude'], row['longitude'])
            
            # Add sample locations to the main dataframe
            df_for_map = pd.concat([df_for_map, sample_df], ignore_index=True)
        
        # Process coordinates for the complete dataset
        df_with_coords = get_location_coordinates(df_for_map)
    
    # Create the map
    charging_map = create_charging_map(df_with_coords)
    
    if charging_map:
        # Display the map
        st.write("Interactive map of your charging locations:")
        folium_static(charging_map)
        
        # Display statistics by location
        st.subheader("Charging Statistics by Location")
        location_stats = df_with_coords.groupby('location').agg({
            'total_kwh': 'sum',
            'total_cost': 'sum',
            'date': 'count',
            'latitude': 'first',
            'longitude': 'first'
        }).reset_index()
        
        location_stats.columns = ['Location', 'Total Energy (kWh)', 'Total Cost ($)', 'Number of Sessions', 'Latitude', 'Longitude']
        location_stats['Average Cost per kWh ($)'] = location_stats['Total Cost ($)'] / location_stats['Total Energy (kWh)']
        
        # Format columns
        location_stats['Total Energy (kWh)'] = location_stats['Total Energy (kWh)'].round(2)
        location_stats['Total Cost ($)'] = location_stats['Total Cost ($)'].round(2)
        location_stats['Average Cost per kWh ($)'] = location_stats['Average Cost per kWh ($)'].round(2)
        
        # Add PlugShare links with HTML formatting for better visibility
        location_stats['PlugShare Link'] = location_stats.apply(
            lambda row: f"<a href='{get_plugshare_link(row['Location'], row['Latitude'], row['Longitude'])}' target='_blank'><span style='background-color: #4CAF50; color: white; padding: 5px 8px; border-radius: 4px;'>View on PlugShare</span></a>", 
            axis=1
        )
        
        # Drop coordinate columns before display
        display_stats = location_stats.drop(columns=['Latitude', 'Longitude'])
        
        # Display the stats dataframe
        st.dataframe(display_stats, use_container_width=True)
    else:
        st.info("Add specific location names like 'Sydney CBD' or 'Brisbane Airport' to view them on the map.")