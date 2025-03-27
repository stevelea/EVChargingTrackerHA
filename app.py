import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

from gmail_api import GmailClient
from tesla_api import TeslaApiClient
from data_parser import parse_charging_emails, parse_evcc_csv, clean_charging_data
from pdf_parser import parse_multiple_pdfs
from data_visualizer import create_visualizations
from data_storage import (
    load_charging_data, save_charging_data, merge_charging_data, 
    convert_to_dataframe, filter_data_by_date_range, delete_charging_data,
    filter_records_by_criteria, delete_selected_records, generate_record_id,
    get_replit_status
)
from utils import get_date_range, export_data_as_csv, save_credentials, load_credentials
from location_mapper import display_charging_map
from predictive_analysis import (
    forecast_monthly_cost, predict_cost_by_provider, usage_prediction
)
from network_map import display_charging_network_map

# Import test data creator
import create_test_data

# Set page configuration
st.set_page_config(
    page_title="EV Charging Data Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for data storage
if 'charging_data' not in st.session_state:
    st.session_state.charging_data = None
    st.session_state.current_user_email = None
    
    # We'll load data once the user is authenticated
    # This keeps data separate for each user
    
    # Generate test data for development/testing
    if os.environ.get('ENABLE_TEST_DATA', 'false').lower() == 'true':
        # Create test data for the network map feature
        try:
            # Create and load the test data
            create_test_data.create_sample_charging_data()
            email_address = 'test@example.com'
            st.session_state.email_address = email_address
            test_data = load_charging_data(email_address)
            
            # Debug info
            print(f"Loaded {len(test_data)} test records")
            if test_data and len(test_data) > 0:
                print(f"Sample record: {test_data[0]}")
            
            if test_data:
                st.session_state.charging_data = clean_charging_data(test_data)
                st.session_state.current_user_email = email_address
                # Only auto-authenticate if specifically requested (not just loading test data)
                if os.environ.get('AUTO_AUTHENTICATE', 'false').lower() == 'true':
                    st.session_state.authenticated = True  # Auto-authenticate for testing
                else:
                    # Make sure test email is loaded in the sidebar, but still require login
                    if 'authenticated' not in st.session_state:
                        st.session_state.authenticated = False
                
                # Debug info for processed data
                if st.session_state.charging_data is not None:
                    print(f"Processed {len(st.session_state.charging_data)} records into DataFrame")
                    if not st.session_state.charging_data.empty:
                        print(f"Sample DataFrame columns: {list(st.session_state.charging_data.columns)}")
                        # Check if location data exists
                        if 'latitude' in st.session_state.charging_data.columns:
                            null_lat = st.session_state.charging_data['latitude'].isnull().sum()
                            print(f"Records with null latitude: {null_lat} out of {len(st.session_state.charging_data)}")
                
        except Exception as e:
            print(f"Error generating test data: {str(e)}")

# Function to load user data
def load_user_data(email_address=None):
    """Load and process data for a specific user"""
    if email_address:
        # Store the current user's email
        st.session_state.current_user_email = email_address
        
    # If we have a current user, load their data
    if st.session_state.current_user_email:
        existing_data = load_charging_data(st.session_state.current_user_email)
        if existing_data:
            # Process the existing data
            try:
                df = clean_charging_data(existing_data)
                st.session_state.charging_data = df
                return True
            except Exception as e:
                st.error(f"Error loading saved data: {str(e)}")
                st.session_state.charging_data = None
        else:
            st.session_state.charging_data = None
    
    return False

if 'last_refresh' not in st.session_state:
    # If we loaded data, set last refresh to now
    if st.session_state.charging_data is not None:
        st.session_state.last_refresh = datetime.now()
    else:
        st.session_state.last_refresh = None

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'gmail_client' not in st.session_state:
    st.session_state.gmail_client = GmailClient()
if 'tesla_client' not in st.session_state:
    st.session_state.tesla_client = TeslaApiClient()
if 'tesla_authenticated' not in st.session_state:
    st.session_state.tesla_authenticated = False
if 'auto_fetch_data' not in st.session_state:
    st.session_state.auto_fetch_data = False

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
            'provider_cost_comparison': {'visible': True, 'order': 8, 'name': 'Provider Cost Comparison'},
            'provider_kwh_comparison': {'visible': True, 'order': 9, 'name': 'Provider Energy Comparison'},
            'monthly_cost_forecast': {'visible': True, 'order': 10, 'name': 'Monthly Cost Forecast'},
            'provider_trend_prediction': {'visible': True, 'order': 11, 'name': 'Provider Cost Trends'},
            'usage_prediction': {'visible': True, 'order': 12, 'name': 'Usage Prediction'},
            'odometer_time_series': {'visible': True, 'order': 13, 'name': 'Odometer Readings Over Time'},
            'energy_efficiency': {'visible': True, 'order': 14, 'name': 'Energy Efficiency (kWh per km)'},
            'cost_per_km': {'visible': True, 'order': 15, 'name': 'Cost Efficiency ($ per km)'},
            'map_view': {'visible': True, 'order': 16, 'name': 'Location Map'},
            'network_map': {'visible': True, 'order': 17, 'name': 'Charging Network Map'},
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
        
        # Load saved credentials if available
        if 'email_loaded' not in st.session_state:
            credentials = load_credentials()
            if credentials and 'email_address' in credentials:
                st.session_state.saved_email = credentials['email_address']
                st.session_state.email_loaded = True
            else:
                st.session_state.saved_email = ""
                st.session_state.email_loaded = True
        
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
            # Pre-fill with saved email if available
            email_address = st.text_input("Enter your Gmail address:", 
                                          key="email_address", 
                                          value=st.session_state.saved_email)
            app_password = st.text_input("Enter the App Password:", key="app_password", type="password")
            save_email = st.checkbox("Remember my email address", value=True)
            
            if st.button("Connect to Gmail"):
                if email_address and app_password:
                    try:
                        # Authenticate with the provided credentials
                        if st.session_state.gmail_client.authenticate(email_address, app_password):
                            st.session_state.authenticated = True
                            
                            # Save credentials if requested
                            if save_email:
                                save_credentials(email_address)
                            
                            # Set a flag to auto-fetch data after authentication
                            st.session_state.auto_fetch_data = True
                                
                            st.success("Authentication successful! Automatically fetching your charging data...")
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
    
    # Tesla API Authentication section
    if st.session_state.authenticated and not st.session_state.tesla_authenticated:
        st.subheader("Tesla API Authentication (Optional)")
        st.info("Connect to Tesla API to retrieve charging data for non-Tesla vehicles using Tesla Superchargers.")
        
        # Show Tesla authentication form
        show_tesla_auth = st.checkbox("Use Tesla API", value=False, key="show_tesla_auth")
        
        if show_tesla_auth:
            # Direct token authentication
            tesla_access_token = st.text_input("Tesla API Access Token:", type="password", key="tesla_access_token")
            tesla_refresh_token = st.text_input("Tesla API Refresh Token:", type="password", key="tesla_refresh_token")
            
            if st.button("Connect to Tesla API"):
                if tesla_access_token and tesla_refresh_token:
                    try:
                        if st.session_state.tesla_client.set_tokens(tesla_access_token, tesla_refresh_token):
                            st.session_state.tesla_authenticated = True
                            st.success("Tesla API authentication successful!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Tesla API authentication error: {str(e)}")
                else:
                    st.error("Please enter both the Tesla API Access Token and Refresh Token")
    
    # Show Tesla status if authenticated
    if st.session_state.tesla_authenticated:
        st.success("Connected to Tesla API")
        if st.button("Disconnect Tesla API"):
            st.session_state.tesla_authenticated = False
            st.session_state.tesla_client = TeslaApiClient()  # Reset the client
            st.rerun()
    
    # Database Cleaning section (only show if authenticated)
    if st.session_state.authenticated:
        st.subheader("Database Management")
        
        # Show Replit database status if available
        replit_status = get_replit_status()
        if replit_status['available']:
            status_icon = "✅" if replit_status['enabled'] else "⚠️"
            status_text = "enabled" if replit_status['enabled'] else "available but not active"
            st.info(f"{status_icon} Replit persistence {status_text}")
        else:
            st.info("🔄 Using local file storage")
        
        # Show currently stored data info
        stored_data = load_charging_data(st.session_state.current_user_email)
        if stored_data:
            st.info(f"You have {len(stored_data)} charging sessions stored in the database.")
            
            # Quick cleaning section (direct access)
            st.write("Clean Database (Fix EVCC Duplicates):")
            clean_evcc_only = st.checkbox(
                "Clean only EVCC data", 
                value=True,
                key="sidebar_clean_evcc_only",
                help="When checked, only EVCC CSV data will be deduplicated. Otherwise, all data sources will be cleaned."
            )
            
            # Option to run cleaning process
            if st.button("Clean Database Now", type="primary", key="sidebar_clean_db"):
                with st.spinner("Cleaning database..."):
                    # Load existing data
                    existing_data = load_charging_data(st.session_state.current_user_email)
                    
                    if not existing_data:
                        st.warning("No data to clean.")
                    else:
                        # Count original records
                        original_count = len(existing_data)
                        
                        # Initialize cleaned data list with seen_ids to track duplicates
                        cleaned_data = []
                        seen_ids = set()
                        
                        # Filter by source if EVCC only option is selected
                        for record in existing_data:
                            # Skip record if it's EVCC and we're cleaning EVCC only
                            # or if we're cleaning all data
                            if (clean_evcc_only and record.get('source') == 'EVCC CSV') or not clean_evcc_only:
                                # Generate a new ID based on current algorithm
                                record_id = generate_record_id(record)
                                
                                # Only keep the record if we haven't seen this ID before
                                if record_id not in seen_ids:
                                    # Force update the ID
                                    record['id'] = record_id
                                    cleaned_data.append(record)
                                    seen_ids.add(record_id)
                            else:
                                # Keep non-EVCC records as they are if EVCC only option is selected
                                cleaned_data.append(record)
                        
                        # Save the cleaned data
                        save_charging_data(cleaned_data, st.session_state.current_user_email)
                        
                        # Report results
                        removed_count = original_count - len(cleaned_data)
                        if removed_count > 0:
                            st.success(f"Successfully removed {removed_count} duplicate records.")
                            
                            # Update main data
                            st.session_state.charging_data = clean_charging_data(cleaned_data)
                            st.rerun()
                        else:
                            st.info("No duplicate records found.")
        else:
            st.info("No charging data is currently stored in the database.")
                
        # Data retrieval section
        st.subheader("Data Retrieval")
        
        # Create tabs for different data sources
        data_source_tabs = st.tabs(["Gmail Search", "EVCC CSV Upload", "PDF Upload", "Data Management"])
        
        # Gmail Search Tab
        with data_source_tabs[0]:
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
        
        # EVCC CSV Upload Tab
        with data_source_tabs[1]:
            st.write("Upload EVCC charging data from CSV export:")
            
            # Cost per kWh for EVCC data
            evcc_cost_per_kwh = st.number_input(
                "Default cost per kWh for EVCC sessions ($)", 
                min_value=0.0, 
                max_value=2.0, 
                value=0.21, 
                step=0.01,
                format="%.2f"
            )
            
            # Upload field
            uploaded_file = st.file_uploader(
                "Choose EVCC CSV file", 
                type="csv", 
                help="Upload a CSV file exported from EVCC"
            )
            
            # Option to replace or merge data
            if uploaded_file is not None:
                replace_evcc_data = st.checkbox(
                    "Replace existing EVCC data", 
                    value=False,
                    help="When checked, new EVCC data will replace any existing EVCC data. Otherwise, it will be merged with all data sources."
                )
        
        # PDF Upload Tab
        with data_source_tabs[2]:
            st.write("Upload PDF charging receipts:")
            st.info("Upload PDF receipts from EV charging stations. The system will extract charging data using OCR.")
            
            # Upload PDF files
            uploaded_pdfs = st.file_uploader(
                "Choose PDF receipts", 
                type="pdf",
                accept_multiple_files=True,
                help="Upload one or more PDF receipts from EV charging stations"
            )
            
            # Option to replace or merge data
            if uploaded_pdfs and len(uploaded_pdfs) > 0:
                replace_pdf_data = st.checkbox(
                    "Replace existing PDF data", 
                    value=False,
                    help="When checked, new PDF data will replace any existing PDF data. Otherwise, it will be merged with all data sources."
                )
        
        # Data Management Tab
        with data_source_tabs[3]:
            st.write("Data Management:")
            
            # Show currently stored data info
            stored_data = load_charging_data(st.session_state.current_user_email)
            if stored_data:
                st.info(f"You have {len(stored_data)} charging sessions stored in the database.")
                
                # Quick cleaning section (direct access)
                with st.expander("Database Cleaning (Fix EVCC Duplicates)", expanded=True):
                    st.write("Use this section to clean duplicate records in the database:")
                    clean_evcc_only = st.checkbox(
                        "Clean only EVCC data", 
                        value=True,
                        help="When checked, only EVCC CSV data will be deduplicated. Otherwise, all data sources will be cleaned."
                    )
                    
                    # Option to run cleaning process
                    if st.button("Clean Database Now", type="primary"):
                        with st.spinner("Cleaning database..."):
                            # Load existing data
                            existing_data = load_charging_data(st.session_state.current_user_email)
                            
                            if not existing_data:
                                st.warning("No data to clean.")
                            else:
                                # Count original records
                                original_count = len(existing_data)
                                
                                # Initialize cleaned data list with seen_ids to track duplicates
                                cleaned_data = []
                                seen_ids = set()
                                
                                # Filter by source if EVCC only option is selected
                                for record in existing_data:
                                    # Skip record if it's EVCC and we're cleaning EVCC only
                                    # or if we're cleaning all data
                                    if (clean_evcc_only and record.get('source') == 'EVCC CSV') or not clean_evcc_only:
                                        # Generate a new ID based on current algorithm
                                        record_id = generate_record_id(record)
                                        
                                        # Only keep the record if we haven't seen this ID before
                                        if record_id not in seen_ids:
                                            # Force update the ID
                                            record['id'] = record_id
                                            cleaned_data.append(record)
                                            seen_ids.add(record_id)
                                    else:
                                        # Keep non-EVCC records as they are if EVCC only option is selected
                                        cleaned_data.append(record)
                                
                                # Save the cleaned data
                                save_charging_data(cleaned_data, st.session_state.current_user_email)
                                
                                # Report results
                                removed_count = original_count - len(cleaned_data)
                                if removed_count > 0:
                                    st.success(f"Successfully removed {removed_count} duplicate records.")
                                    
                                    # Update main data
                                    st.session_state.charging_data = clean_charging_data(cleaned_data)
                                    st.rerun()
                                else:
                                    st.info("No duplicate records found.")
                
                # Data Management Tabs
                data_mgmt_tabs = st.tabs(["Selective Delete", "Manual Entry", "Odometer Updates", "Delete All"])
                
                # Selective Delete Tab
                with data_mgmt_tabs[0]:
                    st.subheader("Selectively Delete Records")
                    
                    # Initialize session state variables for selective deletion
                    if 'selected_records_to_delete' not in st.session_state:
                        st.session_state.selected_records_to_delete = []
                        
                    if 'records_to_display' not in st.session_state:
                        st.session_state.records_to_display = stored_data
                        
                    # Filter options  
                    filter_col1, filter_col2 = st.columns(2)
                    
                    with filter_col1:
                        # Get unique providers
                        providers = ["All"] + sorted(set(record.get('provider', 'Unknown') for record in stored_data))
                        selected_provider = st.selectbox("Filter by Provider:", providers, key="delete_provider_filter")
                    
                    with filter_col2:
                        # Get unique sources
                        sources = ["All"] + sorted(set(record.get('source', 'Unknown') for record in stored_data if record.get('source')))
                        selected_source = st.selectbox("Filter by Source:", sources, key="delete_source_filter")
                    
                    # Date range filter
                    min_date = min((record.get('date') for record in stored_data if record.get('date')), default=datetime.now() - timedelta(days=365))
                    max_date = max((record.get('date') for record in stored_data if record.get('date')), default=datetime.now())
                    
                    # Format dates for display in the date input
                    min_date_str = min_date.strftime('%Y-%m-%d') if isinstance(min_date, datetime) else min_date
                    max_date_str = max_date.strftime('%Y-%m-%d') if isinstance(max_date, datetime) else max_date
                    
                    date_col1, date_col2 = st.columns(2)
                    with date_col1:
                        start_date = st.date_input("From Date:", min_date, key="delete_start_date")
                    with date_col2:
                        end_date = st.date_input("To Date:", max_date, key="delete_end_date")
                    
                    # Create criteria dictionary for filtering
                    filter_criteria = {}
                    
                    if selected_provider != "All":
                        filter_criteria['provider'] = selected_provider
                    
                    if selected_source != "All":
                        filter_criteria['source'] = selected_source
                    
                    # Add date range
                    if start_date and end_date:
                        # Convert to datetime for consistent comparison
                        start_datetime = datetime.combine(start_date, datetime.min.time())
                        end_datetime = datetime.combine(end_date, datetime.max.time())
                        filter_criteria['date_range'] = (start_datetime, end_datetime)
                    
                    # Apply filters button
                    if st.button("Apply Filters"):
                        # Apply the filters
                        st.session_state.records_to_display = filter_records_by_criteria(filter_criteria, st.session_state.current_user_email)
                        # Clear previous selections when filters change
                        st.session_state.selected_records_to_delete = []
                        st.success(f"Found {len(st.session_state.records_to_display)} records matching your criteria.")
                    
                    # Reset filters button
                    if st.button("Reset Filters"):
                        st.session_state.records_to_display = stored_data
                        st.session_state.selected_records_to_delete = []
                        st.success("Filters reset.")
                    
                    # Create a DataFrame for display
                    if st.session_state.records_to_display:
                        # Create a simpler version of the data for the table
                        table_data = []
                        for record in st.session_state.records_to_display:
                            # Format date for display
                            date_str = record.get('date', '')
                            if isinstance(date_str, datetime):
                                date_str = date_str.strftime('%Y-%m-%d')
                                
                            # Add a row for each record
                            table_data.append({
                                'ID': record.get('id', ''),
                                'Date': date_str,
                                'Provider': record.get('provider', 'Unknown'),
                                'Location': record.get('location', 'Unknown'),
                                'kWh': record.get('total_kwh', 0),
                                'Cost': record.get('total_cost', 0),
                                'Source': record.get('source', 'Unknown')
                            })
                        
                        # Convert to DataFrame
                        df_display = pd.DataFrame(table_data)
                        
                        # Display the table with checkboxes for selection
                        st.write("Select records to delete:")
                        
                        # Display in pages if there are many records
                        records_per_page = 10
                        total_pages = (len(df_display) + records_per_page - 1) // records_per_page
                        
                        # Page selector
                        if total_pages > 1:
                            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
                        else:
                            page = 1
                            
                        # Get the current page data
                        start_idx = (page - 1) * records_per_page
                        end_idx = min(start_idx + records_per_page, len(df_display))
                        df_page = df_display.iloc[start_idx:end_idx]
                        
                        # Create checkboxes for each row
                        for idx, row in df_page.iterrows():
                            record_id = row['ID']
                            # Use both the index and the record_id to ensure uniqueness
                            checkbox_key = f"delete_{idx}_{record_id}"
                            col1, col2 = st.columns([1, 10])
                            
                            with col1:
                                is_checked = st.checkbox("", key=checkbox_key, 
                                                        value=record_id in st.session_state.selected_records_to_delete)
                                
                                # Update the selection list based on checkbox state
                                if is_checked:
                                    if record_id not in st.session_state.selected_records_to_delete:
                                        st.session_state.selected_records_to_delete.append(record_id)
                                else:
                                    if record_id in st.session_state.selected_records_to_delete:
                                        st.session_state.selected_records_to_delete.remove(record_id)
                            
                            with col2:
                                st.write(f"**{row['Date']}** | {row['Provider']} | {row['Location']} | {row['kWh']:.2f} kWh | ${row['Cost']:.2f} | Source: {row['Source']}")
                        
                        # Show selection summary and delete button
                        if st.session_state.selected_records_to_delete:
                            st.info(f"Selected {len(st.session_state.selected_records_to_delete)} records to delete.")
                            
                            # Confirm deletion
                            if st.button("Delete Selected Records", type="primary"):
                                success, count = delete_selected_records(st.session_state.selected_records_to_delete, st.session_state.current_user_email)
                                if success:
                                    st.success(f"Successfully deleted {count} records.")
                                    # Reset selections
                                    st.session_state.selected_records_to_delete = []
                                    # Reload data
                                    stored_data = load_charging_data(st.session_state.current_user_email)
                                    st.session_state.records_to_display = stored_data
                                    # Update main data
                                    if stored_data:
                                        st.session_state.charging_data = clean_charging_data(stored_data)
                                    else:
                                        st.session_state.charging_data = None
                                    st.rerun()
                                else:
                                    st.error("Failed to delete records.")
                        else:
                            st.write("Select records to delete using the checkboxes.")
                    else:
                        st.warning("No records found matching your criteria.")
                
                # Manual Entry Tab
                with data_mgmt_tabs[1]:
                    st.subheader("Manually Add Charging Session")
                    st.write("Enter details for a new charging session:")
                    
                    with st.form("manual_entry_form"):
                        # Form fields for charging session data
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Date and time
                            charge_date = st.date_input(
                                "Charging Date:", 
                                value=datetime.now(),
                                key="manual_charge_date"
                            )
                            
                            # Provider
                            providers = sorted(set(record.get('provider', 'Unknown') 
                                              for record in stored_data 
                                              if record.get('provider', 'Unknown') != 'Unknown')
                                          or ['Tesla', 'ChargeFox', 'Evie', 'AmpCharge'])
                            
                            provider = st.selectbox(
                                "Provider:", 
                                options=providers,
                                key="manual_provider"
                            )
                            
                            # Location
                            location = st.text_input(
                                "Location:", 
                                value="",
                                key="manual_location",
                                placeholder="e.g., Westfield Bondi Junction"
                            )
                            
                            # Duration in minutes
                            duration_minutes = st.number_input(
                                "Duration (minutes):", 
                                min_value=1, 
                                max_value=1440,
                                value=30,
                                step=1,
                                key="manual_duration"
                            )
                        
                        with col2:
                            # Energy details
                            total_kwh = st.number_input(
                                "Total Energy (kWh):", 
                                min_value=0.1, 
                                max_value=200.0,
                                value=30.0,
                                step=0.1,
                                format="%.1f",
                                key="manual_kwh"
                            )
                            
                            peak_kw = st.number_input(
                                "Peak Power (kW):", 
                                min_value=1.0, 
                                max_value=350.0,
                                value=50.0,
                                step=1.0,
                                format="%.1f",
                                key="manual_peak_kw"
                            )
                            
                            # Cost details
                            cost_per_kwh = st.number_input(
                                "Cost per kWh ($):", 
                                min_value=0.0, 
                                max_value=2.0,
                                value=0.52,
                                step=0.01,
                                format="%.2f",
                                key="manual_cost_per_kwh"
                            )
                            
                            total_cost = st.number_input(
                                "Total Cost ($):", 
                                min_value=0.0, 
                                max_value=500.0,
                                value=round(total_kwh * cost_per_kwh, 2),
                                step=0.01,
                                format="%.2f",
                                key="manual_total_cost"
                            )
                            
                            # Odometer reading
                            odometer = st.number_input(
                                "Odometer Reading (km):", 
                                min_value=0.0, 
                                max_value=1000000.0,
                                value=0.0,
                                step=1.0,
                                format="%.1f",
                                key="manual_odometer"
                            )
                        
                        # Submit button
                        submit_button = st.form_submit_button("Add Charging Session")
                    
                    # Process form submission outside the form
                    if submit_button:
                        # Create charging record
                        new_record = {
                            'date': datetime.combine(charge_date, datetime.min.time()),
                            'provider': provider,
                            'location': location,
                            'total_kwh': float(total_kwh),
                            'peak_kw': float(peak_kw),
                            'cost_per_kwh': float(cost_per_kwh),
                            'total_cost': float(total_cost),
                            'duration': duration_minutes * 60,  # Convert minutes to seconds
                            'source': 'Manual Entry',
                            'odometer': float(odometer) if odometer > 0 else None
                        }
                        
                        # Generate a unique ID
                        new_record['id'] = generate_record_id(new_record)
                        
                        # Load existing data
                        existing_data = load_charging_data(st.session_state.current_user_email)
                        
                        # Add new record
                        if existing_data:
                            # Check for duplicates
                            duplicate = False
                            for record in existing_data:
                                if record.get('id') == new_record['id']:
                                    duplicate = True
                                    break
                            
                            if not duplicate:
                                existing_data.append(new_record)
                                save_charging_data(existing_data, st.session_state.current_user_email)
                                st.success("Charging session added successfully!")
                                
                                # Update main data
                                st.session_state.charging_data = clean_charging_data(existing_data)
                                st.rerun()
                            else:
                                st.error("A duplicate record already exists.")
                        else:
                            # First record
                            save_charging_data([new_record], st.session_state.current_user_email)
                            st.success("Charging session added successfully!")
                            
                            # Update main data
                            st.session_state.charging_data = clean_charging_data([new_record])
                            st.rerun()
                            
                    # Tips for manual entry
                    with st.expander("Tips for Manual Entry"):
                        st.markdown("""
                        ### Tips for accurate manual entries:
                        
                        - Enter the date when the charging session occurred
                        - Provider refers to the charging network (e.g., Tesla, ChargeFox, Evie)
                        - Location should be descriptive (e.g., "Westfield Bondi Junction")
                        - Total Energy is the amount of electricity delivered in kilowatt-hours (kWh)
                        - Peak Power is the maximum charging rate achieved in kilowatts (kW)
                        - You can enter either Cost per kWh or Total Cost, and the system will calculate the other
                        - Duration is how long the charging session lasted
                        - Odometer reading is optional but helpful for efficiency calculations
                        """)
                
                # Odometer Updates Tab
                with data_mgmt_tabs[2]:
                    st.subheader("Update Odometer Readings")
                    st.write("Manually update the odometer reading for each charging session.")
                    
                    # Initialize session state for odometer updates
                    if 'records_for_odometer' not in st.session_state:
                        st.session_state.records_for_odometer = stored_data
                    
                    # Filter options for finding sessions
                    filter_col1, filter_col2 = st.columns(2)
                    
                    with filter_col1:
                        # Get unique providers
                        providers = ["All"] + sorted(set(record.get('provider', 'Unknown') for record in stored_data))
                        selected_provider = st.selectbox("Filter by Provider:", providers, key="odometer_provider_filter")
                    
                    with filter_col2:
                        # Get unique locations
                        locations = ["All"] + sorted(set(record.get('location', 'Unknown') for record in stored_data if record.get('location')))
                        selected_location = st.selectbox("Filter by Location:", locations, key="odometer_location_filter")
                    
                    # Date range filter
                    min_date = min((record.get('date') for record in stored_data if record.get('date')), default=datetime.now() - timedelta(days=365))
                    max_date = max((record.get('date') for record in stored_data if record.get('date')), default=datetime.now())
                    
                    date_col1, date_col2 = st.columns(2)
                    with date_col1:
                        start_date = st.date_input("From Date:", min_date, key="odometer_start_date")
                    with date_col2:
                        end_date = st.date_input("To Date:", max_date, key="odometer_end_date")
                    
                    # Create criteria dictionary for filtering
                    filter_criteria = {}
                    
                    if selected_provider != "All":
                        filter_criteria['provider'] = selected_provider
                    
                    if selected_location != "All":
                        filter_criteria['location'] = selected_location
                    
                    # Add date range
                    if start_date and end_date:
                        # Convert to datetime for consistent comparison
                        start_datetime = datetime.combine(start_date, datetime.min.time())
                        end_datetime = datetime.combine(end_date, datetime.max.time())
                        filter_criteria['date_range'] = (start_datetime, end_datetime)
                    
                    # Apply filters button
                    if st.button("Find Sessions", key="find_odometer_sessions"):
                        # Apply the filters
                        st.session_state.records_for_odometer = filter_records_by_criteria(filter_criteria, st.session_state.current_user_email)
                        st.success(f"Found {len(st.session_state.records_for_odometer)} records matching your criteria.")
                    
                    # Display records with editable odometer fields
                    if st.session_state.records_for_odometer:
                        st.write("Enter odometer readings for each session:")
                        
                        # Sort records by date for easier entry
                        sorted_records = sorted(
                            st.session_state.records_for_odometer, 
                            key=lambda x: x.get('date', datetime.now()) if x.get('date') else datetime.now()
                        )
                        
                        # Process records in chunks for pagination
                        records_per_page = 10
                        total_pages = (len(sorted_records) + records_per_page - 1) // records_per_page
                        
                        # Page selector
                        if total_pages > 1:
                            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="odometer_page")
                        else:
                            page = 1
                            
                        # Get the current page data
                        start_idx = (page - 1) * records_per_page
                        end_idx = min(start_idx + records_per_page, len(sorted_records))
                        
                        # Create a form for bulk updates
                        with st.form("odometer_update_form"):
                            # Store updates in a dictionary
                            odometer_updates = {}
                            
                            for i, record in enumerate(sorted_records[start_idx:end_idx]):
                                record_id = record.get('id', '')
                                date_str = record.get('date', '')
                                if isinstance(date_str, datetime):
                                    date_str = date_str.strftime('%Y-%m-%d')
                                
                                location = record.get('location', 'Unknown')
                                provider = record.get('provider', 'Unknown')
                                current_odometer = record.get('odometer', None)
                                
                                st.markdown(f"**{date_str}** | {provider} | {location}")
                                
                                # Use string format of the odometer for the input field
                                current_odometer_str = str(current_odometer) if current_odometer is not None else ""
                                
                                # Create an input field for this record
                                new_odometer = st.text_input(
                                    f"Odometer reading (km):",
                                    value=current_odometer_str,
                                    key=f"odometer_{record_id}_{i}"
                                )
                                
                                # Store the update if the field is not empty
                                if new_odometer.strip():
                                    try:
                                        # Try to convert to number
                                        odometer_value = float(new_odometer)
                                        # Only store if different from current value
                                        if current_odometer is None or odometer_value != current_odometer:
                                            odometer_updates[record_id] = odometer_value
                                    except ValueError:
                                        st.error(f"Invalid odometer value: {new_odometer}. Please enter a number.")
                                
                                st.markdown("---")
                            
                            # Submit button for the form
                            submit_button = st.form_submit_button("Save Odometer Readings")
                            
                            # Process form submission
                            if submit_button and odometer_updates:
                                # Load existing data
                                existing_data = load_charging_data(st.session_state.current_user_email)
                                updated_count = 0
                                
                                # Update odometer values
                                for record in existing_data:
                                    record_id = record.get('id', '')
                                    if record_id in odometer_updates:
                                        record['odometer'] = odometer_updates[record_id]
                                        updated_count += 1
                                
                                # Save updated data
                                if updated_count > 0:
                                    save_charging_data(existing_data, st.session_state.current_user_email)
                                    # Update main data
                                    st.session_state.charging_data = clean_charging_data(existing_data)
                                    st.success(f"Successfully updated odometer readings for {updated_count} records.")
                                    # Force refresh
                                    st.rerun()
                                else:
                                    st.info("No odometer readings were changed.")
                    else:
                        st.info("No records found matching your criteria or no data available.")
                    
                    # Tips section
                    with st.expander("Tips for entering odometer readings"):
                        st.markdown("""
                        ### Tips for accurate odometer readings:
                        
                        - Enter the odometer reading as displayed on your vehicle when charging
                        - Use consistent units (kilometers recommended)
                        - For best distance calculations between charges, enter readings for consecutive charging sessions
                        - The system will automatically calculate distance traveled between charging sessions when odometer readings are available
                        """)
                
                # Delete All Tab
                with data_mgmt_tabs[3]:
                    st.subheader("Delete All Data")
                    st.warning("This will permanently delete all your stored charging data. This action cannot be undone.")
                    
                    # Option to clear all data
                    if st.button("Clear All Stored Data", type="secondary"):
                        confirm = st.checkbox("I understand this will delete all my data", key="confirm_delete_all")
                        if confirm and st.button("Confirm Delete All Data", type="primary"):
                            if delete_charging_data(st.session_state.current_user_email):
                                st.success("All stored charging data has been cleared.")
                                st.session_state.charging_data = None
                                st.rerun()
                            else:
                                st.error("Failed to clear charging data.")
            else:
                st.info("No charging data is currently stored in the database.")
            
            # Option to enable incremental updates (only fetch new data)
            st.write("Update Options:")
            incremental_update = st.checkbox(
                "Enable incremental updates", 
                value=True,
                help="Only retrieve and process new charging data that hasn't been seen before."
            )
        
        # Fetch data button
        if st.button("Fetch Charging Data"):
            all_charging_data = []
            
            # EVCC CSV Processing (if file was uploaded)
            if 'uploaded_file' in locals() and uploaded_file is not None:
                with st.spinner("Processing EVCC CSV data..."):
                    try:
                        # Reset file pointer to beginning (in case it was previously read)
                        uploaded_file.seek(0)
                        
                        # Parse EVCC CSV data
                        evcc_data = parse_evcc_csv(uploaded_file, default_cost_per_kwh=evcc_cost_per_kwh)
                        
                        if evcc_data:
                            # Add a source marker to identify EVCC data
                            for item in evcc_data:
                                item['source'] = 'EVCC CSV'
                                # Always generate a fresh ID for EVCC data to avoid issues
                                item['id'] = generate_record_id(item)
                            
                            # If replace_evcc_data is checked, mark the data for replacement
                            if 'replace_evcc_data' in locals() and replace_evcc_data:
                                all_charging_data = evcc_data
                                st.session_state.replace_evcc_data = True
                                st.success(f"Successfully loaded {len(evcc_data)} charging sessions from EVCC CSV. Existing EVCC data will be replaced.")
                                
                                # Skip further data retrieval
                                skip_other_sources = True
                            else:
                                # Otherwise, add EVCC data to the combined dataset
                                all_charging_data.extend(evcc_data)
                                st.success(f"Successfully loaded {len(evcc_data)} charging sessions from EVCC CSV.")
                                
                                # Continue with other data sources
                                skip_other_sources = False
                        else:
                            st.warning("No valid charging data found in the EVCC CSV file.")
                            skip_other_sources = False
                    except Exception as e:
                        st.error(f"Error processing EVCC CSV: {str(e)}")
                        skip_other_sources = False
            else:
                skip_other_sources = False
            
            # PDF Receipt Processing (if files were uploaded)
            if 'uploaded_pdfs' in locals() and uploaded_pdfs and len(uploaded_pdfs) > 0:
                with st.spinner("Processing PDF receipts..."):
                    try:
                        # Parse PDF data
                        pdf_data = parse_multiple_pdfs(uploaded_pdfs)
                        
                        if pdf_data:
                            # If replace_pdf_data is checked, replace existing PDF data
                            if 'replace_pdf_data' in locals() and replace_pdf_data:
                                # Filter out any existing PDF data from all_charging_data
                                all_charging_data = [item for item in all_charging_data if item.get('source') != 'PDF Upload']
                            
                            # Add PDF data to combined dataset
                            all_charging_data.extend(pdf_data)
                            st.success(f"Successfully extracted data from {len(pdf_data)} PDF receipts.")
                        else:
                            st.warning("No charging data could be extracted from the PDF files.")
                    except Exception as e:
                        st.error(f"Error processing PDF files: {str(e)}")
            
            # Gmail Data Retrieval (skip if using only EVCC data)
            if not skip_other_sources:
                with st.spinner("Fetching email data..."):
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
                                    
                                    # Convert date objects to datetime for comparison
                                    start_datetime = datetime.combine(start_date, datetime.min.time()) if isinstance(start_date, date) else start_date
                                    end_datetime = datetime.combine(end_date, datetime.max.time()) if isinstance(end_date, date) else end_date
                                    
                                    if start_datetime <= email_date <= end_datetime:
                                        filtered_emails.append(email)
                            
                            emails_count = len(filtered_emails)
                            st.info(f"Found {emails_count} emails matching your criteria.")
                            
                            # Parse emails to extract charging data
                            with st.spinner("Parsing email data..."):
                                email_charging_data = parse_charging_emails(filtered_emails)
                                
                                if email_charging_data:
                                    all_charging_data.extend(email_charging_data)
                                    st.success(f"Successfully extracted data from {len(email_charging_data)} charging sessions in emails.")
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
                            st.error(f"Error fetching email data: {error_message}")
            
            # Tesla API Data Retrieval (if authenticated)
            if st.session_state.tesla_authenticated:
                with st.spinner("Fetching Tesla charging data..."):
                    try:
                        # Get Tesla charging history
                        tesla_client = st.session_state.tesla_client
                        
                        # Get vehicles
                        vehicles = tesla_client.get_vehicles()
                        if vehicles:
                            # Select first vehicle
                            tesla_client.select_vehicle()
                            
                            # Get charging history
                            charging_history = tesla_client.get_charging_history(
                                start_date=start_date,
                                end_date=end_date
                            )
                            
                            if charging_history:
                                # Format Tesla charging data to match app's format
                                tesla_charging_data = tesla_client.format_charging_data(charging_history)
                                
                                if tesla_charging_data:
                                    all_charging_data.extend(tesla_charging_data)
                                    st.success(f"Successfully retrieved {len(tesla_charging_data)} charging sessions from Tesla API.")
                                else:
                                    st.warning("No charging data could be extracted from Tesla API.")
                            else:
                                st.warning("No charging history found in Tesla API.")
                        else:
                            st.warning("No vehicles found in Tesla account.")
                    except Exception as e:
                        st.error(f"Error fetching Tesla data: {str(e)}")
            
            # Process combined data if any was retrieved
            if all_charging_data:
                with st.spinner("Processing charging data..."):
                    # Always load existing data first
                    existing_data = load_charging_data(st.session_state.current_user_email)
                    
                    # Check if incremental updates are enabled and if we have existing data
                    if ('incremental_update' in locals() and incremental_update) and existing_data:
                        # Check if we're replacing EVCC data
                        if hasattr(st.session_state, 'replace_evcc_data') and st.session_state.replace_evcc_data:
                            # Remove all existing EVCC data first
                            existing_data = [item for item in existing_data if item.get('source') != 'EVCC CSV']
                            st.info("Removing existing EVCC data before merging.")
                            # Reset the flag
                            st.session_state.replace_evcc_data = False
                            
                        # Merge new data with existing data (avoiding duplicates)
                        combined_data = merge_charging_data(existing_data, all_charging_data)
                        st.info(f"Merged {len(all_charging_data)} new charging sessions with {len(existing_data)} existing sessions.")
                        
                        # Update session with incremental count
                        new_sessions_count = len(combined_data) - len(existing_data)
                        if new_sessions_count > 0:
                            st.success(f"Added {new_sessions_count} new charging sessions.")
                        else:
                            st.info("No new charging sessions found.")
                            
                        # Clean and process the combined data
                        df = clean_charging_data(combined_data)
                        
                        # Save the updated data to persistent storage
                        save_charging_data(combined_data, st.session_state.current_user_email)
                    else:
                        # No existing data, just process and save the new data
                        df = clean_charging_data(all_charging_data)
                        save_charging_data(all_charging_data, st.session_state.current_user_email)
                        st.success(f"Saved {len(all_charging_data)} charging sessions to database.")
                    
                    # Store processed data in session state
                    st.session_state.charging_data = df
                    st.session_state.last_refresh = datetime.now()
                    st.success(f"Successfully processed data from {len(df)} total charging sessions.")
            else:
                # Check if we have existing data to load instead
                existing_data = load_charging_data(st.session_state.current_user_email)
                if existing_data:
                    with st.spinner("Loading stored data..."):
                        # Process the existing data
                        df = clean_charging_data(existing_data)
                        
                        # Store in session state
                        st.session_state.charging_data = df
                        st.session_state.last_refresh = datetime.now()
                        st.info(f"Loaded {len(df)} charging sessions from database.")
                else:
                    st.warning("No charging data was retrieved from any source.")
        
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
                        'map_view': {'visible': True, 'order': 8, 'name': 'Location Map'},
                    },
                    'layout': 'tabs',
                    'grid_columns': 2
                }
                st.rerun()

