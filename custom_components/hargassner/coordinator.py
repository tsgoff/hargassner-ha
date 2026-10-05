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
        """Fetch latest widget data."""
        try:
            await self.api.ensure_token_valid()
        except HargassnerAuthError as err:
            _LOGGER.error("Re-authentication failed: %s", err)
            if self._last_good_data:
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
            if self._last_good_data:
                _LOGGER.warning("API error, keeping last known values: %s", err)
                stale = dict(self._last_good_data)
                stale["_online"] = False
                return stale
            raise UpdateFailed(f"API error: {err}") from err

        self.online_state = meta.get("online_state", True) if isinstance(meta, dict) else True
        result: dict[str, Any] = {
            "_online": self.online_state,
            "_meta": meta,
        }

        # EVENTS are no longer part of /widgets on current firmware/cloud
        # (see installation 68381 payload: only CONTROLLER/CIRCUIT/BOILER).
        # Fetch them via the dedicated /events endpoint; fall back to a
        # widgets-embedded EVENTS entry if the call fails.
        try:
            events = await self.api.get_events(self.installation_id)
        except (HargassnerApiError, HargassnerAuthError) as err:
            _LOGGER.debug("Could not fetch events, falling back to widgets: %s", err)
            events = None
        if events is not None and not isinstance(events, list):
            if isinstance(events, dict):
                maybe_data = events.get("data", [])
                events = maybe_data if isinstance(maybe_data, list) else []
            else:
                events = []

        # Event history groups (portal "Verlauf"): best-effort, never fails
        # the whole update. Used as fallback for latest_* when no event is
        # active, and to expose history totals.
        history: list[dict] = []
        history_total = 0
        try:
            history, history_total = await self.api.get_events_history_groups(
                self.installation_id, page_size=1
            )
        except (HargassnerApiError, HargassnerAuthError) as err:
            _LOGGER.debug("Could not fetch event history: %s", err)
            history, history_total = [], 0
        if not isinstance(history, list):
            history = []
        history_first = history[0] if history and isinstance(history[0], dict) else {}

        for widget in widgets:
            if not isinstance(widget, dict):
                _LOGGER.debug("Skipping non-dict widget: %s", type(widget))
                continue

            widget_type = widget.get("widget", "UNKNOWN")
            widget_number = str(widget.get("number", ""))

            # --- values : doit être un dict ---
            raw_values = widget.get("values")
            if isinstance(raw_values, dict):
                values = raw_values
            elif isinstance(raw_values, list) and widget_type == "EVENTS":
                # EVENTS widget returns values as a list of event dicts
                values = {
                    "event_count": len(raw_values),
                    "latest_event": raw_values[0].get("text", "") if raw_values else "",
                    "latest_event_type": raw_values[0].get("event_type", "") if raw_values else "",
                }
            else:
                values = {}
            widget_name = values.get("name", widget_type)

            # --- parameters : doit être un dict, filtrer les valeurs non-dict ---
            raw_parameters = widget.get("parameters")
            if isinstance(raw_parameters, dict):
                # Garder uniquement les paramètres qui sont des dicts (pas les listes/scalaires)
                parameters = {
                    k: v for k, v in raw_parameters.items()
                    if isinstance(v, dict)
                }
                # Logger les paramètres ignorés pour debug
                ignored = [k for k, v in raw_parameters.items() if not isinstance(v, dict)]
                if ignored:
                    _LOGGER.debug("Ignored non-dict parameters in %s: %s", widget_type, ignored)
            else:
                parameters = {}

            # --- actions : doit être un dict ---
            raw_actions = widget.get("actions")
            actions = raw_actions if isinstance(raw_actions, dict) else {}

            suffix = f"_{widget_number}" if widget_number else ""
            widget_key = (
                f"{widget_type}{suffix}_{widget_name}"
                .replace(" ", "_")
                .replace(".", "_")
                .upper()
            )

            result[widget_key] = {
                "widget_type": widget_type,
                "widget_name": widget_name,
                "widget_number": widget_number,
                "parameters": parameters,
                "values": values,
                "actions": actions,
            }

        if events is not None:
            # Dedicated endpoint is source of truth (widgets no longer
            # include EVENTS). Preserve confirm_all action from widgets
            # if present, else synthesize the known resource.
            existing_actions: dict[str, Any] = {}
            for entry in result.values():
                if isinstance(entry, dict) and entry.get("widget_type") == "EVENTS":
                    raw = entry.get("actions", {})
                    if isinstance(raw, dict):
                        existing_actions = raw
                    break
            if "confirm_all" not in existing_actions:
                existing_actions = {
                    **existing_actions,
                    "confirm_all": {
                        "resource": f"/installations/{self.installation_id}/widgets/events/actions/confirm-all"
                    },
                }
            first = events[0] if events else {}
            if not isinstance(first, dict):
                first = {}
            if events:
                latest_text = first.get("text", "")
                latest_type = first.get("event_type", "")
            elif history_first:
                latest_text = history_first.get("text", "")
                latest_type = history_first.get("event_type", "")
            else:
                latest_text, latest_type = "", ""
            last_occurred = history_first.get("last_occurred") if history_first else None
            result["EVENTS_EVENTS"] = {
                "widget_type": "EVENTS",
                "widget_name": "EVENTS",
                "widget_number": "",
                "parameters": {},
                "values": {
                    "event_count": len(events),
                    "latest_event": latest_text,
                    "latest_event_type": latest_type,
                    "history_event_count": history_total,
                    "last_event_occurred": last_occurred,
                },
                "actions": existing_actions,
            }

        self._last_good_data = dict(result)
        self._last_good_data["_online"] = True
        return result

    async def async_patch_value(self, resource_url: str, value: Any) -> bool:
        try:
            await self.api.patch_value(resource_url, value)
            await self.async_request_refresh()
            return True
        except HargassnerApiError as err:
            _LOGGER.error("Failed to set value at %s: %s", resource_url, err)
            return False

    async def async_post_action(self, resource_url: str) -> bool:
        try:
            await self.api.post_action(resource_url)
            await self.async_request_refresh()
            return True
        except HargassnerApiError as err:
            _LOGGER.error("Failed to execute action at %s: %s", resource_url, err)
            return False
