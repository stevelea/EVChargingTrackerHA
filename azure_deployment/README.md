# Azure Deployment for EV Charging Tracker

This directory contains all the files necessary to deploy the EV Charging Tracker application to Azure App Service's free tier.

## Quick Start

1. Create an Azure App Service using Python 3.10 on Linux with the F1 (Free) tier
2. Set up environment variables:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `WEBSITE_RUN_FROM_PACKAGE=0`
3. Deploy using one of these methods:
   - GitHub Actions (see `github-workflow-azure.yml`)
   - Local deployment with Azure CLI
   - Upload via FTP

See `AZURE_DEPLOYMENT.md` for detailed instructions.

## Directory Contents

- `app.py`: Azure-specific entry point
- `application.py`: WSGI application for Azure App Service
- `run_proxy_azure.py`: Azure-specific proxy server combining Streamlit and API
- `azure_storage.py`: Storage adapter for Azure (file-based for free tier)
- `requirements.txt`: Python dependencies for Azure
- `web.config`: Azure App Service configuration
- `AZURE_DEPLOYMENT.md`: Detailed deployment instructions
- `deploy.sh`: Script to prepare the application for deployment
- `github-workflow-azure.yml`: GitHub Actions workflow for automated deployment

## Free Tier Limitations

- 60 minutes of compute per day
- 1GB storage
- App sleeps after 20 minutes of inactivity
- Shared infrastructure (performance may vary)

## Data Storage

On the free tier, data is stored in local files. For a production deployment, consider:

1. Adding Azure Blob Storage (uncomment the code in `azure_storage.py`)
2. Adding Azure SQL Database for more robust storage
3. Upgrading to a Basic B1 tier plan for better performance

## Upgrading Beyond Free Tier

The application is designed to easily scale up when needed:

1. Change the App Service Plan to Basic B1 (or higher)
2. Uncomment the Azure Blob Storage code in `azure_storage.py`
3. Add AZURE_STORAGE_CONNECTION_STRING to your environment variables
4. Consider adding a managed identity for secure credential management