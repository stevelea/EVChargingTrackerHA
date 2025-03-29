"""Sensor platform for EV Charging Tracker Replit integration."""
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

# Import safely without crashing if dependencies are missing
try:
    from homeassistant.components.sensor import (
        SensorDeviceClass,
        SensorEntity,
        SensorEntityDescription,
        SensorStateClass,
    )
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import (
        CURRENCY_DOLLAR,
        ELECTRIC_POTENTIAL_VOLT,
        ENERGY_KILO_WATT_HOUR, 
        POWER_KILO_WATT,
    )
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity import EntityCategory
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType
    from homeassistant.helpers.update_coordinator import (
        CoordinatorEntity,
        DataUpdateCoordinator,
    )
    HA_IMPORTS_SUCCESS = True
except ImportError as e:
    HA_IMPORTS_SUCCESS = False
    logging.getLogger(__name__).error(f"Failed to import Home Assistant components: {e}")
    # Define fallbacks for classes
    SensorEntityDescription = object
    SensorEntity = object
    CoordinatorEntity = object
    StateType = Any

# Only attempt to import our coordinator if we've got the HA components
if HA_IMPORTS_SUCCESS:
    try:
        from . import EVChargingTrackerReplitDataUpdateCoordinator
    except ImportError:
        logging.getLogger(__name__).error("Failed to import coordinator")

_LOGGER = logging.getLogger(__name__)


class EVChargingTrackerReplitSensorEntityDescription(SensorEntityDescription):
    """Describes EV Charging Tracker sensor entity."""

    def __init__(self, **kwargs):
        self.value_fn = kwargs.pop("value_fn", None)
        self.source = kwargs.pop("source", "summary")
        self.source_key = kwargs.pop("source_key", None)
        super().__init__(**kwargs)


# Constants for sensor descriptions - will be used to create entities
# Define these even if imports fail, so we don't get NameError
UNIT_ENERGY = ENERGY_KILO_WATT_HOUR if HA_IMPORTS_SUCCESS else "kWh"
UNIT_POWER = POWER_KILO_WATT if HA_IMPORTS_SUCCESS else "kW"
UNIT_CURRENCY = CURRENCY_DOLLAR if HA_IMPORTS_SUCCESS else "$"
STATE_CLASS_MEASUREMENT = SensorStateClass.MEASUREMENT if HA_IMPORTS_SUCCESS else "measurement"
STATE_CLASS_TOTAL = SensorStateClass.TOTAL_INCREASING if HA_IMPORTS_SUCCESS else "total_increasing"
DEVICE_CLASS_ENERGY = SensorDeviceClass.ENERGY if HA_IMPORTS_SUCCESS else "energy"
DEVICE_CLASS_MONETARY = SensorDeviceClass.MONETARY if HA_IMPORTS_SUCCESS else "monetary"
DEVICE_CLASS_POWER = SensorDeviceClass.POWER if HA_IMPORTS_SUCCESS else "power"
DEVICE_CLASS_TIMESTAMP = SensorDeviceClass.TIMESTAMP if HA_IMPORTS_SUCCESS else "timestamp"

