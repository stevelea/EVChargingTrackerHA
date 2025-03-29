"""Config flow for EV Charging Tracker integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EVChargingTrackerApiClient

_LOGGER = logging.getLogger(__name__)


async def validate_api_connection(
    hass: HomeAssistant, host: str, port: int, api_key: Optional[str] = None
) -> bool:
    """Validate the user input allows us to connect to the API."""
    session = async_get_clientsession(hass)
    
    # Log the initial input parameters
    _LOGGER.info("Validating API connection with host=%s, port=%s", host, port)
    
    # Format the base URL correctly
    # Handle Replit URLs separately (with special port handling)
    if '.replit.app' in host:
        # For Replit deployments, ensure clean host without protocol
        clean_host = host.replace('https://', '').replace('http://', '')
        
        # Remove any port that might be in the hostname
        if ':' in clean_host:
            clean_host = clean_host.split(':')[0]
            _LOGGER.info("Extracted clean hostname from Replit URL: %s", clean_host)
        
        # CRITICAL CHANGE: For Replit, always use HTTPS without port
        # Replit only exposes port 443 publicly
        base_url = f"https://{clean_host}"
        _LOGGER.info("Using Replit URL format without port (public HTTPS): %s", base_url)
        
        # Log a warning message for the user
        _LOGGER.warning(
            "Connecting to a Replit-hosted EV Charging Tracker. "
            "IMPORTANT: Make sure you've updated to the latest integration files that "
            "support the Replit URL format. You must use the exact hostname %s with no port.", 
            clean_host
        )
    else:
        # For standard host:port combinations
        base_url = f"http://{host}:{port}"
        _LOGGER.info("Using standard URL format: %s", base_url)
    
    # Create the client
    client = EVChargingTrackerApiClient(session, base_url, api_key)
    _LOGGER.info("Created API client with base URL: %s", base_url)

    try:
        # Attempt to check API health
        _LOGGER.debug("Making health check request")
        result = await client.async_health_check()
        _LOGGER.debug("Health check result: %s", result)
        
        # Check if the health endpoint returned successfully
        if isinstance(result, dict) and result.get("status") == "ok":
            _LOGGER.info("API connection validated successfully!")
            return True
            
        # Fall back to a different endpoint if health check doesn't return the expected format
        _LOGGER.debug("Health check didn't return expected format, trying summary endpoint")
        summary = await client.async_get_charging_summary()
        if summary is not None:
            _LOGGER.info("API connection validated through summary endpoint!")
            return True
            
        # If we got here, we couldn't validate the connection
        _LOGGER.warning("Could not validate API connection")
        return False
        
    except Exception as e:  # pylint: disable=broad-except
        _LOGGER.error("Error validating API connection: %s", e)
        return False


class EVChargingTrackerConfigFlow(config_entries.ConfigFlow, domain="evchargingtracker"):
    """Handle a config flow for EV Charging Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the provided input
            try:
                host = user_input[CONF_HOST]
                port = user_input[CONF_PORT]
                api_key = user_input.get(CONF_API_KEY)

                # Check connection
                is_valid = await validate_api_connection(self.hass, host, port, api_key)

                if is_valid:
                    # Create entry
                    # Create a better title that won't cause URL parsing issues
                    if '.replit.app' in host:
                        clean_host = host.replace('https://', '').replace('http://', '')
                        title = f"EV Charging Tracker ({clean_host})"
                    else:
                        title = f"EV Charging Tracker ({host}:{port})"
                    
                    return self.async_create_entry(
                        title=title,
                        data=user_input,
                    )
                
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show form with updated defaults for port and API key
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="ev-charging-tracker-stevelea1.replit.app"): str,
                vol.Required(CONF_PORT, default=5000): int,  # Always use port 5000 for Replit
                vol.Optional(CONF_API_KEY, default="ev-charging-api-key"): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )