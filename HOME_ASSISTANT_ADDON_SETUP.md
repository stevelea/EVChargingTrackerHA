# Setting Up EV Charging Tracker as a Home Assistant Add-on

This guide explains how to install EV Charging Tracker as a Home Assistant add-on. This allows you to run the application directly in your Home Assistant environment.

## What is a Home Assistant Add-on?

Home Assistant add-ons are applications that run alongside your Home Assistant installation. They are managed by the Home Assistant Supervisor and are easy to install and update. Add-ons can provide additional functionality, like EV Charging Tracker's ability to collect and visualize your charging data.

## Prerequisites

To use this add-on, you need:

1. A Home Assistant installation with the Supervisor (Home Assistant OS, Home Assistant Supervised)
2. Access to the Home Assistant Add-on Store
3. Internet connection for your Home Assistant instance

## Installation Methods

### Method 1: Using the Built Package

1. Download the `evcharging_tracker_addon.zip` file from this repository's releases.
2. Extract the ZIP file.
3. In the Home Assistant UI, go to **Settings → Add-ons → Add-on Store**.
4. Click the three dots in the top right and select **Repositories**.
5. Click **Add** and enter the path to the extracted add-on folder.
6. Refresh the add-ons list, and you should see "EV Charging Tracker" appear.
7. Click on it and then click **Install**.

### Method 2: Building the Add-on Yourself

1. Clone this repository to your computer.
2. Navigate to the `ha_addon` directory.
3. Run the `build.sh` script to create the add-on package:
   ```bash
   ./build.sh
   ```
4. This will create a `evcharging_tracker_addon.zip` file.
5. Extract this ZIP file and add the repository as described in Method 1.

## Configuration

After installation, you can configure the add-on with these options:

- **use_guest_mode**: Enable or disable guest mode (default: `true`)
- **guest_password**: Password for guest mode (default: `evdata2023`)
- **background_refresh_interval**: Interval in minutes for background data refresh (default: `10`)

## Usage

1. Start the add-on by clicking **Start** in the add-on page.
2. Once started, click **Open Web UI** to access the EV Charging Tracker interface.
3. Use the interface to login with your Gmail account or use guest mode.
4. View and analyze your charging data.

## Data Storage

All data is stored in the `/data` directory within the add-on, which is persistent across restarts and updates. This includes:

- Charging session data for each user
- Credentials (if saved)
- Application settings

## Integration with Home Assistant

The add-on automatically creates sensor entities in Home Assistant. You can use these sensors in dashboards, automations, and scripts.

Available sensors include:

- Total energy consumed
- Total cost
- Average cost per kWh
- Number of charging sessions
- Latest session details

## Updating the Add-on

When a new version is available:

1. Go to the Home Assistant Add-on Store.
2. Click the refresh button to check for updates.
3. If an update is available, click **Update** on the EV Charging Tracker add-on.

## Troubleshooting

If you encounter issues:

1. Check the add-on logs by clicking on the **Logs** tab in the add-on page.
2. Restart the add-on if it's not working properly.
3. If problems persist, try reinstalling the add-on.

## Removing the Add-on

To remove the add-on:

1. Go to the add-on page.
2. Click **Uninstall**.
3. To remove your data as well, delete the add-on data directory.