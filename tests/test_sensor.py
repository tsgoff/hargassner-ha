"""Tests for sensor entity descriptions and state logic."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from custom_components.hargassner.sensor import (
    SENSOR_DESCRIPTIONS,
    HargassnerSensorEntity,
    HargassnerOnlineSensor,
)
from custom_components.hargassner.coordinator import HargassnerCoordinator


# ---------------------------------------------------------------------------
# SENSOR_DESCRIPTIONS integrity
# ---------------------------------------------------------------------------

def test_sensor_descriptions_all_have_english_names():
    """All sensor names must be in English (no French/German characters)."""
    forbidden_chars = set("àâäçéèêëîïôöùûüÿæœÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸÆŒßÄÖÜ")
    for prefix, value_key, desc in SENSOR_DESCRIPTIONS:
        name = desc.name or ""
        bad = [c for c in name if c in forbidden_chars]
        assert not bad, f"Non-English chars in sensor name '{name}': {bad}"


def test_sensor_descriptions_keys_are_unique():
    keys = [desc.key for _, _, desc in SENSOR_DESCRIPTIONS]
    # Keys may repeat across widget types but should be consistent
    assert len(keys) == len(SENSOR_DESCRIPTIONS)


def test_sensor_descriptions_have_required_fields():
    for prefix, value_key, desc in SENSOR_DESCRIPTIONS:
        assert prefix, "Widget prefix must not be empty"
        assert value_key, "value_key must not be empty"
        assert desc.key, f"desc.key must not be empty for {desc.name}"
        assert desc.name, f"desc.name must not be empty for key={desc.key}"
        assert desc.value_key == value_key, (
            f"value_key mismatch for {desc.key}: {desc.value_key!r} != {value_key!r}"
        )


# ---------------------------------------------------------------------------
# HargassnerOnlineSensor
# ---------------------------------------------------------------------------

def make_online_sensor(online: bool | None = True):
    coordinator = MagicMock(spec=HargassnerCoordinator)
    coordinator.installation_id = "42"
    coordinator.installation_name = "My Hargassner"
    if online is None:
        coordinator.data = None
    else:
        coordinator.data = {"_online": online}
    return HargassnerOnlineSensor(coordinator)


def test_online_sensor_when_online():
    sensor = make_online_sensor(True)
    assert sensor.native_value == "Online"
    assert sensor.icon == "mdi:cloud-check"


def test_online_sensor_when_offline():
    sensor = make_online_sensor(False)
    assert sensor.native_value == "Offline"
    assert sensor.icon == "mdi:cloud-off-outline"


def test_online_sensor_when_no_data():
    sensor = make_online_sensor(None)
    assert sensor.native_value == "Unknown"


def test_online_sensor_unique_id():
    sensor = make_online_sensor()
    assert "42" in sensor._attr_unique_id
    assert "online" in sensor._attr_unique_id


# ---------------------------------------------------------------------------
# HargassnerSensorEntity — value retrieval
# ---------------------------------------------------------------------------

def make_sensor_entity(values: dict, description=None):
    from custom_components.hargassner.sensor import HargassnerSensorDescription
    from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
    from homeassistant.const import UnitOfTemperature

    if description is None:
        description = HargassnerSensorDescription(
            key="heater_temp_current",
            name="Boiler Temperature",
            value_key="heater_temperature_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        )

    coordinator = MagicMock(spec=HargassnerCoordinator)
    coordinator.installation_id = "42"
    coordinator.installation_name = "My Hargassner"
    coordinator.data = {
        "HEATER_1_Boiler": {
            "widget_type": "HEATER",
            "widget_name": "Boiler",
            "values": values,
            "parameters": {},
            "actions": {},
        }
    }

    entity = HargassnerSensorEntity(
        coordinator=coordinator,
        widget_key="HEATER_1_Boiler",
        param_key="heater_temperature_current",
        widget_name="Boiler",
        description=description,
    )
    return entity


def test_sensor_entity_reads_value():
    sensor = make_sensor_entity({"heater_temperature_current": 75.5})
    assert sensor.native_value == 75.5


def test_sensor_entity_returns_none_when_key_missing():
    sensor = make_sensor_entity({})
    assert sensor.native_value is None


def test_sensor_entity_name_includes_widget_name():
    sensor = make_sensor_entity({"heater_temperature_current": 75.0})
    assert "Boiler" in sensor._attr_name
    assert "Boiler Temperature" in sensor._attr_name
