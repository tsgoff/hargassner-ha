"""Tests for the Hargassner data coordinator."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.hargassner.api import HargassnerApiError, HargassnerAuthError
from custom_components.hargassner.coordinator import HargassnerCoordinator
from tests.conftest import MOCK_WIDGET_HEATER, MOCK_WIDGET_CIRCUIT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_coordinator(hass, mock_api, scan_interval=60):
    return HargassnerCoordinator(
        hass=hass,
        api=mock_api,
        installation_id="42",
        installation_name="My Hargassner",
        scan_interval=scan_interval,
    )


# ---------------------------------------------------------------------------
# _async_update_data — happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_data_success(hass, mock_api):
    coord = make_coordinator(hass, mock_api)
    data = await coord._async_update_data()

    assert "_online" in data
    assert data["_online"] is True

    # Both widgets should be present
    heater_keys = [k for k in data if "HEATER" in k]
    circuit_keys = [k for k in data if "HEATING_CIRCUIT" in k]
    assert len(heater_keys) >= 1
    assert len(circuit_keys) >= 1


@pytest.mark.asyncio
async def test_update_data_widget_structure(hass, mock_api):
    coord = make_coordinator(hass, mock_api)
    data = await coord._async_update_data()

    # Find the HEATER widget entry
    heater_entry = next((v for k, v in data.items() if isinstance(v, dict) and v.get("widget_type") == "HEATER"), None)
    assert heater_entry is not None
    assert heater_entry["widget_name"] == "Boiler"
    assert heater_entry["values"]["heater_temperature_current"] == 75.0
    assert "fuel_stock" in heater_entry["parameters"]


@pytest.mark.asyncio
async def test_update_data_sets_online_state(hass, mock_api):
    mock_api.get_widgets = AsyncMock(return_value=(
        [MOCK_WIDGET_HEATER],
        {"online_state": False},
    ))
    coord = make_coordinator(hass, mock_api)
    data = await coord._async_update_data()

    assert data["_online"] is False
    assert coord.online_state is False


# ---------------------------------------------------------------------------
# _async_update_data — error handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_data_api_error_with_cache(hass, mock_api):
    """On API error, coordinator should return cached data with _online=False."""
    coord = make_coordinator(hass, mock_api)

    # First call succeeds and populates cache
    await coord._async_update_data()

    # Second call fails
    mock_api.get_widgets = AsyncMock(side_effect=HargassnerApiError("Timeout"))
    data = await coord._async_update_data()

    assert data["_online"] is False
    # Cached widget data should still be present
    heater_keys = [k for k in data if isinstance(data[k], dict) and data[k].get("widget_type") == "HEATER"]
    assert len(heater_keys) >= 1


@pytest.mark.asyncio
async def test_update_data_api_error_no_cache_raises(hass, mock_api):
    """Without cache, API error should raise UpdateFailed."""
    mock_api.get_widgets = AsyncMock(side_effect=HargassnerApiError("Timeout"))
    coord = make_coordinator(hass, mock_api)

    with pytest.raises(UpdateFailed, match="API error"):
        await coord._async_update_data()


@pytest.mark.asyncio
async def test_update_data_auth_error_with_cache(hass, mock_api):
    """On auth error, cached data should be returned."""
    coord = make_coordinator(hass, mock_api)
    await coord._async_update_data()  # populate cache

    mock_api.get_widgets = AsyncMock(side_effect=HargassnerAuthError("Token expired"))
    data = await coord._async_update_data()

    # Should return cached data
    assert data is not None


@pytest.mark.asyncio
async def test_update_data_auth_error_no_cache_raises(hass, mock_api):
    """Without cache, auth error should raise UpdateFailed."""
    mock_api.ensure_token_valid = AsyncMock(side_effect=HargassnerAuthError("No token"))
    coord = make_coordinator(hass, mock_api)

    with pytest.raises(UpdateFailed, match="Authentication error"):
        await coord._async_update_data()


@pytest.mark.asyncio
async def test_update_data_ignores_non_dict_widgets(hass, mock_api):
    """Non-dict items in widget list should be skipped without error."""
    mock_api.get_widgets = AsyncMock(return_value=(
        ["not-a-dict", None, 42, MOCK_WIDGET_HEATER],
        {"online_state": True},
    ))
    coord = make_coordinator(hass, mock_api)
    data = await coord._async_update_data()

    heater_keys = [k for k in data if isinstance(data[k], dict) and data[k].get("widget_type") == "HEATER"]
    assert len(heater_keys) == 1


@pytest.mark.asyncio
async def test_update_data_ignores_non_dict_parameters(hass, mock_api):
    """Non-dict parameters in a widget should be filtered out."""
    widget_with_bad_param = {
        **MOCK_WIDGET_HEATER,
        "parameters": {
            "fuel_stock": {"value": 500, "resource": "/api/res/1"},
            "bad_list_param": [1, 2, 3],
            "bad_scalar": "raw_string",
        },
    }
    mock_api.get_widgets = AsyncMock(return_value=([widget_with_bad_param], {"online_state": True}))
    coord = make_coordinator(hass, mock_api)
    data = await coord._async_update_data()

    heater = next((v for k, v in data.items() if isinstance(v, dict) and v.get("widget_type") == "HEATER"), None)
    assert "fuel_stock" in heater["parameters"]
    assert "bad_list_param" not in heater["parameters"]
    assert "bad_scalar" not in heater["parameters"]


# ---------------------------------------------------------------------------
# async_patch_value / async_post_action
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_patch_value_calls_api(hass, mock_api):
    coord = make_coordinator(hass, mock_api)
    coord.async_request_refresh = AsyncMock()

    result = await coord.async_patch_value("https://api/resource/1", 22.5)
    assert result is True
    mock_api.patch_value.assert_called_once_with("https://api/resource/1", 22.5)


@pytest.mark.asyncio
async def test_async_patch_value_returns_false_on_error(hass, mock_api):
    mock_api.patch_value = AsyncMock(side_effect=HargassnerApiError("Write failed"))
    coord = make_coordinator(hass, mock_api)
    coord.async_request_refresh = AsyncMock()

    result = await coord.async_patch_value("https://api/resource/1", 99)
    assert result is False


@pytest.mark.asyncio
async def test_async_post_action_calls_api(hass, mock_api):
    coord = make_coordinator(hass, mock_api)
    coord.async_request_refresh = AsyncMock()

    result = await coord.async_post_action("https://api/actions/ignition")
    assert result is True
    mock_api.post_action.assert_called_once_with("https://api/actions/ignition")


@pytest.mark.asyncio
async def test_async_post_action_returns_false_on_error(hass, mock_api):
    mock_api.post_action = AsyncMock(side_effect=HargassnerApiError("Action failed"))
    coord = make_coordinator(hass, mock_api)
    coord.async_request_refresh = AsyncMock()

    result = await coord.async_post_action("https://api/actions/ignition")
    assert result is False
