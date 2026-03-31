"""Climate entities for Hargassner heating circuits."""
from __future__ import annotations
import logging
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import HargassnerCoordinator
from .entity_base import HargassnerEntity

_LOGGER = logging.getLogger(__name__)

HEATING_CIRCUIT_WIDGETS = {"HEATING_CIRCUIT_BLOWER","HEATING_CIRCUIT_FLOOR","HEATING_CIRCUIT_RADIATOR","HEATING_CIRCUIT_EXTERNAL","HEATING_CIRCUIT_CONTROLLER","HEATING_CIRCUIT_POOL"}
OFF_MODE = "MODE_OFF"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: HargassnerCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    if not coordinator.data:
        return
    for widget_key, widget_data in coordinator.data.items():
        if not isinstance(widget_data, dict) or "widget_type" not in widget_data:
            continue
        if widget_data["widget_type"] not in HEATING_CIRCUIT_WIDGETS:
            continue
        if "room_temperature_heating" in widget_data.get("parameters", {}):
            entities.append(HargassnerClimateEntity(coordinator, widget_key, widget_data["widget_name"]))
    async_add_entities(entities)

class HargassnerClimateEntity(HargassnerEntity, ClimateEntity):
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_target_temperature_step = 0.5

    def __init__(self, coordinator, widget_key, widget_name):
        super().__init__(coordinator, widget_key, "room_temperature_heating", f"climate_{widget_key}")
        self._attr_name = widget_name

    def _get_param(self, key):
        widget = self._get_widget()
        if widget:
            p = widget.get("parameters", {}).get(key)
            if isinstance(p, dict):
                return p
        return None

    @property
    def min_temp(self):
        p = self._get_param("room_temperature_heating")
        return float(p.get("min", 14)) if p else 14.0

    @property
    def max_temp(self):
        p = self._get_param("room_temperature_heating")
        return float(p.get("max", 26)) if p else 26.0

    @property
    def current_temperature(self):
        widget = self._get_widget()
        if widget:
            val = widget.get("values", {}).get("room_temperature_current")
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
        return None

    @property
    def target_temperature(self):
        p = self._get_param("room_temperature_heating")
        if p:
            try:
                return float(p.get("value", 20))
            except (ValueError, TypeError):
                pass
        return None

    @property
    def hvac_mode(self):
        p = self._get_param("mode")
        if p and p.get("value") == OFF_MODE:
            return HVACMode.OFF
        return HVACMode.HEAT

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None: return
        p = self._get_param("room_temperature_heating")
        if p and p.get("resource"):
            await self.coordinator.async_patch_value(p["resource"], temp)

    async def async_set_hvac_mode(self, hvac_mode):
        p = self._get_param("mode")
        if p and p.get("resource"):
            value = OFF_MODE if hvac_mode == HVACMode.OFF else "MODE_AUTOMATIC"
            await self.coordinator.async_patch_value(p["resource"], value)
