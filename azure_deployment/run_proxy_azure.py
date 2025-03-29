"""
Azure-specific proxy server for EV Charging Tracker app.

This script runs both the Streamlit web UI and Flask API server through a single port,
which is important for Azure App Service free tier that only exposes one port.

The proxy server determines if a request is for the API or the Streamlit UI and
routes it accordingly.
"""

import os
import sys
import threading
import time
import logging
from flask import Flask, request, redirect, Response
import requests
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configuration
STREAMLIT_PORT = 8501  # Streamlit internal port
API_PORT = 8505        # API internal port
EXTERNAL_PORT = int(os.environ.get("PORT", 8000))  # The port exposed by Azure

# Paths that should be handled by the API
API_PATHS = ['/api/', '/health']

# Global variables to track process status
streamlit_process = None
api_process = None


def is_api_request(path):
    """
    Determine if a request should be handled by the API server
    """
    return any(path.startswith(api_path) for api_path in API_PATHS)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    """
    Proxy incoming requests to either Streamlit or the API based on the path
    """
    full_path = request.full_path
    
    # Determine which service to route to
    if is_api_request(request.path):
        target_port = API_PORT
    else:
        target_port = STREAMLIT_PORT
    
    # Forward the request
    target_url = f"http://localhost:{target_port}/{path}{full_path[len('/' + path):]}"
    
    try:
        # Forward the request to the appropriate service
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=60
        )
        
        # Create a Flask Response
        response = Response(resp.content, resp.status_code)
        
        # Copy response headers
        for key, value in resp.headers.items():
            if key.lower() != 'location' or not resp.is_redirect:
                response.headers[key] = value
        
        # Handle redirects
        if resp.is_redirect:
            if 'location' in resp.headers:
                redirect_url = resp.headers['location']
                # Ensure redirect URLs point to our proxy
                if redirect_url.startswith(f'http://localhost:{target_port}'):
                    redirect_url = redirect_url.replace(f'http://localhost:{target_port}', '')
                return redirect(redirect_url, code=resp.status_code)
        
        return response
    except requests.RequestException as e:
        logger.error(f"Error proxying request to {target_url}: {str(e)}")
        return f"Proxy Error: {str(e)}", 503


def start_streamlit():
    """
    Start the Streamlit server
    """
    global streamlit_process
    
    logger.info("Starting Streamlit server...")
    streamlit_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(STREAMLIT_PORT),
        "--server.address", "localhost",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ], env=os.environ.copy())
    
    logger.info(f"Streamlit server started with PID {streamlit_process.pid}")


def start_api():
    """
    Start the API server
    """
    global api_process
    
    logger.info("Starting API server...")
    # Import here to avoid circular imports
    import api
    
    # Run the API server in a thread
    def run_api():
        api.app.run(host='localhost', port=API_PORT)
    
    api_thread = threading.Thread(target=run_api)
    api_thread.daemon = True
    api_thread.start()
    
    logger.info("API server started in thread")


def init_test_data():
    """
    Initialize test data if enabled
    """
    if os.environ.get('ENABLE_TEST_DATA', '').lower() == 'true':
        logger.info("Initializing test data...")
        try:
            import create_test_data
            create_test_data.create_sample_charging_data()
            logger.info("Test data initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing test data: {str(e)}")


def check_service_health():
    """
    Check if Streamlit and API servers are healthy
    """
    # Check Streamlit
    try:
        streamlit_response = requests.get(f"http://localhost:{STREAMLIT_PORT}/healthz", timeout=1)
        streamlit_healthy = streamlit_response.status_code == 200
    except requests.RequestException:
        streamlit_healthy = False
    
    # Check API
    try:
        api_response = requests.get(f"http://localhost:{API_PORT}/health", timeout=1)
        api_healthy = api_response.status_code == 200
    except requests.RequestException:
        api_healthy = False
    
    return streamlit_healthy, api_healthy


def wait_for_services():
    """
    Wait for both services to be healthy
    """
    logger.info("Waiting for services to start...")
    
    max_retries = 30
    retry_interval = 1
    
    for _ in range(max_retries):
        streamlit_healthy, api_healthy = check_service_health()
        
        if streamlit_healthy and api_healthy:
            logger.info("All services are healthy!")
            return True
        
        missing_services = []
        if not streamlit_healthy:
            missing_services.append("Streamlit")
        if not api_healthy:
            missing_services.append("API")
        
        logger.info(f"Waiting for services: {', '.join(missing_services)}")
        time.sleep(retry_interval)
    
    logger.error("Timed out waiting for services to start")
    return False


@app.before_first_request
def start_services():
    """
    Start all required services before handling the first request
    """
    # Initialize test data
    init_test_data()
    
    # Start Streamlit
    start_streamlit()
    
    # Start API
    start_api()
    
    # Wait for services to be ready
    wait_for_services()


@app.route('/health')
def health():
    """
    Health check endpoint
    """
    streamlit_healthy, api_healthy = check_service_health()
    
    if streamlit_healthy and api_healthy:
        return {
            "status": "healthy",
            "streamlit": "ok",
            "api": "ok"
        }
    else:
        status = {
            "status": "degraded",
            "streamlit": "ok" if streamlit_healthy else "down",
            "api": "ok" if api_healthy else "down"
        }
        return status, 503


if __name__ == "__main__":
    # Initialize everything outside of the request context for local testing
    init_test_data()
    start_streamlit()
    start_api()
    wait_for_services()
    
    # Start the Flask server
    port = int(os.environ.get("PORT", EXTERNAL_PORT))
    logger.info(f"Starting proxy server on port {port}...")
    
    # Use Gunicorn for production if available
    try:
        import gunicorn
        gunicorn_available = True
    except ImportError:
        gunicorn_available = False
    
    if gunicorn_available and not os.environ.get('FLASK_DEBUG'):
        logger.info("Starting server with Gunicorn")
        from gunicorn.app.base import BaseApplication
        
        class GunicornApp(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()
                
            def load_config(self):
                for key, value in self.options.items():
                    if key in self.cfg.settings and value is not None:
                        self.cfg.set(key.lower(), value)
                        
            def load(self):
                return self.application
        
        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': 4,
            'timeout': 120,
            'preload_app': True
        }
        
        GunicornApp(app, options).run()
    else:
        # Use Flask's development server
        logger.info("Starting server with Flask (development mode)")
        app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', '').lower() == 'true')