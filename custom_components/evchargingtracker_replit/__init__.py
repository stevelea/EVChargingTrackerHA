"""EV Charging Tracker Replit integration for Home Assistant."""
import logging
from datetime import datetime, timedelta
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
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

# Supported platforms
PLATFORMS = [Platform.SENSOR]

# Configuration schema
CONFIG_SCHEMA = vol.Schema(
    {
        "evchargingtracker_replit": vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT, default=5000): cv.port,
                vol.Optional(CONF_API_KEY): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

# Update interval (60 seconds)
UPDATE_INTERVAL = timedelta(seconds=60)


async def async_setup(hass: HomeAssistant, config: Dict) -> bool:
    """Set up the EV Charging Tracker Replit component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EV Charging Tracker Replit from a config entry."""
    _LOGGER.info("Setting up EV Charging Tracker Replit integration")
    
    # Create update coordinator with demo data
    coordinator = EVChargingTrackerReplitDataUpdateCoordinator(hass)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator
    hass.data.setdefault("evchargingtracker_replit", {})[entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove coordinator
    if unload_ok:
        hass.data["evchargingtracker_replit"].pop(entry.entry_id)

    return unload_ok


class EVChargingTrackerReplitDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching EV Charging Tracker data for Replit."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the coordinator."""
        self.data = {"summary": {}, "latest_record": {}}

        super().__init__(
            hass,
            _LOGGER,
            name="EV Charging Tracker Replit",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from demo dataset."""
        try:
            # Create base synthetic data for Replit deployments
            from datetime import datetime, timedelta
            
            # Update the timestamps to current time
            now = datetime.now()
            
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
            
            # Log that we're returning demo data
            _LOGGER.info("EV Charging Tracker Replit: Returning demo data")
            
            return synthetic_data
        except Exception as err:
            _LOGGER.error("Error updating EV Charging Tracker Replit data: %s", err)
            raise UpdateFailed(f"Error updating data: {err}") from err