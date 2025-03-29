# Docker Deployment Guide

This guide explains how to deploy the EV Charging Tracker application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- Basic familiarity with Docker commands

## Deployment Steps

1. **Clone or download this repository**

2. **Build and start the container**

   From the root directory of the project, you can use either:

   **Option A: Use the helper script (recommended):**
   ```bash
   # Make the script executable if needed
   chmod +x docker-setup.sh
   
   # Run the setup script
   ./docker-setup.sh
   ```

   **Option B: Use docker-compose directly:**
   ```bash
   docker-compose up -d
   ```

   This will:
   - Build the Docker image
   - Start a container in detached mode
   - Mount the `/portainer/Files/AppData` directory for persistent storage
   - Expose the application on port 5000
   
   Note: If you encounter network issues during build, refer to the [Troubleshooting](#troubleshooting) section.

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
- Persist data in `/portainer/Files/AppData` directory
- Enable test data mode for demonstration purposes

## Customization

To modify the configuration:

1. **Environment Variables**: Edit the `docker-compose.yml` file to add environment variables

2. **Data Persistence**: The application stores data in the `/app/data` directory, which is mounted to the host's `/portainer/Files/AppData` directory

3. **Port Mapping**: To change the port mapping, edit the `ports` section in `docker-compose.yml`

## Troubleshooting

1. **Permission Issues**: If you encounter permission issues with the data directory, ensure the `/portainer/Files/AppData` directory has appropriate permissions

2. **Port Conflicts**: If port 5000 is already in use, change the port mapping in `docker-compose.yml`

3. **Docker Build Network Issues**: If you encounter network errors when building the Docker image (such as "failed to do request" or "i/o timeout" errors), these are typically DNS resolution problems. Try these solutions in order:

   ### Solution A: Use the helper script (easiest)
   ```bash
   chmod +x docker-setup.sh
   ./docker-setup.sh
   ```
   The script will:
   - Try multiple ways to pull the image
   - Modify the Dockerfile if needed
   - Attempt builds with different options
   - Start the container when successful
   
   ### Solution B: Fix Docker DNS settings (most reliable)
   
   Edit or create the Docker daemon configuration file:
   ```bash
   sudo nano /etc/docker/daemon.json
   ```
   
   Add or modify the file to include Google DNS:
   ```json
   {
     "dns": ["8.8.8.8", "8.8.4.4"]
   }
   ```
   
   Restart Docker:
   ```bash
   sudo systemctl restart docker
   ```
   
   ### Solution C: Remove the specific digest
   
   Edit the Dockerfile and change:
   ```
   FROM python:3.11-slim@sha256:d71b8eea6c9fcc6b25230361faf142c84f23ad4fbd1f852c8de96316a40a1add
   ```
   to:
   ```
   FROM python:3.11-slim
   ```
   
   ### Solution D: Build with network host option
   ```bash
   docker build --network=host -t ev-charging-tracker:latest .
   docker run -d -p 5000:5000 -v "/portainer/Files/AppData:/app/data" --name ev-charging-tracker ev-charging-tracker:latest
   ```
   
   ### Solution E: Check your networking
   - Verify your internet connection is working
   - Check if you're behind a corporate firewall or VPN
   - Try a different network or disable firewall temporarily
   - Ensure Docker can access external domains

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