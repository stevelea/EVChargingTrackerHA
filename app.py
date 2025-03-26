import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

from gmail_api import GmailClient
from data_parser import parse_charging_emails
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
        search_label = st.text_input("Email search term", "EV charging receipt")
        
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
                            if email['date'] and start_date <= email['date'] <= end_date:
                                filtered_emails.append(email)
                        
                        emails_count = len(filtered_emails)
                        st.info(f"Found {emails_count} emails matching your criteria.")
                        
                        # Parse emails to extract charging data
                        with st.spinner("Parsing email data..."):
                            charging_data = parse_charging_emails(filtered_emails)
                            
                            if charging_data:
                                # Store data in session state
                                st.session_state.charging_data = pd.DataFrame(charging_data)
                                st.session_state.last_refresh = datetime.now()
                                st.success(f"Successfully extracted data from {len(charging_data)} charging sessions.")
                            else:
                                st.warning("No charging data could be extracted from the emails.")
                    else:
                        st.warning("No emails found matching your search criteria.")
                    
                    # Close the IMAP connection when done
                    gmail_client.close()
                        
                except Exception as e:
                    st.error(f"Error fetching data: {str(e)}")
        
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

# Main content area
if st.session_state.authenticated:
    if st.session_state.charging_data is not None:
        data = st.session_state.charging_data
        
        # Summary statistics
        st.header("Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sessions", len(data))
        
        with col2:
            total_kwh = data['total_kwh'].sum()
            st.metric("Total kWh", f"{total_kwh:.2f}")
        
        with col3:
            total_cost = data['total_cost'].sum()
            st.metric("Total Cost", f"${total_cost:.2f}")
        
        with col4:
            avg_cost_per_kwh = total_cost / total_kwh if total_kwh > 0 else 0
            st.metric("Avg. Cost per kWh", f"${avg_cost_per_kwh:.2f}")
        
        # Visualization tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Time Series", "Charging Statistics", "Cost Analysis", "Raw Data"])
        
        with tab1:
            st.subheader("Charging Sessions Over Time")
            charts = create_visualizations(data)
            st.plotly_chart(charts['time_series'], use_container_width=True)
        
        with tab2:
            st.subheader("Charging Power Distribution")
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(charts['peak_kw_histogram'], use_container_width=True)
            
            with col2:
                st.plotly_chart(charts['kwh_by_location'], use_container_width=True)
                
            st.plotly_chart(charts['charging_duration'], use_container_width=True)
        
        with tab3:
            st.subheader("Cost Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(charts['cost_time_series'], use_container_width=True)
            
            with col2:
                st.plotly_chart(charts['cost_per_kwh'], use_container_width=True)
                
            st.plotly_chart(charts['cost_by_location'], use_container_width=True)
        
        with tab4:
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
                filtered_data = filtered_data[
                    (filtered_data['date'] >= start_date) & 
                    (filtered_data['date'] <= end_date)
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
