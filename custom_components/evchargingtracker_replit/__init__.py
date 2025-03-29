"""EV Charging Tracker Replit integration for Home Assistant."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# Don't try to import voluptuous unless it's installed
try:
    import voluptuous as vol
    HAS_VOLUPTUOUS = True
except ImportError:
    HAS_VOLUPTUOUS = False
    vol = None

# Import Home Assistant components with error handling
try:
    from homeassistant.const import (
        CONF_API_KEY,
        CONF_HOST,
        CONF_PORT,
    )
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    # In HA 2023.11.0 and later, use the Platform enum
    try:
        from homeassistant.const import Platform
        PLATFORMS = [Platform.SENSOR]
    except ImportError:
        # For older versions of Home Assistant
        PLATFORMS = ["sensor"]
    
    import homeassistant.helpers.config_validation as cv
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
    HAS_HA_COMPONENTS = True
except ImportError as e:
    HAS_HA_COMPONENTS = False
    logging.getLogger(__name__).error(f"Failed to import Home Assistant components: {e}")

_LOGGER = logging.getLogger(__name__)

# Update interval (60 seconds)
UPDATE_INTERVAL = timedelta(seconds=60)

# Configuration schema - only define if voluptuous is available
if HAS_VOLUPTUOUS and 'cv' in locals():
    CONFIG_SCHEMA = vol.Schema(
        {
            "evchargingtracker_replit": vol.Schema(
                {
                    vol.Required(CONF_HOST, default="ev-charging-tracker.replit.app"): cv.string,
                    vol.Required(CONF_PORT, default=5000): cv.port,
                    vol.Optional(CONF_API_KEY): cv.string,
                }
            )
        },
        extra=vol.ALLOW_EXTRA,
    )


async def async_setup(hass: HomeAssistant, config: Dict) -> bool:
    """Set up the EV Charging Tracker Replit component."""
    _LOGGER.info("Initializing EV Charging Tracker Replit integration")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EV Charging Tracker Replit from a config entry."""
    _LOGGER.info("Setting up EV Charging Tracker Replit integration with config entry")
    
    if not HAS_HA_COMPONENTS:
        _LOGGER.error("Missing required Home Assistant components. Integration cannot be set up.")
        return False
    
    try:
        # Create update coordinator with demo data
        coordinator = EVChargingTrackerReplitDataUpdateCoordinator(hass)
        
        # Fetch initial data
        _LOGGER.debug("Performing initial data refresh")
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug("Initial data refresh completed")

        # Store the coordinator
        hass.data.setdefault("evchargingtracker_replit", {})[entry.entry_id] = coordinator
        _LOGGER.debug("Coordinator stored in hass.data")

        # Set up platforms
        _LOGGER.debug("Setting up sensor platform")
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info("EV Charging Tracker Replit integration setup completed successfully")

        return True
    except Exception as err:
        _LOGGER.error(f"Failed to set up EV Charging Tracker Replit integration: {err}")
        import traceback
        _LOGGER.error(traceback.format_exc())
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading EV Charging Tracker Replit integration")
    
    try:
        # Unload platforms
        _LOGGER.debug("Unloading platforms")
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        # Remove coordinator
        if unload_ok and "evchargingtracker_replit" in hass.data:
            _LOGGER.debug("Removing coordinator from hass.data")
            hass.data["evchargingtracker_replit"].pop(entry.entry_id, None)

        _LOGGER.info("EV Charging Tracker Replit integration unloaded successfully")
        return unload_ok
    except Exception as err:
        _LOGGER.error(f"Error unloading EV Charging Tracker Replit integration: {err}")
        return False


class EVChargingTrackerReplitDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching EV Charging Tracker data for Replit."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the coordinator."""
        _LOGGER.debug("Initializing data coordinator")
        # Initialize with empty data structure
        self.data = {
            "summary": {
                "total_energy_kwh": 0,
                "total_cost": 0,
                "avg_cost_per_kwh": 0,
                "record_count": 0,
                "simulated": True
            },
            "latest_record": {
                "id": "sim_init",
                "date": datetime.now().isoformat(),
                "simulated": True
            }
        }

        super().__init__(
            hass,
            _LOGGER,
            name="EV Charging Tracker Replit",
            update_interval=UPDATE_INTERVAL,
        )
        _LOGGER.debug("Data coordinator initialized")

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from demo dataset."""
        try:
            _LOGGER.debug("Updating data")
            # Update the timestamps to current time
            now = datetime.now()
            
            # Create synthetic data with current timestamps
            synthetic_data = {
                "summary": {
                    "total_energy_kwh": 243.5,
                    "total_cost": 109.57,
                    "avg_cost_per_kwh": 0.45,
                    "record_count": 5,
                    "locations": 5,
                    "providers": 4,
                    "simulated": True,
                    "date_range": {
                        "first_date": (now - timedelta(days=30)).isoformat(),
                        "last_date": now.isoformat()
                    },
                    "top_providers": [
                        {"provider": "Chargefox", "total_kwh": 72.5},
                        {"provider": "Tesla", "total_kwh": 61.0},
                        {"provider": "AmpCharge", "total_kwh": 57.2},
                        {"provider": "Evie", "total_kwh": 52.8}
                    ],
                    "top_locations": [
                        {"location": "Simulated Location 1", "total_kwh": 55.5},
                        {"location": "Simulated Location 2", "total_kwh": 50.0},
                        {"location": "Simulated Location 3", "total_kwh": 48.5},
                        {"location": "Simulated Location 4", "total_kwh": 46.0},
                        {"location": "Simulated Location 5", "total_kwh": 43.5}
                    ]
                },
                "latest_record": {
                    "id": "sim_latest",
                    "date": now.isoformat(),
                    "location": "Simulated Location 1",
                    "provider": "Chargefox",
                    "energy": 25.4,
                    "total_kwh": 25.4,
                    "total_cost": 11.43,
                    "cost_per_kwh": 0.45,
                    "peak_kw": 50.0,
                    "latitude": -33.8688,
                    "longitude": 151.2093,
                    "simulated": True
                }
            }
            
            _LOGGER.info("EV Charging Tracker Replit: Generated demo data with timestamp %s", now.isoformat())
            
            return synthetic_data
        except Exception as err:
            _LOGGER.error("Error updating EV Charging Tracker Replit data: %s", err)
            import traceback
            _LOGGER.error(traceback.format_exc())
            # Return the previous data instead of failing
            return self.data