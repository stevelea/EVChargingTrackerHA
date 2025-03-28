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
    client = EVChargingTrackerApiClient(session, f"http://{host}:{port}", api_key)

    try:
        result = await client.async_health_check()
        return result.get("status") == "ok"
    except Exception:  # pylint: disable=broad-except
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
                    return self.async_create_entry(
                        title=f"EV Charging Tracker ({host}:{port})",
                        data=user_input,
                    )
                
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="localhost"): str,
                vol.Required(CONF_PORT, default=5001): int,
                vol.Optional(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )