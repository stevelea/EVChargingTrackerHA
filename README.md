# EV Charging Tracker

A comprehensive web application that helps you track, analyze, and visualize your electric vehicle charging data.

## Features

- Manual input of charging sessions
- Import data from various sources:
  - Gmail charging receipts via IMAP
  - PDF charging receipts
  - EVCC CSV files
  - Tesla API
- Interactive visualizations:
  - Charging costs over time
  - Energy usage trends
  - Provider comparisons
  - Efficiency metrics (kWh/km, $/km)
- Charging location mapping
- Predictive analysis for future costs
- Multi-user support with data separated by account
- REST API for external applications to access charging data
- Interactive EV charging network map with real-time station availability

## Docker Deployment

### Prerequisites

1. Docker and Docker Compose installed on your system
2. Basic knowledge of running containers

### Getting Started

1. **Download the application code**

   There are two ways to get the application code:

   **Option 1: Use the download script (Recommended)**
   
   Download the `download_for_deployment.sh` script and run it:

   ```bash
   chmod +x download_for_deployment.sh
   ./download_for_deployment.sh
   ```

   This will create a new directory called `ev-charging-tracker` with all necessary files for deployment.

   **Option 2: Manual download**
   
   Download all files from this project to a directory on your computer.

2. **Build and start the container**

   Open a terminal in the directory containing the downloaded files and run:

   ```bash
   docker-compose up -d
   ```

   This will build the Docker image and start the container in detached mode.

3. **Access the application**

   Open your web browser and navigate to:

   ```
   http://localhost:5000
   ```

   If you're accessing from another device on your network, replace `localhost` with the IP address of the computer running Docker.

### Data Persistence

The application stores all data in the `./data` directory, which is mounted as a volume in the Docker container. This ensures your charging data persists even if the container is restarted or rebuilt.

### Updating the Application

To update the application to a newer version:

1. Download the updated code
2. Run the following commands:

   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## Security Notes

- The application uses IMAP for Gmail access, which requires an App Password.
- Never share your Gmail App Password with others.
- When running on your home network, the application is accessible to all devices on the network unless firewall rules are in place.

## API Access

The application includes a REST API for accessing charging data from external applications. The API runs on port 8000 by default.

### API Documentation

For complete API documentation, see the [API_DOCUMENTATION.md](API_DOCUMENTATION.md) file.

### Key Features

- Retrieve charging data with filtering capabilities
- Get charging summary statistics
- Access individual charging records
- Authentication via API key
- Comprehensive Python client library included

### Quick Example

```python
from api_client import EVChargingAPIClient

# Create client
client = EVChargingAPIClient(
    base_url="http://localhost:8000",
    api_key="ev-charging-api-key"
)

# Get charging data
data = client.get_charging_data(email="user@example.com")
print(f"Retrieved {data.get('count', 0)} charging records")

# Get summary statistics
summary = client.get_charging_summary()
print(f"Total Energy: {summary.get('total_energy_kwh', 0)} kWh")
print(f"Total Cost: ${summary.get('total_cost', 0)}")
```

Check the `examples` directory for more comprehensive usage examples.

## Home Assistant Integration

The application can be integrated with Home Assistant to provide sensor entities for monitoring your EV charging data.

### Local Network Setup

For deployments on a local network (Docker, self-hosted), use the standard Home Assistant integration:

1. Install the custom component:
   ```bash
   cp -r custom_components/evchargingtracker /path/to/your/homeassistant/custom_components/
   ```

2. Configure in Home Assistant:
   - Host: Your server IP address
   - Port: 8000 (the API port)
   - API Key: The API key configured in your application

### Replit Deployment Setup

For Replit deployments, a special integration is provided due to Replit's unique routing constraints:

1. Install the Replit-specific component:
   ```bash
   cp -r custom_components/evchargingtracker_replit /path/to/your/homeassistant/custom_components/
   ```

2. Configure in Home Assistant:
   - Host: Your Replit app URL (e.g., `ev-charging-tracker-stevelea1.replit.app`)
   - Port: 5000
   - API Key: Any value (not used in Replit mode)

3. Read the technical details in `custom_components/evchargingtracker_replit/REPLIT_MODE.md`

### Sensors Available

The integration provides several useful sensors including:

- Total energy charged (kWh)
- Total cost
- Average cost per kWh
- Charging session count
- Latest charging location
- Latest charging cost
- Latest peak power
- And more...

## Troubleshooting

### Docker Deployment Issues

- If the application is not accessible, check that Docker is running properly:
  ```bash
  docker ps
  ```
  You should see the `ev-charging-tracker` container running.

- If data is not persisting, check that the volume mount is working correctly:
  ```bash
  docker volume ls
  ```

- To view logs:
  ```bash
  docker logs ev-charging-tracker
  ```

### Replit Deployment Issues

- **API Access:** When hosting on Replit, all external requests to your Replit app URL will return the Streamlit interface, not the API. This is a fundamental limitation of Replit's routing infrastructure. For API access in this environment, use the special Home Assistant integration described above.

- **Port Access:** Replit only exposes port 5000 publicly. All services (Streamlit UI and API) are routed through this port using the proxy application.

- **Home Assistant Integration:** If you're trying to use the standard Home Assistant integration with a Replit-hosted instance, it will not work properly due to routing limitations. Use the special `evchargingtracker_replit` integration instead.

- **Data Persistence:** Replit deployments use the Replit Database for data persistence. If you're experiencing data loss, ensure the application has proper permissions to access the Replit DB.

For technical details on the Replit-specific limitations and workarounds, see:
`custom_components/evchargingtracker_replit/REPLIT_MODE.md`