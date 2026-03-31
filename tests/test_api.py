"""Tests for the Hargassner API client."""
from __future__ import annotations

import time
import pytest
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from custom_components.hargassner.api import (
    HargassnerApi,
    HargassnerApiError,
    HargassnerAuthError,
)
from tests.conftest import MOCK_LOGIN_RESPONSE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_response(status: int, json_data=None, text_data: str = "", content_type: str = "application/json"):
    """Create a mock aiohttp response."""
    resp = MagicMock()
    resp.status = status
    resp.content_type = content_type
    resp.content_length = 1 if json_data or text_data else 0
    resp.json = AsyncMock(return_value=json_data)
    resp.text = AsyncMock(return_value=text_data)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success():
    session = MagicMock()
    session.request = MagicMock(return_value=make_mock_response(200, json_data=MOCK_LOGIN_RESPONSE))
    api = HargassnerApi(session)
    result = await api.login("test@example.com", "secret")
    assert api.is_authenticated
    assert api._access_token == "test-access-token"
    assert api._refresh_token == "test-refresh-token"


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    session = MagicMock()
    session.request = MagicMock(return_value=make_mock_response(401, text_data="Unauthorized"))
    api = HargassnerApi(session)
    with pytest.raises(HargassnerAuthError):
        await api.login("bad@example.com", "wrong")


@pytest.mark.asyncio
async def test_login_network_error():
    session = MagicMock()
    session.request = MagicMock(side_effect=aiohttp.ClientError("connection failed"))
    api = HargassnerApi(session)
    with pytest.raises(HargassnerApiError, match="Network error"):
        await api.login("test@example.com", "secret")


@pytest.mark.asyncio
async def test_login_unexpected_response_type():
    """Non-dict response from login endpoint raises HargassnerAuthError."""
    session = MagicMock()
    session.request = MagicMock(return_value=make_mock_response(200, json_data=["unexpected", "list"]))
    api = HargassnerApi(session)
    with pytest.raises(HargassnerAuthError, match="Unexpected login response"):
        await api.login("test@example.com", "secret")


# ---------------------------------------------------------------------------
# token management
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_token_needs_refresh_when_expired():
    session = MagicMock()
    api = HargassnerApi(session)
    api._access_token = "old-token"
    api._token_expires_at = time.time() - 10  # already expired
    assert api.token_needs_refresh is True


@pytest.mark.asyncio
async def test_token_does_not_need_refresh_when_fresh():
    session = MagicMock()
    api = HargassnerApi(session)
    api._access_token = "fresh-token"
    api._token_expires_at = time.time() + 7200  # 2 hours from now
    assert api.token_needs_refresh is False


@pytest.mark.asyncio
async def test_ensure_token_valid_triggers_refresh():
    session = MagicMock()
    api = HargassnerApi(session)
    api._access_token = "old-token"
    api._token_expires_at = time.time() - 10  # expired
    api._email = "test@example.com"
    api._password = "secret"

    # Mock re-login
    session.request = MagicMock(return_value=make_mock_response(200, json_data=MOCK_LOGIN_RESPONSE))
    await api.ensure_token_valid()
    assert api._access_token == "test-access-token"


@pytest.mark.asyncio
async def test_ensure_token_valid_skips_when_fresh():
    session = MagicMock()
    api = HargassnerApi(session)
    api._access_token = "fresh-token"
    api._token_expires_at = time.time() + 7200
    session.request = MagicMock()  # should NOT be called

    await api.ensure_token_valid()
    session.request.assert_not_called()


# ---------------------------------------------------------------------------
# get_installations
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_installations_returns_list():
    session = MagicMock()
    payload = {"data": [{"id": "42", "name": "My Hargassner"}]}
    session.request = MagicMock(return_value=make_mock_response(200, json_data=payload))
    api = HargassnerApi(session)
    api._access_token = "token"
    api._token_expires_at = time.time() + 3600

    result = await api.get_installations()
    assert isinstance(result, list)
    assert result[0]["id"] == "42"


@pytest.mark.asyncio
async def test_get_installations_returns_empty_on_bad_response():
    session = MagicMock()
    session.request = MagicMock(return_value=make_mock_response(200, json_data="not-a-dict", content_type="application/json"))
    api = HargassnerApi(session)
    api._access_token = "token"
    api._token_expires_at = time.time() + 3600

    result = await api.get_installations()
    assert result == []


# ---------------------------------------------------------------------------
# get_widgets
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_widgets_returns_tuple():
    session = MagicMock()
    widgets_data = [{"widget": "HEATER", "number": "1", "values": {}, "parameters": {}, "actions": {}}]
    payload = {"data": widgets_data, "meta": {"online_state": True}}
    session.request = MagicMock(return_value=make_mock_response(200, json_data=payload))

    api = HargassnerApi(session)
    api._access_token = "token"
    api._token_expires_at = time.time() + 3600

    widgets, meta = await api.get_widgets("42")
    assert isinstance(widgets, list)
    assert len(widgets) == 1
    assert meta == {"online_state": True}


@pytest.mark.asyncio
async def test_get_widgets_404_raises():
    session = MagicMock()
    session.request = MagicMock(return_value=make_mock_response(404, text_data="Not Found"))
    api = HargassnerApi(session)
    api._access_token = "token"
    api._token_expires_at = time.time() + 3600

    with pytest.raises(HargassnerApiError):
        await api.get_widgets("999")


# ---------------------------------------------------------------------------
# patch_value / post_action
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_patch_value_sends_correct_payload():
    session = MagicMock()
    session.request = MagicMock(return_value=make_mock_response(200, json_data={}))
    api = HargassnerApi(session)
    api._access_token = "token"
    api._token_expires_at = time.time() + 3600

    await api.patch_value("https://web.hargassner.at/api/resource/1", 22.5)
    call_kwargs = session.request.call_args
    assert call_kwargs.kwargs["json"] == {"value": 22.5}


@pytest.mark.asyncio
async def test_post_action_sends_post():
    session = MagicMock()
    session.request = MagicMock(return_value=make_mock_response(200, json_data={}))
    api = HargassnerApi(session)
    api._access_token = "token"
    api._token_expires_at = time.time() + 3600

    await api.post_action("https://web.hargassner.at/api/resource/ignition")
    call_args = session.request.call_args
    assert call_args.args[0] == "POST"


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_logout_clears_tokens():
    session = MagicMock()
    session.request = MagicMock(return_value=make_mock_response(204))
    api = HargassnerApi(session)
    api._access_token = "token"
    api._refresh_token = "refresh"

    await api.logout()
    assert api._access_token is None
    assert api._refresh_token is None


@pytest.mark.asyncio
async def test_logout_ignores_api_error():
    """Logout should succeed silently even if the API call fails."""
    session = MagicMock()
    session.request = MagicMock(return_value=make_mock_response(500, text_data="Server Error"))
    api = HargassnerApi(session)
    api._access_token = "token"

    # Should not raise
    await api.logout()
    assert api._access_token is None
