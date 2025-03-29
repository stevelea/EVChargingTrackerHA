# Deploying EV Charging Tracker to Azure

This guide provides step-by-step instructions for deploying the EV Charging Tracker application to Azure's free tier.

## Prerequisites

1. Azure account - [Create a free account](https://azure.microsoft.com/free/) if you don't have one.
2. Local copy of this repository with all the Azure deployment files.
3. [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) (optional, but helpful).
4. Google API Client ID and Secret for authentication.

## Deployment Options

### Option 1: Azure Portal Deployment (Easiest)

1. **Create an App Service**:
   - Log in to the [Azure Portal](https://portal.azure.com)
   - Click "Create a resource" > "Web App"
   - Select your subscription
   - Create a new resource group or use an existing one
   - Name your web app (this will be part of the URL)
   - Select "Code" as the publish method
   - Choose "Python 3.10" as the runtime stack
   - Select "Linux" as the operating system
   - Choose a region close to your users
   - For the App Service Plan, create a new one and select the Free F1 tier
   - Click "Review + create" and then "Create"

2. **Configure Application Settings**:
   - Once the App Service is created, go to "Settings" > "Configuration" > "Application settings"
   - Add the following settings:
     - `GOOGLE_CLIENT_ID`: Your Google API client ID
     - `GOOGLE_CLIENT_SECRET`: Your Google API client secret
     - `WEBSITE_RUN_FROM_PACKAGE`: `0`
     - `SCM_DO_BUILD_DURING_DEPLOYMENT`: `true`

3. **Deploy Your Code**:
   - Go to "Deployment" > "Deployment Center"
   - Choose your source control system (GitHub, Azure Repos, etc.)
   - Follow the prompts to connect to your repository
   - Select the branch to deploy
   - Azure will automatically deploy your code

### Option 2: GitHub Actions Deployment (Automated)

1. **Create an App Service** as described in Option 1.

2. **Configure GitHub Actions**:
   - Create a `.github/workflows/azure-deployment.yml` file in your repository:

   ```yaml
   name: Deploy to Azure Web App

   on:
     push:
       branches:
         - main

   jobs:
     build-and-deploy:
       runs-on: ubuntu-latest
       
       steps:
       - uses: actions/checkout@v2
       
       - name: Set up Python
         uses: actions/setup-python@v2
         with:
           python-version: '3.10'
           
       - name: Install dependencies
         run: |
           python -m pip install --upgrade pip
           pip install -r azure_deployment/requirements.txt
           
       - name: Deploy to Azure Web App
         uses: azure/webapps-deploy@v2
         with:
           app-name: 'your-app-name'
           publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
   ```

3. **Set Up GitHub Secrets**:
   - In your GitHub repository, go to "Settings" > "Secrets"
   - Add the following secrets:
     - `AZURE_WEBAPP_PUBLISH_PROFILE`: The publish profile from your Azure App Service (download from App Service > Overview > Get publish profile)

4. **Push to GitHub**:
   - Push your code to the main branch
   - GitHub Actions will deploy your code to Azure

### Option 3: Manual Deployment (Direct Control)

1. **Prepare Your Code**:
   - Run the deployment script to prepare your files:
     ```
     chmod +x azure_deployment/deploy.sh
     ./azure_deployment/deploy.sh
     ```

2. **Create an App Service** as described in Option 1.

3. **Deploy Using Azure CLI**:
   ```
   az login
   az webapp up --name YourAppName --resource-group YourResourceGroup --sku F1 --runtime "PYTHON|3.10" --location "East US" --os-type linux
   ```

4. **Configure Application Settings** as described in Option 1.

## Free Tier Limitations

- **Compute Time**: 60 minutes per day
- **Storage**: 1GB
- **App will sleep** after 20 minutes of inactivity
- **Shared Infrastructure**: Performance might vary

## Accessing Your Application

After deployment, your application will be available at:
```
https://your-app-name.azurewebsites.net
```

## Troubleshooting

1. **Application Doesn't Start**:
   - Check the logs in App Service > "Monitoring" > "Log stream"
   - Verify your application settings are correct
   - Make sure `WEBSITE_RUN_FROM_PACKAGE` is set to `0`

2. **Google Authentication Fails**:
   - Ensure your Google API client ID and secret are correctly set in application settings
   - Add your Azure app URL to the authorized redirect URIs in your Google API Console

3. **Database Issues**:
   - The free tier uses local file storage
   - If you need a database, consider adding Azure SQL with a basic tier (additional cost)

4. **Performance Issues**:
   - Free tier has limited resources
   - App will "wake up" after sleeping, causing initial delay
   - Consider upgrading to a basic tier for better performance (additional cost)

## Updating Your Application

To update your application:

1. Make changes to your code locally
2. Commit and push changes to your repository
3. If using GitHub Actions, it will automatically deploy
4. If using manual deployment, run the deployment script and re-deploy

## Moving Beyond Free Tier

When ready to move beyond the free tier limitations:

1. Scale up your App Service Plan to a Basic B1 tier
2. Add Azure Blob Storage for data persistence (uncomment the Blob Storage code in `azure_storage.py`)
3. Add Azure SQL Database for more robust data storage
4. Configure autoscaling for handling traffic spikes