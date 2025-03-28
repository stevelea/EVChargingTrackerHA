"""
Example usage of the EV Charging API client
"""

import sys
import os
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

# Add parent directory to path so we can import the API client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_client import EVChargingAPIClient

# Configuration
API_BASE_URL = "http://localhost:5001"
API_KEY = "ev-charging-api-key"  # Default API key
EMAIL = "test@example.com"

def plot_charging_history(data):
    """
    Plot charging history from the API data.
    """
    # Create DataFrame from data
    df = pd.DataFrame(data["data"])
    
    # Convert date strings to datetime objects
    df["date"] = pd.to_datetime(df["date"])
    
    # Ensure columns are numeric
    numeric_cols = ["total_kwh", "total_cost", "peak_kw", "cost_per_kwh"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Sort by date
    df = df.sort_values("date")
    
    # Plot charging history
    plt.figure(figsize=(14, 8))
    
    # Plot total energy over time
    plt.subplot(2, 1, 1)
    plt.plot(df["date"], df["total_kwh"], marker="o", linestyle="-", color="blue")
    plt.title("EV Charging Energy Over Time")
    plt.ylabel("Energy (kWh)")
    plt.grid(True)
    
    # Plot total cost over time
    plt.subplot(2, 1, 2)
    plt.plot(df["date"], df["total_cost"], marker="o", linestyle="-", color="red")
    plt.title("EV Charging Cost Over Time")
    plt.ylabel("Cost ($)")
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig("charging_history.png")
    print("Plot saved as charging_history.png")

def analyze_provider_comparison(data):
    """
    Analyze and compare charging providers.
    """
    # Create DataFrame from data
    df = pd.DataFrame(data["data"])
    
    # Group by provider
    provider_stats = df.groupby("provider").agg({
        "total_kwh": ["sum", "mean", "count"],
        "total_cost": ["sum", "mean"],
        "cost_per_kwh": "mean",
        "peak_kw": "max"
    }).reset_index()
    
    # Flatten the multi-level columns
    provider_stats.columns = [
        "_".join(col).strip("_") for col in provider_stats.columns.values
    ]
    
    # Calculate average cost per kWh for each provider
    provider_stats["avg_cost_per_kwh"] = provider_stats["total_cost_sum"] / provider_stats["total_kwh_sum"]
    
    # Sort by number of charging sessions
    provider_stats = provider_stats.sort_values("total_kwh_count", ascending=False)
    
    # Print the results
    print("\nProvider Comparison:")
    print("====================")
    
    for _, row in provider_stats.iterrows():
        provider = row["provider"]
        count = int(row["total_kwh_count"])
        total_kwh = round(row["total_kwh_sum"], 2)
        total_cost = round(row["total_cost_sum"], 2)
        avg_cost = round(row["avg_cost_per_kwh"], 3)
        max_power = round(row["peak_kw_max"], 1)
        
        print(f"\n{provider} ({count} sessions):")
        print(f"  Total Energy: {total_kwh} kWh")
        print(f"  Total Cost: ${total_cost}")
        print(f"  Avg Cost per kWh: ${avg_cost}/kWh")
        print(f"  Max Power: {max_power} kW")

def main():
    # Create client instance
    client = EVChargingAPIClient(
        base_url=API_BASE_URL,
        api_key=API_KEY
    )
    
    try:
        # Check if the API is running
        health = client.health_check()
        print(f"API Status: {health['status']} (as of {health['timestamp']})")
        
        # Get charging data from the last 180 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        print(f"\nRetrieving charging data from {start_date.date()} to {end_date.date()}...")
        data = client.get_charging_data(
            email=EMAIL,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        print(f"Retrieved {data.get('count', 0)} charging records")
        
        # Get summary statistics
        print("\nRetrieving charging summary...")
        summary = client.get_charging_summary(email=EMAIL)
        
        # Print summary information
        print("\nCharging Summary:")
        print("================")
        print(f"Total Records: {summary.get('record_count', 0)}")
        print(f"Date Range: {summary.get('date_range', {}).get('first_date')} to {summary.get('date_range', {}).get('last_date')}")
        print(f"Total Energy: {round(summary.get('total_energy_kwh', 0), 2)} kWh")
        print(f"Total Cost: ${round(summary.get('total_cost', 0), 2)}")
        print(f"Average Cost per kWh: ${round(summary.get('avg_cost_per_kwh', 0), 3)}/kWh")
        print(f"Unique Locations: {summary.get('locations', 0)}")
        print(f"Unique Providers: {summary.get('providers', 0)}")
        
        # Top providers
        print("\nTop Providers by Energy:")
        for provider in summary.get('top_providers', []):
            print(f"  {provider['provider']}: {round(provider['total_kwh'], 2)} kWh")
            
        # Top locations
        print("\nTop Locations by Energy:")
        for location in summary.get('top_locations', []):
            print(f"  {location['location']}: {round(location['total_kwh'], 2)} kWh")
        
        # Create visualizations if we have data
        if data.get('count', 0) > 0:
            # Plot charging history
            plot_charging_history(data)
            
            # Analyze provider comparison
            analyze_provider_comparison(data)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()