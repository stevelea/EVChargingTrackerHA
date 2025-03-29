#!/bin/bash

# Stop on error
set -e

# Constants
ADDON_DIR="evcharging_tracker"
APP_DIR="app"

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Print status
echo "Building Home Assistant add-on for EV Charging Tracker..."

# Create app directory
mkdir -p $ADDON_DIR/$APP_DIR

# Copy application files
echo "Copying application files..."
cp -r ../*.py $ADDON_DIR/$APP_DIR/
cp -r ../data $ADDON_DIR/$APP_DIR/
mkdir -p $ADDON_DIR/$APP_DIR/.streamlit
cp -r ../.streamlit/* $ADDON_DIR/$APP_DIR/.streamlit/

# Create a README for the add-on
echo "Creating README.md..."
cat > $ADDON_DIR/README.md << 'EOL'
# Home Assistant Add-on: EV Charging Tracker

Track and visualize your EV charging data from various providers.

## About

This add-on allows you to track and analyze your electric vehicle charging data directly in Home Assistant.
It can extract data from Gmail receipts from providers like ChargePoint, Ampol, and more, 
or you can upload data directly from EVCC and other sources.

## Features

- Extract charging data from emails (requires Gmail account)
- Upload data from EVCC CSV files 
- View charging statistics and visualizations
- Track costs and energy usage
- Map charging locations
- Explore charging network
- Automatically creates sensors in Home Assistant

## Configuration

The add-on provides the following configuration options:

| Option | Description |
|--------|-------------|
| `use_guest_mode` | Enable guest mode for read-only access without login |
| `guest_password` | Password for guest mode access |
| `background_refresh_interval` | Interval in minutes for background data refresh |

## How to use

1. Install the add-on
2. Start the add-on
3. Open the Web UI
4. Log in with your Gmail account or use guest mode
5. View your charging data and statistics

## Integration

The add-on automatically creates sensor entities in Home Assistant that you can use
in dashboards, automations, and scripts.
EOL

# Create a zip file for easy installation
echo "Creating zip archive..."
cd ..
zip -r evcharging_tracker_addon.zip ha_addon

echo "Done! Add-on package created: evcharging_tracker_addon.zip"