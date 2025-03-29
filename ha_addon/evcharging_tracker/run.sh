#!/usr/bin/env bashio

bashio::log.info "Starting EV Charging Tracker add-on..."

# Get configuration
USE_GUEST_MODE=$(bashio::config 'use_guest_mode')
GUEST_PASSWORD=$(bashio::config 'guest_password')
REFRESH_INTERVAL=$(bashio::config 'background_refresh_interval')

# Export configuration as environment variables
export EVCT_GUEST_MODE=$USE_GUEST_MODE
export EVCT_GUEST_PASSWORD=$GUEST_PASSWORD
export EVCT_REFRESH_INTERVAL=$REFRESH_INTERVAL

# Set data directory
export EVCT_DATA_DIR="/data"

# Ensure the data directory exists
mkdir -p /data

# Start the combined app (Streamlit + API)
bashio::log.info "Starting combined proxy app with Streamlit and API endpoints..."
cd /app
python run_ha_addon.py