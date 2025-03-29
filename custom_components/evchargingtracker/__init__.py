"""EV Charging Tracker integration for Home Assistant."""
import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EVChargingTrackerApiClient

_LOGGER = logging.getLogger(__name__)

# Supported platforms
PLATFORMS = [Platform.SENSOR]

# Configuration schema
CONFIG_SCHEMA = vol.Schema(
    {
        "evchargingtracker": vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT, default=8000): cv.port,
                vol.Optional(CONF_API_KEY): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

# Update interval (60 seconds)
UPDATE_INTERVAL = timedelta(seconds=60)


async def async_setup(hass: HomeAssistant, config: Dict) -> bool:
    """Set up the EV Charging Tracker component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EV Charging Tracker from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    api_key = entry.data.get(CONF_API_KEY)

    session = async_get_clientsession(hass)
    
    # Special handling for Replit URLs
    if '.replit.app' in host:
        # Remove any existing protocol prefixes and ports for clean processing
        clean_host = host.replace('https://', '').replace('http://', '')
        if ':' in clean_host:
            clean_host = clean_host.split(':')[0]  # Remove any port numbers
            
        # Now rebuild with proper HTTPS protocol WITHOUT port specification
        # CRITICAL CHANGE: Do NOT add port to Replit URLs
        base_url = f"https://{clean_host}"
        
        _LOGGER.info("Using Replit URL configuration (no port specification): %s", base_url)
    else:
        # For standard host:port combinations
        base_url = f"http://{host}:{port}"
        _LOGGER.info("Using standard URL configuration: %s", base_url)

    _LOGGER.debug("Creating API client with base URL: %s", base_url)
    api_client = EVChargingTrackerApiClient(
        session, base_url, api_key
    )

    # Verify connection to API
    try:
        _LOGGER.debug("Verifying connection to EV Charging Tracker API at %s:%s", host, port)
        health_check = await api_client.async_health_check()
        _LOGGER.debug("Health check response: %s", health_check)
        
        # First, check for the expected 'status: ok' response
        if health_check and health_check.get("status") == "ok":
            _LOGGER.info("Successfully connected to EV Charging Tracker API")
        
        # If that fails, try to validate using a different endpoint
        else:
            _LOGGER.debug("Health check didn't return expected format, trying summary endpoint")
            summary = await api_client.async_get_charging_summary()
            _LOGGER.debug("Summary response: %s", summary)
            
            # If we got any valid response, consider it a success
            if summary is not None:
                _LOGGER.info("Successfully connected to EV Charging Tracker API via summary endpoint")
            else:
                _LOGGER.error("Failed to connect to EV Charging Tracker API - no valid response from any endpoint")
                return False
                
    except Exception as exc:  # pylint: disable=broad-except
        _LOGGER.error("Error connecting to EV Charging Tracker API: %s", exc)
        return False

    # Create update coordinator
    coordinator = EVChargingTrackerDataUpdateCoordinator(hass, api_client)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator
    hass.data.setdefault("evchargingtracker", {})[entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove coordinator
    if unload_ok:
        hass.data["evchargingtracker"].pop(entry.entry_id)

    return unload_ok


class EVChargingTrackerDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching EV Charging Tracker data."""

    def __init__(self, hass: HomeAssistant, api_client: EVChargingTrackerApiClient):
        """Initialize the coordinator."""
        self.api_client = api_client
        self.api_data = {"summary": {}, "latest_record": {}}

        super().__init__(
            hass,
            _LOGGER,
            name="EV Charging Tracker",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from EV Charging Tracker API."""
        _LOGGER.error("UPDATE DATA CALLED - STARTING API REQUESTS")
        
        try:
            # Initialize defaults
            summary_result = {}
            latest_record = {}
            
            # Get summary data
            try:
                _LOGGER.error("ATTEMPTING TO GET CHARGING SUMMARY")
                summary_result = await self.api_client.async_get_charging_summary()
                _LOGGER.error("SUMMARY RESULT: %s", summary_result)
                
                if not summary_result:
                    # If summary is empty, attempt direct request
                    _LOGGER.error("TRYING DIRECT SUMMARY REQUEST")
                    if '.replit.app' in self.api_client._base_url:
                        import aiohttp
                        try:
                            # Replit special case, try direct URL
                            url = "https://ev-charging-tracker-stevelea1.replit.app/api/summary"
                            _LOGGER.error("DIRECT REQUEST TO %s", url)
                            timeout = aiohttp.ClientTimeout(total=10)
                            headers = {"X-API-Key": self.api_client._api_key} if self.api_client._api_key else {}
                            
                            async with aiohttp.ClientSession() as direct_session:
                                async with direct_session.get(url, headers=headers, timeout=timeout) as response:
                                    _LOGGER.error("DIRECT SUMMARY RESPONSE: %s", response.status)
                                    if response.status == 200:
                                        direct_result = await response.json()
                                        _LOGGER.error("DIRECT SUMMARY CONTENT: %s", direct_result)
                                        summary_result = direct_result
                        except Exception as direct_err:
                            _LOGGER.error("DIRECT SUMMARY ERROR: %s", direct_err)
            except Exception as e:
                _LOGGER.error("Error getting charging summary: %s", e)
                # Don't raise an exception here; we'll try to get the charging data instead
            
            # Get charging data for latest record
            try:
                _LOGGER.error("ATTEMPTING TO GET CHARGING DATA")
                charging_data_result = await self.api_client.async_get_charging_data()
                _LOGGER.error("CHARGING DATA RESULT: %s", charging_data_result)
                
                # Extract records from response - handle different response formats
                records = []
                if isinstance(charging_data_result, dict):
                    records = charging_data_result.get("data", [])
                
                _LOGGER.error("EXTRACTED %d RECORDS", len(records))
                
                # Find latest record
                if isinstance(records, list) and records:
                    try:
                        # Sort by date if available to get latest record
                        _LOGGER.error("SORTING RECORDS BY DATE")
                        sorted_data = sorted(
                            records,
                            key=lambda x: x.get("date", ""),
                            reverse=True
                        )
                        latest_record = sorted_data[0]
                        _LOGGER.error("LATEST RECORD: %s", latest_record)
                    except (KeyError, IndexError, TypeError) as e:
                        _LOGGER.error("Error sorting records: %s. Using first record instead.", e)
                        if records:
                            latest_record = records[0]
                            _LOGGER.error("USING FIRST RECORD: %s", latest_record)
            except Exception as e:
                _LOGGER.error("Error getting charging data: %s", e)
                # Don't raise an exception here; we'll continue with what we have
            
            # Update and return data
            self.api_data = {
                "summary": summary_result,
                "latest_record": latest_record
            }
            
            _LOGGER.error("FINAL DATA: summary=%s, has_latest_record=%s", 
                          bool(summary_result), bool(latest_record))
            
            # If we got no data at all, try one last direct attempt
            if not summary_result and not latest_record:
                _LOGGER.error("NO DATA RECEIVED - TRYING DIRECT HEALTH CHECK")
                try:
                    import aiohttp
                    url = "https://ev-charging-tracker-stevelea1.replit.app/api/health"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            status = response.status
                            text = await response.text()
                            _LOGGER.error("HEALTH CHECK RESPONSE: %s - %s", status, text)
                except Exception as health_err:
                    _LOGGER.error("HEALTH CHECK ERROR: %s", health_err)
            
            return self.api_data

        except Exception as err:
            _LOGGER.error("ERROR UPDATING EV CHARGING TRACKER DATA: %s", err)
            raise UpdateFailed(f"Error updating data: {err}") from err