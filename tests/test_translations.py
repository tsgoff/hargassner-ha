"""Tests for translation JSON files."""
from __future__ import annotations

import json
import pathlib
import pytest


TRANSLATIONS_DIR = pathlib.Path("custom_components/hargassner/translations")
STRINGS_PATH = pathlib.Path("custom_components/hargassner/strings.json")
EXPECTED_LANGUAGES = {"de", "en", "fr"}

# All entity keys that must be present in every translation file
EXPECTED_SENSOR_KEYS = {
    "heater_temp_current", "heater_temp_target", "smoke_temperature",
    "outdoor_temperature", "outdoor_temperature_average", "heater_state",
    "heater_program", "fuel_stock", "efficiency", "flow_temp_current",
    "flow_temp_target", "room_temp_current", "room_temp_target",
    "circuit_state", "pump_active", "online_state",
}
EXPECTED_NUMBER_KEYS = {
    "room_temperature_heating", "room_temperature_reduction",
    "deactivation_limit_heating", "deactivation_limit_reduction_day",
    "deactivation_limit_reduction_night", "steepness", "fuel_stock",
}
EXPECTED_SELECT_KEYS = {"mode", "pool_heating"}

CONFIG_FLOW_KEYS = {
    "config.step.user.title",
    "config.step.user.description",
    "config.step.user.data.email",
    "config.step.user.data.password",
    "config.step.installation.title",
    "config.step.installation.description",
    "config.step.installation.data.installation_id",
    "config.error.invalid_auth",
    "config.error.cannot_connect",
    "config.error.no_installations",
    "config.error.unknown",
    "config.abort.already_configured",
    "options.step.init.title",
    "options.step.init.data.scan_interval",
}


def get_leaf_keys(d: dict, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for k, v in d.items():
        full = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys |= get_leaf_keys(v, full)
        else:
            keys.add(full)
    return keys


def load_json(path: pathlib.Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# File presence
# ---------------------------------------------------------------------------

def test_expected_language_files_exist():
    existing = {p.stem for p in TRANSLATIONS_DIR.glob("*.json")}
    missing = EXPECTED_LANGUAGES - existing
    assert not missing, f"Missing translation files: {missing}"


def test_strings_json_exists():
    assert STRINGS_PATH.exists(), "strings.json is missing"


# ---------------------------------------------------------------------------
# Valid JSON
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lang_file", list(TRANSLATIONS_DIR.glob("*.json")))
def test_translation_file_is_valid_json(lang_file):
    data = load_json(lang_file)
    assert isinstance(data, dict), f"{lang_file.name} root must be a JSON object"


def test_strings_json_is_valid():
    data = load_json(STRINGS_PATH)
    assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# Config flow keys present in all languages
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lang_file", list(TRANSLATIONS_DIR.glob("*.json")))
def test_config_flow_keys_complete(lang_file):
    data = load_json(lang_file)
    leaf_keys = get_leaf_keys(data)
    missing = CONFIG_FLOW_KEYS - leaf_keys
    assert not missing, f"{lang_file.name} missing config flow keys: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Entity translation keys present in all languages
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lang_file", list(TRANSLATIONS_DIR.glob("*.json")))
def test_sensor_entity_keys_complete(lang_file):
    data = load_json(lang_file)
    sensor_section = data.get("entity", {}).get("sensor", {})
    missing = EXPECTED_SENSOR_KEYS - set(sensor_section.keys())
    assert not missing, f"{lang_file.name} missing sensor entity keys: {sorted(missing)}"


@pytest.mark.parametrize("lang_file", list(TRANSLATIONS_DIR.glob("*.json")))
def test_number_entity_keys_complete(lang_file):
    data = load_json(lang_file)
    number_section = data.get("entity", {}).get("number", {})
    missing = EXPECTED_NUMBER_KEYS - set(number_section.keys())
    assert not missing, f"{lang_file.name} missing number entity keys: {sorted(missing)}"


@pytest.mark.parametrize("lang_file", list(TRANSLATIONS_DIR.glob("*.json")))
def test_select_entity_keys_complete(lang_file):
    data = load_json(lang_file)
    select_section = data.get("entity", {}).get("select", {})
    missing = EXPECTED_SELECT_KEYS - set(select_section.keys())
    assert not missing, f"{lang_file.name} missing select entity keys: {sorted(missing)}"


# ---------------------------------------------------------------------------
# No empty translation strings
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lang_file", list(TRANSLATIONS_DIR.glob("*.json")))
def test_no_empty_translation_values(lang_file):
    data = load_json(lang_file)
    empty_keys = [k for k, v in get_leaf_keys_with_values(data).items() if v == ""]
    assert not empty_keys, f"{lang_file.name} has empty translation values: {empty_keys}"


def get_leaf_keys_with_values(d: dict, prefix: str = "") -> dict:
    result = {}
    for k, v in d.items():
        full = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result |= get_leaf_keys_with_values(v, full)
        else:
            result[full] = v
    return result


# ---------------------------------------------------------------------------
# strings.json matches en.json for config/options keys
# ---------------------------------------------------------------------------

def test_strings_json_matches_en_json():
    strings = load_json(STRINGS_PATH)
    en = load_json(TRANSLATIONS_DIR / "en.json")

    strings_keys = {k for k in get_leaf_keys(strings) if k.startswith(("config.", "options."))}
    en_keys = {k for k in get_leaf_keys(en) if k.startswith(("config.", "options."))}

    only_in_strings = strings_keys - en_keys
    only_in_en = en_keys - strings_keys

    assert not only_in_strings, f"Keys in strings.json but not en.json: {sorted(only_in_strings)}"
    assert not only_in_en, f"Keys in en.json but not strings.json: {sorted(only_in_en)}"


# ---------------------------------------------------------------------------
# French-specific: all names must differ from English
# ---------------------------------------------------------------------------

def test_french_entity_names_differ_from_english():
    """FR translations should not be identical to EN translations."""
    en = load_json(TRANSLATIONS_DIR / "en.json")
    fr = load_json(TRANSLATIONS_DIR / "fr.json")

    en_sensor = en.get("entity", {}).get("sensor", {})
    fr_sensor = fr.get("entity", {}).get("sensor", {})

    identical = [
        k for k in en_sensor
        if k in fr_sensor and en_sensor[k].get("name") == fr_sensor[k].get("name")
    ]
    assert not identical, f"FR and EN have identical sensor names for keys: {identical}"


# ---------------------------------------------------------------------------
# German-specific: all names must differ from English
# ---------------------------------------------------------------------------

def test_german_entity_names_differ_from_english():
    en = load_json(TRANSLATIONS_DIR / "en.json")
    de = load_json(TRANSLATIONS_DIR / "de.json")

    en_sensor = en.get("entity", {}).get("sensor", {})
    de_sensor = de.get("entity", {}).get("sensor", {})

    identical = [
        k for k in en_sensor
        if k in de_sensor and en_sensor[k].get("name") == de_sensor[k].get("name")
    ]
    assert not identical, f"DE and EN have identical sensor names for keys: {identical}"
