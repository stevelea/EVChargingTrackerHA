# EV Charging Tracker Replit Integration

This is a special Home Assistant integration designed specifically for EV Charging Tracker applications hosted on Replit. It provides sensor entities to track and monitor your EV charging data without requiring an actual API connection.

![EV Charging Tracker Logo](https://raw.githubusercontent.com/home-assistant/brands/master/custom_integrations/evchargingtracker_replit/icon.png)

## Overview

When hosting the EV Charging Tracker application on Replit, a fundamental limitation prevents the regular Home Assistant integration from working: **all external requests to the Replit app URL return the Streamlit interface instead of API responses**.

This special integration resolves this issue by providing a simulated data source that maintains the same structure as the API would provide, but without requiring any actual API connection. This allows you to:

1. Visualize EV charging data in Home Assistant
2. Create dashboards incorporating EV charging data
3. Set up automations based on EV charging events
4. Develop your Home Assistant implementation while hosting on Replit

## Key Features

- No API connection required - works even if your Replit app is offline
- All sensor entities match what would be available with a real API connection
- Data is clearly labeled as simulated for transparency
- 60-second update interval to demonstrate the dynamic behavior
- Easy configuration via the standard Home Assistant UI
- Zero-configuration setup - no API key needed

## Available Sensors

This integration provides the following sensors:

| Sensor Name | Description | Example Value |
|-------------|-------------|---------------|
| Total Energy | Total energy consumed across all charging sessions | 243.5 kWh |
| Total Cost | Total cost of all charging sessions | $109.57 |
| Average Cost per kWh | Average cost per kilowatt-hour | $0.45/kWh |
| Charging Session Count | Number of charging sessions recorded | 5 |
| Last Charging Energy | Energy consumed in the most recent charging session | 25.4 kWh |
| Last Charging Cost | Cost of the most recent charging session | $11.43 |
| Last Charging Location | Location of the most recent charging session | Simulated Location 1 |
| Last Charging Date | Date and time of the most recent charging session | [Current timestamp] |
| Last Peak Power | Peak power during the most recent charging session | 50.0 kW |
| Last Cost per kWh | Cost per kWh for the most recent charging session | $0.45/kWh |
| Last Provider | Charging provider for the most recent charging session | Chargefox |

## How is this different from the regular EV Charging Tracker integration?

The regular `evchargingtracker` integration makes API calls to your hosted EV Charging Tracker application to fetch real data. When hosting on Replit, the API endpoints are inaccessible from outside Replit due to routing limitations.

This special `evchargingtracker_replit` integration:
- Doesn't make any API calls at all
- Generates consistent, simulated data that matches the structure of the real API
- Works regardless of whether your Replit application is online or not
- Clearly marks all sensor values as simulated data

## Installation

See the [INSTALLATION.md](INSTALLATION.md) file for detailed installation instructions.

## Technical Details

For a complete explanation of the Replit-specific limitations and how this integration works around them, see [REPLIT_MODE.md](REPLIT_MODE.md).

## When to use this Integration

Use this integration when:

1. You are hosting your EV Charging Tracker on Replit
2. You want to develop your Home Assistant dashboards and automations without having to deploy a local version
3. You need sensor entities for testing and development purposes

## When to use the Regular Integration

Use the regular `evchargingtracker` integration when:

1. You are hosting EV Charging Tracker locally or on a server with proper API access
2. You need to see your actual charging data in Home Assistant
3. You require real-time updates based on your actual charging activity