SENSOR_DESCRIPTIONS = [
    # Summary sensors
    EVChargingTrackerReplitSensorEntityDescription(
        key="total_energy",
        name="Total Energy",
        native_unit_of_measurement=UNIT_ENERGY,
        state_class=STATE_CLASS_TOTAL,
        device_class=DEVICE_CLASS_ENERGY,
        icon="mdi:battery-charging",
        source="summary",
        source_key="total_energy_kwh",
        value_fn=lambda data: float(data.get("total_energy_kwh", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="total_cost",
        name="Total Cost",
        native_unit_of_measurement=UNIT_CURRENCY,
        state_class=STATE_CLASS_TOTAL,
        device_class=DEVICE_CLASS_MONETARY,
        icon="mdi:cash",
        source="summary",
        source_key="total_cost",
        value_fn=lambda data: float(data.get("total_cost", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="average_cost_per_kwh",
        name="Average Cost per kWh",
        native_unit_of_measurement=f"{UNIT_CURRENCY}/{UNIT_ENERGY}",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="mdi:cash-check",
        source="summary",
        source_key="avg_cost_per_kwh",
        value_fn=lambda data: float(data.get("avg_cost_per_kwh", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="charging_session_count",
        name="Charging Session Count",
        state_class=STATE_CLASS_TOTAL,
        icon="mdi:counter",
        source="summary",
        source_key="record_count",
        value_fn=lambda data: int(data.get("record_count", 0)),
    ),
    
    # Latest charging session sensors
    EVChargingTrackerReplitSensorEntityDescription(
        key="last_charging_energy",
        name="Last Charging Energy",
        native_unit_of_measurement=UNIT_ENERGY,
        state_class=STATE_CLASS_MEASUREMENT,
        device_class=DEVICE_CLASS_ENERGY,
        icon="mdi:battery-charging",
        source="latest_record",
        source_key="energy",
        value_fn=lambda data: float(data.get("energy", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="last_charging_cost",
        name="Last Charging Cost",
        native_unit_of_measurement=UNIT_CURRENCY,
        state_class=STATE_CLASS_MEASUREMENT,
        device_class=DEVICE_CLASS_MONETARY,
        icon="mdi:cash",
        source="latest_record",
        source_key="total_cost",
        value_fn=lambda data: float(data.get("total_cost", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="last_charging_location",
        name="Last Charging Location",
        icon="mdi:map-marker",
        source="latest_record",
        source_key="location",
        value_fn=lambda data: str(data.get("location", "")),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="last_charging_date",
        name="Last Charging Date",
        device_class=DEVICE_CLASS_TIMESTAMP,
        icon="mdi:calendar-clock",
        source="latest_record",
        source_key="date",
        value_fn=lambda data: _parse_date(data.get("date", "")),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="last_peak_power",
        name="Last Peak Power",
        native_unit_of_measurement=UNIT_POWER,
        state_class=STATE_CLASS_MEASUREMENT,
        device_class=DEVICE_CLASS_POWER,
        icon="mdi:flash",
        source="latest_record",
        source_key="peak_kw",
        value_fn=lambda data: float(data.get("peak_kw", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="last_cost_per_kwh",
        name="Last Cost per kWh",
        native_unit_of_measurement=f"{UNIT_CURRENCY}/{UNIT_ENERGY}",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="mdi:cash-check",
        source="latest_record",
        source_key="cost_per_kwh",
        value_fn=lambda data: float(data.get("cost_per_kwh", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="last_provider",
        name="Last Provider",
        icon="mdi:ev-station",
        source="latest_record",
        source_key="provider",
        value_fn=lambda data: str(data.get("provider", "")),
    ),
]


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string from the data."""
    if not date_str:
        return None
    
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        try:
            # Try custom format
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return None


async def async_setup_entry(
    hass: object,
    entry: object,
    async_add_entities: callable,
) -> None:
    """Set up EV Charging Tracker Replit sensors based on config entry."""
    _LOGGER.info("Setting up EV Charging Tracker Replit sensors")
    
    # Skip everything if the imports failed
    if not HA_IMPORTS_SUCCESS:
        _LOGGER.error("Cannot set up sensors - Home Assistant components not available")
        return
    
    try:
        # Get coordinator from hass data
        if "evchargingtracker_replit" not in hass.data:
            _LOGGER.error("Integration data not found in Home Assistant data")
            return
            
        if entry.entry_id not in hass.data["evchargingtracker_replit"]:
            _LOGGER.error("Config entry id %s not found in integration data", entry.entry_id)
            return
            
        coordinator = hass.data["evchargingtracker_replit"][entry.entry_id]
        _LOGGER.debug("Found coordinator in hass.data")
        
        # Create sensor entities
        entities = []
        _LOGGER.debug("Creating %d sensor entities", len(SENSOR_DESCRIPTIONS))
        for description in SENSOR_DESCRIPTIONS:
            entities.append(
                EVChargingTrackerReplitSensor(
                    coordinator=coordinator,
                    entry_id=entry.entry_id,
                    description=description,
                )
            )
        
        _LOGGER.debug("Adding entities to Home Assistant")
        async_add_entities(entities, True)
        _LOGGER.info("Added %d sensor entities for EV Charging Tracker Replit", len(entities))
    except Exception as e:
        _LOGGER.error("Error setting up EV Charging Tracker Replit sensors: %s", e)
        import traceback
        _LOGGER.error(traceback.format_exc())


if HA_IMPORTS_SUCCESS:
    class EVChargingTrackerReplitSensor(CoordinatorEntity, SensorEntity):
        """Implementation of a EV Charging Tracker Replit sensor."""

        def __init__(
            self,
            coordinator: DataUpdateCoordinator,
            entry_id: str,
            description: EVChargingTrackerReplitSensorEntityDescription,
        ) -> None:
            """Initialize the sensor."""
            super().__init__(coordinator)
            
            self.entity_description = description
            self._attr_unique_id = f"{entry_id}_{description.key}"
            self._attr_device_info = {
                "identifiers": {("evchargingtracker_replit", entry_id)},
                "name": "EV Charging Tracker Replit",
                "manufacturer": "EV Charging Tracker",
                "model": "Replit Demo Integration",
                "sw_version": "1.0.0",
            }
            self._attr_extra_state_attributes = {
                "simulated": True,
                "replit_mode": True
            }
            self._update_attributes()

        @property
        def available(self) -> bool:
            """Return if entity is available."""
            # Always available since we're using demo data
            return True
            
        @property
        def should_poll(self) -> bool:
            """No polling needed."""
            return False

        def _update_attributes(self) -> None:
            """Update attributes from coordinator data."""
            try:
                data = getattr(self.coordinator, "data", {})
                if not data:
                    _LOGGER.warning("No data available from coordinator for sensor %s", self.entity_description.key)
                    return
                
                source = self.entity_description.source
                
                # Get the source data section
                if source == "summary" and "summary" in data:
                    source_data = data["summary"]
                elif source == "latest_record" and "latest_record" in data:
                    source_data = data["latest_record"]
                else:
                    _LOGGER.warning("Source %s not found in data for sensor %s", source, self.entity_description.key)
                    return
                    
                # Update the native value based on the value_fn or source_key
                value_fn = getattr(self.entity_description, "value_fn", None)
                source_key = getattr(self.entity_description, "source_key", None)
                
                if value_fn and source_key:
                    self._attr_native_value = value_fn(source_data)
                elif source_key:
                    self._attr_native_value = source_data.get(source_key)
                    
                # Add simulated indicator for transparency
                self._attr_extra_state_attributes = {
                    "simulated": True,
                    "replit_mode": True
                }
                
                # For location-based sensors, add lat/lon if available
                if self.entity_description.key == "last_charging_location":
                    if "latitude" in source_data and "longitude" in source_data:
                        self._attr_extra_state_attributes["latitude"] = source_data["latitude"]
                        self._attr_extra_state_attributes["longitude"] = source_data["longitude"]
            except Exception as e:
                _LOGGER.error("Error updating sensor %s: %s", getattr(self, "entity_id", self.entity_description.key), e)
                import traceback
                _LOGGER.error(traceback.format_exc())