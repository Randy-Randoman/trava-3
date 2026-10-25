"""Tests for the OAuth protected resource metadata (RFC 9728, #54)."""

from unittest.mock import patch

import httpx
import pytest

from app.core.config import settings


@pytest.fixture
def client():
    from main import app

    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.mark.parametrize(
    "path", ["/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"]
)
async def test_metadata_names_resource_and_authorization_server(client, path):
    with patch.object(settings, "PUBLIC_BASE_URL", "https://api.trava.test/"), patch.object(
        settings, "SUPABASE_URL", "https://proj.supabase.co"
    ):
        resp = await client.get(path)
    assert resp.status_code == 200
    assert resp.json() == {
        "resource": "https://api.trava.test/mcp",
        "authorization_servers": ["https://proj.supabase.co/auth/v1"],
        "bearer_methods_supported": ["header"],
        "resource_name": "TRAVA",
    }
