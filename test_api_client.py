"""
Test script for the EV Charging API client.
"""

import argparse
from api_client import EVChargingAPIClient
import json
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser(description='Test the EV Charging API client')
    parser.add_argument('--base-url', default='http://localhost:8000', help='Base URL of the API server')
    parser.add_argument('--api-key', default='ev-charging-api-key', help='API key for authentication')
    parser.add_argument('--email', help='Email address to filter data by user')
    parser.add_argument('--days', type=int, default=30, help='Number of days to look back for date filtering')
    
    args = parser.parse_args()
    
    # Create API client
    client = EVChargingAPIClient(base_url=args.base_url, api_key=args.api_key)
    
    try:
        print("Testing API client...")
        
        # Check API health
        print("\n1. Health check:")
        health = client.health_check()
        print(json.dumps(health, indent=2))
        
        # Get charging data with optional filtering
        print("\n2. Getting charging data:")
        
        # Set up parameters
        params = {}
        if args.email:
            params['email'] = args.email
            
        # Calculate dates for filtering (last N days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        
        data = client.get_charging_data(
            email=args.email,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        print(f"Retrieved {data.get('count', 0)} charging records")
        
        # Display first record if available
        if data.get('count', 0) > 0:
            print("\nSample record:")
            print(json.dumps(data['data'][0], indent=2))
        
        # Get summary statistics
        print("\n3. Getting charging summary:")
        summary = client.get_charging_summary(email=args.email)
        print(json.dumps(summary, indent=2))
        
        print("\nAPI client test completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()