import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

from gmail_api import GmailClient
from data_parser import parse_charging_emails, clean_charging_data
from data_visualizer import create_visualizations
from utils import get_date_range, export_data_as_csv

# Set page configuration
st.set_page_config(
    page_title="EV Charging Data Analyzer",
    page_icon="⚡",
    layout="wide"
)

# Initialize session state for data storage
if 'charging_data' not in st.session_state:
    st.session_state.charging_data = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'gmail_client' not in st.session_state:
    st.session_state.gmail_client = GmailClient()

# Initialize dashboard preferences
if 'dashboard_preferences' not in st.session_state:
    st.session_state.dashboard_preferences = {
        'panels': {
            'time_series': {'visible': True, 'order': 1, 'name': 'Charging Sessions Over Time'},
            'peak_kw_histogram': {'visible': True, 'order': 2, 'name': 'Peak Power Distribution'},
            'kwh_by_location': {'visible': True, 'order': 3, 'name': 'Energy by Location'},
            'charging_duration': {'visible': True, 'order': 4, 'name': 'Charging Efficiency'},
            'cost_time_series': {'visible': True, 'order': 5, 'name': 'Cost Over Time'},
            'cost_per_kwh': {'visible': True, 'order': 6, 'name': 'Cost per kWh Trends'},
            'cost_by_location': {'visible': True, 'order': 7, 'name': 'Cost by Location'},
        },
        'layout': 'tabs',  # 'tabs' or 'grid'
        'grid_columns': 2   # Number of columns if using grid layout
    }

# App title and description
st.title("⚡ EV Charging Data Analyzer")
st.write("Extract and visualize your EV charging data from Gmail receipts")

