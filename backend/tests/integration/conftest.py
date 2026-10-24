"""Fixtures for integration tests against a local Supabase stack (`supabase start`).

The whole folder is skipped when the local stack isn't reachable.
"""

import os
import subprocess
import uuid
from pathlib import Path

import pytest
from supabase import Client, create_client

REPO_ROOT = Path(__file__).resolve().parents[3]


def _local_supabase() -> dict | None:
    """Return API_URL / ANON_KEY / SERVICE_ROLE_KEY from `supabase status -o env`, or None."""
    try:
        out = subprocess.run(
            ["supabase", "status", "-o", "env"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    env = {}
    for line in out.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            env[key.strip()] = value.strip().strip('"')
    if not all(env.get(k) for k in ("API_URL", "ANON_KEY", "SERVICE_ROLE_KEY")):
        return None
    return env


LOCAL = _local_supabase()

if LOCAL:
    # Point the backend at local Supabase before the app is imported.
    os.environ["SUPABASE_URL"] = LOCAL["API_URL"]
    os.environ["NEXT_PUBLIC_SUPABASE_URL"] = LOCAL["API_URL"]
    os.environ["SUPABASE_SERVICE_KEY"] = LOCAL["SERVICE_ROLE_KEY"]
    os.environ["NEXT_PUBLIC_SUPABASE_ANON_KEY"] = LOCAL["ANON_KEY"]


def pytest_collection_modifyitems(config, items):
    if LOCAL:
        return
    skip = pytest.mark.skip(reason="local Supabase not running (run `supabase start` from the repo root)")
    here = Path(__file__).parent
    for item in items:
        if here in Path(item.fspath).parents:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def supabase_env() -> dict:
    return LOCAL


@pytest.fixture(scope="session")
def service(supabase_env) -> Client:
    """Service-role client (bypasses RLS)."""
    return create_client(supabase_env["API_URL"], supabase_env["SERVICE_ROLE_KEY"])


@pytest.fixture
def anon(supabase_env) -> Client:
    """Client with only the anon key (not signed in)."""
    return create_client(supabase_env["API_URL"], supabase_env["ANON_KEY"])


def _make_user(supabase_env, service: Client):
    email = f"it-{uuid.uuid4().hex[:12]}@example.com"
    password = f"pw-{uuid.uuid4().hex}"
    user = service.auth.admin.create_user(
        {"email": email, "password": password, "email_confirm": True}
    ).user
    client = create_client(supabase_env["API_URL"], supabase_env["ANON_KEY"])
    session = client.auth.sign_in_with_password({"email": email, "password": password}).session
    # `client` now sends the user's JWT on every PostgREST/Storage request.
    return {"id": user.id, "jwt": session.access_token, "client": client}


@pytest.fixture(scope="session")
def user_a(supabase_env, service):
    user = _make_user(supabase_env, service)
    yield user
    service.auth.admin.delete_user(user["id"])


@pytest.fixture(scope="session")
def user_b(supabase_env, service):
    user = _make_user(supabase_env, service)
    yield user
    service.auth.admin.delete_user(user["id"])


@pytest.fixture
def trip_a(service, user_a) -> dict:
    """A fresh trip owned by user A (the trip trigger also creates its canvas_states row)."""
    trip = service.table("trips").insert(
        {"user_id": user_a["id"], "title": "A's trip", "board_items": [{"name": "Hotel"}]}
    ).execute().data[0]
    yield trip
    service.table("trips").delete().eq("id", trip["id"]).execute()
