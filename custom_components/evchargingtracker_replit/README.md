# EV Charging Tracker Replit Integration for Home Assistant

This is a special version of the EV Charging Tracker integration specifically designed to work with Replit-hosted instances of the EV Charging Tracker application.

## Background

When hosting the EV Charging Tracker application on Replit, there's a fundamental limitation: **all requests to the public Replit URL return Streamlit HTML content instead of the API's JSON responses**. This happens even when using the proxy approach that works locally.

This special integration works around this limitation by providing representative data without trying to connect to the actual API.

## Installation

1. Copy the `evchargingtracker_replit` folder to your Home Assistant's custom_components directory:
   ```bash
   cp -r custom_components/evchargingtracker_replit /path/to/your/homeassistant/custom_components/
   ```

2. Restart Home Assistant.

## Configuration

1. Go to your Home Assistant instance.
2. Navigate to **Configuration** > **Integrations**.
3. Click the **+ ADD INTEGRATION** button.
4. Search for "EV Charging Tracker Replit" and select it.
5. Enter the following information:
   - **Host**: `ev-charging-tracker-stevelea1.replit.app` (or your Replit app domain)
   - **Port**: `5000` (this is required in the form but doesn't affect functionality)
   - **API Key**: `ev-charging-api-key` (or any value, as it's not used)

6. Click **Submit** to add the integration.

## Features

This integration provides:

- Representative data for all the same sensors as the regular EV Charging Tracker integration
- Automatic updating of values to simulate real data changes
- All sensor entities are marked with "simulated: true" and "replit_mode: true" attributes for transparency

## Differences from the Regular Integration

- This integration does not connect to the API at all - it generates representative data locally
- The data is not based on your actual charging history, but uses plausible demonstration data
- All data has timestamps that update in real-time
- The integration will work regardless of the state of your Replit-hosted application

## When to Use This Integration

Use this integration when:

1. Your EV Charging Tracker is hosted on Replit.com
2. You want to see how the sensors would appear in Home Assistant
3. You're developing a dashboard or automation that will eventually use real data

## When to Use the Regular Integration

Use the regular `evchargingtracker` integration when:

1. Your EV Charging Tracker is hosted locally or on a server with proper API access
2. You need to see your actual charging data in Home Assistant
3. You're not using Replit as your hosting platform

## Troubleshooting

If you encounter issues:

1. Make sure you've installed the integration in the correct directory
2. Verify that you're using "EV Charging Tracker Replit" (not the regular integration)
3. Restart Home Assistant after installation
4. Check the Home Assistant logs for any error messages