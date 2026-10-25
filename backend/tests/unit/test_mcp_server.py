"""Tests for the remote MCP server at /mcp (#55)."""

import json
from contextlib import asynccontextmanager

import httpx
import pytest

from app.core.config import settings

INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}},
}
JSON_HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


@asynccontextmanager
async def running(app=None):
    """A client for `app` (default: a fresh MCP app) with its lifespan running, which the MCP session manager needs.

    A context manager, not a fixture: the lifespan's task group must be entered and exited in the same task.
    A session manager runs only once, so each test gets a fresh MCP app; one test covers main.app's wiring.
    """
    from app.api.mcp import mcp_http_app

    app = app or mcp_http_app(["http://localhost:3000"])
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost:8000") as c:
            yield c


AUTH = {"Authorization": "Bearer agent-token"}


@asynccontextmanager
async def mcp_client(app=None):
    """An MCP client session, signed in as user-a, over Streamable HTTP against the in-process app."""
    import httpx2
    from mcp import Client
    from mcp.client.streamable_http import streamable_http_client

    from app.api.mcp import mcp_http_app

    app = app or mcp_http_app(["http://localhost:3000"])
    async with app.router.lifespan_context(app):
        http = httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), headers=AUTH)
        async with http, Client(streamable_http_client("http://localhost:8000/mcp", http_client=http)) as c:
            yield c


@pytest.fixture
def owner(monkeypatch):
    """verify_trip_owner as in production: user-a owns "trip-a" only. Returns the checks it was asked to make."""
    from fastapi import HTTPException

    from app.api import mcp

    checks = []

    async def fake_verify_trip_owner(trip_id: str, user_id: str) -> dict:
        checks.append((trip_id, user_id))
        if (trip_id, user_id) != ("trip-a", "user-a"):
            raise HTTPException(status_code=403, detail="Not authorized to access this trip")
        return {"id": trip_id, "user_id": user_id}

    monkeypatch.setattr(mcp, "verify_trip_owner", fake_verify_trip_owner)
    return checks


@pytest.fixture
def agent(monkeypatch):
    """require_agent accepts "agent-token" as user-a's token and rejects anything else."""
    from fastapi import HTTPException

    from app.core import auth

    async def fake_require_agent(authorization: str) -> dict:
        if authorization != "Bearer agent-token":
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": "user-a", "client_id": "client-1"}

    monkeypatch.setattr(auth, "require_agent", fake_require_agent)


@pytest.fixture(autouse=True)
def no_playwright(monkeypatch):
    """The app lifespan warms up a browser; tests don't need one."""
    import main

    async def noop():
        pass

    monkeypatch.setattr(main, "warmup_playwright", noop)
    monkeypatch.setattr(main, "shutdown_playwright", noop)


async def test_post_without_token_is_401_pointing_at_resource_metadata():
    async with running() as client:
        resp = await client.post("/mcp", json=INIT, headers=JSON_HEADERS)
    assert resp.status_code == 401
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    assert f'resource_metadata="{base}/.well-known/oauth-protected-resource/mcp"' in resp.headers["www-authenticate"]


async def test_disallowed_origin_is_403(agent):
    headers = {**JSON_HEADERS, **AUTH, "Origin": "https://evil.example"}
    async with running() as client:
        resp = await client.post("/mcp", json=INIT, headers=headers)
    assert resp.status_code == 403


async def test_allowed_origin_passes(agent):
    headers = {**JSON_HEADERS, **AUTH, "Origin": "http://localhost:3000"}
    async with running() as client:
        resp = await client.post("/mcp", json=INIT, headers=headers)
    assert resp.status_code == 200, resp.text


async def test_board_add_items_forwards_to_the_skill_for_an_owned_trip(agent, owner, monkeypatch):
    from app.api import mcp

    calls = []

    async def fake_add_items(trip_id, items):
        calls.append((trip_id, items))
        return "Added 1 item(s) to the board."

    monkeypatch.setattr(mcp, "add_items", fake_add_items)
    async with mcp_client() as client:
        result = await client.call_tool("board_add_items", {"trip_id": "trip-a", "items": '[{"name": "Hotel"}]'})

    assert not result.is_error, result
    assert result.content[0].text == "Added 1 item(s) to the board."
    assert calls == [("trip-a", '[{"name": "Hotel"}]')]
    assert owner == [("trip-a", "user-a")]


async def test_board_tool_refuses_a_trip_the_user_does_not_own(agent, owner, monkeypatch):
    from app.api import mcp

    async def fake_clear_board(trip_id):
        raise AssertionError("must not touch another user's board")

    monkeypatch.setattr(mcp, "clear_board", fake_clear_board)
    async with mcp_client() as client:
        result = await client.call_tool("board_clear", {"trip_id": "trip-b"})

    assert result.is_error
    assert "Not authorized" in result.content[0].text


async def test_main_app_serves_the_tools_and_skill_instructions(agent):
    import main
    import skills.booking

    async with mcp_client(main.app) as client:
        tools = await client.list_tools()
        instructions = client.instructions

    assert {t.name for t in tools.tools} == {
        "list_trips", "create_trip", "board_read", "board_add_items", "board_remove_items", "board_clear",
        "booking_search", "web_search", "image_search",
    }
    assert skills.booking.PROMPT in instructions


async def test_trip_tools_act_for_the_signed_in_user(agent, monkeypatch):
    from app.api import mcp
    from app.services.database import db

    created = []

    async def fake_create_trip(user_id, title, **kwargs):
        created.append((user_id, title))
        return {"id": "trip-new", "title": title, "status": "active"}

    async def fake_update_canvas_state(**kwargs):
        return {}

    async def fake_trips(user_id):
        assert user_id == "user-a"
        return [{"id": "trip-a", "title": "Lisbon", "status": "active"}]

    monkeypatch.setattr(db, "create_trip", fake_create_trip)
    monkeypatch.setattr(db, "update_canvas_state", fake_update_canvas_state)
    monkeypatch.setattr(db, "get_user_trips_with_thumbnails", fake_trips)
    async with mcp_client() as client:
        new = await client.call_tool("create_trip", {"name": "Porto"})
        listed = await client.call_tool("list_trips", {})

    assert created == [("user-a", "Porto")]
    assert json.loads(new.content[0].text)["id"] == "trip-new"
    assert [t["id"] for t in json.loads(listed.content[0].text)] == ["trip-a"]


async def test_search_tools_forward_their_arguments(agent, monkeypatch):
    from app.api import mcp
    from skills.booking.models import SearchParams

    calls = []

    def fake(name):
        async def record(arg):
            calls.append((name, arg))
            return f"{name} results"
        return record

    monkeypatch.setattr(mcp, "search_hotels", fake("hotels"))
    monkeypatch.setattr(mcp, "search_web", fake("web"))
    monkeypatch.setattr(mcp, "search_images", fake("images"))
    async with mcp_client() as client:
        hotels = await client.call_tool(
            "booking_search",
            {"destination": "Lisbon", "checkin": "2026-04-01", "checkout": "2026-04-05", "sort_by": "price"},
        )
        await client.call_tool("web_search", {"query": "Lisbon food"})
        await client.call_tool("image_search", {"query": "Alfama"})

    assert hotels.content[0].text == "hotels results"
    assert calls == [
        ("hotels", SearchParams(destination="Lisbon", checkin="2026-04-01", checkout="2026-04-05", sort_by="price")),
        ("web", "Lisbon food"),
        ("images", "Alfama"),
    ]
