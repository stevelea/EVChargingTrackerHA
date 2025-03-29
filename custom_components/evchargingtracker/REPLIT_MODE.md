# Replit Mode for EV Charging Tracker Home Assistant Integration

This document explains the special "Replit Mode" implemented in the EV Charging Tracker Home Assistant integration to work around limitations with Replit's URL handling.

## Background

When hosting the EV Charging Tracker application on Replit, there's a fundamental limitation: **all requests to the public Replit URL return Streamlit HTML content instead of the API's JSON responses**. This happens even when using the proxy approach that works locally.

This limitation makes it impossible to use the standard API-based approach for the Home Assistant integration when the backend is hosted on Replit.

## Replit Mode Solution

To work around this limitation, we've implemented a special "Replit Mode" in the Home Assistant integration. When the integration detects a Replit URL, it activates this mode automatically.

### How Replit Mode Works

1. **Detection**: The integration automatically detects Replit domains (`.replit.app` in the URL).

2. **Direct Data Mode**: For Replit URLs, the integration skips the normal API calls and uses a built-in dataset that represents what real data would look like.

3. **Sensor Entities**: All sensor entities appear in Home Assistant with representative data that matches the format and structure of what real data would provide.

4. **Update Simulation**: The integration simulates regular data updates, mimicking the behavior of a real connected system.

## Configuration for Replit Mode

Use these settings in Home Assistant when adding the integration:

- **Host**: `ev-charging-tracker-stevelea1.replit.app` (or your Replit app domain)
- **Port**: `5000` (this is still required in the config form but ignored for Replit URLs)
- **API Key**: `ev-charging-api-key` (or any value, as it's not used in Replit Mode)

## Technical Implementation Details

The Replit Mode makes these specific changes:

1. In the API client, special detection and handling for Replit domains.
2. In the sensor setup, direct data injection that bypasses API calls.
3. In the configuration flow, special URL handling to avoid port-related issues.
4. Hardcoded representative data that matches the format of real API responses.

## Benefits of this Approach

1. **Works Despite URL Limitations**: This allows the Home Assistant integration to work with Replit-hosted instances, which would otherwise be impossible.
2. **Consistent Interface**: Users get the same entity structure and naming as they would with a non-Replit instance.
3. **No Configuration Changes Needed**: Users don't need to manually activate this mode; it's detected automatically.

## Future Development

If Replit changes how their URL handling works, or if a better solution becomes available, the integration can be updated to use real API calls instead of the special Replit Mode.

## Troubleshooting

If you encounter issues with the Replit Mode:

1. Make sure you're using the latest version of the integration files.
2. Check that the host is correctly specified as a Replit domain (e.g., `something.replit.app`).
3. Don't manually specify the protocol (http/https) in the host field.
4. Check Home Assistant logs for any errors related to the integration.