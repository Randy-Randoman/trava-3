"""Tests for API error status codes and generic error messages (Issue #47)."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException

FAKE_USER_ID = "user-00000000-0000-0000-0000-000000000000"
FAKE_TRIP_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
SECRET_ERROR = "connection to db-host:5432 failed: password=hunter2"


@pytest.fixture
async def client():
    from main import app
    from app.core.auth import require_auth

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    app.dependency_overrides[require_auth] = lambda: FAKE_USER_ID
    original = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.router.lifespan_context = original
    app.dependency_overrides.clear()


@pytest.mark.parametrize("status", [403, 404])
async def test_get_canvas_passes_through_ownership_error(client, status):
    with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock,
               side_effect=HTTPException(status_code=status, detail="nope")):
        resp = await client.get(f"/trips/{FAKE_TRIP_ID}/canvas")
    assert resp.status_code == status
    assert resp.json()["detail"] == "nope"


@pytest.mark.parametrize("status", [403, 404])
async def test_get_messages_passes_through_ownership_error(client, status):
    with patch("app.api.chat.verify_trip_owner", new_callable=AsyncMock,
               side_effect=HTTPException(status_code=status, detail="nope")):
        resp = await client.get(f"/chat/messages/{FAKE_TRIP_ID}")
    assert resp.status_code == status
    assert resp.json()["detail"] == "nope"


async def test_db_failure_returns_generic_500(client):
    with patch("app.api.trips.db") as mock_db:
        mock_db.get_user_trips_with_thumbnails = AsyncMock(side_effect=RuntimeError(SECRET_ERROR))
        resp = await client.get("/trips")
    assert resp.status_code == 500
    assert "hunter2" not in resp.json()["detail"]


async def test_get_messages_db_failure_returns_generic_500(client):
    with patch("app.api.chat.verify_trip_owner", new_callable=AsyncMock, return_value={}), \
         patch("app.api.chat.DatabaseService") as mock_cls:
        mock_cls.return_value.get_or_create_conversation = AsyncMock(side_effect=RuntimeError(SECRET_ERROR))
        resp = await client.get(f"/chat/messages/{FAKE_TRIP_ID}")
    assert resp.status_code == 500
    assert "hunter2" not in resp.json()["detail"]


async def test_invalid_trip_status_returns_422(client):
    with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock, return_value={}), \
         patch("app.api.trips.db") as mock_db:
        mock_db.update_trip = AsyncMock(return_value={"id": FAKE_TRIP_ID})
        resp = await client.patch(f"/trips/{FAKE_TRIP_ID}", json={"status": "bogus"})
    assert resp.status_code == 422
    mock_db.update_trip.assert_not_called()
