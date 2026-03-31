# Hargassner Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Custom integration for Hargassner pellet/biomass boilers via the Hargassner cloud API.

> ⚠️ **Unofficial integration** — reverse-engineered from the Android app v1.10.0. Requires an active Hargassner cloud account.

## Supported Devices

Tested with **Nano.2 12**. Should work with all Touch Tronic devices connected to the Hargassner cloud.

## Features

| Platform | Description |
|---|---|
| `sensor` | Boiler/flue/flow temperatures, fuel stock, outdoor temperature, state |
| `climate` | Thermostat per heating circuit |
| `number` | Day/night setpoints, heating curve slope, deactivation limits, fuel stock |
| `select` | Circuit mode (Auto/Heating/Setback/Off), bathroom heating |

## Installation via HACS

1. HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/lithium73fr/hargassner-ha` → **Integration**
3. Install "Hargassner" → Restart HA

## Manual Installation

Copy `custom_components/hargassner/` into `config/custom_components/` and restart.

## Configuration

Settings → Devices & Services → Add Integration → **Hargassner** → enter your app email and password.

## Contributing

If you have a different model and some entities are missing, open an issue with the output of:
```bash
curl "https://web.hargassner.at/api/installations/{id}/widgets" -H "Authorization: Bearer {token}" -H "Branding: BRANDING_HARGASSNER"
```

You can also use the helper script to log in, print the Bearer token, and list all installation IDs:
```bash
bash scripts/get_hargassner_debug_data.sh
```

Or pass credentials via environment variables:
```bash
HARGASSNER_EMAIL="info@example.de" HARGASSNER_PASSWORD="secret" bash scripts/get_hargassner_debug_data.sh
```

## Disclaimer

Not affiliated with or endorsed by Hargassner GmbH.
