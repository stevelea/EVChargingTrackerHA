#!/bin/bash

# Azure deployment script for EV Charging Tracker
# This script prepares the application for deployment to Azure App Service

# Ensure script stops on errors
set -e

echo "Preparing for Azure deployment..."

# Create directories if they don't exist
mkdir -p azure_deployment/data

# Copy necessary files
echo "Copying application files..."
find . -name "*.py" -not -path "./azure_deployment/*" -not -path "./env/*" -not -path "./custom_components/*" -exec cp {} azure_deployment/ \;

# Create empty __init__.py to ensure modules are recognized
touch azure_deployment/__init__.py

# Copy data files
echo "Copying data files..."
cp -r data/* azure_deployment/data/

# Create .streamlit config directory
mkdir -p azure_deployment/.streamlit
cat > azure_deployment/.streamlit/config.toml << EOL
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false
EOL

echo "Creating runtime.txt for Python version..."
echo "python-3.10" > azure_deployment/runtime.txt

echo "Creating startup command file..."
cat > azure_deployment/startup.txt << EOL
gunicorn --bind=0.0.0.0:8000 --timeout 600 --chdir azure_deployment app:app
EOL

echo "Preparation complete!"
echo "To deploy to Azure App Service:"
echo "1. Create an App Service using the Azure Portal"
echo "2. Set up deployment from GitHub or upload files using FTP"
echo "3. Configure the following environment variables in Azure Portal:"
echo "   - GOOGLE_CLIENT_ID"
echo "   - GOOGLE_CLIENT_SECRET"
echo "   - WEBSITE_RUN_FROM_PACKAGE=0"
echo ""
echo "Your application is ready for deployment!"