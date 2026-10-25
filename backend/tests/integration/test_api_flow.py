"""Happy path through the FastAPI app, backed by local Supabase."""

import httpx
import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
async def client(supabase_env, monkeypatch):
    from main import app
    from app.core import auth
    from app.core.config import settings
    from app.services.database import db

    # Make sure the app talks to local Supabase even if it was imported earlier with other settings.
    monkeypatch.setattr(settings, "SUPABASE_URL", supabase_env["API_URL"])
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_KEY", supabase_env["SERVICE_ROLE_KEY"])
    monkeypatch.setattr(db, "_client", None)
    monkeypatch.setattr(auth, "_jwks_keys", None)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_create_save_share_and_view_public_board(client, user_a):
    headers = {"Authorization": f"Bearer {user_a['jwt']}"}

    resp = await client.post("/trips", json={"title": "Lisbon"}, headers=headers)
    assert resp.status_code == 200, resp.text
    trip_id = resp.json()["id"]

    elements = [{"id": "el1", "type": "rectangle"}]
    resp = await client.put(f"/trips/{trip_id}/canvas", json={"elements": elements, "files": {}}, headers=headers)
    assert resp.status_code == 200, resp.text

    resp = await client.get(f"/trips/{trip_id}/canvas", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["elements"] == elements

    resp = await client.post(f"/trips/{trip_id}/share", headers=headers)
    assert resp.status_code == 200, resp.text
    token = resp.json()["share_token"]

    resp = await client.get(f"/trips/public/{token}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["trip_id"] == trip_id
    assert body["title"] == "Lisbon"
    assert body["elements"] == elements


async def test_other_user_cannot_save_canvas(client, user_b, trip_a):
    resp = await client.put(
        f"/trips/{trip_a['id']}/canvas",
        json={"elements": [], "files": {}},
        headers={"Authorization": f"Bearer {user_b['jwt']}"},
    )
    assert resp.status_code == 403


async def test_other_user_cannot_load_canvas(client, user_b, trip_a):
    resp = await client.get(f"/trips/{trip_a['id']}/canvas", headers={"Authorization": f"Bearer {user_b['jwt']}"})
    assert resp.status_code == 403
