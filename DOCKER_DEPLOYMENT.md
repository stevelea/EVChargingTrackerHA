# Docker Deployment Guide

This guide explains how to deploy the EV Charging Tracker application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- Basic familiarity with Docker commands

## Deployment Steps

1. **Clone or download this repository**

2. **Build and start the container**

   From the root directory of the project, run:

   ```bash
   docker-compose up -d
   ```

   This will:
   - Build the Docker image
   - Start a container in detached mode
   - Mount the `./data` directory for persistent storage
   - Expose the application on port 5000

3. **Access the application**

   Once the container is running, access the application at:
   
   ```
   http://localhost:5000
   ```

4. **View container logs**

   To see the logs from the running container:

   ```bash
   docker-compose logs -f
   ```

## Stopping the Application

To stop the application:

```bash
docker-compose down
```

## Configuration

The application is pre-configured to:

- Run the combined proxy that handles both Streamlit UI and Flask API on port 5000
- Persist data in `/portainer/Files/AppData/evchargingtracker` directory
- Enable test data mode for demonstration purposes

## Customization

To modify the configuration:

1. **Environment Variables**: Edit the `docker-compose.yml` file to add environment variables

2. **Data Persistence**: The application stores data in the `/app/data` directory, which is mounted to the host's `/portainer/Files/AppData/evchargingtracker` directory

3. **Port Mapping**: To change the port mapping, edit the `ports` section in `docker-compose.yml`

## Troubleshooting

1. **Permission Issues**: If you encounter permission issues with the data directory, ensure the `/portainer/Files/AppData/evchargingtracker` directory has appropriate permissions

2. **Port Conflicts**: If port 5000 is already in use, change the port mapping in `docker-compose.yml`

## API Access

The API is accessible through the same port (5000) using the `/api` prefix:

```
http://localhost:5000/api/health
http://localhost:5000/api/charging-data
```

## Home Assistant Integration

To integrate with Home Assistant, configure a custom component with:

- Host: Your Docker host IP address
- Port: 5000
- API Key: Your configured API key (default: none required)