#!/bin/bash

# Script to package the application for Azure deployment
# This will create a zip file that can be directly uploaded to Azure App Service

# Ensure script stops on errors
set -e

cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
AZURE_DIR="$SCRIPT_DIR"
OUTPUT_FILE="$PARENT_DIR/azure_deployment_package.zip"

echo "Packaging EV Charging Tracker for Azure deployment..."

# Create temp directory for organizing files
TEMP_DIR="$AZURE_DIR/temp_package"
mkdir -p "$TEMP_DIR"

# Copy all Python files from main app
echo "Copying main application files..."
find "$PARENT_DIR" -maxdepth 1 -name "*.py" -exec cp {} "$TEMP_DIR/" \;

# Copy Azure-specific files
echo "Copying Azure-specific files..."
cp "$AZURE_DIR/app.py" "$TEMP_DIR/"
cp "$AZURE_DIR/application.py" "$TEMP_DIR/"
cp "$AZURE_DIR/run_proxy_azure.py" "$TEMP_DIR/"
cp "$AZURE_DIR/azure_storage.py" "$TEMP_DIR/"
cp "$AZURE_DIR/azure_data_storage_patch.py" "$TEMP_DIR/"
cp "$AZURE_DIR/requirements.txt" "$TEMP_DIR/"
cp "$AZURE_DIR/web.config" "$TEMP_DIR/"

# Copy configuration files
echo "Copying configuration files..."
mkdir -p "$TEMP_DIR/.streamlit"
cp "$AZURE_DIR/.streamlit/config.toml" "$TEMP_DIR/.streamlit/"

# Create empty data directory
mkdir -p "$TEMP_DIR/data"
touch "$TEMP_DIR/__init__.py"

# Copy documentation
echo "Copying documentation..."
cp "$AZURE_DIR/README.md" "$TEMP_DIR/"
cp "$AZURE_DIR/AZURE_DEPLOYMENT.md" "$TEMP_DIR/"
cp "$AZURE_DIR/QUICK_START.md" "$TEMP_DIR/"

# Create the zip file
echo "Creating deployment package..."
cd "$TEMP_DIR"
zip -r "$OUTPUT_FILE" .

# Clean up
echo "Cleaning up..."
cd "$AZURE_DIR"
rm -rf "$TEMP_DIR"

echo "Deployment package created: $OUTPUT_FILE"
echo "You can now upload this file to Azure App Service."
echo "Make sure to follow the instructions in QUICK_START.md!"