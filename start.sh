#!/bin/bash

# Run the combined proxy app that handles both Streamlit and API
echo "Starting combined app on port 5000..."
ENABLE_TEST_DATA=true exec python run_proxy.py