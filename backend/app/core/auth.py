"""JWT authentication helpers using Supabase JWKS (ES256)."""

import asyncio
import logging
import time
import uuid

import httpx
import jwt
from fastapi import Header, HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level JWKS cache
_jwks_keys: list[dict] | None = None
_jwks_fetched_at = 0.0
# Unknown-kid refetches are limited so bad tokens can't trigger a fetch each
_JWKS_REFRESH_COOLDOWN = 60.0


class UnknownKeyError(jwt.InvalidTokenError):
    """The token's `kid` isn't in the cached JWKS (keys may have rotated)."""


async def _fetch_jwks() -> list[dict]:
    """Fetch JWKS signing keys from Supabase."""
    base = settings.SUPABASE_URL.rstrip("/")
    url = f"{base}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()["keys"]


async def _get_jwks(force_refresh: bool = False) -> list[dict]:
    """Return cached JWKS keys, fetching if needed."""
    global _jwks_keys, _jwks_fetched_at
    if _jwks_keys is None or force_refresh:
        try:
            _jwks_keys = await _fetch_jwks()
        except httpx.HTTPError:
            logger.exception("Failed to fetch JWKS")
            raise HTTPException(status_code=503, detail="Auth temporarily unavailable")
        _jwks_fetched_at = time.monotonic()
    return _jwks_keys


def _signing_key(token: str, keys: list[dict]):
    """Return the JWKS key matching the token's `kid`."""
    # Build PyJWT key set from JWKS
    jwk_set = jwt.PyJWKSet.from_dict({"keys": keys})
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    # Find the matching key
    for jwk in jwk_set.keys:
        if jwk.key_id == kid:
            return jwk.key

    raise UnknownKeyError("No matching key found")


def _decode_token(token: str, keys: list[dict]) -> dict:
    """Decode and validate a JWT using the provided JWKS keys."""
    return jwt.decode(
        token,
        _signing_key(token, keys),
        algorithms=["ES256"],
        audience="authenticated",
        options={"require": ["exp", "sub"]},
    )


def _decode_agent_token(token: str, keys: list[dict]) -> dict:
    """Decode an OAuth access token that this project's Supabase Auth issued to an agent.

    `client_id` is required, so the app's own browser sessions aren't accepted.
    """
    return jwt.decode(
        token,
        _signing_key(token, keys),
        algorithms=["ES256", "RS256"],
        audience="authenticated",
        issuer=f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
        options={"require": ["exp", "sub", "client_id", "session_id"]},
    )


def _bearer_token(authorization: str) -> str:
    """Extract the token from "Bearer <token>", or raise 401."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    return token


async def _verify(token: str, decode) -> dict:
    """Decode with the cached JWKS keys. Only an unknown `kid` (key rotation) refreshes them,
    at most once per cooldown, then retries."""
    try:
        try:
            return decode(token, await _get_jwks())
        except UnknownKeyError:
            if time.monotonic() - _jwks_fetched_at < _JWKS_REFRESH_COOLDOWN:
                raise
            return decode(token, await _get_jwks(force_refresh=True))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except (jwt.InvalidTokenError, jwt.PyJWKSetError):
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_auth(
    authorization: str = Header(..., description="Bearer token"),
) -> str:
    """FastAPI dependency that validates the JWT and returns the user_id (sub claim).

    Usage:
        @router.get("/protected")
        async def protected(user_id: str = Depends(require_auth)):
            ...
    """
    payload = await _verify(_bearer_token(authorization), _decode_token)
    if "client_id" in payload:
        # OAuth tokens issued to agents only work on /mcp, where revocation is checked live
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


async def require_agent(
    authorization: str = Header(..., description="Bearer token"),
) -> dict:
    """FastAPI dependency for agents (the MCP server): validates an OAuth 2.1 access token.

    Besides the JWT checks, the user's grant to the client must still be active (consent not
    revoked, client not deleted, session alive), so disconnecting an app takes effect at once.
    Returns {"user_id": ..., "client_id": ...}.
    """
    from app.services.database import db

    claims = await _verify(_bearer_token(authorization), _decode_agent_token)
    ids = (claims["sub"], claims["client_id"], claims["session_id"])
    try:
        for value in ids:
            uuid.UUID(str(value))
        rpc = db.client.rpc(
            "agent_grant_active", {"p_user": ids[0], "p_client": ids[1], "p_session": ids[2]}
        )
        active = (await asyncio.to_thread(rpc.execute)).data
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        # e.g. the OAuth server isn't enabled, so the auth.oauth_* tables are missing
        logger.exception("Agent grant check failed")
        raise HTTPException(status_code=401, detail="Invalid token")
    if active is not True:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"user_id": claims["sub"], "client_id": claims["client_id"]}


async def verify_trip_owner(trip_id: str, user_id: str) -> dict:
    """Check that the user owns the trip. Returns the trip dict.

    Raises:
        HTTPException 404 if trip not found.
        HTTPException 403 if the user does not own the trip.
    """
    from app.services.database import db

    trip = await db.get_trip(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this trip")
    return trip
