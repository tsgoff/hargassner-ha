"""Hargassner integration for Home Assistant."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HargassnerApi, HargassnerApiError, HargassnerAuthError
from .const import (
    CONF_INSTALLATION_ID,
    CONF_INSTALLATION_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SERVICE_START_IGNITION,
)
from .coordinator import HargassnerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

SERVICE_SCHEMA = vol.Schema({
    vol.Required("installation_id"): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hargassner from a config entry."""
    session = async_get_clientsession(hass)
    api = HargassnerApi(session)

    try:
        await api.login(entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
    except HargassnerAuthError as err:
        _LOGGER.error("Authentication failed: %s", err)
        return False
    except HargassnerApiError as err:
        _LOGGER.error("Could not connect to Hargassner API: %s", err)
        return False

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = HargassnerCoordinator(
        hass,
        api,
        installation_id=entry.data[CONF_INSTALLATION_ID],
        installation_name=entry.data.get(CONF_INSTALLATION_NAME, "Hargassner"),
        scan_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register service: hargassner.start_ignition
    async def handle_start_ignition(call: ServiceCall) -> None:
        """Trigger ignition on the boiler."""
        for coord in hass.data.get(DOMAIN, {}).values():
            if not isinstance(coord, HargassnerCoordinator):
                continue
            data = coord.data or {}
            for widget_data in data.values():
                if not isinstance(widget_data, dict):
                    continue
                actions = widget_data.get("actions", {})
                ignition = actions.get("start_ignition", {})
                if isinstance(ignition, dict) and ignition.get("resource"):
                    await coord.async_post_action(ignition["resource"])
                    _LOGGER.info("start_ignition triggered on %s", coord.installation_name)
                    return
        _LOGGER.warning("start_ignition: no ignition action found")

    if not hass.services.has_service(DOMAIN, SERVICE_START_IGNITION):
        hass.services.async_register(DOMAIN, SERVICE_START_IGNITION, handle_start_ignition)

    # Listen for options updates (scan interval change)
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update (e.g. scan interval changed)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: HargassnerCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.logout()
    return unload_ok
