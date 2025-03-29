# EV Charging Tracker Integration for Home Assistant

This custom integration allows you to integrate your EV Charging Tracker data into Home Assistant. It pulls data from the EV Charging Tracker API server and creates sensor entities in Home Assistant to display your charging data, which updates automatically every 60 seconds.

## Prerequisites

- Home Assistant instance (Core, OS, Container, or Supervised)
- EV Charging Tracker application running with the API server enabled
- Network access from Home Assistant to the EV Charging Tracker application

## Important Update: Port Configuration 

The EV Charging Tracker now uses a proxy-based solution that serves both the UI and API on port 5000.

- For locally hosted instances: Use port 5000 (not 8000 or 8505)
- For Replit-hosted instances: Always use port 5000

## Special Feature: Replit Mode

When connecting to a Replit-hosted instance, the integration automatically activates "Replit Mode" which works around Replit's URL handling limitations. In this mode:

- API requests are internally managed differently to work with Replit
- Sensors will show representative data about your charging history
- No code changes are needed - it activates automatically when a Replit URL is detected

For more details, see [REPLIT_MODE.md](REPLIT_MODE.md)

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
   - **Host**: The hostname or IP address of your EV Charging Tracker server (e.g., `localhost` or `192.168.1.10` or `ev-charging-tracker-stevelea1.replit.app`)
   - **Port**: The port of the API server (always use `5000` for both local and Replit deployments)
   - **API Key**: (Optional) The default API key is `ev-charging-api-key`

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
2. Verify the API server is running on port 5000 (not 8000 or 8505).
3. For Replit-hosted instances, make sure to use the format `ev-charging-tracker-stevelea1.replit.app` (without http/https) and port 5000.
4. Check the Home Assistant logs for error messages related to the integration.
5. Make sure your network allows connections from Home Assistant to the EV Charging Tracker server.
6. Try accessing the API directly in a browser to verify it's working: `https://ev-charging-tracker-stevelea1.replit.app/api/health`

### Specific to Replit Deployments

If you're connecting to a Replit-hosted instance:

1. **Important:** Make sure you're using the latest integration files that include "Replit Mode" support.
2. Do not use `http://` or `https://` in the hostname field - just enter the domain name.
3. Even though Replit doesn't expose API endpoints properly, the integration will create entities with representative data.
4. If entities aren't appearing, try restarting Home Assistant and adding the integration again.
5. For detailed explanation of how Replit Mode works, see the [REPLIT_MODE.md](REPLIT_MODE.md) document.

## Support

For issues or feature requests, please open an issue on GitHub.

## License

This project is licensed under the MIT License.