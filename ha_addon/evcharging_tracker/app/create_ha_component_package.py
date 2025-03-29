#!/usr/bin/env python3
"""
Helper script to create a Home Assistant component package from the integrated components.
This script packages both the standard and Replit-specific integrations for Home Assistant.
"""

import os
import shutil
import zipfile
import tempfile
import sys

def print_status(message):
    """Print a status message"""
    print(f"📦 {message}")

def main():
    print_status("Creating Home Assistant Integration Package...")
    
    # Create temp directory for package
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = os.path.join(temp_dir, "ha_package")
        os.makedirs(package_dir, exist_ok=True)
        
        # Check if the custom_components directory exists
        if not os.path.exists("custom_components"):
            print_status("❌ Error: custom_components directory not found")
            return False
            
        # Copy the standard integration
        std_integration_src = os.path.join("custom_components", "evchargingtracker")
        std_integration_dst = os.path.join(package_dir, "evchargingtracker")
        if os.path.exists(std_integration_src):
            print_status("Copying standard integration...")
            shutil.copytree(std_integration_src, std_integration_dst)
        else:
            print_status("⚠️ Warning: Standard integration not found")
            
        # Copy the Replit-specific integration
        replit_integration_src = os.path.join("custom_components", "evchargingtracker_replit")
        replit_integration_dst = os.path.join(package_dir, "evchargingtracker_replit")
        if os.path.exists(replit_integration_src):
            print_status("Copying Replit-specific integration...")
            shutil.copytree(replit_integration_src, replit_integration_dst)
        else:
            print_status("⚠️ Warning: Replit-specific integration not found")
        
        # Create README file
        readme_path = os.path.join(package_dir, "README.md")
        with open(readme_path, "w") as readme_file:
            readme_file.write("""# EV Charging Tracker - Home Assistant Integration Package

This package contains two different Home Assistant integrations for the EV Charging Tracker application:

1. **Standard Integration** (`evchargingtracker`) - For connecting to locally hosted instances or direct API access
2. **Replit-Specific Integration** (`evchargingtracker_replit`) - Specifically designed to work with Replit-hosted instances

## Which Integration Should I Use?

### Use the Standard Integration (`evchargingtracker`) if:

- You're running the EV Charging Tracker locally on your network
- You're hosting the EV Charging Tracker on a server with direct API access
- You need actual data from your EV Charging Tracker instance

### Use the Replit-Specific Integration (`evchargingtracker_replit`) if:

- Your EV Charging Tracker is hosted on Replit
- You're experiencing issues connecting to the API endpoints on Replit
- You want to see how the integration would work without an actual API connection

## Installation Instructions

### Step 1: Choose Your Integration

Decide which integration you want to use based on your setup (see above).

### Step 2: Copy Files to Home Assistant

1. Copy **only one** of the integration folders to your Home Assistant custom_components directory:

   **For Standard Integration:**
   ```bash
   cp -r evchargingtracker /path/to/your/homeassistant/custom_components/
   ```

   **For Replit-Specific Integration:**
   ```bash
   cp -r evchargingtracker_replit /path/to/your/homeassistant/custom_components/
   ```

2. Restart Home Assistant.

### Step 3: Add the Integration

1. Go to your Home Assistant instance.
2. Navigate to **Configuration** > **Integrations**.
3. Click the **+ ADD INTEGRATION** button.
4. Search for the integration name and select it:
   - "EV Charging Tracker" for the standard integration
   - "EV Charging Tracker Replit" for the Replit-specific integration

5. Enter the configuration details:
   - For Standard Integration: Host, Port (5000), and optional API key
   - For Replit Integration: No configuration needed

6. Click **Submit** to add the integration.

## Standard Integration Configuration

For the standard integration, you'll need to provide:

- **Host**: The hostname or IP address of your EV Charging Tracker server (e.g., `localhost` or `192.168.1.10` or `yourapp.replit.app`)
- **Port**: The port of the API server (always use `5000` for both local and Replit deployments)
- **API Key**: (Optional) The default API key is `ev-charging-api-key`

## Replit Integration Configuration

The Replit-specific integration requires no configuration - it works out of the box.

## Troubleshooting

### Standard Integration Issues

If you're having trouble connecting to the API:

1. **Check the API server is running**: Make sure the EV Charging Tracker API is running and accessible.
2. **Verify connectivity**: Ensure Home Assistant can reach the API server.
3. **Check port settings**: Confirm you're using port 5000 for the connection.
4. **Verify API key**: Make sure you're using the correct API key.

### Replit Integration Issues

The Replit integration doesn't connect to any API, so connectivity issues shouldn't occur. If you have problems:

1. **Check the integration is installed correctly**: Verify the folder is in the right location.
2. **Restart Home Assistant**: Make sure you've completely restarted after installation.

## For More Information

See the individual README files in each integration folder for more detailed documentation.""")

        # Create the output directory
        os.makedirs("downloads", exist_ok=True)
        
        # Create zip file
        zip_path = os.path.join("downloads", "evchargingtracker_ha_package.zip")
        print_status(f"Creating ZIP file: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        print_status(f"✅ Package created successfully at: {zip_path}")
        print(f"\nInstallation Instructions:")
        print(f"1. Download the ZIP file")
        print(f"2. Extract it to get the integration folders")
        print(f"3. Copy your chosen integration folder to your Home Assistant custom_components directory")
        print(f"4. Restart Home Assistant")
        print(f"5. Add the integration in Home Assistant UI (Configuration > Integrations)")
        
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)