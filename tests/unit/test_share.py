"""Tests for trip sharing endpoints (Issue #20)."""

import sys
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

# backend/main.py uses `from app.services...` imports, so we need
# the backend directory on sys.path for those to resolve.
_backend_dir = str(Path(__file__).resolve().parents[2] / "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

FAKE_USER_ID = "user-00000000-0000-0000-0000-000000000000"


@pytest.fixture
def app():
    """Create a FastAPI app instance with lifespan disabled and auth bypassed."""
    from contextlib import asynccontextmanager

    from main import app
    from app.core.auth import require_auth

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    # Override require_auth to return a fake user_id without JWT validation
    app.dependency_overrides[require_auth] = lambda: FAKE_USER_ID

    original = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan
    yield app
    app.router.lifespan_context = original
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Async HTTP client bound to the FastAPI app."""
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


FAKE_TRIP_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
FAKE_SHARE_TOKEN = "11111111-2222-3333-4444-555555555555"


class TestShareTrip:
    """Tests for POST /trips/{trip_id}/share"""

    @pytest.mark.asyncio
    async def test_share_trip_generates_token(self, client):
        """New share generates a uuid4 token and persists it."""
        trip_data = {"id": FAKE_TRIP_ID, "title": "Rome Trip", "share_token": None, "user_id": FAKE_USER_ID}

        with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock, return_value=trip_data), \
             patch("app.api.trips.db") as mock_db:
            mock_db.set_share_token = AsyncMock(return_value={})

            resp = await client.post(f"/trips/{FAKE_TRIP_ID}/share")

        assert resp.status_code == 200
        body = resp.json()
        assert "share_token" in body
        # Token should be a valid uuid4 string
        token = body["share_token"]
        parsed = uuid.UUID(token, version=4)
        assert str(parsed) == token

        # set_share_token should have been called with the generated token
        mock_db.set_share_token.assert_awaited_once_with(FAKE_TRIP_ID, token)

    @pytest.mark.asyncio
    async def test_share_trip_reuses_existing_token(self, client):
        """If the trip already has a share_token, return the same one."""
        trip_data = {
            "id": FAKE_TRIP_ID,
            "title": "Rome Trip",
            "share_token": FAKE_SHARE_TOKEN,
            "user_id": FAKE_USER_ID,
        }

        with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock, return_value=trip_data), \
             patch("app.api.trips.db") as mock_db:
            mock_db.set_share_token = AsyncMock(return_value={})

            resp = await client.post(f"/trips/{FAKE_TRIP_ID}/share")

        assert resp.status_code == 200
        assert resp.json()["share_token"] == FAKE_SHARE_TOKEN
        mock_db.set_share_token.assert_awaited_once_with(FAKE_TRIP_ID, FAKE_SHARE_TOKEN)

    @pytest.mark.asyncio
    async def test_share_trip_not_found(self, client):
        """POST /trips/{bad_id}/share returns 404 when trip doesn't exist."""
        from fastapi import HTTPException
        with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock,
                    side_effect=HTTPException(status_code=404, detail="Trip not found")):

            resp = await client.post("/trips/nonexistent-id/share")

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Trip not found"


class TestGetPublicBoard:
    """Tests for GET /trips/public/{share_token}"""

    @pytest.mark.asyncio
    async def test_get_public_board_success(self, client):
        """Valid share token returns trip title and canvas data."""
        trip_data = {"id": FAKE_TRIP_ID, "title": "Rome Trip"}
        canvas_data = {
            "scene_elements": [{"type": "rectangle", "id": "el1"}],
            "scene_files": {"file1": {"dataURL": "data:image/png;base64,abc"}},
        }

        with patch("app.api.trips.db") as mock_db:
            mock_db.get_trip_by_share_token = AsyncMock(return_value=trip_data)
            mock_db.get_canvas_state = AsyncMock(return_value=canvas_data)

            resp = await client.get(f"/trips/public/{FAKE_SHARE_TOKEN}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["trip_id"] == FAKE_TRIP_ID
        assert body["title"] == "Rome Trip"
        assert len(body["elements"]) == 1
        assert body["elements"][0]["id"] == "el1"
        assert "file1" in body["files"]

    @pytest.mark.asyncio
    async def test_get_public_board_empty_canvas(self, client):
        """Valid token but empty canvas returns empty elements/files."""
        trip_data = {"id": FAKE_TRIP_ID, "title": "Empty Trip"}

        with patch("app.api.trips.db") as mock_db:
            mock_db.get_trip_by_share_token = AsyncMock(return_value=trip_data)
            mock_db.get_canvas_state = AsyncMock(return_value=None)

            resp = await client.get(f"/trips/public/{FAKE_SHARE_TOKEN}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["elements"] == []
        assert body["files"] == {}

    @pytest.mark.asyncio
    async def test_get_public_board_not_found(self, client):
        """Invalid share token returns 404."""
        with patch("app.api.trips.db") as mock_db:
            mock_db.get_trip_by_share_token = AsyncMock(return_value=None)

            resp = await client.get("/trips/public/bad-token-value")

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Board not found"
