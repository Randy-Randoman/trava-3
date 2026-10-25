"""agent_grant_active (#54): only the service role may ask, and only live grants pass."""

import uuid

import jwt
import pytest
from postgrest.exceptions import APIError

pytestmark = pytest.mark.integration


def _args(user: str, client: str, session: str) -> dict:
    return {"p_user": user, "p_client": client, "p_session": session}


def test_unknown_grant_is_inactive(service):
    ids = _args(str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4()))
    assert service.rpc("agent_grant_active", ids).execute().data is False


def test_browser_session_without_consent_is_inactive(service, user_a):
    """The user's own app session is live, but no OAuth client holds a grant for it."""
    session_id = jwt.decode(user_a["jwt"], options={"verify_signature": False})["session_id"]
    ids = _args(user_a["id"], str(uuid.uuid4()), session_id)
    assert service.rpc("agent_grant_active", ids).execute().data is False


def test_not_executable_by_anon_or_authenticated(anon, user_a):
    ids = _args(user_a["id"], str(uuid.uuid4()), str(uuid.uuid4()))
    for client in (anon, user_a["client"]):
        with pytest.raises(APIError):
            client.rpc("agent_grant_active", ids).execute()
