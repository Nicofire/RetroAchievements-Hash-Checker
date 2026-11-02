import io
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError

import pytest

from ra_hash_checker.api import ApiError, RetroAchievementsAPI, build_hash_index
from ra_hash_checker.cache import CatalogStore, atomic_json

HASH = "abcdef01" * 4
GAMES = [{"ID": 10, "Title": "Game", "NumAchievements": 5, "Hashes": [HASH.upper()]}]


class FakeAPI:
    def __init__(self):
        self.calls = []

    def games(self, console_id):
        self.calls.append(console_id)
        return GAMES


def test_hash_index_priority():
    games = [*GAMES, {"ID": 3, "Title": "Alternate", "NumAchievements": 5, "Hashes": [HASH]}]
    assert [game.game_id for game in build_hash_index(games)[HASH]] == [3, 10]


@pytest.mark.parametrize("field,value", [("ID", True), ("ID", -1), ("NumAchievements", False),
                                        ("Title", None), ("Hashes", ["bad"]), ("Hashes", {})])
def test_invalid_catalog(field, value):
    with pytest.raises(ApiError):
        build_hash_index([{**GAMES[0], field: value}])


def test_api_secret_never_in_error():
    def opener(request, timeout):
        raise URLError(request.full_url)

    with pytest.raises(ApiError) as error:
        RetroAchievementsAPI("very-secret", opener=opener).games(18)
    assert "very-secret" not in str(error.value)


def test_incomplete_http_response_is_controlled():
    from http.client import IncompleteRead

    def opener(request, timeout):
        raise IncompleteRead(b"partial secret response")

    with pytest.raises(ApiError) as error:
        RetroAchievementsAPI("private-key", opener=opener).games(18)
    assert "secret" not in str(error.value)


def test_api_request_options_and_retry():
    calls = []
    delays = []

    def opener(request, timeout):
        calls.append(request.full_url)
        assert timeout == 30
        if len(calls) == 1:
            raise HTTPError(request.full_url, 429, "limit", {"Retry-After": "2"}, None)
        return io.BytesIO(json.dumps(GAMES).encode())

    assert RetroAchievementsAPI("key", opener=opener, sleeper=delays.append).games(18) == GAMES
    assert "i=18&h=1&f=0" in calls[0]
    assert len(calls) == 2
    assert delays == [2]


@pytest.mark.parametrize("code", [401, 403, 429])
def test_no_retry_auth_or_long_retry(code):
    calls = []

    def opener(request, timeout):
        calls.append(1)
        raise HTTPError(request.full_url, code, "error", {"Retry-After": "60"}, None)

    with pytest.raises(ApiError):
        RetroAchievementsAPI("secret", opener=opener).games(18)
    assert len(calls) == 1


def test_cache_single_fetch_and_offline(tmp_path):
    api = FakeAPI()
    store = CatalogStore(tmp_path, api)
    assert store.get(53).source == "api"
    store.get(53)
    assert api.calls == [53]
    offline = CatalogStore(tmp_path, api, offline=True)
    assert offline.get(53).source == "cache"
    with pytest.raises(ApiError):
        offline.get(18)
    assert api.calls == [53]


@pytest.mark.parametrize("age", [25, -2])
def test_reject_stale_future_cache(tmp_path, age):
    api = FakeAPI()
    store = CatalogStore(tmp_path, api, offline=True)
    fetched = datetime.now(timezone.utc) - timedelta(hours=age)
    atomic_json(tmp_path / "console-18.json", store._envelope(18, GAMES, fetched.isoformat()))
    with pytest.raises(ApiError):
        store.get(18)


def test_corrupt_cache_and_api_failure_preserve_old(tmp_path):
    path = tmp_path / "console-18.json"
    path.write_text("corrupt cache")
    store = CatalogStore(tmp_path, RetroAchievementsAPI(""))
    with pytest.raises(ApiError):
        store.get(18)
    assert path.read_text() == "corrupt cache"


def test_cache_write_failure_keeps_downloaded_data(tmp_path, monkeypatch):
    def fail(*args):
        raise PermissionError("test")

    monkeypatch.setattr("ra_hash_checker.cache.atomic_json", fail)
    catalog = CatalogStore(tmp_path, FakeAPI()).get(18)
    assert HASH in catalog.index
    assert catalog.warnings


def test_migration_keeps_age_and_original(tmp_path):
    old = tmp_path / "old.json"
    old.write_text(json.dumps(GAMES))
    fetched = datetime.now(timezone.utc) - timedelta(hours=2)
    os.utime(old, (fetched.timestamp(), fetched.timestamp()))
    catalog = CatalogStore(tmp_path / "cache", FakeAPI(), offline=True, legacy_cache=old).get(18)
    assert catalog.source == "legacy-cache"
    assert abs(datetime.fromisoformat(catalog.fetched_at).timestamp() - fetched.timestamp()) < 1
    assert json.loads(old.read_text()) == GAMES


def test_fds_requires_server_confirmation():
    def opener(request, timeout):
        return io.BytesIO(b'[{"ID": 7, "Name": "NES"}]')

    with pytest.raises(ApiError, match="did not confirm"):
        RetroAchievementsAPI("key", opener=opener).games(81)


@pytest.mark.parametrize("field,value", [("schema_version", True), ("console_id", True),
                                        ("options", {"h": True, "f": False}), ("options", {"h": 1})])
def test_reject_invalid_cache_metadata(tmp_path, field, value):
    store = CatalogStore(tmp_path, FakeAPI(), offline=True)
    payload = store._envelope(1, GAMES, datetime.now(timezone.utc).isoformat())
    payload[field] = value
    atomic_json(tmp_path / "console-1.json", payload)
    with pytest.raises(ApiError):
        store.get(1)


def test_atomic_replace_failure_preserves_cache(tmp_path, monkeypatch):
    path = tmp_path / "existing.json"
    atomic_json(path, {"old": True})

    def fail(*args):
        raise PermissionError("test")

    monkeypatch.setattr("ra_hash_checker.cache.os.replace", fail)
    with pytest.raises(PermissionError):
        atomic_json(path, {"new": True})
    assert json.loads(path.read_text(encoding="utf-8")) == {"old": True}
    assert list(tmp_path.iterdir()) == [path]