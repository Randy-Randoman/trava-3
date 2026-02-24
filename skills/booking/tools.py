"""LangChain @tool wrappers for Booking.com search and affiliate links."""

import json
import os
from langchain_core.tools import tool
from .search import search_booking
from .models import SearchParams
from .deeplink import build_affiliate_url


@tool
async def booking_search(
    destination: str,
    checkin: str,
    checkout: str,
    adults: int = 2,
    rooms: int = 1,
) -> str:
    """Search Booking.com for hotels. Returns a JSON array of hotel objects that can be passed directly to board_add_items.

    Args:
        destination: City or area to search (e.g. "Lisbon", "Paris 7th arrondissement")
        checkin: Check-in date in YYYY-MM-DD format
        checkout: Check-out date in YYYY-MM-DD format
        adults: Number of adults (default 2)
        rooms: Number of rooms (default 1)
    """
    params = SearchParams(
        destination=destination,
        checkin=checkin,
        checkout=checkout,
        adults=adults,
        rooms=rooms,
    )

    cj_pid = os.getenv("CJ_PID", "")
    cj_aid = os.getenv("CJ_AID", "")

    try:
        hotels = await search_booking(params, cj_pid, cj_aid)
    except Exception as e:
        return f"Search failed: {e}. Playwright/Chromium may not be installed."

    if not hotels:
        return f"No hotels found in {destination} for {checkin} to {checkout}."

    # Return structured JSON — agent can pass this directly to board_add_items
    results = []
    for h in hotels:
        # Build a description from available data
        desc_parts = []
        if h.rating:
            desc_parts.append(f"Rating {h.rating}/10")
        if h.review_count:
            desc_parts.append(f"{h.review_count} reviews")
        if h.distance:
            desc_parts.append(h.distance)
        desc_parts.append(f"Check-in: {checkin} · Check-out: {checkout}")

        item = {
            "name": h.name,
            "type": "stay",
            "price": h.price or "",
            "rating": h.rating or "",
            "review_count": h.review_count or "",
            "distance": h.distance or "",
            "description": " · ".join(desc_parts) if desc_parts else "",
            "bookingUrl": h.affiliate_url or h.url or "",
            "image_url": h.image_url or "",
        }
        results.append(item)

    return json.dumps(results)


@tool
def deeplink_generate(hotel_url: str) -> str:
    """Generate an affiliate booking link for a specific hotel URL."""
    cj_pid = os.getenv("CJ_PID", "")
    cj_aid = os.getenv("CJ_AID", "")
    return build_affiliate_url(hotel_url, cj_pid, cj_aid)
