"""Sensor platform for EV Charging Tracker integration."""
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

from . import EVChargingTrackerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class EVChargingTrackerSensorEntityDescription(SensorEntityDescription):
    """Describes EV Charging Tracker sensor entity."""

    # Additional attributes for extracting values
    value_fn: Optional[Callable[[Dict[str, Any]], StateType]] = None
    source: str = "summary"  # "summary" or "latest_record"
    source_key: Optional[str] = None


SENSOR_DESCRIPTIONS: List[EVChargingTrackerSensorEntityDescription] = [
    # Summary sensors
    EVChargingTrackerSensorEntityDescription(
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
    EVChargingTrackerSensorEntityDescription(
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
    EVChargingTrackerSensorEntityDescription(
        key="average_cost_per_kwh",
        name="Average Cost per kWh",
        native_unit_of_measurement=f"{CURRENCY_DOLLAR}/{ENERGY_KILO_WATT_HOUR}",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-check",
        source="summary",
        source_key="avg_cost_per_kwh",
        value_fn=lambda data: float(data.get("avg_cost_per_kwh", 0)),
    ),
    EVChargingTrackerSensorEntityDescription(
        key="charging_session_count",
        name="Charging Session Count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
        source="summary",
        source_key="record_count",
        value_fn=lambda data: int(data.get("record_count", 0)),
    ),
    
    # Latest charging session sensors
    EVChargingTrackerSensorEntityDescription(
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
    EVChargingTrackerSensorEntityDescription(
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
    EVChargingTrackerSensorEntityDescription(
        key="last_charging_location",
        name="Last Charging Location",
        icon="mdi:map-marker",
        source="latest_record",
        source_key="location",
        value_fn=lambda data: str(data.get("location", "")),
    ),
    EVChargingTrackerSensorEntityDescription(
        key="last_charging_date",
        name="Last Charging Date",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:calendar-clock",
        source="latest_record",
        source_key="date",
        value_fn=lambda data: _parse_date(data.get("date", "")),
    ),
    EVChargingTrackerSensorEntityDescription(
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
    EVChargingTrackerSensorEntityDescription(
        key="last_cost_per_kwh",
        name="Last Cost per kWh",
        native_unit_of_measurement=f"{CURRENCY_DOLLAR}/{ENERGY_KILO_WATT_HOUR}",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-check",
        source="latest_record",
        source_key="cost_per_kwh",
        value_fn=lambda data: float(data.get("cost_per_kwh", 0)),
    ),
    EVChargingTrackerSensorEntityDescription(
        key="last_provider",
        name="Last Provider",
        icon="mdi:ev-station",
        source="latest_record",
        source_key="provider",
        value_fn=lambda data: str(data.get("provider", "")),
    ),
]


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string from API."""
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
    """Set up EV Charging Tracker sensors based on config entry."""
    coordinator = hass.data["evchargingtracker"][entry.entry_id]
    
    # Create sensor entities
    entities = []
    for description in SENSOR_DESCRIPTIONS:
        entities.append(
            EVChargingTrackerSensor(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                description=description,
            )
        )
    
    async_add_entities(entities, True)


class EVChargingTrackerSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a EV Charging Tracker sensor."""

    entity_description: EVChargingTrackerSensorEntityDescription

    def __init__(
        self,
        coordinator: EVChargingTrackerDataUpdateCoordinator,
        entry_id: str,
        description: EVChargingTrackerSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {("evchargingtracker", entry_id)},
            "name": "EV Charging Tracker",
            "manufacturer": "EV Charging Tracker",
            "model": "API Integration",
            "sw_version": "1.0.0",
        }
        self._update_attributes()

    def _update_from_record(self, record: Dict[str, Any]) -> None:
        """Update entity from record data."""
        try:
            if not record:
                _LOGGER.warning("Empty record data received for %s", self.entity_id)
                return
                
            if self.entity_description.value_fn and self.entity_description.source_key:
                self._attr_native_value = self.entity_description.value_fn(record)
            elif self.entity_description.source_key:
                self._attr_native_value = record.get(self.entity_description.source_key)
                
            # Make sure we don't have unsupported types
            if self._attr_native_value is not None:
                if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
                    # We need a proper datetime object for timestamps
                    if not isinstance(self._attr_native_value, datetime):
                        _LOGGER.warning(
                            "Timestamp sensor %s has non-datetime value: %s (%s)", 
                            self.entity_id, 
                            self._attr_native_value,
                            type(self._attr_native_value)
                        )
                        self._attr_native_value = None
                elif (
                    self.entity_description.device_class in 
                    (SensorDeviceClass.ENERGY, SensorDeviceClass.POWER, SensorDeviceClass.MONETARY)
                ):
                    # Numeric sensors need float values
                    try:
                        self._attr_native_value = float(self._attr_native_value)
                    except (ValueError, TypeError):
                        _LOGGER.warning(
                            "Numeric sensor %s has non-numeric value: %s (%s)", 
                            self.entity_id, 
                            self._attr_native_value,
                            type(self._attr_native_value)
                        )
                        self._attr_native_value = 0.0
        except Exception as e:
            _LOGGER.error("Error updating sensor %s: %s", self.entity_id, e)
            # Don't reset the value - keep the previous one instead

    def _update_attributes(self) -> None:
        """Update attributes from coordinator data."""
        if not self.coordinator.data:
            return

        data = self.coordinator.data
        source = self.entity_description.source

        if source == "summary" and "summary" in data:
            self._update_from_record(data["summary"])
        elif source == "latest_record" and "latest_record" in data:
            self._update_from_record(data["latest_record"])

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.data:
            return False

        source = self.entity_description.source
        data = self.coordinator.data

        if source == "summary" and not data.get("summary"):
            return False
        elif source == "latest_record" and not data.get("latest_record"):
            return False

        return True

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attributes = {}
        
        if not self.coordinator.data:
            return attributes
            
        # Add some extra attributes based on the sensor type
        source = self.entity_description.source
        if source == "summary":
            summary = self.coordinator.data.get("summary", {})
            if isinstance(summary, dict) and summary:
                # Add any summary attributes that aren't already exposed as sensors
                for key, value in summary.items():
                    if key not in ["total_energy_kwh", "total_cost", "avg_cost_per_kwh", "record_count"]:
                        attributes[key] = value
                        
        elif source == "latest_record":
            record = self.coordinator.data.get("latest_record", {})
            if isinstance(record, dict) and record:
                # For last charging session sensors, add the record ID
                if "id" in record:
                    attributes["record_id"] = record["id"]
                # For location-based sensors, add lat/lon if available
                if self.entity_description.key == "last_charging_location":
                    if "latitude" in record and "longitude" in record:
                        attributes["latitude"] = record["latitude"]
                        attributes["longitude"] = record["longitude"]
        
        return attributes