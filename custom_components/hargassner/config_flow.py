"""Config flow for Hargassner integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HargassnerApi, HargassnerApiError, HargassnerAuthError
from .const import (
    CONF_INSTALLATION_ID,
    CONF_INSTALLATION_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    MAX_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema({
    vol.Required(CONF_EMAIL): str,
    vol.Required(CONF_PASSWORD): str,
})


class HargassnerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Hargassner."""

    VERSION = 1

    def __init__(self) -> None:
        self._email: str = ""
        self._password: str = ""
        self._installations: list[dict] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = HargassnerApi(session)
            try:
                await api.login(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
                installations = await api.get_installations()
            except HargassnerAuthError:
                errors["base"] = "invalid_auth"
            except HargassnerApiError:
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected error: %s", err)
                errors["base"] = "unknown"
            else:
                if not installations:
                    errors["base"] = "no_installations"
                else:
                    self._email = user_input[CONF_EMAIL]
                    self._password = user_input[CONF_PASSWORD]
                    self._installations = installations
                    if len(installations) == 1:
                        return await self._create_entry(installations[0])
                    return await self.async_step_installation()

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

    async def async_step_installation(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            installation_id = user_input[CONF_INSTALLATION_ID]
            installation = next((i for i in self._installations if str(i.get("id")) == installation_id), None)
            if installation:
                return await self._create_entry(installation)

        options = {str(i.get("id")): i.get("name", str(i.get("id"))) for i in self._installations}
        schema = vol.Schema({vol.Required(CONF_INSTALLATION_ID): vol.In(options)})
        return self.async_show_form(step_id="installation", data_schema=schema)

    async def _create_entry(self, installation: dict) -> FlowResult:
        installation_id = str(installation.get("id"))
        installation_name = installation.get("name", installation_id)
        await self.async_set_unique_id(f"hargassner_{installation_id}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=installation_name,
            data={
                CONF_EMAIL: self._email,
                CONF_PASSWORD: self._password,
                CONF_INSTALLATION_ID: installation_id,
                CONF_INSTALLATION_NAME: installation_name,
            },
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return HargassnerOptionsFlow(config_entry)


class HargassnerOptionsFlow(config_entries.OptionsFlow):
    """Options flow — allows changing scan interval after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self._config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema({
            vol.Required(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
            ),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
