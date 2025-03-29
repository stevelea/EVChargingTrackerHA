# EV Charging Tracker - Home Assistant Integration Package

This package contains two different Home Assistant integrations for the EV Charging Tracker application:

1. **Standard Integration** (`evchargingtracker`) - For connecting to locally hosted instances or direct API access
2. **Replit-Specific Integration** (`evchargingtracker_replit`) - Specifically designed to work with Replit-hosted instances

## Which Integration Should I Use?

### Use the Standard Integration (`evchargingtracker`) if:

- You're running the EV Charging Tracker locally on your network
- You're hosting the EV Charging Tracker on a server with direct API access
- You need actual data from your EV Charging Tracker instance

### Use the Replit-Specific Integration (`evchargingtracker_replit`) if:

- Your EV Charging Tracker is hosted on Replit
- You're experiencing issues connecting to the API endpoints on Replit
- You want to see how the integration would work without an actual API connection

## Installation Instructions

### Step 1: Choose Your Integration

Decide which integration you want to use based on your setup (see above).

### Step 2: Copy Files to Home Assistant

1. Copy **only one** of the integration folders to your Home Assistant custom_components directory:

   **For Standard Integration:**
   ```bash
   cp -r evchargingtracker /path/to/your/homeassistant/custom_components/
   ```

   **For Replit-Specific Integration:**
   ```bash
   cp -r evchargingtracker_replit /path/to/your/homeassistant/custom_components/
   ```

2. Restart Home Assistant.

### Step 3: Add the Integration

1. Go to your Home Assistant instance.
2. Navigate to **Configuration** > **Integrations**.
3. Click the **+ ADD INTEGRATION** button.
4. Search for the integration name and select it:
   - "EV Charging Tracker" for the standard integration
   - "EV Charging Tracker Replit" for the Replit-specific integration

5. Enter the configuration details:
   - For Standard Integration: Host, Port (5000), and optional API key
   - For Replit Integration: No configuration needed

6. Click **Submit** to add the integration.

## Standard Integration Configuration

For the standard integration, you'll need to provide:

- **Host**: The hostname or IP address of your EV Charging Tracker server (e.g., `localhost` or `192.168.1.10` or `ev-charging-tracker-stevelea1.replit.app`)
- **Port**: The port of the API server (always use `5000` for both local and Replit deployments)
- **API Key**: (Optional) The default API key is `ev-charging-api-key`

## Replit Integration Configuration

The Replit-specific integration requires no configuration - it works out of the box.

## Troubleshooting

### Standard Integration Issues

If you're having trouble connecting to the API:

1. **Check the API server is running**: Make sure the EV Charging Tracker API is running and accessible.
2. **Verify connectivity**: Ensure Home Assistant can reach the API server.
3. **Check port settings**: Confirm you're using port 5000 for the connection.
4. **Verify API key**: Make sure you're using the correct API key.

### Replit Integration Issues

The Replit integration doesn't connect to any API, so connectivity issues shouldn't occur. If you have problems:

1. **Check the integration is installed correctly**: Verify the folder is in the right location.
2. **Restart Home Assistant**: Make sure you've completely restarted after installation.

## For More Information

See the individual README files in each integration folder for more detailed documentation.
