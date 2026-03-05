"""Hargassner API client."""
from __future__ import annotations

import logging
import time
from typing import Any

import aiohttp

from .const import (
    API_BASE_URL,
    API_LOGIN,
    API_LOGOUT,
    API_REFRESH,
    API_INSTALLATIONS,
    API_WIDGETS,
    APP_BRANDING,
    CLIENT_ID,
    CLIENT_SECRET,
)

_LOGGER = logging.getLogger(__name__)


class HargassnerApiError(Exception):
    """Generic API error."""


class HargassnerAuthError(HargassnerApiError):
    """Authentication error."""


class HargassnerApi:
    """Hargassner cloud API client."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._base_url = API_BASE_URL
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: float = 0.0
        self._email: str = ""
        self._password: str = ""

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    @property
    def token_needs_refresh(self) -> bool:
        """True if token expires in less than 5 minutes."""
        return time.time() > (self._token_expires_at - 300)

    def _headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Branding": APP_BRANDING,
        }
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        params: dict | None = None,
        _retry_auth: bool = True,
    ) -> Any:
        url = path if path.startswith("http") else self._base_url + path
        _LOGGER.debug("%s %s", method, url)
        try:
            async with self._session.request(
                method, url,
                headers=self._headers(),
                json=json,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                _LOGGER.debug("Response: %s", resp.status)

                # Token expired — try to refresh once then retry
                if resp.status == 401 and _retry_auth:
                    _LOGGER.info("Token expired, attempting refresh...")
                    await self._refresh_or_relogin()
                    return await self._request(method, path, json=json, params=params, _retry_auth=False)

                if resp.status == 401:
                    raise HargassnerAuthError("Unauthorized after token refresh")
                if resp.status == 404:
                    raise HargassnerApiError(f"Not found: {path}")
                if resp.status >= 400:
                    text = await resp.text()
                    raise HargassnerApiError(f"API error {resp.status}: {text}")
                if resp.status == 204 or resp.content_length == 0:
                    return {}
                content_type = resp.content_type or ""
                if "json" in content_type:
                    return await resp.json(content_type=None)
                return await resp.text()
        except aiohttp.ClientError as err:
            raise HargassnerApiError(f"Network error: {err}") from err

    async def _refresh_or_relogin(self) -> None:
        """Try refresh token, fall back to full re-login."""
        if self._refresh_token:
            try:
                await self._do_refresh()
                return
            except Exception as err:
                _LOGGER.warning("Token refresh failed (%s), re-logging in...", err)
        # Fall back to full login
        if self._email and self._password:
            await self.login(self._email, self._password)
        else:
            raise HargassnerAuthError("Cannot re-authenticate: no credentials stored")

    async def _do_refresh(self) -> None:
        """Use refresh_token to get a new access_token."""
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        data = await self._request("POST", API_REFRESH, json=payload, _retry_auth=False)
        self._store_tokens(data)

    def _store_tokens(self, data: dict) -> None:
        inner = data.get("data", data) if isinstance(data, dict) else data
        self._access_token = inner.get("access_token")
        self._refresh_token = inner.get("refresh_token", self._refresh_token)
        expires_in = inner.get("expires_in", 3600)
        self._token_expires_at = time.time() + expires_in
        if not self._access_token:
            raise HargassnerAuthError("No access_token in response")
        _LOGGER.debug("Tokens stored, expire in %ss", expires_in)

    async def login(self, email: str, password: str) -> dict:
        """Authenticate and store tokens."""
        self._email = email
        self._password = password
        payload = {
            "email": email,
            "password": password,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        data = await self._request("POST", API_LOGIN, json=payload, _retry_auth=False)
        if not isinstance(data, dict):
            raise HargassnerAuthError(f"Unexpected login response: {type(data)}")
        self._store_tokens(data)
        _LOGGER.debug("Login successful")
        return data

    async def logout(self) -> None:
        """Logout and clear tokens."""
        try:
            await self._request("POST", API_LOGOUT, json={}, _retry_auth=False)
        except HargassnerApiError:
            pass
        self._access_token = None
        self._refresh_token = None

    async def ensure_token_valid(self) -> None:
        """Proactively refresh token before it expires."""
        if self.token_needs_refresh:
            _LOGGER.debug("Proactively refreshing token...")
            await self._refresh_or_relogin()

    async def get_installations(self) -> list[dict]:
        """Get list of boiler installations."""
        path = "/installations?with=devices.software%3Bdevices.gateway&sort=name"
        data = await self._request("GET", path)
        if isinstance(data, dict):
            result = data.get("data", [])
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                return [result]
        if isinstance(data, list):
            return data
        return []

    async def get_widgets(self, installation_id: str) -> tuple[list[dict], dict]:
        """Get widget data. Returns (widgets_list, meta_dict)."""
        path = f"{API_INSTALLATIONS}/{installation_id}{API_WIDGETS}"
        data = await self._request("GET", path)
        if isinstance(data, dict):
            widgets = data.get("data", [])
            meta = data.get("meta", {})
            return (widgets if isinstance(widgets, list) else []), meta
        if isinstance(data, list):
            return data, {}
        return [], {}

    async def get_events(self, installation_id: str) -> list[dict]:
        """Get installation events/alarms."""
        path = f"{API_INSTALLATIONS}/{installation_id}/events"
        data = await self._request("GET", path)
        if isinstance(data, dict):
            return data.get("data", [])
        return data if isinstance(data, list) else []

    async def patch_value(self, resource_url: str, value: Any) -> dict:
        """Set a parameter value."""
        return await self._request("PATCH", resource_url, json={"value": value})

    async def post_action(self, resource_url: str) -> dict:
        """Trigger an action."""
        return await self._request("POST", resource_url, json=None)
