# EV Charging Tracker Integration for Home Assistant

This custom integration allows you to integrate your EV Charging Tracker data into Home Assistant. It pulls data from the EV Charging Tracker API server and creates sensor entities in Home Assistant to display your charging data, which updates automatically every 60 seconds.

## Prerequisites

- Home Assistant instance (Core, OS, Container, or Supervised)
- EV Charging Tracker application running with the API server enabled (running on port 5001)
- Network access from Home Assistant to the EV Charging Tracker application

## Installation

### Manual Installation

1. Copy the `evchargingtracker` folder to your Home Assistant's custom_components directory:
   ```bash
   cp -r custom_components/evchargingtracker /path/to/your/homeassistant/custom_components/
   ```

2. Restart Home Assistant.

### HACS Installation (Coming Soon)

1. Add this repository as a custom repository in HACS.
2. Install the "EV Charging Tracker" integration.
3. Restart Home Assistant.

## Configuration

1. Go to your Home Assistant instance.
2. Navigate to **Configuration** > **Integrations**.
3. Click the **+ ADD INTEGRATION** button.
4. Search for "EV Charging Tracker" and select it.
5. Enter the following information:
   - **Host**: The hostname or IP address of your EV Charging Tracker server (e.g., `localhost` or `192.168.1.10`)
   - **Port**: The port of the API server (default is `5001`)
   - **API Key**: (Optional) If your API requires an API key

6. Click **Submit** to add the integration.

## Available Entities

After setup, the following sensor entities will be available in Home Assistant:

### Summary Sensors
- **Total Energy**: Total energy consumed in all charging sessions (kWh)
- **Total Cost**: Total cost of all charging sessions ($)
- **Average Cost per kWh**: Average cost per kWh across all sessions ($/kWh)
- **Charging Session Count**: Number of charging sessions

### Latest Charging Session Sensors
- **Last Charging Energy**: Energy delivered in the latest charging session (kWh)
- **Last Charging Cost**: Cost of the latest charging session ($)
- **Last Charging Location**: Location of the latest charging session
- **Last Charging Date**: Date and time of the latest charging session
- **Last Peak Power**: Peak power of the latest charging session (kW)
- **Last Cost per kWh**: Cost per kWh of the latest charging session ($/kWh)
- **Last Provider**: Provider of the latest charging session

## Troubleshooting

If you encounter issues:

1. Check that the EV Charging Tracker API server is running and accessible.
2. Verify the API server is running on the expected port (default 8000).
3. Check the Home Assistant logs for error messages related to the integration.
4. Make sure your network allows connections from Home Assistant to the EV Charging Tracker server.

## Support

For issues or feature requests, please open an issue on GitHub.

## License

This project is licensed under the MIT License.