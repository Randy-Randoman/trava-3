import importlib

import main


def test_allowed_origins_strips_whitespace_and_drops_empty_entries(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.app, https://b.app,,")
    assert importlib.reload(main).allowed_origins == ["https://a.app", "https://b.app"]
