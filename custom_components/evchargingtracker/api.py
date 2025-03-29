"""API client for the EV Charging Tracker."""
import asyncio
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
        # Clean up the base URL - remove any trailing slashes
        self._base_url = base_url.rstrip("/")
        
        # CRITICAL CHANGE: For Replit URLs, ensure we're using HTTPS without port specification
        if '.replit.app' in self._base_url:
            # Extract the domain without protocol or port
            domain_only = self._base_url
            # Remove protocol if present
            domain_only = domain_only.replace('http://', '').replace('https://', '')
            # Remove port if present
            if ':' in domain_only:
                domain_only = domain_only.split(':')[0]
            # Use HTTPS with the clean domain
            self._base_url = f"https://{domain_only}"
            _LOGGER.info(f"Detected Replit URL, using: {self._base_url}")
            
        self._session = session
        self._api_key = api_key
        # Use X-API-Key header (note the capitalization) to match the Flask API's expected format
        self._headers = {"X-API-Key": api_key} if api_key else {}

    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the API."""
        # Ensure params is a dictionary
        params = params or {}
        
        # Format the base URL correctly (remove trailing slash if present)
        base_url = self._base_url.rstrip('/')
        
        # Special handling for Replit URLs
        is_replit_url = '.replit.app' in base_url
        
        # Normalize the endpoint path
        # For Replit URLs, our API routes all have '/api/' prefix
        
        # Check if endpoint already includes /api/ in some format
        has_api_prefix = False
        if endpoint.startswith('/api/') or endpoint.startswith('api/'):
            has_api_prefix = True
        
        # Format to ensure it has a leading slash
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
            
        # Add /api prefix if needed
        if not has_api_prefix:
            # If endpoint already has a leading slash but not the API prefix, add the prefix
            if not endpoint.startswith('/api/'):
                endpoint = '/api' + endpoint
        
        # Log the final endpoint format
        _LOGGER.debug("Using endpoint format: %s for %s URL", 
                      endpoint, "Replit" if is_replit_url else "standard")
        
        # Special handling for Replit URLs - ensure HTTPS but DO NOT add port
        if '.replit.app' in base_url:
            # For Replit deployments, ensure it uses HTTPS
            if not base_url.startswith('https://') and not base_url.startswith('http://'):
                base_url = f"https://{base_url}"
                
            # CRITICAL CHANGE: Remove any port specification from Replit URLs
            # Extract the domain without any port
            if ':' in base_url.replace('https://', '').replace('http://', ''):
                # There's a port specified, remove it
                protocol = 'https://' if base_url.startswith('https://') else 'http://'
                domain = base_url.replace('https://', '').replace('http://', '').split(':')[0]
                base_url = f"{protocol}{domain}"
                
            _LOGGER.debug("Adjusted Replit URL (no port) to: %s", base_url)
        
        # Combine to form the complete URL
        url = f"{base_url}{endpoint}"
        _LOGGER.debug("Final API URL: %s", url)
        
        _LOGGER.debug("Making request to %s with headers: %s, params: %s", 
                    url, self._headers, params)
        
        try:
            # Set a reasonable timeout for the request (5 seconds)
            timeout = aiohttp.ClientTimeout(total=10)
            async with self._session.get(
                url, 
                headers=self._headers, 
                params=params,
                timeout=timeout,
                raise_for_status=False  # Don't raise for HTTP errors, handle manually
            ) as response:
                # Check status code
                if response.status != 200:
                    status_text = response.reason if hasattr(response, 'reason') else 'Unknown'
                    body = await response.text()
                    _LOGGER.error(
                        "API request to %s failed with status %d (%s): %s", 
                        url, response.status, status_text, body[:100]
                    )
                    return {}
                
                # Try to parse JSON response
                try:
                    result = await response.json()
                    _LOGGER.debug("API response: %s", result)
                    return result
                except ValueError as json_error:
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to parse JSON from %s: %s. Raw response: %s", 
                        url, json_error, text[:100]
                    )
                    return {}
                    
        except asyncio.TimeoutError:
            _LOGGER.error("Request to %s timed out after 10 seconds", url)
            return {}
        except aiohttp.ClientResponseError as error:
            _LOGGER.error("HTTP error from %s: %s", url, error)
            return {}
        except aiohttp.ClientError as error:
            _LOGGER.error("Network error connecting to %s: %s", url, error)
            return {}
        except Exception as error:  # pylint: disable=broad-except
            _LOGGER.error("Unexpected error calling %s: %s", url, error)
            return {}

    async def async_health_check(self) -> Dict[str, Any]:
        """Check if the API is running."""
        try:
            # Try different API endpoints and URL configurations
            # Store results for debugging
            all_attempts = []

            # First attempt - standard api/health endpoint with existing URL
            _LOGGER.info("Attempt 1: Making health check request to api/health endpoint with current URL")
            try:
                result1 = await self._request("api/health")
                all_attempts.append(("api/health with current URL", result1))
                _LOGGER.info("Attempt 1 response: %s", result1)
                if result1 and isinstance(result1, dict) and "status" in result1:
                    return result1
            except Exception as e1:
                _LOGGER.warning("Attempt 1 failed: %s", e1)
                all_attempts.append(("api/health with current URL", f"Error: {e1}"))

            # Second attempt - try without the /api prefix 
            _LOGGER.info("Attempt 2: Trying health endpoint without api prefix")
            try:
                result2 = await self._request("health")
                all_attempts.append(("health without prefix", result2))
                _LOGGER.info("Attempt 2 response: %s", result2)
                if result2 and isinstance(result2, dict) and "status" in result2:
                    return result2
            except Exception as e2:
                _LOGGER.warning("Attempt 2 failed: %s", e2)
                all_attempts.append(("health without prefix", f"Error: {e2}"))

            # Third attempt - try direct URL hitting the API endpoint directly using path format
            if '.replit.app' in self._base_url:
                clean_domain = self._base_url.replace('http://', '').replace('https://', '').split(':')[0]
                direct_url = f"https://{clean_domain}/api/health"
                _LOGGER.info("Attempt 3: Trying direct URL with path format: %s", direct_url)
                try:
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with self._session.get(
                        direct_url, headers=self._headers, timeout=timeout
                    ) as response:
                        if response.status == 200:
                            try:
                                result3 = await response.json()
                                all_attempts.append(("direct URL with path", result3))
                                _LOGGER.info("Attempt 3 response: %s", result3)
                                if result3 and isinstance(result3, dict) and "status" in result3:
                                    return result3
                            except Exception as e3:
                                _LOGGER.warning("Attempt 3 parsing failed: %s", e3)
                                all_attempts.append(("direct URL with path", f"Parse error: {e3}"))
                        else:
                            _LOGGER.warning("Attempt 3 failed with status: %s", response.status)
                            all_attempts.append(("direct URL with path", f"Status: {response.status}"))
                except Exception as e3:
                    _LOGGER.warning("Attempt 3 request failed: %s", e3)
                    all_attempts.append(("direct URL with path", f"Error: {e3}"))

            # Fourth attempt - try a different endpoint (/api/summary) on Replit
            if '.replit.app' in self._base_url:
                clean_domain = self._base_url.replace('http://', '').replace('https://', '').split(':')[0]
                # Use a different endpoint for variety
                direct_url = f"https://{clean_domain}/api/summary"
                _LOGGER.info("Attempt 4: Trying summary endpoint directly: %s", direct_url)
                try:
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with self._session.get(
                        direct_url, headers=self._headers, timeout=timeout
                    ) as response:
                        if response.status == 200:
                            try:
                                result4 = await response.json()
                                all_attempts.append(("direct summary endpoint", result4))
                                _LOGGER.info("Attempt 4 response: %s", result4)
                                if result4 and isinstance(result4, dict):
                                    # Convert summary response to standard health format
                                    return {"status": "ok", "data_source": "summary", "timestamp": result4.get("last_update", "")}
                            except Exception as e4:
                                _LOGGER.warning("Attempt 4 parsing failed: %s", e4)
                                all_attempts.append(("direct summary endpoint", f"Parse error: {e4}"))
                        else:
                            _LOGGER.warning("Attempt 4 failed with status: %s", response.status)
                            all_attempts.append(("direct summary endpoint", f"Status: {response.status}"))
                except Exception as e4:
                    _LOGGER.warning("Attempt 4 request failed: %s", e4)
                    all_attempts.append(("direct summary endpoint", f"Error: {e4}"))

            # If all approaches fail, try the summary endpoint as a last resort
            _LOGGER.info("Attempt 5: Trying summary endpoint as last resort")
            try:
                result5 = await self._request("api/summary")
                all_attempts.append(("summary endpoint", result5))
                _LOGGER.info("Attempt 5 response: %s", result5)
                if result5 and isinstance(result5, dict):
                    # Return a properly formatted health response
                    return {"status": "ok", "data_source": "summary", "timestamp": result5.get("last_update", "")}
            except Exception as e5:
                _LOGGER.warning("Attempt 5 failed: %s", e5)
                all_attempts.append(("summary endpoint", f"Error: {e5}"))

            # If we get here, log all attempts for debugging
            _LOGGER.error("All health check attempts failed. Attempts: %s", all_attempts)
            
            # Return empty dict as fallback
            return {}
            
        except Exception as e:
            _LOGGER.error("Health check error in main function: %s", e)
            return {}

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