"""Constants for the Hargassner integration."""

DOMAIN = "hargassner"

# API
API_BASE_URL = "https://web.hargassner.at/api"
API_LOGIN = "/auth/login"
API_LOGOUT = "/auth/logout"
API_REFRESH = "/auth/refresh"
API_INSTALLATIONS = "/installations"
API_WIDGETS = "/widgets"

# OAuth (from app JS bundle)
CLIENT_ID = 2
CLIENT_SECRET = "F6ye9z5oLaqW6IkGtihTzBpdFM7EAnYdc1Kwoydl"
APP_BRANDING = "BRANDING_HARGASSNER"

# Config keys
CONF_INSTALLATION_ID = "installation_id"
CONF_INSTALLATION_NAME = "installation_name"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 600

# Services
SERVICE_START_IGNITION = "start_ignition"
