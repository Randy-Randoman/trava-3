"""Tests for require_agent: OAuth access tokens presented by external agents (#54)."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException

import app.core.auth as auth_module

SUPABASE_URL = "https://proj.supabase.co"
ISSUER = f"{SUPABASE_URL}/auth/v1"
KID = "test-kid"
USER_ID = "11111111-1111-1111-1111-111111111111"
CLIENT_ID = "22222222-2222-2222-2222-222222222222"
SESSION_ID = "33333333-3333-3333-3333-333333333333"

PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
PUBLIC_JWK = {
    **pyjwt.algorithms.ECAlgorithm.to_jwk(PRIVATE_KEY.public_key(), as_dict=True),
    "kid": KID,
    "alg": "ES256",
}


def _token(drop=(), alg="ES256", key=PRIVATE_KEY, **overrides) -> str:
    claims = {
        "iss": ISSUER,
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "sub": USER_ID,
        "client_id": CLIENT_ID,
        "session_id": SESSION_ID,
        **overrides,
    }
    for name in drop:
        claims.pop(name)
    return pyjwt.encode(claims, key, algorithm=alg, headers={"kid": KID})


@pytest.fixture(autouse=True)
def project():
    """A mocked JWKS endpoint and Supabase URL; the JWKS cache reset around each test."""
    auth_module._jwks_keys = None
    with patch.object(auth_module.settings, "SUPABASE_URL", SUPABASE_URL), patch.object(
        auth_module, "_fetch_jwks", new_callable=AsyncMock, return_value=[PUBLIC_JWK]
    ):
        yield
    auth_module._jwks_keys = None


def _db(active: bool) -> MagicMock:
    """A service client whose agent_grant_active RPC answers `active`."""
    db = MagicMock()
    db.client.rpc.return_value.execute.return_value.data = active
    return db


async def _call(token: str, active: bool = True):
    db = _db(active)
    with patch("app.services.database.db", db):
        return await auth_module.require_agent(authorization=f"Bearer {token}"), db


async def test_valid_agent_token_returns_user_and_client():
    agent, db = await _call(_token())
    assert agent == {"user_id": USER_ID, "client_id": CLIENT_ID}
    db.client.rpc.assert_called_once_with(
        "agent_grant_active",
        {"p_user": USER_ID, "p_client": CLIENT_ID, "p_session": SESSION_ID},
    )


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(lambda: _token(drop=["client_id"]), id="browser session (no client_id)"),
        pytest.param(lambda: _token(drop=["session_id"]), id="no session_id"),
        pytest.param(lambda: _token(iss="https://other.supabase.co/auth/v1"), id="wrong issuer"),
        pytest.param(lambda: _token(aud="anon"), id="wrong audience"),
        pytest.param(lambda: _token(exp=int(time.time()) - 60), id="expired"),
        pytest.param(lambda: _token(alg="HS256", key="a-shared-secret-of-at-least-32-bytes"), id="HS256"),
        pytest.param(
            lambda: _token(key=ec.generate_private_key(ec.SECP256R1())), id="other key"
        ),
        pytest.param(lambda: "not.a.jwt", id="garbage"),
    ],
)
async def test_rejected_tokens_raise_401(token):
    with pytest.raises(HTTPException) as exc_info:
        await _call(token())
    assert exc_info.value.status_code == 401


async def test_revoked_grant_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        await _call(_token(), active=False)
    assert exc_info.value.status_code == 401


async def test_malformed_header_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        await auth_module.require_agent(authorization="Token abc")
    assert exc_info.value.status_code == 401
