"""
Create sample charging data for testing the historical charging locations feature
"""

import pandas as pd
import random
import datetime
import os
import data_storage
import json

def create_sample_charging_data():
    """
    Create sample charging data for testing with realistic Australian locations
    """
    # Ensure data directory exists
    data_storage.ensure_data_directory()
    
    # Create empty charging data (no locations)
    charging_data = []
    
    # Set up the test email address in session state
    email_address = "test@example.com"
    import streamlit as st
    st.session_state["email_address"] = email_address
    
    # Sort by date (newest first)
    charging_data.sort(key=lambda x: x["date"], reverse=True)
    
    # Save to test user data file
    email_address = "test@example.com"
    data_storage.save_charging_data(charging_data, email_address)
    
    print(f"Created {len(charging_data)} test charging records for email: {email_address}")
    
    # Also save the test email in the session state
    import streamlit as st
    st.session_state["email_address"] = email_address
    
    return charging_data

if __name__ == "__main__":
    # Create sample data
    charging_data = create_sample_charging_data()
    
    # Print sample data
    print(json.dumps(charging_data[:3], indent=2))