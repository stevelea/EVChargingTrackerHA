"""Sensor platform for EV Charging Tracker Replit integration."""
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, cast

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

from . import EVChargingTrackerReplitDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class EVChargingTrackerReplitSensorEntityDescription(SensorEntityDescription):
    """Describes EV Charging Tracker sensor entity."""

    # Additional attributes for extracting values
    value_fn: Optional[Callable[[Dict[str, Any]], StateType]] = None
    source: str = "summary"  # "summary" or "latest_record"
    source_key: Optional[str] = None


SENSOR_DESCRIPTIONS: List[EVChargingTrackerReplitSensorEntityDescription] = [
    # Summary sensors
    EVChargingTrackerReplitSensorEntityDescription(
        key="total_energy",
        name="Total Energy",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        icon="mdi:battery-charging",
        source="summary",
        source_key="total_energy_kwh",
        value_fn=lambda data: float(data.get("total_energy_kwh", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="total_cost",
        name="Total Cost",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.MONETARY,
        icon="mdi:cash",
        source="summary",
        source_key="total_cost",
        value_fn=lambda data: float(data.get("total_cost", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="average_cost_per_kwh",
        name="Average Cost per kWh",
        native_unit_of_measurement=f"{CURRENCY_DOLLAR}/{ENERGY_KILO_WATT_HOUR}",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-check",
        source="summary",
        source_key="avg_cost_per_kwh",
        value_fn=lambda data: float(data.get("avg_cost_per_kwh", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="charging_session_count",
        name="Charging Session Count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
        source="summary",
        source_key="record_count",
        value_fn=lambda data: int(data.get("record_count", 0)),
    ),
    
    # Latest charging session sensors
    EVChargingTrackerReplitSensorEntityDescription(
        key="last_charging_energy",
        name="Last Charging Energy",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.ENERGY,
        icon="mdi:battery-charging",
        source="latest_record",
        source_key="energy",
        value_fn=lambda data: float(data.get("energy", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="last_charging_cost",
        name="Last Charging Cost",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
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
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:calendar-clock",
        source="latest_record",
        source_key="date",
        value_fn=lambda data: _parse_date(data.get("date", "")),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="last_peak_power",
        name="Last Peak Power",
        native_unit_of_measurement=POWER_KILO_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:flash",
        source="latest_record",
        source_key="peak_kw",
        value_fn=lambda data: float(data.get("peak_kw", 0)),
    ),
    EVChargingTrackerReplitSensorEntityDescription(
        key="last_cost_per_kwh",
        name="Last Cost per kWh",
        native_unit_of_measurement=f"{CURRENCY_DOLLAR}/{ENERGY_KILO_WATT_HOUR}",
        state_class=SensorStateClass.MEASUREMENT,
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
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EV Charging Tracker Replit sensors based on config entry."""
    _LOGGER.info("Setting up EV Charging Tracker Replit sensors")
    
    try:
        coordinator = hass.data["evchargingtracker_replit"][entry.entry_id]
        
        # Create sensor entities
        entities = []
        for description in SENSOR_DESCRIPTIONS:
            entities.append(
                EVChargingTrackerReplitSensor(
                    coordinator=coordinator,
                    entry_id=entry.entry_id,
                    description=description,
                )
            )
        
        async_add_entities(entities, True)
        _LOGGER.info("Added %d sensor entities for EV Charging Tracker Replit", len(entities))
    except Exception as e:
        _LOGGER.error("Error setting up EV Charging Tracker Replit sensors: %s", e)


class EVChargingTrackerReplitSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a EV Charging Tracker Replit sensor."""

    entity_description: EVChargingTrackerReplitSensorEntityDescription

    def __init__(
        self,
        coordinator: EVChargingTrackerReplitDataUpdateCoordinator,
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
            "model": "API Integration",
            "sw_version": "1.0.0",
        }
        self._update_attributes()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Always available since we're using demo data
        return True

    def _update_attributes(self) -> None:
        """Update attributes from coordinator data."""
        if not self.coordinator.data:
            return
        
        try:
            data = self.coordinator.data
            source = self.entity_description.source
            
            if source == "summary" and "summary" in data:
                source_data = data["summary"]
            elif source == "latest_record" and "latest_record" in data:
                source_data = data["latest_record"]
            else:
                return
                
            if self.entity_description.value_fn and self.entity_description.source_key:
                self._attr_native_value = self.entity_description.value_fn(source_data)
            elif self.entity_description.source_key:
                self._attr_native_value = source_data.get(self.entity_description.source_key)
                
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
            _LOGGER.error("Error updating sensor %s: %s", self.entity_id, e)