"""Switch entities for Hargassner boolean parameters."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import HargassnerCoordinator
from .entity_base import HargassnerEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class HargassnerSwitchDescription(SwitchEntityDescription):
    """Describes a Hargassner switch."""
    widget_prefix: str = ""


SWITCH_DESCRIPTIONS: list[HargassnerSwitchDescription] = [
    HargassnerSwitchDescription(
        key="weather_mode",
        name="Weather Compensation Mode",
        widget_prefix="HEATING_CIRCUIT",
        icon="mdi:weather-partly-cloudy",
    ),
    HargassnerSwitchDescription(
        key="holiday_mode",
        name="Holiday Mode",
        widget_prefix="HEATING_CIRCUIT",
        icon="mdi:palm-tree",
    ),
    HargassnerSwitchDescription(
        key="pool_heating",
        name="Pool Heating",
        widget_prefix="HEATING_CIRCUIT_POOL",
        icon="mdi:pool",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hargassner switch entities."""
    coordinator: HargassnerCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[HargassnerSwitchEntity] = []

    if not coordinator.data:
        return

    for widget_key, widget_data in coordinator.data.items():
        if not isinstance(widget_data, dict) or "widget_type" not in widget_data:
            continue

        widget_type = widget_data["widget_type"]
        widget_name = widget_data["widget_name"]
        parameters = widget_data.get("parameters", {})

        for description in SWITCH_DESCRIPTIONS:
            if not widget_type.startswith(description.widget_prefix):
                continue
            param = parameters.get(description.key)
            if not param or not isinstance(param, dict):
                continue
            if not param.get("resource"):
                continue

            entities.append(
                HargassnerSwitchEntity(
                    coordinator=coordinator,
                    widget_key=widget_key,
                    param_key=description.key,
                    widget_name=widget_name,
                    description=description,
                )
            )

    async_add_entities(entities)


class HargassnerSwitchEntity(HargassnerEntity, SwitchEntity):
    """Switch entity for a boolean Hargassner parameter."""

    entity_description: HargassnerSwitchDescription

    def __init__(
        self,
        coordinator: HargassnerCoordinator,
        widget_key: str,
        param_key: str,
        widget_name: str,
        description: HargassnerSwitchDescription,
    ) -> None:
        super().__init__(
            coordinator,
            widget_key,
            param_key,
            f"switch_{widget_key}_{description.key}",
        )
        self.entity_description = description
        self._attr_name = f"{widget_name} {description.name}"

    @property
    def is_on(self) -> bool | None:
        val = self._get_value()
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        if isinstance(val, str):
            return val.lower() in ("true", "1", "on", "yes", "active")
        return None

    async def async_turn_on(self, **kwargs) -> None:
        resource = self._get_resource()
        if resource:
            await self.coordinator.async_patch_value(resource, True)

    async def async_turn_off(self, **kwargs) -> None:
        resource = self._get_resource()
        if resource:
            await self.coordinator.async_patch_value(resource, False)
