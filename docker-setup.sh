#!/bin/bash

# Script to help with Docker image setup and potential network issues

# Set the base image and digest
BASE_IMAGE="python:3.11-slim"
IMAGE_DIGEST="sha256:d71b8eea6c9fcc6b25230361faf142c84f23ad4fbd1f852c8de96316a40a1add"

echo "Setting up Docker for EV Charging Tracker..."
echo "----------------------------------------"

# Step 1: Try to pull the base image
echo "Step 1: Pulling base image..."
docker pull $BASE_IMAGE@$IMAGE_DIGEST

if [ $? -ne 0 ]; then
    echo "Warning: Failed to pull base image directly."
    echo "Trying alternative approaches..."
    
    # Try using docker.io prefix
    echo "Trying with docker.io prefix..."
    docker pull docker.io/$BASE_IMAGE@$IMAGE_DIGEST
    
    if [ $? -ne 0 ]; then
        echo "Warning: Still having issues with Docker Hub connectivity."
        echo "You may need to check your network settings or Docker daemon configuration."
    fi
fi

# Step 2: Clean up any previous builds
echo "Step 2: Cleaning up previous builds..."
docker-compose down
docker system prune -f

# Step 3: Build with no cache
echo "Step 3: Building the application with no cache..."
docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo "Error: Build failed."
    echo "Check the Troubleshooting section in DOCKER_DEPLOYMENT.md for more information."
    exit 1
fi

# Step 4: Start the container
echo "Step 4: Starting the container..."
docker-compose up -d

echo "----------------------------------------"
echo "Setup complete!"
echo "The application should be available at: http://localhost:5000"
echo "Use 'docker-compose logs -f' to view logs."
echo "Use 'docker-compose down' to stop the application."