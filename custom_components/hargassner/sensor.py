"""Sensor entities for Hargassner."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import HargassnerCoordinator
from .entity_base import HargassnerEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class HargassnerSensorDescription(SensorEntityDescription):
    """Describes a Hargassner sensor."""

    value_key: str = ""


# (widget_type_prefix, value_key, description)
SENSOR_DESCRIPTIONS: list[tuple[str, str, HargassnerSensorDescription]] = [
    # --- HEATER ---
    (
        "HEATER",
        "heater_temperature_current",
        HargassnerSensorDescription(
            key="heater_temp_current",
            name="Boiler Temperature",
            value_key="heater_temperature_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATER",
        "heater_temperature_target",
        HargassnerSensorDescription(
            key="heater_temp_target",
            name="Boiler Target Temperature",
            value_key="heater_temperature_target",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATER",
        "smoke_temperature",
        HargassnerSensorDescription(
            key="smoke_temperature",
            name="Flue Gas Temperature",
            value_key="smoke_temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATER",
        "outdoor_temperature",
        HargassnerSensorDescription(
            key="outdoor_temperature",
            name="Outdoor Temperature",
            value_key="outdoor_temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATER",
        "outdoor_temperature_average",
        HargassnerSensorDescription(
            key="outdoor_temperature_average",
            name="Outdoor Temperature (Average)",
            value_key="outdoor_temperature_average",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATER",
        "state",
        HargassnerSensorDescription(
            key="heater_state",
            name="Boiler State",
            value_key="state",
            icon="mdi:fire",
        ),
    ),
    (
        "HEATER",
        "program",
        HargassnerSensorDescription(
            key="heater_program",
            name="Program",
            value_key="program",
            icon="mdi:calendar-clock",
        ),
    ),
    (
        "HEATER",
        "device_type",
        HargassnerSensorDescription(
            key="device_type",
            name="Device Type",
            value_key="device_type",
            icon="mdi:information-outline",
        ),
    ),
    (
        "HEATER",
        "heater_exhaust_guard",
        HargassnerSensorDescription(
            key="heater_exhaust_guard",
            name="Exhaust Guard",
            value_key="heater_exhaust_guard",
            icon="mdi:shield-alert",
        ),
    ),
    (
        "HEATER",
        "fuel_stock",
        HargassnerSensorDescription(
            key="fuel_stock",
            name="Fuel Stock",
            value_key="fuel_stock",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="kg",
            icon="mdi:sack",
        ),
    ),
    (
        "HEATER",
        "efficiency",
        HargassnerSensorDescription(
            key="efficiency",
            name="Efficiency",
            value_key="efficiency",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=PERCENTAGE,
            icon="mdi:gauge",
        ),
    ),
    # --- HEATING CIRCUIT ---
    (
        "HEATING_CIRCUIT",
        "flow_temperature_current",
        HargassnerSensorDescription(
            key="flow_temp_current",
            name="Flow Temperature",
            value_key="flow_temperature_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATING_CIRCUIT",
        "flow_temperature_target",
        HargassnerSensorDescription(
            key="flow_temp_target",
            name="Flow Target Temperature",
            value_key="flow_temperature_target",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATING_CIRCUIT",
        "room_temperature_current",
        HargassnerSensorDescription(
            key="room_temp_current",
            name="Room Temperature",
            value_key="room_temperature_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATING_CIRCUIT",
        "room_temperature_target",
        HargassnerSensorDescription(
            key="room_temp_target",
            name="Room Target Temperature",
            value_key="room_temperature_target",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATING_CIRCUIT",
        "state",
        HargassnerSensorDescription(
            key="circuit_state",
            name="Circuit State",
            value_key="state",
            icon="mdi:radiator",
        ),
    ),
    (
        "HEATING_CIRCUIT",
        "pump_active",
        HargassnerSensorDescription(
            key="pump_active",
            name="Pump Active",
            value_key="pump_active",
            icon="mdi:pump",
        ),
    ),
    (
        "HEATING_CIRCUIT",
        "outdoor_temperature",
        HargassnerSensorDescription(
            key="circuit_outdoor_temperature",
            name="Outdoor Temperature",
            value_key="outdoor_temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATING_CIRCUIT",
        "outdoor_temperature_average",
        HargassnerSensorDescription(
            key="circuit_outdoor_temperature_average",
            name="Outdoor Temperature (Average)",
            value_key="outdoor_temperature_average",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATING_CIRCUIT",
        "active",
        HargassnerSensorDescription(
            key="circuit_active",
            name="Active",
            value_key="active",
            icon="mdi:radiator",
        ),
    ),
    # --- HEATING_CIRCUIT_CONTROLLER ---
    (
        "HEATING_CIRCUIT_CONTROLLER",
        "source_temperature",
        HargassnerSensorDescription(
            key="source_temperature",
            name="Source Temperature",
            value_key="source_temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATING_CIRCUIT_CONTROLLER",
        "request_temperature",
        HargassnerSensorDescription(
            key="request_temperature",
            name="Request Temperature",
            value_key="request_temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATING_CIRCUIT_CONTROLLER",
        "secondary_flow_temperature_current",
        HargassnerSensorDescription(
            key="secondary_flow_temp_current",
            name="Secondary Flow Temperature",
            value_key="secondary_flow_temperature_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATING_CIRCUIT_CONTROLLER",
        "secondary_flow_temperature_target",
        HargassnerSensorDescription(
            key="secondary_flow_temp_target",
            name="Secondary Flow Target Temperature",
            value_key="secondary_flow_temperature_target",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATING_CIRCUIT_CONTROLLER",
        "primary_return_temperature_current",
        HargassnerSensorDescription(
            key="primary_return_temp_current",
            name="Primary Return Temperature",
            value_key="primary_return_temperature_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "HEATING_CIRCUIT_CONTROLLER",
        "program",
        HargassnerSensorDescription(
            key="controller_program",
            name="Program",
            value_key="program",
            icon="mdi:calendar-clock",
        ),
    ),
    # --- BUFFER ---
    (
        "BUFFER",
        "state",
        HargassnerSensorDescription(
            key="buffer_state",
            name="Buffer State",
            value_key="state",
            icon="mdi:water-boiler",
        ),
    ),
    (
        "BUFFER",
        "buffer_charge",
        HargassnerSensorDescription(
            key="buffer_charge",
            name="Buffer Charge",
            value_key="buffer_charge",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=PERCENTAGE,
            icon="mdi:battery-charging",
        ),
    ),
    (
        "BUFFER",
        "capacity",
        HargassnerSensorDescription(
            key="buffer_capacity",
            name="Buffer Capacity",
            value_key="capacity",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfVolume.LITERS,
            icon="mdi:water",
        ),
    ),
    (
        "BUFFER",
        "buffer_temperature_top",
        HargassnerSensorDescription(
            key="buffer_temp_top",
            name="Buffer Temperature Top",
            value_key="buffer_temperature_top",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "BUFFER",
        "buffer_temperature_center",
        HargassnerSensorDescription(
            key="buffer_temp_center",
            name="Buffer Temperature Center",
            value_key="buffer_temperature_center",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "BUFFER",
        "buffer_temperature_bottom",
        HargassnerSensorDescription(
            key="buffer_temp_bottom",
            name="Buffer Temperature Bottom",
            value_key="buffer_temperature_bottom",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "BUFFER",
        "pump_active",
        HargassnerSensorDescription(
            key="buffer_pump_active",
            name="Pump Active",
            value_key="pump_active",
            icon="mdi:pump",
        ),
    ),
    # --- BOILER ---
    (
        "BOILER",
        "state",
        HargassnerSensorDescription(
            key="boiler_state",
            name="Boiler State",
            value_key="state",
            icon="mdi:water-boiler",
        ),
    ),
    (
        "BOILER",
        "boiler_temperature_current",
        HargassnerSensorDescription(
            key="boiler_temp_current",
            name="Boiler Temperature",
            value_key="boiler_temperature_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "BOILER",
        "boiler_temperature_target",
        HargassnerSensorDescription(
            key="boiler_temp_target",
            name="Boiler Target Temperature",
            value_key="boiler_temperature_target",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ),
    (
        "BOILER",
        "boiler_charge",
        HargassnerSensorDescription(
            key="boiler_charge",
            name="Boiler Charge",
            value_key="boiler_charge",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=PERCENTAGE,
            icon="mdi:battery-charging",
        ),
    ),
    (
        "BOILER",
        "pump_active",
        HargassnerSensorDescription(
            key="boiler_pump_active",
            name="Pump Active",
            value_key="pump_active",
            icon="mdi:pump",
        ),
    ),
    (
        "BOILER",
        "circulation_pump_active",
        HargassnerSensorDescription(
            key="circulation_pump_active",
            name="Circulation Pump Active",
            value_key="circulation_pump_active",
            icon="mdi:pump",
        ),
    ),
    (
        "BOILER",
        "force_charging_active",
        HargassnerSensorDescription(
            key="force_charging_active",
            name="Force Charging Active",
            value_key="force_charging_active",
            icon="mdi:lightning-bolt",
        ),
    ),
    # --- EVENTS ---
    (
        "EVENTS",
        "event_count",
        HargassnerSensorDescription(
            key="event_count",
            name="Active Events",
            value_key="event_count",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:alert-circle",
        ),
    ),
    (
        "EVENTS",
        "latest_event",
        HargassnerSensorDescription(
            key="latest_event",
            name="Latest Event",
            value_key="latest_event",
            icon="mdi:alert",
        ),
    ),
    (
        "EVENTS",
        "latest_event_type",
        HargassnerSensorDescription(
            key="latest_event_type",
            name="Latest Event Type",
            value_key="latest_event_type",
            icon="mdi:alert-outline",
        ),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hargassner sensor entities."""
    coordinator: HargassnerCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[HargassnerSensorEntity] = []

    if not coordinator.data:
        return

    for widget_key, widget_data in coordinator.data.items():
        if not isinstance(widget_data, dict) or "widget_type" not in widget_data:
            continue

        widget_type = widget_data["widget_type"]
        widget_name = widget_data["widget_name"]
        values = widget_data.get("values", {})

        for prefix, value_key, description in SENSOR_DESCRIPTIONS:
            if not widget_type.startswith(prefix):
                continue
            if value_key not in values:
                continue

            entities.append(
                HargassnerSensorEntity(
                    coordinator=coordinator,
                    widget_key=widget_key,
                    param_key=value_key,
                    widget_name=widget_name,
                    description=description,
                )
            )

    # Add online state sensor
    entities.append(HargassnerOnlineSensor(coordinator))
    async_add_entities(entities)


