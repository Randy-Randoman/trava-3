"""LangChain @tool wrappers for Booking.com search and affiliate links."""

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
    """Search Booking.com for hotels. Returns results with prices, ratings, and affiliate booking links.

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

    # Format results for the agent
    results = []
    for i, h in enumerate(hotels, 1):
        parts = [f"**{i}. {h.name}**"]
        if h.price:
            parts.append(f"   Price: {h.price}")
        if h.rating:
            parts.append(f"   Rating: {h.rating}")
        if h.review_count:
            parts.append(f"   Reviews: {h.review_count}")
        if h.distance:
            parts.append(f"   Distance: {h.distance}")
        if h.affiliate_url:
            parts.append(f"   Book: {h.affiliate_url}")
        elif h.url:
            parts.append(f"   Link: {h.url}")
        results.append("\n".join(parts))

    return (
        f"Found {len(hotels)} hotels in {destination} "
        f"({checkin} to {checkout}):\n\n" + "\n\n".join(results)
    )


@tool
def deeplink_generate(hotel_url: str) -> str:
    """Generate an affiliate booking link for a specific hotel URL."""
    cj_pid = os.getenv("CJ_PID", "")
    cj_aid = os.getenv("CJ_AID", "")
    return build_affiliate_url(hotel_url, cj_pid, cj_aid)
