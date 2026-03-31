"""Button entities for Hargassner actions."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import HargassnerCoordinator
from .entity_base import HargassnerEntity

_LOGGER = logging.getLogger(__name__)

# (widget_prefix, action_key, entity_name, icon)
BUTTON_CONFIGS = [
    ("EVENTS", "confirm_all", "Confirm All Events", "mdi:check-all"),
    ("BOILER", "one_time_circulation", "One-Time Circulation", "mdi:pump"),
    ("BOILER", "force_charging", "Force Charging", "mdi:lightning-bolt"),
    ("HEATER", "start_ignition", "Start Ignition", "mdi:fire"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hargassner button entities."""
    coordinator: HargassnerCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[HargassnerButtonEntity] = []

    if not coordinator.data:
        return

    for widget_key, widget_data in coordinator.data.items():
        if not isinstance(widget_data, dict) or "widget_type" not in widget_data:
            continue

        widget_type = widget_data["widget_type"]
        widget_name = widget_data["widget_name"]
        actions = widget_data.get("actions", {})

        for prefix, action_key, entity_name, icon in BUTTON_CONFIGS:
            if not widget_type.startswith(prefix):
                continue
            action = actions.get(action_key)
            if not isinstance(action, dict) or not action.get("resource"):
                continue

            entities.append(
                HargassnerButtonEntity(
                    coordinator=coordinator,
                    widget_key=widget_key,
                    action_key=action_key,
                    widget_name=widget_name,
                    entity_name=entity_name,
                    icon=icon,
                )
            )

    async_add_entities(entities)


class HargassnerButtonEntity(HargassnerEntity, ButtonEntity):
    """Button entity for a Hargassner action."""

    def __init__(
        self,
        coordinator: HargassnerCoordinator,
        widget_key: str,
        action_key: str,
        widget_name: str,
        entity_name: str,
        icon: str,
    ) -> None:
        super().__init__(
            coordinator, widget_key, action_key,
            f"button_{widget_key}_{action_key}",
        )
        self._action_key = action_key
        self._attr_name = f"{widget_name} {entity_name}"
        self._attr_icon = icon

    async def async_press(self) -> None:
        """Execute the action."""
        widget = self._get_widget()
        if not widget:
            return
        action = widget.get("actions", {}).get(self._action_key)
        if isinstance(action, dict) and action.get("resource"):
            await self.coordinator.async_post_action(action["resource"])
