#!/usr/bin/env python3
"""
Test script for the EV Charging Tracker Home Assistant integration.

This script simulates how the integration would interact with the API
and can be used to test connectivity and data retrieval outside of
Home Assistant.
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import aiohttp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
_LOGGER = logging.getLogger("evchargingtracker_test")


class EVChargingTrackerApiClient:
    """API client for the EV Charging Tracker API."""

    def __init__(
        self, session: aiohttp.ClientSession, base_url: str, api_key: Optional[str] = None
    ):
        """Initialize the API client."""
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._headers = {"X-API-KEY": api_key} if api_key else {}

    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the API."""
        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with self._session.get(url, headers=self._headers, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as error:
            _LOGGER.error("Error fetching data from %s: %s", url, error)
            return {}
        except aiohttp.ClientError as error:
            _LOGGER.error("Error connecting to %s: %s", url, error)
            return {}
        except Exception as error:
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

        return await self._request("api/charging-data", params)

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

        return await self._request("api/summary", params)


async def test_api_connection(host: str, port: int, api_key: Optional[str] = None):
    """Test the API connection and retrieve data."""
    base_url = f"http://{host}:{port}"
    
    async with aiohttp.ClientSession() as session:
        client = EVChargingTrackerApiClient(session, base_url, api_key)
        
        # Check connection
        _LOGGER.info("Testing connection to %s...", base_url)
        health_result = await client.async_health_check()
        if not health_result or "status" not in health_result or health_result["status"] != "ok":
            _LOGGER.error("Connection failed: %s", health_result)
            return
        
        _LOGGER.info("✓ Connection successful!")
        
        # Get summary data
        _LOGGER.info("Retrieving charging summary...")
        summary = await client.async_get_charging_summary()
        if not summary:
            _LOGGER.error("Failed to retrieve summary data: %s", summary)
        else:
            _LOGGER.info("✓ Summary data retrieved")
            _LOGGER.info("Summary data: %s", json.dumps(summary, indent=2))
        
        # Get charging data
        _LOGGER.info("Retrieving charging data...")
        charging_data = await client.async_get_charging_data()
        if not charging_data:
            _LOGGER.error("Failed to retrieve charging data: %s", charging_data)
        else:
            _LOGGER.info("✓ Charging data retrieved")
            # Check if the data is wrapped in a 'data' field or is directly returned
            records = charging_data.get("data", []) if isinstance(charging_data, dict) else []
            
            if isinstance(records, list):
                _LOGGER.info("Retrieved %d charging records", len(records))
                if records:
                    # Print the most recent record
                    try:
                        # Sort by date if available
                        sorted_data = sorted(
                            records,
                            key=lambda x: x.get("date", ""),
                            reverse=True
                        )
                        latest_record = sorted_data[0]
                        _LOGGER.info("Latest record: %s", json.dumps(latest_record, indent=2))
                    except (KeyError, IndexError, TypeError):
                        _LOGGER.info("First record: %s", json.dumps(records[0], indent=2))
            else:
                _LOGGER.info("Charging data structure: %s", json.dumps(charging_data, indent=2))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test the EV Charging Tracker Home Assistant integration."
    )
    parser.add_argument(
        "--host", default="localhost", help="Hostname or IP address of the API server"
    )
    parser.add_argument(
        "--port", type=int, default=5001, help="Port of the API server"
    )
    parser.add_argument(
        "--api-key", help="API key for authentication (if required)"
    )
    return parser.parse_args()


async def main():
    """Run the test script."""
    args = parse_args()
    await test_api_connection(args.host, args.port, args.api_key)


if __name__ == "__main__":
    asyncio.run(main())