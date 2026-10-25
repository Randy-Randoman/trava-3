"""Tests for canvas save conflicts (Issue #56): stale tabs can't overwrite or delete items."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

FAKE_USER_ID = "user-00000000-0000-0000-0000-000000000000"
FAKE_TRIP_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

OLD_VERSION = "2026-10-25T10:00:00.000000+00:00"
NEW_VERSION = "2026-10-25T10:05:00.000000+00:00"
SAVED_VERSION = "2026-10-25T10:06:00.000000+00:00"

CARD = {"id": "card1", "type": "rectangle", "groupIds": ["g1"]}
STORED = {
    "trip_id": FAKE_TRIP_ID,
    "scene_elements": [CARD, {"id": "card2", "type": "rectangle", "groupIds": ["g2"]}],
    "scene_files": {},
    "scene_app_state": None,
    "last_modified": NEW_VERSION,
}
BOARD_ITEMS = [{"name": "Hotel", "excalidraw_group_id": "g1"}, {"name": "Museum", "excalidraw_group_id": "g2"}]


@pytest.fixture
def client():
    from contextlib import asynccontextmanager

    from main import app
    from app.core.auth import require_auth

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    app.dependency_overrides[require_auth] = lambda: FAKE_USER_ID
    original = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan
    yield httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    app.router.lifespan_context = original
    app.dependency_overrides.clear()


def _mock_db(mock_db, stored=STORED):
    mock_db.get_canvas_state = AsyncMock(return_value=stored)
    mock_db.update_canvas_state = AsyncMock(
        return_value={**(stored or {}), "scene_elements": [CARD], "last_modified": SAVED_VERSION}
    )
    mock_db.get_board_items = AsyncMock(return_value=BOARD_ITEMS)
    mock_db.update_board_items = AsyncMock()


async def _put(client, base_version):
    body = {"elements": [CARD], "files": {}}
    if base_version is not None:
        body["base_version"] = base_version
    return await client.put(f"/trips/{FAKE_TRIP_ID}/canvas", json=body)


@pytest.mark.asyncio
async def test_stale_base_version_returns_409_with_current_canvas_and_writes_nothing(client):
    with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock), \
         patch("app.api.trips.db") as mock_db:
        _mock_db(mock_db)
        resp = await _put(client, OLD_VERSION)

    assert resp.status_code == 409
    current = resp.json()["detail"]
    assert current["elements"] == STORED["scene_elements"]
    assert current["last_modified"] == NEW_VERSION
    mock_db.update_canvas_state.assert_not_awaited()
    mock_db.update_board_items.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_base_version_conflicts_when_canvas_exists(client):
    with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock), \
         patch("app.api.trips.db") as mock_db:
        _mock_db(mock_db)
        resp = await _put(client, None)

    assert resp.status_code == 409
    mock_db.update_canvas_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_current_base_version_saves_and_reconciles(client):
    with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock), \
         patch("app.api.trips.db") as mock_db:
        _mock_db(mock_db)
        resp = await _put(client, NEW_VERSION)

    assert resp.status_code == 200
    assert resp.json()["last_modified"] == SAVED_VERSION
    mock_db.update_canvas_state.assert_awaited_once()
    # card2 (g2) was deleted in the tab, so its board item goes away
    mock_db.update_board_items.assert_awaited_once_with(FAKE_TRIP_ID, [BOARD_ITEMS[0]])


@pytest.mark.asyncio
async def test_no_canvas_row_and_no_base_version_saves(client):
    with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock), \
         patch("app.api.trips.db") as mock_db:
        _mock_db(mock_db, stored=None)
        resp = await _put(client, None)

    assert resp.status_code == 200
    mock_db.update_canvas_state.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_welcome_template_still_returns_row_version(client):
    """An empty canvas row shows the welcome template but must still report its version."""
    empty = {**STORED, "scene_elements": []}
    with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock), \
         patch("app.api.trips.db") as mock_db:
        _mock_db(mock_db, stored=empty)
        resp = await client.get(f"/trips/{FAKE_TRIP_ID}/canvas")

    assert resp.status_code == 200
    assert resp.json()["elements"]  # welcome template
    assert resp.json()["last_modified"] == NEW_VERSION


@pytest.mark.asyncio
async def test_base_version_without_canvas_row_conflicts(client):
    with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock), \
         patch("app.api.trips.db") as mock_db:
        _mock_db(mock_db, stored=None)
        resp = await _put(client, OLD_VERSION)

    assert resp.status_code == 409
    assert resp.json()["detail"]["last_modified"] is None
    mock_db.update_canvas_state.assert_not_awaited()