# Sidebar for controls
with st.sidebar:
    st.header("Controls")
    
    # Authentication section
    st.subheader("Gmail Authentication")
    
    if not st.session_state.authenticated:
        st.info("Please authenticate with your Gmail account to access your charging receipts.")
        
        # Create two step authentication process
        if 'auth_step' not in st.session_state:
            st.session_state.auth_step = 1
            
        if st.session_state.auth_step == 1:
            # First step: Provide instructions for Google app password
            if st.button("Start Gmail Authentication"):
                try:
                    # Get authentication instructions
                    instructions = st.session_state.gmail_client.get_auth_instructions()
                    st.session_state.auth_instructions = instructions
                    st.session_state.auth_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating authentication instructions: {str(e)}")
        
        elif st.session_state.auth_step == 2:
            # Second step: User follows instructions to create an app password
            st.info("Follow these steps to securely access your Gmail account:")
            
            # Display the instructions provided by the Gmail client
            st.code(st.session_state.auth_instructions, language=None)
            
            # Provide fields for the user to enter their email and app password
            email_address = st.text_input("Enter your Gmail address:", key="email_address")
            app_password = st.text_input("Enter the App Password:", key="app_password", type="password")
            
            if st.button("Connect to Gmail"):
                if email_address and app_password:
                    try:
                        # Authenticate with the provided credentials
                        if st.session_state.gmail_client.authenticate(email_address, app_password):
                            st.session_state.authenticated = True
                            st.success("Authentication successful!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Authentication error: {str(e)}")
                else:
                    st.error("Please enter both your Gmail address and the App Password")
    else:
        st.success("Authenticated with Gmail")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.auth_step = 1
            st.session_state.gmail_client = GmailClient()  # Reset the client
            st.session_state.charging_data = None
            st.rerun()
    
    # Data retrieval section (only show if authenticated)
    if st.session_state.authenticated:
        st.subheader("Data Retrieval")
        
        # Date range selection
        st.write("Select date range for email search:")
        days_back = st.slider("Days to look back", 30, 365, 90)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        st.write(f"From: {start_date.strftime('%Y-%m-%d')}")
        st.write(f"To: {end_date.strftime('%Y-%m-%d')}")
        
        # Search query options
        st.write("Search options:")
        default_search = "EV charging receipt OR Ampol AmpCharge OR charging session"
        search_label = st.text_input("Email search term", default_search)
        st.caption("You can use 'OR' to search for multiple terms. The app will search both subject and body content for each term.")
        
        # Fetch data button
        if st.button("Fetch Charging Data"):
            with st.spinner("Fetching emails..."):
                try:
                    # Use just search term for now (IMAP search is more limited with complex queries)
                    # Get emails
                    gmail_client = st.session_state.gmail_client
                    emails = gmail_client.get_emails(
                        query=search_label
                    )
                    
                    # Apply date filtering in Python rather than in IMAP
                    if emails:
                        # Filter emails by date
                        filtered_emails = []
                        for email in emails:
                            if email['date']:
                                # Make naive datetime for comparison (remove timezone info)
                                email_date = email['date'].replace(tzinfo=None)
                                if start_date <= email_date <= end_date:
                                    filtered_emails.append(email)
                        
                        emails_count = len(filtered_emails)
                        st.info(f"Found {emails_count} emails matching your criteria.")
                        
                        # Parse emails to extract charging data
                        with st.spinner("Parsing email data..."):
                            charging_data = parse_charging_emails(filtered_emails)
                            
                            if charging_data:
                                # Clean and process the charging data
                                df = clean_charging_data(charging_data)
                                
                                # Store data in session state
                                st.session_state.charging_data = df
                                st.session_state.last_refresh = datetime.now()
                                st.success(f"Successfully extracted data from {len(charging_data)} charging sessions.")
                            else:
                                st.warning("No charging data could be extracted from the emails.")
                    else:
                        st.warning("No emails found matching your search criteria.")
                    
                    # Make sure to properly close the IMAP connection when done
                    try:
                        gmail_client.close()
                    except:
                        pass
                        
                except Exception as e:
                    # On error, still try to close the connection
                    try:
                        gmail_client.close()
                    except:
                        pass
                        
                    # Show error message
                    error_message = str(e)
                    if "LOGOUT" in error_message:
                        st.error("Connection error with Gmail. Please try again or log out and log back in.")
                        # Attempt to reconnect
                        try:
                            st.session_state.gmail_client = GmailClient()
                            if st.session_state.gmail_client.authenticate(
                                email_address=gmail_client.email_address, 
                                app_password=gmail_client.app_password
                            ):
                                st.info("Connection restored. Please try searching again.")
                        except:
                            st.error("Could not automatically restore the connection. Please log out and log back in.")
                    else:
                        st.error(f"Error fetching data: {error_message}")
        
        # Display last refresh time
        if st.session_state.last_refresh:
            st.write(f"Last updated: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Export data section
        if st.session_state.charging_data is not None:
            st.subheader("Export Data")
            if st.button("Export as CSV"):
                csv_data = export_data_as_csv(st.session_state.charging_data)
                st.download_button(
                    label="Download CSV file",
                    data=csv_data,
                    file_name=f"ev_charging_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            # Dashboard customization
            st.subheader("Dashboard Customization")
            
            # Layout selection
            st.session_state.dashboard_preferences['layout'] = st.radio(
                "Layout Style",
                ["tabs", "grid"],
                index=0 if st.session_state.dashboard_preferences['layout'] == 'tabs' else 1,
                horizontal=True,
                format_func=lambda x: "Tabbed Layout" if x == "tabs" else "Grid Layout"
            )
            
            # If grid layout, let user select number of columns
            if st.session_state.dashboard_preferences['layout'] == 'grid':
                st.session_state.dashboard_preferences['grid_columns'] = st.slider(
                    "Number of columns in grid", 
                    min_value=1, 
                    max_value=3, 
                    value=st.session_state.dashboard_preferences['grid_columns']
                )
            
            # Visualization selection and ordering
            st.write("Select and order visualizations:")
            
            # Create a temporary list for sorting
            viz_list = []
            for viz_id, viz_props in st.session_state.dashboard_preferences['panels'].items():
                viz_list.append({
                    'id': viz_id,
                    'name': viz_props['name'],
                    'visible': viz_props['visible'],
                    'order': viz_props['order']
                })
            
            # Sort by order
            viz_list = sorted(viz_list, key=lambda x: x['order'])
            
            # Create multiselect for choosing visible visualizations
            selected_viz = st.multiselect(
                "Select visualizations to display",
                options=[viz['id'] for viz in viz_list],
                default=[viz['id'] for viz in viz_list if viz['visible']],
                format_func=lambda x: st.session_state.dashboard_preferences['panels'][x]['name']
            )
            
            # Update visibility based on selection
            for viz_id in st.session_state.dashboard_preferences['panels']:
                st.session_state.dashboard_preferences['panels'][viz_id]['visible'] = viz_id in selected_viz
            
            # Allow reordering for visible visualizations
            st.write("Drag to reorder visualizations:")
            
            # Filter for visible visualizations only
            visible_viz = [v for v in viz_list if v['id'] in selected_viz]
            
            # Create a draggable list for reordering
            for i, viz in enumerate(visible_viz):
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    st.write(f"{viz['name']}")
                
                with col2:
                    # Move up button (disabled for first item)
                    if i > 0 and st.button("↑", key=f"up_{viz['id']}"):
                        # Swap order with previous item
                        current_order = st.session_state.dashboard_preferences['panels'][viz['id']]['order']
                        prev_id = visible_viz[i-1]['id']
                        prev_order = st.session_state.dashboard_preferences['panels'][prev_id]['order']
                        
                        st.session_state.dashboard_preferences['panels'][viz['id']]['order'] = prev_order
                        st.session_state.dashboard_preferences['panels'][prev_id]['order'] = current_order
                        st.rerun()
                    
                    # Move down button (disabled for last item)
                    if i < len(visible_viz) - 1 and st.button("↓", key=f"down_{viz['id']}"):
                        # Swap order with next item
                        current_order = st.session_state.dashboard_preferences['panels'][viz['id']]['order']
                        next_id = visible_viz[i+1]['id']
                        next_order = st.session_state.dashboard_preferences['panels'][next_id]['order']
                        
                        st.session_state.dashboard_preferences['panels'][viz['id']]['order'] = next_order
                        st.session_state.dashboard_preferences['panels'][next_id]['order'] = current_order
                        st.rerun()
            
            # Reset button
            if st.button("Reset to Default Layout"):
                # Reset to default preferences
                st.session_state.dashboard_preferences = {
                    'panels': {
                        'time_series': {'visible': True, 'order': 1, 'name': 'Charging Sessions Over Time'},
                        'peak_kw_histogram': {'visible': True, 'order': 2, 'name': 'Peak Power Distribution'},
                        'kwh_by_location': {'visible': True, 'order': 3, 'name': 'Energy by Location'},
                        'charging_duration': {'visible': True, 'order': 4, 'name': 'Charging Efficiency'},
                        'cost_time_series': {'visible': True, 'order': 5, 'name': 'Cost Over Time'},
                        'cost_per_kwh': {'visible': True, 'order': 6, 'name': 'Cost per kWh Trends'},
                        'cost_by_location': {'visible': True, 'order': 7, 'name': 'Cost by Location'},
                    },
                    'layout': 'tabs',
                    'grid_columns': 2
                }
                st.rerun()

# Main content area
if st.session_state.authenticated:
    if st.session_state.charging_data is not None:
        data = st.session_state.charging_data
        
        # Summary statistics
        st.header("Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        # Import the calculate_statistics function
        from utils import calculate_statistics
        
        # Get statistics from the data
        stats = calculate_statistics(data)
        
        with col1:
            st.metric("Total Sessions", stats['total_sessions'])
        
        with col2:
            # Ensure total_kwh is a valid number
            total_kwh = stats['total_kwh']
            # Use a fallback value of 0 if the value is None or NaN
            if pd.isna(total_kwh):
                total_kwh = 0
            st.metric("Total kWh", f"{total_kwh:.2f}")
        
        with col3:
            # Ensure total_cost is a valid number
            total_cost = stats['total_cost']
            # Use a fallback value of 0 if the value is None or NaN
            if pd.isna(total_cost):
                total_cost = 0
            st.metric("Total Cost", f"${total_cost:.2f}")
        
        with col4:
            # Ensure avg_cost_per_kwh is a valid number
            avg_cost_per_kwh = stats['avg_cost_per_kwh']
            # Use a fallback value of 0 if the value is None or NaN
            if pd.isna(avg_cost_per_kwh):
                avg_cost_per_kwh = 0
            st.metric("Avg. Cost per kWh", f"${avg_cost_per_kwh:.2f}")
        
        # Generate all charts
        charts = create_visualizations(data)
        
        # Function to render a visualization panel
        def render_visualization(viz_id, charts):
            if viz_id in charts and st.session_state.dashboard_preferences['panels'][viz_id]['visible']:
                st.subheader(st.session_state.dashboard_preferences['panels'][viz_id]['name'])
                st.plotly_chart(charts[viz_id], use_container_width=True)
        
        # Create dynamic dashboard based on user preferences
        if st.session_state.dashboard_preferences['layout'] == 'tabs':
            # Create tabs for each visible visualization group
            tab_groups = {
                'time_series': {'name': 'Time Series', 'charts': ['time_series']},
                'charging_stats': {'name': 'Charging Statistics', 'charts': ['peak_kw_histogram', 'kwh_by_location', 'charging_duration']},
                'cost_analysis': {'name': 'Cost Analysis', 'charts': ['cost_time_series', 'cost_per_kwh', 'cost_by_location']},
                'raw_data': {'name': 'Raw Data', 'charts': []}
            }
            
            # Filter for at least one visible chart in each tab group
            visible_tabs = []
            for group_id, group in tab_groups.items():
                if group_id == 'raw_data' or any(chart_id in charts and 
                                              st.session_state.dashboard_preferences['panels'].get(chart_id, {}).get('visible', False) 
                                              for chart_id in group['charts']):
                    visible_tabs.append(group)
            
            # Create tabs
            tabs = st.tabs([group['name'] for group in visible_tabs])
            
            # Populate each tab
            for i, (tab, group) in enumerate(zip(tabs, visible_tabs)):
                with tab:
                    if group['name'] == 'Time Series':
                        # Render time series chart
                        render_visualization('time_series', charts)
                    
                    elif group['name'] == 'Charging Statistics':
                        # Create a 2-column layout for the first two charts
                        if (st.session_state.dashboard_preferences['panels'].get('peak_kw_histogram', {}).get('visible', False) or
                            st.session_state.dashboard_preferences['panels'].get('kwh_by_location', {}).get('visible', False)):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.session_state.dashboard_preferences['panels'].get('peak_kw_histogram', {}).get('visible', False):
                                    st.subheader(st.session_state.dashboard_preferences['panels']['peak_kw_histogram']['name'])
                                    st.plotly_chart(charts['peak_kw_histogram'], use_container_width=True)
                            
                            with col2:
                                if st.session_state.dashboard_preferences['panels'].get('kwh_by_location', {}).get('visible', False):
                                    st.subheader(st.session_state.dashboard_preferences['panels']['kwh_by_location']['name'])
                                    st.plotly_chart(charts['kwh_by_location'], use_container_width=True)
                        
                        # Render charging duration chart
                        render_visualization('charging_duration', charts)
                    
                    elif group['name'] == 'Cost Analysis':
                        # Create a 2-column layout for the first two charts
                        if (st.session_state.dashboard_preferences['panels'].get('cost_time_series', {}).get('visible', False) or
                            st.session_state.dashboard_preferences['panels'].get('cost_per_kwh', {}).get('visible', False)):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.session_state.dashboard_preferences['panels'].get('cost_time_series', {}).get('visible', False):
                                    st.subheader(st.session_state.dashboard_preferences['panels']['cost_time_series']['name'])
                                    st.plotly_chart(charts['cost_time_series'], use_container_width=True)
                            
                            with col2:
                                if st.session_state.dashboard_preferences['panels'].get('cost_per_kwh', {}).get('visible', False):
                                    st.subheader(st.session_state.dashboard_preferences['panels']['cost_per_kwh']['name'])
                                    st.plotly_chart(charts['cost_per_kwh'], use_container_width=True)
                        
                        # Render cost by location chart
                        render_visualization('cost_by_location', charts)
                    
                    elif group['name'] == 'Raw Data':
                        st.subheader("Raw Data")
        
        else:  # Grid layout
            # Create a list of visible visualizations sorted by order
            viz_list = []
            for viz_id, viz_props in st.session_state.dashboard_preferences['panels'].items():
                if viz_props['visible'] and viz_id in charts:
                    viz_list.append({
                        'id': viz_id,
                        'name': viz_props['name'],
                        'order': viz_props['order']
                    })
            
            # Sort by order
            viz_list = sorted(viz_list, key=lambda x: x['order'])
            
            # Determine how many columns to use
            num_columns = st.session_state.dashboard_preferences['grid_columns']
            
            # Split visualizations into rows based on number of columns
            viz_rows = []
            for i in range(0, len(viz_list), num_columns):
                viz_rows.append(viz_list[i:i + num_columns])
            
            # Render each row
            for row in viz_rows:
                columns = st.columns(num_columns)
                
                for i, viz in enumerate(row):
                    if i < len(columns):  # Safety check
                        with columns[i]:
                            st.subheader(viz['name'])
                            st.plotly_chart(charts[viz['id']], use_container_width=True)
            
            # Add Raw Data section at the end
            st.subheader("Raw Data")
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                location_filter = st.multiselect(
                    "Filter by Location",
                    options=data['location'].unique(),
                    default=[]
                )
            
            with col2:
                min_date, max_date = data['date'].min(), data['date'].max()
                date_range = st.date_input(
                    "Date range",
                    [min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )
            
            with col3:
                sort_by = st.selectbox(
                    "Sort by",
                    options=['date', 'total_kwh', 'peak_kw', 'total_cost', 'cost_per_kwh'],
                    index=0
                )
                sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)
            
            # Apply filters
            filtered_data = data.copy()
            
            if location_filter:
                filtered_data = filtered_data[filtered_data['location'].isin(location_filter)]
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                # Make sure date comparison works by converting to same format
                filtered_data = filtered_data[
                    (filtered_data['date'].dt.normalize() >= pd.Timestamp(start_date)) & 
                    (filtered_data['date'].dt.normalize() <= pd.Timestamp(end_date))
                ]
            
            # Apply sorting
            ascending = sort_order == "Ascending"
            filtered_data = filtered_data.sort_values(by=sort_by, ascending=ascending)
            
            # Display filtered data
            st.dataframe(filtered_data, use_container_width=True)
    else:
        st.info("No charging data available. Use the sidebar controls to fetch data from Gmail.")
else:
    st.info("Please authenticate with Gmail using the sidebar controls to get started.")

# Footer
st.markdown("---")
st.write("This app extracts EV charging data from your Gmail receipts. Your data remains private and is not stored on any servers.")
