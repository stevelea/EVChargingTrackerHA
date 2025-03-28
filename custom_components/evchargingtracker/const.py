"""Constants for the EV Charging Tracker integration."""

DOMAIN = "evchargingtracker"
SCAN_INTERVAL = 60  # Update every 60 seconds

# Entity types
ENTITY_TOTAL_ENERGY = "total_energy"
ENTITY_TOTAL_COST = "total_cost"
ENTITY_AVERAGE_COST_PER_KWH = "average_cost_per_kwh"
ENTITY_SESSION_COUNT = "session_count"
ENTITY_LAST_CHARGING_ENERGY = "last_charging_energy"
ENTITY_LAST_CHARGING_COST = "last_charging_cost"
ENTITY_LAST_CHARGING_LOCATION = "last_charging_location"
ENTITY_LAST_CHARGING_DATE = "last_charging_date"
ENTITY_LAST_PEAK_POWER = "last_peak_power"
ENTITY_LAST_COST_PER_KWH = "last_cost_per_kwh"
ENTITY_LAST_PROVIDER = "last_provider"

# Entity names
ENTITY_NAMES = {
    ENTITY_TOTAL_ENERGY: "Total Energy",
    ENTITY_TOTAL_COST: "Total Cost",
    ENTITY_AVERAGE_COST_PER_KWH: "Average Cost per kWh",
    ENTITY_SESSION_COUNT: "Charging Session Count",
    ENTITY_LAST_CHARGING_ENERGY: "Last Charging Energy",
    ENTITY_LAST_CHARGING_COST: "Last Charging Cost",
    ENTITY_LAST_CHARGING_LOCATION: "Last Charging Location",
    ENTITY_LAST_CHARGING_DATE: "Last Charging Date",
    ENTITY_LAST_PEAK_POWER: "Last Peak Power",
    ENTITY_LAST_COST_PER_KWH: "Last Cost per kWh",
    ENTITY_LAST_PROVIDER: "Last Provider",
}

# Default entity icons
ENTITY_ICONS = {
    ENTITY_TOTAL_ENERGY: "mdi:lightning-bolt",
    ENTITY_TOTAL_COST: "mdi:currency-usd",
    ENTITY_AVERAGE_COST_PER_KWH: "mdi:currency-usd-circle",
    ENTITY_SESSION_COUNT: "mdi:counter",
    ENTITY_LAST_CHARGING_ENERGY: "mdi:flash",
    ENTITY_LAST_CHARGING_COST: "mdi:cash",
    ENTITY_LAST_CHARGING_LOCATION: "mdi:map-marker",
    ENTITY_LAST_CHARGING_DATE: "mdi:calendar",
    ENTITY_LAST_PEAK_POWER: "mdi:flash-circle",
    ENTITY_LAST_COST_PER_KWH: "mdi:cash-fast",
    ENTITY_LAST_PROVIDER: "mdi:ev-station",
}

# Entity units
ENTITY_UNITS = {
    ENTITY_TOTAL_ENERGY: "kWh",
    ENTITY_TOTAL_COST: "$",
    ENTITY_AVERAGE_COST_PER_KWH: "$/kWh",
    ENTITY_SESSION_COUNT: None,
    ENTITY_LAST_CHARGING_ENERGY: "kWh",
    ENTITY_LAST_CHARGING_COST: "$",
    ENTITY_LAST_CHARGING_LOCATION: None,
    ENTITY_LAST_CHARGING_DATE: None,
    ENTITY_LAST_PEAK_POWER: "kW",
    ENTITY_LAST_COST_PER_KWH: "$/kWh",
    ENTITY_LAST_PROVIDER: None,
}

# Data attribute mapping
ATTR_MAP = {
    ENTITY_TOTAL_ENERGY: "total_kwh",
    ENTITY_TOTAL_COST: "total_cost",
    ENTITY_AVERAGE_COST_PER_KWH: "avg_cost_per_kwh",
    ENTITY_SESSION_COUNT: "session_count",
    ENTITY_LAST_CHARGING_ENERGY: "energy_kwh",
    ENTITY_LAST_CHARGING_COST: "cost",
    ENTITY_LAST_CHARGING_LOCATION: "location",
    ENTITY_LAST_CHARGING_DATE: "date",
    ENTITY_LAST_PEAK_POWER: "peak_kw",
    ENTITY_LAST_COST_PER_KWH: "cost_per_kwh",
    ENTITY_LAST_PROVIDER: "provider",
}