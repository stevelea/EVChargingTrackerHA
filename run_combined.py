"""
Combined runner for Streamlit app and API server.
This script starts the Streamlit app with integrated Flask API routes on the same port.
"""
import os
import sys
import threading
import time

def run_streamlit_with_api():
    """Run the Streamlit app with integrated API in the current process"""
    print("Starting Streamlit app with integrated API...")
    
    # First, start the Flask API server in a separate thread
    # This is done *before* Streamlit to ensure the API routes are ready
    import streamlit_api
    
    # Start the Flask server in a background thread
    streamlit_api.run_flask_with_streamlit(host='0.0.0.0', port=8505)
    
    # Wait a moment to ensure the Flask server is up
    time.sleep(2)
    
    # Now start Streamlit
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
    
    # Start the background refresh if available
    if hasattr(streamlit_api, 'BACKGROUND_AVAILABLE') and streamlit_api.BACKGROUND_AVAILABLE:
        import utils
        import background
        
        try:
            # Check if we have credentials with password
            credentials = utils.load_credentials()
            if credentials and 'email_address' in credentials and 'password' in credentials:
                print("Found saved credentials, starting background refresh task")
                background.start_background_refresh()
                print("Background refresh task started")
            else:
                print("No saved password found, background refresh not started automatically")
        except Exception as e:
            print(f"Warning: Failed to start background refresh: {str(e)}")
    
    # This will block until Streamlit exits
    stcli.main()

if __name__ == '__main__':
    # Start the combined app
    run_streamlit_with_api()