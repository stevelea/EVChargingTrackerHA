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
    # Create a copy of the DataFrame to avoid modifying the original
    result_df = df.copy()
    
    # Add empty latitude and longitude columns
    if 'latitude' not in result_df.columns:
        result_df['latitude'] = None
    if 'longitude' not in result_df.columns:
        result_df['longitude'] = None
    
    # Get unique locations
    unique_locations = result_df['location'].dropna().unique()
    
    # Create a geocoding cache
    if 'geocoding_cache' not in st.session_state:
        st.session_state.geocoding_cache = {}
    
    # Geocode each unique location
    for location in unique_locations:
        # Skip empty or "Garage" locations for now (can be customized later)
        if not location or location.lower() in st.session_state.geocoding_cache:
            continue
            
        # Get coordinates
        coords = geocode_location(location)
        
        # Add to cache
        st.session_state.geocoding_cache[location.lower()] = coords
    
    # Apply coordinates from cache to DataFrame
    for i, row in result_df.iterrows():
        if pd.notna(row['location']) and row['location'].lower() in st.session_state.geocoding_cache:
            coords = st.session_state.geocoding_cache[row['location'].lower()]
            if coords:
                result_df.at[i, 'latitude'] = coords[0]
                result_df.at[i, 'longitude'] = coords[1]
    
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
        
        # Create popup content
        popup_content = f"""
        <b>Location:</b> {row['location']}<br>
        <b>Date:</b> {row['date'].strftime('%Y-%m-%d')}<br>
        <b>Provider:</b> {row['provider']}<br>
        <b>Energy:</b> {row['total_kwh']:.2f} kWh<br>
        <b>Cost:</b> ${row['total_cost']:.2f}<br>
        <br>
        <a href="{plugshare_url}" target="_blank">View on PlugShare</a>
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
            # Allow user to set home location
            if 'home_location' not in st.session_state:
                st.session_state.home_location = "Garage"
            
            home_location = st.text_input(
                "Home Charger Location Name:", 
                value=st.session_state.home_location
            )
            
            if home_location != st.session_state.home_location:
                st.session_state.home_location = home_location
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
    
    # Create and process the data for mapping
    with st.spinner("Processing location data..."):
        # Replace "Garage" with the home location name in the dataset
        df_for_map = df.copy()
        df_for_map.loc[df_for_map['location'] == "Garage", 'location'] = st.session_state.home_location
        
        # Get coordinates for all locations
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
        
        # Add PlugShare links
        location_stats['PlugShare Link'] = location_stats.apply(
            lambda row: f"[View on PlugShare]({get_plugshare_link(row['Location'], row['Latitude'], row['Longitude'])})", 
            axis=1
        )
        
        # Drop coordinate columns before display
        display_stats = location_stats.drop(columns=['Latitude', 'Longitude'])
        
        st.dataframe(display_stats, use_container_width=True)
    else:
        st.info("Add specific location names like 'Sydney CBD' or 'Brisbane Airport' to view them on the map.")