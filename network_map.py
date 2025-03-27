"""
Module for displaying an interactive EV charging network map with real-time station availability.
"""

import streamlit as st
import folium
from folium.plugins import MarkerCluster, Search
from streamlit_folium import folium_static
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import data_storage
import location_mapper

from charging_network import (
    get_charging_stations, 
    update_station_status, 
    get_connector_types, 
    get_networks
)

def display_charging_network_map():
    """
    Display an interactive map of EV charging stations with real-time availability.
    """
    st.subheader("Interactive Charging Network Map")
    st.write("Find charging stations and view real-time availability")
    
    # Map control settings in sidebar or main view
    with st.container():
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.write("### Map Controls")
            
            # Location search
            st.write("#### Search Area")
            # Default to Sydney, Australia
            default_lat = st.session_state.get('map_latitude', -33.8688)
            default_lon = st.session_state.get('map_longitude', 151.2093)
            
            latitude = st.number_input("Latitude", value=default_lat, format="%.4f")
            longitude = st.number_input("Longitude", value=default_lon, format="%.4f")
            radius = st.slider("Search Radius (km)", min_value=1, max_value=50, value=10)
            
            # Option to show user's historical charging locations
            show_history = st.checkbox("Show my charging history", value=True, 
                                     help="Display your actual charging locations from your history")
            
            # Save in session state
            st.session_state.map_latitude = latitude
            st.session_state.map_longitude = longitude
            
            # Filter options
            st.write("#### Filters")
            
            # Connector types
            connector_options = get_connector_types()
            connector_list = [c["name"] for c in connector_options]
            selected_connectors = st.multiselect("Connector Types", connector_list)
            
            # Convert selected connector names to IDs
            connector_ids = []
            if selected_connectors:
                connector_ids = [c["id"] for c in connector_options if c["name"] in selected_connectors]
            
            # Charging networks
            network_options = get_networks()
            network_list = [n["name"] for n in network_options]
            selected_networks = st.multiselect("Charging Networks", network_list)
            
            # Convert selected network names to IDs
            network_ids = []
            if selected_networks:
                network_ids = [n["id"] for n in network_options if n["name"] in selected_networks]
            
            # Power filter
            min_power = st.slider("Minimum Power (kW)", min_value=0, max_value=350, value=0, step=5)
            
            # Status filter
            status_options = ["Available", "Occupied", "Unknown", "Offline", "Operational"]
            selected_status = st.multiselect("Station Status", status_options, default=["Available", "Operational"])
            
            # Convert status to IDs (simplified mapping)
            status_ids = []
            status_mapping = {
                "Available": 0,
                "Occupied": 10,
                "Unknown": 50,
                "Offline": 75,
                "Operational": 100
            }
            if selected_status:
                status_ids = [status_mapping[s] for s in selected_status if s in status_mapping]
            
            # Compile filters
            filters = {
                "connectors": connector_ids,
                "networks": network_ids,
                "status": status_ids,
                "power": min_power
            }
            
            # Search button
            search_button = st.button("Search Stations")
        
        with col2:
            # Prepare to display map
            st.write("### Charging Station Map")
            
            # Get data and display map when search is clicked
            if search_button or 'charging_map_data' in st.session_state:
                with st.spinner("Fetching charging station data..."):
                    # Check for OpenChargeMap API key
                    api_key = None
                    if "OCMAP_API_KEY" in st.secrets:
                        api_key = st.secrets["OCMAP_API_KEY"]
                    elif "ocmap_api_key" in st.session_state:
                        api_key = st.session_state.ocmap_api_key
                    
                    # If no API key, show option to enter one
                    if not api_key:
                        st.warning("No OpenChargeMap API key found. Using sample data mode.")
                        
                        # Ask for API key
                        provided_key = st.text_input(
                            "Enter OpenChargeMap API key (optional)", 
                            help="Get a free API key from https://openchargemap.org/site/develop",
                            key="api_key_input"
                        )
                        
                        if provided_key:
                            # Store the key in environment variable and session state
                            import os
                            os.environ["OCMAP_API_KEY"] = provided_key
                            st.session_state.ocmap_api_key = provided_key
                            api_key = provided_key
                            st.success("API key saved for this session!")
                    
                    if search_button or not 'charging_map_data' in st.session_state:
                        # Fetch charging station data
                        stations_df = get_charging_stations(latitude, longitude, radius, filters)
                        
                        # Save in session state for persistence between interactions
                        st.session_state.charging_map_data = stations_df
                    else:
                        # Use cached data
                        stations_df = st.session_state.charging_map_data
                    
                    # Always display the map, even if it's using generated sample data
                    # Get user email from session state if available
                    email_address = st.session_state.get('email_address', None)
                    display_network_map(stations_df, latitude, longitude, radius, show_history, email_address)
            else:
                # Show an initial map with sample data if the user hasn't searched yet
                with st.spinner("Loading initial sample data..."):
                    sample_stations_df = get_charging_stations(latitude, longitude, radius, filters)
                    # Get user email from session state if available
                    email_address = st.session_state.get('email_address', None)
                    display_network_map(sample_stations_df, latitude, longitude, radius, show_history, email_address)
                st.info("Adjust your search criteria and click 'Search Stations' to update the map.")
    
    # Stations list
    if 'charging_map_data' in st.session_state:
        display_station_list(st.session_state.charging_map_data)

