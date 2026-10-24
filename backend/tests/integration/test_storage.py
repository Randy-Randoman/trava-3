"""Storage rules on the public `canvas-images` bucket: only the trip owner may write."""

import httpx
import pytest
from storage3.exceptions import StorageApiError

pytestmark = pytest.mark.integration

BUCKET = "canvas-images"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


@pytest.fixture
def image_a(service, user_a, trip_a):
    """x.png uploaded by user A into A's trip folder. Removed via the Storage API afterwards."""
    path = f"{trip_a['id']}/x.png"
    user_a["client"].storage.from_(BUCKET).upload(path, PNG, {"content-type": "image/png"})
    yield path
    service.storage.from_(BUCKET).remove([path])


def _public_get(supabase_env, path) -> httpx.Response:
    return httpx.get(f"{supabase_env['API_URL']}/storage/v1/object/public/{BUCKET}/{path}")


def test_owner_upload_and_anonymous_public_read(supabase_env, image_a):
    resp = _public_get(supabase_env, image_a)
    assert resp.status_code == 200
    assert resp.content == PNG


def test_owner_can_delete(supabase_env, user_a, image_a):
    user_a["client"].storage.from_(BUCKET).remove([image_a])
    assert _public_get(supabase_env, image_a).status_code in (400, 404)


def test_other_user_cannot_upload(supabase_env, user_b, trip_a):
    path = f"{trip_a['id']}/b.png"
    with pytest.raises(StorageApiError):
        user_b["client"].storage.from_(BUCKET).upload(path, PNG, {"content-type": "image/png"})
    assert _public_get(supabase_env, path).status_code in (400, 404)


def test_other_user_cannot_overwrite(supabase_env, user_b, image_a):
    with pytest.raises(StorageApiError):
        user_b["client"].storage.from_(BUCKET).upload(
            image_a, b"evil", {"content-type": "image/png", "upsert": "true"}
        )
    assert _public_get(supabase_env, image_a).content == PNG


def test_other_user_cannot_delete(supabase_env, user_b, image_a):
    user_b["client"].storage.from_(BUCKET).remove([image_a])
    assert _public_get(supabase_env, image_a).content == PNG
