#!/bin/bash

# This script creates a ZIP package of the Home Assistant component for easy distribution

# Set component name
COMPONENT_NAME="evchargingtracker_replit"
OUTPUT_DIR="."

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Copy the component files
echo "Copying component files..."
mkdir -p "$TEMP_DIR/custom_components/$COMPONENT_NAME"
cp -r "custom_components/$COMPONENT_NAME"/* "$TEMP_DIR/custom_components/$COMPONENT_NAME/"

# Create the ZIP file
echo "Creating ZIP package..."
cd "$TEMP_DIR" || exit 1
zip -r "$OUTPUT_DIR/$COMPONENT_NAME.zip" "custom_components/$COMPONENT_NAME"
cd - || exit 1

# Copy the README
cp "custom_components/${COMPONENT_NAME}.zip.readme" "$OUTPUT_DIR/${COMPONENT_NAME}.zip.readme"

# Cleanup
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo "Package created: $OUTPUT_DIR/$COMPONENT_NAME.zip"
echo "README file copied: $OUTPUT_DIR/${COMPONENT_NAME}.zip.readme"
echo "Done!"