def display_network_map(stations_df, center_lat, center_lon, radius, show_history=True, email_address=None):
    """
    Display the charging station network map.
    
    Args:
        stations_df (DataFrame): DataFrame containing charging station data
        center_lat (float): Center latitude
        center_lon (float): Center longitude
        radius (int): Search radius in kilometers
        show_history (bool): Whether to show the user's historical charging locations
        email_address (str): Optional email address to load user-specific data
    """
    if stations_df.empty:
        st.warning("No charging stations found matching your criteria.")
        return
    
    # Create base map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11)
    
    # Add search radius circle
    folium.Circle(
        location=[center_lat, center_lon],
        radius=radius * 1000,  # Convert to meters
        color='blue',
        fill=True,
        fill_opacity=0.1
    ).add_to(m)
    
    # Add marker for search center
    folium.Marker(
        location=[center_lat, center_lon],
        popup="Search Center",
        icon=folium.Icon(color='blue', icon='home', prefix='fa')
    ).add_to(m)
    
    # Create marker cluster
    marker_cluster = MarkerCluster().add_to(m)
    
    # Dictionary for status colors
    status_colors = {
        'Available': 'green',
        'Operational': 'green',
        'Occupied': 'orange',
        'Unknown': 'gray',
        'Offline': 'red',
    }
    
    # Add markers for each station
    for idx, station in stations_df.iterrows():
        # Skip stations without coordinates
        if pd.isna(station['latitude']) or pd.isna(station['longitude']):
            continue
        
        # Determine marker color based on status
        status = station['status']
        color = status_colors.get(status, 'blue')
        
        # Create popup content
        popup_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 5px; min-width: 200px;">
            <h4 style="margin: 0 0 5px 0;">{station['name']}</h4>
            <p><b>Operator:</b> {station['operator']}</p>
            <p><b>Address:</b> {station['address']}</p>
            <p><b>Connector:</b> {station['connector_type']}</p>
            <p><b>Power:</b> {station['power_kw']} kW</p>
            <p><b>Status:</b> <span style="color: {color};">{status}</span></p>
            <p><b>Cost:</b> {station['cost']}</p>
            <p><b>Last Verified:</b> {format_timestamp(station['last_verified'])}</p>
            <p><b>Access:</b> {station['usage_type']}</p>
            <p><i>{station['access_comments']}</i></p>
        </div>
        """
        
        # Create marker with custom icon based on status
        folium.Marker(
            location=[station['latitude'], station['longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f"{station['name']} - {station['connector_type']} - {status}",
            icon=folium.Icon(color=color, icon='plug', prefix='fa')
        ).add_to(marker_cluster)
    
    # Add user's historical charging locations if requested
    if show_history:
        # Get email address from session state if not provided
        if email_address is None and 'email_address' in st.session_state:
            email_address = st.session_state['email_address']
        
        if email_address:
            # Load user's charging data
            charging_data = data_storage.load_charging_data(email_address)
            
            if charging_data:
                # Convert to DataFrame
                user_df = data_storage.convert_to_dataframe(charging_data)
                
                # Get location coordinates
                user_df_with_coords = location_mapper.get_location_coordinates(user_df)
                
                # Create a separate layer for user's charging history
                history_group = folium.FeatureGroup(name="Your Charging History")
                
                # Add markers for user's historical charging locations
                history_count = 0
                
                for idx, record in user_df_with_coords.iterrows():
                    # Skip records without coordinates
                    if pd.isna(record.get('latitude')) or pd.isna(record.get('longitude')):
                        continue
                    
                    # Check if location is within search radius (rough calculation)
                    lat_diff = abs(record['latitude'] - center_lat)
                    lon_diff = abs(record['longitude'] - center_lon)
                    # Simple Euclidean distance in degrees, rough approximation
                    dist_approx = ((lat_diff**2 + lon_diff**2) ** 0.5) * 111  # km
                    
                    if dist_approx <= radius * 1.2:  # 20% buffer to ensure we include all relevant points
                        history_count += 1
                        
                        # Create popup content with charging details
                        date_str = record['date'].strftime('%d %b %Y') if 'date' in record and not pd.isna(record['date']) else 'Unknown date'
                        energy = f"{record.get('energy_kwh', 0):.2f} kWh" if 'energy_kwh' in record and not pd.isna(record['energy_kwh']) else 'Unknown'
                        cost = f"${record.get('cost', 0):.2f}" if 'cost' in record and not pd.isna(record['cost']) else 'Unknown'
                        provider = record.get('provider', record.get('location', 'Unknown Provider'))
                        
                        popup_content = f"""
                        <div style="font-family: Arial, sans-serif; padding: 5px; min-width: 200px;">
                            <h4 style="margin: 0 0 5px 0;">{provider}</h4>
                            <p><b>Date:</b> {date_str}</p>
                            <p><b>Location:</b> {record.get('location', 'Unknown location')}</p>
                            <p><b>Energy:</b> {energy}</p>
                            <p><b>Cost:</b> {cost}</p>
                        </div>
                        """
                        
                        # Add marker
                        folium.Marker(
                            location=[record['latitude'], record['longitude']],
                            popup=folium.Popup(popup_content, max_width=300),
                            tooltip=f"Your charging: {provider} - {date_str}",
                            icon=folium.Icon(color='purple', icon='bolt', prefix='fa')
                        ).add_to(history_group)
                
                # Add the history layer to the map
                history_group.add_to(m)
                
                # Display count of history points
                if history_count > 0:
                    st.info(f"Showing {history_count} of your historical charging locations within this area.")
    
    # Display the map
    folium_static(m)
    
    # Display summary stats
    st.write(f"Found {len(stations_df)} charging stations within {radius} km")
    
    # Show stats by status
    status_counts = stations_df['status'].value_counts()
    
    # Convert to dictionary with all possible statuses (including zeros)
    all_statuses = ['Available', 'Occupied', 'Unknown', 'Offline', 'Operational']
    status_dict = {status: status_counts.get(status, 0) for status in all_statuses}
    
    # Display as colored boxes
    cols = st.columns(len(all_statuses))
    for i, status in enumerate(all_statuses):
        with cols[i]:
            color = status_colors.get(status, 'gray')
            count = status_dict.get(status, 0)
            
            html_content = f"""
            <div style="background-color: {color}; padding: 10px; border-radius: 5px; 
                        color: white; text-align: center; margin: 5px 0;">
                <div style="font-size: 24px; font-weight: bold;">{count}</div>
                <div>{status}</div>
            </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)