class HargassnerSensorEntity(HargassnerEntity, SensorEntity):
    """A sensor entity for a Hargassner parameter."""

    entity_description: HargassnerSensorDescription

    def __init__(
        self,
        coordinator: HargassnerCoordinator,
        widget_key: str,
        param_key: str,
        widget_name: str,
        description: HargassnerSensorDescription,
    ) -> None:
        super().__init__(
            coordinator,
            widget_key,
            param_key,
            f"{widget_key}_{description.key}",
        )
        self.entity_description = description
        self._attr_name = f"{widget_name} {description.name}"

    @property
    def native_value(self) -> Any:
        return self._get_value()


class HargassnerOnlineSensor(HargassnerEntity, SensorEntity):
    """Sensor showing if the boiler is online."""

    def __init__(self, coordinator: HargassnerCoordinator) -> None:
        super().__init__(coordinator, "_online", "_online", "online_state")
        self._attr_name = "Connection State"
        self._attr_icon = "mdi:cloud-check"

    @property
    def native_value(self) -> str:
        if self.coordinator.data:
            return (
                "Online"
                if self.coordinator.data.get("_online", True)
                else "Offline"
            )
        return "Unknown"

    @property
    def icon(self) -> str:
        if self.coordinator.data and not self.coordinator.data.get("_online", True):
            return "mdi:cloud-off-outline"
        return "mdi:cloud-check"
