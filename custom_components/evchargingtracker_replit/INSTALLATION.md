# EV Charging Tracker Replit Integration - Installation Guide

This document provides detailed step-by-step instructions for installing and configuring the EV Charging Tracker Replit integration for Home Assistant.

## Prerequisites

1. Home Assistant instance (Core, OS, Container, or Supervised)
2. Access to the Home Assistant configuration directory
3. SSH access or Samba/network share access to copy files (for some installations)

## Installation Methods

There are several ways to install this integration. Choose the method that best suits your Home Assistant setup:

### Method 1: Manual Installation (Recommended)

1. Download the `evchargingtracker_replit` folder from this repository.
2. Copy the entire folder to your Home Assistant custom_components directory.
   - For Home Assistant OS/Supervised: use the Samba add-on or SSH to copy to `/config/custom_components/`
   - For Home Assistant Core: copy to `~/.homeassistant/custom_components/` or your configured configuration directory
   - For Home Assistant Container: mount and copy to the custom_components directory in your mounted configuration volume

3. Restart Home Assistant completely.

### Method 2: Using HACS (Home Assistant Community Store)

If you have HACS installed:

1. Add this repository as a custom repository in HACS:
   - Go to HACS in your Home Assistant instance
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add the URL of this repository
   - Category: Integration

2. Install the integration through HACS
   - Find "EV Charging Tracker Replit" in the Integrations tab
   - Click "Download"

3. Restart Home Assistant completely.

## Configuration

After installation and restart, you need to add the integration to Home Assistant:

1. Go to **Configuration** → **Devices & Services** in your Home Assistant UI.
2. Click the **+ Add Integration** button in the bottom right corner.
3. Search for "EV Charging Tracker Replit" and select it.
4. Enter the configuration details:
   - **Host**: Your Replit app domain (e.g., `ev-charging-tracker.replit.app`)
   - **Port**: `5000` (this is the only port exposed by Replit)
   - **API Key**: Enter any value (e.g., `ev-charging-api-key`)

5. Click "Submit" to add the integration.

## Verifying the Installation

After adding the integration, you should see several new sensors in your Home Assistant instance:

1. Go to **Configuration** → **Devices & Services**
2. Click on **EV Charging Tracker Replit** in the integrations list
3. You should see a single device with multiple entities including:
   - Total Energy
   - Total Cost
   - Average Cost per kWh
   - Charging Session Count
   - Last Charging Energy
   - Last Charging Cost
   - Last Charging Location
   - And more...

## Troubleshooting

If you encounter issues with the installation or configuration, check the following:

### Integration Not Appearing in the Add Integration List

- Ensure you have restarted Home Assistant completely after copying the files
- Verify the files are in the correct location (should be in `custom_components/evchargingtracker_replit/`)
- Check Home Assistant logs for any errors related to loading the component

### No Entities After Adding the Integration

- Check the Home Assistant logs for any errors related to the integration
- Try removing and re-adding the integration
- Verify you're using the correct port (5000) in the configuration

### Entity Values Not Updating

- This integration uses synthetic data that updates every 60 seconds, so values should change regularly
- If values are not updating, check the Home Assistant logs for any errors

## Log Locations

Home Assistant logs can provide valuable information about integration issues:

- For Home Assistant OS/Supervised: View logs through **Settings** → **System** → **Logs**
- For Home Assistant Core: Check `home-assistant.log` in your configuration directory
- For Home Assistant Container: View logs with `docker logs home-assistant`

## Support

If you continue to experience issues after trying the troubleshooting steps:

1. Check the integration's GitHub repository for known issues
2. Review the Technical Details in the `REPLIT_MODE.md` file to understand the design and limitations
3. Open an issue on the GitHub repository with:
   - Your Home Assistant version
   - Complete logs showing the error
   - Steps to reproduce the issue