def display_station_list(stations_df):
    """
    Display a list of charging stations with filtering options.
    
    Args:
        stations_df (DataFrame): DataFrame containing charging station data
    """
    st.subheader("Charging Station List")
    
    # Skip if no data
    if stations_df.empty:
        st.info("No charging stations found.")
        return
    
    # Create a copy for display
    display_df = stations_df.copy()
    
    # Enhance display formats
    if 'last_verified' in display_df.columns:
        display_df['last_verified'] = display_df['last_verified'].apply(format_timestamp)
    
    # Limit columns for display
    columns_to_show = [
        'name', 'operator', 'connector_type', 'power_kw', 
        'status', 'cost', 'last_verified'
    ]
    
    # Ensure all columns exist
    display_columns = [col for col in columns_to_show if col in display_df.columns]
    
    # Sort options
    sort_options = {
        'Name': 'name',
        'Operator': 'operator',
        'Power (highest first)': 'power_kw',
        'Status': 'status',
        'Recently Verified': 'last_verified'
    }
    
    sort_by = st.selectbox("Sort by:", list(sort_options.keys()))
    
    # Apply sorting
    col_name = sort_options[sort_by]
    ascending = True
    
    if col_name == 'power_kw':
        ascending = False
    elif col_name == 'last_verified':
        ascending = False
    
    if col_name in display_df.columns:
        display_df = display_df.sort_values(by=col_name, ascending=ascending)
    
    # Display the data table with hover for more details
    st.dataframe(
        display_df[display_columns], 
        column_config={
            "power_kw": st.column_config.NumberColumn("Power (kW)", format="%.1f kW"),
            "status": st.column_config.Column("Status", help="Current operational status"),
            "last_verified": st.column_config.Column("Last Verified"),
        },
        use_container_width=True,
        hide_index=True
    )
    
    # View detailed information for a selected station
    if not display_df.empty:
        st.subheader("Station Details")
        st.write("Select a station to view more information:")
        
        # Get list of station names
        station_names = display_df['name'].unique().tolist()
        selected_station = st.selectbox("Select Station:", station_names)
        
        # Get the selected station
        station_data = display_df[display_df['name'] == selected_station].iloc[0]
        
        # Display details
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### Basic Information")
            st.write(f"**Name:** {station_data['name']}")
            st.write(f"**Operator:** {station_data['operator']}")
            st.write(f"**Address:** {station_data['address']}")
            st.write(f"**Connector Type:** {station_data['connector_type']}")
            st.write(f"**Power:** {station_data['power_kw']} kW")
        
        with col2:
            st.write("#### Status & Availability")
            
            # Status with color indicator
            status = station_data['status']
            status_color = {
                'Available': 'green',
                'Operational': 'green',
                'Occupied': 'orange',
                'Unknown': 'gray',
                'Offline': 'red',
            }.get(status, 'gray')
            
            st.markdown(f"**Status:** <span style='color:{status_color};font-weight:bold'>{status}</span>", 
                        unsafe_allow_html=True)
            
            st.write(f"**Cost:** {station_data['cost']}")
            st.write(f"**Last Verified:** {station_data['last_verified']}")
            st.write(f"**Usage Type:** {station_data['usage_type']}")
        
        # Additional comments if available
        if 'access_comments' in station_data and station_data['access_comments']:
            st.write("#### Comments")
            st.write(station_data['access_comments'])
        
        # Allow status reporting for demonstration
        st.write("#### Report Status")
        st.write("You can report the current status of this charging station:")
        
        new_status = st.selectbox(
            "Current Status:", 
            ['Available', 'Occupied', 'Offline', 'Unknown']
        )
        
        if st.button("Update Status"):
            success = update_station_status(station_data.get('station_id'), new_status)
            if success:
                st.success(f"Status updated to: {new_status}")
                # Update the data in the session state
                idx = display_df[display_df['name'] == selected_station].index[0]
                st.session_state.charging_map_data.at[idx, 'status'] = new_status
                st.rerun()
            else:
                st.error("Failed to update status. Please try again.")

def format_timestamp(timestamp):
    """
    Format a timestamp for display.
    
    Args:
        timestamp: Timestamp to format, could be string, datetime, or None
        
    Returns:
        str: Formatted timestamp or 'Unknown'
    """
    if pd.isna(timestamp) or timestamp is None:
        return "Unknown"
    
    # Convert to datetime if string
    if isinstance(timestamp, str):
        try:
            timestamp = pd.to_datetime(timestamp)
        except:
            return timestamp
    
    # Calculate how long ago
    if isinstance(timestamp, datetime) or isinstance(timestamp, pd.Timestamp):
        now = datetime.now()
        if now.tzinfo is not None:
            # Make naive for comparison if now has timezone
            now = now.replace(tzinfo=None)
            
        if timestamp.tzinfo is not None:
            # Make naive for comparison if timestamp has timezone
            timestamp = timestamp.replace(tzinfo=None)
            
        time_diff = now - timestamp
        
        if time_diff.days > 30:
            return f"{timestamp.strftime('%b %d, %Y')}"
        elif time_diff.days > 0:
            return f"{time_diff.days} days ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    return str(timestamp)