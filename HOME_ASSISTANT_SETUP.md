# Setting Up EV Charging Tracker with Home Assistant

This guide explains how to integrate your EV Charging Tracker app with Home Assistant, allowing you to view your charging data directly in your smart home dashboard.

## Overview

We provide two different Home Assistant integrations:

1. **Standard Integration** (`evchargingtracker`)
   - Connects to your EV Charging Tracker API
   - Retrieves actual charging data from your app
   - Best for locally hosted instances or direct API access

2. **Replit-Specific Integration** (`evchargingtracker_replit`)
   - Works specifically with Replit-hosted EV Charging Tracker apps
   - Uses simulated data representation to avoid Replit's API limitations
   - No configuration needed - works out of the box

## Step 1: Choose the Right Integration

- If you're hosting your EV Charging Tracker locally or on a server with direct API access, use the **Standard Integration**.
- If you're hosting on Replit, use the **Replit-Specific Integration** to avoid API connectivity issues.

## Step 2: Download the Integration Package

Run the included helper script to create a package with both integrations:

```bash
python create_ha_component_package.py
```

This will create a ZIP file in the `downloads` folder named `evchargingtracker_ha_package.zip`.

## Step 3: Extract the Package

Download and extract the ZIP file to get access to both integration folders:
- `evchargingtracker` (Standard Integration)
- `evchargingtracker_replit` (Replit-Specific Integration)

## Step 4: Install the Integration in Home Assistant

1. Choose **only one** of the integration folders based on your setup (see Step 1).
2. Copy the chosen folder to your Home Assistant `custom_components` directory:

   - For Home Assistant OS/Supervised:
     ```bash
     # Use Samba add-on or SSH
     cp -r evchargingtracker /config/custom_components/
     # OR
     cp -r evchargingtracker_replit /config/custom_components/
     ```

   - For Home Assistant Core:
     ```bash
     cp -r evchargingtracker ~/.homeassistant/custom_components/
     # OR
     cp -r evchargingtracker_replit ~/.homeassistant/custom_components/
     ```

   - For Home Assistant Container:
     Copy to your mounted configuration volume's custom_components directory

3. Restart Home Assistant completely.

## Step 5: Add the Integration in Home Assistant UI

1. Go to your Home Assistant instance
2. Navigate to **Configuration** > **Integrations**
3. Click the **+ ADD INTEGRATION** button
4. Search for the integration name:
   - `EV Charging Tracker` for the standard integration
   - `EV Charging Tracker Replit` for the Replit-specific integration
5. Select the integration

### For Standard Integration Configuration:

Enter the following details:
- **Host**: Your EV Charging Tracker server address (e.g., `localhost`, `192.168.1.10`, or your Replit URL)
- **Port**: Always use `5000` (both local and Replit deployments use this port)
- **API Key**: (Optional) Default is `ev-charging-api-key` - only change if you've modified the API key in your app

### For Replit-Specific Integration:

No configuration needed! Just click to install it.

## Step 6: Using the Integration

After installation, the following sensor entities will be available in Home Assistant:

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

### Standard Integration Issues

If you have trouble connecting to the API:

1. Verify your EV Charging Tracker app is running
2. Confirm the API server is accessible from Home Assistant
3. Check that you're using port 5000
4. Verify the API key matches what your app is using

### Replit-Specific Integration Issues

The Replit integration doesn't connect to an API, so connectivity issues shouldn't occur. If you have problems:

1. Make sure the integration folder is in the correct location
2. Restart Home Assistant completely

## Need Help?

If you continue to experience issues, check the individual README files in the integration folders for more detailed information and troubleshooting tips.