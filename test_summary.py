#!/usr/bin/env python3

from api_client import EVChargingAPIClient

def main():
    client = EVChargingAPIClient(base_url='http://localhost:8000', api_key='ev-charging-api-key')
    summary = client.get_charging_summary()
    
    print(f"Charging Summary:")
    print(f"Total Energy: {summary.get('total_energy_kwh', 0)} kWh")
    print(f"Total Cost: ${summary.get('total_cost', 0)}")
    print(f"Average Cost per kWh: ${summary.get('average_cost_per_kwh', 0)}")
    print(f"Number of Sessions: {summary.get('charging_sessions', 0)}")

if __name__ == "__main__":
    main()