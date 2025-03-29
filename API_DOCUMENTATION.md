# EV Charging Data API Documentation

This API provides access to electric vehicle charging data stored in the EV Charging Dashboard application. It allows external applications to query and retrieve charging data in a standardized format.

## Base URL

The API is available at:
```
http://localhost:8000
```

For deployed applications, the base URL will be the host where the API is running.

## Authentication

All API endpoints (except the health check) require authentication using an API key. You can provide the API key in one of two ways:

1. As a query parameter: `?api_key=your-api-key`
2. As a request header: `X-API-Key: your-api-key`

## Endpoints

### Health Check

Check if the API is running.

```
GET /api/health
```

**Parameters:** None

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-03-28T23:33:18.373523"
}
```

### Get Charging Data

Retrieve charging data with optional filtering.

```
GET /api/charging-data
```

**Parameters:**
- `email` (optional): Filter by user email
- `start_date` (optional): Filter by date range (start date in YYYY-MM-DD format)
- `end_date` (optional): Filter by date range (end date in YYYY-MM-DD format)
- `provider` (optional): Filter by charging provider (partial match)
- `location` (optional): Filter by charging location (partial match)

**Response:**
```json
{
  "count": 8,
  "data": [
    {
      "cost_per_kwh": 0.55,
      "date": "2025-03-24T00:00:00",
      "duration": "105 min",
      "id": "sample-record-22",
      "latitude": -33.889131,
      "location": "Chargefox Ultra-Rapid, M1 Pacific Motorway, Knockrow NSW 2479",
      "longitude": 151.737149,
      "peak_kw": 15.7,
      "provider": "ChargePoint",
      "source": "Email",
      "time": "19:23:00",
      "total_cost": 19.44,
      "total_kwh": 35.34
    },
    // ... more records
  ]
}
```

### Get Specific Charging Record

Retrieve a specific charging record by ID.

```
GET /api/charging-data/{record_id}
```

**Parameters:**
- `email` (optional): Filter by user email

**Response:**
```json
{
  "cost_per_kwh": 0.55,
  "date": "2025-03-24T00:00:00",
  "duration": "105 min",
  "id": "sample-record-22",
  "latitude": -33.889131,
  "location": "Chargefox Ultra-Rapid, M1 Pacific Motorway, Knockrow NSW 2479",
  "longitude": 151.737149,
  "peak_kw": 15.7,
  "provider": "ChargePoint",
  "source": "Email",
  "time": "19:23:00",
  "total_cost": 19.44,
  "total_kwh": 35.34
}
```

### Get Charging Summary

Get summary statistics for charging data.

```
GET /api/summary
```

**Parameters:**
- `email` (optional): Filter by user email

**Response:**
```json
{
  "avg_cost_per_kwh": 0.48930147883987135,
  "date_range": {
    "first_date": "2024-12-30T00:00:00",
    "last_date": "2025-03-24T00:00:00"
  },
  "locations": 7,
  "providers": 8,
  "record_count": 30,
  "top_locations": [
    {
      "location": "Chargefox Ultra-Rapid, M1 Pacific Motorway, Knockrow NSW 2479",
      "total_kwh": 158.0
    },
    // ... more locations
  ],
  "top_providers": [
    {
      "provider": "Chargefox",
      "total_kwh": 185.72
    },
    // ... more providers
  ],
  "total_cost": 392.41,
  "total_energy_kwh": 801.98
}
```

### Get Users (Admin Only)

Get a list of users with data in the system. This endpoint requires an administrator key.

```
GET /api/users
```

**Parameters:** None

**Headers:**
- `X-API-Key`: Your API key
- `X-Admin-Key`: Administrator key

**Response:**
```json
{
  "count": 1,
  "users": [
    "test@example.com"
  ]
}
```

## Error Responses

The API returns standard HTTP status codes to indicate success or failure:

- `200 OK`: The request was successful
- `400 Bad Request`: The request was invalid
- `401 Unauthorized`: API key is missing or invalid
- `403 Forbidden`: Access denied (e.g., for admin endpoints)
- `404 Not Found`: The requested resource was not found
- `500 Internal Server Error`: An unexpected error occurred

Error responses include a JSON body with details:

```json
{
  "error": "Not Found",
  "message": "Charging record with ID invalid-id not found"
}
```

## Python Client Library

A Python client library is available to simplify integration with the API. See `api_client.py` for usage examples.

### Basic Usage:

```python
from api_client import EVChargingAPIClient

# Create client
client = EVChargingAPIClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Check API health
health = client.health_check()
print("API Status:", health)

# Get charging data
data = client.get_charging_data(email="user@example.com")
print(f"Retrieved {data.get('count', 0)} charging records")

# Get summary statistics
summary = client.get_charging_summary()
print("Summary:", json.dumps(summary, indent=2))
```

## Filtering Examples

### Filter by Date Range

```
GET /api/charging-data?start_date=2025-01-01&end_date=2025-01-31
```

### Filter by Provider

```
GET /api/charging-data?provider=Chargefox
```

### Filter by Location and User

```
GET /api/charging-data?location=Sydney&email=user@example.com
```

### Multiple Filters

```
GET /api/charging-data?email=user@example.com&provider=Tesla&start_date=2025-01-01
```