# Main content area
if st.session_state.authenticated:
    # Auto-fetch data when the user first logs in
    if 'auto_fetch_data' in st.session_state and st.session_state.auto_fetch_data:
        st.info("Automatically fetching your charging data...")
        
        # Set up default search parameters
        days_back = 90
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        search_query = "EV charging receipt OR Ampol AmpCharge OR charging session"
        incremental_update = True
        
        # Execute data fetch
        with st.spinner("Fetching email data..."):
            try:
                # Get emails
                gmail_client = st.session_state.gmail_client
                emails = gmail_client.get_emails(query=search_query)
                
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
                    
                    # Parse emails to extract charging data
                    with st.spinner("Parsing email data..."):
                        email_charging_data = parse_charging_emails(filtered_emails)
                        
                        if email_charging_data:
                            # Process and store the data
                            # Always load existing data from the database first
                            existing_data = load_charging_data(st.session_state.current_user_email)
                            
                            if incremental_update and (existing_data or st.session_state.charging_data is not None):
                                # Merge with new data
                                combined_data = merge_charging_data(existing_data, email_charging_data)
                                
                                # Save the combined data
                                save_charging_data(combined_data, st.session_state.current_user_email)
                                
                                # Process the data for display
                                df = clean_charging_data(combined_data)
                                st.session_state.charging_data = df
                                st.success(f"Successfully added {len(email_charging_data)} new charging sessions.")
                            else:
                                # Save just the new data
                                save_charging_data(email_charging_data, st.session_state.current_user_email)
                                
                                # Process the data for display
                                df = clean_charging_data(email_charging_data)
                                st.session_state.charging_data = df
                                st.success(f"Successfully loaded {len(email_charging_data)} charging sessions.")
                
                # Make sure to properly close the IMAP connection when done
                try:
                    gmail_client.close()
                except:
                    pass
                    
            except Exception as e:
                # On error, still try to close the connection
                try:
                    if 'gmail_client' in locals():
                        gmail_client.close()
                except:
                    pass
                    
                # Show error message
                error_message = str(e)
                if "LOGOUT" in error_message:
                    st.error("Connection error with Gmail. Try again later.")
                else:
                    st.error(f"Error fetching email data: {error_message}")
        
        # Reset the auto fetch flag
        st.session_state.auto_fetch_data = False
        
        # Update last refresh timestamp
        st.session_state.last_refresh = datetime.now()
        
        # Force page refresh to display data
        st.rerun()
            
    # Display data if available
    if st.session_state.charging_data is not None:
        data = st.session_state.charging_data
        
        # Initialize a provider filter in session state if it doesn't exist
        if 'provider_filter' not in st.session_state:
            st.session_state.provider_filter = "All"
        
        # Provider filtering
        st.header("Data Filtering")
        
        # Get unique providers from the data
        providers = ["All"] + sorted(data["provider"].unique().tolist())
        
        # Create a dropdown filter for providers
        selected_provider = st.selectbox(
            "Filter by provider:", 
            providers,
            index=providers.index(st.session_state.provider_filter)
        )
        
        # Store selected provider in session state
        st.session_state.provider_filter = selected_provider
        
        # Apply filter if a specific provider is selected
        if selected_provider != "All":
            filtered_data = data[data["provider"] == selected_provider]
        else:
            filtered_data = data
            
        # Use filtered data for statistics and visualizations
        data = filtered_data
            
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
        
        # Add predictive analysis charts for grid layout
        # Monthly cost forecast
        _, forecast_fig = forecast_monthly_cost(data)
        if forecast_fig:
            charts['monthly_cost_forecast'] = forecast_fig
            
        # Provider cost trends
        provider_trends_fig = predict_cost_by_provider(data)
        if provider_trends_fig:
            charts['provider_trend_prediction'] = provider_trends_fig
            
        # Usage prediction (default 30 days)
        _, usage_fig = usage_prediction(data)
        if usage_fig:
            charts['usage_prediction'] = usage_fig
        
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
                'provider_analysis': {'name': 'Provider Comparison', 'charts': ['provider_cost_comparison', 'provider_kwh_comparison']},
                'predictive_analysis': {'name': 'Future Predictions', 'charts': ['monthly_cost_forecast', 'provider_trend_prediction', 'usage_prediction']},
                'map_view': {'name': 'Location Map', 'charts': []},
                'network_map': {'name': 'Charging Network', 'charts': []},
                'raw_data': {'name': 'Raw Data', 'charts': []}
            }
            
            # Filter for at least one visible chart in each tab group
            visible_tabs = []
            for group_id, group in tab_groups.items():
                if group_id == 'raw_data' or group_id == 'map_view' or group_id == 'network_map' or any(chart_id in charts and 
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
                    
                    elif group['name'] == 'Provider Comparison':
                        # Create a 2-column layout for the provider comparison charts
                        if (st.session_state.dashboard_preferences['panels'].get('provider_cost_comparison', {}).get('visible', False) or
                            st.session_state.dashboard_preferences['panels'].get('provider_kwh_comparison', {}).get('visible', False)):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.session_state.dashboard_preferences['panels'].get('provider_cost_comparison', {}).get('visible', False):
                                    if 'provider_cost_comparison' in charts:
                                        st.subheader(st.session_state.dashboard_preferences['panels']['provider_cost_comparison']['name'])
                                        st.plotly_chart(charts['provider_cost_comparison'], use_container_width=True)
                            
                            with col2:
                                if st.session_state.dashboard_preferences['panels'].get('provider_kwh_comparison', {}).get('visible', False):
                                    if 'provider_kwh_comparison' in charts:
                                        st.subheader(st.session_state.dashboard_preferences['panels']['provider_kwh_comparison']['name'])
                                        st.plotly_chart(charts['provider_kwh_comparison'], use_container_width=True)
                    
                    elif group['name'] == 'Future Predictions':
                        st.subheader("Predictive Analysis for Future Costs")
                        st.write("Based on your historical charging data, here are predictions for future costs and usage patterns.")
                        
                        # Monthly cost forecast
                        if st.session_state.dashboard_preferences['panels'].get('monthly_cost_forecast', {}).get('visible', False):
                            st.markdown("### Monthly Cost Forecast")
                            st.write("Forecast of your monthly charging costs for the next 3 months.")
                            
                            with st.spinner("Generating monthly cost forecast..."):
                                # Generate the forecast
                                forecast_df, forecast_fig = forecast_monthly_cost(data)
                                
                                if forecast_fig:
                                    st.plotly_chart(forecast_fig, use_container_width=True)
                                    
                                    if forecast_df is not None:
                                        with st.expander("View forecast data"):
                                            st.dataframe(forecast_df)
                                else:
                                    st.info("Not enough data for monthly cost forecasting. Continue collecting data for at least 5 charging sessions.")
                        
                        # Provider cost trends prediction
                        if st.session_state.dashboard_preferences['panels'].get('provider_trend_prediction', {}).get('visible', False):
                            st.markdown("### Provider Cost Trends")
                            st.write("Predicted cost per kWh trends by provider over time.")
                            
                            with st.spinner("Analyzing provider cost trends..."):
                                # Generate provider cost trends
                                provider_trends_fig = predict_cost_by_provider(data)
                                
                                if provider_trends_fig:
                                    st.plotly_chart(provider_trends_fig, use_container_width=True)
                                else:
                                    st.info("Not enough data to predict provider cost trends. Try collecting more data from various providers.")
                        
                        # Usage prediction
                        if st.session_state.dashboard_preferences['panels'].get('usage_prediction', {}).get('visible', False):
                            st.markdown("### Charging Usage Prediction")
                            st.write("Prediction of your daily charging usage for the next 30 days.")
                            
                            # Add options for prediction
                            prediction_days = st.slider("Days to predict", 7, 90, 30)
                            
                            with st.spinner("Generating usage prediction..."):
                                # Generate usage prediction
                                usage_df, usage_fig = usage_prediction(data, future_days=prediction_days)
                                
                                if usage_fig:
                                    st.plotly_chart(usage_fig, use_container_width=True)
                                    
                                    if usage_df is not None:
                                        with st.expander("View predicted usage data"):
                                            st.dataframe(usage_df)
                                else:
                                    st.info("Not enough data for usage prediction. Continue collecting data for at least 10 charging sessions.")
                    
                    elif group['name'] == 'Location Map':
                        # Display the map and location statistics
                        display_charging_map(data)
                        
                    elif group['name'] == 'Charging Network':
                        # Display the interactive charging network map
                        display_charging_network_map()
                        
                    elif group['name'] == 'Raw Data':
                        st.subheader("Raw Data")
                        
                        # Add filters similar to grid view
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
                        
                        # Show data table
                        st.dataframe(filtered_data)
        
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
            
            # Add Map View section
            st.subheader("Charging Station Map")
            
            # Display the interactive map
            display_charging_map(data)
            
            # Add Charging Network Map section
            st.subheader("Charging Network Map")
            
            # Display the interactive charging network map
            display_charging_network_map()
            
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
