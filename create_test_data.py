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
    
    # Create sample charging data with realistic locations
    charging_data = []
    
    # List of realistic Australian EV charging locations
    locations = [
        "AmpCharge Waitara, Pacific Highway 59-61, Waitara 2077",
        "bp pulse Beresfield, John Renshaw Drive Beresfield, New South Wales 2322",
        "Evie Networks Warners Bay, 240 Hillsborough Rd Warners Bay, NSW 2282",
        "ChargePoint Sydney, 155 George Street, Sydney NSW 2000",
        "Home Charging Station",
        "NRMA Fast Charger, Pacific Highway, Coffs Harbour NSW 2450",
        "Chargefox Ultra-Rapid, M1 Pacific Motorway, Knockrow NSW 2479",
        "Evie Networks Gold Coast, Pacific Fair Shopping Centre, Broadbeach QLD 4218"
    ]
    
    # List of EV charging providers
    providers = [
        "AmpCharge", 
        "BP Pulse", 
        "Evie Networks", 
        "ChargePoint", 
        "NRMA", 
        "Chargefox",
        "Tesla Supercharger",
        "EVCC"
    ]
    
    # Generate 30 records spanning the last 90 days
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=90)
    
    for i in range(30):
        # Random date within range
        days_ago = random.randint(0, 90)
        charge_date = end_date - datetime.timedelta(days=days_ago)
        
        # Random location and provider
        location = random.choice(locations)
        provider = random.choice(providers)
        
        # If it's a home charge, set provider to EVCC
        if location == "Home Charging Station":
            provider = "EVCC"
            source = "EVCC CSV"
        else:
            source = "Email"
        
        # Random energy and cost values
        energy_kwh = round(random.uniform(5.0, 50.0), 2)
        cost_per_kwh = round(random.uniform(0.30, 0.70), 2)
        total_cost = round(energy_kwh * cost_per_kwh, 2)
        peak_kw = round(random.uniform(7.0, 150.0), 1)
        
        # Create charging record
        record = {
            "date": charge_date.date().isoformat(),
            "time": f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00",
            "location": location,
            "provider": provider,
            "total_kwh": energy_kwh,
            "peak_kw": peak_kw,
            "cost_per_kwh": cost_per_kwh,
            "total_cost": total_cost,
            "duration": f"{random.randint(20, 120)} min",
            "source": source,
            "id": f"sample-record-{i}"
        }
        
        # Add coordinates for non-home locations
        if location != "Home Charging Station":
            # Random coordinates near Sydney, Australia
            record["latitude"] = -33.8688 + random.uniform(-1.0, 1.0)
            record["longitude"] = 151.2093 + random.uniform(-1.0, 1.0)
        
        charging_data.append(record)
    
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