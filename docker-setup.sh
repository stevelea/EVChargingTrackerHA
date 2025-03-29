#!/bin/bash

# Script to help with Docker image setup and potential network issues

# Set the base image and digest
BASE_IMAGE="python:3.11-slim"
IMAGE_DIGEST="sha256:d71b8eea6c9fcc6b25230361faf142c84f23ad4fbd1f852c8de96316a40a1add"

echo "Setting up Docker for EV Charging Tracker..."
echo "----------------------------------------"

# Step 1: Choose setup method
echo "Choose setup method:"
echo "1. Standard setup (with digest-specific image)"
echo "2. Simple setup (without specific digest - better for networks with DNS issues)"
read -p "Enter 1 or 2 [2]: " setup_choice
setup_choice=${setup_choice:-2}

if [ "$setup_choice" = "2" ]; then
    # Use the simpler Dockerfile if it exists, or create it
    if [ -f "Dockerfile.simple" ]; then
        echo "Using simplified Dockerfile..."
        cp Dockerfile.simple Dockerfile
    else
        echo "Creating simplified Dockerfile..."
        cat > Dockerfile << 'EOF'
# Use the Python 3.11 slim image without a specific digest to improve compatibility
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Reduce Python buffering for better logging
ENV PYTHONUNBUFFERED=1

# Copy requirements file
COPY docker-requirements.txt .

# Install dependencies with specific configuration for better compatibility
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r docker-requirements.txt

# Copy the application code
COPY . .

# Expose port 5000 for the application
EXPOSE 5000

# Run the application using the proxy that combines Streamlit and API
CMD ["python", "run_proxy.py"]
EOF
    fi
fi

# Step 2: Configure Docker daemon DNS (if needed)
echo "Step 2: Checking Docker daemon DNS configuration..."
if [ -f "/etc/docker/daemon.json" ]; then
    echo "Docker daemon configuration file exists."
    echo "To fix DNS issues, you may need to edit /etc/docker/daemon.json manually."
    echo "Consider adding the following DNS configuration:"
    echo '{
  "dns": ["8.8.8.8", "8.8.4.4"]
}'
    echo "After editing, restart Docker with: sudo systemctl restart docker"
    echo ""
    echo "Press Enter to continue or Ctrl+C to exit and fix DNS..."
    read -r
else
    echo "Docker daemon configuration file not found at /etc/docker/daemon.json."
    echo "You may need to create it with the following content:"
    echo '{
  "dns": ["8.8.8.8", "8.8.4.4"]
}'
    echo "After creating, restart Docker with: sudo systemctl restart docker"
    echo ""
    echo "Press Enter to continue or Ctrl+C to exit and fix DNS..."
    read -r
fi

# Step 3: Try to pull the base image (only if using standard setup)
if [ "$setup_choice" = "1" ]; then
    echo "Step 3: Trying to pull base image..."
    echo "Trying with default registry..."
    docker pull $BASE_IMAGE@$IMAGE_DIGEST

    if [ $? -ne 0 ]; then
        echo "Warning: Failed to pull base image directly."
        
        # Try using docker.io prefix
        echo "Trying with docker.io prefix..."
        docker pull docker.io/$BASE_IMAGE@$IMAGE_DIGEST
        
        if [ $? -ne 0 ]; then
            echo "Warning: Still having issues with Docker Hub connectivity."
            echo "Switching to simplified setup method..."
            
            # Use the simpler Dockerfile if it exists, or create it
            if [ -f "Dockerfile.simple" ]; then
                echo "Using simplified Dockerfile..."
                cp Dockerfile.simple Dockerfile
            else
                echo "Creating simplified Dockerfile..."
                cat > Dockerfile << 'EOF'
# Use the Python 3.11 slim image without a specific digest to improve compatibility
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Reduce Python buffering for better logging
ENV PYTHONUNBUFFERED=1

# Copy requirements file
COPY docker-requirements.txt .

# Install dependencies with specific configuration for better compatibility
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r docker-requirements.txt

# Copy the application code
COPY . .

# Expose port 5000 for the application
EXPOSE 5000

# Run the application using the proxy that combines Streamlit and API
CMD ["python", "run_proxy.py"]
EOF
            fi
        fi
    fi
else
    echo "Step 3: Skipping digest-specific image pull (using simple setup)"
    
    # Try pulling the base image without digest
    echo "Trying to pull Python image without digest..."
    docker pull python:3.11-slim
    
    if [ $? -ne 0 ]; then
        echo "Warning: Unable to pull Python image."
        echo "This appears to be a serious network or DNS connectivity issue."
        echo ""
        echo "Possible solutions:"
        echo "1. Check your internet connection"
        echo "2. Configure DNS in your Docker daemon settings"
        echo "3. If behind a corporate firewall, configure Docker to use your proxy"
        echo "4. Try using a different network"
        
        echo "Would you like to:"
        echo "1. Continue anyway (likely won't work)"
        echo "2. Exit and troubleshoot"
        read -p "Enter 1 or 2 [2]: " choice
        choice=${choice:-2}
        
        if [ "$choice" != "1" ]; then
            echo "Exiting setup. Please fix connectivity issues and try again."
            exit 1
        fi
    fi
fi

# Step 4: Clean up any previous builds
echo "Step 4: Cleaning up previous builds..."
docker-compose down
docker system prune -f

# Step 5: Try alternate build methods
echo "Step 5: Building the application..."
echo "Trying build with standard options..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "Standard build failed. Trying with --no-cache option..."
    docker-compose build --no-cache
    
    if [ $? -ne 0 ]; then
        echo "Build with --no-cache failed."
        echo "Trying direct build with network host..."
        docker build --network=host -t ev-charging-tracker:latest .
        
        if [ $? -ne 0 ]; then
            echo "Error: All build attempts failed."
            echo "This is likely a network connectivity issue with your Docker environment."
            echo "Please see the full Troubleshooting section in DOCKER_DEPLOYMENT.md"
            exit 1
        else
            echo "Direct build succeeded."
            echo "Starting container manually..."
            docker run -d -p 5000:5000 -v "/portainer/Files/AppData:/app/data" --name ev-charging-tracker ev-charging-tracker:latest
            if [ $? -eq 0 ]; then
                echo "Container started manually."
            else
                echo "Error starting container manually."
                exit 1
            fi
        fi
    else
        # Start the container with docker-compose
        echo "Starting the container with docker-compose..."
        docker-compose up -d
    fi
else
    # Start the container with docker-compose
    echo "Starting the container with docker-compose..."
    docker-compose up -d
fi

echo "----------------------------------------"
echo "Setup completed!"
echo "The application should be available at: http://localhost:5000"
echo "Use 'docker-compose logs -f' to view logs."
echo "Use 'docker-compose down' to stop the application."