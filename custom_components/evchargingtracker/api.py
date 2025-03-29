"""API client for the EV Charging Tracker."""
import logging
from typing import Dict, Any, Optional

import aiohttp

_LOGGER = logging.getLogger(__name__)


class EVChargingTrackerApiClient:
    """API client for the EV Charging Tracker API."""

    def __init__(
        self, session: aiohttp.ClientSession, base_url: str, api_key: Optional[str] = None
    ):
        """Initialize the API client."""
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        # Use X-API-Key header (note the capitalization) to match the Flask API's expected format
        self._headers = {"X-API-Key": api_key} if api_key else {}

    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the API."""
        # Ensure endpoint is properly formatted with leading slash
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
            
        url = f"{self._base_url}{endpoint}"
        
        try:
            # Log the request details for debugging
            _LOGGER.debug("Making request to %s with headers: %s, params: %s", 
                         url, self._headers, params)
                         
            async with self._session.get(url, headers=self._headers, params=params) as response:
                response.raise_for_status()
                result = await response.json()
                _LOGGER.debug("API response: %s", result)
                return result
        except aiohttp.ClientResponseError as error:
            _LOGGER.error("Error fetching data from %s: %s", url, error)
            return {}
        except aiohttp.ClientError as error:
            _LOGGER.error("Error connecting to %s: %s", url, error)
            return {}
        except Exception as error:  # pylint: disable=broad-except
            _LOGGER.error("Unexpected error calling %s: %s", url, error)
            return {}

    async def async_health_check(self) -> Dict[str, Any]:
        """Check if the API is running."""
        return await self._request("api/health")

    async def async_get_charging_data(
        self,
        email: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        provider: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get charging data with optional filtering."""
        params = {}
        if email:
            params["email"] = email
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if provider:
            params["provider"] = provider
        if location:
            params["location"] = location

        result = await self._request("api/charging-data", params)
        
        # Handle different response formats - sometimes the API returns a direct list of records
        # instead of wrapping them in a 'data' field
        if isinstance(result, list):
            return {"data": result}
        
        # If it's an empty dict (error case handled in _request), wrap in expected format
        if not result:
            return {"data": []}
            
        # Return the result as-is if it's already in the expected format
        return result

    async def async_get_charging_record(
        self, record_id: str, email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a specific charging record by ID."""
        params = {}
        if email:
            params["email"] = email

        return await self._request(f"api/charging-data/{record_id}", params)

    async def async_get_charging_summary(
        self, email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a summary of charging data statistics."""
        params = {}
        if email:
            params["email"] = email

        result = await self._request("api/summary", params)
        
        # If no results or an error occurred, return an empty summary
        if not result:
            return {
                "total_energy_kwh": 0.0,
                "total_cost": 0.0,
                "avg_cost_per_kwh": 0.0,
                "record_count": 0
            }
            
        return result