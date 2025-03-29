"""Config flow for EV Charging Tracker Replit integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)


class EVChargingTrackerReplitConfigFlow(config_entries.ConfigFlow, domain="evchargingtracker_replit"):
    """Handle a config flow for EV Charging Tracker Replit."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Accept any input - this is a fully local integration with demo data
            # Create entry
            title = f"EV Charging Tracker Replit ({user_input[CONF_HOST]})"
            
            return self.async_create_entry(
                title=title,
                data=user_input,
            )

        # Show form with default values for Replit
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="ev-charging-tracker-stevelea1.replit.app"): str,
                vol.Required(CONF_PORT, default=5000): int,
                vol.Optional(CONF_API_KEY, default="ev-charging-api-key"): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )