"""Base entity for Hargassner."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HargassnerCoordinator


class HargassnerEntity(CoordinatorEntity[HargassnerCoordinator]):
    """Base class for Hargassner entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HargassnerCoordinator,
        widget_key: str,
        param_key: str,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._widget_key = widget_key
        self._param_key = param_key
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.installation_id}_{unique_suffix}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.installation_id)},
            name=coordinator.installation_name,
            manufacturer="Hargassner",
            model="Touch Tronic",
        )

    def _get_widget(self) -> dict | None:
        if self.coordinator.data:
            return self.coordinator.data.get(self._widget_key)
        return None

    def _get_value(self) -> object | None:
        widget = self._get_widget()
        if widget:
            return widget.get("values", {}).get(self._param_key)
        return None

    def _get_parameter(self) -> dict | None:
        widget = self._get_widget()
        if widget:
            return widget.get("parameters", {}).get(self._param_key)
        return None

    def _get_resource(self) -> str | None:
        param = self._get_parameter()
        if param and isinstance(param, dict):
            return param.get("resource")
        return None
