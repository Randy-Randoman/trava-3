"""Tests for the plain search functions behind the booking and web_search tools."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from skills.booking.models import Hotel, SearchParams
from skills.booking.tools import booking_search, search_hotels
from skills.web_search.tools import image_search, search_images, search_web, web_search

PARAMS = SearchParams(destination="Lisbon", checkin="2026-03-17", checkout="2026-03-20")


class TestSearchHotels:
    async def test_returns_board_ready_items(self):
        hotels = [Hotel(name="Hotel A", price="€150", rating="8.7", review_count="1,234",
                        distance="1 km", url="https://b.com/a", image_url="https://img/a")]
        with patch("skills.booking.tools.search_booking", AsyncMock(return_value=hotels)):
            result = json.loads(await search_hotels(PARAMS))

        assert result == [{
            "name": "Hotel A", "type": "stay", "price": "€150", "rating": "8.7",
            "review_count": "1,234", "distance": "1 km",
            "description": "Rating 8.7/10 · 1,234 reviews · 1 km · Check-in: 2026-03-17 · Check-out: 2026-03-20",
            "bookingUrl": "https://b.com/a", "image_url": "https://img/a",
        }]

    async def test_no_results(self):
        with patch("skills.booking.tools.search_booking", AsyncMock(return_value=[])):
            result = await search_hotels(PARAMS)
        assert result == "No hotels found in Lisbon for 2026-03-17 to 2026-03-20."

    async def test_search_error(self):
        with patch("skills.booking.tools.search_booking", AsyncMock(side_effect=RuntimeError("boom"))):
            result = await search_hotels(PARAMS)
        assert result == "Search failed. Playwright/Chromium may not be installed."

    def test_rejects_bad_dates_and_counts(self):
        for bad in ({"checkin": "2026-03-17&x=1"}, {"adults": 0}, {"rooms": 31}):
            with pytest.raises(ValidationError):
                PARAMS.model_validate({**PARAMS.model_dump(), **bad})

    async def test_tool_passes_params_through(self):
        search = AsyncMock(return_value=[])
        with patch("skills.booking.tools.search_booking", search):
            await booking_search.coroutine(destination="Lisbon", checkin="2026-03-17",
                                           checkout="2026-03-20", sort_by="price")
        assert search.call_args.args[0] == PARAMS.model_copy(update={"sort_by": "price"})


def tavily(response):
    client = MagicMock()
    client.search = AsyncMock(return_value=response)
    return patch("skills.web_search.tools.AsyncTavilyClient", return_value=client)


def api_key(value="key"):
    return patch("skills.web_search.tools.settings.TAVILY_API_KEY", value)


class TestSearchWeb:
    async def test_returns_results(self):
        with api_key(), tavily({"results": [{"title": "T", "content": "C", "url": "U", "score": 1}]}):
            assert json.loads(await search_web("lisbon")) == [{"title": "T", "content": "C", "url": "U"}]

    async def test_no_results(self):
        with api_key(), tavily({"results": []}):
            assert await search_web("lisbon") == "No results found."

    async def test_missing_api_key(self):
        with api_key(""):
            assert await search_web("lisbon") == "Error: TAVILY_API_KEY not set in environment."

    async def test_tool_delegates(self):
        with api_key(), tavily({"results": []}):
            assert await web_search.coroutine(query="lisbon") == "No results found."


class TestSearchImages:
    async def test_returns_at_most_five_urls(self):
        with api_key(), tavily({"images": [f"u{i}" for i in range(7)]}):
            assert await search_images("lisbon") == "- u0\n- u1\n- u2\n- u3\n- u4"

    async def test_no_images(self):
        with api_key(), tavily({"images": []}):
            assert await search_images("lisbon") == "No images found."

    async def test_tool_delegates(self):
        with api_key(), tavily({"images": ["u0"]}):
            assert await image_search.coroutine(query="lisbon") == "- u0"
