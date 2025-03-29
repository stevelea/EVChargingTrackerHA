# Quick Start Guide: Deploy to Azure Free Tier

This guide will help you deploy the EV Charging Tracker application to Azure App Service's free tier in just a few minutes.

## Prerequisites

1. An Azure account ([Create a free account](https://azure.microsoft.com/free/) if you don't have one)
2. Google API Client ID and Secret (for authentication)

## Deployment Steps

### 1. Prepare Your Files

The `azure_deployment` directory already contains all the necessary files for deployment. No additional preparation is needed.

### 2. Create an Azure App Service

1. Log in to the [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" > "Web App"
3. Fill in the basic information:
   - **Subscription**: Select your subscription
   - **Resource Group**: Create new (e.g., "ev-charging-tracker")
   - **Name**: Choose a unique name (this will be your app's URL)
   - **Publish**: Code
   - **Runtime stack**: Python 3.10
   - **Operating System**: Linux
   - **Region**: Choose a region close to you
4. Click "Review + create" and then "Create"
5. Wait for the deployment to complete (1-2 minutes)

### 3. Configure Application Settings

1. Once the App Service is created, navigate to it in the Azure Portal
2. Go to "Settings" > "Configuration" > "Application settings"
3. Click "New application setting" and add the following settings:
   - Name: `GOOGLE_CLIENT_ID`, Value: Your Google API client ID
   - Name: `GOOGLE_CLIENT_SECRET`, Value: Your Google API client secret
   - Name: `WEBSITE_RUN_FROM_PACKAGE`, Value: `0`
   - Name: `ENABLE_TEST_DATA`, Value: `true` (optional, adds sample data)
4. Click "Save" at the top of the page

### 4. Deploy Your Application

#### Option A: Deploy Using Azure Portal (Easiest)

1. In your App Service, go to "Deployment" > "Deployment Center"
2. Choose "Local Git" as the source
3. Click "Save" at the top of the page
4. Go to "Deployment Credentials" and set up your deployment credentials
5. Zip up the contents of the `azure_deployment` directory
6. Go back to "Deployment Center" and click "Browse" to upload your zip file
7. Click "Deploy" to deploy your application

#### Option B: Deploy Using GitHub

1. Create a GitHub repository and push your code to it
2. In your App Service, go to "Deployment" > "Deployment Center"
3. Choose "GitHub" as the source
4. Connect to your GitHub account and select the repository
5. Set up the deployment configurations and click "Save"

### 5. Test Your Application

1. Once deployment is complete, your application will be available at:
   `https://your-app-name.azurewebsites.net`
2. Open this URL in your browser
3. The application should load and you can start using it

## Troubleshooting

- **Deployment Fails**: Check the logs in "Monitoring" > "Log stream"
- **Application Doesn't Start**: Verify your application settings are correct
- **Auth Issues**: Ensure your Google API credentials are correct and have the right redirect URLs

## Limitations of Free Tier

- 60 minutes of compute per day
- App will sleep after 20 minutes of inactivity
- Limited storage (1GB)
- Shared infrastructure with other free apps