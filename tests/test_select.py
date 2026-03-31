"""Tests for select entity labels and behaviour."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.hargassner.select import (
    MODE_LABELS,
    POOL_LABELS,
    PROGRAM_LABELS,
    SELECT_CONFIGS,
    HargassnerSelectEntity,
)
from custom_components.hargassner.coordinator import HargassnerCoordinator


# ---------------------------------------------------------------------------
# Label dicts
# ---------------------------------------------------------------------------

def test_mode_labels_are_english():
    forbidden = set("àâäçéèêëîïôöùûüÿæœÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸÆŒßÄÖÜ")
    for key, label in MODE_LABELS.items():
        bad = [c for c in label if c in forbidden]
        assert not bad, f"Non-English chars in MODE_LABELS['{key}']: '{label}'"


def test_pool_labels_are_english():
    for key, label in POOL_LABELS.items():
        assert label in ("Off", "On", "Automatic"), f"Unexpected pool label: {label}"


def test_program_labels_are_english():
    forbidden = set("àâäçéèêëîïôöùûüÿæœÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸÆŒßÄÖÜ")
    for key, label in PROGRAM_LABELS.items():
        bad = [c for c in label if c in forbidden]
        assert not bad, f"Non-English chars in PROGRAM_LABELS['{key}']: '{label}'"


def test_select_configs_entity_names_are_english():
    forbidden = set("àâäçéèêëîïôöùûüÿæœÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸÆŒßÄÖÜ")
    for prefix, param_key, entity_name, labels in SELECT_CONFIGS:
        bad = [c for c in entity_name if c in forbidden]
        assert not bad, f"Non-English chars in entity name '{entity_name}'"


# ---------------------------------------------------------------------------
# HargassnerSelectEntity
# ---------------------------------------------------------------------------

def make_select_entity(param_value: str, options: list[str], labels: dict):
    coordinator = MagicMock(spec=HargassnerCoordinator)
    coordinator.installation_id = "42"
    coordinator.installation_name = "My Hargassner"
    coordinator.data = {
        "HEATING_CIRCUIT_1_Circuit1": {
            "widget_type": "HEATING_CIRCUIT",
            "widget_name": "Circuit 1",
            "values": {},
            "parameters": {
                "mode": {
                    "value": param_value,
                    "options": options,
                    "resource": "https://api/res/mode",
                }
            },
            "actions": {},
        }
    }

    entity = HargassnerSelectEntity(
        coordinator=coordinator,
        widget_key="HEATING_CIRCUIT_1_Circuit1",
        param_key="mode",
        widget_name="Circuit 1",
        entity_name="Operating Mode",
        labels=labels,
    )
    return entity


def test_select_options_translated():
    entity = make_select_entity(
        "MODE_AUTOMATIC",
        ["MODE_OFF", "MODE_AUTOMATIC", "MODE_HEATING"],
        MODE_LABELS,
    )
    opts = entity.options
    assert "Off" in opts
    assert "Automatic" in opts
    assert "Heating" in opts
    # Raw API values must NOT appear
    assert "MODE_OFF" not in opts
    assert "MODE_AUTOMATIC" not in opts


def test_select_current_option_translated():
    entity = make_select_entity("MODE_HEATING", ["MODE_OFF", "MODE_HEATING"], MODE_LABELS)
    assert entity.current_option == "Heating"


def test_select_current_option_fallback_when_unknown():
    entity = make_select_entity("MODE_UNKNOWN", ["MODE_UNKNOWN"], MODE_LABELS)
    # Unknown value: should return the raw key as fallback
    assert entity.current_option == "MODE_UNKNOWN"


@pytest.mark.asyncio
async def test_select_async_select_option_sends_api_value():
    entity = make_select_entity("MODE_AUTOMATIC", ["MODE_OFF", "MODE_AUTOMATIC"], MODE_LABELS)
    entity.coordinator.async_patch_value = AsyncMock(return_value=True)

    await entity.async_select_option("Off")
    entity.coordinator.async_patch_value.assert_called_once_with("https://api/res/mode", "MODE_OFF")


@pytest.mark.asyncio
async def test_select_async_select_option_no_resource():
    """If no resource URL, patch should not be called."""
    coordinator = MagicMock(spec=HargassnerCoordinator)
    coordinator.installation_id = "42"
    coordinator.installation_name = "My Hargassner"
    coordinator.data = {
        "HEATING_CIRCUIT_1_Circuit1": {
            "widget_type": "HEATING_CIRCUIT",
            "widget_name": "Circuit 1",
            "values": {},
            "parameters": {
                "mode": {
                    "value": "MODE_OFF",
                    "options": ["MODE_OFF"],
                    # No "resource" key
                }
            },
            "actions": {},
        }
    }
    coordinator.async_patch_value = AsyncMock()

    entity = HargassnerSelectEntity(
        coordinator=coordinator,
        widget_key="HEATING_CIRCUIT_1_Circuit1",
        param_key="mode",
        widget_name="Circuit 1",
        entity_name="Operating Mode",
        labels=MODE_LABELS,
    )
    await entity.async_select_option("Off")
    coordinator.async_patch_value.assert_not_called()
