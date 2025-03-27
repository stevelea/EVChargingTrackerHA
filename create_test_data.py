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
    
    # Define major Australian cities with their coordinates and specific charging stations
    locations = [
        {"name": "Sydney Olympic Park", "address": "1 Showground Rd, Sydney Olympic Park NSW 2127", "lat": -33.8472, "lon": 151.0694, "provider": "ChargePoint"},
        {"name": "Bondi Junction", "address": "Westfield Bondi Junction, 500 Oxford Street, Bondi Junction, NSW 2022", "lat": -33.8930, "lon": 151.2498, "provider": "Evie Networks"},
        {"name": "Sydney CBD", "address": "201 Sussex St, Sydney NSW 2000", "lat": -33.8699, "lon": 151.2044, "provider": "AmpCharge"},
        {"name": "Parramatta Westfield", "address": "159-175 Church St, Parramatta NSW 2150", "lat": -33.8152, "lon": 151.0011, "provider": "NRMA"},
        {"name": "Melbourne CBD", "address": "Secure Parking, 300 Flinders St, Melbourne VIC 3000", "lat": -37.8182, "lon": 144.9668, "provider": "Jolt"},
        {"name": "Chadstone Shopping Centre", "address": "1341 Dandenong Rd, Chadstone VIC 3148", "lat": -37.8883, "lon": 145.0839, "provider": "ChargeFox"},
        {"name": "Brisbane Airport", "address": "Airport Drive, Brisbane Airport QLD 4008", "lat": -27.4037, "lon": 153.1080, "provider": "Tesla"},
        {"name": "South Bank Brisbane", "address": "Stanley Place, South Brisbane QLD 4101", "lat": -27.4736, "lon": 153.0178, "provider": "Chargepod"},
        {"name": "Pacific Fair Gold Coast", "address": "Hooker Blvd, Broadbeach QLD 4218", "lat": -28.0327, "lon": 153.4256, "provider": "ChargePoint"},
        {"name": "Adelaide Central Market", "address": "44-60 Gouger St, Adelaide SA 5000", "lat": -34.9295, "lon": 138.5942, "provider": "Evie Networks"},
        {"name": "Marion Shopping Centre", "address": "297 Diagonal Rd, Oaklands Park SA 5046", "lat": -35.0173, "lon": 138.5557, "provider": "AmpCharge"},
        {"name": "Perth CBD", "address": "Murray Street Car Park, 68 Murray St, Perth WA 6000", "lat": -31.9518, "lon": 115.8613, "provider": "NRMA"},
        {"name": "Joondalup Shopping Centre", "address": "420 Joondalup Drive, Joondalup WA 6027", "lat": -31.7415, "lon": 115.7680, "provider": "Jolt"},
        {"name": "Hobart CBD", "address": "55 Murray St, Hobart TAS 7000", "lat": -42.8825, "lon": 147.3281, "provider": "ChargeFox"},
        {"name": "Launceston", "address": "71 Paterson St, Launceston TAS 7250", "lat": -41.4370, "lon": 147.1392, "provider": "Tesla"},
        {"name": "Canberra Centre", "address": "148 Bunda St, Canberra ACT 2601", "lat": -35.2802, "lon": 149.1317, "provider": "ChargePoint"},
        {"name": "Darwin Waterfront", "address": "7 Kitchener Dr, Darwin City NT 0800", "lat": -12.4709, "lon": 130.8456, "provider": "Evie Networks"},
        {"name": "Maroochydore Sunshine Plaza", "address": "154-164 Horton Parade, Maroochydore QLD 4558", "lat": -26.6529, "lon": 153.0856, "provider": "AmpCharge"},
        {"name": "Cairns Shopping Centre", "address": "1-21 McLeod St, Cairns QLD 4870", "lat": -16.9252, "lon": 145.7692, "provider": "Jolt"},
        {"name": "Newcastle Westfield", "address": "15 Lambton Rd, Broadmeadow NSW 2292", "lat": -32.9182, "lon": 151.7365, "provider": "ChargeFox"},
        {"name": "Wollongong Central", "address": "200 Crown St, Wollongong NSW 2500", "lat": -34.4264, "lon": 150.8943, "provider": "Tesla"},
        {"name": "Geelong Westfield", "address": "95 Malop St, Geelong VIC 3220", "lat": -38.1484, "lon": 144.3598, "provider": "NRMA"},
        {"name": "Townsville", "address": "202 Ross River Rd, Aitkenvale QLD 4814", "lat": -19.2820, "lon": 146.7820, "provider": "Chargepod"},
        {"name": "Port Macquarie", "address": "40 Gordon St, Port Macquarie NSW 2444", "lat": -31.4330, "lon": 152.9070, "provider": "ChargePoint"},
        {"name": "Ballarat", "address": "320 Gillies St, Wendouree VIC 3355", "lat": -37.5425, "lon": 143.8425, "provider": "Evie Networks"}
    ]
    
    # Create 30 charging sessions over the past 60 days
    charging_data = []
    
    # Starting odometer reading
    current_odometer = 15000  # Starting at 15,000 km
    
    # Create sessions in chronological order (oldest first)
    for i in range(30):
        # Sequential date distribution over 60 days
        days_ago = 60 - (i * 2)  # Every 2 days on average
        # Add some randomness to the days
        days_ago = max(1, days_ago + random.randint(-1, 1))
        charge_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        
        # Random location, with more weight to some frequent locations
        # Make the first few locations closer together, then branch out
        if i < 10:
            # More likely to be in the same city at the beginning
            location = random.choice(locations[:5])
        else:
            # Later trips can be anywhere
            location = random.choice(locations)
        
        # Random charging amount and cost (more realistic for EV)
        energy_kwh = round(random.uniform(20.0, 60.0), 2)
        
        # Different cost rates by provider
        provider_rates = {
            "ChargePoint": (0.48, 0.52),
            "Evie Networks": (0.50, 0.55),
            "AmpCharge": (0.52, 0.58),
            "NRMA": (0.30, 0.35),  # Cheaper
            "Jolt": (0.45, 0.49),
            "ChargeFox": (0.49, 0.53),
            "Tesla": (0.58, 0.65),  # More expensive
            "Chargepod": (0.47, 0.51)
        }
        
        # Get rate range for this provider
        rate_range = provider_rates.get(location["provider"], (0.45, 0.60))
        cost_per_kwh = round(random.uniform(rate_range[0], rate_range[1]), 2)
        cost = round(energy_kwh * cost_per_kwh, 2)
        
        # Increase the odometer reading based on realistic travel
        # Average 50-80km between charges with some variation
        distance_driven = random.randint(40, 100)
        current_odometer += distance_driven
        
        # Create charging record
        charging_record = {
            "date": charge_date.strftime("%Y-%m-%d %H:%M:%S"),
            "location": location["name"],
            "address": location["address"],
            "latitude": location["lat"],
            "longitude": location["lon"],
            "energy_kwh": energy_kwh,
            "cost": cost,
            "cost_per_kwh": cost_per_kwh,
            "provider": location["provider"],
            "odometer": current_odometer,
            "source": "Test Data",
            "id": f"test-{i+1}"
        }
        
        charging_data.append(charging_record)
    
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