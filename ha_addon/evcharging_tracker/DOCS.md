# EV Charging Tracker

This add-on provides a complete solution for tracking and analyzing your electric vehicle charging data directly in Home Assistant.

## Installation

Follow these steps to install the add-on:

1. Add the EV Charging Tracker repository to your Home Assistant instance.
   - Navigate to the Home Assistant Supervisor panel
   - Click "Add-on Store"
   - Click the three dots in the upper right corner and select "Repositories"
   - Add the repository URL: `https://github.com/yourusername/evcharging-tracker-addon`

2. Find and install the "EV Charging Tracker" add-on.
3. Start the add-on and wait for it to initialize.
4. Open the web UI through Home Assistant to start using the application.

## Configuration

The add-on can be configured through the Home Assistant UI. These options are available:

| Option | Default | Description |
|--------|---------|-------------|
| `use_guest_mode` | `true` | Enable guest mode for read-only access without login |
| `guest_password` | `evdata2023` | Password for guest mode access |
| `background_refresh_interval` | `10` | Interval in minutes for background data refresh |

## Usage

### Authentication Methods

The application supports several authentication methods:

1. **Gmail Authentication**: Log in with your Gmail account to automatically fetch charging data from your inbox.
2. **Guest Mode**: Use the configured password to access the application in read-only mode.

### Data Sources

Data can be imported from multiple sources:

1. **Gmail Receipts**: Automatically parse charging data from email receipts.
2. **EVCC CSV Files**: Upload CSV exports from EVCC.
3. **Manual Entry**: Add charging sessions manually.
4. **PDF Receipts**: Upload and parse PDF charging receipts.

### Features

- **Dashboard**: View summary statistics and visualizations of your charging data.
- **Location Map**: See where you've charged your vehicle on an interactive map.
- **Charging Network**: Explore nearby charging stations.
- **Data Management**: Import, export, and clean your charging data.
- **Predictive Analysis**: Get insights about future charging costs.

## Home Assistant Integration

This add-on automatically creates sensor entities in Home Assistant. These entities are updated every 60 seconds and include:

- `sensor.ev_charging_tracker_total_energy` - Total energy consumed
- `sensor.ev_charging_tracker_total_cost` - Total cost 
- `sensor.ev_charging_tracker_average_cost_per_kwh` - Average cost per kWh
- `sensor.ev_charging_tracker_session_count` - Number of charging sessions
- `sensor.ev_charging_tracker_last_energy` - Energy from latest session
- `sensor.ev_charging_tracker_last_cost` - Cost of latest session
- `sensor.ev_charging_tracker_last_location` - Location of latest session
- `sensor.ev_charging_tracker_last_date` - Date/time of latest session
- `sensor.ev_charging_tracker_last_peak_power` - Peak power of latest session
- `sensor.ev_charging_tracker_last_cost_per_kwh` - Cost per kWh of latest session
- `sensor.ev_charging_tracker_last_provider` - Provider of latest session

You can use these entities in dashboards, automations, and scripts.

## Troubleshooting

### Data Not Appearing

If your charging data isn't appearing:

1. Check your Gmail login credentials
2. Ensure your email contains supported charging receipts
3. Try uploading a CSV file manually

### Integration Errors

If the Home Assistant integration isn't working:

1. Restart the add-on
2. Check the add-on logs for any error messages
3. Make sure your Home Assistant instance has proper network connectivity to the add-on

## Support

For support, please open an issue on the GitHub repository.