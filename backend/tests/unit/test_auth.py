"""Tests for JWT authentication helpers (app.core.auth)."""

from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from fastapi import HTTPException

import app.core.auth as auth_module


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_jwks_cache():
    """Reset the module-level JWKS cache before and after each test."""
    auth_module._jwks_keys = None
    yield
    auth_module._jwks_keys = None


FAKE_KID = "test-key-id"
FAKE_KEYS = [{"kty": "EC", "kid": FAKE_KID, "crv": "P-256", "x": "x", "y": "y"}]
FAKE_USER_ID = "user-abc-123"


def _make_decode_token_patch(payload=None, side_effect=None):
    """Return a patch for auth_module._decode_token."""
    if side_effect is not None:
        return patch.object(auth_module, "_decode_token", side_effect=side_effect)
    return patch.object(
        auth_module, "_decode_token", return_value=payload or {"sub": FAKE_USER_ID}
    )


def _make_get_jwks_patch():
    """Return a patch for auth_module._get_jwks that returns fake keys."""
    return patch.object(
        auth_module, "_get_jwks", new_callable=AsyncMock, return_value=FAKE_KEYS
    )


# ---------------------------------------------------------------------------
# require_auth tests
# ---------------------------------------------------------------------------


class TestRequireAuth:
    """Tests for the require_auth dependency."""

    async def test_missing_bearer_prefix(self):
        """Header without 'Bearer ' prefix raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await auth_module.require_auth(authorization="Token abc123")
        assert exc_info.value.status_code == 401

    async def test_empty_token_after_bearer(self):
        """'Bearer ' with no actual token raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await auth_module.require_auth(authorization="Bearer ")
        assert exc_info.value.status_code == 401

    async def test_bearer_only_whitespace(self):
        """'Bearer ' followed by only whitespace raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await auth_module.require_auth(authorization="Bearer   ")
        assert exc_info.value.status_code == 401

    async def test_valid_token_returns_user_id(self):
        """A valid token returns the sub claim."""
        with _make_get_jwks_patch(), _make_decode_token_patch():
            user_id = await auth_module.require_auth(authorization="Bearer valid.jwt.token")
        assert user_id == FAKE_USER_ID

    async def test_expired_token_raises_401(self):
        """An expired token raises 401 with 'Token expired' detail."""
        # First call fails, refresh also fails with ExpiredSignatureError
        with _make_get_jwks_patch(), patch.object(
            auth_module,
            "_decode_token",
            side_effect=pyjwt.ExpiredSignatureError("expired"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_module.require_auth(authorization="Bearer expired.jwt.token")
            assert exc_info.value.status_code == 401
            assert "expired" in exc_info.value.detail.lower()

    async def test_invalid_token_after_retry_raises_401(self):
        """An invalid token that still fails after JWKS refresh raises 401."""
        with _make_get_jwks_patch(), patch.object(
            auth_module,
            "_decode_token",
            side_effect=pyjwt.InvalidTokenError("bad token"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_module.require_auth(authorization="Bearer bad.jwt.token")
            assert exc_info.value.status_code == 401
            assert "invalid" in exc_info.value.detail.lower()

    async def test_first_decode_fails_retry_succeeds(self):
        """If first decode fails but retry after JWKS refresh succeeds, returns user_id."""
        decode_mock = MagicMock(
            side_effect=[
                pyjwt.InvalidTokenError("stale keys"),
                {"sub": FAKE_USER_ID},
            ]
        )
        with _make_get_jwks_patch(), patch.object(
            auth_module, "_decode_token", decode_mock
        ):
            user_id = await auth_module.require_auth(authorization="Bearer rotated.jwt.token")
        assert user_id == FAKE_USER_ID
        assert decode_mock.call_count == 2


# ---------------------------------------------------------------------------
# verify_trip_owner tests
# ---------------------------------------------------------------------------


class TestVerifyTripOwner:
    """Tests for the verify_trip_owner helper."""

    async def test_trip_not_found_raises_404(self):
        """Returns 404 when the trip does not exist."""
        mock_db = MagicMock()
        mock_db.get_trip = AsyncMock(return_value=None)
        with patch("app.services.database.db", mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await auth_module.verify_trip_owner("trip-1", "user-1")
            assert exc_info.value.status_code == 404

    async def test_wrong_user_raises_403(self):
        """Returns 403 when the user does not own the trip."""
        trip = {"id": "trip-1", "user_id": "other-user"}
        mock_db = MagicMock()
        mock_db.get_trip = AsyncMock(return_value=trip)
        with patch("app.services.database.db", mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await auth_module.verify_trip_owner("trip-1", "user-1")
            assert exc_info.value.status_code == 403

    async def test_correct_owner_returns_trip(self):
        """Returns the trip dict when the user owns the trip."""
        trip = {"id": "trip-1", "user_id": "user-1", "name": "My Trip"}
        mock_db = MagicMock()
        mock_db.get_trip = AsyncMock(return_value=trip)
        with patch("app.services.database.db", mock_db):
            result = await auth_module.verify_trip_owner("trip-1", "user-1")
        assert result == trip


# ---------------------------------------------------------------------------
# _get_jwks caching tests
# ---------------------------------------------------------------------------


class TestGetJwksCaching:
    """Tests for the JWKS caching behaviour in _get_jwks."""

    async def test_first_call_fetches(self):
        """First call triggers a fetch."""
        with patch.object(
            auth_module, "_fetch_jwks", new_callable=AsyncMock, return_value=FAKE_KEYS
        ) as fetch_mock:
            keys = await auth_module._get_jwks()
        assert keys == FAKE_KEYS
        fetch_mock.assert_awaited_once()

    async def test_second_call_uses_cache(self):
        """Second call reuses cached keys without fetching again."""
        with patch.object(
            auth_module, "_fetch_jwks", new_callable=AsyncMock, return_value=FAKE_KEYS
        ) as fetch_mock:
            await auth_module._get_jwks()
            await auth_module._get_jwks()
        fetch_mock.assert_awaited_once()

    async def test_force_refresh_re_fetches(self):
        """force_refresh=True causes a new fetch even if cache is populated."""
        with patch.object(
            auth_module, "_fetch_jwks", new_callable=AsyncMock, return_value=FAKE_KEYS
        ) as fetch_mock:
            await auth_module._get_jwks()
            await auth_module._get_jwks(force_refresh=True)
        assert fetch_mock.await_count == 2
