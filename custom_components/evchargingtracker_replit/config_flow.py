"""Config flow for EV Charging Tracker Replit integration."""
import logging
from typing import Any, Dict, Optional

# Handle import failures gracefully
try:
    import voluptuous as vol
    HAS_VOLUPTUOUS = True
except ImportError:
    HAS_VOLUPTUOUS = False
    # Create placeholder to prevent NameError
    class vol:
        @staticmethod
        def Schema(*args, **kwargs):
            return None
        
        @staticmethod
        def Required(*args, **kwargs):
            return None
        
        @staticmethod
        def Optional(*args, **kwargs):
            return None

try:
    from homeassistant import config_entries
    from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
    from homeassistant.core import HomeAssistant
    from homeassistant.data_entry_flow import FlowResult
    HAS_HA_IMPORTS = True
except ImportError as e:
    HAS_HA_IMPORTS = False
    logging.getLogger(__name__).error(f"Failed to import Home Assistant components: {e}")
    # Create placeholder classes to prevent NameError
    class config_entries:
        class ConfigFlow:
            pass
    # Create placeholder constants
    CONF_API_KEY = "api_key"
    CONF_HOST = "host"
    CONF_PORT = "port"
    # Create placeholder type
    FlowResult = Any

_LOGGER = logging.getLogger(__name__)

# Only define the config flow class if the imports succeeded
if HAS_HA_IMPORTS:
    class EVChargingTrackerReplitConfigFlow(config_entries.ConfigFlow, domain="evchargingtracker_replit"):
        """Handle a config flow for EV Charging Tracker Replit."""

        VERSION = 1

        async def async_step_user(
            self, user_input: Optional[Dict[str, Any]] = None
        ) -> FlowResult:
            """Handle the initial step."""
            _LOGGER.debug("Starting config flow user step")
            errors = {}

            if user_input is not None:
                try:
                    # Accept any input - this is a fully local integration with demo data
                    _LOGGER.debug("User input provided: %s", user_input)
                    # Create entry
                    title = f"EV Charging Tracker Replit ({user_input[CONF_HOST]})"
                    
                    _LOGGER.info("Creating config entry with title: %s", title)
                    return self.async_create_entry(
                        title=title,
                        data=user_input,
                    )
                except Exception as e:
                    _LOGGER.error("Error creating entry: %s", e)
                    errors["base"] = "unknown"
                    import traceback
                    _LOGGER.error(traceback.format_exc())

            # Show form with default values for Replit
            try:
                _LOGGER.debug("Showing config flow form")
                
                if not HAS_VOLUPTUOUS:
                    _LOGGER.error("Voluptuous library not available, cannot create schema")
                    errors["base"] = "missing_dependencies"
                    return self.async_abort(reason="missing_dependencies")
                
                data_schema = vol.Schema(
                    {
                        vol.Required(CONF_HOST, default="ev-charging-tracker.replit.app"): str,
                        vol.Required(CONF_PORT, default=5000): int,
                        vol.Optional(CONF_API_KEY, default="ev-charging-api-key"): str,
                    }
                )

                return self.async_show_form(
                    step_id="user", data_schema=data_schema, errors=errors
                )
            except Exception as e:
                _LOGGER.error("Error showing form: %s", e)
                import traceback
                _LOGGER.error(traceback.format_exc())
                return self.async_abort(reason="unknown")
else:
    # Create a placeholder class if imports failed
    class EVChargingTrackerReplitConfigFlow:
        """Placeholder class when imports fail."""
        
        VERSION = 1
        
        def __init__(self, *args, **kwargs):
            """Initialize but log an error."""
            _LOGGER.error("Cannot instantiate config flow because imports failed")