"""
API server for exposing the EV charging data to external applications.
This provides endpoints to access stored charging data in a RESTful manner.
"""

from flask import Flask, jsonify, request, abort
import os
import json
import hmac
import data_storage
from datetime import datetime
import hashlib

app = Flask(__name__)

# API key variable (for simple authentication)
API_KEY = os.environ.get('API_KEY', 'ev-charging-api-key')

# Helper function to validate API key
def validate_api_key():
    """Validate the API key from the request"""
    provided_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    
    if not provided_key:
        return False
    
    # Compare in a way that's not vulnerable to timing attacks
    return hmac.compare_digest(provided_key, API_KEY)

# Helper function to convert date strings to datetime objects
def parse_date_param(date_str):
    """Parse date string from request parameters"""
    if not date_str:
        return None
        
    try:
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
                
        # If all formats fail, return None
        return None
    except Exception:
        return None

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint that doesn't require authentication"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/charging-data', methods=['GET'])
def get_charging_data():
    """Get charging data, optionally filtered by parameters"""
    # Validate API key
    if not validate_api_key():
        abort(401, description="Invalid or missing API key")
    
    # Get optional query parameters
    email = request.args.get('email')
    start_date = parse_date_param(request.args.get('start_date'))
    end_date = parse_date_param(request.args.get('end_date'))
    provider = request.args.get('provider')
    location = request.args.get('location')
    
    # Load data for the specified user
    charging_data = data_storage.load_charging_data(email_address=email)
    
    # Apply filters if specified
    if charging_data:
        # Filter by date range if specified
        if start_date or end_date:
            charging_data = data_storage.filter_data_by_date_range(
                charging_data, start_date, end_date
            )
        
        # Filter by provider if specified
        if provider:
            charging_data = [
                record for record in charging_data 
                if record.get('provider') and provider.lower() in record.get('provider', '').lower()
            ]
            
        # Filter by location if specified
        if location:
            charging_data = [
                record for record in charging_data 
                if record.get('location') and location.lower() in record.get('location', '').lower()
            ]
    
    # Return the filtered data
    return jsonify({
        'count': len(charging_data),
        'data': charging_data
    })

@app.route('/api/charging-data/<record_id>', methods=['GET'])
def get_charging_record(record_id):
    """Get a specific charging record by ID"""
    # Validate API key
    if not validate_api_key():
        abort(401, description="Invalid or missing API key")
    
    # Get optional email parameter
    email = request.args.get('email')
    
    # Load data for the specified user
    charging_data = data_storage.load_charging_data(email_address=email)
    
    # Find the record with the matching ID
    for record in charging_data:
        if record.get('id') == record_id:
            return jsonify(record)
    
    # If no matching record is found
    abort(404, description=f"Charging record with ID {record_id} not found")

@app.route('/api/summary', methods=['GET'])
def get_charging_summary():
    """Get a summary of charging data statistics"""
    # Validate API key
    if not validate_api_key():
        abort(401, description="Invalid or missing API key")
    
    # Get optional email parameter
    email = request.args.get('email')
    
    # Load data for the specified user
    charging_data = data_storage.load_charging_data(email_address=email)
    
    # Convert to DataFrame for easier aggregation
    import pandas as pd
    if not charging_data:
        return jsonify({
            'status': 'no_data',
            'message': 'No charging data available'
        })
    
    # Create a pandas DataFrame
    df = pd.DataFrame(charging_data)
    
    # Ensure numeric columns
    numeric_cols = ['total_kwh', 'total_cost', 'peak_kw']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calculate summary statistics
    summary = {
        'record_count': len(charging_data),
        'locations': len(df['location'].unique()) if 'location' in df.columns else 0,
        'providers': len(df['provider'].unique()) if 'provider' in df.columns else 0,
        'total_energy_kwh': float(df['total_kwh'].sum()) if 'total_kwh' in df.columns else 0,
        'total_cost': float(df['total_cost'].sum()) if 'total_cost' in df.columns else 0,
        'avg_cost_per_kwh': float(df['total_cost'].sum() / df['total_kwh'].sum()) 
                            if 'total_cost' in df.columns and 'total_kwh' in df.columns 
                            and df['total_kwh'].sum() > 0 else 0,
        'date_range': {
            'first_date': df['date'].min().isoformat() if 'date' in df.columns else None,
            'last_date': df['date'].max().isoformat() if 'date' in df.columns else None
        } if 'date' in df.columns else {}
    }
    
    # Top providers by kWh
    if 'provider' in df.columns and 'total_kwh' in df.columns:
        provider_kwh = df.groupby('provider')['total_kwh'].sum().sort_values(ascending=False)
        summary['top_providers'] = [
            {'provider': provider, 'total_kwh': float(kwh)}
            for provider, kwh in provider_kwh.items()
        ][:5]  # Top 5 providers
    
    # Top locations by kWh
    if 'location' in df.columns and 'total_kwh' in df.columns:
        location_kwh = df.groupby('location')['total_kwh'].sum().sort_values(ascending=False)
        summary['top_locations'] = [
            {'location': location, 'total_kwh': float(kwh)}
            for location, kwh in location_kwh.items()
        ][:5]  # Top 5 locations
    
    return jsonify(summary)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get list of users with data in the system"""
    # Validate API key
    if not validate_api_key():
        abort(401, description="Invalid or missing API key")
    
    # Only administrators can access this endpoint
    admin_key = request.headers.get('X-Admin-Key')
    if admin_key != os.environ.get('ADMIN_KEY', 'ev-charging-admin-key'):
        abort(403, description="Administrator access required")
    
    # This implementation is specific to file storage
    users = []
    
    try:
        # Check if data directory exists
        if os.path.exists(data_storage.DATA_DIR):
            # Look for user data files
            for filename in os.listdir(data_storage.DATA_DIR):
                if filename.startswith('charging_data_') and filename.endswith('.json'):
                    # Extract email from filename
                    email_part = filename[len('charging_data_'):-len('.json')]
                    email = email_part.replace('_at_', '@').replace('_dot_', '.')
                    users.append(email)
        
        # If we're on Replit, also check the database
        if data_storage.ON_REPLIT:
            import replit
            # Look for keys that match the pattern
            for key in replit.db.keys():
                if key.startswith('charging_data_'):
                    # Extract email from key
                    email_part = key[len('charging_data_'):]
                    email = email_part.replace('_at_', '@').replace('_dot_', '.')
                    if email not in users:
                        users.append(email)
    except Exception as e:
        # Log the error but return what we have
        print(f"Error retrieving users: {str(e)}")
    
    return jsonify({
        'count': len(users),
        'users': users
    })

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': str(error.description)
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'error': 'Unauthorized',
        'message': str(error.description)
    }), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        'error': 'Forbidden',
        'message': str(error.description)
    }), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': str(error.description)
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

# Main entry point
if __name__ == '__main__':
    
    # Set default port to 5001 to avoid conflict with Streamlit
    port = int(os.environ.get('API_PORT', 5001))
    
    # Set host to make it accessible from outside
    host = os.environ.get('API_HOST', '0.0.0.0')
    
    # Generate a random API key if one isn't set
    if API_KEY == 'ev-charging-api-key':
        print("WARNING: Using default API key. Set API_KEY environment variable for better security.")
    
    # Start the server
    print(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=False)