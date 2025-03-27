#!/bin/bash

# This script creates a directory with all the files needed to deploy 
# the EV Charging Tracker application in Docker.

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Create deployment directory
echo "Creating deployment directory..."
DEPLOY_DIR="ev-charging-tracker"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Create required directories
mkdir -p data
mkdir -p .streamlit

# Copy all Python files
echo "Copying Python files..."
find "$SCRIPT_DIR" -maxdepth 1 -name "*.py" | grep -v "__pycache__" | xargs -I{} cp {} ./

# Copy Docker and configuration files
echo "Copying Docker and configuration files..."
cp "$SCRIPT_DIR/Dockerfile" ./
cp "$SCRIPT_DIR/docker-compose.yml" ./
cp "$SCRIPT_DIR/docker-requirements.txt" ./
cp "$SCRIPT_DIR/README.md" ./
cp "$SCRIPT_DIR/.streamlit/config.toml" ./.streamlit/

# Create a simple README with instructions
echo "Creating a README.local.md file with local instructions..."
cat > README.local.md << 'EOF'
# EV Charging Tracker - Local Deployment

This directory contains all the files needed to run the EV Charging Tracker
application in Docker.

## Running the Application

1. Make sure Docker and Docker Compose are installed on your system

2. Open a terminal in this directory and run:
   ```
   docker-compose up -d
   ```

3. Access the application in your web browser at:
   ```
   http://localhost:5000
   ```

## Your Charging Data

All your charging data is stored in the `data` directory. This directory is mounted
as a volume in the Docker container, so your data will persist even if you rebuild
or restart the container.

## Stopping the Application

To stop the application, run:
```
docker-compose down
```

## Viewing Logs

To view the application logs, run:
```
docker logs ev-charging-tracker
```
EOF

echo "Files prepared for Docker deployment in the '$DEPLOY_DIR' directory."
echo "To build and run the container:"
echo "  cd $DEPLOY_DIR"
echo "  docker-compose up -d"