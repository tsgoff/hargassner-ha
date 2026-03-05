"""Data update coordinator for Hargassner."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HargassnerApi, HargassnerApiError, HargassnerAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class HargassnerCoordinator(DataUpdateCoordinator):
    """Manages polling data from the Hargassner API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: HargassnerApi,
        installation_id: str,
        installation_name: str,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{installation_id}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        self.installation_id = installation_id
        self.installation_name = installation_name
        self.online_state: bool = True
        self._last_good_data: dict[str, Any] | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest widget data, with offline fallback and token refresh."""
        # Proactively refresh token if close to expiry
        try:
            await self.api.ensure_token_valid()
        except HargassnerAuthError as err:
            _LOGGER.error("Re-authentication failed: %s", err)
            if self._last_good_data:
                _LOGGER.warning("Using cached data due to auth failure")
                return self._last_good_data
            raise UpdateFailed(f"Authentication error: {err}") from err

        try:
            widgets, meta = await self.api.get_widgets(self.installation_id)
        except HargassnerAuthError as err:
            if self._last_good_data:
                _LOGGER.warning("Auth error, using cached data: %s", err)
                return self._last_good_data
            raise UpdateFailed(f"Authentication error: {err}") from err
        except HargassnerApiError as err:
            # Keep last known values when offline
            if self._last_good_data:
                _LOGGER.warning("API error, keeping last known values: %s", err)
                self.online_state = False
                stale = dict(self._last_good_data)
                stale["_online"] = False
                return stale
            raise UpdateFailed(f"API error: {err}") from err

        # Build result dict
        self.online_state = meta.get("online_state", True)
        result: dict[str, Any] = {
            "_online": self.online_state,
            "_meta": meta,
        }

        for widget in widgets:
            if not isinstance(widget, dict):
                continue
            widget_type = widget.get("widget", "UNKNOWN")
            widget_number = widget.get("number", "")
            widget_name = widget.get("values", {}).get("name", widget_type)
            parameters = widget.get("parameters", {})
            values = widget.get("values", {})
            actions = widget.get("actions", {})

            # Include circuit number in key to avoid collisions (e.g. multiple circuits)
            suffix = f"_{widget_number}" if widget_number else ""
            widget_key = f"{widget_type}{suffix}_{widget_name}".replace(" ", "_").replace(".", "_").upper()

            result[widget_key] = {
                "widget_type": widget_type,
                "widget_name": widget_name,
                "widget_number": widget_number,
                "parameters": parameters,
                "values": values,
                "actions": actions,
            }

        # Cache for offline fallback
        self._last_good_data = dict(result)
        self._last_good_data["_online"] = True

        return result

    async def async_patch_value(self, resource_url: str, value: Any) -> bool:
        """Set a parameter value and refresh."""
        try:
            await self.api.patch_value(resource_url, value)
            await self.async_request_refresh()
            return True
        except HargassnerApiError as err:
            _LOGGER.error("Failed to set value at %s: %s", resource_url, err)
            return False

    async def async_post_action(self, resource_url: str) -> bool:
        """Trigger an action and refresh."""
        try:
            await self.api.post_action(resource_url)
            await self.async_request_refresh()
            return True
        except HargassnerApiError as err:
            _LOGGER.error("Failed to execute action at %s: %s", resource_url, err)
            return False
