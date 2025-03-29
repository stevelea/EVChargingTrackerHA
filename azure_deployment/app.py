"""
Azure App Service entry point for EV Charging Tracker app.
This file serves as the main entry point for Azure App Service.
"""
import os
import sys

# Ensure application directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the run_proxy_azure module
from run_proxy_azure import app

# Azure Web Apps expects an app object
application = app

if __name__ == "__main__":
    # When running locally, use this
    port = int(os.environ.get("PORT", 8000))
    application.run(host="0.0.0.0", port=port)