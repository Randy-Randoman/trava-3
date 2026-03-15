"""JWT authentication helpers using Supabase JWKS (ES256)."""

import httpx
import jwt
from fastapi import Header, HTTPException

from app.core.config import settings

# Module-level JWKS cache
_jwks_keys: list[dict] | None = None


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
    global _jwks_keys
    if _jwks_keys is None or force_refresh:
        _jwks_keys = await _fetch_jwks()
    return _jwks_keys


def _decode_token(token: str, keys: list[dict]) -> dict:
    """Decode and validate a JWT using the provided JWKS keys."""
    # Build PyJWT key set from JWKS
    jwk_set = jwt.PyJWKSet.from_dict({"keys": keys})
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    # Find the matching key
    signing_key = None
    for jwk in jwk_set.keys:
        if jwk.key_id == kid:
            signing_key = jwk.key
            break

    if signing_key is None:
        raise jwt.InvalidTokenError("No matching key found")

    return jwt.decode(
        token,
        signing_key,
        algorithms=["ES256"],
        audience="authenticated",
        options={"require": ["exp", "sub"]},
    )


async def require_auth(
    authorization: str = Header(..., description="Bearer token"),
) -> str:
    """FastAPI dependency that validates the JWT and returns the user_id (sub claim).

    Usage:
        @router.get("/protected")
        async def protected(user_id: str = Depends(require_auth)):
            ...
    """
    # Extract token from "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    # Try with cached keys first
    keys = await _get_jwks()
    try:
        payload = _decode_token(token, keys)
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        # Refresh keys once and retry (key rotation)
        keys = await _get_jwks(force_refresh=True)
        try:
            payload = _decode_token(token, keys)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    return payload["sub"]


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
