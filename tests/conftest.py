"""Shared fixtures and helpers for Hargassner tests."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hargassner.api import HargassnerApi


pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


# ---------------------------------------------------------------------------
# Sample API payloads
# ---------------------------------------------------------------------------

MOCK_INSTALLATIONS = [
    {"id": "42", "name": "My Hargassner"},
]

MOCK_WIDGET_HEATER = {
    "widget": "HEATER",
    "number": "1",
    "values": {
        "name": "Boiler",
        "heater_temperature_current": 75.0,
        "heater_temperature_target": 80.0,
        "smoke_temperature": 120.0,
        "outdoor_temperature": 5.0,
        "outdoor_temperature_average": 6.0,
        "state": "HEATING",
        "program": "AUTO",
        "fuel_stock": 500.0,
        "efficiency": 92.0,
    },
    "parameters": {
        "fuel_stock": {
            "value": 500.0,
            "min": 0,
            "max": 32000,
            "step": 1,
            "resource": "https://web.hargassner.at/api/installations/42/widgets/1/parameters/fuel_stock",
        },
    },
    "actions": {
        "start_ignition": {
            "resource": "https://web.hargassner.at/api/installations/42/widgets/1/actions/start_ignition",
        }
    },
}

MOCK_WIDGET_CIRCUIT = {
    "widget": "HEATING_CIRCUIT",
    "number": "1",
    "values": {
        "name": "Circuit 1",
        "flow_temperature_current": 45.0,
        "flow_temperature_target": 48.0,
        "room_temperature_current": 21.0,
        "room_temperature_target": 22.0,
        "state": "ACTIVE",
        "pump_active": True,
    },
    "parameters": {
        "mode": {
            "value": "MODE_AUTOMATIC",
            "options": ["MODE_OFF", "MODE_AUTOMATIC", "MODE_HEATING", "MODE_REDUCTION"],
            "resource": "https://web.hargassner.at/api/installations/42/widgets/2/parameters/mode",
        },
        "room_temperature_heating": {
            "value": 22.0,
            "min": 14,
            "max": 26,
            "step": 0.5,
            "resource": "https://web.hargassner.at/api/installations/42/widgets/2/parameters/room_temperature_heating",
        },
    },
    "actions": {},
}

MOCK_WIDGETS_RESPONSE = {
    "data": [MOCK_WIDGET_HEATER, MOCK_WIDGET_CIRCUIT],
    "meta": {"online_state": True},
}

MOCK_LOGIN_RESPONSE = {
    "data": {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "expires_in": 3600,
    }
}

MOCK_CONFIG_ENTRY_DATA = {
    "email": "test@example.com",
    "password": "secret",
    "installation_id": "42",
    "installation_name": "My Hargassner",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_api():
    """Return a pre-configured mock HargassnerApi."""
    api = MagicMock(spec=HargassnerApi)
    api.is_authenticated = True
    api.token_needs_refresh = False
    api.login = AsyncMock(return_value=MOCK_LOGIN_RESPONSE)
    api.logout = AsyncMock()
    api.get_installations = AsyncMock(return_value=MOCK_INSTALLATIONS)
    api.get_widgets = AsyncMock(
        return_value=(MOCK_WIDGETS_RESPONSE["data"], MOCK_WIDGETS_RESPONSE["meta"])
    )
    api.patch_value = AsyncMock(return_value={})
    api.post_action = AsyncMock(return_value={})
    api.ensure_token_valid = AsyncMock()
    return api
