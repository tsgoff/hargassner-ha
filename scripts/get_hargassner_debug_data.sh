#!/usr/bin/env bash

set -euo pipefail

API_BASE_URL="${API_BASE_URL:-https://web.hargassner.at/api}"
CLIENT_ID="${CLIENT_ID:-2}"
CLIENT_SECRET="${CLIENT_SECRET:-F6ye9z5oLaqW6IkGtihTzBpdFM7EAnYdc1Kwoydl}"
BRANDING="${BRANDING:-BRANDING_HARGASSNER}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

json_get() {
  local expr="$1"
  python3 -c 'import json, sys
data = json.load(sys.stdin)
expr = sys.argv[1]
value = data
for part in expr.split("."):
    if not part:
        continue
    if isinstance(value, list):
        value = value[int(part)]
    else:
        value = value.get(part)
    if value is None:
        break
if isinstance(value, (dict, list)):
    print(json.dumps(value))
elif value is None:
    sys.exit(1)
else:
    print(value)' "$expr"
}

require_command curl
require_command python3

EMAIL="${HARGASSNER_EMAIL:-}"
PASSWORD="${HARGASSNER_PASSWORD:-}"

if [[ -z "$EMAIL" ]]; then
  read -r -p "Hargassner email: " EMAIL
fi

if [[ -z "$PASSWORD" ]]; then
  read -r -s -p "Hargassner password: " PASSWORD
  echo
fi

login_payload="$(python3 -c 'import json, sys
print(json.dumps({
    "email": sys.argv[1],
    "password": sys.argv[2],
    "client_id": sys.argv[3],
    "client_secret": sys.argv[4],
}))' "$EMAIL" "$PASSWORD" "$CLIENT_ID" "$CLIENT_SECRET")"

login_response="$(curl -fsS \
  -X POST "${API_BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -H "Branding: ${BRANDING}" \
  -d "$login_payload")"

access_token="$(
  printf '%s' "$login_response" | json_get "data.access_token" 2>/dev/null || \
  printf '%s' "$login_response" | json_get "access_token" 2>/dev/null
)" || {
  echo "Login response did not contain an access token" >&2
  echo "Response was:" >&2
  printf '%s\n' "$login_response" >&2
  exit 1
}

user_response="$(curl -fsS \
  "${API_BASE_URL}/auth/user" \
  -H "Authorization: Bearer ${access_token}" \
  -H "Branding: ${BRANDING}")"

installations_response="$(curl -fsS \
  "${API_BASE_URL}/installations?with=devices.software%3Bdevices.gateway&sort=name" \
  -H "Authorization: Bearer ${access_token}" \
  -H "Branding: ${BRANDING}")"

echo
echo "Bearer token:"
echo "${access_token}"
echo
echo "Shell variables:"
printf 'TOKEN=%q\n' "${access_token}"
printf 'BRANDING=%q\n' "${BRANDING}"
echo
echo "Authenticated user:"
printf '%s' "$user_response" | python3 -c 'import json, sys
data = json.load(sys.stdin)
user = data.get("data", data)
for key in ("id", "email", "first_name", "last_name"):
    value = user.get(key)
    if value:
        print(f"{key}: {value}")'
echo
echo "Installations:"
printf '%s' "$installations_response" | python3 -c 'import json, sys
data = json.load(sys.stdin)
items = data.get("data", data)
if not isinstance(items, list):
    items = [items]
for item in items:
    installation_id = item.get("id")
    name = item.get("name", "")
    if installation_id is None:
        continue
    print(f"- {installation_id}\t{name}")'
echo
echo "Widget curl examples:"
printf '%s' "$installations_response" | python3 -c 'import json, sys
data = json.load(sys.stdin)
items = data.get("data", data)
if not isinstance(items, list):
    items = [items]
for item in items:
    installation_id = item.get("id")
    if installation_id is None:
        continue
    print(f"curl -s \"https://web.hargassner.at/api/installations/{installation_id}/widgets\" \\")
    print("  -H \"Authorization: Bearer ${TOKEN}\" \\")
    print("  -H \"Branding: ${BRANDING}\" | jq")
    print()'
