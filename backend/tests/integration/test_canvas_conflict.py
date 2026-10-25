"""Stale tab vs. server-side board writes (Issue #56), backed by local Supabase."""

import json

import httpx
import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
async def client(supabase_env, monkeypatch):
    from main import app
    from app.core import auth
    from app.core.config import settings
    from app.services.database import db

    monkeypatch.setattr(settings, "SUPABASE_URL", supabase_env["API_URL"])
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_KEY", supabase_env["SERVICE_ROLE_KEY"])
    monkeypatch.setattr(db, "_client", None)
    monkeypatch.setattr(auth, "_jwks_keys", None)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_stale_tab_save_conflicts_and_keeps_server_added_items(client, user_a):
    from app.services.database import db
    from skills.board.tools import board_add_items

    headers = {"Authorization": f"Bearer {user_a['jwt']}"}
    resp = await client.post("/trips", json={"title": "Porto"}, headers=headers)
    assert resp.status_code == 200, resp.text
    trip_id = resp.json()["id"]

    # Tab loads the board
    loaded = (await client.get(f"/trips/{trip_id}/canvas", headers=headers)).json()

    # Server-side agent adds items after the tab loaded
    items = [{"name": "Hotel Porto", "type": "stay", "price": "100"}]
    await board_add_items.coroutine(items=json.dumps(items), trip_id=trip_id)
    added = await db.get_board_items(trip_id)
    assert added

    # Stale tab autosaves its old canvas
    resp = await client.put(
        f"/trips/{trip_id}/canvas",
        json={"elements": loaded["elements"], "files": {}, "base_version": loaded["last_modified"]},
        headers=headers,
    )
    assert resp.status_code == 409, resp.text
    current = resp.json()["detail"]
    assert current["last_modified"] != loaded["last_modified"]
    assert await db.get_board_items(trip_id) == added

    # After reloading, the tab's save goes through and keeps the items
    resp = await client.put(
        f"/trips/{trip_id}/canvas",
        json={"elements": current["elements"], "files": {}, "base_version": current["last_modified"]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert await db.get_board_items(trip_id) == added
