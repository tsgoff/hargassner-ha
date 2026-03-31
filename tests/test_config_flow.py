"""Tests for the Hargassner config flow."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hargassner.api import HargassnerApiError, HargassnerAuthError
from custom_components.hargassner.const import (
    CONF_INSTALLATION_ID,
    CONF_INSTALLATION_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from tests.conftest import MOCK_INSTALLATIONS


PATCH_API = "custom_components.hargassner.config_flow.HargassnerApi"
PATCH_CLIENT_SESSION = "custom_components.hargassner.config_flow.async_get_clientsession"
PATCH_SETUP_ENTRY = "custom_components.hargassner.async_setup_entry"


# ---------------------------------------------------------------------------
# Single installation (auto-select)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_config_flow_single_installation(hass):
    """With one installation, the flow completes without the extra selection step."""
    with (
        patch(PATCH_API) as MockApi,
        patch(PATCH_CLIENT_SESSION, return_value=MagicMock()),
        patch(PATCH_SETUP_ENTRY, return_value=True),
    ):
        instance = MockApi.return_value
        instance.login = AsyncMock()
        instance.get_installations = AsyncMock(return_value=MOCK_INSTALLATIONS)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"},
        )
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_EMAIL] == "test@example.com"
        assert result["data"][CONF_INSTALLATION_ID] == "42"


# ---------------------------------------------------------------------------
# Multiple installations (selection step)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_config_flow_multiple_installations_select_one(hass):
    """With multiple installations, user can select one."""
    installations = [
        {"id": "42", "name": "Home"},
        {"id": "99", "name": "Office"},
    ]
    with (
        patch(PATCH_API) as MockApi,
        patch(PATCH_CLIENT_SESSION, return_value=MagicMock()),
        patch(PATCH_SETUP_ENTRY, return_value=True),
    ):
        instance = MockApi.return_value
        instance.login = AsyncMock()
        instance.get_installations = AsyncMock(return_value=installations)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"},
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "installation"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"installation_ids": ["99"]},
        )
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_INSTALLATION_ID] == "99"
        assert result["title"] == "Office"


@pytest.mark.asyncio
async def test_config_flow_multiple_installations_select_many(hass):
    """With multiple installations, user can select several at once."""
    installations = [
        {"id": "42", "name": "Home"},
        {"id": "99", "name": "Office"},
    ]
    with (
        patch(PATCH_API) as MockApi,
        patch(PATCH_CLIENT_SESSION, return_value=MagicMock()),
        patch(PATCH_SETUP_ENTRY, return_value=True),
    ):
        instance = MockApi.return_value
        instance.login = AsyncMock()
        instance.get_installations = AsyncMock(return_value=installations)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"},
        )
        assert result["step_id"] == "installation"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"installation_ids": ["42", "99"]},
        )
        # The flow returns the last selected entry
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_INSTALLATION_ID] == "99"

        # The first was created via import
        entries = hass.config_entries.async_entries(DOMAIN)
        assert len(entries) == 2
        ids = {e.data[CONF_INSTALLATION_ID] for e in entries}
        assert ids == {"42", "99"}


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_config_flow_invalid_auth(hass):
    with patch(PATCH_API) as MockApi, patch(PATCH_CLIENT_SESSION, return_value=MagicMock()):
        instance = MockApi.return_value
        instance.login = AsyncMock(side_effect=HargassnerAuthError("Bad credentials"))

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "bad@example.com", CONF_PASSWORD: "wrong"},
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_config_flow_cannot_connect(hass):
    with patch(PATCH_API) as MockApi, patch(PATCH_CLIENT_SESSION, return_value=MagicMock()):
        instance = MockApi.return_value
        instance.login = AsyncMock(side_effect=HargassnerApiError("Timeout"))

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"},
        )
        assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_config_flow_no_installations(hass):
    with patch(PATCH_API) as MockApi, patch(PATCH_CLIENT_SESSION, return_value=MagicMock()):
        instance = MockApi.return_value
        instance.login = AsyncMock()
        instance.get_installations = AsyncMock(return_value=[])

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"},
        )
        assert result["errors"]["base"] == "no_installations"


@pytest.mark.asyncio
async def test_config_flow_unknown_error(hass):
    with patch(PATCH_API) as MockApi, patch(PATCH_CLIENT_SESSION, return_value=MagicMock()):
        instance = MockApi.return_value
        instance.login = AsyncMock(side_effect=RuntimeError("Something went very wrong"))

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"},
        )
        assert result["errors"]["base"] == "unknown"


# ---------------------------------------------------------------------------
# Already configured (abort)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_config_flow_already_configured(hass):
    """Trying to add the same installation twice should abort."""
    with (
        patch(PATCH_API) as MockApi,
        patch(PATCH_CLIENT_SESSION, return_value=MagicMock()),
        patch(PATCH_SETUP_ENTRY, return_value=True),
    ):
        instance = MockApi.return_value
        instance.login = AsyncMock()
        instance.get_installations = AsyncMock(return_value=MOCK_INSTALLATIONS)

        # First setup
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"},
        )

    # Second setup attempt
    with (
        patch(PATCH_API) as MockApi,
        patch(PATCH_CLIENT_SESSION, return_value=MagicMock()),
        patch(PATCH_SETUP_ENTRY, return_value=True),
    ):
        instance = MockApi.return_value
        instance.login = AsyncMock()
        instance.get_installations = AsyncMock(return_value=MOCK_INSTALLATIONS)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"},
        )
        assert result["type"] == data_entry_flow.FlowResultType.ABORT
        assert result["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# Options flow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_options_flow_changes_scan_interval(hass):
    """Options flow should allow changing the scan interval."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "secret",
            CONF_INSTALLATION_ID: "42",
            "installation_name": "My Hargassner",
        },
        options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
        unique_id="hargassner_42",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 120},
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_SCAN_INTERVAL] == 120
