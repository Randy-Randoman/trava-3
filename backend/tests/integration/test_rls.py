"""Row-level security rules on trips, canvas_states, board items, chat and profiles."""

import uuid

import pytest
from postgrest.exceptions import APIError

pytestmark = pytest.mark.integration


@pytest.fixture
def chat_a(service, trip_a) -> dict:
    """A conversation with one message on A's trip."""
    conv = service.table("conversations").insert({"trip_id": trip_a["id"]}).execute().data[0]
    msg = service.table("messages").insert(
        {"conversation_id": conv["id"], "role": "user", "content": "hello"}
    ).execute().data[0]
    return {"conversation": conv, "message": msg}


class TestTrips:
    def test_owner_can_select_update_delete(self, user_a, trip_a):
        db = user_a["client"]
        assert db.table("trips").select("id").eq("id", trip_a["id"]).execute().data
        updated = db.table("trips").update({"title": "Renamed"}).eq("id", trip_a["id"]).execute().data
        assert updated[0]["title"] == "Renamed"
        assert db.table("trips").delete().eq("id", trip_a["id"]).execute().data

    def test_other_user_cannot_select(self, user_b, trip_a):
        assert user_b["client"].table("trips").select("id").eq("id", trip_a["id"]).execute().data == []

    def test_other_user_cannot_update(self, service, user_b, trip_a):
        res = user_b["client"].table("trips").update({"title": "Hacked"}).eq("id", trip_a["id"]).execute()
        assert res.data == []
        assert service.table("trips").select("title").eq("id", trip_a["id"]).execute().data[0]["title"] == "A's trip"

    def test_other_user_cannot_delete(self, service, user_b, trip_a):
        assert user_b["client"].table("trips").delete().eq("id", trip_a["id"]).execute().data == []
        assert service.table("trips").select("id").eq("id", trip_a["id"]).execute().data

    def test_other_user_cannot_create_trip_for_owner(self, user_a, user_b):
        with pytest.raises(APIError):
            user_b["client"].table("trips").insert({"user_id": user_a["id"], "title": "Spoof"}).execute()


class TestBoardItems:
    def test_owner_can_read_and_write(self, user_a, trip_a):
        db = user_a["client"]
        assert db.table("trips").select("board_items").eq("id", trip_a["id"]).execute().data[0]["board_items"]
        res = db.table("trips").update({"board_items": []}).eq("id", trip_a["id"]).execute()
        assert res.data[0]["board_items"] == []

    def test_other_user_cannot_read_or_write(self, service, user_b, trip_a):
        db = user_b["client"]
        assert db.table("trips").select("board_items").eq("id", trip_a["id"]).execute().data == []
        assert db.table("trips").update({"board_items": []}).eq("id", trip_a["id"]).execute().data == []
        stored = service.table("trips").select("board_items").eq("id", trip_a["id"]).execute().data[0]
        assert stored["board_items"] == [{"name": "Hotel"}]


class TestCanvasStates:
    def test_owner_can_select_update_delete(self, user_a, trip_a):
        db = user_a["client"]
        assert db.table("canvas_states").select("id").eq("trip_id", trip_a["id"]).execute().data
        res = db.table("canvas_states").update({"scene_elements": [{"id": "e1"}]}).eq("trip_id", trip_a["id"]).execute()
        assert res.data[0]["scene_elements"] == [{"id": "e1"}]
        assert db.table("canvas_states").delete().eq("trip_id", trip_a["id"]).execute().data

    def test_other_user_cannot_select_update_delete(self, service, user_b, trip_a):
        db = user_b["client"]
        assert db.table("canvas_states").select("id").eq("trip_id", trip_a["id"]).execute().data == []
        assert db.table("canvas_states").update({"scene_elements": [{"id": "x"}]}).eq("trip_id", trip_a["id"]).execute().data == []
        assert db.table("canvas_states").delete().eq("trip_id", trip_a["id"]).execute().data == []
        stored = service.table("canvas_states").select("scene_elements").eq("trip_id", trip_a["id"]).execute().data
        assert stored == [{"scene_elements": []}]


class TestChat:
    def test_owner_can_select_and_delete(self, user_a, chat_a):
        db = user_a["client"]
        conv_id = chat_a["conversation"]["id"]
        assert db.table("conversations").select("id").eq("id", conv_id).execute().data
        assert db.table("messages").select("id").eq("conversation_id", conv_id).execute().data
        assert db.table("messages").delete().eq("id", chat_a["message"]["id"]).execute().data
        assert db.table("conversations").delete().eq("id", conv_id).execute().data

    def test_other_user_cannot_select_update_delete(self, service, user_b, chat_a):
        db = user_b["client"]
        conv_id = chat_a["conversation"]["id"]
        msg_id = chat_a["message"]["id"]
        assert db.table("conversations").select("id").eq("id", conv_id).execute().data == []
        assert db.table("messages").select("id").eq("conversation_id", conv_id).execute().data == []
        assert db.table("conversations").update({"title": "Hacked"}).eq("id", conv_id).execute().data == []
        assert db.table("messages").update({"content": "Hacked"}).eq("id", msg_id).execute().data == []
        assert db.table("messages").delete().eq("id", msg_id).execute().data == []
        assert db.table("conversations").delete().eq("id", conv_id).execute().data == []
        assert service.table("messages").select("content").eq("id", msg_id).execute().data == [{"content": "hello"}]
        assert service.table("conversations").select("title").eq("id", conv_id).execute().data == [{"title": None}]

    def test_other_user_cannot_post_into_owners_conversation(self, user_b, chat_a):
        with pytest.raises(APIError):
            user_b["client"].table("messages").insert(
                {"conversation_id": chat_a["conversation"]["id"], "role": "user", "content": "spam"}
            ).execute()


class TestSharedTrips:
    def test_anon_cannot_read_shared_trip_or_canvas(self, service, anon, trip_a):
        token = str(uuid.uuid4())
        service.table("trips").update({"share_token": token}).eq("id", trip_a["id"]).execute()
        assert anon.table("trips").select("id").execute().data == []
        assert anon.table("trips").select("id").eq("share_token", token).execute().data == []
        assert anon.table("canvas_states").select("id").execute().data == []


class TestProfiles:
    def test_is_approved_column_is_gone(self, service):
        with pytest.raises(APIError) as exc:
            service.table("profiles").select("is_approved").limit(1).execute()
        assert exc.value.code == "42703"  # undefined_column

    def test_sign_up_creates_profile(self, service, anon):
        email = f"it-signup-{uuid.uuid4().hex[:12]}@example.com"
        user = anon.auth.sign_up({"email": email, "password": f"pw-{uuid.uuid4().hex}"}).user
        try:
            assert service.table("profiles").select("id").eq("id", user.id).execute().data == [{"id": user.id}]
        finally:
            service.auth.admin.delete_user(user.id)
