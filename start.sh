#!/bin/bash

# Start the API server in the background
echo "Starting API server on port 5001..."
python api.py &

# Start the Streamlit app in the foreground
echo "Starting Streamlit app on port 5000..."
exec streamlit run app.py --server.port=5000 --server.address=0.0.0.0 --logger.level=debug