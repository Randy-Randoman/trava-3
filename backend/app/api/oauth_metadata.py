"""OAuth 2.0 protected resource metadata (RFC 9728) for the MCP server.

Agents read this before signing in to find the authorization server: Supabase Auth.
Served at both the root and the path-suffixed well-known URL, since clients try either.
"""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/.well-known/oauth-protected-resource")
@router.get("/.well-known/oauth-protected-resource/mcp")
async def protected_resource_metadata():
    return {
        "resource": f"{settings.PUBLIC_BASE_URL.rstrip('/')}/mcp",
        "authorization_servers": [f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"],
        "bearer_methods_supported": ["header"],
        "resource_name": "TRAVA",
    }
