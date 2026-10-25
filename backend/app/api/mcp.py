"""Remote MCP server at /mcp: external agents (Claude Code, claude.ai connectors) plan trips on the board.

Auth uses the MCP SDK's resource-server support: a TokenVerifier backed by `require_agent`.
Requests without a valid token get a 401 whose WWW-Authenticate header points at the
protected resource metadata, which starts the client's OAuth flow.
"""

import json
from urllib.parse import urlparse

from fastapi import HTTPException
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings

import skills.board
import skills.booking
import skills.web_search
from app.api import trips
from app.core import auth
from app.core.auth import verify_trip_owner
from app.core.config import settings
from skills.board.tools import add_items, clear_board, read_board, remove_items
from skills.booking.models import SearchParams
from skills.booking.tools import search_hotels
from skills.web_search.tools import search_images, search_web


class AgentTokenVerifier:
    """Accepts the OAuth access tokens `require_agent` accepts; the user id becomes the token's subject."""

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            agent = await auth.require_agent(f"Bearer {token}")
        except HTTPException:
            return None
        return AccessToken(token=token, client_id=agent["client_id"], scopes=[], subject=agent["user_id"])


_base_url = settings.PUBLIC_BASE_URL.rstrip("/")

INSTRUCTIONS = "\n\n".join([
    "TRAVA is a visual trip-planning board. Every board tool takes a trip_id: "
    "find one with list_trips or make one with create_trip. "
    "Items you add show up on the trip's board in the TRAVA app.",
    skills.board.PROMPT,
    skills.booking.PROMPT,
    skills.web_search.PROMPT,
])

server = MCPServer(
    name="trava",
    instructions=INSTRUCTIONS,
    token_verifier=AgentTokenVerifier(),
    auth=AuthSettings(
        issuer_url=f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
        resource_server_url=f"{_base_url}/mcp",
        # Supabase tokens carry no resource indicator; require_agent checks audience and issuer itself
        validate_token_resource=False,
    ),
)


def _user_id() -> str:
    """The signed-in user, as resolved from this request's bearer token by AgentTokenVerifier."""
    return get_access_token().subject


@server.tool()
async def list_trips() -> str:
    """List the user's trips (id, title, destination, status) as JSON."""
    listed = await trips.list_trips(user_id=_user_id())
    return json.dumps([t.model_dump() for t in listed.trips])


@server.tool()
async def create_trip(name: str) -> str:
    """Create a new trip with an empty board; returns it as JSON (use its id as trip_id)."""
    created = await trips.create_trip(trips.TripCreate(title=name), user_id=_user_id())
    return created.model_dump_json()


async def _check_owner(trip_id: str) -> None:
    """Refuse a trip the signed-in user doesn't own, as a tool error the agent can read."""
    try:
        await verify_trip_owner(trip_id, _user_id())
    except HTTPException as e:
        raise ToolError(e.detail)


@server.tool()
async def board_read(trip_id: str) -> str:
    """See what's on a trip's board: item IDs (for board_remove_items) and details."""
    await _check_owner(trip_id)
    return await read_board(trip_id)


@server.tool()
async def board_add_items(trip_id: str, items: str) -> str:
    """Place hotel/activity cards on a trip's board.

    items: JSON list of items (each with name, type, price, rating, description, bookingUrl, image_url, ...).
    booking_search output can be passed as is.
    """
    await _check_owner(trip_id)
    return await add_items(trip_id, items)


@server.tool()
async def board_remove_items(trip_id: str, ids: str) -> str:
    """Remove items from a trip's board by their short IDs (comma-separated, as shown by board_read)."""
    await _check_owner(trip_id)
    return await remove_items(trip_id, ids)


@server.tool()
async def board_clear(trip_id: str) -> str:
    """Remove all agent-placed items from a trip's board, keeping the user's own drawings."""
    await _check_owner(trip_id)
    return await clear_board(trip_id)


@server.tool()
async def booking_search(
    destination: str,
    checkin: str,
    checkout: str,
    adults: int = 2,
    rooms: int = 1,
    property_type: str | None = None,
    min_review_score: int | None = None,
    star_rating: int | None = None,
    sort_by: str | None = None,
) -> str:
    """Search Booking.com for hotels. Returns a JSON array of hotels that can be passed directly to board_add_items.

    Args:
        destination: City or area to search (e.g. "Lisbon", "Paris 7th arrondissement")
        checkin: Check-in date in YYYY-MM-DD format
        checkout: Check-out date in YYYY-MM-DD format
        adults: Number of adults (default 2)
        rooms: Number of rooms (default 1)
        property_type: Filter by type — one of: hotel, apartment, hostel, resort, villa, guesthouse, boutique
        min_review_score: Minimum guest review score (6, 7, 8, or 9 out of 10)
        star_rating: Hotel star rating (1-5)
        sort_by: Sort results — one of: price, rating, distance, best_value
    """
    return await search_hotels(SearchParams(
        destination=destination,
        checkin=checkin,
        checkout=checkout,
        adults=adults,
        rooms=rooms,
        property_type=property_type,
        min_review_score=min_review_score,
        star_rating=star_rating,
        sort_by=sort_by,
    ))


@server.tool()
async def web_search(query: str) -> str:
    """Search the web for destinations, activities, restaurants, flights and travel tips. Returns JSON results with urls."""
    return await search_web(query)


@server.tool()
async def image_search(query: str) -> str:
    """Search for images of destinations, hotels, or activities. Returns image URLs."""
    return await search_images(query)


def mcp_http_app(allowed_origins: list[str]):
    """The Streamable HTTP app serving POST /mcp. Route /mcp to it and run its lifespan."""
    return server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        # DNS-rebinding protection: an Origin header, when present, must be one of the app's own
        transport_security=TransportSecuritySettings(
            allowed_hosts=[urlparse(_base_url).netloc, "localhost:*", "127.0.0.1:*"],
            allowed_origins=allowed_origins,
        ),
    )
