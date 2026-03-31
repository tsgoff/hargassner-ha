"""Select entities for Hargassner option parameters."""
from __future__ import annotations

import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import HargassnerCoordinator
from .entity_base import HargassnerEntity

_LOGGER = logging.getLogger(__name__)

# Friendly labels for mode values
MODE_LABELS = {
    "MODE_OFF": "Off",
    "MODE_AUTOMATIC": "Automatic",
    "MODE_HEATING": "Heating",
    "MODE_REDUCTION": "Setback",
    "MODE_BRIDGE_REDUCTION": "Override Setback",
    "MODE_BRIDGE_HEATING": "Override Heating",
}

POOL_LABELS = {
    "POOL_HEATING_OFF": "Off",
    "POOL_HEATING_ON": "On",
    "POOL_HEATING_AUTOMATIC": "Automatic",
}

# (widget_prefix, param_key, entity_name, labels_dict)
SELECT_CONFIGS = [
    ("HEATING_CIRCUIT", "mode", "Operating Mode", MODE_LABELS),
    ("HEATING_CIRCUIT", "pool_heating", "Pool Heating", POOL_LABELS),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hargassner select entities."""
    coordinator: HargassnerCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[HargassnerSelectEntity] = []

    if not coordinator.data:
        return

    for widget_key, widget_data in coordinator.data.items():
        if not isinstance(widget_data, dict) or "widget_type" not in widget_data:
            continue

        widget_type = widget_data["widget_type"]
        widget_name = widget_data["widget_name"]
        parameters = widget_data.get("parameters", {})

        for prefix, param_key, entity_name, labels in SELECT_CONFIGS:
            if not widget_type.startswith(prefix):
                continue
            param = parameters.get(param_key)
            if not isinstance(param, dict):
                continue
            if not param.get("resource") or not param.get("options"):
                continue

            entities.append(
                HargassnerSelectEntity(
                    coordinator=coordinator,
                    widget_key=widget_key,
                    param_key=param_key,
                    widget_name=widget_name,
                    entity_name=entity_name,
                    labels=labels,
                )
            )

    async_add_entities(entities)


class HargassnerSelectEntity(HargassnerEntity, SelectEntity):
    """Select entity for a Hargassner option parameter."""

    def __init__(
        self,
        coordinator: HargassnerCoordinator,
        widget_key: str,
        param_key: str,
        widget_name: str,
        entity_name: str,
        labels: dict[str, str],
    ) -> None:
        super().__init__(coordinator, widget_key, param_key, f"select_{widget_key}_{param_key}")
        self._attr_name = f"{widget_name} {entity_name}"
        self._labels = labels

    @property
    def options(self) -> list[str]:
        param = self._get_parameter()
        if param:
            opts = param.get("options", [])
            return [self._labels.get(o, o) for o in opts]
        return []

    @property
    def current_option(self) -> str | None:
        param = self._get_parameter()
        if param:
            val = param.get("value")
            return self._labels.get(val, val)
        return None

    async def async_select_option(self, option: str) -> None:
        # Reverse lookup: friendly label -> API value
        reverse = {v: k for k, v in self._labels.items()}
        api_value = reverse.get(option, option)
        resource = self._get_resource()
        if resource:
            await self.coordinator.async_patch_value(resource, api_value)
