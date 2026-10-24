"""Tests for budget price parsing in GET /trips/{trip_id}/budget (Issue #19)."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import httpx
import pytest

FAKE_USER_ID = "user-00000000-0000-0000-0000-000000000000"
FAKE_TRIP_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


@pytest.fixture
def client():
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


async def get_budget(client, prices, budget=500):
    trip = {
        "id": FAKE_TRIP_ID,
        "budget": budget,
        "board_items": [
            {"name": f"Item {i}", "type": "stay", "data": {"price": p}} for i, p in enumerate(prices)
        ],
    }
    with patch("app.api.trips.verify_trip_owner", new_callable=AsyncMock, return_value=trip):
        resp = await client.get(f"/trips/{FAKE_TRIP_ID}/budget")
    assert resp.status_code == 200
    return resp.json()


@pytest.mark.parametrize("price, expected", [
    ("€120", 120.0),
    ("120 €", 120.0),
    ("EUR 99", 99.0),
    ("$234/night", 234.0),
    ("$1,234", 1234.0),
    ("99.90 EUR", 99.9),
])
async def test_parses_price(client, price, expected):
    body = await get_budget(client, [price])
    assert body["spent"] == expected
    assert body["items"] == [{"name": "Item 0", "type": "stay", "price": expected}]


@pytest.mark.xfail(reason="Bug: commas are stripped, so European '1.234,50' parses as 1.2345", strict=True)
async def test_parses_european_format(client):
    body = await get_budget(client, ["1.234,50 €"])
    assert body["spent"] == 1234.5


@pytest.mark.parametrize("price", [None, "", "Price on request", "n/a"])
async def test_missing_or_garbage_price_is_skipped(client, price):
    body = await get_budget(client, [price])
    assert body["spent"] == 0.0
    assert body["items"] == []


async def test_sums_prices_and_returns_budget(client):
    body = await get_budget(client, ["€120", "garbage", "EUR 80.50"], budget=500)
    assert body == {
        "budget": 500.0,
        "spent": 200.5,
        "items": [
            {"name": "Item 0", "type": "stay", "price": 120.0},
            {"name": "Item 2", "type": "stay", "price": 80.5},
        ],
    }


async def test_no_budget_set(client):
    body = await get_budget(client, [], budget=None)
    assert body == {"budget": None, "spent": 0.0, "items": []}
