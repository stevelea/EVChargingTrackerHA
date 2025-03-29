"""
Combined runner for Streamlit app and API server.
This script starts both the Streamlit app and the Flask API server in separate processes.
"""
import os
import subprocess
import sys
import threading
import time

def run_api_server():
    """Run the API server in a separate process"""
    print("Starting API server...")
    # Set environment variables for the API server
    api_env = os.environ.copy()
    api_env['API_PORT'] = '8000'  # Use a different port for the API
    
    # Start the API server with the environment variables
    api_process = subprocess.Popen([sys.executable, 'api.py'], env=api_env)
    
    # Wait for a few seconds to allow the API server to start
    time.sleep(3)
    
    # Check if the process is still running
    if api_process.poll() is None:
        print("API server started successfully")
    else:
        print("Failed to start API server")
        
    return api_process

def run_streamlit():
    """Run the Streamlit app in the current process"""
    print("Starting Streamlit app...")
    import streamlit.web.cli as stcli
    
    # Set up the Streamlit command
    args = [
        "streamlit", "run", "app.py",  
        "--server.port", "5000",
        "--server.address", "0.0.0.0",
        "--logger.level=debug"
    ]
    
    if os.environ.get('ENABLE_TEST_DATA') == 'true':
        # Add environment variable to enable test data
        os.environ['ENABLE_TEST_DATA'] = 'true'
        print("Test data enabled")
    
    # Run Streamlit
    sys.argv = args
    stcli.main()

if __name__ == '__main__':
    # Start the API server in a separate thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Run Streamlit in the main thread
    run_streamlit()