"""
Runner script to start the proxy application.
This script starts a proxy server on port 5000 that serves both the API and Streamlit UI.
"""
import os
import sys
import subprocess
import threading
import time

def run_streamlit_server():
    """
    Run Streamlit server on a non-standard port that will be proxied.
    We use port 8505 here, as the proxy will intercept requests to port 5000.
    """
    print("Starting Streamlit server on port 8505...")
    
    # Set up environment variables
    streamlit_env = os.environ.copy()
    if os.environ.get('ENABLE_TEST_DATA') == 'true':
        # Add environment variable to enable test data
        streamlit_env['ENABLE_TEST_DATA'] = 'true'
        print("Test data enabled")
    
    # Create Streamlit process (running on port 8505)
    streamlit_args = [
        sys.executable, 
        "-m", "streamlit", 
        "run", 
        "app.py",
        "--server.port", 
        "8505",
        "--server.address", 
        "localhost"
    ]
    
    streamlit_process = subprocess.Popen(
        streamlit_args,
        env=streamlit_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Start a thread to read and log Streamlit output
    def log_streamlit_output():
        for line in streamlit_process.stdout:
            print(f"Streamlit: {line.strip()}")
    
    log_thread = threading.Thread(target=log_streamlit_output)
    log_thread.daemon = True
    log_thread.start()
    
    # Wait for Streamlit to start
    time.sleep(5)
    print("Streamlit is running on port 8505")
    
    return streamlit_process

def run_proxy_server():
    """
    Run the proxy server that will handle both API and Streamlit requests.
    This is what users will interact with on port 5000.
    """
    print("Starting proxy server on port 5000...")
    
    # Set the Streamlit port in environment
    proxy_env = os.environ.copy()
    proxy_env['STREAMLIT_HOST'] = 'localhost:8505'
    
    # For the proxy server - update constants
    proxy_app_src = "proxy_app.py"
    with open(proxy_app_src, "r") as f:
        content = f.read()
    
    # Update Streamlit host parameter
    content = content.replace('STREAMLIT_HOST = "localhost:5000"', 'STREAMLIT_HOST = "localhost:8505"')
    
    with open(proxy_app_src, "w") as f:
        f.write(content)
    
    print("Updated proxy configuration with localhost:8505 for Streamlit host")
    
    # Start the background refresh if available
    try:
        import utils
        import background
        
        credentials = utils.load_credentials()
        if credentials and 'email_address' in credentials and 'password' in credentials:
            print("Found saved credentials, starting background refresh task")
            background.start_background_refresh()
            print("Background refresh task started")
        else:
            print("No saved password found, background refresh not started automatically")
    except Exception as e:
        print(f"Warning: Failed to start background refresh: {str(e)}")
    
    # Run the proxy server (this will block until it exits)
    proxy_args = [sys.executable, "proxy_app.py"]
    subprocess.run(
        proxy_args,
        env=proxy_env
    )

if __name__ == "__main__":
    # Start Streamlit in the background
    streamlit_process = run_streamlit_server()
    
    try:
        # Run proxy in the foreground (blocking)
        run_proxy_server()
    finally:
        # Clean up when the proxy exits
        if streamlit_process:
            print("Terminating Streamlit process...")
            streamlit_process.terminate()