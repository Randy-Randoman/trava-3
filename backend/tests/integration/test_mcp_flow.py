"""The remote MCP server (#55) over Streamable HTTP, backed by local Supabase."""

import json

import httpx
import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

pytestmark = pytest.mark.integration


@pytest.fixture
def app(supabase_env, monkeypatch):
    import main
    from app.core import auth
    from app.core.config import settings
    from app.services.database import db

    # Make sure the app talks to local Supabase even if it was imported earlier with other settings.
    monkeypatch.setattr(settings, "SUPABASE_URL", supabase_env["API_URL"])
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_KEY", supabase_env["SERVICE_ROLE_KEY"])
    monkeypatch.setattr(db, "_client", None)
    monkeypatch.setattr(auth, "_jwks_keys", None)

    async def noop():
        pass

    monkeypatch.setattr(main, "warmup_playwright", noop)
    monkeypatch.setattr(main, "shutdown_playwright", noop)
    return main.app


async def test_agent_creates_a_trip_and_fills_its_board(app, user_a, service, monkeypatch):
    from app.core import auth

    async def as_user_a(authorization: str) -> dict:
        return {"user_id": user_a["id"], "client_id": "test-client"}

    monkeypatch.setattr(auth, "require_agent", as_user_a)
    hotel = {"name": "Casa do Alfama", "type": "stay", "price": "€120", "bookingUrl": "https://booking.com/x"}

    async with app.router.lifespan_context(app):
        http = httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), headers={"Authorization": "Bearer agent-token"}
        )
        async with http, Client(streamable_http_client("http://localhost:8000/mcp", http_client=http)) as client:
            tools = await client.list_tools()
            assert "board_add_items" in {t.name for t in tools.tools}

            created = await client.call_tool("create_trip", {"name": "Lisbon via MCP"})
            assert not created.is_error, created
            trip_id = json.loads(created.content[0].text)["id"]

            try:
                added = await client.call_tool("board_add_items", {"trip_id": trip_id, "items": json.dumps([hotel])})
                assert not added.is_error, added

                board = await client.call_tool("board_read", {"trip_id": trip_id})
                assert "Casa do Alfama" in board.content[0].text

                trip = service.table("trips").select("board_items").eq("id", trip_id).single().execute().data
                [item] = trip["board_items"]
                assert item["name"] == "Casa do Alfama"
                canvas = service.table("canvas_states").select("scene_elements").eq("trip_id", trip_id).single().execute()
                card = [el for el in canvas.data["scene_elements"] if item["excalidraw_group_id"] in (el.get("groupIds") or [])]
                assert card, "the item's card is on the canvas"
            finally:
                service.table("trips").delete().eq("id", trip_id).execute()


async def test_no_token_is_401_with_resource_metadata(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost:8000") as c:
        resp = await c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
    assert resp.status_code == 401
    assert "resource_metadata=" in resp.headers["www-authenticate"]
